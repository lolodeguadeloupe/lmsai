-- Initialize database with extensions and basic setup
-- This script runs when PostgreSQL container starts for the first time

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable vector extension (if using pgvector in the future)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- Create database user (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'course_user') THEN
        CREATE ROLE course_user LOGIN PASSWORD 'course_password';
    END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE course_platform TO course_user;

-- Set timezone
SET timezone = 'UTC';