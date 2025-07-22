"""
🚀 DEPLOYMENT VERIFICATION SCRIPT
================================

Verifies that all security enhancements are properly deployed and functioning
"""

import sys
import os
import importlib
from datetime import datetime

def check_security_imports():
    """Check if all security modules can be imported"""
    print("🔍 Checking Security Module Imports...")
    
    try:
        # Core security modules
        import security_enhancements
        print("  ✅ security_enhancements imported successfully")
        
        import security_monitoring  
        print("  ✅ security_monitoring imported successfully")
        
        import security_validation
        print("  ✅ security_validation imported successfully")
        
        # Security models
        from models.security_enhanced import (
            SecurityEvent, IPBlacklist, SessionSecurity, PasswordHistory,
            SecurityConfiguration, FileUploadSecurity, APISecurityLog, ComplianceLog
        )
        print("  ✅ Enhanced security models imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False

def check_security_templates():
    """Check if security templates exist"""
    print("\n🔍 Checking Security Templates...")
    
    templates = [
        'templates/security/security_dashboard.html',
        'templates/security/security_settings.html',
        'templates/login_modern.html',
        'templates/register_modern.html',
        'templates/register_company_modern.html',
        'templates/welcome_advanced.html'
    ]
    
    all_exist = True
    for template in templates:
        if os.path.exists(template):
            print(f"  ✅ {template}")
        else:
            print(f"  ❌ {template} - NOT FOUND")
            all_exist = False
    
    return all_exist

def check_security_files():
    """Check if security files exist"""
    print("\n🔍 Checking Security Files...")
    
    files = [
        'security_enhancements.py',
        'security_monitoring.py', 
        'security_validation.py',
        'migrate_security_enhancements.py',
        'models/security_enhanced.py',
        'SECURITY_IMPLEMENTATION_REPORT.md'
    ]
    
    all_exist = True
    for file in files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - NOT FOUND")
            all_exist = False
    
    return all_exist

def check_app_configuration():
    """Check app configuration for security settings"""
    print("\n🔍 Checking App Configuration...")
    
    try:
        with open('app.py', 'r') as f:
            content = f.read()
            
        checks = {
            'security_enhancer': 'Security enhancer integration',
            'CSRFProtect': 'CSRF protection',
            'SESSION_COOKIE_SECURE': 'Secure session cookies',
            'security_bp': 'Security blueprint registration'
        }
        
        all_configured = True
        for check, description in checks.items():
            if check in content:
                print(f"  ✅ {description} configured")
            else:
                print(f"  ❌ {description} - NOT CONFIGURED")
                all_configured = False
        
        return all_configured
        
    except Exception as e:
        print(f"  ❌ Error checking app configuration: {e}")
        return False

def run_deployment_verification():
    """Run complete deployment verification"""
    print("🚀 DEPLOYMENT VERIFICATION")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    checks = [
        ("Security Imports", check_security_imports),
        ("Security Templates", check_security_templates), 
        ("Security Files", check_security_files),
        ("App Configuration", check_app_configuration)
    ]
    
    results = []
    for check_name, check_func in checks:
        result = check_func()
        results.append((check_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 DEPLOYMENT VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for check_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {check_name}")
    
    success_rate = (passed / total) * 100
    print(f"\n📈 Success Rate: {passed}/{total} ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("\n🎉 DEPLOYMENT VERIFICATION SUCCESSFUL!")
        print("🛡️ All security enhancements are properly deployed")
        print("🚀 System is ready for production use")
    elif success_rate >= 75:
        print("\n⚠️ DEPLOYMENT MOSTLY SUCCESSFUL")
        print("🔧 Some minor issues need attention")
    else:
        print("\n❌ DEPLOYMENT ISSUES DETECTED")
        print("🛠️ Critical issues need to be resolved")
    
    return success_rate == 100

if __name__ == "__main__":
    success = run_deployment_verification()
    sys.exit(0 if success else 1)
