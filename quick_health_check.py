#!/usr/bin/env python3
"""
Quick System Health Check - Test core functionality after fixes
"""

import requests
import time

BASE_URL = "http://127.0.0.1:5000"

def test_basic_routes():
    """Test basic routes are accessible"""
    routes = [
        ('/', 'Home Page'),
        ('/welcome', 'Welcome Page'),
        ('/login', 'Login Page'),
        ('/register_company', 'Company Registration')
    ]
    
    print("🚀 Testing Core Routes")
    print("-" * 30)
    
    for route, name in routes:
        try:
            response = requests.get(f"{BASE_URL}{route}")
            status = "✅ PASS" if response.status_code in [200, 302] else "❌ FAIL"
            print(f"{status} - {name} ({response.status_code})")
        except Exception as e:
            print(f"❌ FAIL - {name} (Error: {e})")

def test_manual_registration():
    """Manual test - show registration form works"""
    print("\n🔐 Registration Form Test")
    print("-" * 30)
    
    try:
        response = requests.get(f"{BASE_URL}/register_company")
        if response.status_code == 200:
            has_form = "form" in response.text.lower()
            has_fields = all(field in response.text.lower() for field in ['name', 'email', 'founder'])
            
            if has_form and has_fields:
                print("✅ PASS - Registration form is properly rendered")
                print("   → Form elements detected")
                print("   → Required fields present")
            else:
                print("❌ FAIL - Registration form incomplete")
        else:
            print(f"❌ FAIL - Registration page not accessible ({response.status_code})")
    except Exception as e:
        print(f"❌ FAIL - Registration test error: {e}")

def test_database_models():
    """Test if we can access model routes without errors"""
    print("\n🗄️  Database Model Test")
    print("-" * 30)
    
    # These routes should not crash even without authentication
    test_routes = [
        ('/dashboard', 'Dashboard Route'),
        ('/founder_dashboard', 'Founder Dashboard Route'),
    ]
    
    for route, name in test_routes:
        try:
            response = requests.get(f"{BASE_URL}{route}")
            # Should redirect to login (302) or show page (200), not crash (500)
            if response.status_code in [200, 302]:
                print(f"✅ PASS - {name} (No model errors)")
            elif response.status_code == 500:
                print(f"❌ FAIL - {name} (Database/Model error)")
            else:
                print(f"🟡 WARN - {name} ({response.status_code})")
        except Exception as e:
            print(f"❌ FAIL - {name} (Error: {e})")

def main():
    print("🏥 RahaSoft ERP - Quick Health Check")
    print("=" * 40)
    
    start_time = time.time()
    
    test_basic_routes()
    test_manual_registration()
    test_database_models()
    
    end_time = time.time()
    
    print(f"\n⏱️  Test completed in {end_time - start_time:.2f} seconds")
    print("\n💡 Next Steps:")
    print("   1. Try registering a company manually")
    print("   2. Login with founder credentials") 
    print("   3. Access founder dashboard")
    print("   4. Test core ERP modules")

if __name__ == "__main__":
    main()
