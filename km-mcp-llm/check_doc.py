#!/usr/bin/env python3
import requests
import json

# Check document 78 via search
search_url = "https://km-mcp-sql-docs.azurewebsites.net/tools/search-documents"
search_payload = {"query": None, "limit": 100, "offset": 0}

response = requests.post(search_url, json=search_payload)
if response.status_code == 200:
    data = response.json()
    documents = data.get("documents", [])
    
    # Find document 78
    for doc in documents:
        if str(doc.get("id")) == "80":
            print(f"Found document 78!")
            print(f"Title: {doc.get('title')}")
            print(f"Metadata type: {type(doc.get('metadata'))}")
            print(f"Metadata keys: {list(doc.get('metadata', {}).keys()) if isinstance(doc.get('metadata'), dict) else 'Not a dict'}")
            
            metadata = doc.get('metadata', {})
            if isinstance(metadata, dict):
                # Check for ai_classification
                if 'ai_classification' in metadata:
                    print("\nFound ai_classification!")
                    print(f"AI Classification: {json.dumps(metadata['ai_classification'], indent=2)}")
                else:
                    print("\nNo ai_classification in metadata")
                    print(f"Full metadata: {json.dumps(metadata, indent=2)}")
            break
    else:
        print("Document 78 not found")
else:
    print(f"Search failed: {response.status_code}")