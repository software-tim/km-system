-- Verify embedding tables and their structure
USE [knowledge-base];
GO

PRINT '=== VERIFYING EMBEDDING TABLES ==='
PRINT ''

-- 1. Check if all tables exist
PRINT '1. Checking table existence:'
SELECT 
    CASE WHEN OBJECT_ID('document_embeddings', 'U') IS NOT NULL THEN '✅' ELSE '❌' END + ' document_embeddings' as [Table Status]
UNION ALL
SELECT 
    CASE WHEN OBJECT_ID('node_embeddings', 'U') IS NOT NULL THEN '✅' ELSE '❌' END + ' node_embeddings'
UNION ALL
SELECT 
    CASE WHEN OBJECT_ID('query_embeddings_cache', 'U') IS NOT NULL THEN '✅' ELSE '❌' END + ' query_embeddings_cache'
UNION ALL
SELECT 
    CASE WHEN OBJECT_ID('embedding_jobs', 'U') IS NOT NULL THEN '✅' ELSE '❌' END + ' embedding_jobs'
UNION ALL
SELECT 
    CASE WHEN OBJECT_ID('search_results_log', 'U') IS NOT NULL THEN '✅' ELSE '❌' END + ' search_results_log'
UNION ALL
SELECT 
    CASE WHEN OBJECT_ID('v_searchable_chunks', 'V') IS NOT NULL THEN '✅' ELSE '❌' END + ' v_searchable_chunks (view)';

PRINT ''
PRINT '2. Table structures:'
PRINT ''

-- 2. Show document_embeddings structure
IF OBJECT_ID('document_embeddings', 'U') IS NOT NULL
BEGIN
    PRINT '-- document_embeddings columns:'
    SELECT 
        c.name as [Column],
        t.name as [Type],
        c.max_length as [Length],
        CASE WHEN c.is_nullable = 1 THEN 'NULL' ELSE 'NOT NULL' END as [Nullable]
    FROM sys.columns c
    JOIN sys.types t ON c.user_type_id = t.user_type_id
    WHERE c.object_id = OBJECT_ID('document_embeddings')
    ORDER BY c.column_id;
END

PRINT ''

-- 3. Show node_embeddings structure
IF OBJECT_ID('node_embeddings', 'U') IS NOT NULL
BEGIN
    PRINT '-- node_embeddings columns:'
    SELECT 
        c.name as [Column],
        t.name as [Type],
        c.max_length as [Length],
        CASE WHEN c.is_nullable = 1 THEN 'NULL' ELSE 'NOT NULL' END as [Nullable]
    FROM sys.columns c
    JOIN sys.types t ON c.user_type_id = t.user_type_id
    WHERE c.object_id = OBJECT_ID('node_embeddings')
    ORDER BY c.column_id;
END

PRINT ''
PRINT '3. Checking foreign key relationships:'

-- 4. Check foreign keys
SELECT 
    fk.name as [Foreign Key],
    OBJECT_NAME(fk.parent_object_id) as [Table],
    COL_NAME(fkc.parent_object_id, fkc.parent_column_id) as [Column],
    OBJECT_NAME(fk.referenced_object_id) as [Referenced Table],
    COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) as [Referenced Column]
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
WHERE fk.parent_object_id IN (
    OBJECT_ID('document_embeddings'),
    OBJECT_ID('node_embeddings'),
    OBJECT_ID('embedding_jobs'),
    OBJECT_ID('search_results_log')
);

PRINT ''
PRINT '4. Row counts:'

-- 5. Check row counts
SELECT 'document_embeddings' as [Table], COUNT(*) as [Row Count] FROM document_embeddings
UNION ALL
SELECT 'node_embeddings', COUNT(*) FROM node_embeddings
UNION ALL
SELECT 'query_embeddings_cache', COUNT(*) FROM query_embeddings_cache
UNION ALL
SELECT 'embedding_jobs', COUNT(*) FROM embedding_jobs
UNION ALL
SELECT 'search_results_log', COUNT(*) FROM search_results_log;

PRINT ''
PRINT '5. Sample data check:'

-- 6. Check if we have any documents that need embeddings
SELECT TOP 5
    d.id as [Document ID],
    d.title as [Title],
    CASE WHEN de.document_id IS NULL THEN '❌ Needs Embeddings' ELSE '✅ Has Embeddings' END as [Embedding Status],
    COUNT(de.id) as [Chunk Count]
FROM documents d
LEFT JOIN document_embeddings de ON d.id = de.document_id
GROUP BY d.id, d.title, de.document_id
ORDER BY d.id DESC;

PRINT ''
PRINT '=== VERIFICATION COMPLETE ==='