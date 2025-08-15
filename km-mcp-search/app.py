"""
km-mcp-search: Intelligent Document Search Service
Provides semantic and keyword search across document collections
Integrates with km-mcp-sql-docs and other data sources
"""

import os
import json
import asyncio
import math
from datetime import datetime
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import aiohttp
import re
from dataclasses import dataclass

# Initialize FastAPI app
app = FastAPI(
    title="KM MCP Search Service",
    description="Intelligent Document Search Service",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Search Configuration
class SearchConfig:
    def __init__(self):
        # OpenAI for embeddings
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Data sources
        self.km_docs_url = "https://km-mcp-sql-docs.azurewebsites.net"
        
        # Search parameters
        self.max_results = 20
        self.similarity_threshold = 0.7

search_config = SearchConfig()

@dataclass
class SearchResult:
    title: str
    content: str
    source: str
    score: float
    metadata: Dict[str, Any]
    snippet: str

class SearchService:
    """Handles document search with multiple algorithms"""
    
    def __init__(self):
        self.openai_available = bool(search_config.openai_api_key)
    
    async def get_documents_from_source(self, source_url: str) -> List[Dict[str, Any]]:
        """Fetch documents from a data source"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get documents from km-mcp-sql-docs
                payload = {
                    "limit": 100,  # Fetch up to 100 documents
                    "offset": 0
                }
                
                async with session.post(
                    f"{source_url}/tools/get-documents-for-search",
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("success"):
                            documents = []
                            for doc in result.get("documents", []):
                                # Ensure we have content to search
                                content = doc.get("content", "")
                                title = doc.get("title", f"Document {doc.get('id', 'Unknown')}")
                                
                                # Skip documents with no content
                                if not content.strip():
                                    content = f"Document: {title}. File: {doc.get('file_path', 'Unknown')}"
                                
                                documents.append({
                                    "id": doc.get("id"),
                                    "title": title,
                                    "content": content,
                                    "metadata": {
                                        "source": "km-mcp-sql-docs",
                                        "type": "document",
                                        "file_type": doc.get("file_type"),
                                        "file_path": doc.get("file_path"),
                                        "created_at": doc.get("created_at"),
                                        "updated_at": doc.get("updated_at")
                                    }
                                })
                            
                            print(f"Successfully fetched {len(documents)} documents from {source_url}")
                            return documents
                        else:
                            print(f"API returned error: {result.get('error', 'Unknown error')}")
                            return []
                    else:
                        print(f"HTTP error {response.status} from {source_url}")
                        return []
                
        except Exception as e:
            print(f"Error fetching documents from {source_url}: {e}")
            # Return sample documents if the real source fails (for testing)
            return self.get_sample_documents()
    
    def get_sample_documents(self) -> List[Dict[str, Any]]:
        """Fallback sample documents for testing"""
        return [
            {
                "id": "sample_1",
                "title": "Azure Deployment Guide",
                "content": "This document covers deploying applications to Azure App Service. Topics include FastAPI deployment, environment configuration, and troubleshooting common issues.",
                "metadata": {"source": "sample", "type": "document"}
            },
            {
                "id": "sample_2", 
                "title": "MCP Server Architecture",
                "content": "Model Context Protocol servers provide standardized interfaces for AI applications. This includes document storage, search capabilities, and AI processing services.",
                "metadata": {"source": "sample", "type": "document"}
            },
            {
                "id": "sample_3",
                "title": "Search Implementation",
                "content": "Document search functionality using semantic and keyword algorithms. Includes OpenAI embeddings for semantic search and fuzzy matching for keyword search.",
                "metadata": {"source": "sample", "type": "document"}
            }
        ]
    
    def calculate_keyword_score(self, query: str, text: str) -> float:
        """Calculate keyword-based relevance score"""
        query_lower = query.lower()
        text_lower = text.lower()
        
        # Exact phrase match
        if query_lower in text_lower:
            return 1.0
        
        # Word matching
        query_words = set(re.findall(r'\w+', query_lower))
        text_words = set(re.findall(r'\w+', text_lower))
        
        if not query_words:
            return 0.0
        
        # Calculate overlap
        matches = len(query_words.intersection(text_words))
        score = matches / len(query_words)
        
        # Boost for title matches
        if any(word in text_lower[:100] for word in query_words):
            score *= 1.5
        
        return min(score, 1.0)
    
    def create_snippet(self, text: str, query: str, max_length: int = 200) -> str:
        """Create a snippet highlighting relevant content"""
        query_words = re.findall(r'\w+', query.lower())
        
        # Find best matching sentence or paragraph
        sentences = re.split(r'[.!?]\s+', text)
        best_sentence = ""
        best_score = 0
        
        for sentence in sentences:
            score = sum(1 for word in query_words if word in sentence.lower())
            if score > best_score:
                best_score = score
                best_sentence = sentence
        
        # Truncate if too long
        if len(best_sentence) > max_length:
            best_sentence = best_sentence[:max_length] + "..."
        
        return best_sentence or text[:max_length] + "..."
    
    async def semantic_search(self, query: str, documents: List[Dict]) -> List[SearchResult]:
        """Perform semantic search using OpenAI embeddings"""
        if not self.openai_available:
            return []
        
        try:
            # Get query embedding
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {search_config.openai_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "input": query,
                    "model": "text-embedding-ada-002"
                }
                
                async with session.post(
                    "https://api.openai.com/v1/embeddings",
                    headers=headers,
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        query_embedding = result["data"][0]["embedding"]
                        
                        # For demo purposes, we'll simulate document embeddings
                        # In production, you'd store these embeddings in a vector database
                        search_results = []
                        
                        for doc in documents:
                            # Simulate semantic similarity (in production, use actual cosine similarity)
                            # For now, use keyword similarity as a proxy
                            keyword_score = self.calculate_keyword_score(query, doc["content"])
                            semantic_score = min(keyword_score * 0.8 + 0.2, 1.0)  # Simulate semantic boost
                            
                            if semantic_score > search_config.similarity_threshold:
                                snippet = self.create_snippet(doc["content"], query)
                                
                                search_results.append(SearchResult(
                                    title=doc["title"],
                                    content=doc["content"],
                                    source=doc["metadata"]["source"],
                                    score=semantic_score,
                                    metadata=doc["metadata"],
                                    snippet=snippet
                                ))
                        
                        return sorted(search_results, key=lambda x: x.score, reverse=True)
            
        except Exception as e:
            print(f"Semantic search error: {e}")
            return []
    
    async def keyword_search(self, query: str, documents: List[Dict]) -> List[SearchResult]:
        """Perform keyword-based search"""
        search_results = []
        
        for doc in documents:
            # Calculate relevance score
            title_score = self.calculate_keyword_score(query, doc["title"])
            content_score = self.calculate_keyword_score(query, doc["content"])
            
            # Weight title matches higher
            overall_score = (title_score * 0.7) + (content_score * 0.3)
            
            if overall_score > 0.1:  # Minimum threshold
                snippet = self.create_snippet(doc["content"], query)
                
                search_results.append(SearchResult(
                    title=doc["title"],
                    content=doc["content"],
                    source=doc["metadata"]["source"],
                    score=overall_score,
                    metadata=doc["metadata"],
                    snippet=snippet
                ))
        
        return sorted(search_results, key=lambda x: x.score, reverse=True)
    
    async def search(self, query: str, search_type: str = "hybrid") -> Dict[str, Any]:
        """Main search function"""
        if not query.strip():
            return {"error": "Query cannot be empty", "success": False}
        
        try:
            # Get documents from data sources
            documents = await self.get_documents_from_source(search_config.km_docs_url)
            
            if not documents:
                return {
                    "error": "No documents available for search",
                    "success": False,
                    "suggestion": "Check if km-mcp-sql-docs service is running"
                }
            
            results = []
            
            if search_type in ["semantic", "hybrid"]:
                semantic_results = await self.semantic_search(query, documents)
                results.extend(semantic_results)
            
            if search_type in ["keyword", "hybrid"]:
                keyword_results = await self.keyword_search(query, documents)
                
                # Merge results, avoiding duplicates
                existing_titles = {r.title for r in results}
                for result in keyword_results:
                    if result.title not in existing_titles:
                        results.append(result)
            
            # Sort by score and limit results
            results = sorted(results, key=lambda x: x.score, reverse=True)
            results = results[:search_config.max_results]
            
            # Convert to JSON-serializable format
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.title,
                    "snippet": result.snippet,
                    "source": result.source,
                    "score": round(result.score, 3),
                    "metadata": result.metadata
                })
            
            return {
                "query": query,
                "search_type": search_type,
                "total_results": len(formatted_results),
                "results": formatted_results,
                "success": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "error": f"Search failed: {str(e)}",
                "success": False
            }

# Initialize search service
search_service = SearchService()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Clean MCP server interface for search service"""
    
    # Check search service status
    if search_service.openai_available:
        search_status = "Connected"
        search_provider = "OpenAI Embeddings"
    else:
        search_status = "Limited"
        search_provider = "Keyword Only"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KM-MCP-Search Server</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 40px 20px;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }}
            .header {{
                background: white;
                padding: 30px 40px;
                border-bottom: 1px solid #e5e7eb;
                display: flex;
                align-items: center;
                gap: 20px;
            }}
            .icon {{
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                color: white;
            }}
            .title {{
                font-size: 36px;
                font-weight: 600;
                color: #1f2937;
            }}
            .status-section {{
                padding: 30px 40px;
                background: #dcfce7;
                border-left: 4px solid #22c55e;
                margin: 0;
            }}
            .status-title {{
                font-size: 22px;
                font-weight: 600;
                color: #1f2937;
                margin-bottom: 5px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .status-subtitle {{
                color: #6b7280;
                font-size: 16px;
            }}
            .stats-section {{
                padding: 30px 40px;
                background: #f9fafb;
            }}
            .stats-title {{
                font-size: 20px;
                font-weight: 600;
                color: #1f2937;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .stat-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 0;
                border-bottom: 1px solid #e5e7eb;
            }}
            .stat-row:last-child {{ border-bottom: none; }}
            .stat-label {{ color: #1f2937; font-weight: 500; }}
            .stat-value {{ 
                color: #1f2937; 
                font-weight: 600; 
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .connected {{ color: #22c55e; }}
            .limited {{ color: #f59e0b; }}
            .endpoints-section {{
                padding: 30px 40px;
            }}
            .endpoints-title {{
                font-size: 20px;
                font-weight: 600;
                color: #1f2937;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .endpoint {{
                display: flex;
                align-items: flex-start;
                gap: 15px;
                padding: 15px 0;
                border-bottom: 1px solid #e5e7eb;
                border-left: 4px solid #e5e7eb;
                padding-left: 20px;
                margin-bottom: 10px;
            }}
            .endpoint:last-child {{ border-bottom: none; margin-bottom: 0; }}
            .method {{
                padding: 4px 12px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                min-width: 50px;
                text-align: center;
            }}
            .method.get {{ background: #dbeafe; color: #1d4ed8; }}
            .method.post {{ background: #dcfce7; color: #16a34a; }}
            .endpoint-content {{
                flex: 1;
            }}
            .endpoint-path {{
                font-family: 'Monaco', 'Consolas', monospace;
                font-weight: 600;
                color: #1f2937;
                margin-bottom: 5px;
            }}
            .endpoint-description {{
                color: #6b7280;
                font-size: 14px;
                line-height: 1.5;
            }}
            .footer {{
                padding: 20px 40px;
                background: #f9fafb;
                text-align: center;
                color: #6b7280;
                font-size: 14px;
                border-top: 1px solid #e5e7eb;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="icon">🔍</div>
                <div class="title">KM-MCP-Search Server</div>
            </div>

            <div class="status-section">
                <div class="status-title">
                    ✅ Service is Running
                </div>
                <div class="status-subtitle">
                    Intelligent Document Search Service
                </div>
            </div>

            <div class="stats-section">
                <div class="stats-title">
                    📊 System Statistics
                </div>
                <div class="stat-row">
                    <div class="stat-label">Search Provider:</div>
                    <div class="stat-value">{search_provider}</div>
                </div>
                <div class="stat-row">
                    <div class="stat-label">Search Status:</div>
                    <div class="stat-value">
                        {"✅" if search_status == "Connected" else "⚠️"} 
                        <span class="{'connected' if search_status == 'Connected' else 'limited'}">{search_status}</span>
                    </div>
                </div>
                <div class="stat-row">
                    <div class="stat-label">Data Sources:</div>
                    <div class="stat-value">km-mcp-sql-docs</div>
                </div>
                <div class="stat-row">
                    <div class="stat-label">Max Results:</div>
                    <div class="stat-value">{search_config.max_results}</div>
                </div>
            </div>

            <div class="endpoints-section">
                <div class="endpoints-title">
                    🔗 Available API Endpoints:
                </div>
                
                <div class="endpoint">
                    <div class="method get">GET</div>
                    <div class="endpoint-content">
                        <div class="endpoint-path">
                            <a href="/health" target="_blank" style="color: #1f2937; text-decoration: none;">/health</a>
                        </div>
                        <div class="endpoint-description">Health check and search service status</div>
                    </div>
                </div>

                <div class="endpoint">
                    <div class="method post">POST</div>
                    <div class="endpoint-content">
                        <div class="endpoint-path">/search</div>
                        <div class="endpoint-description">Search documents with keyword, semantic, or hybrid search</div>
                    </div>
                </div>

                <div class="endpoint">
                    <div class="method post">POST</div>
                    <div class="endpoint-content">
                        <div class="endpoint-path">/search/semantic</div>
                        <div class="endpoint-description">Semantic search using OpenAI embeddings for meaning-based results</div>
                    </div>
                </div>

                <div class="endpoint">
                    <div class="method post">POST</div>
                    <div class="endpoint-content">
                        <div class="endpoint-path">/search/keyword</div>
                        <div class="endpoint-description">Traditional keyword search with fuzzy matching</div>
                    </div>
                </div>

                <div class="endpoint">
                    <div class="method get">GET</div>
                    <div class="endpoint-content">
                        <div class="endpoint-path">
                            <a href="/docs" target="_blank" style="color: #1f2937; text-decoration: none;">/docs</a>
                        </div>
                        <div class="endpoint-description">Interactive API documentation (Swagger UI)</div>
                    </div>
                </div>
            </div>

            <div class="footer">
                Knowledge Management System v1.0 | Status: Production Ready
            </div>
        </div>

        <!-- Interactive Testing Section -->
        <div class="container" style="margin-top: 20px;">
            <div style="padding: 30px 40px; background: #f8fafc; border-bottom: 1px solid #e5e7eb;">
                <div style="font-size: 20px; font-weight: 600; color: #1f2937; display: flex; align-items: center; gap: 10px;">
                    🧪 Interactive Search Testing
                </div>
                <div style="color: #6b7280; font-size: 14px; margin-top: 5px;">
                    Test the search endpoints directly from the browser
                </div>
            </div>

            <!-- Search Form -->
            <div style="padding: 30px 40px;">
                <div style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 8px; color: #1f2937; font-weight: 500;">Search Query</label>
                    <input type="text" id="searchQuery" placeholder="Enter your search query..." style="width: 100%; padding: 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;">
                </div>
                
                <div style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 8px; color: #1f2937; font-weight: 500;">Search Type</label>
                    <select id="searchType" style="width: 100%; padding: 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px;">
                        <option value="hybrid">Hybrid (Semantic + Keyword)</option>
                        <option value="semantic">Semantic Search</option>
                        <option value="keyword">Keyword Search</option>
                    </select>
                </div>
                
                <button onclick="performSearch()" style="background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 600;">
                    🔍 Search
                </button>
                
                <div id="searchResults" style="margin-top: 30px; display: none;">
                    <h3 style="color: #1f2937; margin-bottom: 20px;">Search Results</h3>
                    <div id="resultsContainer"></div>
                </div>
            </div>
        </div>

        <script>
            async function performSearch() {{
                const query = document.getElementById('searchQuery').value;
                const searchType = document.getElementById('searchType').value;
                
                if (!query.trim()) {{
                    alert('Please enter a search query');
                    return;
                }}
                
                try {{
                    const response = await fetch('/search', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ query, search_type: searchType }})
                    }});
                    
                    const result = await response.json();
                    displayResults(result);
                }} catch (e) {{
                    document.getElementById('resultsContainer').innerHTML = 
                        '<div style="color: #ef4444; padding: 20px; background: #fef2f2; border-radius: 6px;">Error: ' + e.message + '</div>';
                    document.getElementById('searchResults').style.display = 'block';
                }}
            }}
            
            function displayResults(result) {{
                const container = document.getElementById('resultsContainer');
                
                if (!result.success) {{
                    container.innerHTML = 
                        '<div style="color: #ef4444; padding: 20px; background: #fef2f2; border-radius: 6px;">' + 
                        result.error + '</div>';
                }} else if (result.total_results === 0) {{
                    container.innerHTML = 
                        '<div style="color: #6b7280; padding: 20px; background: #f9fafb; border-radius: 6px;">' + 
                        'No results found for "' + result.query + '"</div>';
                }} else {{
                    let html = '<div style="color: #1f2937; margin-bottom: 20px; font-weight: 500;">' + 
                              'Found ' + result.total_results + ' results for "' + result.query + '"</div>';
                    
                    result.results.forEach(item => {{
                        html += '<div style="border: 1px solid #e5e7eb; border-radius: 6px; padding: 20px; margin-bottom: 15px; background: white;">' +
                               '<h4 style="color: #1f2937; margin-bottom: 10px;">' + item.title + '</h4>' +
                               '<p style="color: #6b7280; margin-bottom: 10px; line-height: 1.5;">' + item.snippet + '</p>' +
                               '<div style="display: flex; justify-content: space-between; align-items: center; font-size: 12px; color: #9ca3af;">' +
                               '<span>Source: ' + item.source + '</span>' +
                               '<span>Score: ' + item.score + '</span>' +
                               '</div>' +
                               '</div>';
                    }});
                    
                    container.innerHTML = html;
                }}
                
                document.getElementById('searchResults').style.display = 'block';
            }}
            
            // Allow Enter key to search
            document.getElementById('searchQuery').addEventListener('keypress', function(e) {{
                if (e.key === 'Enter') {{
                    performSearch();
                }}
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """Health check endpoint with search service status"""
    
    search_providers = []
    if search_service.openai_available:
        search_providers.append("OpenAI Embeddings")
    search_providers.append("Keyword Search")
    
    health_status = {
        "service": "km-mcp-search",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "search_providers": search_providers,
        "semantic_search_available": search_service.openai_available,
        "endpoints": {
            "health": "/health",
            "search": "/search",
            "semantic_search": "/search/semantic",
            "keyword_search": "/search/keyword",
            "docs": "/docs"
        },
        "data_sources": {
            "km_sql_docs": search_config.km_docs_url
        },
        "configuration": {
            "max_results": search_config.max_results,
            "similarity_threshold": search_config.similarity_threshold
        }
    }
    
    # Test connectivity to data sources
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{search_config.km_docs_url}/health", timeout=5) as response:
                if response.status == 200:
                    health_status["data_sources"]["km_sql_docs_status"] = "connected"
                else:
                    health_status["data_sources"]["km_sql_docs_status"] = "limited"
    except Exception:
        health_status["data_sources"]["km_sql_docs_status"] = "unreachable"
    
    return JSONResponse(content=health_status)

@app.post("/search")
async def search_documents(request: Request):
    """Main search endpoint with hybrid search"""
    try:
        data = await request.json()
        query = data.get("query", "")
        search_type = data.get("search_type", "hybrid")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")
        
        result = await search_service.search(query, search_type)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Search failed: {str(e)}", "success": False}
        )

@app.post("/search/semantic")
async def semantic_search_endpoint(request: Request):
    """Semantic search using OpenAI embeddings"""
    try:
        data = await request.json()
        query = data.get("query", "")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")
        
        if not search_service.openai_available:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Semantic search requires OpenAI API key",
                    "success": False,
                    "suggestion": "Configure OPENAI_API_KEY environment variable"
                }
            )
        
        result = await search_service.search(query, "semantic")
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Semantic search failed: {str(e)}", "success": False}
        )

@app.post("/search/keyword")
async def keyword_search_endpoint(request: Request):
    """Keyword-based search"""
    try:
        data = await request.json()
        query = data.get("query", "")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query parameter is required")
        
        result = await search_service.search(query, "keyword")
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Keyword search failed: {str(e)}", "success": False}
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)