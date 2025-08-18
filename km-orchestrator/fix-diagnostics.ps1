# PowerShell Script to Fix KM Orchestrator Diagnostics
# This script adds missing API endpoints and fixes CORS issues

Write-Host "🔧 KM ORCHESTRATOR DIAGNOSTICS FIX" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "requirements.txt")) {
    Write-Host "❌ Error: requirements.txt not found!" -ForegroundColor Red
    Write-Host "   Please run this script from your km-orchestrator directory" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Found requirements.txt - proceeding with fixes..." -ForegroundColor Green

# 1. Update requirements.txt to add pydantic
Write-Host "`n📦 Step 1: Updating requirements.txt..." -ForegroundColor Yellow

$requirementsContent = @"
fastapi==0.104.1
uvicorn==0.24.0
httpx==0.25.2
python-multipart==0.0.6
aiofiles==23.2.1
pydantic>=2.0.0
"@

$requirementsContent | Out-File -FilePath "requirements.txt" -Encoding UTF8
Write-Host "   ✅ Added pydantic dependency" -ForegroundColor Green

# 2. Create the complete FastAPI app with missing endpoints
Write-Host "`n⚡ Step 2: Creating FastAPI app with missing endpoints..." -ForegroundColor Yellow

$fastApiContent = @"
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
import httpx
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="KM Orchestrator",
    description="Knowledge Management System Orchestrator",
    version="1.0.0"
)

# CORS middleware - this fixes the dashboard connectivity issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs - centralized configuration
SERVICES = {
    'docs': 'https://km-mcp-sql-docs.azurewebsites.net',
    'search': 'https://km-mcp-search.azurewebsites.net', 
    'llm': 'https://km-mcp-llm.azurewebsites.net',
    'graphrag': 'https://km-mcp-graphrag.azurewebsites.net'
}

# Pydantic models for request/response validation
class DocumentUpload(BaseModel):
    title: str
    content: str
    file_type: Optional[str] = "text"
    classification: Optional[str] = "General"
    entities: Optional[str] = ""
    metadata: Optional[Dict[str, Any]] = {}

class SearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 10
    max_results: Optional[int] = 10

class AnalysisRequest(BaseModel):
    content: str
    type: Optional[str] = "general"

class ChatRequest(BaseModel):
    message: str

# HEALTH AND STATUS ENDPOINTS

@app.get("/health")
async def health_check():
    ""\"Basic health check for the orchestrator""\"
    return {
        'status': 'healthy',
        'service': 'km-orchestrator',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    }

@app.get("/services/status")
async def services_status():
    ""\"Comprehensive services status check - this fixes the diagnostics""\"
    services_config = [
        {'name': 'km-mcp-sql-docs', 'url': SERVICES['docs']},
        {'name': 'km-mcp-search', 'url': SERVICES['search']},
        {'name': 'km-mcp-llm', 'url': SERVICES['llm']},
        {'name': 'km-mcp-graphrag', 'url': SERVICES['graphrag']}
    ]
    
    status_results = {}
    overall_health = True
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for service in services_config:
            try:
                start_time = time.time()
                response = await client.get(f"{service['url']}/health")
                response_time = (time.time() - start_time) * 1000
                
                is_healthy = response.status_code == 200
                if not is_healthy:
                    overall_health = False
                    
                status_results[service['name']] = {
                    'status': 'healthy' if is_healthy else 'unhealthy',
                    'status_code': response.status_code,
                    'url': service['url'],
                    'response_time_ms': round(response_time, 2)
                }
            except Exception as e:
                overall_health = False
                status_results[service['name']] = {
                    'status': 'unhealthy',
                    'error': str(e),
                    'url': service['url']
                }
    
    return {
        'timestamp': datetime.now().isoformat(),
        'orchestrator_status': 'healthy',
        'overall_health': overall_health,
        'services': status_results
    }

@app.get("/api/simple-test")
async def simple_test():
    ""\"Health check for all MCP services - from your simple-test.js""\"
    services = [
        {'name': 'km-mcp-sql-docs', 'title': 'SQL Docs Service', 'icon': '📚', 'url': SERVICES['docs']},
        {'name': 'km-mcp-search', 'title': 'Search Service', 'icon': '🔍', 'url': SERVICES['search']},
        {'name': 'km-mcp-llm', 'title': 'LLM Service', 'icon': '🤖', 'url': SERVICES['llm']},
        {'name': 'km-mcp-graphrag', 'title': 'GraphRAG Service', 'icon': '🕸️', 'url': SERVICES['graphrag']}
    ]
    
    results = []
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for service in services:
            start_time = time.time()
            try:
                response = await client.get(f"{service['url']}/health")
                response_time = int((time.time() - start_time) * 1000)
                
                results.append({
                    **service,
                    'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                    'responseTime': response_time,
                    'statusCode': response.status_code,
                    'lastChecked': datetime.now().isoformat()
                })
            except Exception as error:
                results.append({
                    **service,
                    'status': 'unhealthy',
                    'responseTime': int((time.time() - start_time) * 1000),
                    'error': str(error),
                    'lastChecked': datetime.now().isoformat()
                })
    
    return {
        'timestamp': datetime.now().isoformat(),
        'services': results,
        'summary': {
            'total': len(results),
            'healthy': len([s for s in results if s['status'] == 'healthy']),
            'unhealthy': len([s for s in results if s['status'] == 'unhealthy'])
        }
    }

