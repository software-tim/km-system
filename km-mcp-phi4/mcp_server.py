#!/usr/bin/env python3
"""
MCP Server for KM-MCP-SQL-DOCS
Implements Model Context Protocol alongside existing REST API
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from datetime import datetime

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.websocket import websocket_server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource,
    CallToolRequest, CallToolResult, ListResourcesRequest, ListResourcesResult,
    ListToolsRequest, ListToolsResult, ReadResourceRequest, ReadResourceResult
)

# Import existing operations
from km_docs_config import Settings
from km_docs_operations import DocumentOperations
from km_docs_schemas import DocumentCreate, SearchRequest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize operations (same as REST API)
settings = Settings()
ops = DocumentOperations()

class MCPDocumentServer:
    """MCP Server for Document Management Operations"""
    
    def __init__(self):
        self.server = Server("km-mcp-sql-docs")
        self._setup_tools()
        self._setup_resources()
        
    def _setup_tools(self):
        """Define MCP tools that mirror REST API functionality"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available MCP tools"""
            return [
                Tool(
                    name="store_document",
                    description="Store a new document in the knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Document title"
                            },
                            "content": {
                                "type": "string", 
                                "description": "Document content"
                            },
                            "classification": {
                                "type": "string",
                                "description": "Document classification (optional)"
                            },
                            "entities": {
                                "type": "string",
                                "description": "Named entities (optional)"
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata (optional)"
                            }
                        },
                        "required": ["title", "content"]
                    }
                ),
                Tool(
                    name="search_documents", 
                    description="Search documents in the knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "classification": {
                                "type": "string", 
                                "description": "Filter by classification (optional)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 10
                            },
                            "offset": {
                                "type": "integer", 
                                "description": "Results offset",
                                "default": 0
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_document",
                    description="Retrieve a specific document by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "document_id": {
                                "type": "integer",
                                "description": "Document ID to retrieve"
                            }
                        },
                        "required": ["document_id"]
                    }
                ),
                Tool(
                    name="database_stats",
                    description="Get database statistics and metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="get_documents_for_search",
                    description="Get all documents for search indexing and graph construction",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of documents",
                                "default": 1000
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="delete_document",
                    description="Delete a document by ID", 
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "document_id": {
                                "type": "integer",
                                "description": "Document ID to delete"
                            }
                        },
                        "required": ["document_id"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent | EmbeddedResource]:
            """Handle MCP tool calls"""
            try:
                if name == "store_document":
                    return await self._store_document(arguments)
                elif name == "search_documents":
                    return await self._search_documents(arguments)
                elif name == "get_document":
                    return await self._get_document(arguments)
                elif name == "database_stats":
                    return await self._database_stats(arguments)
                elif name == "get_documents_for_search":
                    return await self._get_documents_for_search(arguments)
                elif name == "delete_document":
                    return await self._delete_document(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")
                    
            except Exception as e:
                logger.error(f"Tool {name} failed: {str(e)}")
                return [TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )]

    def _setup_resources(self):
        """Define MCP resources (document access)"""
        
        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            """List available document resources"""
            try:
                # Get recent documents as resources
                stats = await ops.get_database_stats()
                return [
                    Resource(
                        uri=f"document://recent",
                        name="Recent Documents",
                        description=f"Access to {stats.get('total_documents', 0)} documents in the knowledge base",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri=f"document://stats", 
                        name="Database Statistics",
                        description="Knowledge base statistics and metrics",
                        mimeType="application/json"
                    )
                ]
            except Exception as e:
                logger.error(f"Failed to list resources: {e}")
                return []

        @self.server.read_resource() 
        async def read_resource(uri: str) -> str:
            """Read resource content"""
            try:
                if uri == "document://recent":
                    # Return recent documents
                    search_result = await ops.search_documents(SearchRequest(query="", limit=10))
                    return json.dumps(search_result, default=str, indent=2)
                elif uri == "document://stats":
                    # Return database stats
                    stats = await ops.get_database_stats()
                    return json.dumps(stats, default=str, indent=2)
                else:
                    raise ValueError(f"Unknown resource: {uri}")
            except Exception as e:
                logger.error(f"Failed to read resource {uri}: {e}")
                return json.dumps({"error": str(e)})

    # Tool implementation methods (using existing operations)
    async def _store_document(self, args: dict) -> list[TextContent]:
        """Store document via MCP"""
        try:
            # Create document using existing operations
            doc_create = DocumentCreate(
                title=args["title"],
                content=args["content"],
                classification=args.get("classification"),
                entities=args.get("entities"),
                metadata=args.get("metadata")
            )
            
            result = await ops.store_document(doc_create)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "document_id": result["document_id"],
                    "message": "Document stored successfully via MCP",
                    "timestamp": datetime.utcnow().isoformat()
                }, indent=2)
            )]
        except Exception as e:
            raise Exception(f"Failed to store document: {str(e)}")

    async def _search_documents(self, args: dict) -> list[TextContent]:
        """Search documents via MCP"""
        try:
            search_req = SearchRequest(
                query=args["query"],
                classification=args.get("classification"),
                limit=args.get("limit", 10),
                offset=args.get("offset", 0)
            )
            
            result = await ops.search_documents(search_req)
            
            return [TextContent(
                type="text", 
                text=json.dumps({
                    "success": True,
                    "documents": result["documents"],
                    "total": result["total"],
                    "query": args["query"],
                    "source": "mcp"
                }, default=str, indent=2)
            )]
        except Exception as e:
            raise Exception(f"Search failed: {str(e)}")

    async def _get_document(self, args: dict) -> list[TextContent]:
        """Get specific document via MCP"""
        try:
            doc_id = args["document_id"]
            result = await ops.get_document(doc_id)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "document": result,
                    "source": "mcp"
                }, default=str, indent=2)
            )]
        except Exception as e:
            raise Exception(f"Failed to get document: {str(e)}")

    async def _database_stats(self, args: dict) -> list[TextContent]:
        """Get database statistics via MCP"""
        try:
            stats = await ops.get_database_stats()
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "stats": stats,
                    "timestamp": datetime.utcnow().isoformat(),
                    "source": "mcp"
                }, default=str, indent=2)
            )]
        except Exception as e:
            raise Exception(f"Failed to get stats: {str(e)}")

    async def _get_documents_for_search(self, args: dict) -> list[TextContent]:
        """Get documents for search indexing via MCP"""
        try:
            limit = args.get("limit", 1000)
            result = await ops.get_documents_for_search(limit)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "documents": result["documents"],
                    "total": result["total"],
                    "source": "mcp"
                }, default=str, indent=2)
            )]
        except Exception as e:
            raise Exception(f"Failed to get documents for search: {str(e)}")

    async def _delete_document(self, args: dict) -> list[TextContent]:
        """Delete document via MCP"""
        try:
            doc_id = args["document_id"]
            result = await ops.delete_document(doc_id)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "message": f"Document {doc_id} deleted successfully",
                    "source": "mcp"
                }, indent=2)
            )]
        except Exception as e:
            raise Exception(f"Failed to delete document: {str(e)}")

    async def run_stdio(self):
        """Run MCP server with stdio transport"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())

    async def run_websocket(self, host: str = "localhost", port: int = 8001):
        """Run MCP server with WebSocket transport"""
        async with websocket_server(host=host, port=port) as server:
            await self.server.run_websocket(server)

# Main execution
async def main():
    """Main entry point for MCP server"""
    mcp_server = MCPDocumentServer()
    
    # For now, run stdio mode (can be extended to support WebSocket)
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "websocket":
        logger.info("Starting MCP server with WebSocket transport on ws://localhost:8001")
        await mcp_server.run_websocket()
    else:
        logger.info("Starting MCP server with stdio transport")
        await mcp_server.run_stdio()

if __name__ == "__main__":
    asyncio.run(main())