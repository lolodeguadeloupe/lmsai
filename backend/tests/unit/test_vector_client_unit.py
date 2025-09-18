"""
Unit tests for vector database client components.

Tests individual components and methods without requiring external dependencies.
"""

import pytest
from datetime import datetime
from uuid import UUID, uuid4
from unittest.mock import Mock, AsyncMock, patch

from src.integrations.vector_client import (
    VectorConfig,
    VectorBackend,
    ContentEmbedding,
    ContentType,
    VectorSearchQuery,
    SimilarityResult,
    VectorDatabaseClient,
    create_vector_client,
    VectorDatabaseError,
    PineconeVectorClient,
    ChromaVectorClient
)
from src.integrations.config import (
    VectorDatabaseSettings,
    get_environment_settings,
    validate_vector_config,
    CHROMA_LOCAL_CONFIG
)


class TestVectorConfig:
    """Test VectorConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = VectorConfig(backend=VectorBackend.CHROMA)
        
        assert config.backend == VectorBackend.CHROMA
        assert config.chroma_host == "localhost"
        assert config.chroma_port == 8000
        assert config.embedding_dimension == 1536
        assert config.connection_pool_size == 10
        assert config.max_retries == 3
    
    def test_pinecone_config(self):
        """Test Pinecone-specific configuration."""
        config = VectorConfig(
            backend=VectorBackend.PINECONE,
            pinecone_api_key="test-key",
            pinecone_environment="us-west1-gcp",
            pinecone_index_name="test-index"
        )
        
        assert config.backend == VectorBackend.PINECONE
        assert config.pinecone_api_key == "test-key"
        assert config.pinecone_environment == "us-west1-gcp"
        assert config.pinecone_index_name == "test-index"
    
    def test_chroma_config(self):
        """Test ChromaDB-specific configuration."""
        config = VectorConfig(
            backend=VectorBackend.CHROMA,
            chroma_host="remote-host",
            chroma_port=9000,
            chroma_collection_name="test_collection"
        )
        
        assert config.backend == VectorBackend.CHROMA
        assert config.chroma_host == "remote-host"
        assert config.chroma_port == 9000
        assert config.chroma_collection_name == "test_collection"


class TestContentEmbedding:
    """Test ContentEmbedding model."""
    
    def test_valid_content_embedding(self):
        """Test creating valid content embedding."""
        course_id = uuid4()
        embedding = ContentEmbedding(
            id="test-content",
            content_type=ContentType.COURSE,
            course_id=course_id,
            title="Test Course",
            text="This is test content for the course.",
            metadata={"difficulty": "beginner"}
        )
        
        assert embedding.id == "test-content"
        assert embedding.content_type == ContentType.COURSE
        assert embedding.course_id == course_id
        assert embedding.title == "Test Course"
        assert embedding.text == "This is test content for the course."
        assert embedding.metadata["difficulty"] == "beginner"
        assert isinstance(embedding.created_at, datetime)
    
    def test_embedding_with_vector(self):
        """Test content embedding with vector data."""
        embedding_vector = [0.1, 0.2, 0.3] * 512  # 1536 dimensions
        
        embedding = ContentEmbedding(
            id="test-content",
            content_type=ContentType.CONCEPT,
            course_id=uuid4(),
            title="Test Concept",
            text="Test concept content",
            embedding=embedding_vector
        )
        
        assert embedding.embedding == embedding_vector
        assert len(embedding.embedding) == 1536
    
    def test_different_content_types(self):
        """Test different content types."""
        course_id = uuid4()
        
        for content_type in ContentType:
            embedding = ContentEmbedding(
                id=f"test-{content_type.value}",
                content_type=content_type,
                course_id=course_id,
                title=f"Test {content_type.value}",
                text=f"Content for {content_type.value}"
            )
            assert embedding.content_type == content_type


class TestVectorSearchQuery:
    """Test VectorSearchQuery model."""
    
    def test_query_with_text(self):
        """Test query with text input."""
        query = VectorSearchQuery(query_text="machine learning")
        
        assert query.query_text == "machine learning"
        assert query.query_embedding is None
        assert query.limit == 10
        assert query.min_similarity == 0.7
    
    def test_query_with_embedding(self):
        """Test query with embedding vector."""
        embedding = [0.1] * 1536
        query = VectorSearchQuery(query_embedding=embedding)
        
        assert query.query_embedding == embedding
        assert query.query_text is None
    
    def test_query_with_filters(self):
        """Test query with filters."""
        course_ids = [uuid4(), uuid4()]
        content_types = [ContentType.COURSE, ContentType.CHAPTER]
        
        query = VectorSearchQuery(
            query_text="test query",
            course_ids=course_ids,
            content_types=content_types,
            metadata_filters={"difficulty": "intermediate"},
            limit=20,
            min_similarity=0.8
        )
        
        assert query.course_ids == course_ids
        assert query.content_types == content_types
        assert query.metadata_filters["difficulty"] == "intermediate"
        assert query.limit == 20
        assert query.min_similarity == 0.8
    
    def test_query_validation_requires_input(self):
        """Test that query requires either text or embedding."""
        with pytest.raises(ValueError, match="Either query_text or query_embedding must be provided"):
            VectorSearchQuery()
    
    def test_query_limit_validation(self):
        """Test query limit validation."""
        # Valid limits
        query1 = VectorSearchQuery(query_text="test", limit=1)
        assert query1.limit == 1
        
        query2 = VectorSearchQuery(query_text="test", limit=100)
        assert query2.limit == 100
        
        # Invalid limits should be handled by Pydantic
        with pytest.raises(ValueError):
            VectorSearchQuery(query_text="test", limit=0)
        
        with pytest.raises(ValueError):
            VectorSearchQuery(query_text="test", limit=101)
    
    def test_similarity_threshold_validation(self):
        """Test similarity threshold validation."""
        # Valid thresholds
        query1 = VectorSearchQuery(query_text="test", min_similarity=0.0)
        assert query1.min_similarity == 0.0
        
        query2 = VectorSearchQuery(query_text="test", min_similarity=1.0)
        assert query2.min_similarity == 1.0
        
        # Invalid thresholds
        with pytest.raises(ValueError):
            VectorSearchQuery(query_text="test", min_similarity=-0.1)
        
        with pytest.raises(ValueError):
            VectorSearchQuery(query_text="test", min_similarity=1.1)


class TestSimilarityResult:
    """Test SimilarityResult model."""
    
    def test_valid_similarity_result(self):
        """Test creating valid similarity result."""
        content = ContentEmbedding(
            id="test-content",
            content_type=ContentType.CONCEPT,
            course_id=uuid4(),
            title="Test Concept",
            text="Test content"
        )
        
        result = SimilarityResult(
            content=content,
            similarity_score=0.85,
            distance=0.15
        )
        
        assert result.content == content
        assert result.similarity_score == 0.85
        assert result.distance == 0.15
    
    def test_similarity_score_validation(self):
        """Test similarity score validation."""
        content = ContentEmbedding(
            id="test",
            content_type=ContentType.CONCEPT,
            course_id=uuid4(),
            title="Test",
            text="Test"
        )
        
        # Valid scores
        result1 = SimilarityResult(content=content, similarity_score=0.0, distance=1.0)
        assert result1.similarity_score == 0.0
        
        result2 = SimilarityResult(content=content, similarity_score=1.0, distance=0.0)
        assert result2.similarity_score == 1.0
        
        # Invalid scores
        with pytest.raises(ValueError):
            SimilarityResult(content=content, similarity_score=-0.1, distance=0.0)
        
        with pytest.raises(ValueError):
            SimilarityResult(content=content, similarity_score=1.1, distance=0.0)


class TestVectorDatabaseClient:
    """Test VectorDatabaseClient main interface."""
    
    def test_client_initialization(self):
        """Test client initialization with different backends."""
        # Chroma client
        chroma_config = VectorConfig(backend=VectorBackend.CHROMA)
        chroma_client = VectorDatabaseClient(chroma_config)
        
        assert chroma_client.config.backend == VectorBackend.CHROMA
        assert isinstance(chroma_client._client, ChromaVectorClient)
        
        # Pinecone client
        pinecone_config = VectorConfig(
            backend=VectorBackend.PINECONE,
            pinecone_api_key="test-key",
            pinecone_environment="test-env"
        )
        pinecone_client = VectorDatabaseClient(pinecone_config)
        
        assert pinecone_client.config.backend == VectorBackend.PINECONE
        assert isinstance(pinecone_client._client, PineconeVectorClient)
    
    def test_invalid_backend(self):
        """Test invalid backend handling."""
        with pytest.raises(ValueError, match="Unsupported vector backend"):
            config = VectorConfig(backend="invalid")  # This should fail at enum level
    
    @pytest.mark.asyncio
    async def test_store_course_embeddings_validation(self):
        """Test store_course_embeddings input validation."""
        config = VectorConfig(backend=VectorBackend.CHROMA)
        client = VectorDatabaseClient(config)
        
        course_id = uuid4()
        content_data = [{"id": "test", "title": "Test", "text": "Test content"}]
        embeddings = [[0.1] * 1536, [0.2] * 1536]  # Mismatched lengths
        
        # Should raise error for mismatched lengths
        with pytest.raises(ValueError, match="Content data and embeddings lists must have same length"):
            await client.store_course_embeddings(course_id, content_data, embeddings)
    
    @pytest.mark.asyncio
    async def test_operations_without_client(self):
        """Test operations when client is not initialized."""
        config = VectorConfig(backend=VectorBackend.CHROMA)
        client = VectorDatabaseClient(config)
        client._client = None  # Simulate uninitialized client
        
        with pytest.raises(VectorDatabaseError, match="Client not initialized"):
            await client.search_similar_content(query_text="test")
        
        with pytest.raises(VectorDatabaseError, match="Client not initialized"):
            await client.get_related_concepts("test concept")
        
        with pytest.raises(VectorDatabaseError, match="Client not initialized"):
            await client.delete_course_vectors(uuid4())


class TestVectorClientFactory:
    """Test vector client factory function."""
    
    def test_create_chroma_client(self):
        """Test creating ChromaDB client."""
        client = create_vector_client(
            backend="chroma",
            chroma_host="test-host",
            chroma_port=9000
        )
        
        assert client.config.backend == VectorBackend.CHROMA
        assert client.config.chroma_host == "test-host"
        assert client.config.chroma_port == 9000
    
    def test_create_pinecone_client(self):
        """Test creating Pinecone client."""
        client = create_vector_client(
            backend="pinecone",
            pinecone_api_key="test-key",
            pinecone_environment="test-env",
            pinecone_index_name="test-index"
        )
        
        assert client.config.backend == VectorBackend.PINECONE
        assert client.config.pinecone_api_key == "test-key"
        assert client.config.pinecone_environment == "test-env"
        assert client.config.pinecone_index_name == "test-index"
    
    def test_create_client_with_extra_params(self):
        """Test creating client with additional parameters."""
        client = create_vector_client(
            backend="chroma",
            connection_pool_size=20,
            max_retries=5,
            timeout_seconds=60
        )
        
        assert client.config.connection_pool_size == 20
        assert client.config.max_retries == 5
        assert client.config.timeout_seconds == 60
    
    def test_invalid_backend_factory(self):
        """Test factory with invalid backend."""
        with pytest.raises(ValueError):
            create_vector_client(backend="invalid_backend")


class TestVectorConfigValidation:
    """Test vector configuration validation."""
    
    def test_validate_valid_config(self):
        """Test validation of valid configurations."""
        from src.integrations.config import validate_vector_config
        
        # Valid Chroma config
        chroma_config = VectorConfig(backend=VectorBackend.CHROMA)
        assert validate_vector_config(chroma_config) is True
        
        # Valid Pinecone config
        pinecone_config = VectorConfig(
            backend=VectorBackend.PINECONE,
            pinecone_api_key="test-key",
            pinecone_environment="test-env"
        )
        assert validate_vector_config(pinecone_config) is True
    
    def test_validate_invalid_pinecone_config(self):
        """Test validation of invalid Pinecone config."""
        from src.integrations.config import validate_vector_config
        
        # Missing API key
        config1 = VectorConfig(
            backend=VectorBackend.PINECONE,
            pinecone_environment="test-env"
        )
        assert validate_vector_config(config1) is False
        
        # Missing environment
        config2 = VectorConfig(
            backend=VectorBackend.PINECONE,
            pinecone_api_key="test-key"
        )
        assert validate_vector_config(config2) is False
    
    def test_validate_invalid_dimensions(self):
        """Test validation of invalid dimensions."""
        from src.integrations.config import validate_vector_config
        
        config = VectorConfig(
            backend=VectorBackend.CHROMA,
            embedding_dimension=0
        )
        assert validate_vector_config(config) is False
        
        config.embedding_dimension = -100
        assert validate_vector_config(config) is False
    
    def test_validate_invalid_pool_size(self):
        """Test validation of invalid connection pool size."""
        from src.integrations.config import validate_vector_config
        
        config = VectorConfig(
            backend=VectorBackend.CHROMA,
            connection_pool_size=0
        )
        assert validate_vector_config(config) is False
    
    def test_validate_invalid_timeout(self):
        """Test validation of invalid timeout."""
        from src.integrations.config import validate_vector_config
        
        config = VectorConfig(
            backend=VectorBackend.CHROMA,
            timeout_seconds=0
        )
        assert validate_vector_config(config) is False


class TestVectorDatabaseSettings:
    """Test VectorDatabaseSettings configuration model."""
    
    def test_default_settings(self):
        """Test default settings values."""
        settings = VectorDatabaseSettings()
        
        assert settings.vector_backend == VectorBackend.CHROMA
        assert settings.chroma_host == "localhost"
        assert settings.chroma_port == 8000
        assert settings.embedding_dimension == 1536
        assert settings.connection_pool_size == 10
    
    def test_backend_validation(self):
        """Test backend string validation."""
        # Valid backend strings
        settings1 = VectorDatabaseSettings(vector_backend="chroma")
        assert settings1.vector_backend == VectorBackend.CHROMA
        
        settings2 = VectorDatabaseSettings(vector_backend="pinecone")
        assert settings2.vector_backend == VectorBackend.PINECONE
        
        # Invalid backend
        with pytest.raises(ValueError):
            VectorDatabaseSettings(vector_backend="invalid")
    
    def test_pinecone_validation(self):
        """Test Pinecone-specific validation."""
        # Should require API key for Pinecone
        with pytest.raises(ValueError, match="Pinecone API key is required"):
            VectorDatabaseSettings(
                vector_backend=VectorBackend.PINECONE,
                pinecone_api_key=None
            )
        
        # Valid Pinecone config
        settings = VectorDatabaseSettings(
            vector_backend=VectorBackend.PINECONE,
            pinecone_api_key="test-key",
            pinecone_environment="test-env"
        )
        assert settings.pinecone_api_key == "test-key"
    
    def test_to_vector_config(self):
        """Test conversion to VectorConfig."""
        settings = VectorDatabaseSettings(
            vector_backend=VectorBackend.CHROMA,
            chroma_host="test-host",
            chroma_port=9000,
            connection_pool_size=15
        )
        
        config = settings.to_vector_config()
        
        assert isinstance(config, VectorConfig)
        assert config.backend == VectorBackend.CHROMA
        assert config.chroma_host == "test-host"
        assert config.chroma_port == 9000
        assert config.connection_pool_size == 15
    
    def test_connection_pool_validation(self):
        """Test connection pool size validation."""
        # Valid range
        settings1 = VectorDatabaseSettings(connection_pool_size=1)
        assert settings1.connection_pool_size == 1
        
        settings2 = VectorDatabaseSettings(connection_pool_size=50)
        assert settings2.connection_pool_size == 50
        
        # Invalid range
        with pytest.raises(ValueError):
            VectorDatabaseSettings(connection_pool_size=0)
        
        with pytest.raises(ValueError):
            VectorDatabaseSettings(connection_pool_size=51)
    
    def test_timeout_validation(self):
        """Test timeout validation."""
        # Valid range
        settings1 = VectorDatabaseSettings(timeout_seconds=5)
        assert settings1.timeout_seconds == 5
        
        settings2 = VectorDatabaseSettings(timeout_seconds=300)
        assert settings2.timeout_seconds == 300
        
        # Invalid range
        with pytest.raises(ValueError):
            VectorDatabaseSettings(timeout_seconds=4)
        
        with pytest.raises(ValueError):
            VectorDatabaseSettings(timeout_seconds=301)


class TestPresetConfigurations:
    """Test preset configuration objects."""
    
    def test_chroma_local_config(self):
        """Test local ChromaDB configuration."""
        config = CHROMA_LOCAL_CONFIG
        
        assert config.backend == VectorBackend.CHROMA
        assert config.chroma_host == "localhost"
        assert config.chroma_port == 8000
        assert config.chroma_collection_name == "course_embeddings"
    
    def test_environment_settings(self):
        """Test environment-specific settings."""
        # This test depends on mocking environment variables
        with patch.dict('os.environ', {'ENVIRONMENT': 'test'}):
            settings = get_environment_settings()
            assert settings.chroma_collection_name == "test_course_embeddings"
        
        with patch.dict('os.environ', {'ENVIRONMENT': 'development'}):
            settings = get_environment_settings()
            assert settings.chroma_collection_name == "dev_course_embeddings"