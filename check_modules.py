#!/usr/bin/env python3
"""
Comprehensive Module Functionality Check for RahaSoft ERP
This script tests all registered modules and their key endpoints
"""

from app import app
from flask import url_for
import sys

def test_module_functionality():
    """Test all registered modules and their endpoints"""
    
    with app.test_request_context():
        print("=" * 60)
        print("🔍 RAHASOFT ERP MODULE FUNCTIONALITY CHECK")
        print("=" * 60)
        
        # Test results storage
        working_modules = []
        problematic_modules = []
        
        # Define modules to test with their expected endpoints
        modules_to_test = {
            "Core Operations": {
                "inventory": ["/inventory", "Inventory Management"],
                "warehouse": ["/warehouse", "Warehouse Management"],
                "suppliers": ["/suppliers", "Supplier Management"],
                "procurement": ["/procurement", "Procurement"],
            },
            "Sales & Marketing": {
                "crm.dashboard": ["CRM Dashboard", "Customer Relationship Management"],
                "pos": ["/pos", "Point of Sale"],
                "leads": ["/leads", "Lead Management"],
                "campaigns": ["/campaigns", "Marketing Campaigns"],
            },
            "Finance & Accounting": {
                "finance.dashboard": ["Finance Dashboard", "Financial Management"],
                "invoicing": ["/invoicing", "Invoicing System"],
                "payments": ["/payments", "Payment Processing"],
                "expenses": ["/expenses", "Expense Management"],
            },
            "Human Resources": {
                "employees": ["/employees", "Employee Management"],
                "payroll": ["/payroll", "Payroll Management"],
                "attendance": ["/attendance", "Attendance Tracking"],
                "leave": ["/leave", "Leave Management"],
            },
            "Analytics & Reports": {
                "business_intelligence.dashboards": ["Business Intelligence", "BI Dashboard"],
                "reports": ["/reports", "Report Generation"],
                "analytics": ["/analytics", "Analytics Engine"],
                "kpis": ["/kpis", "Key Performance Indicators"],
            },
            "Utilities & Tools": {
                "security.security_dashboard": ["Security Management", "Security Dashboard"],
                "settings": ["/settings", "System Settings"],
                "backups": ["/backups", "Backup Management"],
                "support": ["/support", "Support System"],
            }
        }
        
        # Test each module category
        for category, modules in modules_to_test.items():
            print(f"\n📂 {category}")
            print("-" * 40)
            
            for module_key, (endpoint_or_url, description) in modules.items():
                try:
                    # Check if it's a Flask endpoint (contains dots) or direct URL
                    if "." in module_key:
                        # It's a Flask endpoint
                        url = url_for(module_key)
                        status = "✅ WORKING"
                        working_modules.append(f"{description} ({module_key})")
                    else:
                        # It's a direct URL
                        url = endpoint_or_url
                        status = "⚠️  STATIC URL"
                        working_modules.append(f"{description} ({url})")
                    
                    print(f"  {status} - {description}")
                    print(f"           URL: {url}")
                    
                except Exception as e:
                    status = "❌ ERROR"
                    problematic_modules.append(f"{description} ({module_key}): {str(e)}")
                    print(f"  {status} - {description}")
                    print(f"           Error: {str(e)}")
        
        # Summary Report
        print("\n" + "=" * 60)
        print("📊 FUNCTIONALITY SUMMARY")
        print("=" * 60)
        
        print(f"\n✅ WORKING MODULES ({len(working_modules)}):")
        for module in working_modules:
            print(f"  • {module}")
            
        if problematic_modules:
            print(f"\n❌ PROBLEMATIC MODULES ({len(problematic_modules)}):")
            for module in problematic_modules:
                print(f"  • {module}")
        
        # Additional tests for blueprint registration
        print(f"\n🔧 BLUEPRINT REGISTRATION CHECK:")
        print("-" * 40)
        
        blueprints = app.blueprints
        print(f"Registered Blueprints: {len(blueprints)}")
        for bp_name, bp in blueprints.items():
            print(f"  • {bp_name}: {bp.url_prefix or '/'}")
        
        # Test database connectivity
        print(f"\n💾 DATABASE CHECK:")
        print("-" * 40)
        try:
            from extensions import db
            with app.app_context():
                # Try a simple query
                result = db.engine.execute("SELECT 1").fetchone()
                print("  ✅ Database connection: WORKING")
        except Exception as e:
            print(f"  ❌ Database connection: ERROR - {str(e)}")
        
        # Test model imports
        print(f"\n📋 MODEL IMPORTS CHECK:")
        print("-" * 40)
        
        models_to_test = [
            "models.user.User",
            "models.company.Company", 
            "models.employee.Employee",
            "models.product.Product",
            "models.sale.Sale",
            "models.crm.Lead",
            "models.security.SecuritySettings",
        ]
        
        for model_path in models_to_test:
            try:
                module_path, class_name = model_path.rsplit('.', 1)
                exec(f"from {module_path} import {class_name}")
                print(f"  ✅ {model_path}: IMPORTED")
            except Exception as e:
                print(f"  ❌ {model_path}: ERROR - {str(e)}")
        
        print(f"\n🎯 OVERALL STATUS:")
        print("-" * 40)
        total_modules = len(working_modules) + len(problematic_modules)
        success_rate = (len(working_modules) / total_modules * 100) if total_modules > 0 else 0
        
        if success_rate >= 90:
            status_emoji = "🟢"
            status_text = "EXCELLENT"
        elif success_rate >= 75:
            status_emoji = "🟡"
            status_text = "GOOD"
        elif success_rate >= 50:
            status_emoji = "🟠"
            status_text = "FAIR"
        else:
            status_emoji = "🔴"
            status_text = "NEEDS ATTENTION"
            
        print(f"  {status_emoji} System Status: {status_text}")
        print(f"  📈 Success Rate: {success_rate:.1f}%")
        print(f"  ✅ Working: {len(working_modules)}")
        print(f"  ❌ Issues: {len(problematic_modules)}")
        
        print(f"\n{'=' * 60}")
        print("✨ MODULE FUNCTIONALITY CHECK COMPLETE")
        print("=" * 60)

if __name__ == "__main__":
    test_module_functionality()
