# Code Examples and Usage Samples

## Quick Start Examples

### Python Examples

#### Basic Course Creation

```python
import requests
import time

# Configuration
API_KEY = "your-api-key-here"
BASE_URL = "https://api.courseplatform.com/v1"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Create a basic course
def create_basic_course():
    course_data = {
        "title": "Introduction to Python Programming",
        "description": "Learn Python programming from scratch",
        "subject_domain": "Computer Science",
        "target_audience": {
            "proficiency_level": "beginner",
            "prerequisites": ["Basic computer skills"],
            "learning_preferences": ["practical", "visual"]
        },
        "estimated_duration": "PT15H",
        "content_preferences": {
            "include_practical_examples": True,
            "theory_to_practice_ratio": 0.7
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/courses",
        json=course_data,
        headers=headers
    )
    
    if response.status_code == 201:
        return response.json()
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

# Monitor generation progress
def monitor_course_generation(course_id):
    while True:
        response = requests.get(
            f"{BASE_URL}/courses/{course_id}/generation-status",
            headers=headers
        )
        
        if response.status_code == 200:
            status = response.json()
            print(f"Progress: {status['progress_percentage']}% - {status['current_phase']}")
            
            if status['status'] == 'completed':
                print("Course generation completed!")
                return True
            elif status['status'] == 'failed':
                print(f"Generation failed: {status.get('error_message', 'Unknown error')}")
                return False
        
        time.sleep(30)  # Check every 30 seconds

# Usage
if __name__ == "__main__":
    course = create_basic_course()
    if course:
        print(f"Course created with ID: {course['id']}")
        success = monitor_course_generation(course['id'])
        if success:
            print("Course is ready for use!")
```

#### Complete Course Management

```python
import requests
from datetime import datetime
import json

class CourseManager:
    def __init__(self, api_key, base_url="https://api.courseplatform.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def create_course(self, title, description, subject_domain, target_audience, **kwargs):
        """Create a new course with specified parameters"""
        course_data = {
            "title": title,
            "description": description,
            "subject_domain": subject_domain,
            "target_audience": target_audience,
            **kwargs
        }
        
        response = requests.post(
            f"{self.base_url}/courses",
            json=course_data,
            headers=self.headers
        )
        
        if response.status_code == 201:
            return response.json()
        else:
            raise Exception(f"Failed to create course: {response.text}")
    
    def list_courses(self, status=None, limit=20, offset=0):
        """List courses with optional filtering"""
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
        
        response = requests.get(
            f"{self.base_url}/courses",
            headers=self.headers,
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to list courses: {response.text}")
    
    def get_course(self, course_id):
        """Get detailed course information"""
        response = requests.get(
            f"{self.base_url}/courses/{course_id}",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            raise ValueError(f"Course {course_id} not found")
        else:
            raise Exception(f"Failed to get course: {response.text}")
    
    def update_course(self, course_id, **updates):
        """Update course metadata"""
        response = requests.put(
            f"{self.base_url}/courses/{course_id}",
            json=updates,
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to update course: {response.text}")
    
    def delete_course(self, course_id):
        """Delete a course"""
        response = requests.delete(
            f"{self.base_url}/courses/{course_id}",
            headers=self.headers
        )
        
        if response.status_code == 204:
            return True
        else:
            raise Exception(f"Failed to delete course: {response.text}")
    
    def export_course(self, course_id, format="scorm2004", **options):
        """Export course in specified format"""
        export_data = {
            "format": format,
            **options
        }
        
        response = requests.post(
            f"{self.base_url}/courses/{course_id}/export",
            json=export_data,
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to export course: {response.text}")
    
    def get_quality_metrics(self, course_id):
        """Get course quality metrics"""
        response = requests.get(
            f"{self.base_url}/courses/{course_id}/quality-metrics",
            headers=self.headers
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get quality metrics: {response.text}")

# Usage example
def main():
    manager = CourseManager("your-api-key")
    
    # Create a new course
    course = manager.create_course(
        title="Data Science Fundamentals",
        description="Learn the basics of data science and analytics",
        subject_domain="Data Science",
        target_audience={
            "proficiency_level": "intermediate",
            "prerequisites": ["Statistics basics", "Python programming"],
            "learning_preferences": ["practical"]
        },
        estimated_duration="PT25H"
    )
    
    print(f"Created course: {course['id']}")
    
    # List all ready courses
    ready_courses = manager.list_courses(status="ready")
    print(f"Found {len(ready_courses['courses'])} ready courses")
    
    # Get course details
    if course['status'] == 'ready':
        details = manager.get_course(course['id'])
        print(f"Course has {len(details['chapters'])} chapters")
        
        # Get quality metrics
        metrics = manager.get_quality_metrics(course['id'])
        print(f"Quality score: {metrics['pedagogical_alignment']:.2f}")

if __name__ == "__main__":
    main()
```

