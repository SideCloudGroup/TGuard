-- TGuard Database Initialization Script
-- This script creates the database and sets up initial configuration

-- Create database if it doesn't exist
-- Note: In Docker, this is usually handled by POSTGRES_DB environment variable

-- Set timezone
SET timezone = 'UTC';

-- Create indexes for better performance
-- (SQLAlchemy will create the tables, but we can add additional indexes here)

-- Create extension for better UUID support if needed
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Initial setup complete
SELECT 'TGuard database initialized successfully' as status;
