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
            relationship_types[rel.relationship_type] += 1
        
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
    """Web interface for GraphRAG service"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>KM MCP GraphRAG Service</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
            .section {{ margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #3498db; }}
            .endpoint {{ background: #e8f5e9; padding: 15px; margin: 10px 0; border-radius: 5px; border: 1px solid #4caf50; }}
            .method {{ color: #2e7d32; font-weight: bold; }}
            .path {{ color: #1565c0; font-family: monospace; }}
            .expandable {{ cursor: pointer; border: 1px solid #ddd; margin: 10px 0; }}
            .expandable summary {{ background: #f1f1f1; padding: 15px; font-weight: bold; }}
            .expandable[open] summary {{ background: #e3f2fd; }}
            .content {{ padding: 15px; }}
            .json {{ background: #2d3748; color: #e2e8f0; padding: 15px; border-radius: 5px; font-family: monospace; white-space: pre-wrap; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
            .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
            .stat-number {{ font-size: 2em; font-weight: bold; }}
            .stat-label {{ opacity: 0.9; }}
            button {{ background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; margin: 5px; }}
            button:hover {{ background: #2980b9; }}
            .error {{ color: #e74c3c; }}
            .success {{ color: #27ae60; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🕸️ KM MCP GraphRAG Service</h1>
            
            <div class="section">
                <h2>📊 Service Status</h2>
                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-number" id="entities-count">-</div>
                        <div class="stat-label">Entities</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="relationships-count">-</div>
                        <div class="stat-label">Relationships</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="documents-count">-</div>
                        <div class="stat-label">Documents Analyzed</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number" id="openai-status">-</div>
                        <div class="stat-label">OpenAI Status</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🔧 Available Endpoints</h2>
                
                <details class="expandable">
                    <summary>POST /tools/extract-entities - Extract entities from text</summary>
                    <div class="content">
                        <p>Extracts entities and relationships from provided text using AI analysis.</p>
                        <div class="json">{{
    "text": "Your document text here",
    "document_id": "optional_document_id"
}}</div>
                        <button onclick="testExtractEntities()">Test Extract Entities</button>
                        <div id="extract-result"></div>
                    </div>
                </details>

                <details class="expandable">
                    <summary>POST /tools/analyze-entity - Analyze specific entity</summary>
                    <div class="content">
                        <p>Get detailed analysis and connections for a specific entity.</p>
                        <div class="json">{{
    "entity_name": "Entity to analyze"
}}</div>
                        <button onclick="testAnalyzeEntity()">Test Analyze Entity</button>
                        <div id="analyze-result"></div>
                    </div>
                </details>

                <details class="expandable">
                    <summary>GET /tools/graph-stats - Get knowledge graph statistics</summary>
                    <div class="content">
                        <p>Returns comprehensive statistics about the knowledge graph.</p>
                        <button onclick="loadStats()">Load Statistics</button>
                        <div id="stats-result"></div>
                    </div>
                </details>

                <details class="expandable">
                    <summary>POST /tools/build-graph-from-documents - Build graph from all documents</summary>
                    <div class="content">
                        <p>Processes all documents from the document service to build the knowledge graph.</p>
                        <button onclick="buildGraph()">Build Knowledge Graph</button>
                        <div id="build-result"></div>
                    </div>
                </details>
            </div>
        </div>

        <script>
            async function loadStats() {{
                try {{
                    const response = await fetch('/tools/graph-stats');
                    const data = await response.json();
                    
                    document.getElementById('entities-count').textContent = data.total_entities;
                    document.getElementById('relationships-count').textContent = data.total_relationships;
                    document.getElementById('stats-result').innerHTML = '<div class="success">Statistics loaded successfully!</div><pre class="json">' + JSON.stringify(data, null, 2) + '</pre>';
                }} catch (error) {{
                    document.getElementById('stats-result').innerHTML = '<div class="error">Error loading stats: ' + error.message + '</div>';
                }}
            }}

            async function testExtractEntities() {{
                const testText = "John Smith works at Microsoft Corporation in Seattle. He collaborates with Sarah Johnson on AI projects.";
                try {{
                    const response = await fetch('/tools/extract-entities', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{text: testText, document_id: "test_doc"}})
                    }});
                    const data = await response.json();
                    document.getElementById('extract-result').innerHTML = '<div class="success">Entities extracted successfully!</div><pre class="json">' + JSON.stringify(data, null, 2) + '</pre>';
                }} catch (error) {{
                    document.getElementById('extract-result').innerHTML = '<div class="error">Error: ' + error.message + '</div>';
                }}
            }}

            async function testAnalyzeEntity() {{
                try {{
                    const response = await fetch('/tools/analyze-entity', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{entity_name: "Microsoft"}})
                    }});
                    const data = await response.json();
                    document.getElementById('analyze-result').innerHTML = '<div class="success">Entity analyzed successfully!</div><pre class="json">' + JSON.stringify(data, null, 2) + '</pre>';
                }} catch (error) {{
                    document.getElementById('analyze-result').innerHTML = '<div class="error">Error: ' + error.message + '</div>';
                }}
            }}

            async function buildGraph() {{
                document.getElementById('build-result').innerHTML = '<div>Building knowledge graph... This may take a few minutes.</div>';
                try {{
                    const response = await fetch('/tools/build-graph-from-documents', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{}})
                    }});
                    const data = await response.json();
                    document.getElementById('build-result').innerHTML = '<div class="success">Knowledge graph built successfully!</div><pre class="json">' + JSON.stringify(data, null, 2) + '</pre>';
                    loadStats(); // Refresh stats
                }} catch (error) {{
                    document.getElementById('build-result').innerHTML = '<div class="error">Error building graph: ' + error.message + '</div>';
                }}
            }}

            // Load initial stats
            loadStats();
            
            // Check OpenAI status
            document.getElementById('openai-status').textContent = {'✅' if config.openai_api_key else '❌'};
        </script>
    </body>
    </html>
    """

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