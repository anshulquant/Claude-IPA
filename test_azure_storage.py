#!/usr/bin/env python3
"""
Azure Storage Test Script for Claude IPA MVP
Tests Azure Storage connectivity and functionality
"""

import asyncio
import os
import sys
from datetime import datetime

def test_azure_imports():
    """Test Azure Storage imports"""
    print("🔍 Testing Azure Storage imports...")
    
    try:
        from azure.storage.blob import BlobServiceClient, BlobClient
        print("✅ Azure Storage Blob imported")
        
        from azure.core.exceptions import AzureError
        print("✅ Azure Core exceptions imported")
        
        from core.azure_storage import AzureStorageService, azure_storage
        print("✅ Azure Storage service imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_azure_configuration():
    """Test Azure Storage configuration"""
    print("\n🔍 Testing Azure Storage configuration...")
    
    try:
        from core.azure_storage import azure_storage
        
        storage_info = azure_storage.get_storage_info()
        print(f"Storage available: {storage_info['available']}")
        print(f"Screenshots container: {storage_info['screenshots_container']}")
        print(f"Logs container: {storage_info['logs_container']}")
        print(f"Connection string configured: {storage_info['connection_string_configured']}")
        
        if not storage_info['connection_string_configured']:
            print("⚠️  Azure Storage connection string not configured")
            print("   Add AZURE_STORAGE_CONNECTION_STRING to your .env file")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

async def test_azure_connectivity():
    """Test Azure Storage connectivity"""
    print("\n🔍 Testing Azure Storage connectivity...")
    
    try:
        from core.azure_storage import azure_storage
        
        if not azure_storage.is_available():
            print("❌ Azure Storage not available")
            return False
        
        # Test with a small blob
        test_data = b"Test data for Claude IPA MVP"
        test_workflow_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"Uploading test data for workflow: {test_workflow_id}")
        
        # Test screenshot upload
        screenshot_url = await azure_storage.upload_screenshot(
            test_data, test_workflow_id, "test_screenshot"
        )
        
        if screenshot_url:
            print(f"✅ Screenshot uploaded: {screenshot_url}")
        else:
            print("❌ Screenshot upload failed")
            return False
        
        # Test log upload
        log_data = '{"test": "log data", "timestamp": "' + datetime.now().isoformat() + '"}'
        log_url = await azure_storage.upload_workflow_log(log_data, test_workflow_id)
        
        if log_url:
            print(f"✅ Log uploaded: {log_url}")
        else:
            print("❌ Log upload failed")
            return False
        
        # Test workflow data upload
        workflow_data = {
            "workflow_id": test_workflow_id,
            "status": "test",
            "timestamp": datetime.now().isoformat(),
            "test_data": "Azure Storage integration test"
        }
        
        data_url = await azure_storage.upload_workflow_data(workflow_data, test_workflow_id)
        
        if data_url:
            print(f"✅ Workflow data uploaded: {data_url}")
        else:
            print("❌ Workflow data upload failed")
            return False
        
        # Test file listing
        files = await azure_storage.list_workflow_files(test_workflow_id)
        print(f"✅ Found {len(files)} files for test workflow")
        
        for file_info in files:
            print(f"   - {file_info['type']}: {file_info['name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connectivity test failed: {e}")
        return False

def test_environment_setup():
    """Test environment setup"""
    print("\n🔍 Testing environment setup...")
    
    # Check if .env file exists
    if os.path.exists(".env"):
        print("✅ .env file exists")
        
        # Read and check for Azure configuration
        with open(".env", "r") as f:
            env_content = f.read()
            
        if "AZURE_STORAGE_CONNECTION_STRING" in env_content:
            print("✅ Azure Storage connection string found in .env")
        else:
            print("⚠️  Azure Storage connection string not found in .env")
            
        if "AZURE_STORAGE_CONTAINER_NAME" in env_content:
            print("✅ Azure Storage container name found in .env")
        else:
            print("⚠️  Azure Storage container name not found in .env")
            
    else:
        print("❌ .env file not found")
        print("   Create .env file with your Azure Storage credentials")
        return False
    
    return True

def print_setup_instructions():
    """Print setup instructions for Azure Storage"""
    print("\n📋 Azure Storage Setup Instructions:")
    print("=" * 50)
    print("1. Create a .env file in your project root")
    print("2. Add the following configuration:")
    print()
    print("AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=your_account;AccountKey=your_key;EndpointSuffix=core.windows.net")
    print("AZURE_STORAGE_CONTAINER_NAME=claude-ipa-screenshots")
    print("AZURE_STORAGE_CONTAINER_LOGS=claude-ipa-logs")
    print()
    print("3. Install Azure Storage dependencies:")
    print("   pip install azure-storage-blob azure-identity")
    print()
    print("4. Run this test script again to verify connectivity")

async def main():
    """Run all Azure Storage tests"""
    print("🚀 Claude IPA MVP - Azure Storage Integration Test")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_azure_imports),
        ("Environment Setup", test_environment_setup),
        ("Configuration Test", test_azure_configuration),
        ("Connectivity Test", test_azure_connectivity)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
                
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "="*60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All Azure Storage tests passed! Integration is ready!")
        print("\n🚀 Next steps:")
        print("1. Start the server: python api/main.py")
        print("2. Test workflow execution with Azure Storage")
        print("3. Check Azure Storage containers for uploaded files")
        return True
    else:
        print("⚠️  Some tests failed. Please check the setup.")
        print_setup_instructions()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
