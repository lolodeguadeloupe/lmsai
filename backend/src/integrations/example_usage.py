"""
Example usage of the vector database client for course content embeddings.

This script demonstrates how to:
1. Set up and configure the vector client
2. Store course content with embeddings
3. Perform similarity searches
4. Find related concepts
5. Update and delete content
"""

import asyncio
import json
from datetime import datetime
from uuid import uuid4
from typing import List

from vector_client import (
    VectorDatabaseClient,
    create_vector_client,
    ContentType,
    VectorSearchQuery
)
from config import get_environment_settings


# Mock embedding service for demonstration
class MockEmbeddingService:
    """Simple mock embedding service for demo purposes."""
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate deterministic embeddings based on text content."""
        embeddings = []
        for text in texts:
            # Create a simple hash-based embedding
            text_hash = hash(text.lower())
            base_value = (text_hash % 10000) / 10000.0
            
            # Create 1536-dimensional embedding
            embedding = []
            for i in range(1536):
                value = base_value + (i * 0.0001) + (len(text) * 0.00001)
                embedding.append(value % 1.0)
            
            embeddings.append(embedding)
        
        return embeddings


async def demonstrate_vector_client():
    """Demonstrate vector client functionality."""
    
    print("🚀 Vector Database Client Demo")
    print("=" * 50)
    
    # 1. Setup and configuration
    print("\n1. Setting up vector client...")
    
    # Get configuration from environment
    settings = get_environment_settings()
    config = settings.to_vector_config()
    
    print(f"   Backend: {config.backend.value}")
    if config.backend.value == "chroma":
        print(f"   Host: {config.chroma_host}:{config.chroma_port}")
        print(f"   Collection: {config.chroma_collection_name}")
    
    # Create client
    client = VectorDatabaseClient(config)
    embedding_service = MockEmbeddingService()
    
    # 2. Connect to database
    print("\n2. Connecting to vector database...")
    try:
        await client.connect()
        print("   ✅ Connected successfully")
        
        # Health check
        health = await client.health_check()
        print(f"   Health status: {health['status']}")
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return
    
    # 3. Prepare sample course content
    print("\n3. Preparing sample course content...")
    
    course_id = uuid4()
    print(f"   Course ID: {course_id}")
    
    # Sample course content
    course_content = [
        {
            "id": f"course-{course_id}",
            "content_type": "course",
            "title": "Introduction to Machine Learning",
            "text": "Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn and make decisions from data.",
            "metadata": {
                "difficulty": "beginner",
                "estimated_duration": "20 hours",
                "subject": "Computer Science"
            }
        },
        {
            "id": f"chapter-1-{course_id}",
            "content_type": "chapter",
            "title": "What is Machine Learning?",
            "text": "Machine learning involves creating algorithms that can automatically learn and improve from experience without being explicitly programmed for every scenario.",
            "metadata": {
                "chapter_number": 1,
                "learning_objectives": ["Understand ML definition", "Identify ML applications"]
            }
        },
        {
            "id": f"concept-supervised-{course_id}",
            "content_type": "concept", 
            "title": "Supervised Learning",
            "text": "Supervised learning is a type of machine learning where algorithms learn from labeled training data to make predictions on new, unseen data.",
            "metadata": {
                "concept_category": "learning_types",
                "difficulty": "intermediate"
            }
        },
        {
            "id": f"concept-unsupervised-{course_id}",
            "content_type": "concept",
            "title": "Unsupervised Learning", 
            "text": "Unsupervised learning finds hidden patterns in data without labeled examples, including clustering and dimensionality reduction techniques.",
            "metadata": {
                "concept_category": "learning_types",
                "difficulty": "advanced"
            }
        },
        {
            "id": f"concept-neural-networks-{course_id}",
            "content_type": "concept",
            "title": "Neural Networks",
            "text": "Neural networks are computing systems inspired by biological neural networks, consisting of interconnected nodes that process information.",
            "metadata": {
                "concept_category": "algorithms",
                "difficulty": "advanced"
            }
        }
    ]
    
    print(f"   Created {len(course_content)} content items")
    
    # 4. Generate embeddings
    print("\n4. Generating embeddings...")
    texts = [content["text"] for content in course_content]
    embeddings = embedding_service.generate_embeddings(texts)
    print(f"   Generated embeddings: {len(embeddings)} x {len(embeddings[0])} dimensions")
    
    # 5. Store content in vector database
    print("\n5. Storing content in vector database...")
    try:
        success = await client.store_course_embeddings(
            course_id=course_id,
            content_data=course_content,
            embeddings=embeddings
        )
        
        if success:
            print("   ✅ Content stored successfully")
        else:
            print("   ❌ Failed to store content")
            return
            
    except Exception as e:
        print(f"   ❌ Storage error: {e}")
        return
    
    # Wait for indexing
    print("   Waiting for indexing...")
    await asyncio.sleep(2)
    
    # 6. Perform similarity searches
    print("\n6. Performing similarity searches...")
    
    # Search for content related to "learning algorithms"
    search_queries = [
        "learning algorithms and data patterns",
        "neural networks and deep learning",
        "supervised machine learning techniques"
    ]
    
    for i, query_text in enumerate(search_queries, 1):
        print(f"\n   Query {i}: '{query_text}'")
        
        try:
            # Generate query embedding
            query_embedding = embedding_service.generate_embeddings([query_text])[0]
            
            # Search for similar content
            results = await client.search_similar_content(
                query_embedding=query_embedding,
                course_ids=[course_id],
                limit=3,
                min_similarity=0.1  # Low threshold for demo
            )
            
            print(f"   Found {len(results)} similar items:")
            
            for j, result in enumerate(results, 1):
                content = result.content
                print(f"     {j}. {content.title}")
                print(f"        Type: {content.content_type.value}")
                print(f"        Similarity: {result.similarity_score:.3f}")
                print(f"        Text: {content.text[:100]}...")
                
        except Exception as e:
            print(f"   ❌ Search error: {e}")
    
    # 7. Find related concepts
    print("\n7. Finding related concepts...")
    
    try:
        related_concepts = await client.get_related_concepts(
            concept_text="supervised learning with labeled data",
            course_id=course_id,
            limit=3
        )
        
        print(f"   Found {len(related_concepts)} related concepts:")
        
        for i, concept in enumerate(related_concepts, 1):
            print(f"     {i}. {concept.content.title}")
            print(f"        Similarity: {concept.similarity_score:.3f}")
            print(f"        Category: {concept.content.metadata.get('concept_category', 'N/A')}")
            
    except Exception as e:
        print(f"   ❌ Related concepts error: {e}")
    
    # 8. Content filtering by type
    print("\n8. Testing content filtering...")
    
    try:
        # Search only for concepts
        query_embedding = embedding_service.generate_embeddings(["machine learning concepts"])[0]
        
        concept_results = await client.search_similar_content(
            query_embedding=query_embedding,
            course_ids=[course_id],
            content_types=["concept"],
            limit=5,
            min_similarity=0.1
        )
        
        print(f"   Found {len(concept_results)} concepts:")
        for result in concept_results:
            print(f"     - {result.content.title} (type: {result.content.content_type.value})")
            
    except Exception as e:
        print(f"   ❌ Filtering error: {e}")
    
    # 9. Update content
    print("\n9. Updating content...")
    
    try:
        # Update the neural networks concept with more information
        updated_text = "Neural networks are deep learning models inspired by the human brain, consisting of layers of interconnected nodes that can learn complex patterns in data through backpropagation."
        updated_embedding = embedding_service.generate_embeddings([updated_text])[0]
        updated_metadata = {
            "concept_category": "algorithms",
            "difficulty": "advanced",
            "last_updated": datetime.utcnow().isoformat(),
            "version": 2
        }
        
        update_success = await client.update_content_vectors([
            (f"concept-neural-networks-{course_id}", updated_embedding, updated_metadata)
        ])
        
        if update_success:
            print("   ✅ Content updated successfully")
            
            # Verify update
            updated_content = await client.get_content_by_id(f"concept-neural-networks-{course_id}")
            if updated_content and "version" in updated_content.metadata:
                print(f"   Updated version: {updated_content.metadata['version']}")
        else:
            print("   ❌ Update failed")
            
    except Exception as e:
        print(f"   ❌ Update error: {e}")
    
    # 10. Content retrieval
    print("\n10. Testing content retrieval...")
    
    try:
        content_id = f"concept-supervised-{course_id}"
        retrieved_content = await client.get_content_by_id(content_id)
        
        if retrieved_content:
            print(f"   ✅ Retrieved: {retrieved_content.title}")
            print(f"   Content type: {retrieved_content.content_type.value}")
            print(f"   Metadata keys: {list(retrieved_content.metadata.keys())}")
        else:
            print(f"   ❌ Content not found: {content_id}")
            
    except Exception as e:
        print(f"   ❌ Retrieval error: {e}")
    
    # 11. Performance and statistics
    print("\n11. Performance statistics...")
    
    try:
        health = await client.health_check()
        print(f"   Backend: {health.get('backend', 'Unknown')}")
        print(f"   Status: {health.get('status', 'Unknown')}")
        if 'response_time_seconds' in health:
            print(f"   Response time: {health['response_time_seconds']:.3f}s")
        if 'test_results_count' in health:
            print(f"   Test results: {health['test_results_count']}")
            
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    # 12. Cleanup
    print("\n12. Cleaning up...")
    
    try:
        cleanup_success = await client.delete_course_vectors(course_id)
        
        if cleanup_success:
            print("   ✅ Course content deleted successfully")
        else:
            print("   ❌ Cleanup failed")
            
    except Exception as e:
        print(f"   ❌ Cleanup error: {e}")
    
    # 13. Disconnect
    print("\n13. Disconnecting...")
    
    try:
        await client.disconnect()
        print("   ✅ Disconnected successfully")
        
    except Exception as e:
        print(f"   ❌ Disconnect error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Demo completed!")


if __name__ == "__main__":
    print("Vector Database Client Demo")
    print("This demo requires a running vector database instance.")
    print("For ChromaDB, run: docker run -p 8000:8000 chromadb/chroma")
    print("For Pinecone, set VECTOR_PINECONE_API_KEY and VECTOR_PINECONE_ENVIRONMENT")
    print()
    
    # Run the demo
    asyncio.run(demonstrate_vector_client())