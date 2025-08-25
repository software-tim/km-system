"""
Test script to generate embeddings for one existing document
Run this after deployment to test the embedding generation
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_embedding_generation():
    """Test generating embeddings for document 94 (orchestrator_api_guide)"""
    
    orchestrator_url = "https://km-orchestrator.azurewebsites.net"
    
    # First, get the document content
    print("Testing embedding generation for orchestrator_api_guide (ID: 94)")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Get document details
            response = await client.get(f"{orchestrator_url}/api/documents/94")
            if response.status_code == 200:
                doc = response.json()
                print(f"Found document: {doc.get('title', 'Unknown')}")
                
                # Trigger embedding generation by calling a special endpoint
                # or by re-processing the document
                print("Note: Embeddings will be generated on next document upload")
                print("Upload a new document to test the embedding generation")
            else:
                print(f"Could not fetch document: {response.status_code}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_embedding_generation())