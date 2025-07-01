#!/usr/bin/env python3
"""
Test script for enhanced server with mouse functionality
Tests both keyboard and mouse endpoints
"""

import requests
import json
import time
import sys
from urllib3.exceptions import InsecureRequestWarning

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class EnhancedServerTester:
    def __init__(self, use_https=False):
        self.base_url = "https://localhost:8444" if use_https else "http://localhost:8334"
        self.verify_ssl = False
        
    def test_request(self, method, endpoint, data=None):
        """Make a test request and return results"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            print(f"\n🧪 Testing {method} {endpoint}")
            if data:
                print(f"   📤 Data: {json.dumps(data)}")
            
            if method == "GET":
                response = requests.get(url, verify=self.verify_ssl, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=data, verify=self.verify_ssl, timeout=10)
            else:
                print(f"   ❌ Unsupported method: {method}")
                return False
            
            print(f"   📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    print(f"   ✅ Success: {result.get('message', 'OK')}")
                    return True
                except:
                    print(f"   ✅ Success: {response.text[:100]}")
                    return True
            else:
                print(f"   ❌ Failed: {response.text[:200]}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request failed: {e}")
            return False
    
    def run_tests(self):
        """Run comprehensive test suite"""
        print("=" * 60)
        print("🚀 ENHANCED SERVER TEST SUITE")
        print("=" * 60)
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Server info
        total_tests += 1
        if self.test_request("GET", "/"):
            tests_passed += 1
        
        # Test 2: Debug info
        total_tests += 1
        if self.test_request("GET", "/debug"):
            tests_passed += 1
        
        # Test 3: Script listing
        total_tests += 1
        if self.test_request("GET", "/scripts"):
            tests_passed += 1
        
        # Test 4: Macro status
        total_tests += 1
        if self.test_request("GET", "/status"):
            tests_passed += 1
        
        # Test 5: Mouse status
        total_tests += 1
        if self.test_request("GET", "/mouse/status"):
            tests_passed += 1
        
        # Test 6: Mouse center
        total_tests += 1
        if self.test_request("POST", "/mouse/center"):
            tests_passed += 1
        
        # Test 7: Mouse move
        total_tests += 1
        if self.test_request("POST", "/mouse/move", {"x": 500, "y": 400}):
            tests_passed += 1
        
        # Test 8: Mouse click
        total_tests += 1
        if self.test_request("POST", "/mouse/click", {"x": 1280, "y": 800}):
            tests_passed += 1
        
        # Test 9: Invalid coordinates (should fail gracefully)
        total_tests += 1
        print(f"\n🧪 Testing POST /mouse/click (invalid coordinates)")
        print(f"   📤 Data: {json.dumps({'x': 9999, 'y': 9999})}")
        try:
            response = requests.post(
                f"{self.base_url}/mouse/click", 
                json={"x": 9999, "y": 9999}, 
                verify=self.verify_ssl, 
                timeout=10
            )
            if response.status_code == 400:  # Should return bad request
                print(f"   ✅ Correctly rejected invalid coordinates")
                tests_passed += 1
            else:
                print(f"   ❌ Should have rejected invalid coordinates")
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 TEST RESULTS: {tests_passed}/{total_tests} passed")
        if tests_passed == total_tests:
            print("✅ All tests passed!")
        else:
            print(f"❌ {total_tests - tests_passed} tests failed")
        print("=" * 60)
        
        return tests_passed == total_tests

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--https":
        print("Testing HTTPS endpoint (port 8444)")
        tester = EnhancedServerTester(use_https=True)
    else:
        print("Testing HTTP endpoint (port 8334)")
        tester = EnhancedServerTester(use_https=False)
    
    print(f"Target: {tester.base_url}")
    print("Make sure the enhanced server is running first!")
    print("(Run: python3 enhanced_server.py)")
    
    # Wait a moment for user to read
    time.sleep(2)
    
    # Run the tests
    success = tester.run_tests()
    
    if success:
        print("\n🎉 Enhanced server integration working!")
        print("\nQuick manual tests you can try:")
        print(f"  curl -X POST {tester.base_url}/mouse/center")
        print(f"  curl -X POST {tester.base_url}/mouse/click -H 'Content-Type: application/json' -d '{{\"x\": 1280, \"y\": 800}}'")
        print(f"  Visit: {tester.base_url}/docs")
    else:
        print("\n❌ Some tests failed. Check server logs for details.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
