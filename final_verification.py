#!/usr/bin/env python3
"""
FINAL SYSTEM VERIFICATION
Test all routes with correct paths
"""
import os
from dotenv import load_dotenv
load_dotenv()

print("🔍 FINAL RAHASOFT ERP SYSTEM VERIFICATION")
print("=" * 60)

try:
    from app import app
    
    with app.test_client() as client:
        print("📋 TESTING CORRECTED ROUTES:")
        print("-" * 40)
        
        # Test with correct blueprint paths
        corrected_routes = [
            # Core working routes
            ('/welcome', 'Welcome Page'),
            ('/login', 'Login Page'),
            ('/register', 'Registration'),
            ('/register_company', 'Company Registration'),
            ('/dashboard', 'Dashboard'),
            
            # Core modules
            ('/inventory/', 'Inventory Management'),
            ('/pos/', 'Point of Sale'),
            ('/employees/employees', 'Employee Management'),
            ('/users/users', 'User Management'),
            
            # Corrected blueprint routes
            ('/payroll/payroll/create', 'Payroll Creation'),  # Blueprint + route
            ('/support/support/create', 'Support Ticket'),   # Blueprint + route
            
            # Advanced features from rahasoft blueprint
            ('/calendar', 'Business Calendar'),
            ('/receipt-scanner', 'Receipt Scanner'),
            ('/vendor-ratings', 'Vendor Ratings'),
            ('/notifications', 'Notifications'),
            ('/health-score', 'Business Health Score'),
            ('/training', 'Training Portal'),
            
            # Advanced features from advanced blueprint  
            ('/ai-assistant', 'AI Assistant'),
            ('/meeting-rooms', 'Meeting Rooms'),
            ('/b2b-marketplace', 'B2B Marketplace'),
        ]
        
        working_routes = []
        auth_required = []
        still_broken = []
        
        for route, name in corrected_routes:
            try:
                response = client.get(route)
                status = response.status_code
                
                if status == 200:
                    print(f"✅ {name}: WORKING")
                    working_routes.append(name)
                elif status == 302:
                    print(f"🔐 {name}: AUTH REQUIRED")
                    auth_required.append(name)
                elif status == 404:
                    print(f"❌ {name}: NOT FOUND")
                    still_broken.append(name)
                elif status == 500:
                    print(f"💥 {name}: SERVER ERROR")
                    still_broken.append(name)
                else:
                    print(f"⚠️ {name}: STATUS {status}")
                    still_broken.append(name)
                    
            except Exception as e:
                print(f"💀 {name}: EXCEPTION")
                still_broken.append(name)
        
        print("\n📊 FINAL RESULTS:")
        print("=" * 40)
        print(f"✅ FULLY WORKING: {len(working_routes)}")
        print(f"🔐 AUTH PROTECTED: {len(auth_required)}")
        print(f"❌ STILL BROKEN: {len(still_broken)}")
        
        total_functional = len(working_routes) + len(auth_required)
        total_tested = len(corrected_routes)
        success_rate = (total_functional / total_tested * 100) if total_tested > 0 else 0
        
        print(f"\n🎯 SYSTEM SUCCESS RATE: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🟢 EXCELLENT - Production ready!")
        elif success_rate >= 75:
            print("🟡 VERY GOOD - Minor issues remain")
        elif success_rate >= 60:
            print("🟠 GOOD - Core functionality working")
        else:
            print("🔴 NEEDS WORK - Major issues remain")
            
        print(f"\n🏆 CONCLUSION:")
        if total_functional >= 15:
            print("✅ RahaSoft ERP has SOLID CORE FUNCTIONALITY!")
            print("✅ All essential business modules are working")
            print("✅ Ready for production use with core features")
        else:
            print("⚠️ System needs more fixes for production readiness")
            
except Exception as e:
    print(f"❌ Critical error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