### JavaScript/Node.js Examples

#### Basic Course Creation

```javascript
const axios = require('axios');

// Configuration
const API_KEY = 'your-api-key-here';
const BASE_URL = 'https://api.courseplatform.com/v1';

const headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
};

// Create a basic course
async function createBasicCourse() {
    const courseData = {
        title: "Modern JavaScript Development",
        description: "Learn modern JavaScript and ES6+ features",
        subject_domain: "Web Development",
        target_audience: {
            proficiency_level: "intermediate",
            prerequisites: ["HTML basics", "CSS basics", "Basic JavaScript"],
            learning_preferences: ["practical", "visual"]
        },
        estimated_duration: "PT18H",
        content_preferences: {
            include_practical_examples: true,
            theory_to_practice_ratio: 0.8
        }
    };
    
    try {
        const response = await axios.post(
            `${BASE_URL}/courses`,
            courseData,
            { headers }
        );
        
        return response.data;
    } catch (error) {
        console.error('Error creating course:', error.response.data);
        throw error;
    }
}

// Monitor generation progress
async function monitorCourseGeneration(courseId) {
    while (true) {
        try {
            const response = await axios.get(
                `${BASE_URL}/courses/${courseId}/generation-status`,
                { headers }
            );
            
            const status = response.data;
            console.log(`Progress: ${status.progress_percentage}% - ${status.current_phase}`);
            
            if (status.status === 'completed') {
                console.log('Course generation completed!');
                return true;
            } else if (status.status === 'failed') {
                console.log(`Generation failed: ${status.error_message || 'Unknown error'}`);
                return false;
            }
            
            // Wait 30 seconds before next check
            await new Promise(resolve => setTimeout(resolve, 30000));
        } catch (error) {
            console.error('Error checking status:', error.response.data);
            throw error;
        }
    }
}

// Usage
async function main() {
    try {
        const course = await createBasicCourse();
        console.log(`Course created with ID: ${course.id}`);
        
        const success = await monitorCourseGeneration(course.id);
        if (success) {
            console.log('Course is ready for use!');
        }
    } catch (error) {
        console.error('Error:', error.message);
    }
}

main();
```

#### Express.js Integration

