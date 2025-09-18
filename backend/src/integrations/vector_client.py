"""
Vector database client supporting both Pinecone and Chroma backends.

Provides unified interface for course content embeddings, similarity search,
and concept relationship management for the course generation platform.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

import chromadb
import numpy as np
import pinecone
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from pydantic import BaseModel, Field, model_validator, field_validator

logger = logging.getLogger(__name__)


class VectorBackend(str, Enum):
    """Supported vector database backends."""
    
    PINECONE = "pinecone"
    CHROMA = "chroma"


class ContentType(str, Enum):
    """Types of content that can be stored as embeddings."""
    
    COURSE = "course"
    CHAPTER = "chapter"
    SUBCHAPTER = "subchapter"
    CONCEPT = "concept"
    QUESTION = "question"
    FLASHCARD = "flashcard"


@dataclass
class VectorConfig:
    """Configuration for vector database connections."""
    
    backend: VectorBackend
    # Pinecone config
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None
    pinecone_index_name: str = "course-embeddings"
    # Chroma config
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_collection_name: str = "course_embeddings"
    # General config
    embedding_dimension: int = 1536  # OpenAI ada-002 default
    connection_pool_size: int = 10
    max_retries: int = 3
    timeout_seconds: int = 30


class ContentEmbedding(BaseModel):
    """Represents content with its vector embedding."""
    
    id: str = Field(..., description="Unique identifier for the content")
    content_type: ContentType = Field(..., description="Type of content")
    course_id: UUID = Field(..., description="Associated course ID")
    title: str = Field(..., description="Content title")
    text: str = Field(..., description="Text content to embed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    embedding: Optional[List[float]] = Field(None, description="Vector embedding")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator("embedding")
    @classmethod
    def validate_embedding_dimension(cls, v):
        """Validate embedding dimension if present."""
        if v is not None and len(v) != 1536:  # Default OpenAI dimension
            logger.warning(f"Embedding dimension {len(v)} differs from expected 1536")
        return v


class SimilarityResult(BaseModel):
    """Result from similarity search."""
    
    content: ContentEmbedding
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    distance: float = Field(..., ge=0.0)


class VectorSearchQuery(BaseModel):
    """Query parameters for vector similarity search."""
    
    query_text: Optional[str] = None
    query_embedding: Optional[List[float]] = None
    content_types: Optional[List[ContentType]] = None
    course_ids: Optional[List[UUID]] = None
    metadata_filters: Optional[Dict[str, Any]] = None
    limit: int = Field(10, ge=1, le=100)
    min_similarity: float = Field(0.7, ge=0.0, le=1.0)
    
    @model_validator(mode='before')
    @classmethod
    def validate_query_input(cls, values):
        """Ensure either query_text or query_embedding is provided."""
        if isinstance(values, dict):
            query_text = values.get("query_text")
            query_embedding = values.get("query_embedding")
            if not query_text and not query_embedding:
                raise ValueError("Either query_text or query_embedding must be provided")
        return values


class VectorDatabaseError(Exception):
    """Base exception for vector database operations."""
    pass


class ConnectionError(VectorDatabaseError):
    """Connection-related errors."""
    pass


class EmbeddingError(VectorDatabaseError):
    """Embedding generation errors."""
    pass


class SearchError(VectorDatabaseError):
    """Search operation errors."""
    pass


class BaseVectorClient(ABC):
    """Abstract base class for vector database clients."""
    
    def __init__(self, config: VectorConfig):
        self.config = config
        self._connection_pool = asyncio.Semaphore(config.connection_pool_size)
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the vector database."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the vector database."""
        pass
    
    @abstractmethod
    async def store_embeddings(self, embeddings: List[ContentEmbedding]) -> bool:
        """Store content embeddings in the database."""
        pass
    
    @abstractmethod
    async def search_similar_content(self, query: VectorSearchQuery) -> List[SimilarityResult]:
        """Search for similar content using vector similarity."""
        pass
    
    @abstractmethod
    async def delete_content(self, content_ids: List[str]) -> bool:
        """Delete content by IDs."""
        pass
    
    @abstractmethod
    async def delete_course_content(self, course_id: UUID) -> bool:
        """Delete all content for a specific course."""
        pass
    
    @abstractmethod
    async def get_content(self, content_id: str) -> Optional[ContentEmbedding]:
        """Retrieve specific content by ID."""
        pass
    
    @abstractmethod
    async def update_content_metadata(self, content_id: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for specific content."""
        pass
    
    @asynccontextmanager
    async def _connection_context(self):
        """Context manager for connection pooling."""
        async with self._connection_pool:
            yield


class PineconeVectorClient(BaseVectorClient):
    """Pinecone vector database client implementation."""
    
    def __init__(self, config: VectorConfig):
        super().__init__(config)
        self._index = None
    
    async def connect(self) -> None:
        """Initialize Pinecone connection."""
        try:
            if not self.config.pinecone_api_key:
                raise ConnectionError("Pinecone API key not provided")
            
            pinecone.init(
                api_key=self.config.pinecone_api_key,
                environment=self.config.pinecone_environment
            )
            
            # Create index if it doesn't exist
            if self.config.pinecone_index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=self.config.pinecone_index_name,
                    dimension=self.config.embedding_dimension,
                    metric="cosine"
                )
            
            self._index = pinecone.Index(self.config.pinecone_index_name)
            logger.info(f"Connected to Pinecone index: {self.config.pinecone_index_name}")
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Pinecone: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close Pinecone connection."""
        self._index = None
        logger.info("Disconnected from Pinecone")
    
    async def store_embeddings(self, embeddings: List[ContentEmbedding]) -> bool:
        """Store embeddings in Pinecone."""
        if not self._index:
            raise ConnectionError("Not connected to Pinecone")
        
        try:
            async with self._connection_context():
                vectors = []
                for embedding in embeddings:
                    if not embedding.embedding:
                        raise EmbeddingError(f"Missing embedding for content {embedding.id}")
                    
                    metadata = {
                        "content_type": embedding.content_type.value,
                        "course_id": str(embedding.course_id),
                        "title": embedding.title,
                        "text": embedding.text[:1000],  # Pinecone metadata limit
                        "created_at": embedding.created_at.isoformat(),
                        **embedding.metadata
                    }
                    
                    vectors.append({
                        "id": embedding.id,
                        "values": embedding.embedding,
                        "metadata": metadata
                    })
                
                # Batch upsert
                batch_size = 100
                for i in range(0, len(vectors), batch_size):
                    batch = vectors[i:i + batch_size]
                    self._index.upsert(vectors=batch)
                
                logger.info(f"Stored {len(embeddings)} embeddings in Pinecone")
                return True
                
        except Exception as e:
            logger.error(f"Error storing embeddings in Pinecone: {str(e)}")
            return False
    
    async def search_similar_content(self, query: VectorSearchQuery) -> List[SimilarityResult]:
        """Search for similar content in Pinecone."""
        if not self._index:
            raise ConnectionError("Not connected to Pinecone")
        
        try:
            async with self._connection_context():
                # Build metadata filter
                filter_dict = {}
                if query.content_types:
                    filter_dict["content_type"] = {"$in": [ct.value for ct in query.content_types]}
                if query.course_ids:
                    filter_dict["course_id"] = {"$in": [str(cid) for cid in query.course_ids]}
                if query.metadata_filters:
                    filter_dict.update(query.metadata_filters)
                
                # Use provided embedding or generate from text
                query_vector = query.query_embedding
                if not query_vector and query.query_text:
                    # Note: In production, you'd call an embedding service here
                    raise EmbeddingError("Query embedding generation not implemented")
                
                if not query_vector:
                    raise SearchError("No query vector available")
                
                # Perform search
                search_response = self._index.query(
                    vector=query_vector,
                    top_k=query.limit,
                    include_metadata=True,
                    filter=filter_dict if filter_dict else None
                )
                
                # Convert results
                results = []
                for match in search_response.matches:
                    if match.score >= query.min_similarity:
                        metadata = match.metadata
                        content = ContentEmbedding(
                            id=match.id,
                            content_type=ContentType(metadata["content_type"]),
                            course_id=UUID(metadata["course_id"]),
                            title=metadata["title"],
                            text=metadata["text"],
                            created_at=datetime.fromisoformat(metadata["created_at"]),
                            metadata={k: v for k, v in metadata.items() 
                                    if k not in ["content_type", "course_id", "title", "text", "created_at"]}
                        )
                        
                        results.append(SimilarityResult(
                            content=content,
                            similarity_score=float(match.score),
                            distance=1.0 - float(match.score)
                        ))
                
                logger.info(f"Found {len(results)} similar content items in Pinecone")
                return results
                
        except Exception as e:
            logger.error(f"Error searching in Pinecone: {str(e)}")
            raise SearchError(f"Pinecone search failed: {str(e)}")
    
    async def delete_content(self, content_ids: List[str]) -> bool:
        """Delete content by IDs from Pinecone."""
        if not self._index:
            raise ConnectionError("Not connected to Pinecone")
        
        try:
            async with self._connection_context():
                self._index.delete(ids=content_ids)
                logger.info(f"Deleted {len(content_ids)} items from Pinecone")
                return True
        except Exception as e:
            logger.error(f"Error deleting from Pinecone: {str(e)}")
            return False
    
    async def delete_course_content(self, course_id: UUID) -> bool:
        """Delete all content for a course from Pinecone."""
        if not self._index:
            raise ConnectionError("Not connected to Pinecone")
        
        try:
            async with self._connection_context():
                self._index.delete(filter={"course_id": str(course_id)})
                logger.info(f"Deleted course {course_id} content from Pinecone")
                return True
        except Exception as e:
            logger.error(f"Error deleting course content from Pinecone: {str(e)}")
            return False
    
    async def get_content(self, content_id: str) -> Optional[ContentEmbedding]:
        """Retrieve content by ID from Pinecone."""
        if not self._index:
            raise ConnectionError("Not connected to Pinecone")
        
        try:
            async with self._connection_context():
                response = self._index.fetch(ids=[content_id])
                if content_id not in response.vectors:
                    return None
                
                vector_data = response.vectors[content_id]
                metadata = vector_data.metadata
                
                return ContentEmbedding(
                    id=content_id,
                    content_type=ContentType(metadata["content_type"]),
                    course_id=UUID(metadata["course_id"]),
                    title=metadata["title"],
                    text=metadata["text"],
                    embedding=vector_data.values,
                    created_at=datetime.fromisoformat(metadata["created_at"]),
                    metadata={k: v for k, v in metadata.items() 
                            if k not in ["content_type", "course_id", "title", "text", "created_at"]}
                )
        except Exception as e:
            logger.error(f"Error retrieving content from Pinecone: {str(e)}")
            return None
    
    async def update_content_metadata(self, content_id: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for content in Pinecone."""
        if not self._index:
            raise ConnectionError("Not connected to Pinecone")
        
        try:
            async with self._connection_context():
                # Pinecone requires full vector update, so we fetch first
                current_content = await self.get_content(content_id)
                if not current_content:
                    return False
                
                current_content.metadata.update(metadata)
                return await self.store_embeddings([current_content])
        except Exception as e:
            logger.error(f"Error updating metadata in Pinecone: {str(e)}")
            return False


class ChromaVectorClient(BaseVectorClient):
    """ChromaDB vector database client implementation."""
    
    def __init__(self, config: VectorConfig):
        super().__init__(config)
        self._client = None
        self._collection = None
    
    async def connect(self) -> None:
        """Initialize ChromaDB connection."""
        try:
            self._client = chromadb.HttpClient(
                host=self.config.chroma_host,
                port=self.config.chroma_port,
                settings=Settings(
                    chroma_client_auth_provider="chromadb.auth.basic.BasicAuthClientProvider",
                    chroma_client_auth_credentials_provider="chromadb.auth.basic.BasicAuthCredentialsProvider"
                )
            )
            
            # Create or get collection
            try:
                self._collection = self._client.get_collection(self.config.chroma_collection_name)
            except Exception:
                # Collection doesn't exist, create it
                self._collection = self._client.create_collection(
                    name=self.config.chroma_collection_name,
                    embedding_function=embedding_functions.DefaultEmbeddingFunction()
                )
            
            logger.info(f"Connected to ChromaDB collection: {self.config.chroma_collection_name}")
            
        except Exception as e:
            raise ConnectionError(f"Failed to connect to ChromaDB: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close ChromaDB connection."""
        self._client = None
        self._collection = None
        logger.info("Disconnected from ChromaDB")
    
    async def store_embeddings(self, embeddings: List[ContentEmbedding]) -> bool:
        """Store embeddings in ChromaDB."""
        if not self._collection:
            raise ConnectionError("Not connected to ChromaDB")
        
        try:
            async with self._connection_context():
                ids = []
                embeddings_list = []
                metadatas = []
                documents = []
                
                for embedding in embeddings:
                    if not embedding.embedding:
                        raise EmbeddingError(f"Missing embedding for content {embedding.id}")
                    
                    ids.append(embedding.id)
                    embeddings_list.append(embedding.embedding)
                    documents.append(embedding.text)
                    
                    metadata = {
                        "content_type": embedding.content_type.value,
                        "course_id": str(embedding.course_id),
                        "title": embedding.title,
                        "created_at": embedding.created_at.isoformat(),
                        **embedding.metadata
                    }
                    metadatas.append(metadata)
                
                # Upsert to ChromaDB
                self._collection.upsert(
                    ids=ids,
                    embeddings=embeddings_list,
                    metadatas=metadatas,
                    documents=documents
                )
                
                logger.info(f"Stored {len(embeddings)} embeddings in ChromaDB")
                return True
                
        except Exception as e:
            logger.error(f"Error storing embeddings in ChromaDB: {str(e)}")
            return False
    
    async def search_similar_content(self, query: VectorSearchQuery) -> List[SimilarityResult]:
        """Search for similar content in ChromaDB."""
        if not self._collection:
            raise ConnectionError("Not connected to ChromaDB")
        
        try:
            async with self._connection_context():
                # Build where clause
                where_clause = {}
                if query.content_types:
                    where_clause["content_type"] = {"$in": [ct.value for ct in query.content_types]}
                if query.course_ids:
                    where_clause["course_id"] = {"$in": [str(cid) for cid in query.course_ids]}
                if query.metadata_filters:
                    where_clause.update(query.metadata_filters)
                
                # Use provided embedding or query text
                if query.query_embedding:
                    search_response = self._collection.query(
                        query_embeddings=[query.query_embedding],
                        n_results=query.limit,
                        where=where_clause if where_clause else None
                    )
                elif query.query_text:
                    search_response = self._collection.query(
                        query_texts=[query.query_text],
                        n_results=query.limit,
                        where=where_clause if where_clause else None
                    )
                else:
                    raise SearchError("No query vector or text available")
                
                # Convert results
                results = []
                if search_response["ids"] and search_response["ids"][0]:
                    for i, content_id in enumerate(search_response["ids"][0]):
                        distance = search_response["distances"][0][i]
                        similarity = 1.0 - distance  # Convert distance to similarity
                        
                        if similarity >= query.min_similarity:
                            metadata = search_response["metadatas"][0][i]
                            document = search_response["documents"][0][i]
                            
                            content = ContentEmbedding(
                                id=content_id,
                                content_type=ContentType(metadata["content_type"]),
                                course_id=UUID(metadata["course_id"]),
                                title=metadata["title"],
                                text=document,
                                created_at=datetime.fromisoformat(metadata["created_at"]),
                                metadata={k: v for k, v in metadata.items() 
                                        if k not in ["content_type", "course_id", "title", "created_at"]}
                            )
                            
                            results.append(SimilarityResult(
                                content=content,
                                similarity_score=similarity,
                                distance=distance
                            ))
                
                logger.info(f"Found {len(results)} similar content items in ChromaDB")
                return results
                
        except Exception as e:
            logger.error(f"Error searching in ChromaDB: {str(e)}")
            raise SearchError(f"ChromaDB search failed: {str(e)}")
    
    async def delete_content(self, content_ids: List[str]) -> bool:
        """Delete content by IDs from ChromaDB."""
        if not self._collection:
            raise ConnectionError("Not connected to ChromaDB")
        
        try:
            async with self._connection_context():
                self._collection.delete(ids=content_ids)
                logger.info(f"Deleted {len(content_ids)} items from ChromaDB")
                return True
        except Exception as e:
            logger.error(f"Error deleting from ChromaDB: {str(e)}")
            return False
    
    async def delete_course_content(self, course_id: UUID) -> bool:
        """Delete all content for a course from ChromaDB."""
        if not self._collection:
            raise ConnectionError("Not connected to ChromaDB")
        
        try:
            async with self._connection_context():
                self._collection.delete(where={"course_id": str(course_id)})
                logger.info(f"Deleted course {course_id} content from ChromaDB")
                return True
        except Exception as e:
            logger.error(f"Error deleting course content from ChromaDB: {str(e)}")
            return False
    
    async def get_content(self, content_id: str) -> Optional[ContentEmbedding]:
        """Retrieve content by ID from ChromaDB."""
        if not self._collection:
            raise ConnectionError("Not connected to ChromaDB")
        
        try:
            async with self._connection_context():
                response = self._collection.get(ids=[content_id], include=["metadatas", "documents", "embeddings"])
                
                if not response["ids"] or content_id not in response["ids"]:
                    return None
                
                idx = response["ids"].index(content_id)
                metadata = response["metadatas"][idx]
                document = response["documents"][idx]
                embedding = response["embeddings"][idx] if response["embeddings"] else None
                
                return ContentEmbedding(
                    id=content_id,
                    content_type=ContentType(metadata["content_type"]),
                    course_id=UUID(metadata["course_id"]),
                    title=metadata["title"],
                    text=document,
                    embedding=embedding,
                    created_at=datetime.fromisoformat(metadata["created_at"]),
                    metadata={k: v for k, v in metadata.items() 
                            if k not in ["content_type", "course_id", "title", "created_at"]}
                )
        except Exception as e:
            logger.error(f"Error retrieving content from ChromaDB: {str(e)}")
            return None
    
    async def update_content_metadata(self, content_id: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for content in ChromaDB."""
        if not self._collection:
            raise ConnectionError("Not connected to ChromaDB")
        
        try:
            async with self._connection_context():
                # Get current content
                current = await self.get_content(content_id)
                if not current:
                    return False
                
                # Update metadata and store
                current.metadata.update(metadata)
                return await self.store_embeddings([current])
        except Exception as e:
            logger.error(f"Error updating metadata in ChromaDB: {str(e)}")
            return False


class VectorDatabaseClient:
    """Unified vector database client supporting multiple backends."""
    
    def __init__(self, config: VectorConfig):
        self.config = config
        self._client: Optional[BaseVectorClient] = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the appropriate client based on configuration."""
        if self.config.backend == VectorBackend.PINECONE:
            self._client = PineconeVectorClient(self.config)
        elif self.config.backend == VectorBackend.CHROMA:
            self._client = ChromaVectorClient(self.config)
        else:
            raise ValueError(f"Unsupported vector backend: {self.config.backend}")
    
    async def connect(self) -> None:
        """Connect to the vector database."""
        if self._client:
            await self._client.connect()
    
    async def disconnect(self) -> None:
        """Disconnect from the vector database."""
        if self._client:
            await self._client.disconnect()
    
    async def store_course_embeddings(
        self, 
        course_id: UUID, 
        content_data: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> bool:
        """
        Store course content embeddings.
        
        Args:
            course_id: Course identifier
            content_data: List of content metadata dicts
            embeddings: Corresponding embedding vectors
            
        Returns:
            Success status
        """
        if not self._client:
            raise VectorDatabaseError("Client not initialized")
        
        if len(content_data) != len(embeddings):
            raise ValueError("Content data and embeddings lists must have same length")
        
        content_embeddings = []
        for i, (content, embedding) in enumerate(zip(content_data, embeddings)):
            content_embedding = ContentEmbedding(
                id=content.get("id", f"{course_id}-{i}"),
                content_type=ContentType(content.get("content_type", "course")),
                course_id=course_id,
                title=content.get("title", ""),
                text=content.get("text", ""),
                embedding=embedding,
                metadata=content.get("metadata", {})
            )
            content_embeddings.append(content_embedding)
        
        return await self._client.store_embeddings(content_embeddings)
    
    async def search_similar_content(
        self, 
        query_text: Optional[str] = None,
        query_embedding: Optional[List[float]] = None,
        course_ids: Optional[List[UUID]] = None,
        content_types: Optional[List[str]] = None,
        limit: int = 10,
        min_similarity: float = 0.7
    ) -> List[SimilarityResult]:
        """
        Search for similar content.
        
        Args:
            query_text: Text to search for
            query_embedding: Pre-computed query embedding
            course_ids: Filter by specific courses
            content_types: Filter by content types
            limit: Maximum results to return
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of similar content results
        """
        if not self._client:
            raise VectorDatabaseError("Client not initialized")
        
        content_type_enums = None
        if content_types:
            content_type_enums = [ContentType(ct) for ct in content_types]
        
        query = VectorSearchQuery(
            query_text=query_text,
            query_embedding=query_embedding,
            course_ids=course_ids,
            content_types=content_type_enums,
            limit=limit,
            min_similarity=min_similarity
        )
        
        return await self._client.search_similar_content(query)
    
    async def get_related_concepts(
        self, 
        concept_text: str,
        course_id: Optional[UUID] = None,
        limit: int = 5
    ) -> List[SimilarityResult]:
        """
        Find concepts related to the given concept.
        
        Args:
            concept_text: The concept to find relations for
            course_id: Optional course context
            limit: Maximum related concepts to return
            
        Returns:
            List of related concepts
        """
        course_ids = [course_id] if course_id else None
        return await self.search_similar_content(
            query_text=concept_text,
            course_ids=course_ids,
            content_types=["concept"],
            limit=limit,
            min_similarity=0.6
        )
    
    async def update_content_vectors(
        self, 
        content_updates: List[Tuple[str, List[float], Dict[str, Any]]]
    ) -> bool:
        """
        Update content vectors and metadata.
        
        Args:
            content_updates: List of (content_id, new_embedding, new_metadata) tuples
            
        Returns:
            Success status
        """
        if not self._client:
            raise VectorDatabaseError("Client not initialized")
        
        success_count = 0
        for content_id, embedding, metadata in content_updates:
            # Get current content
            current_content = await self._client.get_content(content_id)
            if current_content:
                # Update embedding and metadata
                current_content.embedding = embedding
                current_content.metadata.update(metadata)
                
                if await self._client.store_embeddings([current_content]):
                    success_count += 1
        
        return success_count == len(content_updates)
    
    async def delete_course_vectors(self, course_id: UUID) -> bool:
        """
        Delete all vectors for a specific course.
        
        Args:
            course_id: Course identifier
            
        Returns:
            Success status
        """
        if not self._client:
            raise VectorDatabaseError("Client not initialized")
        
        return await self._client.delete_course_content(course_id)
    
    async def get_content_by_id(self, content_id: str) -> Optional[ContentEmbedding]:
        """
        Retrieve content by ID.
        
        Args:
            content_id: Content identifier
            
        Returns:
            Content embedding if found
        """
        if not self._client:
            raise VectorDatabaseError("Client not initialized")
        
        return await self._client.get_content(content_id)
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the vector database connection.
        
        Returns:
            Health status information
        """
        try:
            # Try a simple operation to test connectivity
            test_query = VectorSearchQuery(
                query_text="test",
                limit=1
            )
            
            start_time = datetime.utcnow()
            results = await self._client.search_similar_content(test_query)
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                "status": "healthy",
                "backend": self.config.backend.value,
                "response_time_seconds": response_time,
                "connection_pool_size": self.config.connection_pool_size,
                "test_results_count": len(results)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": self.config.backend.value,
                "error": str(e),
                "connection_pool_size": self.config.connection_pool_size
            }


# Factory function for easy client creation
def create_vector_client(
    backend: str,
    pinecone_api_key: Optional[str] = None,
    pinecone_environment: Optional[str] = None,
    chroma_host: str = "localhost",
    chroma_port: int = 8000,
    **kwargs
) -> VectorDatabaseClient:
    """
    Factory function to create a vector database client.
    
    Args:
        backend: Vector database backend ("pinecone" or "chroma")
        pinecone_api_key: Pinecone API key (required for Pinecone)
        pinecone_environment: Pinecone environment (required for Pinecone)
        chroma_host: ChromaDB host (for Chroma)
        chroma_port: ChromaDB port (for Chroma)
        **kwargs: Additional configuration options
        
    Returns:
        Configured vector database client
    """
    config = VectorConfig(
        backend=VectorBackend(backend),
        pinecone_api_key=pinecone_api_key,
        pinecone_environment=pinecone_environment,
        chroma_host=chroma_host,
        chroma_port=chroma_port,
        **kwargs
    )
    
    return VectorDatabaseClient(config)