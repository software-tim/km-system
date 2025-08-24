#!/usr/bin/env python3
"""
Test GraphRAG integration after timeout fix
"""
import requests
import json
import time

def test_graphrag_entity_extraction():
    """Test the GraphRAG entity extraction endpoint directly"""
    print("1. Testing GraphRAG entity extraction...")
    
    test_text = """
    Microsoft Corporation, headquartered in Redmond, Washington, is a leading technology company. 
    Bill Gates and Paul Allen founded Microsoft in 1975. The company develops software products 
    including Windows operating system and Office productivity suite. Satya Nadella currently 
    serves as CEO. Microsoft Azure provides cloud computing services competing with Amazon AWS.
    """
    
    url = "https://km-mcp-graphrag.azurewebsites.net/tools/extract-entities"
    payload = {
        "text": test_text,
        "document_id": "test_doc_graphrag"
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, json=payload, timeout=30)
        elapsed = time.time() - start_time
        
        print(f"   Response time: {elapsed:.2f}s")
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success! Found {result.get('entities_found', 0)} entities")
            print(f"   ✅ Found {result.get('relationships_found', 0)} relationships")
            
            # Show some entities
            entities = result.get('entities', [])
            if entities:
                print("\n   Sample entities found:")
                for entity in entities[:5]:
                    print(f"     - {entity['name']} ({entity['type']})")
                    
            return True
        else:
            print(f"   ❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return False

def test_orchestrator_upload():
    """Test document upload through orchestrator"""
    print("\n2. Testing document upload through orchestrator...")
    
    url = "https://km-orchestrator.azurewebsites.net/upload"
    
    # Create test content
    test_content = """
    Amazon Web Services (AWS) is a cloud computing platform by Amazon. 
    Jeff Bezos founded Amazon in 1994. AWS competes with Microsoft Azure and Google Cloud Platform.
    Key services include EC2 for compute, S3 for storage, and Lambda for serverless computing.
    """
    
    files = {
        'file': ('test_graphrag.txt', test_content, 'text/plain')
    }
    data = {
        'title': 'GraphRAG Test Document',
        'classification': 'unclassified'
    }
    
    print("   Uploading test document...")
    start_time = time.time()
    
    try:
        response = requests.post(url, files=files, data=data, timeout=120)
        elapsed = time.time() - start_time
        
        print(f"   Response time: {elapsed:.2f}s")
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            doc_id = result.get('document_id')
            print(f"   ✅ Document uploaded successfully! ID: {doc_id}")
            
            # Check processing results
            summary = result.get('processing_summary', {})
            print(f"\n   Processing summary:")
            print(f"     - Total time: {summary.get('total_time_seconds', 0)}s")
            print(f"     - Entities extracted: {summary.get('entities_extracted', 0)}")
            print(f"     - Relationships found: {summary.get('relationships_found', 0)}")
            print(f"     - GraphRAG updated: {summary.get('graphrag_updated', False)}")
            
            # Check if GraphRAG processing succeeded
            validation = result.get('validation_summary', {})
            graphrag_validation = validation.get('validation_details', {}).get('graphrag_processing', {})
            
            if graphrag_validation.get('success'):
                print(f"\n   ✅ GraphRAG processing succeeded!")
                print(f"     - Total entities in graph: {graphrag_validation.get('total_graph_entities', 0)}")
                print(f"     - Total relationships in graph: {graphrag_validation.get('total_graph_relationships', 0)}")
            else:
                print(f"\n   ❌ GraphRAG processing failed: {graphrag_validation.get('error', 'Unknown error')}")
                
            return doc_id if response.status_code == 200 else None
        else:
            print(f"   ❌ Upload failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return None

def check_graph_stats():
    """Check GraphRAG knowledge graph statistics"""
    print("\n3. Checking GraphRAG knowledge graph stats...")
    
    url = "https://km-mcp-graphrag.azurewebsites.net/health"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            stats = data.get('graph_stats', {})
            
            print(f"   ✅ GraphRAG service is healthy")
            print(f"\n   Knowledge Graph Statistics:")
            print(f"     - Total entities: {stats.get('total_entities', 0)}")
            print(f"     - Total relationships: {stats.get('total_relationships', 0)}")
            
            # Show entity types
            entity_types = stats.get('entity_types', {})
            if entity_types:
                print(f"\n     Entity types:")
                for etype, count in entity_types.items():
                    print(f"       - {etype}: {count}")
                    
            # Show most connected entities
            most_connected = stats.get('most_connected_entities', [])
            if most_connected:
                print(f"\n     Most connected entities:")
                for entity in most_connected[:3]:
                    print(f"       - {entity['entity']}: {entity['connections']} connections")
                    
        else:
            print(f"   ❌ Failed to get stats: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

if __name__ == "__main__":
    print("=== Testing GraphRAG Integration ===\n")
    
    # Test 1: Direct entity extraction
    extraction_success = test_graphrag_entity_extraction()
    
    # Test 2: Upload through orchestrator
    doc_id = test_orchestrator_upload()
    
    # Test 3: Check graph stats
    check_graph_stats()
    
    print("\n=== Test Summary ===")
    print(f"Entity extraction: {'✅ PASSED' if extraction_success else '❌ FAILED'}")
    print(f"Document upload: {'✅ PASSED' if doc_id else '❌ FAILED'}")
    print("\nThe GraphRAG timeout issue should now be fixed!")