#!/usr/bin/env python3
"""
Debug why only 1 chunk shows for document 91
"""
import requests
import json

def debug_chunks():
    """Check what the results API returns for chunks"""
    url = "https://km-orchestrator.azurewebsites.net/api/document/91/results"
    
    print("Fetching results for document 91...\n")
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            
            # Check chunks array
            chunks = data.get('chunks', [])
            print(f"✅ Number of chunks returned by API: {len(chunks)}")
            
            # Show each chunk
            for i, chunk in enumerate(chunks):
                print(f"\nChunk {i+1}:")
                print(f"  ID: {chunk.get('id')}")
                print(f"  Metadata: {chunk.get('metadata')}")
                print(f"  Start position: {chunk.get('start_position')}")
                print(f"  Length: {chunk.get('length')}")
                print(f"  Content (first 80 chars): {chunk.get('content', '')[:80]}...")
                
            # Check processing summary
            proc_summary = data.get('processing_summary', {})
            print(f"\n📊 Processing Summary:")
            print(f"  chunks_count: {proc_summary.get('chunks_count')}")
            
            # Check document metadata
            doc_metadata = data.get('document_metadata', {})
            print(f"\n📋 Document Metadata:")
            print(f"  {json.dumps(doc_metadata, indent=2)}")
            
            # Save full response for analysis
            with open('doc91_results.json', 'w') as f:
                json.dump(data, f, indent=2)
            print("\n💾 Full response saved to doc91_results.json")
            
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

debug_chunks()