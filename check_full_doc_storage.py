#!/usr/bin/env python3
"""
Check if full document is stored anywhere (file_data column?)
"""
import requests
import json
import base64

def check_full_document_storage():
    """Check all document fields including file_data"""
    
    # First, let's check the database schema
    print("Checking what fields are available in the documents table...\n")
    
    # Get a document to see all fields
    search_url = "https://km-mcp-sql-docs.azurewebsites.net/tools/search-documents"
    
    search_payload = {
        "query": None,
        "limit": 1,
        "offset": 0
    }
    
    try:
        response = requests.post(search_url, json=search_payload)
        if response.status_code == 200:
            result = response.json()
            documents = result.get('documents', [])
            
            if documents:
                doc = documents[0]
                print("Available fields in documents table:")
                for key in doc.keys():
                    value = doc[key]
                    if key == 'content':
                        print(f"  - {key}: {len(str(value))} chars")
                    elif key == 'file_data' and value:
                        # Check if it's base64 encoded file
                        try:
                            if isinstance(value, str) and len(value) > 100:
                                # Try to decode to check size
                                decoded = base64.b64decode(value)
                                print(f"  - {key}: {len(decoded)} bytes (base64 encoded)")
                            else:
                                print(f"  - {key}: {type(value)}")
                        except:
                            print(f"  - {key}: Present but not base64")
                    elif key == 'metadata' and value:
                        print(f"  - {key}: {len(str(value))} chars")
                    else:
                        print(f"  - {key}: {type(value).__name__}")
                        
        # Now specifically check document 91
        print("\n\nChecking document 91 specifically...")
        
        search_payload = {
            "query": None,
            "limit": 100,
            "offset": 0
        }
        
        response = requests.post(search_url, json=search_payload)
        if response.status_code == 200:
            result = response.json()
            documents = result.get('documents', [])
            
            for doc in documents:
                if doc.get('id') == 91:
                    print(f"\n✅ Found document 91: {doc.get('title')}")
                    
                    # Check content field
                    content = doc.get('content', '')
                    print(f"\n📄 Content field: {len(content)} characters")
                    
                    # Check file_data field
                    file_data = doc.get('file_data')
                    if file_data:
                        try:
                            if isinstance(file_data, str):
                                decoded = base64.b64decode(file_data)
                                print(f"\n📦 File_data field: {len(decoded)} bytes")
                                print(f"   Decoded preview: {decoded[:200].decode('utf-8', errors='ignore')}...")
                                
                                # Save to file to check
                                with open('doc91_file_data.txt', 'wb') as f:
                                    f.write(decoded)
                                print(f"   Saved decoded content to doc91_file_data.txt")
                        except Exception as e:
                            print(f"\n📦 File_data field: Present but error decoding: {e}")
                    else:
                        print(f"\n📦 File_data field: Not present or empty")
                        
                    # Check metadata for any full content
                    metadata = doc.get('metadata')
                    if metadata:
                        if isinstance(metadata, str):
                            metadata = json.loads(metadata)
                        
                        # Check if chunks are stored in metadata
                        if 'chunks' in metadata:
                            print(f"\n🧩 Chunks in metadata: {len(metadata['chunks'])} chunks")
                        else:
                            print(f"\n🧩 No chunks stored in metadata")
                            
                    # Check file_name and file_size
                    print(f"\n📎 File info:")
                    print(f"   File name: {doc.get('file_name')}")
                    print(f"   File type: {doc.get('file_type')}")
                    print(f"   File size: {doc.get('file_size')} bytes")
                    
                    break
                    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

check_full_document_storage()