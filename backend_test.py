import requests
import sys
import json
import time
from datetime import datetime

class RecursiveReasoningTester:
    def __init__(self, base_url="https://recursive-solver-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.api_base}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_create_session(self):
        """Test creating a new reasoning session"""
        test_data = {
            "query": "What are the main factors that contribute to climate change?",
            "max_depth": 3,
            "model": "gpt-4o-mini"
        }
        
        success, response = self.run_test(
            "Create Reasoning Session",
            "POST",
            "sessions",
            200,
            data=test_data
        )
        
        if success and 'id' in response:
            self.session_id = response['id']
            print(f"   Session ID: {self.session_id}")
            return True
        return False

    def test_get_sessions(self):
        """Test getting all sessions"""
        success, response = self.run_test(
            "Get All Sessions",
            "GET",
            "sessions",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} sessions")
            return True
        return False

    def test_get_specific_session(self):
        """Test getting a specific session"""
        if not self.session_id:
            print("❌ No session ID available for testing")
            return False
            
        success, response = self.run_test(
            "Get Specific Session",
            "GET",
            f"sessions/{self.session_id}",
            200
        )
        
        if success and 'id' in response:
            print(f"   Retrieved session: {response['query'][:50]}...")
            return True
        return False

    def test_websocket_connection(self):
        """Test WebSocket connection (basic connectivity)"""
        if not self.session_id:
            print("❌ No session ID available for WebSocket testing")
            return False
            
        try:
            import websocket
            
            ws_url = self.base_url.replace('https://', 'wss://').replace('http://', 'ws://')
            ws_endpoint = f"{ws_url}/api/ws/{self.session_id}"
            
            print(f"\n🔍 Testing WebSocket Connection...")
            print(f"   URL: {ws_endpoint}")
            
            # Test basic connection
            ws = websocket.create_connection(ws_endpoint, timeout=10)
            print("✅ WebSocket connection established")
            
            # Wait a moment for any initial messages
            time.sleep(2)
            
            ws.close()
            self.tests_run += 1
            self.tests_passed += 1
            return True
            
        except Exception as e:
            print(f"❌ WebSocket connection failed: {str(e)}")
            self.tests_run += 1
            return False

    def test_emergent_llm_key(self):
        """Test if Emergent LLM key is configured"""
        print(f"\n🔍 Testing Emergent LLM Key Configuration...")
        
        # This is indirect - we'll check if we can create a session successfully
        # The actual LLM processing happens via WebSocket
        test_data = {
            "query": "Test query for LLM key validation",
            "max_depth": 1,
            "model": "gpt-4o-mini"
        }
        
        success, response = self.run_test(
            "LLM Key Validation (via session creation)",
            "POST",
            "sessions",
            200,
            data=test_data
        )
        
        return success

def main():
    print("🚀 Starting Recursive Reasoning Framework Backend Tests")
    print("=" * 60)
    
    # Setup
    tester = RecursiveReasoningTester()
    
    # Run core API tests
    tests = [
        tester.test_create_session,
        tester.test_get_sessions,
        tester.test_get_specific_session,
        tester.test_emergent_llm_key,
        tester.test_websocket_connection,
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            tester.tests_run += 1
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 Backend Tests Summary:")
    print(f"   Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"   Success rate: {(tester.tests_passed/tester.tests_run*100):.1f}%" if tester.tests_run > 0 else "No tests run")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All backend tests passed!")
        return 0
    else:
        print("⚠️  Some backend tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())