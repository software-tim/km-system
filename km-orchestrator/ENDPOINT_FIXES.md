# km-mcp-sql-docs Endpoint Corrections for Orchestrator

## WRONG → CORRECT Endpoint Mappings:

❌ /api/upload          → ✅ /tools/store-document  (POST)
❌ /stats               → ✅ /tools/database-stats  (GET)  
❌ /tools/stats         → ✅ /tools/database-stats  (GET)
❌ /api/search          → ✅ /tools/search-documents (POST)
❌ /tools/direct-search → ✅ /tools/search-documents (POST)

## Correct JSON Format for /tools/store-document:
{
    "title": "Document Title",
    "content": "Document content text",
    "file_type": "text",
    "metadata": {
        "source": "orchestrator",
        "created_by": "system"
    }
}

## Correct JSON Format for /tools/search-documents:
{
    "query": "search terms",
    "max_results": 10,
    "classification": "optional filter"
}
