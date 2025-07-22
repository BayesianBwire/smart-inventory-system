"""
Security Enhancement Database Migration
=====================================
Adds new security tables to the database
"""

from extensions import db
from models.security_enhanced import (
    SecurityEvent, IPBlacklist, SessionSecurity, PasswordHistory,
    SecurityConfiguration, FileUploadSecurity, APISecurityLog, ComplianceLog
)

def create_security_tables():
    """Create new security tables"""
    print("🔒 Creating enhanced security tables...")
    
    try:
        # Create all tables
        db.create_all()
        
        print("✅ Security tables created successfully:")
        print("  - SecurityEvent: Track security incidents")
        print("  - IPBlacklist: IP blocking management")
        print("  - SessionSecurity: Enhanced session tracking")
        print("  - PasswordHistory: Password reuse prevention")
        print("  - SecurityConfiguration: Company security policies")
        print("  - FileUploadSecurity: File upload protection")
        print("  - APISecurityLog: API security monitoring")
        print("  - ComplianceLog: Regulatory compliance tracking")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating security tables: {e}")
        return False

def create_default_security_configurations():
    """Create default security configurations for existing companies"""
    print("🔧 Creating default security configurations...")
    
    try:
        from models.company import Company
        from models.security_enhanced import SecurityConfiguration
        
        companies = Company.query.all()
        
        for company in companies:
            existing_config = SecurityConfiguration.query.filter_by(
                company_id=company.id
            ).first()
            
            if not existing_config:
                config = SecurityConfiguration(company_id=company.id)
                db.session.add(config)
                print(f"  ✅ Created security config for {company.name}")
        
        db.session.commit()
        print(f"✅ Created security configurations for {len(companies)} companies")
        
    except Exception as e:
        print(f"❌ Error creating default configurations: {e}")
        db.session.rollback()

if __name__ == "__main__":
    print("🔒 SECURITY ENHANCEMENT DATABASE MIGRATION")
    print("=" * 50)
    
    # Create tables
    if create_security_tables():
        # Create default configurations
        create_default_security_configurations()
        print("\n🛡️ Security enhancement migration completed successfully!")
    else:
        print("\n❌ Security enhancement migration failed!")
