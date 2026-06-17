-- PostgreSQL initialization script for NexusAI
-- Enables pgvector extension and creates initial database indices

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Verify vector extension is functional
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