```javascript
const express = require('express');
const axios = require('axios');
const app = express();

app.use(express.json());

// Course API client
class CourseAPIClient {
    constructor(apiKey, baseUrl = 'https://api.courseplatform.com/v1') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.headers = {
            'X-API-Key': apiKey,
            'Content-Type': 'application/json'
        };
    }
    
    async createCourse(courseData) {
        try {
            const response = await axios.post(
                `${this.baseUrl}/courses`,
                courseData,
                { headers: this.headers }
            );
            return response.data;
        } catch (error) {
            throw new Error(`Failed to create course: ${error.response.data.message}`);
        }
    }
    
    async getCourse(courseId) {
        try {
            const response = await axios.get(
                `${this.baseUrl}/courses/${courseId}`,
                { headers: this.headers }
            );
            return response.data;
        } catch (error) {
            if (error.response.status === 404) {
                throw new Error('Course not found');
            }
            throw new Error(`Failed to get course: ${error.response.data.message}`);
        }
    }
    
    async listCourses(filters = {}) {
        try {
            const response = await axios.get(
                `${this.baseUrl}/courses`,
                { 
                    headers: this.headers,
                    params: filters
                }
            );
            return response.data;
        } catch (error) {
            throw new Error(`Failed to list courses: ${error.response.data.message}`);
        }
    }
}

// Initialize client
const courseClient = new CourseAPIClient(process.env.COURSEPLATFORM_API_KEY);

// Routes
app.post('/api/courses', async (req, res) => {
    try {
        const course = await courseClient.createCourse(req.body);
        res.status(201).json(course);
    } catch (error) {
        res.status(400).json({ error: error.message });
    }
});

app.get('/api/courses', async (req, res) => {
    try {
        const courses = await courseClient.listCourses(req.query);
        res.json(courses);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/api/courses/:id', async (req, res) => {
    try {
        const course = await courseClient.getCourse(req.params.id);
        res.json(course);
    } catch (error) {
        res.status(404).json({ error: error.message });
    }
});

// Start server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
```

### cURL Examples

#### Create Course

```bash
curl -X POST "https://api.courseplatform.com/v1/courses" \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Introduction to Machine Learning",
    "description": "Comprehensive ML course for beginners",
    "subject_domain": "Computer Science",
    "target_audience": {
      "proficiency_level": "beginner",
      "prerequisites": ["Basic mathematics", "Python programming"],
      "learning_preferences": ["visual", "practical"]
    },
    "estimated_duration": "PT20H",
    "content_preferences": {
      "include_practical_examples": true,
      "theory_to_practice_ratio": 0.6
    }
  }'
```

#### List Courses

```bash
curl -X GET "https://api.courseplatform.com/v1/courses?status=ready&limit=10" \
  -H "X-API-Key: your-api-key-here"
```

#### Get Course Details

```bash
curl -X GET "https://api.courseplatform.com/v1/courses/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your-api-key-here"
```

#### Check Generation Status

```bash
curl -X GET "https://api.courseplatform.com/v1/courses/550e8400-e29b-41d4-a716-446655440000/generation-status" \
  -H "X-API-Key: your-api-key-here"
```

#### Export Course

```bash
curl -X POST "https://api.courseplatform.com/v1/courses/550e8400-e29b-41d4-a716-446655440000/export" \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "scorm2004",
    "include_assessments": true,
    "include_multimedia": true
  }'
```

#### Regenerate Chapter

```bash
curl -X POST "https://api.courseplatform.com/v1/courses/550e8400-e29b-41d4-a716-446655440000/regenerate-chapter" \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "chapter_id": "550e8400-e29b-41d4-a716-446655440001",
    "regeneration_reason": "Content too advanced for beginner level"
  }'
```

### PHP Examples

#### Basic Course Management

