#!/usr/bin/env python3
"""
Verify document 84 metadata storage
"""
import requests
import json

def check_via_sql_service(doc_id):
    """Check document directly via SQL service"""
    # First, let's search for all documents to find ours
    search_url = "https://km-mcp-sql-docs.azurewebsites.net/tools/search-documents"
    
    search_payload = {
        "query": "",  # Get all documents
        "limit": 100,
        "offset": 0
    }
    
    print(f"Searching for document {doc_id} in SQL service...")
    
    try:
        response = requests.post(search_url, json=search_payload)
        print(f"Search response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            documents = result.get('documents', [])
            
            # Find our document
            for doc in documents:
                if doc.get('id') == doc_id:
                    print(f"\n✅ Found document {doc_id}")
                    print(f"Title: {doc.get('title')}")
                    print(f"Classification: {doc.get('classification')}")
                    
                    # Check metadata
                    metadata = doc.get('metadata')
                    print(f"\nMetadata type: {type(metadata)}")
                    
                    if metadata:
                        if isinstance(metadata, str):
                            try:
                                metadata = json.loads(metadata)
                                print("Parsed metadata from string")
                            except:
                                print(f"Could not parse metadata: {metadata[:100]}...")
                        
                        if isinstance(metadata, dict):
                            print(f"Metadata keys: {list(metadata.keys())}")
                            
                            if 'ai_classification' in metadata:
                                print("\n✅ AI CLASSIFICATION FOUND!")
                                ai_class = metadata['ai_classification']
                                print(f"  Category: {ai_class.get('category')}")
                                print(f"  Summary: {ai_class.get('summary', '')[:200]}...")
                            else:
                                print("\n❌ No AI classification in metadata")
                                print(f"Available metadata: {json.dumps(metadata, indent=2)[:500]}")
                        else:
                            print(f"Metadata is not a dict: {metadata}")
                    else:
                        print("❌ No metadata found")
                    
                    return doc
            
            print(f"❌ Document {doc_id} not found in {len(documents)} documents")
            
            # Show last few documents
            print("\nLast 5 documents:")
            for doc in documents[-5:]:
                print(f"  ID: {doc.get('id')}, Title: {doc.get('title', 'No title')[:50]}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

# Check document 84
check_via_sql_service(84)

# Also check if our test metadata update worked
print("\n\nChecking document 83 (our test update)...")
check_via_sql_service(83)