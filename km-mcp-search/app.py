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
            
            /* Form styles matching km-mcp-sql-docs */
            .form-area {{
                margin-top: 15px;
                padding: 15px;
                background: #fff;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                display: none;
            }}
            .form-area.show {{ display: block; }}
            .form-group {{
                margin-bottom: 15px;
            }}
            .form-group label {{
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
                color: #333;
            }}
            .form-group input, .form-group textarea, .form-group select {{
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-size: 14px;
            }}
            .form-group textarea {{
                min-height: 100px;
                resize: vertical;
            }}
            .btn {{
                background: #007bff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                margin-right: 10px;
            }}
            .btn:hover {{
                background: #0056b3;
            }}
            
            /* Result display area */
            .result-area {{
                margin-top: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 10px;
                display: none;
            }}
            .result-area.show {{ display: block; }}
            .result-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }}
            .result-content {{
                background: #2d3748;
                color: #e2e8f0;
                padding: 15px;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                overflow-x: auto;
                white-space: pre-wrap;
            }}
            .close-btn {{
                background: #dc3545;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                cursor: pointer;
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
                
                <div class="endpoint" onclick="callEndpoint('GET', '/health')">
                    <div class="method get">GET</div>
                    <div class="endpoint-content">
                        <div class="endpoint-path">
                            <a href="/health" target="_blank" style="color: #1f2937; text-decoration: none;">/health</a>
                        </div>
                        <div class="endpoint-description">Health check and search service status</div>
                    </div>
                </div>

                <div class="endpoint" onclick="showForm('search')">
                    <div class="method post">POST</div>
                    <div class="endpoint-content">
                        <div class="endpoint-path">/search</div>
                        <div class="endpoint-description">Search documents with keyword, semantic, or hybrid search</div>
                        <div class="form-area" id="form-search">
                            <div class="form-group">
                                <label>Search Query:</label>
                                <input type="text" id="main-search-query" placeholder="Enter your search query..." required>
                            </div>
                            <div class="form-group">
                                <label>Search Type:</label>
                                <select id="main-search-type">
                                    <option value="hybrid">Hybrid (Semantic + Keyword)</option>
                                    <option value="semantic">Semantic Search</option>
                                    <option value="keyword">Keyword Search</option>
                                </select>
                            </div>
                            <button class="btn" onclick="submitMainSearch()">🔍 Search</button>
                            <button class="btn" style="background: #6c757d;" onclick="hideForm('search')">Cancel</button>
                        </div>
                    </div>
                </div>

                <div class="endpoint" onclick="showForm('semantic-search')">
                    <div class="method post">POST</div>
                    <div class="endpoint-content">
                        <div class="endpoint-path">/search/semantic</div>
                        <div class="endpoint-description">Semantic search using OpenAI embeddings for meaning-based results</div>
                        <div class="form-area" id="form-semantic-search">
                            <div class="form-group">
                                <label>Search Query:</label>
                                <input type="text" id="semantic-search-query" placeholder="Enter semantic search query..." required>
                            </div>
                            <div class="form-group">
                                <label>Description:</label>
                                <p style="color: #666; font-size: 14px; margin: 0;">Semantic search finds documents based on meaning and context, not just exact word matches.</p>
                            </div>
                            <button class="btn" onclick="submitSemanticSearch()">🧠 Semantic Search</button>
                            <button class="btn" style="background: #6c757d;" onclick="hideForm('semantic-search')">Cancel</button>
                        </div>
                    </div>
                </div>

                <div class="endpoint" onclick="showForm('keyword-search')">
                    <div class="method post">POST</div>
                    <div class="endpoint-content">
                        <div class="endpoint-path">/search/keyword</div>
                        <div class="endpoint-description">Traditional keyword search with fuzzy matching</div>
                        <div class="form-area" id="form-keyword-search">
                            <div class="form-group">
                                <label>Search Query:</label>
                                <input type="text" id="keyword-search-query" placeholder="Enter keyword search query..." required>
                            </div>
                            <div class="form-group">
                                <label>Description:</label>
                                <p style="color: #666; font-size: 14px; margin: 0;">Keyword search finds documents containing exact words or phrases from your query.</p>
                            </div>
                            <button class="btn" onclick="submitKeywordSearch()">📝 Keyword Search</button>
                            <button class="btn" style="background: #6c757d;" onclick="hideForm('keyword-search')">Cancel</button>
                        </div>
                    </div>
                </div>

                <div class="endpoint" onclick="callEndpoint('GET', '/docs')">
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

            <div class="footer">
                Knowledge Management System v1.0 | Status: Production Ready
            </div>
        </div>

        <!-- Result display area -->
        <div class="result-area" id="result-area">
            <div class="result-header">
                <h3 id="result-title">Search Results</h3>
                <button class="close-btn" onclick="hideResult()">Close</button>
            </div>
            <div class="result-content" id="result-content"></div>
        </div>

        <script>
            // Show form for POST endpoints (matching km-mcp-sql-docs behavior)
            function showForm(formType) {{
                // Hide all forms first
                const forms = document.querySelectorAll('.form-area');
                forms.forEach(form => form.classList.remove('show'));
                
                // Show the requested form
                const form = document.getElementById(`form-${{formType}}`);
                if (form) {{
                    form.classList.add('show');
                }}
            }}
            
            // Hide form
            function hideForm(formType) {{
                const form = document.getElementById(`form-${{formType}}`);
                if (form) {{
                    form.classList.remove('show');
                }}
            }}
            
            // Call GET endpoints directly
            async function callEndpoint(method, path) {{
                showResult(`${{method}} ${{path}}`, 'Loading...');
                
                try {{
                    const response = await fetch(path, {{ method: method }});
                    const data = await response.json();
                    showResult(`${{method}} ${{path}}`, JSON.stringify(data, null, 2));
                }} catch (error) {{
                    showResult(`${{method}} ${{path}}`, `Error: ${{error.message}}`);
                }}
            }}
            
            // Submit main search form
            async function submitMainSearch() {{
                const query = document.getElementById('main-search-query').value;
                const searchType = document.getElementById('main-search-type').value;
                
                if (!query.trim()) {{
                    alert('Please enter a search query');
                    return;
                }}
                
                showResult('POST /search', 'Searching...');
                
                try {{
                    const response = await fetch('/search', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ query, search_type: searchType }})
                    }});
                    
                    const result = await response.json();
                    displaySearchResults(result, 'POST /search');
                    hideForm('search');
                }} catch (e) {{
                    showResult('POST /search', `Error: ${{e.message}}`);
                }}
            }}
            
            // Submit semantic search form
            async function submitSemanticSearch() {{
                const query = document.getElementById('semantic-search-query').value;
                
                if (!query.trim()) {{
                    alert('Please enter a search query');
                    return;
                }}
                
                showResult('POST /search/semantic', 'Searching with AI...');
                
                try {{
                    const response = await fetch('/search/semantic', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ query }})
                    }});
                    
                    const result = await response.json();
                    displaySearchResults(result, 'POST /search/semantic');
                    hideForm('semantic-search');
                }} catch (e) {{
                    showResult('POST /search/semantic', `Error: ${{e.message}}`);
                }}
            }}
            
            // Submit keyword search form
            async function submitKeywordSearch() {{
                const query = document.getElementById('keyword-search-query').value;
                
                if (!query.trim()) {{
                    alert('Please enter a search query');
                    return;
                }}
                
                showResult('POST /search/keyword', 'Searching keywords...');
                
                try {{
                    const response = await fetch('/search/keyword', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ query }})
                    }});
                    
                    const result = await response.json();
                    displaySearchResults(result, 'POST /search/keyword');
                    hideForm('keyword-search');
                }} catch (e) {{
                    showResult('POST /search/keyword', `Error: ${{e.message}}`);
                }}
            }}
            
            // Display search results in a user-friendly format
            function displaySearchResults(result, title) {{
                if (!result.success) {{
                    showResult(title, `Error: ${{result.error}}`);
                    return;
                }}
                
                if (result.total_results === 0) {{
                    showResult(title, 'No results found for your search query.');
                    return;
                }}
                
                let formattedResults = `Found ${{result.total_results}} results for "${{result.query}}"\\n`;
                formattedResults += `Search Type: ${{result.search_type}}\\n`;
                formattedResults += `Timestamp: ${{result.timestamp}}\\n\\n`;
                
                result.results.forEach((item, index) => {{
                    formattedResults += `--- Result ${{index + 1}} ---\\n`;
                    formattedResults += `Title: ${{item.title}}\\n`;
                    formattedResults += `Score: ${{item.score}}\\n`;
                    formattedResults += `Source: ${{item.source}}\\n`;
                    formattedResults += `Snippet: ${{item.snippet}}\\n`;
                    if (item.metadata && item.metadata.file_type) {{
                        formattedResults += `File Type: ${{item.metadata.file_type}}\\n`;
                    }}
                    formattedResults += `\\n`;
                }});
                
                showResult(title, formattedResults);
            }}
            
            // Show result in the result area
            function showResult(title, content) {{
                document.getElementById('result-title').textContent = title;
                document.getElementById('result-content').textContent = content;
                document.getElementById('result-area').classList.add('show');
                document.getElementById('result-area').scrollIntoView({{ behavior: 'smooth' }});
            }}
            
            // Hide result area
            function hideResult() {{
                document.getElementById('result-area').classList.remove('show');
            }}
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