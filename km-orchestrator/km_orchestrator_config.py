"""
Configuration management for KM Orchestrator
"""
import os
from typing import Dict, List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    app_name: str = "KM Orchestrator"
    version: str = "1.0.0"
    debug: bool = False
    
    # Database settings (inherited from existing setup)
    km_sql_server: str = os.getenv("KM_SQL_SERVER", "knowledge-sql.database.windows.net")
    km_sql_database: str = os.getenv("KM_SQL_DATABASE", "knowledge-base")
    km_sql_username: str = os.getenv("KM_SQL_USERNAME", "mcpadmin")
    km_sql_password: str = os.getenv("KM_SQL_PASSWORD", "Theodore03$")
    
    # MCP Services Configuration
    mcp_services: Dict[str, str] = {
        "km-mcp-sql": "https://km-mcp-sql.azurewebsites.net",
        "km-mcp-sql-docs": "https://km-mcp-sql-docs.azurewebsites.net", 
        "km-mcp-llm": "https://km-mcp-llm.azurewebsites.net",
        "km-mcp-search": "https://km-mcp-search.azurewebsites.net",
        "km-mcp-graphrag": "https://km-mcp-graphrag.azurewebsites.net"
    }
    
    # Service timeout settings
    service_timeout: int = 30
    health_check_timeout: int = 10
    
    # Orchestrator settings
    max_concurrent_requests: int = 10
    request_retry_attempts: int = 3
    
    # Workflow settings
    workflow_timeout: int = 300  # 5 minutes for complex workflows
    
    # Caching settings
    cache_ttl: int = 300  # 5 minutes
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Service health check endpoints
HEALTH_ENDPOINTS = {
    service_name: f"{url}/health"
    for service_name, url in settings.mcp_services.items()
}

# Service capabilities mapping
SERVICE_CAPABILITIES = {
    "km-mcp-sql": {
        "description": "Core SQL database operations",
        "endpoints": ["/health", "/tools/execute-query", "/tools/get-schema"],
        "capabilities": ["database_query", "schema_inspection"]
    },
    "km-mcp-sql-docs": {
        "description": "Document storage and text search",
        "endpoints": ["/health", "/tools/store-document", "/tools/search-documents", "/tools/database-stats"],
        "capabilities": ["document_storage", "text_search", "document_management"]
    },
    "km-mcp-llm": {
        "description": "AI reasoning and document analysis",
        "endpoints": ["/health", "/tools/analyze-document", "/tools/summarize-content", "/tools/answer-question"],
        "capabilities": ["document_analysis", "ai_reasoning", "qa_system"]
    },
    "km-mcp-search": {
        "description": "Semantic and vector-based search",
        "endpoints": ["/health", "/tools/semantic-search", "/tools/vector-search", "/tools/hybrid-search"],
        "capabilities": ["semantic_search", "vector_search", "similarity_matching"]
    },
    "km-mcp-graphrag": {
        "description": "Knowledge graph and graph-based reasoning",
        "endpoints": ["/health", "/tools/extract-entities", "/tools/build-graph", "/tools/graph-query"],
        "capabilities": ["entity_extraction", "knowledge_graph", "graph_reasoning"]
    }
}

# Workflow definitions
WORKFLOW_DEFINITIONS = {
    "document_processing": {
        "description": "Complete document processing pipeline",
        "steps": [
            {"service": "km-mcp-sql-docs", "action": "store-document"},
            {"service": "km-mcp-llm", "action": "analyze-document"},
            {"service": "km-mcp-graphrag", "action": "extract-entities"},
            {"service": "km-mcp-search", "action": "index-document"}
        ]
    },
    "intelligent_search": {
        "description": "Multi-service search with AI ranking",
        "steps": [
            {"service": "km-mcp-sql-docs", "action": "search-documents", "parallel": True},
            {"service": "km-mcp-search", "action": "semantic-search", "parallel": True},
            {"service": "km-mcp-llm", "action": "rank-results"}
        ]
    },
    "comprehensive_analysis": {
        "description": "Deep document analysis using all AI services",
        "steps": [
            {"service": "km-mcp-llm", "action": "analyze-document", "parallel": True},
            {"service": "km-mcp-graphrag", "action": "extract-entities", "parallel": True},
            {"service": "km-mcp-llm", "action": "synthesize-insights"}
        ]
    }
}

# Routing rules for intelligent request routing
ROUTING_RULES = {
    "document_storage": ["km-mcp-sql-docs"],
    "text_search": ["km-mcp-sql-docs", "km-mcp-search"],
    "semantic_search": ["km-mcp-search"],
    "ai_analysis": ["km-mcp-llm"],
    "entity_extraction": ["km-mcp-graphrag"],
    "qa_system": ["km-mcp-llm", "km-mcp-sql-docs"],
    "graph_reasoning": ["km-mcp-graphrag"],
    "document_insights": ["km-mcp-llm", "km-mcp-graphrag"]
}

# Error handling configuration
ERROR_HANDLING = {
    "retry_on_status_codes": [500, 502, 503, 504],
    "fallback_services": {
        "km-mcp-search": ["km-mcp-sql-docs"],  # Fallback to text search if semantic search fails
        "km-mcp-llm": ["km-mcp-sql-docs"],     # Fallback to basic document retrieval
    }
}