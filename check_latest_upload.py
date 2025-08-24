#!/usr/bin/env python3
"""
Check the latest uploaded document and why results page can't find it
"""
import requests
import json

def check_latest_upload():
    """Find the most recently uploaded document"""
    
    print("=== Checking Latest Upload ===\n")
    
    # Get all documents
    search_url = "https://km-mcp-sql-docs.azurewebsites.net/tools/search-documents"
    search_payload = {"query": None, "limit": 100, "offset": 0}
    
    try:
        response = requests.post(search_url, json=search_payload)
        if response.status_code == 200:
            result = response.json()
            documents = result.get('documents', [])
            
            # Sort by ID (assuming higher ID = newer)
            documents.sort(key=lambda x: x.get('id', 0), reverse=True)
            
            if documents:
                latest = documents[0]
                doc_id = latest.get('id')
                
                print(f"✅ Latest document ID: {doc_id}")
                print(f"   Title: {latest.get('title')}")
                print(f"   Content length: {len(latest.get('content', ''))} chars")
                print(f"   File name: {latest.get('file_name')}")
                print(f"   File size: {latest.get('file_size')}")
                
                # Check if metadata has GraphRAG data
                metadata = latest.get('metadata')
                if metadata and isinstance(metadata, str):
                    metadata = json.loads(metadata)
                    
                if metadata:
                    print(f"\n   Metadata keys: {list(metadata.keys())[:10]}")
                    if 'ai_classification' in metadata:
                        print("   ✅ Has AI classification")
                    if 'entities' in metadata:
                        print(f"   ✅ Has {len(metadata['entities'])} entities")
                    if 'top_chunks' in metadata:
                        print(f"   ✅ Has {len(metadata['top_chunks'])} chunks stored")
                        
                # Now test the results endpoint
                print(f"\n2. Testing results endpoint for document {doc_id}...")
                
                results_url = f"https://km-orchestrator.azurewebsites.net/api/document/{doc_id}/results"
                
                results_response = requests.get(results_url, timeout=30)
                print(f"   Results endpoint status: {results_response.status_code}")
                
                if results_response.status_code == 200:
                    print("   ✅ Results endpoint working")
                    data = results_response.json()
                    print(f"   Document title in results: {data.get('document_title')}")
                    print(f"   Chunks returned: {len(data.get('chunks', []))}")
                    print(f"   Entities returned: {len(data.get('entities', []))}")
                else:
                    print(f"   ❌ Results endpoint error: {results_response.text[:200]}")
                    
                # Check with string ID
                print(f"\n3. Testing with string ID...")
                results_url_str = f"https://km-orchestrator.azurewebsites.net/api/document/{str(doc_id)}/results"
                results_response2 = requests.get(results_url_str, timeout=30)
                print(f"   String ID status: {results_response2.status_code}")
                
                return doc_id
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

check_latest_upload()