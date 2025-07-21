#!/usr/bin/env python3
"""
Direct PostgreSQL Test - bypassing environment variables
"""

import os
from sqlalchemy import create_engine, text

def test_direct_postgres():
    """Test PostgreSQL connection directly"""
    print("🔗 Direct PostgreSQL Connection Test")
    print("=" * 50)
    
    # Direct connection string from .env
    db_uri = "postgresql+psycopg2://postgres:Di6ZH8wcNu3n88iq@db.uiijismqsdjeabuqnxkl.supabase.co:5432/postgres?sslmode=require"
    
    print(f"Testing connection to: db.uiijismqsdjeabuqnxkl.supabase.co")
    print(f"Database: postgres")
    print(f"User: postgres")
    print()
    
    try:
        # Try without psycopg2 first - use pure PostgreSQL driver
        simple_uri = "postgresql://postgres:Di6ZH8wcNu3n88iq@db.uiijismqsdjeabuqnxkl.supabase.co:5432/postgres?sslmode=require"
        
        print("Attempting connection...")
        engine = create_engine(simple_uri, echo=False)
        
        with engine.connect() as connection:
            # Test basic query
            result = connection.execute(text("SELECT 1 as test"))
            test_result = result.fetchone()[0]
            print(f"✅ Connection successful! Test query: {test_result}")
            
            # Get database info
            result = connection.execute(text("SELECT current_database()"))
            db_name = result.fetchone()[0]
            print(f"✅ Database: {db_name}")
            
            result = connection.execute(text("SELECT current_user"))
            user = result.fetchone()[0]
            print(f"✅ User: {user}")
            
            # Check existing tables
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.fetchall()]
            print(f"\n📋 Found {len(tables)} existing tables:")
            
            if tables:
                for i, table in enumerate(tables, 1):
                    print(f"   {i:2d}. {table}")
            else:
                print("   No tables found in public schema")
            
            # Check required tables
            required_tables = [
                'users', 'companies', 'employees', 'attendance_records',
                'payrolls', 'products', 'sale', 'transaction', 
                'support_tickets', 'login_logs', 'audit_log', 
                'bank_account', 'leave_requests'
            ]
            
            existing_set = set(tables)
            required_set = set(required_tables)
            missing_tables = required_set - existing_set
            
            print(f"\n🔍 Required vs Existing Analysis:")
            print(f"   Required tables: {len(required_tables)}")
            print(f"   Existing tables: {len(tables)}")
            print(f"   Missing tables: {len(missing_tables)}")
            
            if missing_tables:
                print(f"\n❌ Missing tables ({len(missing_tables)}):")
                for table in sorted(missing_tables):
                    print(f"   ✗ {table}")
                    
                print(f"\n📝 Next Steps:")
                print("1. Create missing tables using setup_database.py")
                print("2. Or run: flask db upgrade")
                print("3. Or use: db.create_all() in Flask context")
            else:
                print(f"\n🎉 All required tables exist!")
            
        engine.dispose()
        return True
        
    except ImportError as e:
        print(f"❌ Driver not available: {str(e)}")
        print("💡 Install PostgreSQL driver: pip install psycopg2-binary")
        return False
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print()
        
        if "password authentication failed" in str(e).lower():
            print("🔑 Authentication issue - check credentials")
        elif "could not connect" in str(e).lower():
            print("🌐 Network issue - check internet/firewall")
        elif "database" in str(e).lower() and "does not exist" in str(e).lower():
            print("🗃️  Database does not exist")
        else:
            print("🔧 General connection error")
            
        print("\nTroubleshooting:")
        print("1. Check Supabase project status")
        print("2. Verify credentials are correct")
        print("3. Test network connectivity")
        print("4. Check if IP is allowlisted in Supabase")
        
        return False

if __name__ == "__main__":
    test_direct_postgres()
