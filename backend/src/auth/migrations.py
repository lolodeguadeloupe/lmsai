"""
Database migration utilities for API key authentication.

Provides functions to create and manage API key related database tables.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database.session import get_db_session, engine
from ..models.base import Base
from .api_key_auth import APIKeyTable, APIKeyUsageLog


def create_api_key_tables():
    """
    Create API key authentication tables.
    
    This function creates the necessary database tables for API key
    authentication if they don't already exist.
    """
    try:
        # Create tables using SQLAlchemy metadata
        APIKeyTable.__table__.create(engine, checkfirst=True)
        APIKeyUsageLog.__table__.create(engine, checkfirst=True)
        
        print("✅ API key tables created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating API key tables: {e}")
        return False


def drop_api_key_tables():
    """
    Drop API key authentication tables.
    
    WARNING: This will permanently delete all API keys and usage logs.
    """
    try:
        APIKeyUsageLog.__table__.drop(engine, checkfirst=True)
        APIKeyTable.__table__.drop(engine, checkfirst=True)
        
        print("✅ API key tables dropped successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error dropping API key tables: {e}")
        return False


def check_api_key_tables_exist() -> bool:
    """
    Check if API key tables exist in the database.
    
    Returns:
        True if tables exist, False otherwise
    """
    try:
        with engine.connect() as connection:
            # Check if api_keys table exists
            result = connection.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'api_keys'
                );
            """))
            
            return result.scalar()
            
    except Exception as e:
        print(f"❌ Error checking table existence: {e}")
        return False


def migrate_api_key_tables():
    """
    Run migration to create API key tables if they don't exist.
    
    This is safe to run multiple times.
    """
    if check_api_key_tables_exist():
        print("ℹ️  API key tables already exist, skipping migration")
        return True
    
    print("🔄 Creating API key tables...")
    return create_api_key_tables()


def add_indexes():
    """
    Add performance indexes to API key tables.
    
    These indexes improve query performance for common operations.
    """
    indexes = [
        # API keys table indexes
        "CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);",
        "CREATE INDEX IF NOT EXISTS idx_api_keys_status ON api_keys(status);",
        "CREATE INDEX IF NOT EXISTS idx_api_keys_created_at ON api_keys(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_api_keys_expires_at ON api_keys(expires_at);",
        "CREATE INDEX IF NOT EXISTS idx_api_keys_key_prefix ON api_keys(key_prefix);",
        
        # Usage logs table indexes
        "CREATE INDEX IF NOT EXISTS idx_usage_logs_api_key_id ON api_key_usage_logs(api_key_id);",
        "CREATE INDEX IF NOT EXISTS idx_usage_logs_timestamp ON api_key_usage_logs(timestamp);",
        "CREATE INDEX IF NOT EXISTS idx_usage_logs_endpoint ON api_key_usage_logs(endpoint);",
        "CREATE INDEX IF NOT EXISTS idx_usage_logs_status_code ON api_key_usage_logs(status_code);",
        "CREATE INDEX IF NOT EXISTS idx_usage_logs_api_key_timestamp ON api_key_usage_logs(api_key_id, timestamp);",
    ]
    
    try:
        with engine.connect() as connection:
            for index_sql in indexes:
                connection.execute(text(index_sql))
            connection.commit()
            
        print("✅ Performance indexes created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")
        return False


def initialize_api_key_system():
    """
    Initialize the complete API key system.
    
    This function:
    1. Creates tables if they don't exist
    2. Adds performance indexes
    3. Verifies the system is working
    """
    print("🚀 Initializing API key authentication system...")
    
    # Step 1: Create tables
    if not migrate_api_key_tables():
        return False
    
    # Step 2: Add indexes
    if not add_indexes():
        print("⚠️  Warning: Failed to create some performance indexes")
    
    # Step 3: Verify system
    try:
        with get_db_session() as db:
            # Test basic query
            count = db.query(APIKeyTable).count()
            print(f"✅ API key system initialized successfully. Current API keys: {count}")
            return True
            
    except Exception as e:
        print(f"❌ Error verifying API key system: {e}")
        return False


def cleanup_expired_keys():
    """
    Clean up expired API keys and old usage logs.
    
    This function:
    1. Marks expired keys as expired
    2. Optionally removes old usage logs (older than 90 days)
    """
    from datetime import datetime, timedelta
    
    try:
        with get_db_session() as db:
            # Mark expired keys
            expired_count = db.query(APIKeyTable).filter(
                APIKeyTable.expires_at <= datetime.utcnow(),
                APIKeyTable.status == "active"
            ).update({"status": "expired"})
            
            # Clean up old usage logs (older than 90 days)
            cutoff_date = datetime.utcnow() - timedelta(days=90)
            old_logs_count = db.query(APIKeyUsageLog).filter(
                APIKeyUsageLog.timestamp < cutoff_date
            ).delete()
            
            db.commit()
            
            print(f"✅ Cleanup completed:")
            print(f"   - Marked {expired_count} expired keys")
            print(f"   - Removed {old_logs_count} old usage log entries")
            
            return True
            
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        return False


if __name__ == "__main__":
    # Run initialization when script is executed directly
    initialize_api_key_system()