"""
KM Orchestrator - Intelligent Request Routing for Knowledge Management System
FastAPI service that routes requests across all MCP services
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import httpx
import asyncio
from typing import Dict, List, Any, Optional
import json
from datetime import datetime
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="KM Orchestrator",
    description="Intelligent request routing and workflow orchestration for Knowledge Management System",
    version="1.0.0"
)

# Mount static files
if os.path.exists("public"):
    app.mount("/static", StaticFiles(directory="public"), name="static")

# Service endpoints
SERVICES = {
    "km-mcp-sql-docs": "https://km-mcp-sql-docs.azurewebsites.net",
    "km-mcp-search": "https://km-mcp-search.azurewebsites.net",
    "km-mcp-llm": "https://km-mcp-llm.azurewebsites.net",
    "km-mcp-graphrag": "https://km-mcp-graphrag.azurewebsites.net"
}

@app.get("/")
async def dashboard():
    """Serve the complete dashboard from file"""
    dashboard_path = "public/index.html"
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    elif os.path.exists("index.html"):
        return FileResponse("index.html")
    else:
        return HTMLResponse("""
        <html><body style="font-family: Arial; padding: 20px;">
        <h1>🎯 KM Orchestrator</h1>
        <p>Dashboard file not found. Please ensure index.html exists.</p>
        <a href="/docs">View API Documentation</a>
        </body></html>
        """)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "km-orchestrator",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/services/status")
async def services_status():
    """Get detailed status of all MCP services"""
    status = {}
    
    for service_name, service_url in SERVICES.items():
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{service_url}/health")
                status[service_name] = {
                    "online": response.status_code == 200,
                    "url": service_url,
                    "last_check": datetime.utcnow().isoformat()
                }
        except Exception as e:
            status[service_name] = {
                "online": False,
                "url": service_url,
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    return {
        "services": status,
        "summary": {
            "total_services": len(SERVICES),
            "online_services": sum(1 for s in status.values() if s.get("online", False)),
            "timestamp": datetime.utcnow().isoformat()
        }
    }

@app.post("/api/chat")
async def chat_orchestration(request: Request):
    """Simple working chat with document search"""
    try:
        body = await request.json()
        user_message = body.get("message", "")
        
        # Search for documents
        search_count = 0
        ai_response = "Hello! I'm your knowledge base assistant."
        
        if user_message:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    search_response = await client.post(
                        "https://km-mcp-sql-docs.azurewebsites.net/tools/search-documents",
                        json={"query": user_message, "limit": 5}
                    )
                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        if search_data.get("success"):
                            documents = search_data.get("documents", [])
                            search_count = len(documents)
                            
                            if search_count > 0:
                                titles = [doc.get("title", "Untitled") for doc in documents[:3]]
                                ai_response = f"I found {search_count} documents about '{user_message}'. Top results: {', '.join(titles)}. The AI analysis feature is being enhanced."
                            else:
                                ai_response = f"I searched for '{user_message}' but didn't find matching documents. Try topics like 'artificial intelligence', 'machine learning', or 'orchestrator'."
            except:
                ai_response = f"I'm having trouble searching for '{user_message}' right now. The search service may be temporarily unavailable."
        
        return {
            "user_message": user_message,
            "relevant_documents": search_count,
            "ai_response": ai_response,
            "status": "success" if search_count > 0 else "no_results",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "user_message": "Error",
            "relevant_documents": 0,
            "ai_response": "I'm experiencing technical difficulties. Please try again.",
            "status": "error",
            "timestamp": datetime.utcnow().isoformat()
        }

# Other endpoints preserved
@app.post("/api/upload")
async def upload_orchestration(request: Request):
    """Orchestrate document upload across services"""
    try:
        body = await request.json()
        # Ensure UTF-8 encoding for all text fields
        form_data = {
            'title': str(body.get('title', '')).encode('utf-8').decode('utf-8'),
            'content': str(body.get('content', '')).encode('utf-8').decode('utf-8'),
            'classification': str(body.get('classification', '')).encode('utf-8').decode('utf-8'),
            'entities': str(body.get('entities', '')).encode('utf-8').decode('utf-8'),
            'metadata': str(body.get('metadata', '{}')).encode('utf-8').decode('utf-8')
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://km-mcp-sql-docs.azurewebsites.net/tools/store-document",
                data=form_data
            )
            return response.json()
    except UnicodeDecodeError as e:
        return {
            "status": "error",
            "message": f"Text encoding error: {str(e)}",
            "suggestion": "Please ensure your document contains valid UTF-8 text"
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Upload failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/api/search") 
async def search_orchestration(request: Request):
    """Orchestrate search across all services"""
    try:
        body = await request.json()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://km-mcp-sql-docs.azurewebsites.net/tools/search-documents",
                json=body
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_orchestration(request: Request):
    """Orchestrate AI analysis across services"""
    try:
        body = await request.json()
        return {
            "status": "analysis_ready", 
            "message": "Analysis orchestration endpoint - routes to LLM and GraphRAG services",
            "request": body
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


@app.get("/diagnostics")
async def diagnostics_dashboard():
    """Comprehensive system diagnostics dashboard"""
    try:
        return FileResponse("public/diagnostics.html")
    except FileNotFoundError:
        return HTMLResponse("<h1>Diagnostics dashboard not found</h1>")
