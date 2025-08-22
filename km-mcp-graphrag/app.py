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
    document_id: str
    confidence: float
    context: str

@dataclass
class Relationship:
    source_entity: str
    target_entity: str
    relationship_type: str
    document_id: str
    confidence: float
    context: str

class KnowledgeGraph:
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.relationships: List[Relationship] = []
        self.entity_connections: Dict[str, Set[str]] = defaultdict(set)

    def add_entity(self, entity: Entity):
        """Add an entity to the graph"""
        key = f"{entity.name.lower()}_{entity.type}"
        if key not in self.entities:
            self.entities[key] = entity
        else:
            # Update confidence if higher
            if entity.confidence > self.entities[key].confidence:
                self.entities[key] = entity

    def add_relationship(self, relationship: Relationship):
        """Add a relationship to the graph"""
        self.relationships.append(relationship)
        # Update connections
        self.entity_connections[relationship.source_entity.lower()].add(relationship.target_entity.lower())
        self.entity_connections[relationship.target_entity.lower()].add(relationship.source_entity.lower())

    def get_entity_connections(self, entity_name: str) -> List[Dict]:
        """Get all connections for an entity"""
        connections = []
        entity_key = entity_name.lower()

        for rel in self.relationships:
            if rel.source_entity.lower() == entity_key:
                connections.append({
                    "connected_entity": rel.target_entity,
                    "relationship": rel.relationship_type,
                    "document_id": rel.document_id,
                    "confidence": rel.confidence,
                    "context": rel.context
                })
            elif rel.target_entity.lower() == entity_key:
                connections.append({
                    "connected_entity": rel.source_entity,
                    "relationship": f"inverse_{rel.relationship_type}",
                    "document_id": rel.document_id,
                    "confidence": rel.confidence,
                    "context": rel.context
                })

        return connections

    def get_graph_stats(self) -> Dict:
        """Get knowledge graph statistics"""
        entity_types = defaultdict(int)
        relationship_types = defaultdict(int)

        for entity in self.entities.values():
            entity_types[entity.type] += 1

        for rel in self.relationships:
            # Normalize relationship type to avoid duplicate keys
            normalized_type = rel.relationship_type.upper()
            relationship_types[normalized_type] += 1

        return {
            "total_entities": len(self.entities),
            "total_relationships": len(self.relationships),
            "entity_types": dict(entity_types),
            "relationship_types": dict(relationship_types),
            "most_connected_entities": self._get_most_connected_entities(5)
        }

    def _get_most_connected_entities(self, limit: int) -> List[Dict]:
        """Get entities with the most connections"""
        connection_counts = defaultdict(int)

        for rel in self.relationships:
            connection_counts[rel.source_entity] += 1
            connection_counts[rel.target_entity] += 1

        sorted_entities = sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)

        return [{"entity": entity, "connections": count} for entity, count in sorted_entities[:limit]]

# Global knowledge graph
knowledge_graph = KnowledgeGraph()

async def call_openai_api(prompt: str, system_message: str = None) -> str:
    """Call OpenAI API for entity extraction and analysis"""
    if not config.openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    headers = {
        "Authorization": f"Bearer {config.openai_api_key}",
        "Content-Type": "application/json"
    }

    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 1500
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.openai.com/v1/chat/completions",
                               headers=headers, json=data) as response:
            if response.status != 200:
                error_text = await response.text()
                raise HTTPException(status_code=500, detail=f"OpenAI API error: {error_text}")

            result = await response.json()
            return result["choices"][0]["message"]["content"]

async def extract_entities_and_relationships(text: str, document_id: str) -> Tuple[List[Entity], List[Relationship]]:
    """Extract entities and relationships from text using OpenAI"""

    system_message = """You are an expert at extracting entities and relationships from text.
    Extract entities (people, organizations, locations, concepts) and relationships between them.
    Return a JSON object with 'entities' and 'relationships' arrays.

    Entity format: {"name": "entity_name", "type": "PERSON|ORGANIZATION|LOCATION|CONCEPT", "confidence": 0.0-1.0, "context": "surrounding text"}
    Relationship format: {"source": "entity1", "target": "entity2", "type": "relationship_type", "confidence": 0.0-1.0, "context": "supporting text"}
    """

    prompt = f"""Extract entities and relationships from this text:

{text[:2000]}  # Limit text length for API

Return valid JSON only."""

    try:
        response = await call_openai_api(prompt, system_message)

        # Parse JSON response
        parsed = json.loads(response)

        entities = []
        relationships = []

        # Process entities
        for entity_data in parsed.get("entities", []):
            entity = Entity(
                name=entity_data["name"],
                type=entity_data["type"],
                document_id=document_id,
                confidence=entity_data.get("confidence", 0.8),
                context=entity_data.get("context", "")
            )
            entities.append(entity)

        # Process relationships
        for rel_data in parsed.get("relationships", []):
            relationship = Relationship(
                source_entity=rel_data["source"],
                target_entity=rel_data["target"],
                relationship_type=rel_data["type"],
                document_id=document_id,
                confidence=rel_data.get("confidence", 0.8),
                context=rel_data.get("context", "")
            )
            relationships.append(relationship)

        return entities, relationships

    except json.JSONDecodeError:
        # Fallback: simple regex-based extraction
        return await simple_entity_extraction(text, document_id)
    except Exception as e:
        print(f"Entity extraction error: {e}")
        return [], []

