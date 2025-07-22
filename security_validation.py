"""
🔒 COMPREHENSIVE SECURITY VALIDATION SCRIPT
==========================================

Validates the security implementation and checks for vulnerabilities
Provides recommendations for improving security posture
"""

import os
import re
import hashlib
import secrets
from datetime import datetime
from pathlib import Path
import subprocess
import sys

class SecurityValidator:
    """Comprehensive security validation tool"""
    
    def __init__(self):
        self.vulnerabilities = []
        self.warnings = []
        self.passed_checks = []
        self.security_score = 0
        self.max_score = 0
    
    def run_all_checks(self):
        """Run all security validation checks"""
        print("🔒 COMPREHENSIVE SECURITY VALIDATION")
        print("=" * 50)
        
        self.check_environment_security()
        self.check_database_security()
        self.check_application_security()
        self.check_dependency_security()
        self.check_configuration_security()
        self.check_input_validation()
        self.check_authentication_security()
        self.check_session_security()
        self.check_file_security()
        
        self.generate_security_report()
    
    def check_environment_security(self):
        """Check environment variable security"""
        print("\n🔍 Checking Environment Security...")
        
        env_file = Path('.env')
        if env_file.exists():
            self.add_pass("Environment file found")
            
            # Check for sensitive data exposure
            with open(env_file, 'r') as f:
                content = f.read()
                
                # Check for weak secret keys
                secret_key_match = re.search(r'SECRET_KEY\s*=\s*["\']?([^"\']+)["\']?', content)
                if secret_key_match:
                    secret_key = secret_key_match.group(1)
                    if len(secret_key) < 32:
                        self.add_vulnerability("SECRET_KEY is too short (< 32 characters)")
                    elif secret_key == 'fallback-secret-key':
                        self.add_vulnerability("Using default/fallback SECRET_KEY")
                    else:
                        self.add_pass("SECRET_KEY is sufficiently long")
                
                # Check for database URL security
                if 'postgresql' in content and 'sslmode=require' not in content:
                    self.add_warning("Database connection should enforce SSL")
                
                # Check for debug mode
                if re.search(r'DEBUG\s*=\s*True', content, re.IGNORECASE):
                    self.add_vulnerability("Debug mode is enabled in production")
        else:
            self.add_warning("No .env file found - ensure environment variables are set securely")
    
    def check_database_security(self):
        """Check database security configuration"""
        print("\n🔍 Checking Database Security...")
        
        # Check for SQL injection prevention
        python_files = list(Path('.').rglob('*.py'))
        sql_injection_patterns = [
            r'query\s*=\s*["\'].*%.*["\']',  # String formatting in queries
            r'\.execute\s*\(["\'].*\+.*["\']',  # String concatenation in execute
            r'\.raw\s*\(["\'].*\+.*["\']',  # Raw queries with concatenation
        ]
        
        vulnerable_files = []
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for pattern in sql_injection_patterns:
                        if re.search(pattern, content):
                            vulnerable_files.append(str(file_path))
                            break
            except:
                continue
        
        if vulnerable_files:
            self.add_vulnerability(f"Potential SQL injection vulnerabilities in: {vulnerable_files[:3]}")
        else:
            self.add_pass("No obvious SQL injection vulnerabilities found")
    
    def check_application_security(self):
        """Check Flask application security"""
        print("\n🔍 Checking Application Security...")
        
        # Check for CSRF protection
        app_py = Path('app.py')
        if app_py.exists():
            with open(app_py, 'r') as f:
                content = f.read()
                
                if 'CSRFProtect' in content:
                    self.add_pass("CSRF protection is enabled")
                else:
                    self.add_vulnerability("CSRF protection not found")
                
                # Check for security headers
                if 'security_enhancer' in content:
                    self.add_pass("Security enhancements are integrated")
                else:
                    self.add_warning("Security enhancements not integrated")
                
                # Check for debug mode
                if re.search(r'debug\s*=\s*True', content, re.IGNORECASE):
                    self.add_vulnerability("Debug mode is enabled")
                
                # Check for secure session configuration
                if 'SESSION_COOKIE_SECURE' in content:
                    self.add_pass("Secure session cookies configured")
                else:
                    self.add_warning("Session cookie security not explicitly configured")
    
    def check_dependency_security(self):
        """Check for vulnerable dependencies"""
        print("\n🔍 Checking Dependency Security...")
        
        requirements_file = Path('requirements.txt')
        if requirements_file.exists():
            self.add_pass("Requirements file found")
            
            # Check for known vulnerable packages (simplified check)
            vulnerable_packages = {
                'flask<2.0': 'Upgrade Flask to 2.0+ for security fixes',
                'sqlalchemy<1.4': 'Upgrade SQLAlchemy for security improvements',
                'werkzeug<2.0': 'Upgrade Werkzeug for security fixes',
            }
            
            with open(requirements_file, 'r') as f:
                content = f.read().lower()
                
                for vuln_package, message in vulnerable_packages.items():
                    if vuln_package.split('<')[0] in content:
                        # This is a simplified check - in production, use pip-audit or safety
                        self.add_warning(f"Check for updates: {message}")
        else:
            self.add_warning("No requirements.txt found")
    
    def check_configuration_security(self):
        """Check security configuration"""
        print("\n🔍 Checking Configuration Security...")
        
        # Check for hardcoded secrets
        python_files = list(Path('.').rglob('*.py'))
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
        ]
        
        files_with_secrets = []
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for pattern in secret_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            # Exclude common false positives
                            if 'test' not in str(file_path).lower() and 'example' not in content.lower():
                                files_with_secrets.append(str(file_path))
                                break
            except:
                continue
        
        if files_with_secrets:
            self.add_warning(f"Potential hardcoded secrets in: {files_with_secrets[:3]}")
        else:
            self.add_pass("No obvious hardcoded secrets found")
    
    def check_input_validation(self):
        """Check input validation implementation"""
        print("\n🔍 Checking Input Validation...")
        
        # Check for WTForms usage
        forms_dir = Path('forms')
        if forms_dir.exists():
            form_files = list(forms_dir.glob('*.py'))
            
            validation_found = False
            for form_file in form_files:
                try:
                    with open(form_file, 'r') as f:
                        content = f.read()
                        if 'validators' in content and 'DataRequired' in content:
                            validation_found = True
                            break
                except:
                    continue
            
            if validation_found:
                self.add_pass("Input validation using WTForms found")
            else:
                self.add_warning("Limited input validation found")
        else:
            self.add_warning("No forms directory found")
    
    def check_authentication_security(self):
        """Check authentication security"""
        print("\n🔍 Checking Authentication Security...")
        
        # Check for proper password hashing
        user_model = Path('models/user.py')
        if user_model.exists():
            with open(user_model, 'r') as f:
                content = f.read()
                
                if 'generate_password_hash' in content and 'check_password_hash' in content:
                    self.add_pass("Proper password hashing implemented")
                else:
                    self.add_vulnerability("Password hashing not properly implemented")
                
                # Check for 2FA implementation
                security_model = Path('models/security.py')
                if security_model.exists():
                    with open(security_model, 'r') as f:
                        security_content = f.read()
                        if 'TwoFactorAuth' in security_content:
                            self.add_pass("Two-factor authentication implemented")
                        else:
                            self.add_warning("Two-factor authentication not found")
    
    def check_session_security(self):
        """Check session security configuration"""
        print("\n🔍 Checking Session Security...")
        
        # Check app.py for session configuration
        app_py = Path('app.py')
        if app_py.exists():
            with open(app_py, 'r') as f:
                content = f.read()
                
                session_checks = {
                    'SESSION_COOKIE_SECURE': 'Secure cookies for HTTPS',
                    'SESSION_COOKIE_HTTPONLY': 'HTTP-only cookies',
                    'SESSION_COOKIE_SAMESITE': 'SameSite cookie protection',
                }
                
                for config, description in session_checks.items():
                    if config in content:
                        self.add_pass(f"{description} configured")
                    else:
                        self.add_warning(f"{description} not configured")
    
    def check_file_security(self):
        """Check file upload and handling security"""
        print("\n🔍 Checking File Security...")
        
        # Check for file upload validation
        upload_patterns = [
            r'secure_filename',
            r'allowed_file',
            r'UPLOAD_FOLDER',
        ]
        
        python_files = list(Path('.').rglob('*.py'))
        upload_security_found = False
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    for pattern in upload_patterns:
                        if re.search(pattern, content):
                            upload_security_found = True
                            break
                if upload_security_found:
                    break
            except:
                continue
        
        if upload_security_found:
            self.add_pass("File upload security measures found")
        else:
            self.add_warning("File upload security not implemented")
    
    def add_vulnerability(self, message):
        """Add a security vulnerability"""
        self.vulnerabilities.append(message)
        print(f"  ❌ VULNERABILITY: {message}")
    
    def add_warning(self, message):
        """Add a security warning"""
        self.warnings.append(message)
        print(f"  ⚠️  WARNING: {message}")
    
    def add_pass(self, message):
        """Add a passed security check"""
        self.passed_checks.append(message)
        self.security_score += 1
        print(f"  ✅ PASS: {message}")
        
        # Increment max score for each check
        self.max_score += 1
    
    def generate_security_report(self):
        """Generate comprehensive security report"""
        print("\n" + "=" * 50)
        print("🔒 SECURITY VALIDATION REPORT")
        print("=" * 50)
        
        # Calculate security score
        if self.max_score > 0:
            score_percentage = (self.security_score / self.max_score) * 100
        else:
            score_percentage = 0
        
        print(f"\n📊 SECURITY SCORE: {self.security_score}/{self.max_score} ({score_percentage:.1f}%)")
        
        # Security level assessment
        if score_percentage >= 90:
            level = "🛡️  EXCELLENT"
            color = "GREEN"
        elif score_percentage >= 75:
            level = "✅ GOOD"
            color = "BLUE"
        elif score_percentage >= 60:
            level = "⚠️  MODERATE"
            color = "YELLOW"
        else:
            level = "❌ POOR"
            color = "RED"
        
        print(f"🔒 SECURITY LEVEL: {level}")
        
        # Summary
        print(f"\n📈 SUMMARY:")
        print(f"  ✅ Passed Checks: {len(self.passed_checks)}")
        print(f"  ⚠️  Warnings: {len(self.warnings)}")
        print(f"  ❌ Vulnerabilities: {len(self.vulnerabilities)}")
        
        # Critical vulnerabilities
        if self.vulnerabilities:
            print(f"\n🚨 CRITICAL VULNERABILITIES TO FIX:")
            for i, vuln in enumerate(self.vulnerabilities, 1):
                print(f"  {i}. {vuln}")
        
        # Warnings to address
        if self.warnings:
            print(f"\n⚠️  WARNINGS TO ADDRESS:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        # Security recommendations
        self.generate_recommendations()
    
    def generate_recommendations(self):
        """Generate security recommendations"""
        print(f"\n🎯 SECURITY RECOMMENDATIONS:")
        
        recommendations = [
            "Enable HTTPS in production with valid SSL certificates",
            "Implement regular security updates and dependency scanning",
            "Set up monitoring and alerting for security events",
            "Conduct regular penetration testing",
            "Implement backup and disaster recovery procedures",
            "Train users on security best practices",
            "Enable two-factor authentication for all admin accounts",
            "Regular security audits and code reviews",
            "Implement rate limiting and DDoS protection",
            "Keep security documentation up to date"
        ]
        
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
        
        print(f"\n🔒 SECURITY COMPLIANCE CHECKLIST:")
        compliance_items = [
            "GDPR compliance for data protection",
            "SOX compliance for financial data (if applicable)",
            "HIPAA compliance for healthcare data (if applicable)",
            "PCI DSS compliance for payment processing (if applicable)",
            "Regular security training for staff",
            "Incident response plan documented and tested",
            "Data retention and deletion policies",
            "Third-party security assessments"
        ]
        
        for i, item in enumerate(compliance_items, 1):
            print(f"  {i}. {item}")


def main():
    """Main function to run security validation"""
    validator = SecurityValidator()
    validator.run_all_checks()
    
    print(f"\n🛡️  SECURITY VALIDATION COMPLETE")
    print(f"Review the report above and address any vulnerabilities or warnings.")
    print(f"Regular security validation is recommended to maintain security posture.")

if __name__ == "__main__":
    main()
