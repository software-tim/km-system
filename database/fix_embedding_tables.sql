-- Fix script to create remaining embedding tables
-- Run this after the initial migration to fix errors

USE [knowledge-base];
GO

-- Drop the view that had errors
IF OBJECT_ID('v_searchable_chunks', 'V') IS NOT NULL
    DROP VIEW v_searchable_chunks;
GO

-- Drop node_embeddings if it exists (due to foreign key error)
IF OBJECT_ID('node_embeddings', 'U') IS NOT NULL
    DROP TABLE node_embeddings;
GO

-- Recreate node_embeddings with correct data type
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

-- Create corrected view without is_deleted
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
JOIN documents d ON de.document_id = d.id;
GO

-- Add index if not exists
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_doc_classification' AND object_id = OBJECT_ID('documents'))
    CREATE INDEX idx_doc_classification ON documents(classification);
GO

PRINT '✅ Fixed embedding tables successfully!';
GO