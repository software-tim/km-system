"""
km-mcp-graphrag: Knowledge Graph and Relationship Analysis Service
Builds knowledge graphs from documents and provides graph-based insights
Integrates with km-mcp-search and km-mcp-llm for enhanced analysis
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Set, Tuple
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import aiohttp
import re
from dataclasses import dataclass, asdict
from collections import defaultdict

# Initialize FastAPI app
app = FastAPI(
    title="KM MCP GraphRAG Service",
    description="Knowledge Graph and Relationship Analysis Service",
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

# Configuration
class GraphRAGConfig:
    def __init__(self):
        # OpenAI for entity extraction and analysis
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Service integrations
        self.km_search_url = "https://km-mcp-search.azurewebsites.net"
        self.km_llm_url = "https://km-mcp-llm.azurewebsites.net"
        self.km_docs_url = "https://km-mcp-sql-docs.azurewebsites.net"

config = GraphRAGConfig()

@dataclass
class Entity:
    name: str
    type: str  # PERSON, ORGANIZATION, LOCATION, CONCEPT, etc.
    description: str
    confidence: float
    documents: List[str]  # Document IDs where this entity appears

@dataclass
class Relationship:
    source_entity: str
    target_entity: str
    relation_type: str
    description: str
    confidence: float
    documents: List[str]

@dataclass
class KnowledgeGraph:
    entities: Dict[str, Entity]
    relationships: List[Relationship]
    metadata: Dict[str, Any]

class GraphRAGService:
    """Handles knowledge graph construction and analysis"""
    
    def __init__(self):
        self.openai_available = bool(config.openai_api_key)
        self.knowledge_graph = KnowledgeGraph(entities={}, relationships=[], metadata={})
    
    async def extract_entities_from_text(self, text: str, doc_id: str) -> List[Entity]:
        """Extract entities from text using OpenAI"""
        if not self.openai_available:
            return []
        
        prompt = f"""Extract named entities from the following text. For each entity, provide:
1. Entity name
2. Entity type (PERSON, ORGANIZATION, LOCATION, CONCEPT, TECHNOLOGY, EVENT)
3. Brief description
4. Confidence score (0.0-1.0)

Format as JSON array:
[{{"name": "Entity Name", "type": "TYPE", "description": "Brief description", "confidence": 0.9}}]

Text: {text[:2000]}"""  # Limit text length
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.openai_api_key}"
            }
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.3
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.openai.com/v1/chat/completions", 
                                      headers=headers, json=payload, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        entities_text = result["choices"][0]["message"]["content"]
                        
                        # Parse JSON response
                        try:
                            entities_data = json.loads(entities_text)
                            entities = []
                            for e in entities_data:
                                entity = Entity(
                                    name=e["name"],
                                    type=e["type"],
                                    description=e["description"],
                                    confidence=e["confidence"],
                                    documents=[doc_id]
                                )
                                entities.append(entity)
                            return entities
                        except json.JSONDecodeError:
                            # Fallback to simple extraction if JSON parsing fails
                            return self.fallback_entity_extraction(text, doc_id)
        except Exception as e:
            print(f"Entity extraction error: {e}")
            return self.fallback_entity_extraction(text, doc_id)
    
    def fallback_entity_extraction(self, text: str, doc_id: str) -> List[Entity]:
        """Simple fallback entity extraction using regex patterns"""
        entities = []
        
        # Simple patterns for common entities
        patterns = {
            "ORGANIZATION": r'\b[A-Z][a-z]+ (?:Inc|Corp|LLC|Ltd|Company|Corporation|Organization)\b',
            "TECHNOLOGY": r'\b(?:API|Azure|AWS|Docker|Python|JavaScript|React|FastAPI|OpenAI|AI|ML)\b',
            "CONCEPT": r'\b(?:deployment|service|database|search|analysis|integration)\b'
        }
        
        for entity_type, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entity = Entity(
                    name=match.group(),
                    type=entity_type,
                    description=f"{entity_type} entity extracted from document",
                    confidence=0.7,
                    documents=[doc_id]
                )
                entities.append(entity)
        
        return entities
    
    async def extract_relationships_from_text(self, text: str, entities: List[Entity], doc_id: str) -> List[Relationship]:
        """Extract relationships between entities using OpenAI"""
        if not self.openai_available or len(entities) < 2:
            return []
        
        entity_names = [e.name for e in entities]
        prompt = f"""Given these entities from a document: {', '.join(entity_names)}

