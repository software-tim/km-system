# PowerShell script to verify embedding tables setup
# Uses Azure CLI to check the database

$resourceGroup = "km-group"
$serverName = "knowledge-sql"
$databaseName = "knowledge-base"

Write-Host "Verifying Embedding Tables Setup..." -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

# Check if logged in to Azure
$account = az account show 2>$null
if (-not $account) {
    Write-Host "Please login to Azure..." -ForegroundColor Yellow
    az login
}

Write-Host "`nDatabase: $databaseName on $serverName" -ForegroundColor White

# Function to run SQL query
function Run-SqlQuery {
    param(
        [string]$query,
        [string]$description
    )
    
    Write-Host "`n$description" -ForegroundColor Yellow
    
    # Using Azure CLI to run SQL query
    az sql db query `
        --resource-group $resourceGroup `
        --server $serverName `
        --database $databaseName `
        --query-text "$query" `
        --output table
}

# 1. Check which tables exist
$tableCheckQuery = @"
SELECT 
    'document_embeddings' as TableName,
    CASE WHEN OBJECT_ID('document_embeddings', 'U') IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END as Status
UNION ALL
SELECT 'node_embeddings',
    CASE WHEN OBJECT_ID('node_embeddings', 'U') IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END
UNION ALL
SELECT 'query_embeddings_cache',
    CASE WHEN OBJECT_ID('query_embeddings_cache', 'U') IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END
UNION ALL
SELECT 'embedding_jobs',
    CASE WHEN OBJECT_ID('embedding_jobs', 'U') IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END
UNION ALL
SELECT 'search_results_log',
    CASE WHEN OBJECT_ID('search_results_log', 'U') IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END
"@

Run-SqlQuery -query $tableCheckQuery -description "1. Checking table existence:"

# 2. Check row counts
$rowCountQuery = @"
SELECT 'document_embeddings' as TableName, COUNT(*) as RowCount FROM document_embeddings
UNION ALL
SELECT 'node_embeddings', COUNT(*) FROM node_embeddings
UNION ALL
SELECT 'query_embeddings_cache', COUNT(*) FROM query_embeddings_cache
UNION ALL
SELECT 'embedding_jobs', COUNT(*) FROM embedding_jobs
UNION ALL
SELECT 'search_results_log', COUNT(*) FROM search_results_log
"@

Run-SqlQuery -query $rowCountQuery -description "2. Checking row counts:"

# 3. Check documents needing embeddings
$documentsQuery = @"
SELECT TOP 5
    d.id as DocumentID,
    LEFT(d.title, 50) as Title,
    CASE WHEN de.document_id IS NULL THEN 'NEEDS EMBEDDINGS' ELSE 'HAS EMBEDDINGS' END as Status
FROM documents d
LEFT JOIN document_embeddings de ON d.id = de.document_id
GROUP BY d.id, d.title, de.document_id
ORDER BY d.id DESC
"@

Run-SqlQuery -query $documentsQuery -description "3. Documents embedding status:"

# 4. Check foreign key constraints
$fkQuery = @"
SELECT 
    fk.name as ForeignKey,
    OBJECT_NAME(fk.parent_object_id) as FromTable,
    OBJECT_NAME(fk.referenced_object_id) as ToTable
FROM sys.foreign_keys fk
WHERE fk.parent_object_id IN (
    OBJECT_ID('document_embeddings'),
    OBJECT_ID('node_embeddings'),
    OBJECT_ID('embedding_jobs'),
    OBJECT_ID('search_results_log')
)
"@

Run-SqlQuery -query $fkQuery -description "4. Foreign key relationships:"

# Summary
Write-Host "`n===================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

# Get table status for summary
$tables = @("document_embeddings", "node_embeddings", "query_embeddings_cache", "embedding_jobs", "search_results_log")
$allTablesExist = $true

foreach ($table in $tables) {
    $checkQuery = "SELECT CASE WHEN OBJECT_ID('$table', 'U') IS NOT NULL THEN 1 ELSE 0 END as Exists"
    $result = az sql db query `
        --resource-group $resourceGroup `
        --server $serverName `
        --database $databaseName `
        --query-text "$checkQuery" `
        --output tsv 2>$null
    
    if ($result -eq "1") {
        Write-Host "✅ $table" -ForegroundColor Green
    } else {
        Write-Host "❌ $table" -ForegroundColor Red
        $allTablesExist = $false
    }
}

Write-Host "`n===================================" -ForegroundColor Cyan

if ($allTablesExist) {
    Write-Host "`n✅ All embedding tables are properly set up!" -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "1. Deploy the updated orchestrator code" -ForegroundColor White
    Write-Host "2. New documents will automatically get embeddings" -ForegroundColor White
    Write-Host "3. For existing documents, run a migration script" -ForegroundColor White
} else {
    Write-Host "`n❌ Some tables are missing. Please run the fix script." -ForegroundColor Red
    Write-Host "Run: ./run_sql_migration.ps1" -ForegroundColor Yellow
}

# Check if OpenAI key is configured
Write-Host "`nChecking Azure App Service configuration..." -ForegroundColor Cyan
$appSettings = az webapp config appsettings list `
    --resource-group $resourceGroup `
    --name km-orchestrator `
    --query "[?name=='OPENAI_API_KEY'].value" `
    --output tsv 2>$null

if ($appSettings) {
    Write-Host "✅ OPENAI_API_KEY is configured" -ForegroundColor Green
} else {
    Write-Host "❌ OPENAI_API_KEY is not configured" -ForegroundColor Red
    Write-Host "Run: ./configure_azure_settings.ps1" -ForegroundColor Yellow
}