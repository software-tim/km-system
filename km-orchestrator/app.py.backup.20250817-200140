"""
KM Orchestrator - Intelligent Request Routing for Knowledge Management System
FastAPI service that routes requests across all MCP services
Updated with CORS-aware service communication
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
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

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    try:
        return FileResponse("public/index.html")
    except FileNotFoundError:
        return HTMLResponse("""
        <html><body style="font-family: Arial; padding: 20px;">
        <h1>🎯 KM Orchestrator</h1>
        <p>Dashboard file not found. Please ensure index.html exists in public/ directory.</p>
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
    """Get detailed status of all MCP services with server-side calls"""
    status = {}
    
    for service_name, service_url in SERVICES.items():
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start_time = datetime.utcnow()
                response = await client.get(f"{service_url}/health")
                end_time = datetime.utcnow()
                response_time = (end_time - start_time).total_seconds() * 1000
                
                status[service_name] = {
                    "online": response.status_code == 200,
                    "status_code": response.status_code,
                    "response_time_ms": round(response_time, 2),
                    "url": service_url,
                    "last_check": datetime.utcnow().isoformat(),
                    "response_data": response.json() if response.status_code == 200 else None
                }
        except Exception as e:
            status[service_name] = {
                "online": False,
                "status_code": None,
                "response_time_ms": None,
                "url": service_url,
                "error": str(e),
                "error_type": type(e).__name__,
                "last_check": datetime.utcnow().isoformat()
            }
    
    online_services = sum(1 for s in status.values() if s.get("online", False))
    total_services = len(status)
    
    return {
        "services": status,
        "summary": {
            "total_services": total_services,
            "online_services": online_services,
            "offline_services": total_services - online_services,
            "overall_status": "healthy" if online_services == total_services else "degraded",
            "timestamp": datetime.utcnow().isoformat()
        }
    }

