#!/usr/bin/env python3
"""
Check actual content length in database
"""
import requests
import json

def check_content_length():
    """Check the actual content stored in database"""
    search_url = "https://km-mcp-sql-docs.azurewebsites.net/tools/search-documents"
    
    search_payload = {
        "query": None,
        "limit": 100,
        "offset": 0
    }
    
    print("Fetching document 91 from SQL service...\n")
    
    try:
        response = requests.post(search_url, json=search_payload)
        if response.status_code == 200:
            result = response.json()
            documents = result.get('documents', [])
            
            # Find document 91
            for doc in documents:
                if doc.get('id') == 91:
                    content = doc.get('content', '')
                    print(f"✅ Found document 91")
                    print(f"   Title: {doc.get('title')}")
                    print(f"   Content length: {len(content)} characters")
                    print(f"   Content preview (first 200 chars): {content[:200]}...")
                    print(f"   Content preview (last 200 chars): ...{content[-200:]}")
                    
                    # Check metadata
                    metadata = doc.get('metadata')
                    if metadata and isinstance(metadata, str):
                        metadata = json.loads(metadata)
                    
                    if metadata and 'processing_summary' in metadata:
                        ps = metadata['processing_summary']
                        print(f"\n📊 Processing Summary from metadata:")
                        print(f"   Chunks created: {ps.get('chunks_created')}")
                        
                    return
                    
            print("❌ Document 91 not found")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

check_content_length()