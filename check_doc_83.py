#!/usr/bin/env python3
"""
Check document 83 to see what metadata is stored
"""
import requests
import json

def check_document(doc_id):
    """Check a document's metadata via the API"""
    try:
        # Get document via search API
        search_url = "https://km-orchestrator.azurewebsites.net/api/documents/search"
        search_payload = {
            "query": f"id:{doc_id}",
            "limit": 10
        }
        
        print(f"Checking document {doc_id}...")
        
        # Try search endpoint
        response = requests.post(search_url, json=search_payload)
        if response.status_code == 200:
            results = response.json()
            docs = results.get('documents', [])
            
            # Find our document
            for doc in docs:
                if doc.get('id') == doc_id:
                    print(f"\n✅ Found document {doc_id}")
                    print(f"Title: {doc.get('title')}")
                    print(f"Classification: {doc.get('classification')}")
                    
                    # Check metadata
                    metadata = doc.get('metadata', {})
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                        except:
                            pass
                    
                    print(f"\nMetadata type: {type(metadata)}")
                    print(f"Metadata keys: {list(metadata.keys()) if isinstance(metadata, dict) else 'Not a dict'}")
                    
                    if isinstance(metadata, dict):
                        # Check for AI classification
                        if 'ai_classification' in metadata:
                            print("\n✅ AI Classification found in metadata!")
                            ai_class = metadata['ai_classification']
                            print(f"  Category: {ai_class.get('category')}")
                            print(f"  Domains: {ai_class.get('domains')}")
                            print(f"  Themes: {ai_class.get('themes')}")
                            print(f"  Summary preview: {ai_class.get('summary', '')[:100]}...")
                        else:
                            print("\n❌ No AI classification in metadata")
                            print(f"Available metadata: {json.dumps(metadata, indent=2)}")
                    else:
                        print(f"\nMetadata content: {metadata}")
                    
                    return doc
        
        # Try direct document endpoint
        direct_url = f"https://km-orchestrator.azurewebsites.net/api/documents/{doc_id}"
        response = requests.get(direct_url)
        
        if response.status_code == 200:
            doc = response.json()
            print(f"\n✅ Found document {doc_id} (direct)")
            print(f"Response keys: {list(doc.keys())}")
            print(f"Full response: {json.dumps(doc, indent=2)}")
            return doc
        else:
            print(f"\n❌ Could not find document {doc_id}")
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

# Check document 83
check_document(83)

# Also check what stats show
print("\n\n📊 Checking system stats...")
stats_response = requests.get("https://km-orchestrator.azurewebsites.net/api/stats")
if stats_response.status_code == 200:
    stats = stats_response.json()
    print(f"Total documents: {stats.get('documents', {}).get('total_documents', 0)}")
    print(f"Classification breakdown: {stats.get('classification_breakdown', [])}")