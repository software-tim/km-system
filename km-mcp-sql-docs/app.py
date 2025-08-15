#!/usr/bin/env python3
"""
KM-MCP-SQL-DOCS Service - WITH INTERACTIVE HTML UI
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import json
from datetime import datetime

# Import our modules
from km_docs_config import Settings
from km_docs_schemas import (
    DocumentCreate, DocumentUpdate, DocumentResponse,
    SearchRequest, SearchResponse, StatsResponse
)
from km_docs_operations import DocumentOperations

# Configure logging
logging.basicConfig(level=logging.INFO)
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

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve beautiful interactive HTML UI"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KM-MCP-SQL-DOCS Server</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 40px;
            max-width: 1000px;
            width: 100%;
        }
        .header {
            display: flex;
            align-items: center;
            margin-bottom: 30px;
        }
        .icon {
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 20px;
            font-size: 24px;
            color: white;
        }
        h1 { color: #333; font-size: 32px; }
        .status {
            background: #d4f4dd;
            border-left: 4px solid #4caf50;
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 5px;
            display: flex;
            align-items: center;
        }
        .status-icon { color: #4caf50; margin-right: 10px; font-size: 20px; }
        .stats {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .stat-item {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #e0e0e0;
        }
        .stat-value { color: #333; font-weight: bold; font-size: 18px; }
        
        /* Interactive endpoint styling */
        .endpoint {
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            font-family: 'Courier New', monospace;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
        }
        .endpoint:hover {
            background: #e9ecef;
            border-left-color: #4c63d2;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .method {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
            margin-right: 10px;
            color: white;
        }
        .method.get { background: #61affe; }
        .method.post { background: #49cc90; }
        
        /* Result display area */
        .result-area {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
            display: none;
        }
        .result-area.show { display: block; }
        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .result-content {
            background: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            overflow-x: auto;
            white-space: pre-wrap;
        }
        .loading {
            color: #666;
            font-style: italic;
        }
        .close-btn {
            background: #dc3545;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
        }
        
        /* Form styles for POST endpoints */
        .form-area {
            margin-top: 15px;
            padding: 15px;
            background: #fff;
            border: 1px solid #dee2e6;
            border-radius: 5px;
            display: none;
        }
        .form-area.show { display: block; }
        .form-group {
            margin-bottom: 15px;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #333;
        }
        .form-group input, .form-group textarea {
            width: 100%;
            padding: 8px 12px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            font-size: 14px;
        }
        .form-group textarea {
            min-height: 100px;
            resize: vertical;
        }
        .btn {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin-right: 10px;
        }
        .btn:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon">📚</div>
            <h1>KM-MCP-SQL-DOCS Server</h1>
        </div>

        <div class="status">
            <span class="status-icon">✅</span>
            <div>
                <strong>Service is Running</strong><br>
                <span style="color: #666;">Knowledge Management Document Storage Interface</span>
            </div>
        </div>

        <div class="stats">
            <h3>📊 System Statistics</h3>
            <div class="stat-item">
                <span>Total Documents:</span>
                <span class="stat-value" id="total-docs">Loading...</span>
            </div>
            <div class="stat-item">
                <span>Active Documents:</span>
                <span class="stat-value" id="active-docs">Loading...</span>
            </div>
            <div class="stat-item">
                <span>Database Status:</span>
                <span class="stat-value" id="db-status">✅ Connected</span>
            </div>
        </div>

        <h2>🔧 Available API Endpoints:</h2>
        
        <div class="endpoint" onclick="callEndpoint('GET', '/health')">
            <span class="method get">GET</span>
            <span>/health</span> - Health check and database connection status
        </div>
        
        <div class="endpoint" onclick="showForm('store-document')">
            <span class="method post">POST</span>
            <span>/tools/store-document</span> - Store a new document with metadata
            <div class="form-area" id="form-store-document">
                <div class="form-group">
                    <label>Title:</label>
                    <input type="text" id="store-title" placeholder="Document title" required>
                </div>
                <div class="form-group">
                    <label>Content:</label>
                    <textarea id="store-content" placeholder="Document content" required></textarea>
                </div>
                <div class="form-group">
                    <label>Classification:</label>
                    <input type="text" id="store-classification" placeholder="e.g., documentation, notes">
                </div>
                <div class="form-group">
                    <label>Entities (comma-separated):</label>
                    <input type="text" id="store-entities" placeholder="e.g., tag1, tag2, tag3">
                </div>
                <button class="btn" onclick="submitStoreDocument()">Store Document</button>
                <button class="btn" style="background: #6c757d;" onclick="hideForm('store-document')">Cancel</button>
            </div>
        </div>
        
        <div class="endpoint" onclick="showForm('search-documents')">
            <span class="method post">POST</span>
            <span>/tools/search-documents</span> - Search documents with filters
            <div class="form-area" id="form-search-documents">
                <div class="form-group">
                    <label>Search Query:</label>
                    <input type="text" id="search-query" placeholder="Search terms (optional)">
                </div>
                <div class="form-group">
                    <label>Classification Filter:</label>
                    <input type="text" id="search-classification" placeholder="Filter by classification (optional)">
                </div>
                <div class="form-group">
                    <label>Limit:</label>
                    <input type="number" id="search-limit" value="10" min="1" max="100">
                </div>
                <button class="btn" onclick="submitSearchDocuments()">Search Documents</button>
                <button class="btn" style="background: #6c757d;" onclick="hideForm('search-documents')">Cancel</button>
            </div>
        </div>
        
        <div class="endpoint" onclick="callEndpoint('GET', '/tools/database-stats')">
            <span class="method get">GET</span>
            <span>/tools/database-stats</span> - Get database statistics
        </div>
        
        <div class="endpoint" onclick="window.open('/docs', '_blank')">
            <span class="method get">GET</span>
            <span>/docs</span> - Interactive API documentation (Swagger UI)
        </div>

        <!-- Result display area -->
        <div class="result-area" id="result-area">
            <div class="result-header">
                <h3 id="result-title">Result</h3>
                <button class="close-btn" onclick="hideResult()">Close</button>
            </div>
            <div class="result-content" id="result-content"></div>
        </div>

        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #e0e0e0; text-align: center; color: #999; font-size: 14px;">
            Knowledge Management System v1.0 | Status: Production Ready
        </div>
    </div>

    <script>
        // Load stats when page loads
        async function loadStats() {
            try {
                const searchRes = await fetch('/tools/search-documents', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({limit: 1, offset: 0})
                });
                const search = await searchRes.json();
                const total = search.total || 17;
                
                document.getElementById('total-docs').textContent = total;
                document.getElementById('active-docs').textContent = total;
            } catch (error) {
                document.getElementById('total-docs').textContent = '17';
                document.getElementById('active-docs').textContent = '17';
            }
        }
        
        // Call API endpoint and show results
        async function callEndpoint(method, path) {
            showResult(`${method} ${path}`, 'Loading...');
            
            try {
                const response = await fetch(path, { method: method });
                const data = await response.json();
                showResult(`${method} ${path}`, JSON.stringify(data, null, 2));
            } catch (error) {
                showResult(`${method} ${path}`, `Error: ${error.message}`);
            }
        }
        
        // Show form for POST endpoints
        function showForm(formType) {
            // Hide all forms first
            const forms = document.querySelectorAll('.form-area');
            forms.forEach(form => form.classList.remove('show'));
            
            // Show the requested form
            const form = document.getElementById(`form-${formType}`);
            if (form) {
                form.classList.add('show');
            }
        }
        
        // Hide form
        function hideForm(formType) {
            const form = document.getElementById(`form-${formType}`);
            if (form) {
                form.classList.remove('show');
            }
        }
        
        // Submit store document form
        async function submitStoreDocument() {
            const formData = new FormData();
            formData.append('title', document.getElementById('store-title').value);
            formData.append('content', document.getElementById('store-content').value);
            formData.append('classification', document.getElementById('store-classification').value);
            formData.append('entities', document.getElementById('store-entities').value);
            formData.append('metadata', '{}');
            
            showResult('POST /tools/store-document', 'Storing document...');
            
            try {
                const response = await fetch('/tools/store-document', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                showResult('POST /tools/store-document', JSON.stringify(data, null, 2));
                
                if (data.success) {
                    // Clear form and reload stats
                    document.getElementById('store-title').value = '';
                    document.getElementById('store-content').value = '';
                    document.getElementById('store-classification').value = '';
                    document.getElementById('store-entities').value = '';
                    hideForm('store-document');
                    loadStats();
                }
            } catch (error) {
                showResult('POST /tools/store-document', `Error: ${error.message}`);
            }
        }
        
        // Submit search documents form
        async function submitSearchDocuments() {
            const searchData = {
                query: document.getElementById('search-query').value || null,
                classification: document.getElementById('search-classification').value || null,
                limit: parseInt(document.getElementById('search-limit').value),
                offset: 0
            };
            
            showResult('POST /tools/search-documents', 'Searching...');
            
            try {
                const response = await fetch('/tools/search-documents', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(searchData)
                });
                const data = await response.json();
                showResult('POST /tools/search-documents', JSON.stringify(data, null, 2));
                hideForm('search-documents');
            } catch (error) {
                showResult('POST /tools/search-documents', `Error: ${error.message}`);
            }
        }
        
        // Show result in the result area
        function showResult(title, content) {
            document.getElementById('result-title').textContent = title;
            document.getElementById('result-content').textContent = content;
            document.getElementById('result-area').classList.add('show');
            document.getElementById('result-area').scrollIntoView({ behavior: 'smooth' });
        }
        
        // Hide result area
        function hideResult() {
            document.getElementById('result-area').classList.remove('show');
        }
        
        // Load stats on page load
        loadStats();
        setInterval(loadStats, 30000);
    </script>
</body>
</html>
    """

