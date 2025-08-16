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

from km_orchestrator_config import settings
from km_orchestrator_schemas import *
from km_orchestrator_operations import OrchestratorOperations

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="KM Orchestrator",
    description="Intelligent request routing and workflow orchestration for Knowledge Management System",
    version="1.0.0"
)

# Initialize operations
ops = OrchestratorOperations()

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Interactive dashboard for the orchestrator"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KM Orchestrator Dashboard</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: rgba(255,255,255,0.95); padding: 30px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); }
            .header h1 { color: #2c3e50; margin: 0; font-size: 2.5em; }
            .header p { color: #7f8c8d; margin: 10px 0 0; font-size: 1.2em; }
            .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
            .stat-card { background: rgba(255,255,255,0.95); padding: 25px; border-radius: 15px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); }
            .stat-card h3 { color: #2c3e50; margin: 0 0 15px; font-size: 1.3em; }
            .stat-value { font-size: 2.5em; font-weight: bold; color: #3498db; margin: 10px 0; }
            .endpoints-section { background: rgba(255,255,255,0.95); padding: 30px; border-radius: 15px; box-shadow: 0 8px 32px rgba(0,0,0,0.1); }
            .endpoints-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 20px; }
            .endpoint-card { background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid #3498db; }
            .endpoint-card h4 { color: #2c3e50; margin: 0 0 10px; }
            .endpoint-card .method { background: #3498db; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; display: inline-block; margin-bottom: 10px; }
            .endpoint-card .description { color: #7f8c8d; font-size: 0.9em; }
            .test-button { background: #27ae60; color: white; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer; margin-top: 10px; }
            .test-button:hover { background: #219a52; }
            .services-status { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 20px; }
            .service-status { background: #ecf0f1; padding: 15px; border-radius: 8px; text-align: center; }
            .service-status.healthy { border-left: 4px solid #27ae60; }
            .service-status.unhealthy { border-left: 4px solid #e74c3c; }
            .status-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; }
            .status-dot.healthy { background: #27ae60; }
            .status-dot.unhealthy { background: #e74c3c; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>ðŸŽ¯ KM Orchestrator</h1>
                <p>Intelligent request routing and workflow orchestration for Knowledge Management System</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>System Status</h3>
                    <div class="stat-value" id="system-status">Checking...</div>
                    <div>Overall Health</div>
                </div>
                <div class="stat-card">
                    <h3>Active Services</h3>
                    <div class="stat-value" id="active-services">0/5</div>
                    <div>MCP Services Online</div>
                </div>
                <div class="stat-card">
                    <h3>Avg Response</h3>
                    <div class="stat-value" id="avg-response">---ms</div>
                    <div>Cross-Service</div>
                </div>
                <div class="stat-card">
                    <h3>Total Requests</h3>
                    <div class="stat-value" id="total-requests">---</div>
                    <div>Since Startup</div>
                </div>
            </div>

            <div class="endpoints-section">
                <h2>ðŸš€ Orchestrator API Endpoints</h2>
                <div class="endpoints-grid">
                    <div class="endpoint-card">
                        <h4>/api/upload</h4>
                        <span class="method">POST</span>
                        <div class="description">Upload documents through sql-docs + trigger processing pipeline</div>
                        <button class="test-button" onclick="testEndpoint('/api/upload')">Test Endpoint</button>
                    </div>
                    <div class="endpoint-card">
                        <h4>/api/search</h4>
                        <span class="method">POST</span>
                        <div class="description">Intelligent search across search + sql-docs services</div>
                        <button class="test-button" onclick="testEndpoint('/api/search')">Test Endpoint</button>
                    </div>
                    <div class="endpoint-card">
                        <h4>/api/analyze</h4>
                        <span class="method">POST</span>
                        <div class="description">AI analysis using llm + graphrag services</div>
                        <button class="test-button" onclick="testEndpoint('/api/analyze')">Test Endpoint</button>
                    </div>
                    <div class="endpoint-card">
                        <h4>/api/insights</h4>
                        <span class="method">POST</span>
                        <div class="description">Combined multi-service insights and analytics</div>
                        <button class="test-button" onclick="testEndpoint('/api/insights')">Test Endpoint</button>
                    </div>
                    <div class="endpoint-card">
                        <h4>/api/chat</h4>
                        <span class="method">POST</span>
                        <div class="description">Interactive AI chat across all services</div>
                        <button class="test-button" onclick="testEndpoint('/api/chat')">Test Endpoint</button>
                    </div>
                    <div class="endpoint-card">
                        <h4>/health</h4>
                        <span class="method">GET</span>
                        <div class="description">Health check and service status monitoring</div>
                        <button class="test-button" onclick="testEndpoint('/health')">Test Endpoint</button>
                    </div>
                </div>
            </div>

            <div class="endpoints-section" style="margin-top: 30px;">
                <h2>ðŸ”§ MCP Services Status</h2>
                <div class="services-status" id="services-status">
                    <div class="service-status">
                        <span class="status-dot"></span>
                        <strong>Loading...</strong>
                    </div>
                </div>
            </div>
        </div>

        <script>
            async function loadStats() {
                try {
                    const response = await fetch('/health');
                    const data = await response.json();
                    
                    // Update stats
                    document.getElementById('system-status').textContent = data.status === 'healthy' ? 'âœ… Healthy' : 'âŒ Issues';
                    document.getElementById('active-services').textContent = `${data.services_healthy}/${data.services_total}`;
                    document.getElementById('avg-response').textContent = data.avg_response_time + 'ms';
                    document.getElementById('total-requests').textContent = data.total_requests || '0';
                    
                    // Update services status
                    const servicesDiv = document.getElementById('services-status');
                    servicesDiv.innerHTML = data.services.map(service => `
                        <div class="service-status ${service.status}">
                            <span class="status-dot ${service.status}"></span>
                            <strong>${service.name}</strong><br>
                            <small>${service.response_time}ms</small>
                        </div>
                    `).join('');
                    
                } catch (error) {
                    console.error('Failed to load stats:', error);
                }
            }
            
            async function testEndpoint(endpoint) {
                window.open(endpoint, '_blank');
            }
            
            // Load stats on page load and refresh every 30 seconds
            loadStats();
            setInterval(loadStats, 30000);
        </script>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Comprehensive health check across all MCP services"""
    return await ops.check_all_services_health()

@app.post("/api/upload")
async def upload_document(request: UploadRequest):
    """Upload documents through sql-docs + trigger processing pipeline"""
    try:
        # Route to sql-docs for document storage
        sql_docs_result = await ops.route_to_service("km-mcp-sql-docs", "POST", "/tools/store-document", request.dict())
        
        # TODO: Trigger processing pipeline when available
        # processing_result = await ops.route_to_service("km-mcp-processing", "POST", "/tools/process-document", {"document_id": sql_docs_result.get("id")})
        
        return {
            "status": "success",
            "message": "Document uploaded successfully",
            "document_id": sql_docs_result.get("id"),
            "storage_result": sql_docs_result,
            "processing_status": "pending"  # Will be "completed" when processing pipeline is ready
        }
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/api/search")
async def intelligent_search(request: SearchRequest):
    """Intelligent search across search + sql-docs services"""
    try:
        # Run searches in parallel for better performance
        tasks = []
        
        # Search via sql-docs (text search)
        tasks.append(ops.route_to_service("km-mcp-sql-docs", "POST", "/tools/search-documents", request.dict()))
        
        # Search via search service (semantic search) - when available
        # tasks.append(ops.route_to_service("km-mcp-search", "POST", "/tools/semantic-search", request.dict()))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and rank results
        combined_results = await ops.combine_search_results(results, request.query)
        
        return {
            "status": "success",
            "query": request.query,
            "results": combined_results,
            "sources": ["sql-docs"],  # Will include "search" when semantic search is ready
            "total_results": len(combined_results)
        }
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/api/analyze")
async def ai_analysis(request: AnalyzeRequest):
    """AI analysis using llm + graphrag services"""
    try:
        # Get document content first
        if request.document_id:
            doc_result = await ops.route_to_service("km-mcp-sql-docs", "GET", f"/tools/get-document/{request.document_id}")
        
        tasks = []
        
        # LLM analysis - when available
        # tasks.append(ops.route_to_service("km-mcp-llm", "POST", "/tools/analyze-document", request.dict()))
        
        # GraphRAG analysis - when available  
        # tasks.append(ops.route_to_service("km-mcp-graphrag", "POST", "/tools/extract-entities", request.dict()))
        
        # For now, return a structured response indicating readiness
        return {
            "status": "ready",
            "message": "Analysis services are being prepared",
            "document_id": request.document_id,
            "analysis_type": request.analysis_type,
            "services_available": await ops.get_available_analysis_services()
        }
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/insights")
async def combined_insights(request: InsightsRequest):
    """Combined multi-service insights and analytics"""
    try:
        insights = {
            "document_stats": await ops.get_document_statistics(),
            "system_health": await ops.check_all_services_health(),
            "usage_metrics": await ops.get_usage_metrics(),
            "recommendations": await ops.get_system_recommendations()
        }
        
        return {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "insights": insights
        }
    except Exception as e:
        logger.error(f"Insights failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Insights failed: {str(e)}")

@app.post("/api/chat")
async def interactive_chat(request: ChatRequest):
    """Interactive AI chat across all services"""
    try:
        # Determine which services to use based on the question
        routing_decision = await ops.determine_chat_routing(request.message)
        
        # For now, provide a structured response about chat capabilities
        return {
            "status": "ready", 
            "message": "Chat interface is being prepared",
            "user_message": request.message,
            "routing_decision": routing_decision,
            "available_capabilities": await ops.get_available_chat_capabilities()
        }
    except Exception as e:
        logger.error(f"Chat failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.get("/services/status")
async def services_status():
    """Get detailed status of all MCP services"""
    return await ops.get_detailed_service_status()

@app.get("/metrics")
async def get_metrics():
    """Get orchestrator performance metrics"""
    return await ops.get_orchestrator_metrics()

@app.post("/workflows/{workflow_name}")
async def execute_workflow(workflow_name: str, request: Dict[str, Any]):
    """Execute complex multi-service workflows"""
    try:
        result = await ops.execute_workflow(workflow_name, request)
        return result
    except Exception as e:
        logger.error(f"Workflow {workflow_name} failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)# Updated for deployment