@app.post("/api/chat")
async def chat_orchestration(request: Request):
    """Server-side chat with document search - bypasses CORS"""
    try:
        body = await request.json()
        user_message = body.get("message", "")
        
        if not user_message:
            return JSONResponse({
                "status": "error",
                "message": "No message provided",
                "timestamp": datetime.utcnow().isoformat()
            }, status_code=400)

        logger.info(f"Chat request: {user_message}")
        
        # Server-side call to document service (bypasses CORS)
        search_count = 0
        documents = []
        service_errors = []
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Make server-to-server call (no CORS issues)
                search_response = await client.post(
                    f"{SERVICES['km-mcp-sql-docs']}/tools/search-documents",
                    json={"query": user_message, "limit": 5},
                    headers={"Content-Type": "application/json"}
                )
                
                logger.info(f"Search response status: {search_response.status_code}")
                
                if search_response.status_code == 200:
                    search_data = search_response.json()
                    logger.info(f"Search data: {search_data}")
                    
                    if search_data.get("success"):
                        documents = search_data.get("documents", [])
                        search_count = len(documents)
                    else:
                        service_errors.append(f"Search failed: {search_data.get('message', 'Unknown error')}")
                else:
                    service_errors.append(f"Search service returned status {search_response.status_code}")
                    
        except Exception as e:
            service_errors.append(f"Document service error: {str(e)}")
            logger.error(f"Document service error: {e}")

        # Generate AI response
        if search_count > 0:
            doc_titles = [doc.get("title", doc.get("filename", "Unknown")) for doc in documents[:3]]
            ai_response = f"I found {search_count} documents about '{user_message}'. Top results: {', '.join(doc_titles)}. The AI analysis feature is being enhanced."
            status = "success"
        elif service_errors:
            ai_response = f"I searched for '{user_message}' but encountered issues: {'; '.join(service_errors)}. The document service is reachable but may have internal problems."
            status = "service_error"
        else:
            ai_response = f"I searched for '{user_message}' but didn't find matching documents. Try topics like 'artificial intelligence', 'machine learning', or 'data analysis'."
            status = "no_results"

        return {
            "user_message": user_message,
            "relevant_documents": search_count,
            "ai_response": ai_response,
            "status": status,
            "documents": documents[:3],
            "service_errors": service_errors if service_errors else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return JSONResponse({
            "status": "error",
            "message": f"Internal server error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }, status_code=500)

@app.post("/tools/store-document")
async def upload_orchestration(request: Request):
    """Server-side document upload - bypasses CORS"""
    try:
        body = await request.json()
        
        # Prepare form data for the document service
        form_data = {
            'title': str(body.get('title', '')),
            'content': str(body.get('content', '')),
            'classification': str(body.get('classification', '')),
            'entities': str(body.get('entities', '')),
            'metadata': str(body.get('metadata', '{}'))
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SERVICES['km-mcp-sql-docs']}/tools/store-document",
                data=form_data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return JSONResponse({
                    "status": "error",
                    "message": f"Document service returned status {response.status_code}",
                    "details": response.text
                }, status_code=response.status_code)
                
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return JSONResponse({
            "status": "error",
            "message": f"Upload failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }, status_code=500)

@app.post("/tools/search-documents") 
async def search_orchestration(request: Request):
    """Server-side search - bypasses CORS"""
    try:
        body = await request.json()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{SERVICES['km-mcp-sql-docs']}/tools/search-documents",
                json=body
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return JSONResponse({
                    "status": "error", 
                    "message": f"Search service returned status {response.status_code}",
                    "details": response.text
                }, status_code=response.status_code)
                
    except Exception as e:
        logger.error(f"Search error: {e}")
        return JSONResponse({
            "status": "error",
            "message": f"Search failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }, status_code=500)

@app.post("/api/analyze")
async def analyze_orchestration(request: Request):
    """Orchestrate AI analysis across services"""
    try:
        body = await request.json()
        return {
            "status": "analysis_ready", 
            "message": "Analysis orchestration endpoint - routes to LLM and GraphRAG services",
            "request": body,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": f"Analysis error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }, status_code=500)

# Proxy endpoints for direct service access (bypasses CORS)
@app.get("/proxy/docs-stats")
async def proxy_docs_stats():
    """Proxy to document service stats - bypasses CORS"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{SERVICES['km-mcp-sql-docs']}/stats")
            if response.status_code == 200:
                return response.json()
            else:
                return JSONResponse({
                    "error": f"Service returned status {response.status_code}",
                    "details": response.text
                }, status_code=response.status_code)
    except Exception as e:
        return JSONResponse({
            "error": f"Failed to fetch stats: {str(e)}"
        }, status_code=500)

@app.get("/proxy/docs-health")
async def proxy_docs_health():
    """Proxy to document service health - bypasses CORS"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{SERVICES['km-mcp-sql-docs']}/health")
            if response.status_code == 200:
                return response.json()
            else:
                return JSONResponse({
                    "error": f"Service returned status {response.status_code}",
                    "details": response.text
                }, status_code=response.status_code)
    except Exception as e:
        return JSONResponse({
            "error": f"Failed to fetch health: {str(e)}"
        }, status_code=500)

# Service diagnostics and status pages
@app.get("/diagnostics")
async def diagnostics_dashboard():
    """Comprehensive system diagnostics dashboard"""
    try:
        return FileResponse("public/diagnostics.html")
    except FileNotFoundError:
        return HTMLResponse("<h1>Diagnostics dashboard not found</h1>")

@app.get("/enhanced-diagnostics")
async def enhanced_diagnostics():
    """Enhanced diagnostics with CORS and connectivity analysis"""
    try:
        return FileResponse("public/enhanced-diagnostics.html")
    except FileNotFoundError:
        return HTMLResponse("<h1>Enhanced diagnostics not found</h1>")

@app.get("/service-status")
async def service_status_page():
    """Service status monitoring page"""
    try:
        return FileResponse("public/service-status.html")
    except FileNotFoundError:
        return HTMLResponse("<h1>Service status page not found</h1>")

# Comprehensive service diagnostics API
@app.get("/service-diagnostics")
async def detailed_service_diagnostics():
    """Detailed diagnostics for all MCP services"""
    results = {}
    
    for service_name, service_url in SERVICES.items():
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start_time = datetime.utcnow()
                response = await client.get(f"{service_url}/health")
                end_time = datetime.utcnow()
                response_time = (end_time - start_time).total_seconds() * 1000
                
                results[service_name] = {
                    "service": service_name,
                    "url": service_url,
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "status_code": response.status_code,
                    "response_time": round(response_time, 2),
                    "error": None,
                    "last_check": datetime.utcnow().isoformat()
                }
        except Exception as e:
            results[service_name] = {
                "service": service_name,
                "url": service_url,
                "status": "unreachable",
                "status_code": None,
                "response_time": None,
                "error": str(e),
                "error_type": type(e).__name__,
                "last_check": datetime.utcnow().isoformat()
            }
    
    # Generate recommendations
    recommendations = []
    healthy_services = [s for s in results.values() if s["status"] == "healthy"]
    
    for service_name, result in results.items():
        if result["status"] == "unreachable":
            if "timeout" in result.get("error", "").lower():
                recommendations.append(f"🕐 {service_name}: Service timeout - check if service is running")
            elif "connection" in result.get("error", "").lower():
                recommendations.append(f"🚫 {service_name}: Connection refused - service appears down")
            else:
                recommendations.append(f"❓ {service_name}: Check service deployment and URL")
        elif result["status"] == "unhealthy":
            recommendations.append(f"⚠️ {service_name}: Service responding but unhealthy")
    
    if not recommendations:
        recommendations.append("✅ All services are healthy and responding normally")
    
    return {
        "overall_status": "healthy" if len(healthy_services) == len(results) else "degraded",
        "healthy_services": len(healthy_services),
        "total_services": len(results),
        "services": results,
        "recommendations": recommendations,
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.get("/fixed-diagnostics")
async def fixed_diagnostics():
    """Fixed diagnostics with server-side proxy calls"""
    try:
        return FileResponse("public/fixed-diagnostics.html")
    except FileNotFoundError:
        return HTMLResponse("<h1>Fixed diagnostics not found</h1>")

# SAFE DIAGNOSTIC ADDITION - Testing deployment and CORS
@app.get("/debug-cors")
async def debug_cors_endpoint():
    """Simple diagnostic to test if deployments are working"""
    try:
        # Test if we can reach km-mcp-sql-docs from server side
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://km-mcp-sql-docs.azurewebsites.net/health")
            server_side_result = {
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "response": response.json() if response.status_code == 200 else response.text
            }
    except Exception as e:
        server_side_result = {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
    
    return {
        "diagnostic": "CORS Debug Endpoint",
        "deployment_test": "If you see this, deployment is working",
        "timestamp": datetime.utcnow().isoformat(),
        "server_side_call_to_docs": server_side_result,
        "next_step": "Check if server can reach km-mcp-sql-docs"
    }

# SAFE ADDITION - Debug page route
@app.get("/debug-cors-page")
async def debug_cors_page():
    """Safe debug page to test CORS issues"""
    try:
        return FileResponse("public/debug-cors.html")
    except FileNotFoundError:
        return HTMLResponse("<h1>Debug page not found</h1>")

