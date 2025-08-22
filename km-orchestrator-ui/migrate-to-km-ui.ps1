# Complete automated migration to km-ui repository
Write-Host "🆕 Migrating to fresh km-ui repository..." -ForegroundColor Cyan

$repoName = "km-ui"
$username = "software-tim"
$repoUrl = "https://github.com/$username/$repoName.git"

Write-Host "`n📋 Repository Details:" -ForegroundColor Blue
Write-Host "• Name: $repoName" -ForegroundColor White
Write-Host "• Username: $username" -ForegroundColor White
Write-Host "• URL: $repoUrl" -ForegroundColor White

# Step 1: Check if repository exists on GitHub
Write-Host "`n🔍 Step 1: Checking if GitHub repository exists..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "https://api.github.com/repos/$username/$repoName" -Method GET -ErrorAction Stop
    Write-Host "✅ Repository exists on GitHub!" -ForegroundColor Green
} catch {
    Write-Host "❌ Repository does not exist yet!" -ForegroundColor Red
    Write-Host "`n📋 Please create it first:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://github.com/new" -ForegroundColor White
    Write-Host "2. Repository name: $repoName" -ForegroundColor White
    Write-Host "3. Keep it public or make private" -ForegroundColor White
    Write-Host "4. DON'T add README, .gitignore, or license" -ForegroundColor White
    Write-Host "5. Click ''Create repository''" -ForegroundColor White
    Write-Host "`n🔗 Direct link: https://github.com/new" -ForegroundColor Cyan
    
    $continue = Read-Host "`nPress Enter after creating the repository, or type ''exit'' to stop"
    if ($continue -eq "exit") { exit 0 }
}

# Step 2: Clean current directory
Write-Host "`n🧹 Step 2: Cleaning current directory..." -ForegroundColor Yellow
$itemsToClean = @("node_modules", "dist", ".astro", "package-lock.json", ".npm", ".cache", ".github")
foreach ($item in $itemsToClean) {
    if (Test-Path $item) {
        Remove-Item $item -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "✅ Removed: $item" -ForegroundColor Green
    }
}

# Step 3: Create new directory
Write-Host "`n📁 Step 3: Creating fresh directory..." -ForegroundColor Yellow
$newDir = "../$repoName"
if (Test-Path $newDir) {
    Remove-Item $newDir -Recurse -Force
}
New-Item -Path $newDir -ItemType Directory -Force | Out-Null
Write-Host "✅ Created: $newDir" -ForegroundColor Green

# Step 4: Copy files
Write-Host "`n📋 Step 4: Copying files..." -ForegroundColor Yellow
$excludeFiles = @("*.ps1", "fresh-*")
Get-ChildItem -Force | Where-Object { 
    $exclude = $false
    foreach ($pattern in $excludeFiles) {
        if ($_.Name -like $pattern) { $exclude = $true; break }
    }
    -not $exclude
} | ForEach-Object {
    if ($_.PSIsContainer) {
        Copy-Item $_.FullName -Destination $newDir -Recurse -Force
    } else {
        Copy-Item $_.FullName -Destination $newDir -Force
    }
    Write-Host "✅ Copied: $($_.Name)" -ForegroundColor Green
}

# Step 5: Create fresh configurations
Write-Host "`n⚙️ Step 5: Creating fresh configurations..." -ForegroundColor Yellow
Push-Location $newDir

# Create astro.config.mjs
$astroConfig = @"
import { defineConfig } from ''astro/config'';
import node from ''@astrojs/node'';

export default defineConfig({
  output: ''server'',
  adapter: node({
    mode: ''standalone''
  }),
  site: ''https://km-orchestrator.azurewebsites.net'',
  server: {
    port: process.env.PORT || 4321,
    host: true
  }
});
"@
$astroConfig | Out-File -FilePath "astro.config.mjs" -Encoding UTF8

# Create package.json (UTF8NoBOM)
$packageJson = @"
{
  "name": "km-ui",
  "type": "module",
  "version": "1.0.0",
  "scripts": {
    "dev": "astro dev",
    "start": "node ./dist/server/entry.mjs",
    "build": "astro build",
    "preview": "astro preview"
  },
  "dependencies": {
    "astro": "^4.16.18",
    "@astrojs/node": "^8.3.4"
  },
  "engines": {
    "node": ">=18.0.0"
  }
}
"@
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText("package.json", $packageJson, $utf8NoBom)

# Create GitHub workflow
New-Item -Path ".github/workflows" -ItemType Directory -Force | Out-Null
$workflow = @"
name: Deploy km-ui

on:
  push:
    branches: [ master ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ''18''
          cache: ''npm''
      - run: npm ci
      - run: npm run build
      - uses: azure/webapps-deploy@v2
        with:
          app-name: ''km-orchestrator''
          publish-profile: `${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
          package: ''./dist''
"@
$workflow | Out-File -FilePath ".github/workflows/deploy.yml" -Encoding UTF8

# Create .gitignore
$gitignore = @"
node_modules/
dist/
.astro/
package-lock.json
.env
*.log
"@
$gitignore | Out-File -FilePath ".gitignore" -Encoding UTF8

Write-Host "✅ Created all configurations" -ForegroundColor Green

# Step 6: Git setup and push
Write-Host "`n🚀 Step 6: Setting up git and pushing..." -ForegroundColor Yellow
git init
git add .
git commit -m "Initial commit - Fresh km-ui"
git branch -M master
git remote add origin $repoUrl
git push -u origin master

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n🎉 SUCCESS! Repository created and pushed!" -ForegroundColor Green
    Write-Host "`n📋 Next steps:" -ForegroundColor Blue
    Write-Host "1. Go to GitHub: $repoUrl" -ForegroundColor White
    Write-Host "2. Go to repository Settings → Secrets and variables → Actions" -ForegroundColor White
    Write-Host "3. Add secret: AZURE_WEBAPP_PUBLISH_PROFILE" -ForegroundColor White
    Write-Host "4. Go to Azure Portal → App Service → Deployment Center" -ForegroundColor White
    Write-Host "5. Disconnect old repo and connect to: $username/$repoName" -ForegroundColor White
    Write-Host "`n🌐 Repository: $repoUrl" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Git push failed! Check if repository exists and try again." -ForegroundColor Red
}

Pop-Location
