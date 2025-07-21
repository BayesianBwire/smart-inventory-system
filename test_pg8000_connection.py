#!/usr/bin/env python3
"""
Test PostgreSQL connection with pg8000 driver
Compatible with Python 3.14 beta
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_postgres_connection():
    """Test PostgreSQL connection with pg8000"""
    print("🚀 Testing PostgreSQL Connection (Python 3.14 Compatible)")
    print("=" * 60)
    
    try:
        from sqlalchemy import create_engine, text
        
        # Get database URI
        db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
        print(f"Database URI: {db_uri[:30]}...{db_uri[-20:]}")
        
        # Create engine with pg8000
        engine = create_engine(db_uri, echo=False)
        
        # Test connection
        with engine.connect() as connection:
            # Basic test
            result = connection.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            print(f"✅ Connection successful! Test query: {test_value}")
            
            # Get database info
            result = connection.execute(text("SELECT current_database(), current_user, version()"))
            db_info = result.fetchone()
            print(f"✅ Database: {db_info[0]}")
            print(f"✅ User: {db_info[1]}")
            print(f"✅ PostgreSQL Version: {db_info[2][:50]}...")
            
            # Check existing tables
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.fetchall()]
            print(f"\n📋 Existing tables in database: {len(tables)}")
            
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
            matching_tables = existing_set & required_set
            
            print(f"\n🔍 Schema Analysis:")
            print(f"   Required tables: {len(required_tables)}")
            print(f"   Existing tables: {len(tables)}")
            print(f"   Matching tables: {len(matching_tables)}")
            print(f"   Missing tables: {len(missing_tables)}")
            
            if matching_tables:
                print(f"\n✅ Existing required tables:")
                for table in sorted(matching_tables):
                    print(f"   ✓ {table}")
            
            if missing_tables:
                print(f"\n❌ Missing tables:")
                for table in sorted(missing_tables):
                    print(f"   ✗ {table}")
                
                print(f"\n📝 Next Steps:")
                print("1. Run: python setup_database.py")
                print("2. Or create tables via Flask app context")
            else:
                print(f"\n🎉 All required tables exist!")
            
            # Test database performance
            import time
            start_time = time.time()
            connection.execute(text("SELECT COUNT(*) FROM information_schema.tables"))
            response_time = (time.time() - start_time) * 1000
            print(f"\n⚡ Performance: Response time {response_time:.1f}ms")
            
        engine.dispose()
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependencies: {str(e)}")
        print("💡 Install: pip install sqlalchemy pg8000 python-dotenv")
        return False
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        
        # Provide specific troubleshooting
        error_str = str(e).lower()
        if "authentication failed" in error_str:
            print("🔑 Issue: Invalid credentials")
            print("   → Check username/password in .env file")
        elif "could not connect" in error_str or "network" in error_str:
            print("🌐 Issue: Network connectivity")
            print("   → Check internet connection and Supabase status")
        elif "database does not exist" in error_str:
            print("🗃️  Issue: Database not found")
            print("   → Verify database name in connection string")
        elif "ssl" in error_str:
            print("🔒 Issue: SSL connection problem")
            print("   → Try adding ?sslmode=require to connection string")
        else:
            print("🔧 General connection error")
            
        print("\n🏥 Environment Issues (Python 3.14 beta):")
        print("   → Some packages may be incompatible")
        print("   → Consider using Python 3.11 or 3.12 for production")
        
        return False

if __name__ == "__main__":
    success = test_postgres_connection()
    
    if success:
        print(f"\n🎯 Summary: PostgreSQL connection successful!")
        print("   Your laptop environment is now compatible")
        print("   Database configuration is working correctly")
    else:
        print(f"\n❌ Summary: Connection failed")
        print("   Laptop environment issues identified:")
        print("   1. Python 3.14 beta compatibility problems")
        print("   2. Missing PostgreSQL development libraries")
        print("   3. Network or credential issues")