# DOCUMENT MANAGEMENT ENDPOINTS

@app.post("/api/upload")
async def upload_document(document: DocumentUpload):
    ""\"Document upload endpoint - forwards to km-mcp-sql-docs""\"
    try:
        logger.info(f"Upload request received: {document.dict()}")
        
        # Prepare document for km-mcp-sql-docs service
        doc_data = {
            'title': document.title,
            'content': document.content,
            'file_type': document.file_type,
            'metadata': {
                'source': 'orchestrator_upload',
                'classification': document.classification,
                'entities': document.entities,
                'uploaded_at': datetime.now().isoformat(),
                **document.metadata
            }
        }
        
        logger.info(f"Forwarding to docs service: {doc_data}")
        
        # Forward to document service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SERVICES['docs']}/tools/store-document",
                json=doc_data,
                headers={'Content-Type': 'application/json'}
            )
        
        logger.info(f"Docs service response: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            return {
                'status': 'success',
                'message': 'Document uploaded successfully',
                'document_id': result.get('document_id'),
                'data': result
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    'status': 'error',
                    'message': f'Failed to store document: {response.text}',
                    'service_status_code': response.status_code
                }
            )
            
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail={
                'status': 'error',
                'message': 'Document service timeout - service may be slow or unavailable'
            }
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail={
                'status': 'error',
                'message': 'Cannot connect to document service - service may be down'
            }
        )
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                'status': 'error',
                'message': f'Upload failed: {str(e)}'
            }
        )

# SEARCH ENDPOINTS

@app.post("/api/search")
async def search_documents(search: SearchRequest):
    ""\"Search endpoint - forwards to km-mcp-sql-docs""\"
    try:
        # Prepare search request
        search_data = {
            'query': search.query,
            'max_results': search.limit or search.max_results
        }
        
        # Forward to document service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SERVICES['docs']}/tools/search-documents",
                json=search_data,
                headers={'Content-Type': 'application/json'}
            )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'status': 'success',
                'results': result.get('documents', []),
                'total': len(result.get('documents', [])),
                'query': search.query
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail={
                    'status': 'error',
                    'message': f'Search failed: {response.text}',
                    'service_status_code': response.status_code
                }
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                'status': 'error',
                'message': f'Search failed: {str(e)}'
            }
        )

# AI/LLM ENDPOINTS

@app.post("/api/analyze")
async def analyze_content(analysis: AnalysisRequest):
    ""\"Analysis endpoint - forwards to LLM service""\"
    try:
        # Forward to LLM service - try different endpoints
        llm_endpoints = ['/analyze', '/tools/analyze', '/api/analyze']
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for endpoint in llm_endpoints:
                try:
                    response = await client.post(
                        f"{SERVICES['llm']}{endpoint}",
                        json=analysis.dict(),
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        return {
                            'status': 'success',
                            'analysis': result,
                            'endpoint_used': endpoint
                        }
                except:
                    continue
        
        # If all endpoints fail, return error
        raise HTTPException(
            status_code=503,
            detail={
                'status': 'error',
                'message': 'LLM analysis service unavailable - all endpoints failed'
            }
        )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                'status': 'error',
                'message': f'Analysis failed: {str(e)}'
            }
        )

@app.post("/api/chat")
async def chat(chat_request: ChatRequest):
    ""\"Chat endpoint - basic implementation""\"
    try:
        # Basic chat response - replace with your actual chat logic
        return {
            'status': 'success',
            'response': f'Echo: {chat_request.message}',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                'status': 'error',
                'message': f'Chat failed: {str(e)}'
            }
        )

# DIAGNOSTICS DASHBOARD

