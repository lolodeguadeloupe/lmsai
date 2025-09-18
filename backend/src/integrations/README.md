# Vector Database Integration

This module provides a unified interface for vector database operations supporting both Pinecone and ChromaDB backends for the course generation platform.

## Features

- **Dual Backend Support**: Seamlessly switch between Pinecone and ChromaDB
- **Course Content Embeddings**: Store and search course content with semantic similarity
- **Comprehensive Search**: Filter by content type, course, and metadata
- **Related Concepts**: Discover conceptual relationships within courses
- **Async Operations**: Full async/await support with connection pooling
- **Production Ready**: Error handling, retries, and configuration validation

## Quick Start

```python
from integrations.vector_client import create_vector_client

# Create ChromaDB client
client = create_vector_client(
    backend="chroma",
    chroma_host="localhost",
    chroma_port=8000
)

# Create Pinecone client
client = create_vector_client(
    backend="pinecone",
    pinecone_api_key="your-api-key",
    pinecone_environment="us-west1-gcp"
)

# Connect and use
await client.connect()

# Store course content
await client.store_course_embeddings(
    course_id=course_id,
    content_data=content_list,
    embeddings=embedding_vectors
)

# Search similar content
results = await client.search_similar_content(
    query_text="machine learning concepts",
    course_ids=[course_id],
    content_types=["concept"],
    limit=10
)

await client.disconnect()
```

## Configuration

### Environment Variables

```bash
# Backend selection
VECTOR_BACKEND=chroma  # or pinecone

# ChromaDB settings
VECTOR_CHROMA_HOST=localhost
VECTOR_CHROMA_PORT=8000
VECTOR_CHROMA_COLLECTION_NAME=course_embeddings

# Pinecone settings (required for Pinecone backend)
VECTOR_PINECONE_API_KEY=your-api-key
VECTOR_PINECONE_ENVIRONMENT=us-west1-gcp
VECTOR_PINECONE_INDEX_NAME=course-embeddings

# General settings
VECTOR_EMBEDDING_DIMENSION=1536
VECTOR_CONNECTION_POOL_SIZE=10
VECTOR_MAX_RETRIES=3
VECTOR_TIMEOUT_SECONDS=30
```

### Programmatic Configuration

```python
from integrations.config import VectorDatabaseSettings, get_environment_settings

# From environment
settings = get_environment_settings()
client = VectorDatabaseClient(settings.to_vector_config())

# Manual configuration
settings = VectorDatabaseSettings(
    vector_backend="chroma",
    chroma_host="remote-host",
    chroma_port=8000
)
```

## Core Methods

### Storage Operations

- `store_course_embeddings()` - Store course content with embeddings
- `update_content_vectors()` - Update existing content vectors and metadata
- `delete_course_vectors()` - Remove all content for a course

### Search Operations

- `search_similar_content()` - Semantic similarity search
- `get_related_concepts()` - Find related concepts within a course
- `get_content_by_id()` - Retrieve specific content

### Management Operations

- `connect()` / `disconnect()` - Connection lifecycle
- `health_check()` - Database health and performance metrics

## Content Types

Supported content types for course embeddings:

- `course` - Course-level content and descriptions
- `chapter` - Chapter content and objectives
- `subchapter` - Section-level content
- `concept` - Individual concepts and definitions
- `question` - Assessment questions
- `flashcard` - Flashcard content for spaced repetition

## Example: Course Content Workflow

```python
import asyncio
from uuid import uuid4
from integrations.vector_client import create_vector_client

async def course_embedding_workflow():
    # Setup
    client = create_vector_client(backend="chroma")
    await client.connect()
    
    course_id = uuid4()
    
    # Prepare content
    content_data = [
        {
            "id": f"course-{course_id}",
            "content_type": "course",
            "title": "Introduction to Machine Learning",
            "text": "Comprehensive course on ML fundamentals...",
            "metadata": {"difficulty": "beginner"}
        },
        {
            "id": f"concept-supervised-{course_id}",
            "content_type": "concept",
            "title": "Supervised Learning",
            "text": "Learning with labeled training data...",
            "metadata": {"category": "learning_types"}
        }
    ]
    
    # Generate embeddings (use your embedding service)
    embeddings = generate_embeddings([item["text"] for item in content_data])
    
    # Store in vector database
    await client.store_course_embeddings(course_id, content_data, embeddings)
    
    # Search for related content
    results = await client.search_similar_content(
        query_text="machine learning algorithms",
        course_ids=[course_id],
        limit=5
    )
    
    for result in results:
        print(f"Found: {result.content.title} (similarity: {result.similarity_score:.3f})")
    
    # Find related concepts
    related = await client.get_related_concepts(
        concept_text="supervised learning",
        course_id=course_id
    )
    
    # Cleanup
    await client.delete_course_vectors(course_id)
    await client.disconnect()

# Run the workflow
asyncio.run(course_embedding_workflow())
```

## Testing

Run the contract tests to verify both backend implementations:

```bash
# Contract tests (requires running databases)
pytest tests/contract/test_vector_client_contract.py

# Integration tests
pytest tests/integration/test_vector_client_integration.py

# Unit tests (no dependencies)
pytest tests/unit/test_vector_client_unit.py
```

## Deployment

### ChromaDB Setup

```bash
# Docker
docker run -p 8000:8000 chromadb/chroma

# Or with docker compose
version: '3.8'
services:
  chroma:
    image: chromadb/chroma
    ports:
      - "8000:8000"
```

### Pinecone Setup

1. Create account at [Pinecone](https://pinecone.io)
2. Create an index with cosine similarity metric
3. Set environment variables for API key and environment

## Performance Considerations

- **Batch Operations**: Store embeddings in batches for better performance
- **Connection Pooling**: Configure appropriate pool size for your workload
- **Indexing Time**: Allow time for content indexing before searching
- **Embedding Dimensions**: Use consistent dimensions (default: 1536 for OpenAI)

## Error Handling

The client provides comprehensive error handling:

- `VectorDatabaseError` - Base exception for all operations
- `ConnectionError` - Database connection issues
- `EmbeddingError` - Embedding-related errors
- `SearchError` - Search operation failures

## Security

- Store API keys securely using environment variables
- Use connection timeouts to prevent hanging operations
- Validate all input data before storage
- Consider encryption for sensitive course content