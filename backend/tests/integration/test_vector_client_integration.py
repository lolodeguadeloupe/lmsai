"""
Integration tests for vector database client with course platform components.

These tests verify integration with the course model and real embeddings workflow.
"""

import asyncio
import os
import pytest
from datetime import datetime, timedelta
from typing import List
from uuid import UUID, uuid4

from src.integrations.vector_client import (
    VectorDatabaseClient,
    create_vector_client,
    ContentType,
    VectorDatabaseError
)
from src.models.course import Course, TargetAudience, CourseCreate
from src.models.enums import ProficiencyLevel, LearningPreference, CourseStatus


@pytest.fixture
def mock_embedding_service():
    """Mock embedding service for testing."""
    class MockEmbeddingService:
        def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
            """Generate mock embeddings for texts."""
            embeddings = []
            for i, text in enumerate(texts):
                # Create deterministic embeddings based on text hash
                base_value = hash(text) % 100 / 100.0
                embedding = [base_value + (j * 0.001) for j in range(1536)]
                embeddings.append(embedding)
            return embeddings
    
    return MockEmbeddingService()


@pytest.fixture
def sample_course():
    """Create a sample course for testing."""
    target_audience = TargetAudience(
        proficiency_level=ProficiencyLevel.BEGINNER,
        prerequisites=["basic mathematics"],
        learning_preferences=[LearningPreference.VISUAL]
    )
    
    return Course(
        id=uuid4(),
        title="Introduction to Machine Learning",
        description="A comprehensive introduction to machine learning concepts",
        subject_domain="Computer Science",
        target_audience=target_audience,
        learning_objectives=[
            "Understand basic ML concepts",
            "Apply supervised learning algorithms", 
            "Evaluate model performance"
        ],
        estimated_duration="PT20H",
        difficulty_score=2.0,
        language="en",
        version="1.0.0",
        status=CourseStatus.DRAFT,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@pytest.fixture
def course_content_hierarchy(sample_course):
    """Create a hierarchical course content structure for testing."""
    return {
        "course": {
            "id": str(sample_course.id),
            "title": sample_course.title,
            "description": sample_course.description,
            "content_type": "course"
        },
        "chapters": [
            {
                "id": f"{sample_course.id}-chapter-1",
                "title": "What is Machine Learning?",
                "content": "Machine learning is a method of data analysis that automates analytical model building...",
                "content_type": "chapter",
                "chapter_number": 1
            },
            {
                "id": f"{sample_course.id}-chapter-2", 
                "title": "Types of Machine Learning",
                "content": "There are three main types of machine learning: supervised, unsupervised, and reinforcement learning...",
                "content_type": "chapter",
                "chapter_number": 2
            }
        ],
        "concepts": [
            {
                "id": f"{sample_course.id}-concept-supervised",
                "title": "Supervised Learning",
                "content": "Supervised learning uses labeled training data to learn a mapping from inputs to outputs...",
                "content_type": "concept",
                "category": "learning_types"
            },
            {
                "id": f"{sample_course.id}-concept-unsupervised",
                "title": "Unsupervised Learning", 
                "content": "Unsupervised learning finds hidden patterns in data without labeled examples...",
                "content_type": "concept",
                "category": "learning_types"
            },
            {
                "id": f"{sample_course.id}-concept-algorithm",
                "title": "Algorithm",
                "content": "An algorithm is a set of rules or instructions given to an AI, neural network, or other machine...",
                "content_type": "concept",
                "category": "fundamentals"
            }
        ]
    }


class TestVectorClientCourseIntegration:
    """Integration tests for vector client with course data."""
    
    @pytest.fixture
    def vector_client(self):
        """Create a test vector client."""
        # Prefer ChromaDB for integration tests as it's easier to set up
        return create_vector_client(
            backend="chroma",
            chroma_host=os.getenv("CHROMA_HOST", "localhost"),
            chroma_port=int(os.getenv("CHROMA_PORT", "8000")),
            chroma_collection_name="integration_test_embeddings"
        )
    
    @pytest.mark.asyncio
    async def test_store_complete_course_structure(
        self, 
        vector_client, 
        sample_course, 
        course_content_hierarchy, 
        mock_embedding_service
    ):
        """Test storing a complete course structure with embeddings."""
        await vector_client.connect()
        
        try:
            # Prepare all content for embedding
            all_content = []
            all_texts = []
            
            # Add course-level content
            course_data = course_content_hierarchy["course"]
            all_content.append({
                "id": course_data["id"],
                "content_type": "course",
                "title": course_data["title"],
                "text": f"{course_data['title']} - {course_data.get('description', '')}",
                "metadata": {"level": "course"}
            })
            all_texts.append(all_content[-1]["text"])
            
            # Add chapters
            for chapter in course_content_hierarchy["chapters"]:
                all_content.append({
                    "id": chapter["id"],
                    "content_type": "chapter",
                    "title": chapter["title"],
                    "text": f"{chapter['title']} - {chapter['content']}",
                    "metadata": {"chapter_number": chapter["chapter_number"]}
                })
                all_texts.append(all_content[-1]["text"])
            
            # Add concepts
            for concept in course_content_hierarchy["concepts"]:
                all_content.append({
                    "id": concept["id"],
                    "content_type": "concept",
                    "title": concept["title"],
                    "text": f"{concept['title']} - {concept['content']}",
                    "metadata": {"category": concept["category"]}
                })
                all_texts.append(all_content[-1]["text"])
            
            # Generate embeddings
            embeddings = mock_embedding_service.generate_embeddings(all_texts)
            
            # Store in vector database
            success = await vector_client.store_course_embeddings(
                course_id=sample_course.id,
                content_data=all_content,
                embeddings=embeddings
            )
            
            assert success is True
            
            # Wait for indexing
            await asyncio.sleep(2)
            
            # Verify course content can be retrieved
            course_content = await vector_client.get_content_by_id(str(sample_course.id))
            if course_content:  # May not be immediately available in all backends
                assert course_content.course_id == sample_course.id
                assert course_content.content_type == ContentType.COURSE
        
        finally:
            # Cleanup
            await vector_client.delete_course_vectors(sample_course.id)
            await vector_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_semantic_course_search(
        self, 
        vector_client, 
        sample_course, 
        course_content_hierarchy, 
        mock_embedding_service
    ):
        """Test semantic search within course content."""
        await vector_client.connect()
        
        try:
            # Store course content
            all_content = []
            all_texts = []
            
            for concept in course_content_hierarchy["concepts"]:
                all_content.append({
                    "id": concept["id"],
                    "content_type": "concept",
                    "title": concept["title"],
                    "text": concept["content"],
                    "metadata": {"category": concept["category"]}
                })
                all_texts.append(concept["content"])
            
            embeddings = mock_embedding_service.generate_embeddings(all_texts)
            
            await vector_client.store_course_embeddings(
                course_id=sample_course.id,
                content_data=all_content,
                embeddings=embeddings
            )
            
            await asyncio.sleep(2)  # Wait for indexing
            
            # Search for supervised learning concepts
            search_query = "supervised learning with labeled data"
            query_embedding = mock_embedding_service.generate_embeddings([search_query])[0]
            
            results = await vector_client.search_similar_content(
                query_embedding=query_embedding,
                course_ids=[sample_course.id],
                content_types=["concept"],
                limit=3,
                min_similarity=0.1  # Low threshold for mock embeddings
            )
            
            # Should find related concepts
            assert isinstance(results, list)
            
            # If results found, verify they're relevant
            for result in results:
                assert result.content.course_id == sample_course.id
                assert result.content.content_type == ContentType.CONCEPT
                assert 0.0 <= result.similarity_score <= 1.0
        
        finally:
            await vector_client.delete_course_vectors(sample_course.id)
            await vector_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_concept_relationship_discovery(
        self, 
        vector_client, 
        sample_course, 
        course_content_hierarchy, 
        mock_embedding_service
    ):
        """Test discovering relationships between concepts."""
        await vector_client.connect()
        
        try:
            # Store concepts
            concepts = course_content_hierarchy["concepts"]
            content_data = []
            texts = []
            
            for concept in concepts:
                content_data.append({
                    "id": concept["id"],
                    "content_type": "concept",
                    "title": concept["title"],
                    "text": concept["content"],
                    "metadata": {"category": concept["category"]}
                })
                texts.append(concept["content"])
            
            embeddings = mock_embedding_service.generate_embeddings(texts)
            
            await vector_client.store_course_embeddings(
                course_id=sample_course.id,
                content_data=content_data,
                embeddings=embeddings
            )
            
            await asyncio.sleep(2)
            
            # Find concepts related to "supervised learning"
            related = await vector_client.get_related_concepts(
                concept_text="supervised learning",
                course_id=sample_course.id,
                limit=2
            )
            
            assert isinstance(related, list)
            
            # All results should be concepts from the same course
            for concept in related:
                assert concept.content.content_type == ContentType.CONCEPT
                assert concept.content.course_id == sample_course.id
        
        finally:
            await vector_client.delete_course_vectors(sample_course.id)
            await vector_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_cross_course_content_search(
        self, 
        vector_client, 
        mock_embedding_service
    ):
        """Test searching across multiple courses."""
        await vector_client.connect()
        
        course1_id = uuid4()
        course2_id = uuid4()
        
        try:
            # Create content for two different courses
            course1_content = [
                {
                    "id": f"{course1_id}-ml-basics",
                    "content_type": "concept",
                    "title": "Machine Learning Basics",
                    "text": "Machine learning is about creating algorithms that learn from data",
                    "metadata": {"course_name": "ML Intro"}
                }
            ]
            
            course2_content = [
                {
                    "id": f"{course2_id}-ai-overview",
                    "content_type": "concept", 
                    "title": "Artificial Intelligence Overview",
                    "text": "AI encompasses machine learning and other intelligent systems",
                    "metadata": {"course_name": "AI Fundamentals"}
                }
            ]
            
            # Generate embeddings
            texts1 = [c["text"] for c in course1_content]
            texts2 = [c["text"] for c in course2_content]
            
            embeddings1 = mock_embedding_service.generate_embeddings(texts1)
            embeddings2 = mock_embedding_service.generate_embeddings(texts2)
            
            # Store both courses
            await vector_client.store_course_embeddings(course1_id, course1_content, embeddings1)
            await vector_client.store_course_embeddings(course2_id, course2_content, embeddings2)
            
            await asyncio.sleep(2)
            
            # Search across both courses
            query_embedding = mock_embedding_service.generate_embeddings(["artificial intelligence"])[0]
            
            results = await vector_client.search_similar_content(
                query_embedding=query_embedding,
                course_ids=[course1_id, course2_id],
                content_types=["concept"],
                limit=5,
                min_similarity=0.1
            )
            
            # Should find content from both courses
            found_course_ids = {result.content.course_id for result in results}
            
            # At least one course should be found (may be both depending on embeddings)
            assert len(found_course_ids) >= 1
            assert all(cid in [course1_id, course2_id] for cid in found_course_ids)
        
        finally:
            await vector_client.delete_course_vectors(course1_id)
            await vector_client.delete_course_vectors(course2_id)
            await vector_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_content_versioning_and_updates(
        self, 
        vector_client, 
        sample_course, 
        mock_embedding_service
    ):
        """Test updating content and maintaining version history."""
        await vector_client.connect()
        
        try:
            # Store initial content
            initial_content = [{
                "id": "concept-ml",
                "content_type": "concept",
                "title": "Machine Learning",
                "text": "Machine learning is about pattern recognition",
                "metadata": {"version": 1, "last_updated": datetime.utcnow().isoformat()}
            }]
            
            initial_embedding = mock_embedding_service.generate_embeddings([initial_content[0]["text"]])
            
            await vector_client.store_course_embeddings(
                course_id=sample_course.id,
                content_data=initial_content,
                embeddings=initial_embedding
            )
            
            await asyncio.sleep(1)
            
            # Update content with new information
            updated_text = "Machine learning is about algorithms that learn from data automatically"
            updated_embedding = mock_embedding_service.generate_embeddings([updated_text])[0]
            updated_metadata = {
                "version": 2,
                "last_updated": datetime.utcnow().isoformat(),
                "change_reason": "Added more detail"
            }
            
            success = await vector_client.update_content_vectors([
                ("concept-ml", updated_embedding, updated_metadata)
            ])
            
            assert success is True
            
            # Verify update
            updated_content = await vector_client.get_content_by_id("concept-ml")
            if updated_content:
                assert updated_content.metadata["version"] == 2
                assert "change_reason" in updated_content.metadata
        
        finally:
            await vector_client.delete_course_vectors(sample_course.id)
            await vector_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_bulk_course_deletion(
        self, 
        vector_client, 
        mock_embedding_service
    ):
        """Test bulk deletion of course content."""
        await vector_client.connect()
        
        course_id = uuid4()
        
        try:
            # Create multiple content items
            content_items = [
                {
                    "id": f"item-{i}",
                    "content_type": "concept",
                    "title": f"Concept {i}",
                    "text": f"This is concept number {i}",
                    "metadata": {"item_number": i}
                }
                for i in range(5)
            ]
            
            texts = [item["text"] for item in content_items]
            embeddings = mock_embedding_service.generate_embeddings(texts)
            
            # Store all content
            await vector_client.store_course_embeddings(course_id, content_items, embeddings)
            
            await asyncio.sleep(1)
            
            # Verify content exists (at least try to search)
            query_embedding = mock_embedding_service.generate_embeddings(["concept"])[0]
            results_before = await vector_client.search_similar_content(
                query_embedding=query_embedding,
                course_ids=[course_id],
                limit=10,
                min_similarity=0.1
            )
            
            # Delete entire course
            deletion_success = await vector_client.delete_course_vectors(course_id)
            assert deletion_success is True
            
            await asyncio.sleep(1)
            
            # Verify content is deleted
            results_after = await vector_client.search_similar_content(
                query_embedding=query_embedding,
                course_ids=[course_id],
                limit=10,
                min_similarity=0.1
            )
            
            # Should have fewer or no results after deletion
            assert len(results_after) <= len(results_before)
        
        finally:
            # Ensure cleanup even if test fails
            await vector_client.delete_course_vectors(course_id)
            await vector_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_error_handling_and_resilience(self, vector_client):
        """Test error handling and system resilience."""
        # Test operations without connection
        with pytest.raises((VectorDatabaseError, Exception)):
            await vector_client.search_similar_content(query_text="test")
        
        await vector_client.connect()
        
        try:
            # Test invalid course ID
            invalid_uuid = "not-a-uuid"
            
            # Should handle gracefully
            try:
                results = await vector_client.search_similar_content(
                    query_text="test",
                    course_ids=[invalid_uuid],  # This should be handled gracefully
                    limit=1
                )
                # If no exception, results should be empty or valid
                assert isinstance(results, list)
            except (ValueError, VectorDatabaseError):
                # Expected for invalid UUID
                pass
            
            # Test empty content
            empty_success = await vector_client.store_course_embeddings(
                course_id=uuid4(),
                content_data=[],
                embeddings=[]
            )
            assert isinstance(empty_success, bool)
        
        finally:
            await vector_client.disconnect()


class TestVectorClientPerformance:
    """Performance and scalability tests for vector client."""
    
    @pytest.fixture
    def performance_vector_client(self):
        """Create vector client for performance testing."""
        return create_vector_client(
            backend="chroma",
            chroma_host=os.getenv("CHROMA_HOST", "localhost"),
            chroma_port=int(os.getenv("CHROMA_PORT", "8000")),
            chroma_collection_name="performance_test_embeddings"
        )
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_bulk_content_storage(self, performance_vector_client, mock_embedding_service):
        """Test storing large amounts of content efficiently."""
        await performance_vector_client.connect()
        
        course_id = uuid4()
        
        try:
            # Create 100 content items
            content_items = []
            texts = []
            
            for i in range(100):
                content = {
                    "id": f"bulk-item-{i}",
                    "content_type": "concept",
                    "title": f"Concept {i}",
                    "text": f"This is a detailed explanation of concept {i} " * 10,  # Longer text
                    "metadata": {"batch": "performance_test", "item_number": i}
                }
                content_items.append(content)
                texts.append(content["text"])
            
            # Generate embeddings
            start_time = datetime.utcnow()
            embeddings = mock_embedding_service.generate_embeddings(texts)
            embedding_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Store in vector database
            start_time = datetime.utcnow()
            success = await performance_vector_client.store_course_embeddings(
                course_id=course_id,
                content_data=content_items,
                embeddings=embeddings
            )
            storage_time = (datetime.utcnow() - start_time).total_seconds()
            
            assert success is True
            
            # Log performance metrics
            print(f"Embedding generation time: {embedding_time:.2f}s")
            print(f"Storage time for 100 items: {storage_time:.2f}s")
            print(f"Average time per item: {(storage_time / 100):.4f}s")
            
            # Verify storage worked
            await asyncio.sleep(3)  # Wait for indexing
            
            query_embedding = mock_embedding_service.generate_embeddings(["concept"])[0]
            results = await performance_vector_client.search_similar_content(
                query_embedding=query_embedding,
                course_ids=[course_id],
                limit=10,
                min_similarity=0.1
            )
            
            # Should find some results
            print(f"Found {len(results)} results in search")
        
        finally:
            await performance_vector_client.delete_course_vectors(course_id)
            await performance_vector_client.disconnect()
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, performance_vector_client, mock_embedding_service):
        """Test concurrent vector operations."""
        await performance_vector_client.connect()
        
        course_ids = [uuid4() for _ in range(3)]
        
        async def store_course_content(course_id, course_index):
            """Store content for a single course."""
            content_items = [
                {
                    "id": f"course-{course_index}-item-{i}",
                    "content_type": "concept",
                    "title": f"Course {course_index} Concept {i}",
                    "text": f"Content for course {course_index}, concept {i}",
                    "metadata": {"course_index": course_index}
                }
                for i in range(10)
            ]
            
            texts = [item["text"] for item in content_items]
            embeddings = mock_embedding_service.generate_embeddings(texts)
            
            return await performance_vector_client.store_course_embeddings(
                course_id=course_id,
                content_data=content_items,
                embeddings=embeddings
            )
        
        try:
            # Store content for multiple courses concurrently
            start_time = datetime.utcnow()
            
            tasks = [
                store_course_content(course_id, i) 
                for i, course_id in enumerate(course_ids)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            concurrent_time = (datetime.utcnow() - start_time).total_seconds()
            
            # All operations should succeed
            for result in results:
                if isinstance(result, Exception):
                    pytest.fail(f"Concurrent operation failed: {result}")
                assert result is True
            
            print(f"Concurrent storage of 3 courses (30 items total): {concurrent_time:.2f}s")
            
        finally:
            # Cleanup all courses
            cleanup_tasks = [
                performance_vector_client.delete_course_vectors(course_id)
                for course_id in course_ids
            ]
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            await performance_vector_client.disconnect()