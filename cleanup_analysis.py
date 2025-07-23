#!/usr/bin/env python3
"""
Project Cleanup Script - Remove duplicates and unnecessary files
This script identifies files that can be safely removed to clean up the project.
"""

import os
import glob

def cleanup_project():
    """Identify files for removal"""
    
    print("🧹 RAHASOFT PROJECT CLEANUP ANALYSIS")
    print("=" * 50)
    
    # Files to remove (testing, debugging, temporary)
    files_to_remove = [
        # Testing files
        "test_*.py",
        "debug_*.py", 
        "check_*.py",
        "verify_*.py",
        "diagnose_*.py",
        
        # Temporary/duplicate files
        "clean_welcome.py",
        "create_test_*.py", 
        "delete_all_users.py",
        "manual_check.py",
        "quick_health_check.py",
        "comprehensive_system_test.py",
        "final_system_test.py",
        "SYSTEM_STATUS_FINAL.py",
        
        # Database setup duplicates (keep setup_database.py)
        "migrate_database.py",
        "postgres_setup_helper.py",
        "setup_rahasoft_users.py",
        
        # App startup duplicates (keep app.py)
        "run_app.py",
        "start_app.py", 
        "flask_dev_server.py",
        "start_flask_cli.py",
        
        # Batch files (Windows specific, keep .ps1)
        "fix_flask.bat",
        "flask_run.bat", 
        "start_rahasoft.bat",
        
        # Documentation duplicates
        "COMPANY_FEATURES_COMPLETE.md",
        "DEPLOYMENT_COMPLETE.md", 
        "FULL_TEST_RESULTS.md",
        "NEW_FEATURES_DOCUMENTATION.md",
        "RAHASOFT_MODULES_COMPLETE.md",
        "SECURITY_IMPLEMENTATION_REPORT.md",
        "WORKFLOW_MODULE_COMPLETE.md",
        
        # Test results
        "test_results*.json",
        
        # Supabase files (using PostgreSQL)
        "supabase_rls_policies.sql",
        "test_supabase_connection.py",
    ]
    
    # Files to keep (essential)
    essential_files = [
        "app.py",  # Main application
        "extensions.py",  # Flask extensions
        "forms.py",  # Forms (if used)
        "helpers.py",  # Helper functions
        "mpesa.py",  # Payment integration
        "security_enhancements.py",  # Security features
        "security_monitoring.py",  # Security monitoring
        "security_validation.py",  # Security validation
        "setup_database.py",  # Database setup
        "requirements.txt",  # Dependencies
        "README.md",  # Documentation
        "CONTRIBUTING.md",  # Contribution guide
        "ENTERPRISE_DEPLOYMENT_GUIDE.md",  # Important docs
        "FLASK_COMMANDS.md",  # Flask commands
        ".env",  # Environment variables
        ".env.example",  # Environment template
        ".gitignore",  # Git ignore
        "Procfile",  # Deployment
        "flask_run.ps1",  # PowerShell script
        "start_flask.ps1",  # PowerShell script
    ]
    
    print("\n📋 FILES RECOMMENDED FOR REMOVAL:")
    print("-" * 40)
    
    removal_count = 0
    for pattern in files_to_remove:
        matches = glob.glob(pattern)
        for file in matches:
            if os.path.exists(file):
                print(f"❌ {file}")
                removal_count += 1
    
    print(f"\n📊 CLEANUP SUMMARY:")
    print(f"• Files to remove: {removal_count}")
    print(f"• Essential files: {len(essential_files)}")
    
    print(f"\n🗂️ ESSENTIAL FILES TO KEEP:")
    print("-" * 30)
    for file in essential_files:
        if os.path.exists(file):
            print(f"✅ {file}")
    
    print(f"\n📁 ESSENTIAL DIRECTORIES:")
    print("-" * 25)
    essential_dirs = [
        "forms/",
        "models/", 
        "routes/",
        "templates/",
        "static/",
        "migrations/",
        "utils/",
        "translations/",
        "instance/"
    ]
    
    for dir_name in essential_dirs:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name}")
    
    print(f"\n💡 RECOMMENDATION:")
    print("Run the following commands to clean up:")
    print("1. Remove testing files:")
    for pattern in ["test_*.py", "debug_*.py", "check_*.py", "verify_*.py"]:
        print(f"   rm {pattern}")
    
    print("2. Remove temporary files:")
    temp_files = [
        "clean_welcome.py", "manual_check.py", "quick_health_check.py",
        "comprehensive_system_test.py", "final_system_test.py"
    ]
    for file in temp_files:
        print(f"   rm {file}")
    
    print("3. Remove duplicate documentation:")
    docs = [
        "COMPANY_FEATURES_COMPLETE.md", "DEPLOYMENT_COMPLETE.md",
        "FULL_TEST_RESULTS.md", "RAHASOFT_MODULES_COMPLETE.md"
    ]
    for file in docs:
        print(f"   rm {file}")

if __name__ == "__main__":
    cleanup_project()