```php
<?php

class CourseAPIClient {
    private $apiKey;
    private $baseUrl;
    
    public function __construct($apiKey, $baseUrl = 'https://api.courseplatform.com/v1') {
        $this->apiKey = $apiKey;
        $this->baseUrl = $baseUrl;
    }
    
    private function makeRequest($method, $endpoint, $data = null) {
        $url = $this->baseUrl . $endpoint;
        
        $headers = [
            'X-API-Key: ' . $this->apiKey,
            'Content-Type: application/json'
        ];
        
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
        
        if ($data !== null) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        $decoded = json_decode($response, true);
        
        if ($httpCode >= 400) {
            throw new Exception("API Error ({$httpCode}): " . ($decoded['message'] ?? 'Unknown error'));
        }
        
        return $decoded;
    }
    
    public function createCourse($courseData) {
        return $this->makeRequest('POST', '/courses', $courseData);
    }
    
    public function getCourse($courseId) {
        return $this->makeRequest('GET', "/courses/{$courseId}");
    }
    
    public function listCourses($filters = []) {
        $query = http_build_query($filters);
        $endpoint = '/courses' . ($query ? '?' . $query : '');
        return $this->makeRequest('GET', $endpoint);
    }
    
    public function getGenerationStatus($courseId) {
        return $this->makeRequest('GET', "/courses/{$courseId}/generation-status");
    }
    
    public function exportCourse($courseId, $exportData) {
        return $this->makeRequest('POST', "/courses/{$courseId}/export", $exportData);
    }
}

// Usage example
try {
    $client = new CourseAPIClient('your-api-key-here');
    
    // Create a course
    $courseData = [
        'title' => 'PHP Web Development',
        'description' => 'Learn modern PHP web development',
        'subject_domain' => 'Web Development',
        'target_audience' => [
            'proficiency_level' => 'intermediate',
            'prerequisites' => ['HTML', 'CSS', 'Basic programming'],
            'learning_preferences' => ['practical']
        ],
        'estimated_duration' => 'PT20H'
    ];
    
    $course = $client->createCourse($courseData);
    echo "Course created with ID: " . $course['id'] . "\n";
    
    // Monitor generation
    do {
        sleep(30);
        $status = $client->getGenerationStatus($course['id']);
        echo "Progress: " . $status['progress_percentage'] . "% - " . $status['current_phase'] . "\n";
    } while ($status['status'] === 'in_progress');
    
    if ($status['status'] === 'completed') {
        echo "Course generation completed!\n";
        
        // Get final course details
        $finalCourse = $client->getCourse($course['id']);
        echo "Course has " . count($finalCourse['chapters']) . " chapters\n";
    } else {
        echo "Course generation failed: " . ($status['error_message'] ?? 'Unknown error') . "\n";
    }
    
} catch (Exception $e) {
    echo "Error: " . $e->getMessage() . "\n";
}
?>
```

## Advanced Examples

### Batch Course Processing

```python
import asyncio
import aiohttp
from typing import List, Dict

class BatchCourseProcessor:
    def __init__(self, api_key: str, base_url: str = "https://api.courseplatform.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
        
    async def create_courses_batch(self, courses_data: List[Dict]) -> List[Dict]:
        """Create multiple courses concurrently"""
        async with aiohttp.ClientSession() as session:
            tasks = [
                self._create_single_course(session, course_data)
                for course_data in courses_data
            ]
            return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _create_single_course(self, session: aiohttp.ClientSession, course_data: Dict) -> Dict:
        try:
            async with session.post(
                f"{self.base_url}/courses",
                json=course_data,
                headers=self.headers
            ) as response:
                if response.status == 201:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"HTTP {response.status}: {error_text}")
        except Exception as e:
            return {
                'error': str(e),
                'course_title': course_data.get('title', 'Unknown')
            }

# Usage
async def batch_example():
    processor = BatchCourseProcessor("your-api-key")
    
    courses_to_create = [
        {
            "title": "Python Basics",
            "description": "Learn Python fundamentals",
            "subject_domain": "Computer Science",
            "target_audience": {"proficiency_level": "beginner"},
            "estimated_duration": "PT12H"
        },
        {
            "title": "Web Development with Django",
            "description": "Build web applications with Django",
            "subject_domain": "Web Development",
            "target_audience": {"proficiency_level": "intermediate"},
            "estimated_duration": "PT24H"
        },
        {
            "title": "Data Analysis with Pandas",
            "description": "Analyze data using Python and Pandas",
            "subject_domain": "Data Science",
            "target_audience": {"proficiency_level": "intermediate"},
            "estimated_duration": "PT16H"
        }
    ]
    
    results = await processor.create_courses_batch(courses_to_create)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception) or 'error' in result:
            print(f"Course {i} failed: {result}")
        else:
            print(f"Course {i} created successfully: {result['id']}")

# Run the batch processing
asyncio.run(batch_example())
```

