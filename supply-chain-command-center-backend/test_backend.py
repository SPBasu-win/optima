#!/usr/bin/env python3
"""
Quick test script to verify the backend is working
"""
import requests
import json

def test_backend():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Supply Chain Backend API...")
    print("=" * 50)
    
    try:
        # Test root endpoint
        response = requests.get(f"{base_url}/")
        print(f"✅ Root endpoint: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test health endpoint
        response = requests.get(f"{base_url}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test inventory endpoint
        response = requests.get(f"{base_url}/api/v1/inventory/")
        print(f"✅ Inventory endpoint: {response.status_code}")
        inventory_data = response.json()
        print(f"   Found {len(inventory_data)} items")
        
        # Test dashboard endpoint
        response = requests.get(f"{base_url}/api/v1/dashboard/summary")
        print(f"✅ Dashboard endpoint: {response.status_code}")
        dashboard_data = response.json()
        print(f"   Dashboard data: {dashboard_data}")
        
        # Test low stock items
        response = requests.get(f"{base_url}/api/v1/inventory/low-stock/items")
        print(f"✅ Low stock endpoint: {response.status_code}")
        low_stock = response.json()
        print(f"   Low stock items: {low_stock['count']}")
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Backend is working correctly!")
        print(f"🌐 API is running at: {base_url}")
        print(f"📚 Documentation at: {base_url}/docs")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running at http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error testing backend: {str(e)}")
        return False

if __name__ == "__main__":
    test_backend()
