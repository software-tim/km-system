#!/usr/bin/env python3
"""
Test metadata update directly
"""
import requests
import json

# Test data
test_metadata = {
    "document_id": 83,
    "metadata": {
        "test_field": "test_value",
        "timestamp": "2024-08-24T12:00:00",
        "ai_classification": {
            "category": "test_category",
            "summary": "This is a test summary",
            "domains": ["test_domain"],
            "themes": ["test_theme"]
        }
    }
}

# Call the update endpoint directly
url = "https://km-mcp-sql-docs.azurewebsites.net/tools/update-document-metadata"

print(f"Testing metadata update for document 83...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(test_metadata, indent=2)}")

try:
    response = requests.post(url, json=test_metadata)
    print(f"\nResponse status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    print(f"Response body: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nParsed response: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Also check the health endpoint to see version
print("\n\nChecking health endpoint...")
health_response = requests.get("https://km-mcp-sql-docs.azurewebsites.net/health")
if health_response.status_code == 200:
    health = health_response.json()
    print(f"Health check: {json.dumps(health, indent=2)}")