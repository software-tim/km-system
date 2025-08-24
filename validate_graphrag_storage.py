#!/usr/bin/env python3
"""
Validate GraphRAG data is stored in document metadata
"""
import requests
import json

def validate_graphrag_storage(doc_id):
    """Check if GraphRAG data is properly stored in metadata"""
    
    print(f"=== Validating GraphRAG Storage for Document {doc_id} ===\n")
    
    # 1. Get document from SQL service
    search_url = "https://km-mcp-sql-docs.azurewebsites.net/tools/search-documents"
    
    search_payload = {
        "query": None,
        "limit": 100,
        "offset": 0
    }
    
    print("1. Fetching document from SQL service...")
    
    try:
        response = requests.post(search_url, json=search_payload)
        if response.status_code == 200:
            result = response.json()
            documents = result.get('documents', [])
            
            # Find our document
            doc = None
            for d in documents:
                if d.get('id') == doc_id:
                    doc = d
                    break
                    
            if not doc:
                print(f"❌ Document {doc_id} not found")
                return
                
            print(f"✅ Found document: {doc.get('title')}")
            
            # 2. Check metadata
            metadata = doc.get('metadata')
            if not metadata:
                print("❌ No metadata found")
                return
                
            # Parse metadata if it's a string
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    print("❌ Could not parse metadata JSON")
                    return
                    
            print("\n2. Checking GraphRAG data in metadata...")
            
            # Check for AI classification
            if 'ai_classification' in metadata:
                ai_class = metadata['ai_classification']
                print(f"\n✅ AI Classification:")
                print(f"   Category: {ai_class.get('category')}")
                print(f"   Domains: {ai_class.get('domains')}")
                print(f"   Themes: {ai_class.get('themes')}")
                print(f"   Keywords: {ai_class.get('keywords')}")
            else:
                print("❌ No AI classification found")
                
            # Check for auto-generated tags
            if 'tags' in metadata:
                print(f"\n✅ Auto-generated Tags: {metadata['tags']}")
            else:
                print("❌ No auto-generated tags found")
                
            # Check for entities
            if 'entities' in metadata:
                entities = metadata['entities']
                print(f"\n✅ Entities Stored: {len(entities)} entities")
                for i, entity in enumerate(entities[:3]):
                    print(f"   Entity {i+1}: {entity.get('name')} ({entity.get('type')})")
                if len(entities) > 3:
                    print(f"   ... and {len(entities) - 3} more entities")
            else:
                print("❌ No entities stored in metadata")
                
            # Check for relationships
            if 'relationships' in metadata:
                relationships = metadata['relationships']
                print(f"\n✅ Relationships Stored: {len(relationships)} relationships")
                for i, rel in enumerate(relationships[:3]):
                    print(f"   Relationship {i+1}: {rel.get('source_entity')} -> {rel.get('target_entity')} ({rel.get('relationship_type')})")
                if len(relationships) > 3:
                    print(f"   ... and {len(relationships) - 3} more relationships")
            else:
                print("❌ No relationships stored in metadata")
                
            # Check for themes
            if 'themes' in metadata:
                themes = metadata['themes']
                print(f"\n✅ Themes Stored: {len(themes)} themes")
                for theme in themes:
                    print(f"   - {theme.get('name')} (confidence: {theme.get('confidence')})")
            else:
                print("❌ No themes stored in metadata")
                
            # Check for processing summary
            if 'processing_summary' in metadata:
                proc_sum = metadata['processing_summary']
                print(f"\n✅ Processing Summary:")
                print(f"   Total time: {proc_sum.get('total_time_seconds')}s")
                print(f"   Chunks created: {proc_sum.get('chunks_created')}")
                print(f"   Entities extracted: {proc_sum.get('entities_extracted')}")
                print(f"   Relationships found: {proc_sum.get('relationships_found')}")
            else:
                print("❌ No processing summary found")
                
            # Check for chunk info
            if 'chunk_info' in metadata:
                chunk_info = metadata['chunk_info']
                print(f"\n✅ Chunk Information:")
                print(f"   Total chunks: {chunk_info.get('total_chunks')}")
                print(f"   Chunk size: {chunk_info.get('chunk_size')}")
                print(f"   Chunking method: {chunk_info.get('chunking_method')}")
            else:
                print("❌ No chunk information found")
                
            # Summary
            print("\n" + "="*50)
            print("SUMMARY:")
            has_all = all([
                'ai_classification' in metadata,
                'tags' in metadata,
                'entities' in metadata,
                'relationships' in metadata,
                'themes' in metadata,
                'processing_summary' in metadata,
                'chunk_info' in metadata
            ])
            
            if has_all:
                print("✅ ALL GraphRAG data is properly persisted!")
            else:
                print("⚠️  Some GraphRAG data is missing from metadata")
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

# Check the latest document (91)
print("Checking document 91 (latest upload)...\n")
validate_graphrag_storage(91)

# Also check an older document for comparison
print("\n\n" + "="*70)
print("Checking document 90 (previous upload) for comparison...\n")
validate_graphrag_storage(90)