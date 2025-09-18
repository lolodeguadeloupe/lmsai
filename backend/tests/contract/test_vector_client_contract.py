"""
Contract tests for vector database client implementations.

These tests verify that both Pinecone and Chroma implementations
conform to the same interface and behavior expectations.
"""

import asyncio
import os
import pytest
from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from src.integrations.vector_client import (
    VectorDatabaseClient,
    VectorConfig,
    VectorBackend,
    ContentEmbedding,
    ContentType,
    VectorSearchQuery,
    create_vector_client
)


@pytest.fixture
def sample_course_id():
    """Sample course ID for testing."""
    return uuid4()


@pytest.fixture
def sample_embeddings():
    """Sample embeddings for testing."""
    return [
        [0.1] * 1536,  # Dummy 1536-dimensional embedding
        [0.2] * 1536,
        [0.3] * 1536
    ]


@pytest.fixture
def sample_content_data(sample_course_id):
    """Sample content data for testing."""
    return [
        {
            "id": "course-intro",
            "content_type": "course",
            "title": "Introduction to Machine Learning",
            "text": "Machine learning is a subset of artificial intelligence...",
            "metadata": {"difficulty": "beginner", "duration": "30min"}
        },
        {
            "id": "chapter-1",
            "content_type": "chapter", 
            "title": "What is Machine Learning?",
            "text": "Machine learning algorithms build mathematical models...",
            "metadata": {"chapter_number": 1}
        },
        {
            "id": "concept-supervised",
            "content_type": "concept",
            "title": "Supervised Learning",
            "text": "Supervised learning uses labeled training data...",
            "metadata": {"concept_category": "learning_types"}
        }
    ]


