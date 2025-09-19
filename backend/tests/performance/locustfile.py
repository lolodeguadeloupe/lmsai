"""
Locust load testing configuration for the course generation platform.
Run with: locust -f locustfile.py --host=http://localhost:8000
"""
import random
import uuid
from locust import HttpUser, task, between


class CourseGenerationUser(HttpUser):
    """Simulates a typical user of the course generation platform."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when a user starts - setup user data."""
        self.course_ids = []
        self.user_id = str(uuid.uuid4())
        
        # Sample course data for creation
        self.sample_courses = [
            {
                "title": f"Introduction to Python Programming - User {self.user_id[:8]}",
                "description": "Comprehensive Python course for beginners",
                "subject_domain": "COMPUTER_SCIENCE",
                "target_audience": "BEGINNER",
                "difficulty_level": "EASY",
                "estimated_duration_hours": 20,
                "learning_objectives": [
                    "Learn Python basics",
                    "Understand data structures",
                    "Write simple programs"
                ]
            },
            {
                "title": f"Advanced Machine Learning - User {self.user_id[:8]}",
                "description": "Deep dive into ML algorithms and techniques",
                "subject_domain": "COMPUTER_SCIENCE", 
                "target_audience": "ADVANCED",
                "difficulty_level": "HARD",
                "estimated_duration_hours": 40,
                "learning_objectives": [
                    "Master ML algorithms",
                    "Implement neural networks",
                    "Build production ML systems"
                ]
            },
            {
                "title": f"Digital Marketing Fundamentals - User {self.user_id[:8]}",
                "description": "Learn the basics of digital marketing",
                "subject_domain": "BUSINESS",
                "target_audience": "BEGINNER",
                "difficulty_level": "EASY",
                "estimated_duration_hours": 15,
                "learning_objectives": [
                    "Understand digital marketing channels",
                    "Create marketing campaigns",
                    "Analyze marketing metrics"
                ]
            }
        ]
    
    @task(10)
    def health_check(self):
        """Health check endpoint - high frequency."""
        self.client.get("/api/v1/health")
    
    @task(8)
    def list_courses(self):
        """List courses - frequent operation."""
        params = {}
        
        # Randomly add filters
        if random.random() < 0.3:
            params["status"] = random.choice(["DRAFT", "GENERATING", "COMPLETED"])
        if random.random() < 0.2:
            params["subject_domain"] = random.choice(["COMPUTER_SCIENCE", "BUSINESS", "SCIENCE"])
        if random.random() < 0.4:
            params["page"] = random.randint(1, 5)
            params["limit"] = random.choice([10, 20, 50])
        
        self.client.get("/api/v1/courses/", params=params)
    
    @task(5)
    def get_api_info(self):
        """Get API info - moderate frequency."""
        self.client.get("/api/v1/info")
    
    @task(3)
    def create_course(self):
        """Create a new course - lower frequency."""
        course_data = random.choice(self.sample_courses).copy()
        
        # Make title unique
        course_data["title"] += f" - {random.randint(1000, 9999)}"
        
        with self.client.post("/api/v1/courses/", json=course_data, catch_response=True) as response:
            if response.status_code == 201:
                # Store course ID for later use
                course_id = response.json().get("id")
                if course_id:
                    self.course_ids.append(course_id)
                response.success()
            else:
                response.failure(f"Course creation failed: {response.status_code}")
    
    @task(6)
    def get_course_details(self):
        """Get course details - moderate frequency."""
        if self.course_ids:
            course_id = random.choice(self.course_ids)
            self.client.get(f"/api/v1/courses/{course_id}")
        else:
            # Use a sample course ID if none created yet
            sample_id = "550e8400-e29b-41d4-a716-446655440000"
            self.client.get(f"/api/v1/courses/{sample_id}")
    
    @task(4)
    def check_generation_status(self):
        """Check course generation status."""
        if self.course_ids:
            course_id = random.choice(self.course_ids)
            include_logs = random.choice([True, False])
            params = {"include_logs": include_logs}
            self.client.get(f"/api/v1/courses/{course_id}/generation-status", params=params)
        else:
            # Use a sample course ID
            sample_id = "550e8400-e29b-41d4-a716-446655440000"
            self.client.get(f"/api/v1/courses/{sample_id}/generation-status")
    
    @task(2)
    def update_course(self):
        """Update course - low frequency."""
        if self.course_ids:
            course_id = random.choice(self.course_ids)
            update_data = {
                "title": f"Updated Course - {random.randint(1000, 9999)}",
                "description": f"Updated description at {random.randint(1000, 9999)}"
            }
            self.client.put(f"/api/v1/courses/{course_id}", json=update_data)
    
    @task(3)
    def get_chapters(self):
        """Get course chapters."""
        if self.course_ids:
            course_id = random.choice(self.course_ids)
            self.client.get(f"/api/v1/courses/{course_id}/chapters")
        else:
            sample_id = "550e8400-e29b-41d4-a716-446655440000"
            self.client.get(f"/api/v1/courses/{sample_id}/chapters")
    
    @task(3)
    def get_quizzes(self):
        """Get course quizzes."""
        if self.course_ids:
            course_id = random.choice(self.course_ids)
            self.client.get(f"/api/v1/courses/{course_id}/quizzes")
        else:
            sample_id = "550e8400-e29b-41d4-a716-446655440000"
            self.client.get(f"/api/v1/courses/{sample_id}/quizzes")
    
    @task(1)
    def submit_quiz_attempt(self):
        """Submit a quiz attempt - low frequency."""
        if self.course_ids:
            course_id = random.choice(self.course_ids)
            quiz_id = str(uuid.uuid4())  # Random quiz ID
            
            attempt_data = {
                "answers": [
                    {
                        "question_id": f"q{i}",
                        "selected_options": [f"option{random.randint(1, 4)}"]
                    }
                    for i in range(random.randint(3, 8))
                ]
            }
            
            self.client.post(
                f"/api/v1/courses/{course_id}/quizzes/{quiz_id}/attempts",
                json=attempt_data
            )
    
    @task(1)
    def quality_analysis(self):
        """Run quality analysis - low frequency."""
        if self.course_ids:
            course_id = random.choice(self.course_ids)
            analysis_data = {
                "analysis_type": random.choice([
                    "content_quality", 
                    "readability", 
                    "engagement", 
                    "comprehensive"
                ])
            }
            self.client.post(
                f"/api/v1/courses/{course_id}/quality-analysis",
                json=analysis_data
            )
    
    @task(1)
    def export_course(self):
        """Export course - low frequency, resource intensive."""
        if self.course_ids:
            course_id = random.choice(self.course_ids)
            export_data = {
                "format": random.choice(["pdf", "docx", "html", "scorm"])
            }
            
            # Use longer timeout for exports
            with self.client.post(
                f"/api/v1/courses/{course_id}/export",
                json=export_data,
                timeout=30,
                catch_response=True
            ) as response:
                if response.status_code in [200, 202]:  # Accept both success and accepted
                    response.success()
                else:
                    response.failure(f"Export failed: {response.status_code}")


