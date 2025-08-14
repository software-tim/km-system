# First, save the complete app.py content
@'
#!/usr/bin/env python3
"""
KM-MCP-SQL Server - Knowledge Management SQL Interface
FastAPI implementation for Azure SQL Database operations
"""

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import os
import logging
from datetime import datetime
from pathlib import Path

# Import our SQL operations module
from km_sql_operations import SQLOperations
from km_sql_schemas import (
    ToolExecutionRequest,
    ToolExecutionResponse,
    StatusResponse,
    DatabaseInfoResponse,
    VisualizationRequest
)
from km_config import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load settings
settings = Settings()

# Initialize SQL operations
sql_ops = SQLOperations(settings)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting KM-MCP-SQL Server")
    logger.info(f"Connecting to: {settings.km_sql_server}")
    logger.info(f"Database: {settings.km_sql_database}")
    
    # Test database connection
    try:
        result = await sql_ops.get_database_info()
        if result.get("success"):
            logger.info("✅ Database connection successful")
        else:
            logger.warning("⚠️ Database connection test failed")
    except Exception as e:
        logger.error(f"❌ Database connection error: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down KM-MCP-SQL Server")

# Create FastAPI app
app = FastAPI(
    title="KM-MCP-SQL Server",
    description="Knowledge Management SQL Database Interface with MCP Tools",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional API Key authentication
async def verify_api_key(request: Request) -> bool:
    """Verify API key if configured"""
    if not settings.api_key:
        return True
    
    api_key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    if api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True

# Root endpoint
@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the main web interface"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>KM-MCP-SQL Server</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            .status { padding: 10px; background: #e8f5e9; border-radius: 5px; margin: 20px 0; }
            .endpoint { margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 5px; }
            code { background: #e0e0e0; padding: 2px 5px; border-radius: 3px; font-family: monospace; }
            h1 { color: #333; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🗄️ KM-MCP-SQL Server</h1>
            <div class="status">
                <h3>✅ Service is Running</h3>
                <p>Knowledge Management SQL Database Interface</p>
            </div>
            <h2>Available API Endpoints:</h2>
            <div class="endpoint">
                <strong>GET /api/status</strong> - Check service status
            </div>
            <div class="endpoint">
                <strong>GET /api/tools</strong> - List available tools
            </div>
            <div class="endpoint">
                <strong>POST /api/tools/{tool_name}</strong> - Execute a tool
            </div>
            <div class="endpoint">
                <strong>GET /health</strong> - Health check
            </div>
            <div class="endpoint">
                <strong>GET /docs</strong> - Interactive API documentation
            </div>
        </div>
    </body>
    </html>
    """)

# API Status endpoint
@app.get("/api/status")
async def api_status():
    """Get API and database connection status"""
    return {
        "status": "online",
        "service": "km-mcp-sql",
        "database": {
            "server": settings.km_sql_server,
            "database": settings.km_sql_database,
            "user": settings.km_sql_username
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# List available tools
@app.get("/api/tools")
async def list_tools():
    """List all available SQL tools"""
    tools = [
        {
            "name": "sql_query",
            "description": "Execute a SQL query on the database",
            "available": True
        },
        {
            "name": "get_database_info",
            "description": "Get server version, current database, and user information",
            "available": True
        },
        {
            "name": "show_tables",
            "description": "Show all tables in the current database",
            "available": True
        },
        {
            "name": "describe_table",
            "description": "Show detailed information about a specific table's structure",
            "available": True
        },
        {
            "name": "show_indexes",
            "description": "Show indexes for a table or all tables",
            "available": True
        },
        {
            "name": "get_schema",
            "description": "Get the database schema information for AI understanding",
            "available": True
        },
        {
            "name": "generate_visualization",
            "description": "Generate visualizations from query results",
            "available": True
        },
        {
            "name": "generate_analysis_notebook",
            "description": "Generate a Jupyter notebook with analysis code",
            "available": True
        }
    ]
    
    return {
        "tools": tools,
        "count": len(tools),
        "timestamp": datetime.utcnow().isoformat()
    }

# Main tool execution endpoint
@app.post("/api/tools/{tool_name}")
async def execute_tool(
    tool_name: str,
    request: ToolExecutionRequest
):
    """Execute a SQL tool and return results"""
    try:
        # Map tool names to operations
        tool_mapping = {
            "sql_query": sql_ops.sql_query,
            "get_database_info": sql_ops.get_database_info,
            "show_tables": sql_ops.show_tables,
            "describe_table": sql_ops.describe_table,
            "show_indexes": sql_ops.show_indexes,
            "get_schema": sql_ops.get_schema,
            "generate_visualization": sql_ops.generate_visualization,
            "generate_analysis_notebook": sql_ops.generate_analysis_notebook
        }
        
        if tool_name not in tool_mapping:
            raise HTTPException(
                status_code=404,
                detail=f"Unknown tool: {tool_name}. Available tools: {list(tool_mapping.keys())}"
            )
        
        logger.info(f"Executing tool: {tool_name} with args: {request.arguments}")
        
        # Execute the tool
        tool_function = tool_mapping[tool_name]
        result = await tool_function(**request.arguments)
        
        # Return the result
        return ToolExecutionResponse(
            success=True,
            content=result,
            tool=tool_name,
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool execution failed for {tool_name}: {str(e)}")
        return ToolExecutionResponse(
            success=False,
            error=str(e),
            tool=tool_name,
            timestamp=datetime.utcnow()
        )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for Azure monitoring"""
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "status": 404,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status": 500,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Main entry point for local development
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    
    print("=" * 60)
    print("KM-MCP-SQL Server - Knowledge Management SQL Interface")
    print("=" * 60)
    print(f"Starting server on port {port}")
    print(f"Debug mode: {debug_mode}")
    print(f"API Documentation: http://localhost:{port}/docs")
    print("-" * 60)
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=debug_mode
    )
'@ | Out-File -FilePath app.py -Encoding utf8

# Commit and push the updated app.py
git add app.py
git commit -m "Update app.py with complete FastAPI implementation"
git push azure master