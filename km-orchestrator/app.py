"""
KM Orchestrator - Intelligent Request Routing for Knowledge Management System
FastAPI service that routes requests across all MCP services
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
import httpx
import asyncio
from typing import Dict, List, Any, Optional
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="KM Orchestrator",
    description="Intelligent request routing and workflow orchestration for Knowledge Management System",
    version="1.0.0"
)

# Service endpoints
SERVICES = {
    "km-mcp-sql-docs": "https://km-mcp-sql-docs.azurewebsites.net",
    "km-mcp-search": "https://km-mcp-search.azurewebsites.net",
    "km-mcp-llm": "https://km-mcp-llm.azurewebsites.net",
    "km-mcp-graphrag": "https://km-mcp-graphrag.azurewebsites.net"
}

@app.get("/")
async def dashboard():
    """Interactive dashboard"""
    return {"message": "KM Orchestrator is running", "services": len(SERVICES)}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)