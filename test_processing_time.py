#!/usr/bin/env python3
"""
Test processing time retrieval for document 93
"""
import requests
import json

def test_processing_time():
    """Check what processing time is stored"""
    
    # First get the document from SQL to see metadata
    search_url = "https://km-mcp-sql-docs.azurewebsites.net/tools/search-documents"
    search_payload = {"query": None, "limit": 100, "offset": 0}
    
    print("1. Checking document 93 metadata...\n")
    
    try:
        response = requests.post(search_url, json=search_payload)
        if response.status_code == 200:
            result = response.json()
            documents = result.get('documents', [])
            
            for doc in documents:
                if doc.get('id') == 93:
                    print(f"✅ Found document 93: {doc.get('title')}")
                    print(f"   File name: {doc.get('file_name')}")
                    print(f"   File size: {doc.get('file_size')}")
                    
                    metadata = doc.get('metadata')
                    if metadata and isinstance(metadata, str):
                        metadata = json.loads(metadata)
                        
                    if metadata:
                        # Check for processing summary
                        if 'processing_summary' in metadata:
                            ps = metadata['processing_summary']
                            print(f"\n📊 Processing Summary:")
                            print(f"   Total time: {ps.get('total_time_seconds')} seconds")
                            print(f"   Chunks created: {ps.get('chunks_created')}")
                            print(f"   Entities extracted: {ps.get('entities_extracted')}")
                        else:
                            print("\n❌ No processing_summary in metadata")
                            
                        # Check for file info
                        if 'file_info' in metadata:
                            fi = metadata['file_info']
                            print(f"\n📁 File Info in metadata:")
                            print(f"   Name: {fi.get('name')}")
                            print(f"   Size: {fi.get('size')}")
                            print(f"   Type: {fi.get('type')}")
                            
                    # Now test the results endpoint
                    print(f"\n2. Testing results endpoint...")
                    results_url = f"https://km-orchestrator.azurewebsites.net/api/document/93/results"
                    
                    results_response = requests.get(results_url, timeout=30)
                    if results_response.status_code == 200:
                        data = results_response.json()
                        doc_meta = data.get('document_metadata', {})
                        proc_summary = data.get('processing_summary', {})
                        
                        print(f"\n✅ Results endpoint data:")
                        print(f"   Processing time: {proc_summary.get('processing_time')} seconds")
                        print(f"   File name: {doc_meta.get('file_name')}")
                        print(f"   File size: {doc_meta.get('file_size')} bytes")
                        print(f"   Processing time in metadata: {doc_meta.get('processing_time_seconds')}")
                    else:
                        print(f"\n❌ Results endpoint error: {results_response.status_code}")
                        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

test_processing_time()