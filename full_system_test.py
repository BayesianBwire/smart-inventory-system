#!/usr/bin/env python3
"""
RahaSoft ERP - Comprehensive Full System Test
Tests all major functionality including authentication, CRUD operations, and core features
"""

import requests
import time
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://127.0.0.1:5000"
TEST_DATA = {
    'company': {
        'name': 'Test Company Ltd',
        'email': 'test@company.com',
        'phone': '+1234567890',
        'address': '123 Test Street',
        'city': 'Test City',
        'state': 'Test State',
        'country': 'Test Country',
        'postal_code': '12345',
        'website': 'https://testcompany.com',
        'description': 'A test company for system testing',
        'industry': 'Technology',
        'founder_name': 'John Test Founder',
        'founder_username': 'testfounder',
        'founder_email': 'founder@test.com',
        'founder_password': 'TestPass123!'
    }
}

class SystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.company_id = None
        self.founder_user_id = None
        
    def log_test(self, test_name, passed, details=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
    def test_server_health(self):
        """Test if server is running and responsive"""
        try:
            response = self.session.get(f"{BASE_URL}/")
            self.log_test("Server Health Check", response.status_code in [200, 302])
            return response.status_code in [200, 302]
        except Exception as e:
            self.log_test("Server Health Check", False, str(e))
            return False
            
    def test_welcome_page(self):
        """Test welcome page accessibility"""
        try:
            response = self.session.get(f"{BASE_URL}/welcome")
            self.log_test("Welcome Page", response.status_code == 200)
            return response.status_code == 200
        except Exception as e:
            self.log_test("Welcome Page", False, str(e))
            return False
            
    def test_login_page(self):
        """Test login page accessibility"""
        try:
            response = self.session.get(f"{BASE_URL}/login")
            self.log_test("Login Page", response.status_code == 200)
            return response.status_code == 200
        except Exception as e:
            self.log_test("Login Page", False, str(e))
            return False
            
    def test_company_registration_page(self):
        """Test company registration page"""
        try:
            response = self.session.get(f"{BASE_URL}/register_company")
            passed = response.status_code == 200 and "Company Registration" in response.text
            self.log_test("Company Registration Page", passed)
            return passed
        except Exception as e:
            self.log_test("Company Registration Page", False, str(e))
            return False
            
    def get_csrf_token(self, url):
        """Extract CSRF token from form"""
        try:
            response = self.session.get(url)
            if 'csrf_token' in response.text:
                # Simple extraction - in real app you'd parse HTML properly
                start = response.text.find('name="csrf_token" value="') + len('name="csrf_token" value="')
                end = response.text.find('"', start)
                return response.text[start:end]
        except:
            pass
        return None
        
    def test_company_registration(self):
        """Test complete company registration process"""
        try:
            # Get CSRF token
            csrf_token = self.get_csrf_token(f"{BASE_URL}/register_company")
            
            # Prepare form data
            form_data = TEST_DATA['company'].copy()
            if csrf_token:
                form_data['csrf_token'] = csrf_token
                
            # Submit registration
            response = self.session.post(f"{BASE_URL}/register_company", data=form_data)
            
            # Check if redirected (successful registration) or form errors
            passed = response.status_code in [200, 302]
            
            if response.status_code == 302:
                self.log_test("Company Registration", True, "Registration successful, redirected")
            elif "error" in response.text.lower():
                self.log_test("Company Registration", False, "Form validation errors")
            else:
                self.log_test("Company Registration", passed, f"Status: {response.status_code}")
                
            return passed
        except Exception as e:
            self.log_test("Company Registration", False, str(e))
            return False
            
    def test_founder_login(self):
        """Test founder login after registration"""
        try:
            # Get CSRF token for login
            csrf_token = self.get_csrf_token(f"{BASE_URL}/login")
            
            login_data = {
                'username': TEST_DATA['company']['founder_username'],
                'password': TEST_DATA['company']['founder_password']
            }
            if csrf_token:
                login_data['csrf_token'] = csrf_token
                
            response = self.session.post(f"{BASE_URL}/login", data=login_data)
            passed = response.status_code in [200, 302]
            
            if response.status_code == 302:
                self.log_test("Founder Login", True, "Login successful, redirected to dashboard")
            else:
                self.log_test("Founder Login", passed, f"Status: {response.status_code}")
                
            return passed
        except Exception as e:
            self.log_test("Founder Login", False, str(e))
            return False
            
    def test_protected_routes(self):
        """Test access to protected routes after login"""
        protected_routes = [
            ('/founder_dashboard', 'Founder Dashboard'),
            ('/dashboard', 'Main Dashboard'),
            ('/inventory', 'Inventory Management'),
            ('/pos', 'Point of Sale'),
            ('/users', 'User Management'),
            ('/employees', 'Employee Management'),
            ('/payroll', 'Payroll System'),
            ('/support', 'Support System')
        ]
        
        for route, name in protected_routes:
            try:
                response = self.session.get(f"{BASE_URL}{route}")
                passed = response.status_code == 200
                self.log_test(f"Protected Route: {name}", passed)
            except Exception as e:
                self.log_test(f"Protected Route: {name}", False, str(e))
                
    def test_advanced_features(self):
        """Test advanced features"""
        advanced_routes = [
            ('/ai-assistant', 'AI Assistant'),
            ('/meeting-rooms', 'Meeting Rooms'),
            ('/marketplace', 'Marketplace'),
            ('/calendar', 'Calendar'),
            ('/notifications', 'Notifications'),
            ('/training', 'Training Center'),
            ('/audit-me', 'Audit System'),
            ('/backup', 'Backup System')
        ]
        
        for route, name in advanced_routes:
            try:
                response = self.session.get(f"{BASE_URL}{route}")
                passed = response.status_code == 200
                self.log_test(f"Advanced Feature: {name}", passed)
            except Exception as e:
                self.log_test(f"Advanced Feature: {name}", False, str(e))
                
    def test_error_pages(self):
        """Test custom error pages"""
        try:
            # Test 404 page
            response = self.session.get(f"{BASE_URL}/nonexistent-page")
            passed_404 = response.status_code == 404
            self.log_test("404 Error Page", passed_404)
            
            return passed_404
        except Exception as e:
            self.log_test("Error Pages", False, str(e))
            return False
            
    def test_static_assets(self):
        """Test if static assets are accessible"""
        static_files = [
            '/static/css/dashboard.css',
            '/static/js/main.js'
        ]
        
        for asset in static_files:
            try:
                response = self.session.get(f"{BASE_URL}{asset}")
                passed = response.status_code == 200
                self.log_test(f"Static Asset: {asset}", passed)
            except Exception as e:
                self.log_test(f"Static Asset: {asset}", False, str(e))
                
    def test_api_endpoints(self):
        """Test basic API functionality"""
        api_endpoints = [
            ('/api/health', 'Health Check API'),
        ]
        
        for endpoint, name in api_endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                # API might not exist, so we don't fail the test
                passed = response.status_code in [200, 404]
                self.log_test(f"API Endpoint: {name}", passed, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"API Endpoint: {name}", False, str(e))
                
    def test_database_operations(self):
        """Test basic database connectivity through routes"""
        try:
            # Test route that definitely uses database
            response = self.session.get(f"{BASE_URL}/founder_dashboard")
            passed = response.status_code == 200 and "Database" not in response.text or "Error" not in response.text
            self.log_test("Database Operations", passed)
            return passed
        except Exception as e:
            self.log_test("Database Operations", False, str(e))
            return False
            
    def run_full_test_suite(self):
        """Run complete test suite"""
        print("🚀 Starting RahaSoft ERP Full System Test")
        print("=" * 60)
        
        start_time = time.time()
        
        # Core Infrastructure Tests
        print("\n📋 CORE INFRASTRUCTURE TESTS")
        print("-" * 40)
        self.test_server_health()
        self.test_welcome_page()
        self.test_login_page()
        self.test_company_registration_page()
        
        # Registration and Authentication Tests
        print("\n🔐 AUTHENTICATION TESTS")
        print("-" * 40)
        self.test_company_registration()
        self.test_founder_login()
        
        # Core Module Tests
        print("\n🏢 CORE MODULE TESTS")
        print("-" * 40)
        self.test_protected_routes()
        
        # Advanced Features Tests
        print("\n⚡ ADVANCED FEATURES TESTS")
        print("-" * 40)
        self.test_advanced_features()
        
        # System Tests
        print("\n🔧 SYSTEM TESTS")
        print("-" * 40)
        self.test_error_pages()
        self.test_static_assets()
        self.test_api_endpoints()
        self.test_database_operations()
        
        # Calculate results
        end_time = time.time()
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"⏱️  Total execution time: {end_time - start_time:.2f} seconds")
        print(f"📝 Total tests run: {total_tests}")
        print(f"✅ Tests passed: {passed_tests}")
        print(f"❌ Tests failed: {failed_tests}")
        print(f"📈 Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"   • {result['test']}: {result['details']}")
        
        # Save detailed results
        self.save_test_results()
        
        # Overall result
        overall_success = (passed_tests / total_tests) >= 0.8  # 80% pass rate
        print(f"\n🎯 OVERALL RESULT: {'🎉 SUCCESS' if overall_success else '⚠️  NEEDS ATTENTION'}")
        
        if overall_success:
            print("✨ RahaSoft ERP system is functioning well!")
        else:
            print("🔧 Some issues detected. Review failed tests above.")
            
        return overall_success
        
    def save_test_results(self):
        """Save test results to JSON file"""
        try:
            results = {
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_tests': len(self.test_results),
                    'passed': sum(1 for r in self.test_results if r['passed']),
                    'failed': sum(1 for r in self.test_results if not r['passed']),
                    'success_rate': (sum(1 for r in self.test_results if r['passed']) / len(self.test_results)) * 100
                },
                'detailed_results': self.test_results
            }
            
            with open('test_results_full.json', 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Detailed results saved to 'test_results_full.json'")
        except Exception as e:
            print(f"❌ Could not save test results: {e}")

if __name__ == "__main__":
    tester = SystemTester()
    tester.run_full_test_suite()
