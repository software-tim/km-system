# PowerShell script to verify embedding tables setup
# Alternative approach using invoke-sqlcmd or Azure Portal

$resourceGroup = "km-group"
$serverName = "knowledge-sql"
$databaseName = "knowledge-base"

Write-Host "Verifying Embedding Tables Setup..." -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

# Method 1: Try using Invoke-Sqlcmd if available
$sqlcmdAvailable = Get-Command Invoke-Sqlcmd -ErrorAction SilentlyContinue

if ($sqlcmdAvailable) {
    Write-Host "Using Invoke-Sqlcmd..." -ForegroundColor Green
    
    Write-Host "Enter SQL credentials:" -ForegroundColor Yellow
    $cred = Get-Credential -UserName "software-tim" -Message "Enter SQL Password"
    
    $params = @{
        ServerInstance = "$serverName.database.windows.net"
        Database = $databaseName
        Username = $cred.UserName
        Password = $cred.GetNetworkCredential().Password
    }
    
    # Check tables
    $tableCheck = @"
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
    
    try {
        $results = Invoke-Sqlcmd @params -Query $tableCheck
        Write-Host "`nTable Status:" -ForegroundColor Yellow
        $results | Format-Table -AutoSize
    } catch {
        Write-Host "Error connecting to database: $_" -ForegroundColor Red
    }
    
} else {
    Write-Host "Invoke-Sqlcmd not available. Install SQL Server module:" -ForegroundColor Yellow
    Write-Host "Install-Module -Name SqlServer -AllowClobber" -ForegroundColor White
}

# Method 2: Alternative verification approach
Write-Host "`n===================================" -ForegroundColor Cyan
Write-Host "Alternative Verification Methods:" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

Write-Host "`n1. Use Azure Portal:" -ForegroundColor Yellow
Write-Host "   - Go to your SQL Database in Azure Portal" -ForegroundColor White
Write-Host "   - Click 'Query editor (preview)'" -ForegroundColor White
Write-Host "   - Run this query:" -ForegroundColor White
Write-Host @"

SELECT 
    t.name as TableName,
    t.create_date as Created,
    p.rows as RowCount
FROM sys.tables t
JOIN sys.partitions p ON t.object_id = p.object_id
WHERE t.name IN ('document_embeddings', 'node_embeddings', 'query_embeddings_cache', 'embedding_jobs', 'search_results_log')
    AND p.index_id <= 1
ORDER BY t.name;

"@ -ForegroundColor Cyan

Write-Host "`n2. Use SSMS (SQL Server Management Studio):" -ForegroundColor Yellow
Write-Host "   - Connect to: $serverName.database.windows.net" -ForegroundColor White
Write-Host "   - Database: $databaseName" -ForegroundColor White
Write-Host "   - Run the verification script: verify_embedding_tables.sql" -ForegroundColor White

Write-Host "`n3. Quick Check - Test if tables exist:" -ForegroundColor Yellow
Write-Host "   Run this simple query in any SQL tool:" -ForegroundColor White
Write-Host @"

SELECT COUNT(*) as TablesFound
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_NAME IN ('document_embeddings', 'node_embeddings', 'query_embeddings_cache', 'embedding_jobs', 'search_results_log');

-- Should return 5 if all tables exist

"@ -ForegroundColor Cyan

# Check App Service settings
Write-Host "`n===================================" -ForegroundColor Cyan
Write-Host "Checking App Service Configuration:" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

try {
    $openaiKey = az webapp config appsettings list `
        --resource-group $resourceGroup `
        --name km-orchestrator `
        --query "[?name=='OPENAI_API_KEY'].value" `
        --output tsv 2>$null
    
    if ($openaiKey) {
        Write-Host "✅ OPENAI_API_KEY is configured in km-orchestrator" -ForegroundColor Green
    } else {
        Write-Host "❌ OPENAI_API_KEY is NOT configured" -ForegroundColor Red
        Write-Host "   Run: ./configure_azure_settings.ps1" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Could not check app settings. Make sure you're logged in to Azure CLI" -ForegroundColor Yellow
}

Write-Host "`n===================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host "1. Verify tables exist using one of the methods above" -ForegroundColor White
Write-Host "2. If tables are missing, run the fix script in SSMS" -ForegroundColor White
Write-Host "3. Configure OpenAI API key if not set" -ForegroundColor White
Write-Host "4. Deploy the updated orchestrator code" -ForegroundColor White