### Quality Monitoring Dashboard

```python
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta

class QualityDashboard:
    def __init__(self, course_manager):
        self.course_manager = course_manager
    
    def get_quality_report(self, course_ids: List[str]) -> pd.DataFrame:
        """Generate quality report for multiple courses"""
        data = []
        
        for course_id in course_ids:
            try:
                course = self.course_manager.get_course(course_id)
                metrics = self.course_manager.get_quality_metrics(course_id)
                
                data.append({
                    'course_id': course_id,
                    'title': course['title'],
                    'subject_domain': course['subject_domain'],
                    'proficiency_level': course['target_audience']['proficiency_level'],
                    'readability_score': metrics['readability_score'],
                    'pedagogical_alignment': metrics['pedagogical_alignment'],
                    'objective_coverage': metrics['objective_coverage'],
                    'content_accuracy': metrics['content_accuracy'],
                    'bias_detection_score': metrics['bias_detection_score'],
                    'created_at': course['created_at']
                })
            except Exception as e:
                print(f"Error processing course {course_id}: {e}")
        
        return pd.DataFrame(data)
    
    def plot_quality_metrics(self, df: pd.DataFrame):
        """Create visualizations for quality metrics"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # Readability scores by subject domain
        df.boxplot(column='readability_score', by='subject_domain', ax=axes[0,0])
        axes[0,0].set_title('Readability Scores by Subject Domain')
        
        # Pedagogical alignment by proficiency level
        df.boxplot(column='pedagogical_alignment', by='proficiency_level', ax=axes[0,1])
        axes[0,1].set_title('Pedagogical Alignment by Proficiency Level')
        
        # Content accuracy vs objective coverage
        axes[1,0].scatter(df['content_accuracy'], df['objective_coverage'])
        axes[1,0].set_xlabel('Content Accuracy')
        axes[1,0].set_ylabel('Objective Coverage')
        axes[1,0].set_title('Content Accuracy vs Objective Coverage')
        
        # Bias detection scores histogram
        axes[1,1].hist(df['bias_detection_score'], bins=20, alpha=0.7)
        axes[1,1].set_xlabel('Bias Detection Score')
        axes[1,1].set_ylabel('Frequency')
        axes[1,1].set_title('Distribution of Bias Detection Scores')
        
        plt.tight_layout()
        plt.savefig('quality_dashboard.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def identify_improvement_opportunities(self, df: pd.DataFrame) -> Dict:
        """Identify courses that need improvement"""
        opportunities = {
            'low_readability': df[df['readability_score'] < 70]['course_id'].tolist(),
            'poor_alignment': df[df['pedagogical_alignment'] < 0.8]['course_id'].tolist(),
            'incomplete_coverage': df[df['objective_coverage'] < 0.9]['course_id'].tolist(),
            'high_bias': df[df['bias_detection_score'] > 0.1]['course_id'].tolist()
        }
        return opportunities

# Usage
manager = CourseManager("your-api-key")
dashboard = QualityDashboard(manager)

# Get list of course IDs
courses = manager.list_courses(status="ready", limit=50)
course_ids = [course['id'] for course in courses['courses']]

# Generate quality report
quality_df = dashboard.get_quality_report(course_ids)
print(quality_df.describe())

# Create visualizations
dashboard.plot_quality_metrics(quality_df)

# Identify improvement opportunities
improvements = dashboard.identify_improvement_opportunities(quality_df)
print("Courses needing improvement:")
for category, course_list in improvements.items():
    if course_list:
        print(f"  {category}: {len(course_list)} courses")
```

### LMS Integration Example

