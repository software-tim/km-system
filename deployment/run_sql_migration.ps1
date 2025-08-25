# Run SQL migration to add embedding tables
# Requires Azure CLI and SQL tools

$resourceGroup = "km-group"
$serverName = "knowledge-sql" # Your Azure SQL server
$databaseName = "knowledge-base"
$sqlFile = "../database/add_embedding_tables.sql"

Write-Host "Running SQL migration to add embedding tables..." -ForegroundColor Green

# Get SQL server details
Write-Host "Getting SQL server connection info..." -ForegroundColor Cyan
$server = az sql server show --resource-group $resourceGroup --name $serverName --query fullyQualifiedDomainName -o tsv

if (-not $server) {
    Write-Host "Could not find SQL server. Please check the server name." -ForegroundColor Red
    exit 1
}

Write-Host "SQL Server: $server" -ForegroundColor White

# Run the SQL script using sqlcmd
Write-Host "`nRunning migration script..." -ForegroundColor Cyan
Write-Host "Enter your SQL admin username:" -ForegroundColor Yellow
$username = Read-Host

Write-Host "Enter your SQL admin password:" -ForegroundColor Yellow
$password = Read-Host -AsSecureString
$passwordPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password))

# Execute SQL script
sqlcmd -S $server -d $databaseName -U $username -P $passwordPlain -i $sqlFile

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Migration completed successfully!" -ForegroundColor Green
    Write-Host "Embedding tables have been created in the database." -ForegroundColor White
} else {
    Write-Host "`n❌ Migration failed. Please check the error messages above." -ForegroundColor Red
}

# Alternative: Use Azure Data Studio or SSMS if sqlcmd is not available
Write-Host "`nAlternatively, you can run the SQL script using:" -ForegroundColor Yellow
Write-Host "- Azure Data Studio" -ForegroundColor White
Write-Host "- SQL Server Management Studio (SSMS)" -ForegroundColor White
Write-Host "- Azure Portal Query Editor" -ForegroundColor White
Write-Host "`nSQL script location: $sqlFile" -ForegroundColor Cyan