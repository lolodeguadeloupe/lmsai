"""
Celery configuration and settings.

Provides environment-specific configuration for Celery workers,
monitoring, and performance optimization.
"""

import os
from typing import Dict, Any, List


class CeleryConfig:
    """Celery configuration class."""
    
    # Redis configuration
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
    
    # Broker settings
    broker_url = REDIS_URL
    broker_pool_limit = REDIS_MAX_CONNECTIONS
    broker_connection_retry_on_startup = True
    broker_connection_retry = True
    broker_connection_max_retries = 10
    
    # Result backend
    result_backend = REDIS_URL
    result_expires = 3600 * 24  # 24 hours
    result_compression = "gzip"
    result_backend_max_retries = 10
    
    # Task settings
    task_serializer = "json"
    result_serializer = "json"
    accept_content = ["json"]
    timezone = "UTC"
    enable_utc = True
    
    # Worker settings
    worker_concurrency = int(os.getenv("CELERY_WORKER_CONCURRENCY", "4"))
    worker_prefetch_multiplier = 1
    worker_max_tasks_per_child = int(os.getenv("CELERY_MAX_TASKS_PER_CHILD", "1000"))
    worker_disable_rate_limits = False
    
    # Task execution
    task_acks_late = True
    task_reject_on_worker_lost = True
    task_track_started = True
    task_send_sent_event = True
    
    # Retry settings
    task_retry_jitter = True
    task_retry_jitter_max = 5.0
    task_default_retry_delay = 60
    task_max_retries = 3
    
    # Time limits (performance requirement: <2min for chapters)
    task_soft_time_limit = 110  # 1:50 for chapters
    task_time_limit = 120  # 2:00 hard limit
    
    # Monitoring
    worker_send_task_events = True
    task_send_sent_event = True
    worker_hijack_root_logger = False
    worker_log_color = False
    
    # Queue routing
    task_routes = {
        "src.tasks.generation_tasks.generate_course_task": {"queue": "course_generation"},
        "src.tasks.generation_tasks.generate_chapter_task": {"queue": "chapter_generation"},
        "src.tasks.generation_tasks.validate_quality_task": {"queue": "quality_validation"},
        "src.tasks.generation_tasks.export_course_task": {"queue": "export"},
        "src.tasks.generation_tasks.regenerate_chapter_task": {"queue": "chapter_generation"},
    }
    
    # Environment-specific overrides
    @classmethod
    def get_config(cls, environment: str = None) -> Dict[str, Any]:
        """
        Get environment-specific configuration.
        
        Args:
            environment: Environment name (development, testing, production)
            
        Returns:
            Configuration dictionary
        """
        env = environment or os.getenv("ENVIRONMENT", "development")
        
        config = {
            attr: getattr(cls, attr)
            for attr in dir(cls)
            if not attr.startswith("_") and not callable(getattr(cls, attr))
        }
        
        if env == "testing":
            # Testing configuration
            config.update({
                "task_always_eager": True,  # Execute tasks synchronously
                "task_eager_propagates": True,
                "task_store_eager_result": True,
                "broker_url": "memory://",
                "result_backend": "cache+memory://",
            })
        
        elif env == "production":
            # Production optimizations
            config.update({
                "worker_concurrency": int(os.getenv("CELERY_WORKER_CONCURRENCY", "8")),
                "worker_max_tasks_per_child": 500,  # More conservative in production
                "task_compression": "gzip",
                "result_compression": "gzip",
                "worker_log_level": "INFO",
            })
        
        elif env == "development":
            # Development settings
            config.update({
                "worker_log_level": "DEBUG",
                "worker_concurrency": 2,  # Lower concurrency for development
            })
        
        return config


class MonitoringConfig:
    """Configuration for task monitoring and metrics."""
    
    # Flower monitoring (optional)
    FLOWER_PORT = int(os.getenv("FLOWER_PORT", "5555"))
    FLOWER_ADDRESS = os.getenv("FLOWER_ADDRESS", "0.0.0.0")
    FLOWER_URL_PREFIX = os.getenv("FLOWER_URL_PREFIX", "")
    
    # Performance thresholds
    MAX_TASK_DURATION = {
        "generate_course": 600,  # 10 minutes
        "generate_chapter": 120,  # 2 minutes (requirement)
        "validate_quality": 300,  # 5 minutes
        "export_course": 180,  # 3 minutes
        "regenerate_chapter": 120,  # 2 minutes
    }
    
    # Success rate requirements
    MINIMUM_SUCCESS_RATE = 95.0  # 95% as per requirements
    
    # Queue capacity limits
    MAX_CONCURRENT_COURSES = 100  # FR-022 requirement
    MAX_QUEUE_SIZE = 500
    
    # Alert thresholds
    ALERT_THRESHOLDS = {
        "high_failure_rate": 10.0,  # >10% failure rate
        "high_queue_length": 100,  # >100 pending tasks
        "worker_down": 0,  # No workers available
        "slow_processing": 150,  # >150% of expected time
    }


