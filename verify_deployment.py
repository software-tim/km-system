#!/usr/bin/env python3
"""
Verify if the latest code is actually deployed
"""
import requests
import json

def verify_deployment():
    """Check if the latest code is deployed"""
    
    print("=== Verifying Deployment Status ===\n")
    
    # 1. Check orchestrator health to see version
    print("1. Checking orchestrator health endpoint...")
    try:
        response = requests.get("https://km-orchestrator.azurewebsites.net/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Orchestrator is running")
            print(f"   Version: {data.get('version', 'unknown')}")
            print(f"   Timestamp: {data.get('timestamp', 'unknown')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # 2. Test the results endpoint to see if it has new fields
    print("\n2. Testing results endpoint for document 93...")
    try:
        response = requests.get("https://km-orchestrator.azurewebsites.net/api/document/93/results")
        if response.status_code == 200:
            data = response.json()
            doc_metadata = data.get('document_metadata', {})
            
            print("\n📋 Document metadata fields:")
            for key in doc_metadata.keys():
                print(f"   - {key}: {doc_metadata[key]}")
            
            # Check for new fields
            has_new_fields = all([
                'file_name' in doc_metadata,
                'file_size' in doc_metadata,
                'processing_time_seconds' in doc_metadata
            ])
            
            if has_new_fields:
                print("\n✅ NEW CODE IS DEPLOYED! New fields are present.")
            else:
                print("\n❌ OLD CODE STILL RUNNING! New fields missing.")
                print("\nMissing fields:")
                if 'file_name' not in doc_metadata:
                    print("   - file_name")
                if 'file_size' not in doc_metadata:
                    print("   - file_size")
                if 'processing_time_seconds' not in doc_metadata:
                    print("   - processing_time_seconds")
                    
            # Check processing summary
            proc_summary = data.get('processing_summary', {})
            print(f"\n📊 Processing time shown: {proc_summary.get('processing_time')}")
            
        else:
            print(f"❌ Results endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n3. Possible solutions if old code is still running:")
    print("   a) Restart the Azure App Service:")
    print("      az webapp restart --name km-orchestrator --resource-group km-group")
    print("   b) Check deployment logs:")
    print("      az webapp log tail --name km-orchestrator --resource-group km-group")
    print("   c) Force a redeploy by pushing an empty commit:")
    print("      git commit --allow-empty -m 'Force redeploy'")
    print("      git push origin master")

verify_deployment()