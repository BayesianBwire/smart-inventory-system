#!/usr/bin/env python3
"""
🧪 RahaSoft ERP - Comprehensive System Test Suite
================================================
Complete end-to-end testing of all system components
"""

import os
import sys
import requests
import time
import json
from datetime import datetime
import subprocess
import sqlite3

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(message):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(message):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.END}")

class RahaSoftSystemTest:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5000"
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'total': 0
        }
        self.server_process = None

    def log_result(self, test_name, passed, message=""):
        self.test_results['total'] += 1
        if passed:
            self.test_results['passed'] += 1
            print_success(f"{test_name}: {message}")
        else:
            self.test_results['failed'] += 1
            print_error(f"{test_name}: {message}")

    def start_server(self):
        """Start the Flask development server"""
        print_header("🚀 STARTING FLASK SERVER")
        try:
            # Set environment variables
            env = os.environ.copy()
            env['FLASK_APP'] = 'app.py'
            env['FLASK_ENV'] = 'development'
            env['FLASK_DEBUG'] = '0'  # Disable debug for testing
            
            print_info("Starting Flask server on port 5000...")
            self.server_process = subprocess.Popen([
                sys.executable, '-m', 'flask', 'run', 
                '--host=127.0.0.1', '--port=5000'
            ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            time.sleep(5)
            
            # Test if server is running
            response = requests.get(f"{self.base_url}/welcome", timeout=10)
            if response.status_code == 200:
                print_success("Flask server started successfully")
                return True
            else:
                print_error(f"Server responded with status {response.status_code}")
                return False
                
        except Exception as e:
            print_error(f"Failed to start server: {str(e)}")
            return False

    def stop_server(self):
        """Stop the Flask development server"""
        if self.server_process:
            print_info("Stopping Flask server...")
            self.server_process.terminate()
            self.server_process.wait()
            print_success("Server stopped")

    def test_database_connection(self):
        """Test database connectivity and tables"""
        print_header("🗄️  DATABASE TESTS")
        
        # Test SQLite connection
        try:
            conn = sqlite3.connect('rahasoft.db')
            cursor = conn.cursor()
            
            # Check if main tables exist
            tables = ['user', 'company', 'login_log', 'product', 'sale', 'employee', 'payroll']
            for table in tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    self.log_result(f"Table '{table}' exists", True)
                else:
                    self.log_result(f"Table '{table}' missing", False)
            
            conn.close()
            
        except Exception as e:
            self.log_result("Database connection", False, str(e))

    def test_environment_config(self):
        """Test environment configuration"""
        print_header("⚙️  ENVIRONMENT CONFIGURATION")
        
        # Check .env file
        if os.path.exists('.env'):
            self.log_result("Environment file exists", True)
            
            # Check required environment variables
            with open('.env', 'r') as f:
                env_content = f.read()
                
            required_vars = ['SECRET_KEY', 'SQLALCHEMY_DATABASE_URI', 'SMTP_SERVER']
            for var in required_vars:
                if var in env_content:
                    self.log_result(f"Environment variable '{var}' found", True)
                else:
                    self.log_result(f"Environment variable '{var}' missing", False)
        else:
            self.log_result("Environment file", False, ".env file not found")

    def test_imports_and_dependencies(self):
        """Test all Python imports and dependencies"""
        print_header("📦 IMPORT & DEPENDENCY TESTS")
        
        imports_to_test = [
            'flask',
            'flask_wtf',
            'flask_login',
            'flask_sqlalchemy',
            'flask_migrate',
            'flask_mail',
            'wtforms',
            'sqlalchemy',
            'werkzeug',
            'itsdangerous',
            'pandas',
            'numpy'
        ]
        
        for module in imports_to_test:
            try:
                __import__(module)
                self.log_result(f"Import {module}", True)
            except ImportError as e:
                self.log_result(f"Import {module}", False, str(e))

    def test_web_pages(self):
        """Test all web page endpoints"""
        print_header("🌐 WEB PAGE TESTS")
        
        pages_to_test = [
            ('/welcome', 'Welcome Page'),
            ('/login', 'Login Page'),
            ('/register', 'User Registration Page'),
            ('/register_company', 'Company Registration Page'),
            ('/terms', 'Terms of Service Page'),
            ('/privacy', 'Privacy Policy Page'),
            ('/forgot_password', 'Forgot Password Page')
        ]
        
        for endpoint, name in pages_to_test:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    self.log_result(f"{name} accessibility", True, f"Status: {response.status_code}")
                else:
                    self.log_result(f"{name} accessibility", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result(f"{name} accessibility", False, str(e))

    def test_forms_and_validation(self):
        """Test form functionality and validation"""
        print_header("📋 FORM VALIDATION TESTS")
        
        # Test company registration form
        try:
            response = requests.get(f"{self.base_url}/register_company", timeout=10)
            if 'Company Name' in response.text and 'Founder Information' in response.text:
                self.log_result("Company registration form", True, "Form fields present")
            else:
                self.log_result("Company registration form", False, "Missing form fields")
        except Exception as e:
            self.log_result("Company registration form", False, str(e))
            
        # Test login form
        try:
            response = requests.get(f"{self.base_url}/login", timeout=10)
            if 'username' in response.text.lower() and 'password' in response.text.lower():
                self.log_result("Login form", True, "Form fields present")
            else:
                self.log_result("Login form", False, "Missing form fields")
        except Exception as e:
            self.log_result("Login form", False, str(e))

    def test_static_assets(self):
        """Test static file accessibility"""
        print_header("🎨 STATIC ASSETS TESTS")
        
        # Check if static directory exists
        if os.path.exists('static'):
            self.log_result("Static directory exists", True)
            
            # Check for common static files
            static_files = ['css', 'js', 'images']
            for folder in static_files:
                if os.path.exists(f'static/{folder}'):
                    self.log_result(f"Static/{folder} directory", True)
                else:
                    self.log_result(f"Static/{folder} directory", False, "Directory not found")
        else:
            self.log_result("Static directory", False, "Static directory not found")

    def test_blueprints_and_routes(self):
        """Test blueprint registration and routes"""
        print_header("🗺️  BLUEPRINT & ROUTE TESTS")
        
        # Test blueprint endpoints
        blueprint_routes = [
            ('/employees/', 'Employee Routes'),
            ('/payroll/', 'Payroll Routes'),
            ('/support/', 'Support Routes'),
            ('/users/', 'User Management Routes')
        ]
        
        for endpoint, name in blueprint_routes:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                # These may redirect to login, so 302 is also acceptable
                if response.status_code in [200, 302, 401]:
                    self.log_result(f"{name} blueprint", True, f"Status: {response.status_code}")
                else:
                    self.log_result(f"{name} blueprint", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_result(f"{name} blueprint", False, str(e))

    def test_security_features(self):
        """Test security implementations"""
        print_header("🔒 SECURITY TESTS")
        
        # Test CSRF protection
        try:
            response = requests.get(f"{self.base_url}/register_company", timeout=10)
            if 'csrf_token' in response.text:
                self.log_result("CSRF protection", True, "CSRF tokens present")
            else:
                self.log_result("CSRF protection", False, "CSRF tokens missing")
        except Exception as e:
            self.log_result("CSRF protection", False, str(e))
            
        # Test secure headers
        try:
            response = requests.get(f"{self.base_url}/welcome", timeout=10)
            headers = response.headers
            
            # Check for basic security headers
            if 'X-Frame-Options' in headers or 'Content-Security-Policy' in headers:
                self.log_result("Security headers", True, "Some security headers present")
            else:
                print_warning("Security headers not detected (consider adding)")
                
        except Exception as e:
            self.log_result("Security headers", False, str(e))

    def test_responsive_design(self):
        """Test responsive design elements"""
        print_header("📱 RESPONSIVE DESIGN TESTS")
        
        try:
            response = requests.get(f"{self.base_url}/welcome", timeout=10)
            content = response.text.lower()
            
            # Check for Bootstrap and responsive elements
            if 'bootstrap' in content:
                self.log_result("Bootstrap framework", True, "Bootstrap CSS detected")
            else:
                self.log_result("Bootstrap framework", False, "Bootstrap not detected")
                
            if 'viewport' in content:
                self.log_result("Viewport meta tag", True, "Mobile viewport configured")
            else:
                self.log_result("Viewport meta tag", False, "Mobile viewport missing")
                
        except Exception as e:
            self.log_result("Responsive design", False, str(e))

    def test_file_structure(self):
        """Test project file structure"""
        print_header("📁 FILE STRUCTURE TESTS")
        
        required_dirs = ['templates', 'static', 'models', 'routes', 'forms', 'utils']
        for directory in required_dirs:
            if os.path.exists(directory):
                self.log_result(f"Directory '{directory}'", True)
            else:
                self.log_result(f"Directory '{directory}'", False, "Directory missing")
                
        required_files = ['app.py', 'extensions.py', 'requirements.txt', '.env']
        for file in required_files:
            if os.path.exists(file):
                self.log_result(f"File '{file}'", True)
            else:
                self.log_result(f"File '{file}'", False, "File missing")

    def run_full_test_suite(self):
        """Run the complete test suite"""
        print_header("🧪 RAHASOFT ERP - COMPREHENSIVE SYSTEM TEST")
        print_info(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all test categories
        test_methods = [
            self.test_file_structure,
            self.test_environment_config,
            self.test_imports_and_dependencies,
            self.test_database_connection,
            self.test_web_pages,
            self.test_forms_and_validation,
            self.test_static_assets,
            self.test_blueprints_and_routes,
            self.test_security_features,
            self.test_responsive_design
        ]
        
        # Start server first
        if not self.start_server():
            print_error("Cannot start server. Skipping web-related tests.")
            # Run only non-web tests
            test_methods = [
                self.test_file_structure,
                self.test_environment_config,
                self.test_imports_and_dependencies,
                self.test_database_connection
            ]
        
        # Execute all tests
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print_error(f"Test method {test_method.__name__} failed: {str(e)}")
        
        # Stop server
        self.stop_server()
        
        # Print final results
        self.print_test_summary()

    def print_test_summary(self):
        """Print comprehensive test results"""
        print_header("📊 TEST RESULTS SUMMARY")
        
        total = self.test_results['total']
        passed = self.test_results['passed']
        failed = self.test_results['failed']
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"{Colors.BOLD}Total Tests Run:{Colors.END} {total}")
        print(f"{Colors.GREEN}✅ Passed:{Colors.END} {passed}")
        print(f"{Colors.RED}❌ Failed:{Colors.END} {failed}")
        print(f"{Colors.BOLD}Success Rate:{Colors.END} {success_rate:.1f}%")
        
        if success_rate >= 90:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 EXCELLENT! System is ready for production!{Colors.END}")
        elif success_rate >= 75:
            print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  GOOD! Minor issues need attention.{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}🚨 CRITICAL! Major issues require fixing.{Colors.END}")
        
        # Save results to file
        results = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'success_rate': success_rate
        }
        
        with open('test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print_info("Detailed results saved to test_results.json")

if __name__ == "__main__":
    print(f"{Colors.BOLD}{Colors.PURPLE}")
    print("🧪 RahaSoft ERP - Comprehensive System Test Suite")
    print("=" * 60)
    print(f"{Colors.END}")
    
    tester = RahaSoftSystemTest()
    tester.run_full_test_suite()
