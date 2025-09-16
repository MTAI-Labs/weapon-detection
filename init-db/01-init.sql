-- PostgreSQL initialization script for API
-- This script runs when the database container starts for the first time

-- Create extensions for better performance and functionality
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Set timezone
SET timezone = 'UTC';

-- Configure search path
SET search_path TO public;

-- Logging configuration for API workloads
SET log_statement = 'mod';
SET log_min_duration_statement = 1000; -- Log queries taking more than 1 second

-- Performance settings for API workloads
SET shared_preload_libraries = 'pg_stat_statements';
SET track_activity_query_size = 2048;
SET track_io_timing = on;

-- Create a function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'API database initialization completed successfully at %', NOW();
END
$$;