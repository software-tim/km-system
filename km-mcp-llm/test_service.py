#!/usr/bin/env python3
"""Test script to verify km-mcp-llm service functionality"""

import requests
import json
import sys

# Service URL (adjust if running on different port)
BASE_URL = "https://km-mcp-llm.azurewebsites.net"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✓ Health check passed")
            print(f"  - Service: {health['service']}")
            print(f"  - Status: {health['status']}")
            print(f"  - AI Providers: {health.get('ai_providers', health.get('ai_services', 'N/A'))}")
            return True
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False

def test_analyze():
    """Test document analysis"""
    print("\nTesting document analysis...")
    
    test_document = """
    This is a test document about artificial intelligence and machine learning.
    AI systems are becoming increasingly sophisticated and are being deployed
    in various industries including healthcare, finance, and transportation.
    The ethical implications of AI deployment need careful consideration.
    """
    
    payload = {
        "content": test_document,
        "analysis_type": "comprehensive"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/analyze", json=payload)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✓ Analysis successful")
                print(f"  - Provider: {result.get('provider', 'Unknown')}")
                print(f"  - Model: {result.get('model', 'Unknown')}")
                print(f"  - Analysis preview: {result['analysis'][:200]}...")
                return True
            else:
                print(f"✗ Analysis failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"✗ Analysis request failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Analysis error: {e}")
        return False

def test_qa():
    """Test question answering"""
    print("\nTesting question answering...")
    
    context = "The company was founded in 2020 and specializes in AI-powered document management."
    question = "When was the company founded?"
    
    payload = {
        "question": question,
        "context": context
    }
    
    try:
        response = requests.post(f"{BASE_URL}/qa", json=payload)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✓ Q&A successful")
                print(f"  - Question: {question}")
                print(f"  - Answer: {result['answer']}")
                return True
            else:
                print(f"✗ Q&A failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"✗ Q&A request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Q&A error: {e}")
        return False

def test_summarize():
    """Test summarization"""
    print("\nTesting summarization...")
    
    long_text = """
    Knowledge management systems are essential for modern organizations.
    They help capture, organize, and share information across teams.
    Effective knowledge management can improve productivity, reduce duplication
    of effort, and accelerate innovation. Modern systems often incorporate
    AI and machine learning to enhance search capabilities and provide
    intelligent recommendations.
    """
    
    payload = {
        "content": long_text,
        "style": "concise"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/summarize", json=payload)
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print(f"✓ Summarization successful")
                print(f"  - Summary: {result['summary']}")
                return True
            else:
                print(f"✗ Summarization failed: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"✗ Summarization request failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Summarization error: {e}")
        return False

def main():
    print("=" * 60)
    print("Testing km-mcp-llm service")
    print("=" * 60)
    
    # Run all tests
    tests = [
        test_health,
        test_analyze,
        test_qa,
        test_summarize
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)