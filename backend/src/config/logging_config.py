"""
Logging configuration for the Course Generation Platform
Centralized configuration for structured logging across the application.
"""

import os
import logging
import logging.config
from typing import Dict, Any

# Environment-based logging configuration
def get_log_level() -> str:
    """Get log level from environment variable"""
    return os.getenv('LOG_LEVEL', 'INFO').upper()

def get_log_format() -> str:
    """Get log format preference"""
    return os.getenv('LOG_FORMAT', 'json')  # json or text

def is_development() -> bool:
    """Check if running in development mode"""
    return os.getenv('ENVIRONMENT', 'development').lower() in ['dev', 'development', 'local']

def get_logging_config() -> Dict[str, Any]:
    """
    Get comprehensive logging configuration
    
    Returns:
        Dictionary containing logging configuration suitable for logging.dictConfig()
    """
    
    log_level = get_log_level()
    log_format = get_log_format()
    is_dev = is_development()
    
    # Base configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'text': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(pathname)s:%(lineno)d]',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'json' if log_format == 'json' and not is_dev else 'text',
                'stream': 'ext://sys.stdout'
            }
        },
        'loggers': {
            'course_platform': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'course_platform.middleware.logging': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'course_platform.api': {
                'level': log_level,
                'handlers': ['console'],
                'propagate': False
            },
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'uvicorn.access': {
                'level': 'WARNING',  # Reduce uvicorn access logs since we have our own
                'handlers': ['console'],
                'propagate': False
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['console']
        }
    }
    
    # Add file handler for production
    if not is_dev:
        log_dir = os.getenv('LOG_DIR', '/var/log/course-platform')
        os.makedirs(log_dir, exist_ok=True)
        
        config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': log_level,
            'formatter': 'json',
            'filename': f'{log_dir}/app.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8'
        }
        
        config['handlers']['error_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'json',
            'filename': f'{log_dir}/error.log',
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'encoding': 'utf-8'
        }
        
        # Add file handlers to all loggers
        for logger_name in config['loggers']:
            config['loggers'][logger_name]['handlers'].extend(['file', 'error_file'])
        
        config['root']['handlers'].extend(['file', 'error_file'])
    
    return config

def configure_logging():
    """Configure logging for the application"""
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # Set up correlation context
    logging.getLogger('course_platform').info(
        "Logging configured",
        extra={
            'log_level': get_log_level(),
            'log_format': get_log_format(),
            'environment': os.getenv('ENVIRONMENT', 'development')
        }
    )

# Logging utilities
def get_logger(name: str) -> logging.Logger:
    """Get a logger with the course platform naming convention"""
    if not name.startswith('course_platform'):
        name = f'course_platform.{name}'
    return logging.getLogger(name)

def log_startup_info():
    """Log application startup information"""
    logger = get_logger('startup')
    logger.info(
        "Application starting up",
        extra={
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'log_level': get_log_level(),
            'python_version': os.sys.version,
            'working_directory': os.getcwd()
        }
    )

# Example middleware configuration for different environments
MIDDLEWARE_CONFIGS = {
    'development': {
        'skip_paths': {'/health', '/metrics', '/favicon.ico', '/docs', '/redoc', '/openapi.json'},
        'max_body_size': 50000,  # 50KB for development
        'log_request_body': True,
        'log_response_body': True,
    },
    'staging': {
        'skip_paths': {'/health', '/metrics', '/favicon.ico'},
        'max_body_size': 10000,  # 10KB for staging
        'log_request_body': True,
        'log_response_body': False,  # Reduce response logging in staging
    },
    'production': {
        'skip_paths': {'/health', '/metrics', '/favicon.ico'},
        'max_body_size': 5000,   # 5KB for production
        'log_request_body': False,  # Security: don't log request bodies in prod
        'log_response_body': False, # Security: don't log response bodies in prod
    }
}

def get_middleware_config() -> Dict[str, Any]:
    """Get middleware configuration based on environment"""
    env = os.getenv('ENVIRONMENT', 'development').lower()
    
    if env in ['prod', 'production']:
        return MIDDLEWARE_CONFIGS['production']
    elif env in ['staging', 'stage']:
        return MIDDLEWARE_CONFIGS['staging']
    else:
        return MIDDLEWARE_CONFIGS['development']