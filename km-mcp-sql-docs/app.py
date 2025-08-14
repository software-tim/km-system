#!/usr/bin/env python3
"""
KM-MCP-SQL-DOCS Server - Document Storage and Retrieval Service
FastAPI implementation for document management in Azure SQL Database
"""

from fastapi import FastAPI, HTTPException, Request, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
import os
import json
import logging
from datetime import datetime

# Import our document operations module
from km_docs_operations import DocumentOperations
from km_docs_schemas import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    SearchRequest,
    SearchResponse,
    DatabaseStats,
    ToolInfo
)
from km_docs_config import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load settings
settings = Settings()

# Initialize document operations
doc_ops = DocumentOperations(settings)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting KM-MCP-SQL-DOCS Server")
    logger.info(f"Connecting to: {settings.km_sql_server}")
    logger.info(f"Database: {settings.km_sql_database}")
    
    # Initialize database connection and create tables if needed
    try:
        await doc_ops.initialize_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down KM-MCP-SQL-DOCS Server")

# Create FastAPI app
app = FastAPI(
    title="KM-MCP-SQL-DOCS Server",
    description="Document Storage and Retrieval Service for Knowledge Management",
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
@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "km-mcp-sql-docs",
        "description": "Document Storage and Retrieval Service",
        "version": "1.0.0",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "endpoints": {
            "health": "/health",
            "tools": "/tools",
            "store_document": "/tools/store-document",
            "search_documents": "/tools/search-documents",
            "get_document": "/tools/get-document/{id}",
            "update_document": "/tools/update-document/{id}",
            "delete_document": "/tools/delete-document/{id}",
            "database_stats": "/tools/database-stats",
            "docs": "/docs"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        db_status = await doc_ops.check_connection()
        return JSONResponse(
            content={
                "status": "healthy" if db_status else "degraded",
                "service": "km-mcp-sql-docs",
                "database": "connected" if db_status else "disconnected",
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=200 if db_status else 503
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# List available tools
@app.get("/tools")
async def list_tools():
    """List all available document management tools"""
    return {
        "service": "km-mcp-sql-docs",
        "available_tools": [
            {
                "name": "store-document",
                "description": "Store a new document in the database",
                "endpoint": "/tools/store-document",
                "method": "POST",
                "parameters": ["title", "content", "classification", "entities", "metadata", "file"]
            },
            {
                "name": "search-documents",
                "description": "Search documents in the database",
                "endpoint": "/tools/search-documents",
                "method": "POST",
                "parameters": ["query", "classification", "limit", "offset"]
            },
            {
                "name": "get-document",
                "description": "Get a specific document by ID",
                "endpoint": "/tools/get-document/{id}",
                "method": "GET",
                "parameters": ["id"]
            },
            {
                "name": "update-document",
                "description": "Update an existing document",
                "endpoint": "/tools/update-document/{id}",
                "method": "PUT",
                "parameters": ["id", "title", "content", "classification", "entities", "metadata"]
            },
            {
                "name": "delete-document",
                "description": "Delete a document (soft delete)",
                "endpoint": "/tools/delete-document/{id}",
                "method": "DELETE",
                "parameters": ["id"]
            },
            {
                "name": "database-stats",
                "description": "Get database statistics",
                "endpoint": "/tools/database-stats",
                "method": "GET",
                "parameters": []
            }
        ]
    }

# Store document endpoint
@app.post("/tools/store-document")
async def store_document(
    title: str = Form(...),
    content: str = Form(...),
    classification: Optional[str] = Form(None),
    entities: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """Store a new document"""
    try:
        doc_create = DocumentCreate(
            title=title,
            content=content,
            classification=classification,
            entities=entities.split(",") if entities else None,
            metadata=json.loads(metadata) if metadata else None
        )
        
        if file:
            if file.size > settings.max_file_size:
                raise HTTPException(400, f"File size exceeds limit of {settings.max_file_size} bytes")
            
            doc_create.file_data = await file.read()
            doc_create.file_name = file.filename
            doc_create.file_type = file.content_type
            doc_create.file_size = file.size
        
        result = await doc_ops.store_document(doc_create)
        return result
        
    except Exception as e:
        logger.error(f"Error storing document: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# Search documents endpoint
@app.post("/tools/search-documents")
async def search_documents(request: Dict[str, Any]):
    """Search documents"""
    try:
        result = await doc_ops.search_documents(
            query=request.get("query"),
            classification=request.get("classification"),
            limit=request.get("limit", 10),
            offset=request.get("offset", 0)
        )
        
        return {
            "success": True,
            "documents": result.get("documents", []),
            "total": result.get("total", 0),
            "query": request.get("query", ""),
            "source": "km-mcp-sql-docs"
        }
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        return {
            "success": False,
            "error": str(e),
            "documents": [],
            "total": 0
        }

# Get document endpoint
@app.get("/tools/get-document/{document_id}")
async def get_document(document_id: int):
    """Get document by ID"""
    try:
        document = await doc_ops.get_document(document_id)
        if not document:
            raise HTTPException(404, "Document not found")
        return {
            "success": True,
            "document": document
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# Update document endpoint
@app.put("/tools/update-document/{document_id}")
async def update_document(document_id: int, update_data: DocumentUpdate):
    """Update document"""
    try:
        success = await doc_ops.update_document(document_id, update_data)
        if not success:
            raise HTTPException(404, "Document not found")
        return {
            "success": True,
            "message": "Document updated"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# Delete document endpoint
@app.delete("/tools/delete-document/{document_id}")
async def delete_document(document_id: int):
    """Delete document"""
    try:
        success = await doc_ops.delete_document(document_id)
        if not success:
            raise HTTPException(404, "Document not found")
        return {
            "success": True,
            "message": "Document deleted"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        return {
            "success": False,
            "error": str(e)
        }

# Database stats endpoint
@app.get("/tools/database-stats")
async def database_stats():
    """Get database statistics"""
    try:
        stats = await doc_ops.get_database_stats()
        return {
            "success": True,
            "statistics": stats.get("statistics", {}),
            "classification_breakdown": stats.get("classification_breakdown", [])
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            "success": False,
            "error": str(e)
        }

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
    print("KM-MCP-SQL-DOCS Server - Document Storage Service")
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
