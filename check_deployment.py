#!/usr/bin/env python3
"""
Check deployment status of services
"""
import requests

services = {
    "orchestrator": "https://km-orchestrator.azurewebsites.net/health",
    "sql-docs": "https://km-mcp-sql-docs.azurewebsites.net/health",
    "llm": "https://km-mcp-llm.azurewebsites.net/health",
    "graphrag": "https://km-mcp-graphrag.azurewebsites.net/health"
}

for name, url in services.items():
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            version = data.get('version', 'no version')
            timestamp = data.get('timestamp', 'no timestamp')
            print(f"✅ {name}: {version} - {timestamp}")
        else:
            print(f"❌ {name}: Status {response.status_code}")
    except Exception as e:
        print(f"❌ {name}: {str(e)}")