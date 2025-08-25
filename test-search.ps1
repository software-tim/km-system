# Test search functionality
Write-Host "Testing KM Search API..." -ForegroundColor Green

# Test 1: Basic search
Write-Host "`nTest 1: Basic keyword search" -ForegroundColor Yellow
$response1 = Invoke-RestMethod -Uri "https://km-orchestrator.azurewebsites.net/api/search?q=document&limit=5" -Method Get
Write-Host "Results found: $($response1.total)"
Write-Host "Search type: $($response1.search_type)"
Write-Host "Status: $($response1.status)"

# Test 2: Semantic search
Write-Host "`nTest 2: Semantic search with AI enhancement" -ForegroundColor Yellow
$response2 = Invoke-RestMethod -Uri "https://km-orchestrator.azurewebsites.net/api/search?q=knowledge%20management&limit=10&enhance=true&type=semantic" -Method Get
Write-Host "Results found: $($response2.total)"
Write-Host "Search type: $($response2.search_type)"

# Display results if any
if ($response2.results.Count -gt 0) {
    Write-Host "`nFirst few results:" -ForegroundColor Cyan
    $response2.results | Select-Object -First 3 | ForEach-Object {
        Write-Host "- Document: $($_.document_title)"
        Write-Host "  Score: $($_.relevance_score)"
        Write-Host "  Preview: $($_.chunk_text.Substring(0, [Math]::Min(100, $_.chunk_text.Length)))..."
        Write-Host ""
    }
}

# Test 3: Check search page
Write-Host "`nTest 3: Search page availability" -ForegroundColor Yellow
try {
    $webResponse = Invoke-WebRequest -Uri "https://km-ui.azurewebsites.net/search" -Method Get
    Write-Host "✓ Search page is accessible (Status: $($webResponse.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "✗ Search page error: $_" -ForegroundColor Red
}

Write-Host "`nTo test interactively, visit: https://km-ui.azurewebsites.net/search" -ForegroundColor Cyan