```python
import zipfile
import tempfile
import os
from pathlib import Path

class LMSIntegration:
    def __init__(self, course_api_client, lms_client):
        self.course_api = course_api_client
        self.lms = lms_client
    
    def bulk_import_to_lms(self, course_configs: List[Dict]) -> List[Dict]:
        """Import multiple courses to LMS"""
        results = []
        
        for config in course_configs:
            try:
                result = self.import_single_course_to_lms(config)
                results.append({
                    'success': True,
                    'config': config,
                    'result': result
                })
            except Exception as e:
                results.append({
                    'success': False,
                    'config': config,
                    'error': str(e)
                })
        
        return results
    
    def import_single_course_to_lms(self, course_config: Dict) -> Dict:
        """Import a single course to LMS"""
        # 1. Create course via API
        course = self.course_api.create_course(course_config['course_data'])
        course_id = course['id']
        
        # 2. Wait for generation to complete
        self._wait_for_completion(course_id)
        
        # 3. Get final course data
        final_course = self.course_api.get_course(course_id)
        
        # 4. Export in SCORM format
        export_response = self.course_api.export_course(
            course_id,
            format="scorm2004",
            include_assessments=True,
            include_multimedia=True
        )
        
        # 5. Download and extract SCORM package
        package_path = self._download_scorm_package(export_response['download_url'])
        
        # 6. Import to LMS
        lms_course_id = self.lms.import_scorm_package(
            package_path,
            course_name=final_course['title'],
            category=course_config.get('lms_category', 'Generated Courses')
        )
        
        # 7. Configure LMS course settings
        self.lms.configure_course(lms_course_id, {
            'enrollment_method': course_config.get('enrollment_method', 'manual'),
            'start_date': course_config.get('start_date'),
            'end_date': course_config.get('end_date'),
            'visible': course_config.get('visible', True)
        })
        
        # 8. Add course metadata
        self.lms.add_course_metadata(lms_course_id, {
            'generated_by': 'Course Generation Platform',
            'api_course_id': course_id,
            'generation_date': final_course['created_at'],
            'quality_score': final_course['quality_metrics']['pedagogical_alignment'],
            'estimated_duration': final_course['estimated_duration']
        })
        
        # 9. Clean up temporary files
        os.unlink(package_path)
        
        return {
            'api_course_id': course_id,
            'lms_course_id': lms_course_id,
            'course_title': final_course['title'],
            'quality_metrics': final_course['quality_metrics']
        }
    
    def _wait_for_completion(self, course_id: str, timeout: int = 3600):
        """Wait for course generation to complete"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.course_api.get_generation_status(course_id)
            
            if status['status'] == 'completed':
                return
            elif status['status'] == 'failed':
                raise Exception(f"Course generation failed: {status.get('error_message')}")
            
            time.sleep(30)
        
        raise Exception("Course generation timeout")
    
    def _download_scorm_package(self, download_url: str) -> str:
        """Download SCORM package to temporary file"""
        import requests
        
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            return temp_file.name

# Usage example
def main():
    # Initialize clients
    course_api = CourseManager("your-api-key")
    lms_client = YourLMSClient("lms-credentials")  # Your LMS client implementation
    
    integration = LMSIntegration(course_api, lms_client)
    
    # Define courses to create and import
    course_configs = [
        {
            'course_data': {
                'title': 'Introduction to Python',
                'description': 'Learn Python programming basics',
                'subject_domain': 'Computer Science',
                'target_audience': {'proficiency_level': 'beginner'},
                'estimated_duration': 'PT15H'
            },
            'lms_category': 'Programming Courses',
            'enrollment_method': 'self',
            'visible': True
        },
        {
            'course_data': {
                'title': 'Web Development Fundamentals',
                'description': 'Learn HTML, CSS, and JavaScript',
                'subject_domain': 'Web Development',
                'target_audience': {'proficiency_level': 'beginner'},
                'estimated_duration': 'PT20H'
            },
            'lms_category': 'Web Development',
            'enrollment_method': 'manual',
            'visible': True
        }
    ]
    
    # Import courses to LMS
    results = integration.bulk_import_to_lms(course_configs)
    
    # Report results
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"Successfully imported {len(successful)} courses")
    print(f"Failed to import {len(failed)} courses")
    
    for failure in failed:
        print(f"Failed: {failure['config']['course_data']['title']} - {failure['error']}")

if __name__ == "__main__":
    main()
```

