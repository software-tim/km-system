# Configure Azure App Service settings for semantic search
# Run this after deploying the SQL scripts

$resourceGroup = "km-group"
$orchestratorApp = "km-orchestrator"

Write-Host "Configuring Azure App Service settings for semantic search..." -ForegroundColor Green

# Check if logged in
$account = az account show 2>$null
if (-not $account) {
    Write-Host "Please login to Azure..." -ForegroundColor Yellow
    az login
}

Write-Host "`nAdding required app settings to $orchestratorApp..." -ForegroundColor Cyan

# Add OPENAI_API_KEY (you'll need to set this value)
Write-Host "Please enter your OpenAI API key:" -ForegroundColor Yellow
$openaiKey = Read-Host -AsSecureString
$openaiKeyPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($openaiKey))

# Set app settings
az webapp config appsettings set `
    --resource-group $resourceGroup `
    --name $orchestratorApp `
    --settings `
    OPENAI_API_KEY=$openaiKeyPlain `
    EMBEDDING_MODEL="text-embedding-ada-002" `
    EMBEDDING_DIMENSION="1536" `
    EMBEDDING_BATCH_SIZE="20"

Write-Host "`n✅ App settings configured!" -ForegroundColor Green

# Also update km-mcp-search if it needs real implementation
$searchApp = "km-mcp-search"
Write-Host "`nConfiguring $searchApp..." -ForegroundColor Cyan

az webapp config appsettings set `
    --resource-group $resourceGroup `
    --name $searchApp `
    --settings `
    OPENAI_API_KEY=$openaiKeyPlain `
    SEARCH_TYPE="semantic"

Write-Host "`n✅ All services configured for semantic search!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Run the SQL scripts to create embedding tables" -ForegroundColor White
Write-Host "2. Deploy the updated orchestrator code" -ForegroundColor White
Write-Host "3. Process existing documents to generate embeddings" -ForegroundColor White