async def simple_entity_extraction(text: str, document_id: str) -> Tuple[List[Entity], List[Relationship]]:
    """Fallback entity extraction using simple patterns"""
    entities = []

    # Simple patterns for entity extraction
    person_pattern = r'\b[A-Z][a-z]+ [A-Z][a-z]+\b'
    org_pattern = r'\b[A-Z][a-z]+ (?:Inc|Corp|LLC|Company|Organization)\b'

    # Extract potential people
    for match in re.finditer(person_pattern, text):
        entity = Entity(
            name=match.group(),
            type="PERSON",
            document_id=document_id,
            confidence=0.6,
            context=text[max(0, match.start()-50):match.end()+50]
        )
        entities.append(entity)

    # Extract potential organizations
    for match in re.finditer(org_pattern, text):
        entity = Entity(
            name=match.group(),
            type="ORGANIZATION",
            document_id=document_id,
            confidence=0.7,
            context=text[max(0, match.start()-50):match.end()+50]
        )
        entities.append(entity)

    return entities, []

# API Routes

@app.get("/", response_class=HTMLResponse)
async def root():
    """Clean MCP server interface matching the standard format"""
    
    # Check knowledge graph status
    graph_stats = knowledge_graph.get_graph_stats()
    entities_count = graph_stats.get("total_entities", 0)
    relationships_count = graph_stats.get("total_relationships", 0)
    
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
                    <div class="stat-label">Knowledge Graph Entities:</div>
                    <div class="stat-value">{entities_count}</div>
                </div>
                <div class="stat-row">
                    <div class="stat-label">Relationships:</div>
                    <div class="stat-value">{relationships_count}</div>
                </div>
                <div class="stat-row">
                    <div class="stat-label">OpenAI Status:</div>
                    <div class="stat-value">
                        {"✅" if config.openai_api_key else "❌"} 
                        <span class="{'connected' if config.openai_api_key else ''}">{"Connected" if config.openai_api_key else "Not Configured"}</span>
                    </div>
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
                    <span>/health</span> - Health check and knowledge graph status
                </div>

                <div class="endpoint" onclick="callEndpoint('POST', '/tools/build-graph-from-documents')">
                    <span class="method post">POST</span>
                    <span>/tools/build-graph-from-documents</span> - Build knowledge graph from all documents
                </div>

                <div class="endpoint" onclick="callEndpoint('POST', '/tools/extract-entities')">
                    <span class="method post">POST</span>
                    <span>/tools/extract-entities</span> - Extract entities and relationships from text
                </div>

                <div class="endpoint" onclick="callEndpoint('POST', '/tools/analyze-entity')">
                    <span class="method post">POST</span>
                    <span>/tools/analyze-entity</span> - Analyze specific entity connections
                </div>

                <div class="endpoint" onclick="callEndpoint('GET', '/tools/graph-stats')">
                    <span class="method get">GET</span>
                    <span>/tools/graph-stats</span> - Get knowledge graph statistics
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

        <script>
            // Simple endpoint caller (matching other services)
            async function callEndpoint(method, path) {{
                try {{
                    let response;
                    if (method === 'POST' && (path.includes('build-graph') || path.includes('extract-entities') || path.includes('analyze-entity'))) {{
                        // For POST endpoints that need sample data
                        let body = {{}};
                        if (path.includes('extract-entities')) {{
                            body = {{"text": "John Smith works at Microsoft Corporation in Seattle. He collaborates with Sarah Johnson on AI projects.", "document_id": "test_doc"}};
                        }} else if (path.includes('analyze-entity')) {{
                            body = {{"entity_name": "Microsoft"}};
                        }}
                        
                        response = await fetch(path, {{
                            method: method,
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify(body)
                        }});
                    }} else {{
                        response = await fetch(path, {{ method: method }});
                    }}
                    
                    const data = await response.json();
                    
                    // Create result display
                    const resultWindow = window.open('', '_blank');
                    resultWindow.document.write(`
                        <html>
                        <head><title>${{method}} ${{path}} - Result</title></head>
                        <body style="font-family: monospace; padding: 20px; background: #f5f5f5;">
                            <h2>${{method}} ${{path}}</h2>
                            <pre style="background: #2d3748; color: #e2e8f0; padding: 20px; border-radius: 5px; overflow: auto;">
${{JSON.stringify(data, null, 2)}}
                            </pre>
                        </body>
                        </html>
                    `);
                }} catch (error) {{
                    alert('Error: ' + error.message);
                }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "km-mcp-graphrag",
        "timestamp": datetime.now().isoformat(),
        "openai_configured": bool(config.openai_api_key),
        "graph_stats": knowledge_graph.get_graph_stats()
    }

@app.post("/tools/extract-entities")
async def extract_entities(request: Request):
    """Extract entities and relationships from text"""
    try:
        data = await request.json()
        text = data.get("text", "")
        document_id = data.get("document_id", f"doc_{datetime.now().isoformat()}")

        if not text:
            raise HTTPException(status_code=400, detail="Text is required")

        # Extract entities and relationships
        entities, relationships = await extract_entities_and_relationships(text, document_id)

        # Add to knowledge graph
        for entity in entities:
            knowledge_graph.add_entity(entity)

        for relationship in relationships:
            knowledge_graph.add_relationship(relationship)

        return {
            "status": "success",
            "document_id": document_id,
            "entities_found": len(entities),
            "relationships_found": len(relationships),
            "entities": [asdict(e) for e in entities],
            "relationships": [asdict(r) for r in relationships]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/analyze-entity")
async def analyze_entity(request: Request):
    """Analyze a specific entity and its connections"""
    try:
        data = await request.json()
        entity_name = data.get("entity_name", "")

        if not entity_name:
            raise HTTPException(status_code=400, detail="Entity name is required")

        # Find the entity
        entity_key = None
        entity_info = None

        for key, entity in knowledge_graph.entities.items():
            if entity.name.lower() == entity_name.lower():
                entity_key = key
                entity_info = entity
                break

        if not entity_info:
            return {
                "status": "not_found",
                "entity_name": entity_name,
                "message": "Entity not found in knowledge graph"
            }

        # Get connections
        connections = knowledge_graph.get_entity_connections(entity_name)

        return {
            "status": "success",
            "entity": asdict(entity_info),
            "total_connections": len(connections),
            "connections": connections
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tools/graph-stats")
async def get_graph_stats():
    """Get knowledge graph statistics"""
    try:
        return knowledge_graph.get_graph_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/build-graph-from-documents")
async def build_graph_from_documents(request: Request):
    """Build knowledge graph from all documents in the document service"""
    try:
        # Get documents from the document service
        async with aiohttp.ClientSession() as session:
            # Call the document service to get all documents
            async with session.post(f"{config.km_docs_url}/tools/get-documents-for-search",
                                  json={"limit": 1000}) as response:
                if response.status != 200:
                    raise HTTPException(status_code=500, detail="Failed to fetch documents")

                docs_data = await response.json()
                # Handle both "status" and "success" response formats
                if docs_data.get("success") or docs_data.get("status") == "success":
                    documents = docs_data.get("documents", [])
                else:
                    documents = []

        if not documents:
            return {
                "status": "error",
                "message": "No documents available for graph construction",
                "documents_found": 0
            }

        processed_docs = 0
        total_entities = 0
        total_relationships = 0

        # Process each document
        for doc in documents:
            try:
                content = doc.get("content", "")
                doc_id = str(doc.get("id", "unknown"))

                if content and len(content.strip()) > 50:  # Only process substantial content
                    entities, relationships = await extract_entities_and_relationships(content, doc_id)

                    # Add to knowledge graph
                    for entity in entities:
                        knowledge_graph.add_entity(entity)
                        total_entities += 1

                    for relationship in relationships:
                        knowledge_graph.add_relationship(relationship)
                        total_relationships += 1

                    processed_docs += 1

                    # Add small delay to avoid API rate limits
                    await asyncio.sleep(0.1)

            except Exception as e:
                print(f"Error processing document {doc_id}: {e}")
                continue

        return {
            "status": "success",
            "documents_processed": processed_docs,
            "total_documents": len(documents),
            "entities_extracted": total_entities,
            "relationships_extracted": total_relationships,
            "graph_stats": knowledge_graph.get_graph_stats()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)