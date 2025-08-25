-- Quick verification query for Azure Portal Query Editor
-- Shows all embedding-related tables and their status

-- 1. Check which tables exist
SELECT 
    'EMBEDDING TABLES STATUS' as Report,
    COUNT(*) as TablesFound,
    CONCAT(COUNT(*), ' of 5 tables exist') as Status
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME IN ('document_embeddings', 'node_embeddings', 'query_embeddings_cache', 'embedding_jobs', 'search_results_log');

-- 2. List all embedding tables with details
SELECT 
    t.TABLE_NAME as TableName,
    CASE 
        WHEN t.TABLE_NAME IS NOT NULL THEN 'EXISTS' 
        ELSE 'MISSING' 
    END as Status,
    (
        SELECT COUNT(*) 
        FROM INFORMATION_SCHEMA.COLUMNS c 
        WHERE c.TABLE_NAME = t.TABLE_NAME
    ) as ColumnCount
FROM (
    VALUES 
        ('document_embeddings'),
        ('node_embeddings'),
        ('query_embeddings_cache'),
        ('embedding_jobs'),
        ('search_results_log')
) AS expected(TABLE_NAME)
LEFT JOIN INFORMATION_SCHEMA.TABLES t 
    ON t.TABLE_NAME = expected.TABLE_NAME
    AND t.TABLE_SCHEMA = 'dbo'
ORDER BY expected.TABLE_NAME;

-- 3. If document_embeddings exists, show sample
IF OBJECT_ID('document_embeddings', 'U') IS NOT NULL
BEGIN
    SELECT TOP 5 
        'Sample from document_embeddings:' as Info,
        document_id,
        chunk_index,
        LEFT(chunk_text, 50) + '...' as ChunkPreview,
        created_at
    FROM document_embeddings
    ORDER BY created_at DESC;
END
ELSE
BEGIN
    SELECT 'document_embeddings table does not exist' as Message;
END

-- 4. Check which documents need embeddings
SELECT 
    'Documents needing embeddings:' as Report,
    COUNT(DISTINCT d.id) as DocumentsWithoutEmbeddings
FROM documents d
WHERE NOT EXISTS (
    SELECT 1 FROM document_embeddings de 
    WHERE de.document_id = d.id
);