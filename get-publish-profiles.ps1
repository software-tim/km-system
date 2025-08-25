# PowerShell script to get publish profiles for GitHub Actions
# Resource group: km-group
# Username: software-tim

Write-Host "Getting publish profiles for KM services..." -ForegroundColor Green

# Login to Azure (if not already logged in)
Write-Host "`nChecking Azure login status..." -ForegroundColor Yellow
$account = az account show 2>$null
if (-not $account) {
    Write-Host "Please login to Azure..." -ForegroundColor Yellow
    az login
}

# Set the resource group
$resourceGroup = "km-group"

Write-Host "`nGetting publish profiles from resource group: $resourceGroup" -ForegroundColor Green

# Function to get publish profile
function Get-PublishProfile {
    param (
        [string]$appName
    )
    
    Write-Host "`nGetting publish profile for: $appName" -ForegroundColor Cyan
    
    try {
        $profile = az webapp deployment list-publishing-profiles `
            --name $appName `
            --resource-group $resourceGroup `
            --xml
        
        if ($profile) {
            $fileName = "$appName-publish-profile.xml"
            $profile | Out-File -FilePath $fileName -Encoding UTF8
            Write-Host "✓ Saved to: $fileName" -ForegroundColor Green
            Write-Host "  Add this as GitHub secret: AZURE_WEBAPP_PUBLISH_PROFILE_$($appName.ToUpper().Replace('-', '_'))" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "✗ Failed to get profile for $appName" -ForegroundColor Red
        Write-Host "  Error: $_" -ForegroundColor Red
    }
}

# Get publish profiles for each service
$services = @(
    "km-orchestrator",
    "km-ui",
    "km-mcp-sql-docs",
    "km-mcp-graphrag",
    "km-mcp-llm",
    "km-mcp-search"
)

foreach ($service in $services) {
    Get-PublishProfile -appName $service
}

Write-Host "`n`nNext steps:" -ForegroundColor Green
Write-Host "1. Go to your GitHub repository settings" -ForegroundColor White
Write-Host "2. Navigate to Settings > Secrets and variables > Actions" -ForegroundColor White
Write-Host "3. Add each publish profile as a new secret with the names shown above" -ForegroundColor White
Write-Host "4. Copy the entire content of each .xml file as the secret value" -ForegroundColor White
Write-Host "`nOnce done, delete the .xml files for security!" -ForegroundColor Yellow