## Error Handling Examples

### Comprehensive Error Handling

```python
import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RobustCourseClient:
    def __init__(self, api_key, base_url="https://api.courseplatform.com/v1", max_retries=3):
        self.api_key = api_key
        self.base_url = base_url
        self.max_retries = max_retries
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method, endpoint, data=None, timeout=30):
        """Make HTTP request with retry logic and error handling"""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    json=data,
                    headers=self.headers,
                    timeout=timeout
                )
                
                # Handle specific HTTP status codes
                if response.status_code == 200 or response.status_code == 201:
                    return response.json()
                elif response.status_code == 204:
                    return None  # No content
                elif response.status_code == 400:
                    error_data = response.json()
                    raise ValueError(f"Bad request: {error_data.get('message', 'Invalid data')}")
                elif response.status_code == 401:
                    raise PermissionError("Invalid API key or insufficient permissions")
                elif response.status_code == 404:
                    raise ValueError("Resource not found")
                elif response.status_code == 409:
                    error_data = response.json()
                    raise ValueError(f"Conflict: {error_data.get('message', 'Resource already exists')}")
                elif response.status_code == 422:
                    error_data = response.json()
                    raise ValueError(f"Validation error: {error_data.get('message', 'Invalid data')}")
                elif response.status_code == 429:
                    retry_after = int(response.headers.get('retry-after', 60))
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                        time.sleep(retry_after)
                        continue
                    else:
                        raise Exception("Rate limit exceeded. Please try again later.")
                elif response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Server error {response.status_code}. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"Server error: {response.status_code}")
                else:
                    response.raise_for_status()
                    
            except Timeout:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Request timeout. Retrying... (attempt {attempt + 1})")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise Exception("Request timeout. Please check your connection and try again.")
                    
            except ConnectionError:
                if attempt < self.max_retries - 1:
                    logger.warning(f"Connection error. Retrying... (attempt {attempt + 1})")
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise Exception("Connection error. Please check your network connection.")
                    
            except HTTPError as e:
                logger.error(f"HTTP error: {e}")
                raise Exception(f"HTTP error: {e}")
                
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise
        
        raise Exception("Maximum retries exceeded")
    
    def create_course_safe(self, course_data):
        """Create course with comprehensive error handling"""
        try:
            # Validate required fields
            required_fields = ['title', 'subject_domain', 'target_audience']
            for field in required_fields:
                if field not in course_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Create course
            result = self._make_request('POST', '/courses', course_data)
            logger.info(f"Course created successfully: {result['id']}")
            return result
            
        except ValueError as e:
            logger.error(f"Validation error: {e}")
            raise
        except PermissionError as e:
            logger.error(f"Authentication error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create course: {e}")
            raise

# Usage with error handling
def create_course_with_error_handling():
    client = RobustCourseClient("your-api-key")
    
    course_data = {
        "title": "Test Course",
        "description": "A test course",
        "subject_domain": "Computer Science",
        "target_audience": {
            "proficiency_level": "beginner"
        },
        "estimated_duration": "PT10H"
    }
    
    try:
        course = client.create_course_safe(course_data)
        print(f"Course created: {course['id']}")
        return course
    except ValueError as e:
        print(f"Data validation error: {e}")
        # Handle validation errors - fix data and retry
    except PermissionError as e:
        print(f"Authentication error: {e}")
        # Handle auth errors - check API key
    except Exception as e:
        print(f"Unexpected error: {e}")
        # Handle other errors - log and notify admin

if __name__ == "__main__":
    create_course_with_error_handling()
```

These examples provide comprehensive coverage of the Course Generation Platform API, from basic usage to advanced integration patterns. They demonstrate best practices for error handling, performance optimization, and real-world integration scenarios.