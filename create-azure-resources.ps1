# Set variables
$RESOURCE_GROUP="km-group"
$LOCATION="eastus2"
$APP_SERVICE_PLAN="km-plan"

# Create Resource Group
Write-Host "Creating Resource Group..." -ForegroundColor Green
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create Premium P0v3 App Service Plan
Write-Host "Creating App Service Plan..." -ForegroundColor Green
az appservice plan create --name $APP_SERVICE_PLAN --resource-group $RESOURCE_GROUP --location $LOCATION --is-linux --sku P0v3

# Create Python 3.10 Web Apps
Write-Host "Creating km-mcp-sql..." -ForegroundColor Green
az webapp create --name km-mcp-sql --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --runtime "PYTHON:3.10"

Write-Host "Creating km-mcp-sql-docs..." -ForegroundColor Green
az webapp create --name km-mcp-sql-docs --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --runtime "PYTHON:3.10"

Write-Host "Creating km-mcp-phi4..." -ForegroundColor Green
az webapp create --name km-mcp-phi4 --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --runtime "PYTHON:3.10"

Write-Host "Creating km-mcp-search..." -ForegroundColor Green
az webapp create --name km-mcp-search --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --runtime "PYTHON:3.10"

Write-Host "Creating km-mcp-graphrag..." -ForegroundColor Green
az webapp create --name km-mcp-graphrag --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --runtime "PYTHON:3.10"

Write-Host "Creating km-orchestrator..." -ForegroundColor Green
az webapp create --name km-orchestrator --resource-group $RESOURCE_GROUP --plan $APP_SERVICE_PLAN --runtime "PYTHON:3.10"

# Create Static Web App
Write-Host "Creating km-ui Static Web App..." -ForegroundColor Green
az staticwebapp create --name km-ui --resource-group $RESOURCE_GROUP --location $LOCATION --sku Free

Write-Host "All resources created successfully!" -ForegroundColor Green