class PowerUser(CourseGenerationUser):
    """Power user that creates more courses and performs more operations."""
    
    wait_time = between(0.5, 2)  # Faster operations
    weight = 1  # Less common than regular users
    
    @task(5)
    def create_course(self):
        """Power users create more courses."""
        super().create_course()
    
    @task(3)
    def batch_operations(self):
        """Perform multiple operations in sequence."""
        # Create course
        course_data = random.choice(self.sample_courses).copy()
        course_data["title"] += f" - Batch {random.randint(1000, 9999)}"
        
        response = self.client.post("/api/v1/courses/", json=course_data)
        if response.status_code == 201:
            course_id = response.json().get("id")
            if course_id:
                # Immediately check status
                self.client.get(f"/api/v1/courses/{course_id}/generation-status")
                # Get details
                self.client.get(f"/api/v1/courses/{course_id}")
                # Update
                update_data = {"title": f"Batch Updated - {random.randint(1000, 9999)}"}
                self.client.put(f"/api/v1/courses/{course_id}", json=update_data)


class AdminUser(HttpUser):
    """Admin user performing system monitoring tasks."""
    
    wait_time = between(5, 10)  # Less frequent operations
    weight = 1  # Very few admin users
    
    @task(5)
    def system_health_monitoring(self):
        """Admin monitoring system health."""
        self.client.get("/api/v1/health")
        self.client.get("/api/v1/info")
    
    @task(3)
    def course_overview(self):
        """Admin getting overview of all courses."""
        # Get courses with different filters
        for status in ["DRAFT", "GENERATING", "COMPLETED", "FAILED"]:
            self.client.get("/api/v1/courses/", params={"status": status, "limit": 100})
    
    @task(2)
    def generation_monitoring(self):
        """Monitor course generation across system."""
        # Get list of courses first
        response = self.client.get("/api/v1/courses/", params={"limit": 50})
        if response.status_code == 200:
            courses = response.json().get("courses", [])
            
            # Check generation status for multiple courses
            for course in courses[:10]:  # Check first 10
                course_id = course.get("id")
                if course_id:
                    self.client.get(
                        f"/api/v1/courses/{course_id}/generation-status",
                        params={"include_logs": True}
                    )


# Configure user classes with weights
# 80% regular users, 15% power users, 5% admin users
CourseGenerationUser.weight = 8
PowerUser.weight = 2
AdminUser.weight = 1