class SecurityConfig:
    """Security configuration for Celery."""
    
    # Worker security
    WORKER_HIJACK_ROOT_LOGGER = False
    WORKER_DISABLE_RATE_LIMITS = False
    
    # Redis security
    REDIS_SOCKET_KEEPALIVE = True
    REDIS_SOCKET_KEEPALIVE_OPTIONS = {
        "TCP_KEEPINTVL": 1,
        "TCP_KEEPCNT": 3,
        "TCP_KEEPIDLE": 1,
    }
    
    # Task signature verification (if needed)
    TASK_ALWAYS_EAGER = False
    TASK_STORE_EAGER_RESULT = True
    
    # Content filtering
    ACCEPT_CONTENT = ["json"]
    TASK_SERIALIZER = "json"
    RESULT_SERIALIZER = "json"


def get_celery_config(environment: str = None) -> Dict[str, Any]:
    """
    Get complete Celery configuration for environment.
    
    Args:
        environment: Target environment
        
    Returns:
        Complete configuration dictionary
    """
    base_config = CeleryConfig.get_config(environment)
    
    # Add monitoring configuration
    monitoring = MonitoringConfig()
    base_config["monitoring"] = {
        attr: getattr(monitoring, attr)
        for attr in dir(monitoring)
        if not attr.startswith("_") and not callable(getattr(monitoring, attr))
    }
    
    # Add security configuration
    security = SecurityConfig()
    security_config = {
        attr.lower(): getattr(security, attr)
        for attr in dir(security)
        if not attr.startswith("_") and not callable(getattr(security, attr))
    }
    base_config.update(security_config)
    
    return base_config


def get_queue_definitions() -> List[Dict[str, Any]]:
    """
    Get queue definitions for different task types.
    
    Returns:
        List of queue configurations
    """
    return [
        {
            "name": "course_generation",
            "routing_key": "course_generation",
            "priority": 5,
            "max_length": 50,
            "description": "Full course generation tasks"
        },
        {
            "name": "chapter_generation",
            "routing_key": "chapter_generation",
            "priority": 8,
            "max_length": 100,
            "description": "Individual chapter generation tasks"
        },
        {
            "name": "quality_validation",
            "routing_key": "quality_validation",
            "priority": 6,
            "max_length": 75,
            "description": "Content quality validation tasks"
        },
        {
            "name": "export",
            "routing_key": "export",
            "priority": 4,
            "max_length": 25,
            "description": "Course export tasks"
        },
        {
            "name": "default",
            "routing_key": "default",
            "priority": 3,
            "max_length": 100,
            "description": "Default queue for misc tasks"
        }
    ]


def get_performance_settings() -> Dict[str, Any]:
    """
    Get performance-optimized settings based on requirements.
    
    Returns:
        Performance configuration
    """
    return {
        # Concurrency for 100+ simultaneous operations (FR-022)
        "max_concurrent_courses": 100,
        "worker_pool_size": int(os.getenv("CELERY_WORKER_CONCURRENCY", "8")),
        "prefetch_multiplier": 1,  # Prevent worker overload
        
        # Time limits per requirements
        "chapter_generation_limit": 120,  # <2 min requirement
        "course_generation_limit": 600,  # 10 min reasonable limit
        "quality_validation_limit": 300,  # 5 min limit
        
        # Success rate targeting 95%+ (requirement)
        "max_retries": 3,
        "retry_delay": 60,
        "exponential_backoff": True,
        
        # Memory and resource management
        "max_tasks_per_child": 1000,
        "memory_limit_per_child": "500MB",
        "result_expiry": 86400,  # 24 hours
        
        # Queue management
        "queue_length_limit": 500,
        "priority_routing": True,
        "dead_letter_queue": True,
    }