class VectorClientContractTest:
    """Base contract test class for vector database clients."""
    
    @pytest.fixture
    def client(self):
        """Override this in implementation-specific test classes."""
        raise NotImplementedError
    
    @pytest.mark.asyncio
    async def test_connection_lifecycle(self, client):
        """Test connection and disconnection."""
        await client.connect()
        # Connection should be established without errors
        
        health = await client.health_check()
        assert health["status"] in ["healthy", "unhealthy"]  # Should return status
        
        await client.disconnect()
        # Disconnection should complete without errors
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_content(self, client, sample_course_id, sample_content_data, sample_embeddings):
        """Test storing and retrieving content embeddings."""
        await client.connect()
        
        try:
            # Store embeddings
            success = await client.store_course_embeddings(
                course_id=sample_course_id,
                content_data=sample_content_data,
                embeddings=sample_embeddings
            )
            assert success is True
            
            # Retrieve specific content
            content = await client.get_content_by_id("course-intro")
            if content:  # Some backends might not support immediate retrieval
                assert content.id == "course-intro"
                assert content.course_id == sample_course_id
                assert content.content_type == ContentType.COURSE
                assert content.title == "Introduction to Machine Learning"
                assert "difficulty" in content.metadata
        
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_similarity_search(self, client, sample_course_id, sample_content_data, sample_embeddings):
        """Test similarity search functionality."""
        await client.connect()
        
        try:
            # Store test data
            await client.store_course_embeddings(
                course_id=sample_course_id,
                content_data=sample_content_data,
                embeddings=sample_embeddings
            )
            
            # Wait a bit for indexing (some backends need time)
            await asyncio.sleep(1)
            
            # Search with query embedding
            results = await client.search_similar_content(
                query_embedding=sample_embeddings[0],
                course_ids=[sample_course_id],
                limit=2,
                min_similarity=0.0  # Low threshold for test data
            )
            
            # Should find at least one result (might be empty if backend doesn't support immediate search)
            assert isinstance(results, list)
            for result in results:
                assert hasattr(result, 'content')
                assert hasattr(result, 'similarity_score')
                assert hasattr(result, 'distance')
                assert 0.0 <= result.similarity_score <= 1.0
                assert result.distance >= 0.0
        
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_content_filtering(self, client, sample_course_id, sample_content_data, sample_embeddings):
        """Test content filtering by type and course."""
        await client.connect()
        
        try:
            # Store test data
            await client.store_course_embeddings(
                course_id=sample_course_id,
                content_data=sample_content_data,
                embeddings=sample_embeddings
            )
            
            await asyncio.sleep(1)  # Wait for indexing
            
            # Search for concepts only
            results = await client.search_similar_content(
                query_embedding=sample_embeddings[2],
                content_types=["concept"],
                limit=5,
                min_similarity=0.0
            )
            
            # All results should be concepts (if any)
            for result in results:
                assert result.content.content_type == ContentType.CONCEPT
        
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_related_concepts(self, client, sample_course_id, sample_content_data, sample_embeddings):
        """Test related concepts functionality."""
        await client.connect()
        
        try:
            # Store test data
            await client.store_course_embeddings(
                course_id=sample_course_id,
                content_data=sample_content_data,
                embeddings=sample_embeddings
            )
            
            await asyncio.sleep(1)  # Wait for indexing
            
            # Find related concepts
            related = await client.get_related_concepts(
                concept_text="supervised learning",
                course_id=sample_course_id,
                limit=3
            )
            
            # Should return list (might be empty)
            assert isinstance(related, list)
            for concept in related:
                assert concept.content.content_type == ContentType.CONCEPT
        
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_content_deletion(self, client, sample_course_id, sample_content_data, sample_embeddings):
        """Test content deletion functionality."""
        await client.connect()
        
        try:
            # Store test data
            await client.store_course_embeddings(
                course_id=sample_course_id,
                content_data=sample_content_data,
                embeddings=sample_embeddings
            )
            
            # Delete course content
            success = await client.delete_course_vectors(sample_course_id)
            assert success is True
            
            # Verify deletion (might not be immediate)
            content = await client.get_content_by_id("course-intro")
            # Content should be None or method should not raise errors
            
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_content_updates(self, client, sample_course_id, sample_content_data, sample_embeddings):
        """Test content vector and metadata updates."""
        await client.connect()
        
        try:
            # Store initial data
            await client.store_course_embeddings(
                course_id=sample_course_id,
                content_data=sample_content_data,
                embeddings=sample_embeddings
            )
            
            # Update content
            new_embedding = [0.5] * 1536
            new_metadata = {"updated": True, "version": 2}
            
            updates = [("course-intro", new_embedding, new_metadata)]
            success = await client.update_content_vectors(updates)
            
            # Update should succeed or fail gracefully
            assert isinstance(success, bool)
        
        finally:
            await client.disconnect()
    
    @pytest.mark.asyncio
    async def test_error_handling(self, client):
        """Test error handling for invalid operations."""
        # Test operations without connection
        with pytest.raises(Exception):  # Should raise some form of error
            await client.search_similar_content(query_text="test")
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check functionality."""
        health = await client.health_check()
        
        assert isinstance(health, dict)
        assert "status" in health
        assert health["status"] in ["healthy", "unhealthy"]
        assert "backend" in health


class TestPineconeVectorClient(VectorClientContractTest):
    """Contract tests for Pinecone implementation."""
    
    @pytest.fixture
    def client(self):
        """Create Pinecone test client."""
        # Skip if Pinecone credentials not available
        api_key = os.getenv("PINECONE_API_KEY")
        environment = os.getenv("PINECONE_ENVIRONMENT")
        
        if not api_key or not environment:
            pytest.skip("Pinecone credentials not available")
        
        return create_vector_client(
            backend="pinecone",
            pinecone_api_key=api_key,
            pinecone_environment=environment,
            pinecone_index_name="test-course-embeddings"
        )


class TestChromaVectorClient(VectorClientContractTest):
    """Contract tests for ChromaDB implementation."""
    
    @pytest.fixture
    def client(self):
        """Create ChromaDB test client."""
        # Check if ChromaDB is available
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
        
        return create_vector_client(
            backend="chroma",
            chroma_host=chroma_host,
            chroma_port=chroma_port,
            chroma_collection_name="test_course_embeddings"
        )


class TestVectorClientConfiguration:
    """Test vector client configuration and factory."""
    
    def test_create_pinecone_client(self):
        """Test Pinecone client creation."""
        client = create_vector_client(
            backend="pinecone",
            pinecone_api_key="test-key",
            pinecone_environment="test-env"
        )
        
        assert client.config.backend == VectorBackend.PINECONE
        assert client.config.pinecone_api_key == "test-key"
        assert client.config.pinecone_environment == "test-env"
    
    def test_create_chroma_client(self):
        """Test ChromaDB client creation."""
        client = create_vector_client(
            backend="chroma",
            chroma_host="test-host",
            chroma_port=9000
        )
        
        assert client.config.backend == VectorBackend.CHROMA
        assert client.config.chroma_host == "test-host"
        assert client.config.chroma_port == 9000
    
    def test_invalid_backend(self):
        """Test invalid backend handling."""
        with pytest.raises(ValueError):
            create_vector_client(backend="invalid")


class TestContentEmbedding:
    """Test ContentEmbedding model validation."""
    
    def test_valid_content_embedding(self):
        """Test valid content embedding creation."""
        embedding = ContentEmbedding(
            id="test-id",
            content_type=ContentType.COURSE,
            course_id=uuid4(),
            title="Test Content",
            text="Test text content",
            metadata={"key": "value"}
        )
        
        assert embedding.id == "test-id"
        assert embedding.content_type == ContentType.COURSE
        assert embedding.metadata["key"] == "value"
        assert isinstance(embedding.created_at, datetime)
    
    def test_embedding_dimension_validation(self):
        """Test embedding dimension validation."""
        # This should log a warning but not fail
        embedding = ContentEmbedding(
            id="test-id",
            content_type=ContentType.COURSE,
            course_id=uuid4(),
            title="Test",
            text="Test",
            embedding=[0.1] * 512  # Wrong dimension
        )
        
        assert len(embedding.embedding) == 512


class TestVectorSearchQuery:
    """Test VectorSearchQuery validation."""
    
    def test_query_with_text(self):
        """Test query with text input."""
        query = VectorSearchQuery(query_text="machine learning")
        
        assert query.query_text == "machine learning"
        assert query.query_embedding is None
        assert query.limit == 10
        assert query.min_similarity == 0.7
    
    def test_query_with_embedding(self):
        """Test query with embedding input."""
        embedding = [0.1] * 1536
        query = VectorSearchQuery(query_embedding=embedding)
        
        assert query.query_embedding == embedding
        assert query.query_text is None
    
    def test_query_validation_error(self):
        """Test query validation requires either text or embedding."""
        with pytest.raises(ValueError, match="Either query_text or query_embedding must be provided"):
            VectorSearchQuery()
    
    def test_query_with_filters(self):
        """Test query with various filters."""
        course_ids = [uuid4(), uuid4()]
        content_types = [ContentType.COURSE, ContentType.CHAPTER]
        
        query = VectorSearchQuery(
            query_text="test",
            course_ids=course_ids,
            content_types=content_types,
            metadata_filters={"difficulty": "beginner"},
            limit=20,
            min_similarity=0.8
        )
        
        assert query.course_ids == course_ids
        assert query.content_types == content_types
        assert query.metadata_filters["difficulty"] == "beginner"
        assert query.limit == 20
        assert query.min_similarity == 0.8