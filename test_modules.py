#!/usr/bin/env python3
"""
Test module routes and functionality
"""
import os
from dotenv import load_dotenv
load_dotenv()

try:
    from app import app
    print("✅ App imported successfully")
    
    with app.test_client() as client:
        print("\n🔍 Testing Module Routes...")
        
        # Test core module routes
        test_routes = [
            ('/', 'Root/Home'),
            ('/welcome', 'Welcome Page'),
            ('/register_company', 'Company Registration'),
            ('/dashboard', 'Dashboard'),
            ('/inventory/', 'Inventory Module'),
            ('/pos/', 'Point of Sale'),
            ('/employees/employees', 'Employee Management'),  # Blueprint route with prefix
            ('/payroll/payroll', 'Payroll Module'),  # Blueprint route with prefix
            ('/support/support', 'Support Module'),  # Blueprint route with prefix
            ('/users/users', 'User Management'),  # Blueprint route with prefix
        ]
        
        for route, name in test_routes:
            try:
                response = client.get(route)
                status = "✅" if response.status_code in [200, 302, 401] else "❌"
                print(f"{status} {name}: {response.status_code}")
                if response.status_code >= 400 and response.status_code not in [401, 403]:
                    print(f"   Error: {response.status_code}")
            except Exception as e:
                print(f"❌ {name}: Error - {str(e)[:50]}")
        
        print("\n🔍 Testing Advanced Routes...")
        advanced_routes = [
            ('/calendar', 'Business Calendar'),
            ('/receipt-scanner', 'Receipt Scanner'),
            ('/ai-assistant', 'AI Assistant'),
            ('/meeting-rooms', 'Meeting Rooms'),
            ('/b2b-marketplace', 'B2B Marketplace'),
        ]
        
        for route, name in advanced_routes:
            try:
                response = client.get(route)
                status = "✅" if response.status_code in [200, 302, 401] else "❌"
                print(f"{status} {name}: {response.status_code}")
            except Exception as e:
                print(f"❌ {name}: Error - {str(e)[:50]}")
                
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
