#!/usr/bin/env python3
"""
Find documents with full content (>1000 chars)
"""
import requests
import json

def find_full_documents():
    """Find documents with substantial content"""
    search_url = "https://km-mcp-sql-docs.azurewebsites.net/tools/search-documents"
    
    search_payload = {
        "query": None,
        "limit": 100,
        "offset": 0
    }
    
    print("Searching for documents with full content...\n")
    
    try:
        response = requests.post(search_url, json=search_payload)
        if response.status_code == 200:
            result = response.json()
            documents = result.get('documents', [])
            
            full_docs = []
            
            for doc in documents:
                doc_id = doc.get('id')
                title = doc.get('title', 'Untitled')
                content = doc.get('content', '')
                content_len = len(content)
                
                # Check metadata for GraphRAG data
                metadata = doc.get('metadata')
                has_graphrag = False
                if metadata:
                    if isinstance(metadata, str):
                        try:
                            metadata = json.loads(metadata)
                            has_graphrag = 'entities' in metadata or 'ai_classification' in metadata
                        except:
                            pass
                
                if content_len > 1000:  # Documents with substantial content
                    full_docs.append({
                        'id': doc_id,
                        'title': title,
                        'content_length': content_len,
                        'has_graphrag': has_graphrag
                    })
                    
            # Sort by content length
            full_docs.sort(key=lambda x: x['content_length'], reverse=True)
            
            print(f"Found {len(full_docs)} documents with >1000 characters:\n")
            
            for doc in full_docs[:10]:  # Show top 10
                graphrag_status = "✅ Has GraphRAG data" if doc['has_graphrag'] else "❌ No GraphRAG data"
                print(f"Document {doc['id']}: {doc['title'][:50]}...")
                print(f"  Content: {doc['content_length']:,} characters")
                print(f"  {graphrag_status}")
                print()
                
            # Find best candidate (full content + GraphRAG data)
            best_candidates = [d for d in full_docs if d['has_graphrag']]
            if best_candidates:
                best = best_candidates[0]
                print(f"\n🎯 Best candidate for testing:")
                print(f"   Document {best['id']}: {best['title']}")
                print(f"   {best['content_length']:,} characters with GraphRAG data")
            else:
                print("\n⚠️  No documents found with both full content and GraphRAG data")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")

find_full_documents()