Identify relationships between these entities in the text. For each relationship, provide:
1. Source entity name
2. Target entity name  
3. Relationship type (WORKS_FOR, USES, RELATED_TO, PART_OF, etc.)
4. Description of the relationship
5. Confidence score (0.0-1.0)

Format as JSON array:
[{{"source": "Entity1", "target": "Entity2", "type": "USES", "description": "Entity1 uses Entity2 for analysis", "confidence": 0.8}}]

Text: {text[:1500]}"""
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.openai_api_key}"
            }
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 800,
                "temperature": 0.3
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.openai.com/v1/chat/completions", 
                                      headers=headers, json=payload, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        relationships_text = result["choices"][0]["message"]["content"]
                        
                        try:
                            relationships_data = json.loads(relationships_text)
                            relationships = []
                            for r in relationships_data:
                                if r["source"] in entity_names and r["target"] in entity_names:
                                    relationship = Relationship(
                                        source_entity=r["source"],
                                        target_entity=r["target"],
                                        relation_type=r["type"],
                                        description=r["description"],
                                        confidence=r["confidence"],
                                        documents=[doc_id]
                                    )
                                    relationships.append(relationship)
                            return relationships
                        except json.JSONDecodeError:
                            return []
        except Exception as e:
            print(f"Relationship extraction error: {e}")
            return []
    
    async def get_documents_from_search(self) -> List[Dict[str, Any]]:
        """Get documents from search service"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"query": "", "search_type": "keyword", "limit": 100}
                async with session.post(f"{config.km_search_url}/search", 
                                      json=payload, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("success"):
                            return result.get("results", [])
        except Exception as e:
            print(f"Error getting documents from search: {e}")
        return []
    
    async def build_knowledge_graph(self) -> Dict[str, Any]:
        """Build complete knowledge graph from all documents"""
        try:
            # Get documents from search service
            documents = await self.get_documents_from_search()
            
            if not documents:
                return {
                    "success": False,
                    "error": "No documents available for graph construction"
                }
            
            all_entities = {}
            all_relationships = []
            
            # Process each document
            for i, doc in enumerate(documents):
                doc_id = str(doc.get("metadata", {}).get("id", i))
                title = doc.get("title", f"Document {i+1}")
                content = doc.get("snippet", "")
                
                if not content.strip():
                    continue
                
                # Extract entities
                entities = await self.extract_entities_from_text(content, doc_id)
                
                # Merge entities (combine if same name)
                for entity in entities:
                    if entity.name in all_entities:
                        # Update existing entity
                        existing = all_entities[entity.name]
                        existing.documents.append(doc_id)
                        existing.confidence = max(existing.confidence, entity.confidence)
                    else:
                        all_entities[entity.name] = entity
                
                # Extract relationships
                relationships = await self.extract_relationships_from_text(content, entities, doc_id)
                all_relationships.extend(relationships)
            
            # Update knowledge graph
            self.knowledge_graph = KnowledgeGraph(
                entities=all_entities,
                relationships=all_relationships,
                metadata={
                    "documents_processed": len(documents),
                    "entities_found": len(all_entities),
                    "relationships_found": len(all_relationships),
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "success": True,
                "graph": {
                    "entities": {name: asdict(entity) for name, entity in all_entities.items()},
                    "relationships": [asdict(rel) for rel in all_relationships],
                    "metadata": self.knowledge_graph.metadata
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Graph construction failed: {str(e)}"
            }
    
    async def analyze_entity_connections(self, entity_name: str) -> Dict[str, Any]:
        """Analyze connections for a specific entity"""
        if entity_name not in self.knowledge_graph.entities:
            return {
                "success": False,
                "error": f"Entity '{entity_name}' not found in knowledge graph"
            }
        
        entity = self.knowledge_graph.entities[entity_name]
        
        # Find all relationships involving this entity
        connections = []
        for rel in self.knowledge_graph.relationships:
            if rel.source_entity == entity_name:
                connections.append({
                    "direction": "outgoing",
                    "target": rel.target_entity,
                    "type": rel.relation_type,
                    "description": rel.description,
                    "confidence": rel.confidence
                })
            elif rel.target_entity == entity_name:
                connections.append({
                    "direction": "incoming",
                    "source": rel.source_entity,
                    "type": rel.relation_type,
                    "description": rel.description,
                    "confidence": rel.confidence
                })
        
        return {
            "success": True,
            "entity": asdict(entity),
            "connections": connections,
            "connection_count": len(connections)
        }
    
    async def get_graph_insights(self) -> Dict[str, Any]:
        """Generate insights about the knowledge graph"""
        entities = self.knowledge_graph.entities
        relationships = self.knowledge_graph.relationships
        
        if not entities:
            return {
                "success": False,
                "error": "No knowledge graph available. Build graph first."
            }
        
        # Entity type distribution
        entity_types = defaultdict(int)
        for entity in entities.values():
            entity_types[entity.type] += 1
        
        # Relationship type distribution
        relation_types = defaultdict(int)
        for rel in relationships:
            relation_types[rel.relation_type] += 1
        
        # Most connected entities
        entity_connections = defaultdict(int)
        for rel in relationships:
            entity_connections[rel.source_entity] += 1
            entity_connections[rel.target_entity] += 1
        
        most_connected = sorted(entity_connections.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "success": True,
            "insights": {
                "total_entities": len(entities),
                "total_relationships": len(relationships),
                "entity_types": dict(entity_types),
                "relationship_types": dict(relation_types),
                "most_connected_entities": most_connected,
                "average_connections": sum(entity_connections.values()) / len(entity_connections) if entity_connections else 0
            },
            "metadata": self.knowledge_graph.metadata
        }

# Initialize GraphRAG service
graphrag_service = GraphRAGService()

@app.get("/", response_class=HTMLResponse)
async def root():
    """Clean MCP server interface for GraphRAG service"""
    
    # Check service status
    if graphrag_service.openai_available:
        ai_status = "Connected"
        ai_provider = "OpenAI API"
    else:
        ai_status = "Not Configured"
        ai_provider = "None"
    
    # Graph stats
    graph_stats = len(graphrag_service.knowledge_graph.entities)
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>KM-MCP-GraphRAG Server</title>
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
                background: #f8f9fa;
                padding: 15px;
                margin: 10px 0;
                border-radius: 8px;
                border-left: 4px solid #667eea;
                font-family: 'Courier New', monospace;
                cursor: pointer;
                transition: all 0.3s ease;
                position: relative;
            }}
            .endpoint:hover {{
                background: #e9ecef;
                border-left-color: #4c63d2;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }}
            .method {{
                display: inline-block;
                padding: 3px 8px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
                margin-right: 10px;
                color: white;
            }}
            .method.get {{ background: #61affe; }}
            .method.post {{ background: #49cc90; }}
            .footer {{
                padding: 20px 40px;
                background: #f9fafb;
                text-align: center;
                color: #6b7280;
                font-size: 14px;
                border-top: 1px solid #e5e7eb;
            }}
            
            /* Form styles matching other services */
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
            .form-group input, .form-group textarea {{
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-size: 14px;
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
                <div class="icon">🕸️</div>
                <div class="title">KM-MCP-GraphRAG Server</div>
            </div>

            <div class="status-section">
                <div class="status-title">
                    ✅ Service is Running
                </div>
                <div class="status-subtitle">
                    Knowledge Graph and Relationship Analysis Service
                </div>
            </div>

            <div class="stats-section">
                <div class="stats-title">
                    📊 System Statistics
                </div>
                <div class="stat-row">
                    <div class="stat-label">AI Provider:</div>
                    <div class="stat-value">{ai_provider}</div>
                </div>
                <div class="stat-row">
                    <div class="stat-label">AI Status:</div>
                    <div class="stat-value">
                        {"✅" if ai_status == "Connected" else "❌"} 
                        <span class="{'connected' if ai_status == 'Connected' else ''}">{ai_status}</span>
                    </div>
                </div>
                <div class="stat-row">
                    <div class="stat-label">Knowledge Graph:</div>
                    <div class="stat-value">{graph_stats} entities</div>
                </div>
                <div class="stat-row">
                    <div class="stat-label">Service Status:</div>
                    <div class="stat-value">✅ <span class="connected">Running</span></div>
                </div>
            </div>

            <div class="endpoints-section">
                <div class="endpoints-title">
                    🔗 Available API Endpoints:
                </div>
                
                <div class="endpoint" onclick="callEndpoint('GET', '/health')">
                    <span class="method get">GET</span>
                    <span>/health</span> - Health check and GraphRAG service status
                </div>

                <div class="endpoint" onclick="showForm('build-graph')">
                    <span class="method post">POST</span>
                    <span>/build-graph</span> - Build knowledge graph from all documents
                    <div class="form-area" id="form-build-graph">
                        <div class="form-group">
                            <label>Description:</label>
                            <p style="color: #666; font-size: 14px; margin: 0;">This will analyze all documents to extract entities and relationships, building a comprehensive knowledge graph.</p>
                        </div>
                        <button class="btn" onclick="submitBuildGraph()">🕸️ Build Knowledge Graph</button>
                        <button class="btn" style="background: #6c757d;" onclick="hideForm('build-graph')">Cancel</button>
                    </div>
                </div>

                <div class="endpoint" onclick="showForm('analyze-entity')">
                    <span class="method post">POST</span>
                    <span>/analyze-entity</span> - Analyze connections for a specific entity
                    <div class="form-area" id="form-analyze-entity">
                        <div class="form-group">
                            <label>Entity Name:</label>
                            <input type="text" id="entity-name" placeholder="Enter entity name to analyze..." required>
                        </div>
                        <div class="form-group">
                            <label>Description:</label>
                            <p style="color: #666; font-size: 14px; margin: 0;">Find all connections and relationships for a specific entity in the knowledge graph.</p>
                        </div>
                        <button class="btn" onclick="submitAnalyzeEntity()">🔍 Analyze Entity</button>
                        <button class="btn" style="background: #6c757d;" onclick="hideForm('analyze-entity')">Cancel</button>
                    </div>
                </div>

                <div class="endpoint" onclick="showForm('graph-insights')">
                    <span class="method post">POST</span>
                    <span>/graph-insights</span> - Get insights and statistics about the knowledge graph
                    <div class="form-area" id="form-graph-insights">
                        <div class="form-group">
                            <label>Description:</label>
                            <p style="color: #666; font-size: 14px; margin: 0;">Generate comprehensive insights about entity types, relationships, and graph structure.</p>
                        </div>
                        <button class="btn" onclick="submitGraphInsights()">📈 Get Graph Insights</button>
                        <button class="btn" style="background: #6c757d;" onclick="hideForm('graph-insights')">Cancel</button>
                    </div>
                </div>

                <div class="endpoint" onclick="callEndpoint('GET', '/docs')">
                    <span class="method get">GET</span>
                    <span>/docs</span> - Interactive API documentation (Swagger UI)
                </div>
            </div>

            <div class="footer">
                Knowledge Management System v1.0 | Status: Production Ready
            </div>
        </div>

        <!-- Result display area -->
        <div class="result-area" id="result-area">
            <div class="result-header">
                <h3 id="result-title">GraphRAG Results</h3>
                <button class="close-btn" onclick="hideResult()">Close</button>
            </div>
            <div class="result-content" id="result-content"></div>
        </div>

        <script>
            // Show form for POST endpoints
            function showForm(formType) {{
                const forms = document.querySelectorAll('.form-area');
                forms.forEach(form => form.classList.remove('show'));
                
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
            
            // Submit build graph
            async function submitBuildGraph() {{
                showResult('POST /build-graph', 'Building knowledge graph...');
                
                try {{
                    const response = await fetch('/build-graph', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{}})
                    }});
                    
                    const result = await response.json();
                    displayGraphResult(result, 'Knowledge Graph Construction');
                    hideForm('build-graph');
                }} catch (e) {{
                    showResult('POST /build-graph', `Error: ${{e.message}}`);
                }}
            }}
            
            // Submit analyze entity
            async function submitAnalyzeEntity() {{
                const entityName = document.getElementById('entity-name').value;
                
                if (!entityName.trim()) {{
                    alert('Please enter an entity name');
                    return;
                }}
                
                showResult('POST /analyze-entity', 'Analyzing entity connections...');
                
                try {{
                    const response = await fetch('/analyze-entity', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ entity_name: entityName }})
                    }});
                    
                    const result = await response.json();
                    displayGraphResult(result, 'Entity Analysis');
                    hideForm('analyze-entity');
                }} catch (e) {{
                    showResult('POST /analyze-entity', `Error: ${{e.message}}`);
                }}
            }}
            
            // Submit graph insights
            async function submitGraphInsights() {{
                showResult('POST /graph-insights', 'Generating graph insights...');
                
                try {{
                    const response = await fetch('/graph-insights', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{}})
                    }});
                    
                    const result = await response.json();
                    displayGraphResult(result, 'Graph Insights');
                    hideForm('graph-insights');
                }} catch (e) {{
                    showResult('POST /graph-insights', `Error: ${{e.message}}`);
                }}
            }}
            
            // Display graph results in a user-friendly format
            function displayGraphResult(result, title) {{
                if (!result.success) {{
                    showResult(title, `Error: ${{result.error}}`);
                    return;
                }}
                
                showResult(title, JSON.stringify(result, null, 2));
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
    """Health check endpoint with GraphRAG service status"""
    
    ai_providers = []
    if graphrag_service.openai_available:
        ai_providers.append("OpenAI")
    
    health_status = {
        "service": "km-mcp-graphrag",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "ai_providers": ai_providers,
        "ai_configured": len(ai_providers) > 0,
        "knowledge_graph": {
            "entities_count": len(graphrag_service.knowledge_graph.entities),
            "relationships_count": len(graphrag_service.knowledge_graph.relationships),
            "last_updated": graphrag_service.knowledge_graph.metadata.get("created_at", "Never")
        },
        "endpoints": {
            "health": "/health",
            "build_graph": "/build-graph",
            "analyze_entity": "/analyze-entity", 
            "graph_insights": "/graph-insights",
            "docs": "/docs"
        },
        "integrations": {
            "km_search": config.km_search_url,
            "km_llm": config.km_llm_url,
            "km_docs": config.km_docs_url
        }
    }
    
    return JSONResponse(content=health_status)

@app.post("/build-graph")
async def build_graph(request: Request):
    """Build knowledge graph from all documents"""
    try:
        result = await graphrag_service.build_knowledge_graph()
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Graph construction failed: {str(e)}", "success": False}
        )

@app.post("/analyze-entity")
async def analyze_entity(request: Request):
    """Analyze connections for a specific entity"""
    try:
        data = await request.json()
        entity_name = data.get("entity_name", "")
        
        if not entity_name:
            raise HTTPException(status_code=400, detail="Entity name is required")
        
        result = await graphrag_service.analyze_entity_connections(entity_name)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Entity analysis failed: {str(e)}", "success": False}
        )

@app.post("/graph-insights")
async def graph_insights(request: Request):
    """Get insights about the knowledge graph"""
    try:
        result = await graphrag_service.get_graph_insights()
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Insights generation failed: {str(e)}", "success": False}
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)