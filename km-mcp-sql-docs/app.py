#!/usr/bin/env python3
"""
KM-MCP-SQL-DOCS Service
Document management service for Knowledge Management System
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import json
from datetime import datetime
import io
import os
import sys

# Import our modules
from km_docs_config import Settings
from km_docs_schemas import (
    DocumentCreate, DocumentUpdate, DocumentResponse,
    SearchRequest, SearchResponse, StatsResponse
)
from km_docs_operations import DocumentOperations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="KM-MCP-SQL-DOCS API",
    description="Document Management Service for Knowledge Management System",
    version="1.0.0"
)

# Initialize settings and operations
settings = Settings()
doc_ops = DocumentOperations(settings)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting KM-MCP-SQL-DOCS service")
    await doc_ops.initialize_database()
    logger.info("Service started successfully")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "km-mcp-sql-docs",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "tools": "/tools",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_connected = await doc_ops.check_connection()
    return {
        "status": "healthy",
        "service": "km-mcp-sql-docs",
        "database": "connected" if db_connected else "disconnected",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/tools")
async def list_tools():
    """List available MCP tools"""
    return {
        "available_tools": [
            {
                "name": "store-document",
                "description": "Store a new document in the database"
            },
            {
                "name": "search-documents",
                "description": "Search documents in the database"
            },
            {
                "name": "get-document",
                "description": "Get a specific document by ID"
            },
            {
                "name": "update-document",
                "description": "Update an existing document"
            },
            {
                "name": "delete-document",
                "description": "Delete a document (soft delete)"
            },
            {
                "name": "database-stats",
                "description": "Get database statistics"
            }
        ]
    }

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
        # Parse entities and metadata if provided
        entities_list = entities.split(',') if entities else None
        metadata_dict = json.loads(metadata) if metadata else None
        
        # Handle file upload
        file_data = None
        file_name = None
        file_type = None
        file_size = None
        
        if file:
            file_data = await file.read()
            file_name = file.filename
            file_type = file.content_type
            file_size = len(file_data)
        
        # Create document
        doc = DocumentCreate(
            title=title,
            content=content,
            classification=classification,
            entities=entities_list,
            metadata=metadata_dict,
            file_data=file_data,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size
        )
        
        result = await doc_ops.store_document(doc)
        return result
        
    except Exception as e:
        logger.error(f"Error storing document: {e}")
        return {"success": False, "error": str(e)}

@app.post("/tools/search-documents")
async def search_documents(request: SearchRequest):
    """Search for documents"""
    try:
        result = await doc_ops.search_documents(
            query=request.query,
            classification=request.classification,
            limit=request.limit,
            offset=request.offset
        )
        return {
            "success": True,
            "documents": result.get("documents", []),
            "total": result.get("total", 0)
        }
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {
            "success": False,
            "documents": [],
            "total": 0,
            "error": str(e)
        }

@app.get("/tools/database-stats")
async def get_database_stats():
    """Get database statistics"""
    try:
        stats = await doc_ops.get_database_stats()
        return {
            "success": True,
            "statistics": stats.get("statistics", {}),
            "classification_breakdown": stats.get("classification_breakdown", [])
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "success": False,
            "statistics": {},
            "classification_breakdown": [],
            "error": str(e)
        }

@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    return await health_check()


@app.get("/debug-stats")
async def debug_stats():
    """Debug stats directly"""
    import pyodbc
    try:
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=km-sql-server.database.windows.net;"
            "DATABASE=km-db;"
            "UID=kmadmin;"
            "PWD=Km123456!"
        )
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Get count
        cursor.execute("SELECT COUNT(*) FROM documents")
        total = cursor.fetchone()[0]
        
        # Get classifications
        cursor.execute("""
            SELECT classification, COUNT(*) as cnt 
            FROM documents 
            GROUP BY classification
        """)
        classifications = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "total": total,
            "classifications": [
                {"class": row[0], "count": row[1]} 
                for row in classifications
            ]
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

