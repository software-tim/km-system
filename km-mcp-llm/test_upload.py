#!/usr/bin/env python3
import requests
import json
import time

print("Testing document upload with AI classification...")

# Test document
test_doc = {
    "title": "Test Document for AI Classification",
    "content": """This is a test document about artificial intelligence and machine learning.
    AI systems are becoming increasingly sophisticated. Machine learning algorithms
    can now process vast amounts of data and identify patterns. Deep learning has
    revolutionized computer vision and natural language processing. The future of
    AI looks promising with continued advances in neural networks and computing power.""",
    "classification": "test"
}

# Upload document
print("\n1. Uploading document...")
response = requests.post("https://km-orchestrator.azurewebsites.net/api/upload", json=test_doc)

if response.status_code == 200:
    result = response.json()
    doc_id = result.get("document_id")
    print(f"✓ Document uploaded successfully with ID: {doc_id}")
    print(f"  AI Classification: {result.get('validation_results', {}).get('ai_classification')}")
    
    # Wait a moment for processing
    print("\n2. Waiting for processing to complete...")
    time.sleep(5)
    
    # Check if metadata was saved
    print("\n3. Checking if AI classification was saved...")
    search_response = requests.post(
        "https://km-mcp-sql-docs.azurewebsites.net/tools/search-documents",
        json={"query": None, "limit": 100, "offset": 0}
    )
    
    if search_response.status_code == 200:
        docs = search_response.json().get("documents", [])
        for doc in docs:
            if str(doc.get("id")) == str(doc_id):
                metadata = doc.get("metadata", {})
                if "ai_classification" in metadata:
                    print("✓ AI classification SAVED in metadata!")
                    print(f"  Category: {metadata['ai_classification'].get('category')}")
                    print(f"  Has summary: {'summary' in metadata['ai_classification']}")
                else:
                    print("✗ AI classification NOT found in metadata")
                    print(f"  Metadata keys: {list(metadata.keys())}")
                break
    
    # Check results endpoint
    print(f"\n4. Results available at: https://km-ui-g2beg9brgjbkf9fr.eastus2-01.azurewebsites.net/upload/results?id={doc_id}")
    
else:
    print(f"✗ Upload failed: {response.status_code}")
    print(response.text)