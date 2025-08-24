#!/usr/bin/env python3
"""
Check the structure of stored chunks
"""
import requests
import json

def check_chunk_structure():
    """Check how chunks are stored in metadata"""
    
    # Get document 92
    search_url = "https://km-mcp-sql-docs.azurewebsites.net/tools/search-documents"
    search_payload = {"query": None, "limit": 100, "offset": 0}
    
    try:
        response = requests.post(search_url, json=search_payload)
        if response.status_code == 200:
            result = response.json()
            documents = result.get('documents', [])
            
            # Find document 92
            for doc in documents:
                if doc.get('id') == 92:
                    print(f"✅ Found document 92")
                    
                    metadata = doc.get('metadata')
                    if metadata and isinstance(metadata, str):
                        metadata = json.loads(metadata)
                        
                    if metadata and 'top_chunks' in metadata:
                        chunks = metadata['top_chunks']
                        print(f"\n📊 Stored chunks: {len(chunks)} chunks")
                        
                        # Check first chunk structure
                        if chunks:
                            first_chunk = chunks[0]
                            print(f"\nFirst chunk structure:")
                            print(f"  Keys: {list(first_chunk.keys())}")
                            
                            # Check for different possible key names
                            content_key = None
                            for key in ['content', 'text', 'chunk_content']:
                                if key in first_chunk:
                                    content_key = key
                                    break
                                    
                            if content_key:
                                print(f"  Content key: '{content_key}'")
                                print(f"  Content length: {len(first_chunk[content_key])}")
                                print(f"  Content preview: {first_chunk[content_key][:100]}...")
                            
                            # Check for ID field
                            id_key = None
                            for key in ['id', 'chunk_id', 'index']:
                                if key in first_chunk:
                                    id_key = key
                                    print(f"  ID key: '{id_key}' = {first_chunk[id_key]}")
                                    break
                                    
                            # Show full first chunk
                            print(f"\nFull first chunk:")
                            print(json.dumps(first_chunk, indent=2)[:500])
                            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

check_chunk_structure()