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

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Interactive dashboard for the orchestrator"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KM Orchestrator</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                min-height: 100vh; 
                padding: 15px;
            }
            .container { max-width: 1400px; margin: 0 auto; }
            
            .header { 
                background: rgba(255,255,255,0.95); 
                padding: 20px; 
                border-radius: 20px; 
                margin-bottom: 20px; 
                box-shadow: 0 20px 60px rgba(0,0,0,0.3); 
                display: flex;
                align-items: center;
            }
            .header-icon { 
                font-size: 2.5em; 
                margin-right: 20px;
            }
            .header h1 { 
                color: #2c3e50; 
                font-size: 1.8em; 
                font-weight: 700; 
                margin: 0; 
            }
            .header p { 
                color: #7f8c8d; 
                font-size: 0.9em; 
                margin: 5px 0 0 0; 
            }

            .stats-grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
                gap: 20px; 
                margin-bottom: 20px; 
            }
            .stat-card { 
                background: rgba(255,255,255,0.95); 
                padding: 20px; 
                border-radius: 20px; 
                box-shadow: 0 20px 60px rgba(0,0,0,0.3); 
                text-align: center;
            }
            .stat-card h3 { 
                color: #7f8c8d; 
                font-size: 0.8em; 
                font-weight: 500; 
                margin-bottom: 8px; 
                text-transform: uppercase; 
                letter-spacing: 0.5px; 
            }
            .stat-value { 
                font-size: 1.8em; 
                font-weight: 700; 
                margin-bottom: 3px; 
            }
            .stat-label { 
                color: #7f8c8d; 
                font-size: 0.75em; 
            }
            .stat-value.blue { color: #3498db; }
            .stat-value.green { color: #2ecc71; }
            .stat-value.orange { color: #f39c12; }
            .stat-value.purple { color: #9b59b6; }

            .endpoints-section { 
                background: rgba(255,255,255,0.95); 
                border-radius: 20px; 
                padding: 20px; 
                margin-bottom: 20px; 
                box-shadow: 0 20px 60px rgba(0,0,0,0.3); 
            }
            .endpoints-section h2 { 
                color: #2c3e50; 
                font-size: 1.2em; 
                margin-bottom: 15px; 
            }
            .endpoints-grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); 
                gap: 20px; 
            }
            .endpoint-card { 
                border: 2px solid #ecf0f1; 
                border-radius: 15px; 
                padding: 15px; 
                cursor: pointer; 
                transition: all 0.3s ease; 
                background: #fff;
            }
            .endpoint-card:hover { 
                border-color: #3498db; 
                transform: translateY(-3px); 
            }

            .services-section { 
                background: rgba(255,255,255,0.95); 
                border-radius: 20px; 
                padding: 20px; 
                box-shadow: 0 20px 60px rgba(0,0,0,0.3); 
            }
            .services-section h2 { 
                color: #2c3e50; 
                font-size: 1.2em; 
                margin-bottom: 15px; 
            }
            .services-grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); 
                gap: 15px; 
            }
            .service-card { 
                border: 2px solid #ecf0f1; 
                border-radius: 15px; 
                padding: 15px; 
                cursor: pointer; 
                transition: all 0.3s ease; 
                background: #fff;
            }
            .service-card:hover { 
                transform: translateY(-3px); 
            }
            .service-card.online { border-color: #2ecc71; }
            .service-card.offline { border-color: #e74c3c; }
            .service-status { 
                display: flex; 
                align-items: center; 
                margin-bottom: 10px; 
            }
            .status-dot { 
                width: 12px; 
                height: 12px; 
                border-radius: 50%; 
                margin-right: 10px; 
            }
            .status-dot.online { background: #2ecc71; }
            .status-dot.offline { background: #e74c3c; }
            .service-name { 
                font-weight: 600; 
                color: #2c3e50; 
                font-size: 1.1em; 
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="header-icon">🎯</div>
                <div>
                    <h1>KM Orchestrator</h1>
                    <p>Intelligent request routing and workflow orchestration for Knowledge Management System</p>
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <h3>System Status</h3>
                    <div class="stat-value green" id="system-status">All OK</div>
                    <div class="stat-label">Overall Health</div>
                </div>
                <div class="stat-card">
                    <h3>Active Services</h3>
                    <div class="stat-value blue" id="active-services">4/4</div>
                    <div class="stat-label">MCP Services Online</div>
                </div>
                <div class="stat-card">
                    <h3>Avg Response</h3>
                    <div class="stat-value orange" id="avg-response">105ms</div>
                    <div class="stat-label">Cross-Service</div>
                </div>
                <div class="stat-card">
                    <h3>Total Requests</h3>
                    <div class="stat-value purple" id="total-requests">1</div>
                    <div class="stat-label">Since Startup</div>
                </div>
            </div>

            <div class="endpoints-section">
                <h2>🚀 Orchestrator API Endpoints</h2>
                <div class="endpoints-grid">
                    <div class="endpoint-card" onclick="window.open('/docs', '_blank')">
                        <div><strong>GET /health</strong></div>
                        <div>Health check and service status</div>
                    </div>
                    <div class="endpoint-card" onclick="window.open('/services/status', '_blank')">
                        <div><strong>GET /services/status</strong></div>
                        <div>Check status of all MCP services</div>
                    </div>
                    <div class="endpoint-card" onclick="window.open('/docs', '_blank')">
                        <div><strong>GET /docs</strong></div>
                        <div>Interactive API documentation</div>
                    </div>
                </div>
            </div>

            <div class="services-section">
                <h2>⚡ MCP Services Status</h2>
                <div class="services-grid" id="services-grid">
                    <!-- Services populated by JavaScript -->
                </div>
            </div>
        </div>

        <script>
            const serviceUrls = {
                'km-mcp-sql-docs': 'https://km-mcp-sql-docs.azurewebsites.net',
                'km-mcp-search': 'https://km-mcp-search.azurewebsites.net',
                'km-mcp-llm': 'https://km-mcp-llm.azurewebsites.net',
                'km-mcp-graphrag': 'https://km-mcp-graphrag.azurewebsites.net'
            };

            async function loadServiceStatus() {
                try {
                    const response = await fetch('/services/status');
                    const data = await response.json();
                    updateServiceStatus(data);
                } catch (error) {
                    console.error('Failed to load service status:', error);
                }
            }

            function updateServiceStatus(data) {
                const servicesGrid = document.getElementById('services-grid');
                servicesGrid.innerHTML = '';

                if (data.summary) {
                    document.getElementById('active-services').textContent = 
                        `${data.summary.online_services}/${data.summary.total_services}`;
                }

                if (data.services) {
                    Object.entries(data.services).forEach(([serviceName, serviceData]) => {
                        const serviceCard = document.createElement('div');
                        serviceCard.className = `service-card ${serviceData.online ? 'online' : 'offline'}`;
                        serviceCard.onclick = () => window.open(serviceUrls[serviceName], '_blank');
                        
                        serviceCard.innerHTML = `
                            <div class="service-status">
                                <div class="status-dot ${serviceData.online ? 'online' : 'offline'}"></div>
                                <div class="service-name">${serviceName}</div>
                            </div>
                        `;
                        
                        servicesGrid.appendChild(serviceCard);
                    });
                }
            }

            loadServiceStatus();
            setInterval(loadServiceStatus, 30000);
        </script>
    </body>
    </html>
    """

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


# Orchestration endpoints
@app.post("/api/upload")
async def upload_orchestration(request: Request):
    """Orchestrate document upload across services"""
    try:
        body = await request.json()
        # Convert JSON to form data for km-mcp-sql-docs
        form_data = {
            'title': body.get('title', ''),
            'content': body.get('content', ''),
            'classification': body.get('classification', ''),
            'entities': body.get('entities', ''),
            'metadata': body.get('metadata', '{}')
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://km-mcp-sql-docs.azurewebsites.net/tools/store-document",
                data=form_data
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search") 
async def search_orchestration(request: Request):
    """Orchestrate search across all services"""
    try:
        body = await request.json()
        # Route to km-mcp-sql-docs for search
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

@app.post("/api/chat")
async def chat_orchestration(request: Request):
    """Orchestrate interactive chat across services"""
    try:
        body = await request.json()
        return {
            "status": "chat_ready", 
            "message": "Chat orchestration endpoint - routes across all MCP services",
            "request": body
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/insights")
async def insights_orchestration(request: Request):
    """Generate insights across all services"""
    try:
        body = await request.json()
        return {
            "status": "insights_ready", 
            "message": "Insights orchestration endpoint - combines data from all services",
            "request": body
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