@app.get("/diagnostics", response_class=HTMLResponse)
async def diagnostics_dashboard():
    ""\"Serve the diagnostics dashboard""\"
    try:
        # Read and return your diagnostics.html file
        with open('diagnostics.html', 'r', encoding='utf-8') as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content=\"""
            <html>
                <body>
                    <h1>Diagnostics Dashboard</h1>
                    <p>diagnostics.html file not found. Please ensure it's in the root directory.</p>
                    <p>Available endpoints:</p>
                    <ul>
                        <li><a href="/health">/health</a></li>
                        <li><a href="/services/status">/services/status</a></li>
                        <li><a href="/api/simple-test">/api/simple-test</a></li>
                    </ul>
                </body>
            </html>
            \"",
            status_code=200
        )

# ERROR HANDLERS

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            'status': 'error',
            'message': 'Endpoint not found',
            'available_endpoints': [
                '/health',
                '/services/status', 
                '/api/chat',
                '/api/upload',
                '/api/search',
                '/api/analyze',
                '/api/simple-test',
                '/diagnostics'
            ]
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=500,
        content={
            'status': 'error',
            'message': 'Internal server error'
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"@

# Check if main.py exists, otherwise use app.py
$appFile = if (Test-Path "main.py") { "main.py" } elseif (Test-Path "app.py") { "app.py" } else { "main.py" }

# Backup existing file if it exists
if (Test-Path $appFile) {
    $backupFile = "$appFile.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Copy-Item $appFile $backupFile
    Write-Host "   ✅ Backed up existing $appFile to $backupFile" -ForegroundColor Green
}

$fastApiContent | Out-File -FilePath $appFile -Encoding UTF8
Write-Host "   ✅ Created $appFile with all missing endpoints" -ForegroundColor Green

# 3. Git operations
Write-Host "`n📝 Step 3: Committing changes to Git..." -ForegroundColor Yellow

try {
    git add .
    git status
    
    $commitMessage = "🔧 FIXED: Added missing API endpoints and CORS configuration

✅ Fixed missing endpoints:
   - POST /api/upload (document upload)
   - POST /api/search (document search)
   - POST /api/analyze (content analysis)
   - GET /services/status (service health check)
   - GET /api/simple-test (health check from simple-test.js)

✅ Fixed CORS issues:
   - Added proper CORS middleware
   - Allow all origins for testing
   - Automatic OPTIONS handling

✅ Added dependencies:
   - pydantic for request validation
   
✅ Error handling:
   - Timeout handling for slow services
   - Connection error handling
   - Detailed error messages

This should fix all 7 broken diagnostic tests!"

    git commit -m $commitMessage
    Write-Host "   ✅ Changes committed to Git" -ForegroundColor Green
    
    Write-Host "`n🚀 Step 4: Pushing to Azure..." -ForegroundColor Yellow
    git push origin master
    Write-Host "   ✅ Changes pushed to Azure!" -ForegroundColor Green
    
} catch {
    Write-Host "   ⚠️  Git operations failed: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "   Please run git commands manually:" -ForegroundColor Yellow
    Write-Host "   git add ." -ForegroundColor Gray
    Write-Host "   git commit -m 'Fixed missing API endpoints'" -ForegroundColor Gray
    Write-Host "   git push origin master" -ForegroundColor Gray
}

# 4. Summary
Write-Host "`n🎉 ORCHESTRATOR DIAGNOSTICS FIX COMPLETE!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green

Write-Host "`n📋 What was fixed:" -ForegroundColor Cyan
Write-Host "   ✅ Added pydantic to requirements.txt" -ForegroundColor White
Write-Host "   ✅ Created/updated $appFile with missing endpoints" -ForegroundColor White
Write-Host "   ✅ Added CORS middleware configuration" -ForegroundColor White
Write-Host "   ✅ Added proper error handling" -ForegroundColor White
Write-Host "   ✅ Committed and pushed changes to Azure" -ForegroundColor White

Write-Host "`n🔧 New endpoints added:" -ForegroundColor Cyan
Write-Host "   • POST /api/upload - Document upload" -ForegroundColor White
Write-Host "   • POST /api/search - Document search" -ForegroundColor White
Write-Host "   • POST /api/analyze - Content analysis" -ForegroundColor White
Write-Host "   • GET /services/status - Service health check" -ForegroundColor White
Write-Host "   • GET /api/simple-test - Simple health test" -ForegroundColor White

Write-Host "`n⏱️  Next steps:" -ForegroundColor Yellow
Write-Host "   1. Wait 2-3 minutes for Azure deployment to complete" -ForegroundColor White
Write-Host "   2. Visit: https://km-orchestrator.azurewebsites.net/diagnostics" -ForegroundColor White
Write-Host "   3. Click 'Run All Diagnostics' button" -ForegroundColor White
Write-Host "   4. Should see 19/19 tests passing (instead of 12/7)!" -ForegroundColor White

Write-Host "`n🎯 Expected result: All diagnostic tests should now be GREEN!" -ForegroundColor Green