#!/usr/bin/env python3
"""
Check document 88 metadata and results
"""
import requests
import json

def check_document_metadata(doc_id):
    """Check document metadata via SQL service"""
    search_url = "https://km-mcp-sql-docs.azurewebsites.net/tools/search-documents"
    
    search_payload = {
        "query": None,
        "limit": 100,
        "offset": 0
    }
    
    print(f"1. Checking document {doc_id} in SQL service...")
    
    try:
        response = requests.post(search_url, json=search_payload)
        if response.status_code == 200:
            result = response.json()
            documents = result.get('documents', [])
            
            for doc in documents:
                if doc.get('id') == doc_id:
                    print(f"\n✅ Found document {doc_id}")
                    print(f"Title: {doc.get('title')}")
                    print(f"Classification: {doc.get('classification')}")
                    
                    metadata = doc.get('metadata')
                    if metadata:
                        if isinstance(metadata, str):
                            try:
                                metadata = json.loads(metadata)
                            except:
                                pass
                        
                        if isinstance(metadata, dict) and 'ai_classification' in metadata:
                            print("\n✅ AI Classification found in metadata!")
                            ai_class = metadata['ai_classification']
                            print(f"  Category: {ai_class.get('category')}")
                            print(f"  Domains: {ai_class.get('domains')}")
                            print(f"  Themes: {ai_class.get('themes')}")
                            print(f"  Keywords: {ai_class.get('keywords')}")
                            print(f"  Summary: {ai_class.get('summary', '')[:200]}...")
                        else:
                            print("\n❌ No AI classification in metadata")
                    else:
                        print("❌ No metadata found")
                    
                    return doc
    except Exception as e:
        print(f"Error: {e}")

def check_document_results(doc_id):
    """Check document results via orchestrator API"""
    print(f"\n2. Checking document {doc_id} results via orchestrator...")
    
    url = f"https://km-orchestrator.azurewebsites.net/api/document/{doc_id}/results"
    
    try:
        response = requests.get(url, timeout=30)
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Results retrieved successfully!")
            
            # Check AI classification
            ai_class = data.get('ai_classification', {})
            if ai_class:
                print(f"\nAI Classification:")
                print(f"  Category: {ai_class.get('category')}")
                print(f"  Domains: {ai_class.get('domains')}")
                print(f"  Confidence: {ai_class.get('confidence')}")
            
            # Check entities
            entities = data.get('entities', [])
            print(f"\nEntities: {len(entities)} found")
            for entity in entities[:3]:
                print(f"  - {entity.get('name')} ({entity.get('type')})")
            
            # Check relationships
            relationships = data.get('relationships', [])
            print(f"\nRelationships: {len(relationships)} found")
            for rel in relationships[:3]:
                print(f"  - {rel.get('source')} -> {rel.get('target')} ({rel.get('type')})")
            
            # Check themes
            themes = data.get('themes', [])
            print(f"\nThemes: {len(themes)} found")
            for theme in themes[:3]:
                print(f"  - {theme.get('name')} (confidence: {theme.get('confidence')})")
                
        else:
            print(f"❌ Failed to get results: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

# Check document 88
check_document_metadata(88)
check_document_results(88)