# Clean up current directory for migration to fresh repository
Write-Host "🧹 Cleaning up code for fresh repository migration..." -ForegroundColor Cyan

# Items to clean up
$itemsToClean = @(
    "node_modules",
    "dist", 
    ".astro",
    "package-lock.json",
    ".npm",
    ".cache",
    ".temp",
    "build"
)

Write-Host "`nRemoving build artifacts and caches..." -ForegroundColor Yellow
foreach ($item in $itemsToClean) {
    if (Test-Path $item) {
        Remove-Item $item -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "✅ Removed: $item" -ForegroundColor Green
    } else {
        Write-Host "⏭️  Not found: $item" -ForegroundColor Gray
    }
}

# Remove problematic GitHub workflows (we'll create fresh ones)
Write-Host "`nRemoving old GitHub workflows..." -ForegroundColor Yellow
if (Test-Path ".github") {
    Remove-Item ".github" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "✅ Removed: .github directory (will recreate fresh)" -ForegroundColor Green
} else {
    Write-Host "⏭️  No .github directory found" -ForegroundColor Gray
}

# Remove other problematic files
$problemFiles = @(
    ".deployment",
    "build.sh",
    "web.config",
    "staticwebapp.config.json"
)

Write-Host "`nRemoving deployment configuration files..." -ForegroundColor Yellow
foreach ($file in $problemFiles) {
    if (Test-Path $file) {
        Remove-Item $file -Force -ErrorAction SilentlyContinue
        Write-Host "✅ Removed: $file" -ForegroundColor Green
    }
}

# Show what remains
Write-Host "`n📁 Remaining files for migration:" -ForegroundColor Blue
Get-ChildItem -Force | Where-Object { 
    $_.Name -notlike "prepare-for-migration.ps1" -and 
    $_.Name -notlike "fresh-*" 
} | ForEach-Object {
    if ($_.PSIsContainer) {
        Write-Host "📂 $($_.Name)/" -ForegroundColor Cyan
    } else {
        Write-Host "📄 $($_.Name)" -ForegroundColor White
    }
}

Write-Host "`n✅ Code cleaned and ready for migration to fresh repository!" -ForegroundColor Green
Write-Host "`n🚀 Next steps:" -ForegroundColor Yellow
Write-Host "1. Create new GitHub repository" -ForegroundColor White
Write-Host "2. Copy these cleaned files to a new directory" -ForegroundColor White
Write-Host "3. Use the fresh-* files I created" -ForegroundColor White
Write-Host "4. Initialize git and push to new repo" -ForegroundColor White
