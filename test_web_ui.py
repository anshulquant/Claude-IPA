#!/usr/bin/env python3
"""
Web UI Test Suite
Tests the web interface components and user interactions
"""

import requests
import time
import json
from datetime import datetime

class WebUITester:
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
    
    def test_endpoint(self, name, url, expected_status=200, method="GET", data=None):
        """Test a single endpoint"""
        try:
            if method == "GET":
                response = self.session.get(f"{self.base_url}{url}", timeout=10)
            elif method == "POST":
                response = self.session.post(f"{self.base_url}{url}", json=data, timeout=10)
            
            success = response.status_code == expected_status
            self.test_results.append({
                'name': name,
                'success': success,
                'status_code': response.status_code,
                'expected_status': expected_status,
                'url': url
            })
            
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {name}: {response.status_code}")
            
            if not success:
                print(f"   Expected: {expected_status}, Got: {response.status_code}")
            
            return success
            
        except requests.exceptions.ConnectionError:
            self.test_results.append({
                'name': name,
                'success': False,
                'status_code': None,
                'expected_status': expected_status,
                'url': url,
                'error': 'Connection refused - Server not running'
            })
            print(f"❌ {name}: Connection refused (Server not running)")
            return False
        except Exception as e:
            self.test_results.append({
                'name': name,
                'success': False,
                'status_code': None,
                'expected_status': expected_status,
                'url': url,
                'error': str(e)
            })
            print(f"❌ {name}: {str(e)}")
            return False
    
    def test_page_content(self, name, url, expected_content=None):
        """Test page content"""
        try:
            response = self.session.get(f"{self.base_url}{url}", timeout=10)
            
            if response.status_code != 200:
                print(f"❌ {name}: Page not accessible ({response.status_code})")
                return False
            
            content = response.text
            
            # Check for basic HTML structure
            has_html = "<html" in content.lower()
            has_title = "<title>" in content.lower()
            has_body = "<body" in content.lower()
            
            basic_structure = has_html and has_title and has_body
            
            # Check for specific content if provided
            specific_content = True
            if expected_content:
                for content_item in expected_content:
                    if content_item not in content:
                        specific_content = False
                        break
            
            success = basic_structure and specific_content
            
            self.test_results.append({
                'name': name,
                'success': success,
                'status_code': response.status_code,
                'has_html': has_html,
                'has_title': has_title,
                'has_body': has_body,
                'specific_content': specific_content
            })
            
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {name}: Page structure and content")
            
            if not basic_structure:
                print(f"   Missing basic HTML structure")
            if not specific_content and expected_content:
                print(f"   Missing expected content: {expected_content}")
            
            return success
            
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
            return False
    
    def test_api_response(self, name, url, expected_keys=None):
        """Test API response structure"""
        try:
            response = self.session.get(f"{self.base_url}{url}", timeout=10)
            
            if response.status_code != 200:
                print(f"❌ {name}: API not accessible ({response.status_code})")
                return False
            
            try:
                data = response.json()
            except json.JSONDecodeError:
                print(f"❌ {name}: Invalid JSON response")
                return False
            
            # Check for expected keys
            has_expected_keys = True
            if expected_keys:
                for key in expected_keys:
                    if key not in data:
                        has_expected_keys = False
                        break
            
            success = has_expected_keys
            
            self.test_results.append({
                'name': name,
                'success': success,
                'status_code': response.status_code,
                'has_expected_keys': has_expected_keys,
                'response_keys': list(data.keys()) if isinstance(data, dict) else None
            })
            
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {name}: API response structure")
            
            if not has_expected_keys and expected_keys:
                print(f"   Missing expected keys: {expected_keys}")
                print(f"   Available keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            return success
            
        except Exception as e:
            print(f"❌ {name}: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all web UI tests"""
        print("🌐 Web UI Test Suite")
        print("=" * 50)
        print(f"Testing server at: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        # Test basic connectivity
        print("\n📡 Testing Basic Connectivity...")
        self.test_endpoint("Health Check", "/api/health")
        
        # Test main pages
        print("\n📄 Testing Main Pages...")
        self.test_page_content(
            "Main Workflow Page", 
            "/", 
            ["Claude Automation Hub", "Start New Workflow", "Review Queue"]
        )
        self.test_page_content(
            "Review Queue Page", 
            "/review-queue", 
            ["Review Queue Management", "Filter and Search", "Review Items"]
        )
        
        # Test static files
        print("\n📁 Testing Static Files...")
        self.test_endpoint("CSS File", "/static/style.css")
        self.test_endpoint("Main JavaScript", "/static/app.js")
        self.test_endpoint("Review Queue JavaScript", "/static/review_queue.js")
        
        # Test API endpoints
        print("\n🔌 Testing API Endpoints...")
        self.test_api_response("Review Queue Stats", "/api/review-queue/stats", ["success", "stats"])
        self.test_api_response("Review Queue Pending", "/api/review-queue/pending", ["success"])
        self.test_api_response("Review Queue Filter", "/api/review-queue/filter", ["success"])
        self.test_api_response("Review Queue Search", "/api/review-queue/search?query=test", ["success"])
        self.test_api_response("Review Queue Categories", "/api/review-queue/categories", ["success"])
        self.test_api_response("Review Queue Priorities", "/api/review-queue/priorities", ["success"])
        
        # Test workflow API
        print("\n⚙️ Testing Workflow API...")
        workflow_data = {
            "goal": "Test workflow for UI testing",
            "start_url": "https://example.com"
        }
        self.test_endpoint("Workflow Execution", "/api/execute-workflow", 200, "POST", workflow_data)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 Web UI Test Results Summary")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "Success Rate: N/A")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['name']}: {result.get('error', 'Unknown error')}")
        
        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if failed_tests == 0:
            print("\n🎉 All Web UI tests passed!")
        else:
            print(f"\n⚠️  {failed_tests} tests failed. Please check the server and try again.")
        
        return failed_tests == 0

def main():
    """Main function to run web UI tests"""
    tester = WebUITester()
    success = tester.run_all_tests()
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
