#!/usr/bin/env python3
"""
COMPREHENSIVE RAHASOFT ERP SYSTEM DIAGNOSTIC
This script will test every aspect of the system and identify all issues
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

print("=" * 70)
print("🔍 RAHASOFT ERP SYSTEM DIAGNOSTIC REPORT")
print("=" * 70)
print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Load environment
load_dotenv()

# 1. IMPORT AND APP INITIALIZATION CHECK
print("1️⃣ SYSTEM IMPORTS & INITIALIZATION")
print("-" * 50)
try:
    from app import app, db
    print("✅ Flask app imported successfully")
    
    with app.app_context():
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        table_count = len(inspector.get_table_names())
        print(f"✅ Database connected: {table_count} tables found")
        
        # Check critical models
        try:
            from models.user import User
            from models.company import Company
            from models.product import Product
            print("✅ Core models imported successfully")
        except Exception as e:
            print(f"❌ Model import error: {e}")
            
except Exception as e:
    print(f"❌ CRITICAL: App initialization failed: {e}")
    sys.exit(1)

print()

# 2. BLUEPRINT REGISTRATION CHECK
print("2️⃣ BLUEPRINT REGISTRATION STATUS")
print("-" * 50)
with app.app_context():
    registered_blueprints = list(app.blueprints.keys())
    print(f"📦 Total blueprints registered: {len(registered_blueprints)}")
    for bp_name in registered_blueprints:
        print(f"  ✅ {bp_name}")
    
    if not registered_blueprints:
        print("❌ No blueprints registered!")

print()

# 3. ROUTE MAPPING CHECK
print("3️⃣ ROUTE MAPPING ANALYSIS")
print("-" * 50)
with app.test_client() as client:
    # Define all expected routes
    test_routes = {
        'Core Pages': [
            ('/', 'Root'),
            ('/welcome', 'Welcome Page'),
            ('/login', 'Login Page'),
            ('/register', 'Registration'),
            ('/register_company', 'Company Registration'),
            ('/dashboard', 'Dashboard'),
        ],
        'Core Modules': [
            ('/inventory/', 'Inventory Management'),
            ('/pos/', 'Point of Sale'),
            ('/stock_management/', 'Stock Management'),
            ('/purchasing/', 'Purchasing'),
            ('/warehouse/', 'Warehouse'),
            ('/order_management/', 'Order Management'),
        ],
        'Blueprint Routes': [
            ('/employees/employees', 'Employee Management'),
            ('/payroll/payroll', 'Payroll'),
            ('/support/support', 'Support'),
            ('/users/users', 'User Management'),
        ],
        'Advanced Features': [
            ('/calendar', 'Business Calendar'),
            ('/receipt-scanner', 'Receipt Scanner'),
            ('/ai-assistant', 'AI Assistant'),
            ('/meeting-rooms', 'Meeting Rooms'),
            ('/b2b-marketplace', 'B2B Marketplace'),
            ('/vendor-ratings', 'Vendor Ratings'),
            ('/notifications', 'Notifications'),
            ('/health-score', 'Business Health'),
            ('/training', 'Training Portal'),
        ]
    }
    
    all_working = []
    all_broken = []
    all_missing_templates = []
    
    for category, routes in test_routes.items():
        print(f"\n📂 {category}:")
        for route, name in routes:
            try:
                response = client.get(route)
                status = response.status_code
                
                if status == 200:
                    print(f"  ✅ {name}: {status} (Working)")
                    all_working.append((route, name))
                elif status == 302:
                    print(f"  🔄 {name}: {status} (Redirect - Auth required)")
                    all_working.append((route, name))
                elif status == 404:
                    print(f"  ❌ {name}: {status} (Route not found)")
                    all_broken.append((route, name, "Route missing"))
                elif status == 500:
                    print(f"  💥 {name}: {status} (Server error)")
                    error_content = response.data.decode('utf-8')
                    if 'TemplateNotFound' in error_content:
                        print(f"     📄 Missing template error")
                        all_missing_templates.append((route, name))
                    else:
                        all_broken.append((route, name, "Server error"))
                else:
                    print(f"  ⚠️ {name}: {status} (Unexpected)")
                    all_broken.append((route, name, f"Status {status}"))
                    
            except Exception as e:
                print(f"  💀 {name}: Exception - {str(e)[:50]}")
                all_broken.append((route, name, str(e)))

print("\n")

# 4. TEMPLATE ANALYSIS
print("4️⃣ TEMPLATE STRUCTURE ANALYSIS")
print("-" * 50)
template_dir = "templates"
if os.path.exists(template_dir):
    print(f"📁 Template directory found: {template_dir}")
    
    # Check critical templates
    critical_templates = [
        'base.html',
        'welcome.html',
        'login.html',
        'register.html',
        'register_company.html',
        'dashboard.html',
        'errors/404.html',
        'errors/500.html',
    ]
    
    missing_critical = []
    for template in critical_templates:
        template_path = os.path.join(template_dir, template)
        if os.path.exists(template_path):
            print(f"  ✅ {template}")
        else:
            print(f"  ❌ {template} (MISSING)")
            missing_critical.append(template)
    
    # Check module templates
    print(f"\n📂 Module Templates:")
    modules_dir = os.path.join(template_dir, "modules")
    if os.path.exists(modules_dir):
        module_templates = os.listdir(modules_dir)
        print(f"  📦 Found {len(module_templates)} module templates:")
        for template in module_templates:
            print(f"    ✅ {template}")
    else:
        print("  ❌ modules/ directory missing")
        
else:
    print(f"❌ Template directory not found: {template_dir}")

print()

# 5. DATABASE HEALTH CHECK
print("5️⃣ DATABASE HEALTH CHECK")
print("-" * 50)
try:
    with app.app_context():
        # Test database connection
        tables = inspector.get_table_names()
        print(f"✅ Database connection healthy")
        print(f"📊 Tables: {', '.join(tables)}")
        
        # Test basic queries
        try:
            from models.user import User
            user_count = User.query.count()
            print(f"👥 Users in database: {user_count}")
        except Exception as e:
            print(f"❌ User query failed: {e}")
            
        try:
            from models.company import Company
            company_count = Company.query.count()
            print(f"🏢 Companies in database: {company_count}")
        except Exception as e:
            print(f"❌ Company query failed: {e}")
            
except Exception as e:
    print(f"❌ Database health check failed: {e}")

print()

# 6. ENVIRONMENT CONFIGURATION CHECK
print("6️⃣ ENVIRONMENT CONFIGURATION")
print("-" * 50)
critical_env_vars = [
    'SECRET_KEY',
    'SQLALCHEMY_DATABASE_URI',
    'SMTP_SERVER',
    'SMTP_USERNAME',
    'FROM_EMAIL'
]

for var in critical_env_vars:
    value = os.getenv(var)
    if value:
        # Mask sensitive values
        if 'PASSWORD' in var or 'SECRET' in var:
            display_value = f"{value[:5]}***{value[-3:]}" if len(value) > 8 else "***"
        else:
            display_value = value[:50] + "..." if len(value) > 50 else value
        print(f"  ✅ {var}: {display_value}")
    else:
        print(f"  ❌ {var}: NOT SET")

print()

# 7. SUMMARY REPORT
print("7️⃣ SYSTEM HEALTH SUMMARY")
print("=" * 50)
print(f"✅ WORKING ROUTES: {len(all_working)}")
print(f"💥 BROKEN ROUTES: {len(all_broken)}")
print(f"📄 MISSING TEMPLATES: {len(all_missing_templates)}")

if all_working:
    print(f"\n🟢 FUNCTIONAL MODULES ({len(all_working)}):")
    for route, name in all_working:
        print(f"  ✅ {name}")

if all_missing_templates:
    print(f"\n🟡 ROUTES WITH MISSING TEMPLATES ({len(all_missing_templates)}):")
    for route, name in all_missing_templates:
        print(f"  📄 {name} -> Missing template")

if all_broken:
    print(f"\n🔴 BROKEN ROUTES ({len(all_broken)}):")
    for route, name, error in all_broken:
        print(f"  ❌ {name} -> {error}")

# Overall system health percentage
total_routes = len(all_working) + len(all_broken) + len(all_missing_templates)
working_percentage = (len(all_working) / total_routes * 100) if total_routes > 0 else 0

print(f"\n🎯 OVERALL SYSTEM HEALTH: {working_percentage:.1f}%")

if working_percentage >= 80:
    print("🟢 EXCELLENT - System is highly functional")
elif working_percentage >= 60:
    print("🟡 GOOD - System has core functionality")
elif working_percentage >= 40:
    print("🟠 FAIR - System needs attention")
else:
    print("🔴 POOR - System requires major fixes")

print("\n" + "=" * 70)
print("🏁 DIAGNOSTIC COMPLETE")
print("=" * 70)