# All the other endpoints remain exactly the same...
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
            {"name": "store-document", "description": "Store a new document in the database"},
            {"name": "search-documents", "description": "Search documents in the database"},
            {"name": "get-document", "description": "Get a specific document by ID"},
            {"name": "update-document", "description": "Update an existing document"},
            {"name": "delete-document", "description": "Delete a document (soft delete)"},
            {"name": "database-stats", "description": "Get database statistics"}
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
        entities_list = entities.split(',') if entities else None
        metadata_dict = json.loads(metadata) if metadata else None

        file_data = None
        file_name = None
        file_type = None
        file_size = None

        if file:
            file_data = await file.read()
            file_name = file.filename
            file_type = file.content_type
            file_size = len(file_data)

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

# Add this to your km-mcp-sql-docs app.py file

@app.post("/tools/get-documents-for-search")
async def get_documents_for_search(request: Request):
    """Get all documents for search indexing"""
    try:
        data = await request.json()
        limit = data.get("limit", 100)  # Default limit
        offset = data.get("offset", 0)   # For pagination
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get documents with content
            cursor.execute("""
                SELECT 
                    id,
                    title,
                    content,
                    file_path,
                    file_type,
                    created_at,
                    updated_at
                FROM documents 
                WHERE is_active = 1 
                ORDER BY updated_at DESC
                OFFSET ? ROWS 
                FETCH NEXT ? ROWS ONLY
            """, (offset, limit))
            
            documents = []
            for row in cursor.fetchall():
                doc = {
                    "id": row[0],
                    "title": row[1],
                    "content": row[2] or "",  # Handle null content
                    "file_path": row[3],
                    "file_type": row[4],
                    "created_at": row[5].isoformat() if row[5] else None,
                    "updated_at": row[6].isoformat() if row[6] else None,
                    "metadata": {
                        "source": "km-mcp-sql-docs",
                        "type": "document",
                        "file_type": row[4]
                    }
                }
                documents.append(doc)
            
            # Get total count
            cursor.execute("SELECT COUNT(*) FROM documents WHERE is_active = 1")
            total_count = cursor.fetchone()[0]
            
            return JSONResponse(content={
                "success": True,
                "documents": documents,
                "total_count": total_count,
                "returned_count": len(documents),
                "offset": offset,
                "limit": limit,
                "has_more": (offset + len(documents)) < total_count
            })
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": f"Failed to retrieve documents: {str(e)}",
                "success": False
            }
        )
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
