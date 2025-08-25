-- Add embedding tables to Knowledge Base system
-- This script adds tables for storing vector embeddings for semantic search

USE [knowledge-base];
GO

-- 1. Store document chunk embeddings
CREATE TABLE document_embeddings (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    document_id BIGINT NOT NULL,
    chunk_index INT NOT NULL,
    chunk_text NVARCHAR(MAX) NOT NULL,
    embedding_vector VARBINARY(MAX) NOT NULL, -- Binary storage for 1536-dim vectors
    embedding_model VARCHAR(50) NOT NULL DEFAULT 'text-embedding-ada-002',
    vector_dimension INT NOT NULL DEFAULT 1536,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    INDEX idx_doc_chunk (document_id, chunk_index)
);
GO

-- 2. Store knowledge graph node embeddings for concept similarity
-- Note: knowledge_graph_nodes.id is NVARCHAR(255), not VARCHAR
CREATE TABLE node_embeddings (
    node_id NVARCHAR(255) NOT NULL PRIMARY KEY,
    embedding_vector VARBINARY(MAX) NOT NULL,
    embedding_model VARCHAR(50) NOT NULL DEFAULT 'text-embedding-ada-002',
    vector_dimension INT NOT NULL DEFAULT 1536,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    updated_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (node_id) REFERENCES knowledge_graph_nodes(id) ON DELETE CASCADE
);
GO

-- 3. Cache for search query embeddings (performance optimization)
CREATE TABLE query_embeddings_cache (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    query_hash VARCHAR(64) NOT NULL UNIQUE, -- SHA256 hash of lowercase query
    query_text NVARCHAR(MAX) NOT NULL,
    embedding_vector VARBINARY(MAX) NOT NULL,
    embedding_model VARCHAR(50) NOT NULL DEFAULT 'text-embedding-ada-002',
    vector_dimension INT NOT NULL DEFAULT 1536,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    last_accessed DATETIME2 DEFAULT GETUTCDATE(),
    access_count INT DEFAULT 1,
    INDEX idx_query_hash (query_hash),
    INDEX idx_last_accessed (last_accessed) -- For cache cleanup
);
GO

-- 4. Track embedding generation jobs
CREATE TABLE embedding_jobs (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    document_id BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    total_chunks INT NULL,
    processed_chunks INT DEFAULT 0,
    error_message NVARCHAR(MAX) NULL,
    started_at DATETIME2 NULL,
    completed_at DATETIME2 NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    INDEX idx_status (status),
    INDEX idx_document (document_id)
);
GO

-- 5. Store similarity search results for analytics
CREATE TABLE search_results_log (
    id BIGINT IDENTITY(1,1) PRIMARY KEY,
    query_id BIGINT NOT NULL,
    document_id BIGINT NOT NULL,
    chunk_index INT NOT NULL,
    similarity_score FLOAT NOT NULL,
    rank_position INT NOT NULL,
    was_clicked BIT DEFAULT 0,
    click_timestamp DATETIME2 NULL,
    created_at DATETIME2 DEFAULT GETUTCDATE(),
    FOREIGN KEY (query_id) REFERENCES search_queries(id),
    FOREIGN KEY (document_id) REFERENCES documents(id),
    INDEX idx_query_results (query_id, rank_position)
);
GO

-- Helper function to convert embedding array to binary
-- This will be used when storing embeddings from Python
CREATE FUNCTION dbo.EmbeddingToBinary(@embedding NVARCHAR(MAX))
RETURNS VARBINARY(MAX)
AS
BEGIN
    -- Expects JSON array format: [0.1234, -0.5678, ...]
    -- Converts to binary format for efficient storage
    -- Implementation would depend on SQL Server version
    -- For now, return placeholder
    RETURN CAST(@embedding AS VARBINARY(MAX))
END
GO

-- Helper view for semantic search
CREATE VIEW v_searchable_chunks AS
SELECT 
    de.id as embedding_id,
    de.document_id,
    de.chunk_index,
    de.chunk_text,
    d.title as document_title,
    d.classification,
    d.metadata as document_metadata,
    d.created_at as document_created,
    d.user_id,
    de.created_at as embedding_created
FROM document_embeddings de
JOIN documents d ON de.document_id = d.id
-- Note: No is_deleted column in documents table
GO

-- Add indexes for better performance
CREATE INDEX idx_embedding_created ON document_embeddings(created_at DESC);
CREATE INDEX idx_doc_classification ON documents(classification);
GO

-- Clean up old query cache entries (run periodically)
CREATE PROCEDURE sp_cleanup_query_cache
    @days_to_keep INT = 7
AS
BEGIN
    DELETE FROM query_embeddings_cache
    WHERE last_accessed < DATEADD(DAY, -@days_to_keep, GETUTCDATE());
END
GO

PRINT '✅ Embedding tables created successfully!';
PRINT '📊 Added tables for document embeddings, node embeddings, and query cache';
PRINT '🔍 Ready for semantic search implementation';
GO