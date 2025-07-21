"""
Blueprint Route Timeout Debug Script
This script tests individual blueprint routes to identify timeout issues
"""
import requests
import time
import sys
import subprocess
import threading
from datetime import datetime

class BlueprintTester:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.timeout = 10  # 10 second timeout
        
    def test_route(self, route, method="GET", data=None, requires_auth=False):
        """Test a specific route and measure response time"""
        url = f"{self.base_url}{route}"
        
        try:
            start_time = time.time()
            
            if method == "GET":
                response = self.session.get(url, timeout=self.timeout)
            elif method == "POST":
                response = self.session.post(url, data=data, timeout=self.timeout)
            
            response_time = time.time() - start_time
            
            return {
                'route': route,
                'status_code': response.status_code,
                'response_time': round(response_time, 3),
                'success': response.status_code < 400,
                'content_length': len(response.content),
                'error': None
            }
            
        except requests.exceptions.Timeout:
            return {
                'route': route,
                'status_code': None,
                'response_time': self.timeout,
                'success': False,
                'content_length': 0,
                'error': 'TIMEOUT'
            }
        except Exception as e:
            return {
                'route': route,
                'status_code': None,
                'response_time': None,
                'success': False,
                'content_length': 0,
                'error': str(e)
            }

def start_flask_server():
    """Start Flask server in background"""
    import subprocess
    import time
    
    print("🚀 Starting Flask server...")
    process = subprocess.Popen(
        ["python", "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd="."
    )
    
    # Wait for server to start
    time.sleep(3)
    
    # Check if server is running
    try:
        response = requests.get("http://127.0.0.1:5000", timeout=5)
        print("✅ Flask server started successfully")
        return process
    except:
        print("❌ Failed to start Flask server")
        return None

def main():
    print("🔍 RahaSoft ERP Blueprint Route Timeout Debugger")
    print("=" * 50)
    
    # Test routes that were timing out
    test_routes = [
        # Core routes
        "/",
        "/welcome",
        "/login",
        "/register_company",
        
        # Blueprint routes that were timing out
        "/employees",
        "/employees/add",
        "/payroll",
        "/payroll/calculate",
        "/support",
        "/support/new_ticket",
        "/user_management",
        "/user_management/users",
        
        # Additional routes to test
        "/dashboard",
        "/sales",
        "/inventory",
        "/attendance",
        "/reports"
    ]
    
    # Start Flask server
    server_process = start_flask_server()
    if not server_process:
        print("❌ Cannot start Flask server. Exiting.")
        return
    
    try:
        # Initialize tester
        tester = BlueprintTester()
        
        # Test each route
        results = []
        print("\n🧪 Testing Routes:")
        print("-" * 50)
        
        for route in test_routes:
            print(f"Testing {route}...", end=" ")
            result = tester.test_route(route)
            results.append(result)
            
            if result['success']:
                print(f"✅ {result['status_code']} ({result['response_time']}s)")
            else:
                error_msg = result['error'] or f"HTTP {result['status_code']}"
                print(f"❌ {error_msg}")
        
        # Analyze results
        print("\n📊 Results Summary:")
        print("-" * 50)
        
        successful_routes = [r for r in results if r['success']]
        failed_routes = [r for r in results if not r['success']]
        timeout_routes = [r for r in results if r['error'] == 'TIMEOUT']
        
        print(f"✅ Successful: {len(successful_routes)}/{len(results)}")
        print(f"❌ Failed: {len(failed_routes)}/{len(results)}")
        print(f"⏰ Timeouts: {len(timeout_routes)}/{len(results)}")
        
        if timeout_routes:
            print("\n⏰ Routes with Timeouts:")
            for route in timeout_routes:
                print(f"  - {route['route']}")
        
        if failed_routes:
            print("\n❌ Failed Routes:")
            for route in failed_routes:
                if route['error'] != 'TIMEOUT':
                    print(f"  - {route['route']}: {route['error'] or route['status_code']}")
        
        # Performance analysis
        if successful_routes:
            avg_response_time = sum(r['response_time'] for r in successful_routes) / len(successful_routes)
            slow_routes = [r for r in successful_routes if r['response_time'] > 2.0]
            
            print(f"\n⚡ Performance Analysis:")
            print(f"  - Average response time: {avg_response_time:.3f}s")
            
            if slow_routes:
                print(f"  - Slow routes (>2s):")
                for route in slow_routes:
                    print(f"    - {route['route']}: {route['response_time']}s")
        
    finally:
        # Stop Flask server
        print("\n🛑 Stopping Flask server...")
        server_process.terminate()
        server_process.wait()
        print("✅ Flask server stopped")

if __name__ == "__main__":
    main()
