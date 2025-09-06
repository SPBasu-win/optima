#!/usr/bin/env python3
"""
Test data import functionality
"""

import requests
import os

def test_data_import():
    """Test the data import API"""
    base_url = "http://localhost:8000/api/v1"
    
    # Check if CSV file exists
    csv_file = "D:\\sample_inventory.csv"
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found at: {csv_file}")
        return False
    
    print(f"📁 Found CSV file: {csv_file}")
    
    try:
        # Test file upload
        print("🔄 Testing file upload...")
        
        with open(csv_file, 'rb') as f:
            files = {'file': ('sample_inventory.csv', f, 'text/csv')}
            response = requests.post(f"{base_url}/data-import/upload", files=files)
        
        if response.status_code == 200:
            print("✅ File upload successful!")
            data = response.json()
            print(f"   Upload ID: {data['upload_id']}")
            print(f"   Rows: {data['file_info']['rows']}")
            print(f"   Columns: {data['file_info']['columns']}")
            
            # Test data cleaning
            print("🧹 Testing data cleaning...")
            upload_id = data['upload_id']
            clean_response = requests.post(f"{base_url}/data-import/clean/{upload_id}")
            
            if clean_response.status_code == 200:
                print("✅ Data cleaning successful!")
                clean_data = clean_response.json()
                print(f"   Cleaned fields: {clean_data['changes_summary']['cleaned_fields']}")
                print(f"   Text fields processed: {clean_data['changes_summary']['text_fields_processed']}")
                
                # Test data import
                print("💾 Testing data import...")
                import_payload = {
                    "upload_id": upload_id,
                    "confirmed_data": clean_data['cleaned_data'],
                    "import_options": {"skip_duplicates": True}
                }
                
                import_response = requests.post(f"{base_url}/data-import/import", json=import_payload)
                
                if import_response.status_code == 200:
                    print("✅ Data import successful!")
                    import_data = import_response.json()
                    print(f"   Imported: {import_data['imported_count']} records")
                    print(f"   Skipped: {import_data['skipped_count']} records")
                    print(f"   Errors: {import_data['error_count']} records")
                    return True
                else:
                    print(f"❌ Data import failed: {import_response.status_code}")
                    print(f"   Response: {import_response.text}")
            else:
                print(f"❌ Data cleaning failed: {clean_response.status_code}")
                print(f"   Response: {clean_response.text}")
        else:
            print(f"❌ File upload failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        return False
    
    return False

def main():
    """Main test function"""
    print("=" * 60)
    print("🧪 Testing Data Import API Functionality")
    print("=" * 60)
    
    if test_data_import():
        print("\n🎉 All data import tests passed!")
        print("✨ The CSV file upload, cleaning, and import functionality is working!")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
        print("💡 Make sure the backend server is running at http://localhost:8000")

if __name__ == "__main__":
    main()
