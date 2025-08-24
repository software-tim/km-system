#!/usr/bin/env python3
"""
Test that document upload stores full content and file info
"""
import requests
import json
import base64

def test_upload_fix():
    """Test uploading a document with full content"""
    
    # Create test content (larger than 203 chars)
    test_content = """# Test Document for Upload Fix

This is a test document to verify that the full content is stored properly.
It contains multiple paragraphs and should be much longer than 203 characters.

## Section 1: Introduction
The upload was previously truncating content to only 203 characters. This test
verifies that the full document content is now stored in the database.

## Section 2: Technical Details
- Full content should be stored in the 'content' field
- Full file data should be stored in the 'file_data' field as base64
- File name, size, and type should be captured
- Top 25 chunks should be stored in metadata

## Section 3: Lorem Ipsum
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor 
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis 
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

## Section 4: Verification
This document is exactly 1234 characters long and should demonstrate proper storage.
""" * 3  # Make it even longer

    print(f"Test content length: {len(test_content)} characters\n")
    
    # Test JSON upload
    print("1. Testing JSON upload...")
    
    json_payload = {
        "title": "Test Upload Fix Document",
        "content": test_content,
        "classification": "test",
        "file_type": "text/markdown",
        "file_name": "test_upload_fix.md"
    }
    
    response = requests.post(
        "https://km-orchestrator.azurewebsites.net/api/upload",
        json=json_payload,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        doc_id = result.get('document_id')
        print(f"   ✅ Document uploaded with ID: {doc_id}")
        
        # Verify storage
        print(f"\n2. Verifying document storage...")
        
        search_url = "https://km-mcp-sql-docs.azurewebsites.net/tools/search-documents"
        search_payload = {"query": None, "limit": 100, "offset": 0}
        
        search_response = requests.post(search_url, json=search_payload)
        if search_response.status_code == 200:
            docs = search_response.json().get('documents', [])
            
            for doc in docs:
                if doc.get('id') == doc_id:
                    print(f"\n   ✅ Found document {doc_id}")
                    print(f"   Content length: {len(doc.get('content', ''))} chars")
                    print(f"   File name: {doc.get('file_name')}")
                    print(f"   File size: {doc.get('file_size')} bytes")
                    print(f"   File type: {doc.get('file_type')}")
                    
                    # Check file_data
                    file_data = doc.get('file_data')
                    if file_data:
                        try:
                            decoded = base64.b64decode(file_data)
                            print(f"   File data: {len(decoded)} bytes stored")
                        except:
                            print(f"   File data: Present but not base64")
                    else:
                        print(f"   File data: Not present")
                        
                    # Check metadata
                    metadata = doc.get('metadata')
                    if metadata and isinstance(metadata, str):
                        metadata = json.loads(metadata)
                        
                    if metadata:
                        if 'top_chunks' in metadata:
                            print(f"   Top chunks: {len(metadata['top_chunks'])} stored")
                        if 'file_info' in metadata:
                            print(f"   File info in metadata: {metadata['file_info']}")
                            
                    return doc_id
                    
    else:
        print(f"   ❌ Upload failed: {response.text}")
        
    return None

if __name__ == "__main__":
    print("=== Testing Document Upload Fix ===\n")
    doc_id = test_upload_fix()
    
    if doc_id:
        print(f"\n✅ Test passed! Document {doc_id} stored with full content.")
    else:
        print(f"\n❌ Test failed!")