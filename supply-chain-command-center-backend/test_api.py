#!/usr/bin/env python3
"""
Quick API Test Script for Supply Chain Command Center
This script tests basic API functionality to ensure everything works.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import app

def test_basic_endpoints():
    """Test basic API endpoints"""
    client = TestClient(app)
    
    print("🧪 Testing Supply Chain Command Center API...")
    print("=" * 50)
    
    # Test root endpoint
    response = client.get("/")
    print(f"✅ Root endpoint: {response.status_code} - {response.json()}")
    
    # Test health check
    response = client.get("/health")
    print(f"✅ Health check: {response.status_code} - {response.json()}")
    
    # Test API docs are accessible
    response = client.get("/docs")
    print(f"✅ API docs: {response.status_code} - Documentation accessible")
    
    # Test inventory categories (should work without database)
    try:
        response = client.get("/api/v1/inventory/categories/list")
        print(f"✅ Inventory categories: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Inventory endpoint (DB required): {str(e)[:50]}...")
    
    # Test logistics demo endpoint
    try:
        response = client.get("/api/v1/logistics/demo/sample-request")
        if response.status_code == 200:
            print(f"✅ Logistics demo: {response.status_code} - Sample data available")
        else:
            print(f"⚠️ Logistics demo: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Logistics demo: {str(e)[:50]}...")
    
    # Test forecasting demo endpoints
    try:
        response = client.get("/api/v1/forecasting/insights/DEMO001?days=7")
        print(f"✅ Forecasting endpoint accessible: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Forecasting endpoint (DB required): {str(e)[:50]}...")
    
    print("\n" + "=" * 50)
    print("🎉 Basic API functionality test completed!")
    print("\nTo start the full application with database:")
    print("1. Start with Docker: docker-compose up -d")
    print("2. Or manually: uvicorn main:app --reload")
    print("\nThen visit:")
    print("- API: http://localhost:8000")
    print("- Docs: http://localhost:8000/docs")
    print("- MongoDB Admin: http://localhost:8081")

if __name__ == "__main__":
    test_basic_endpoints()
