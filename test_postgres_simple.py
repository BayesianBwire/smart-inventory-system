#!/usr/bin/env python3
"""
PostgreSQL Connection Test - Alternative without psycopg2
Tests Supabase PostgreSQL connection using SQLAlchemy only
"""

import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError
import traceback

# Load environment variables
load_dotenv()

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection to PostgreSQL"""
    print("🔗 Testing PostgreSQL Connection via SQLAlchemy...")
    print("=" * 60)
    
    try:
        db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
        
        if not db_uri:
            print("❌ No SQLALCHEMY_DATABASE_URI found in environment")
            return None
            
        print(f"Database URI: {db_uri[:50]}...{db_uri[-20:]}")  # Masked for security
        
        # Add SSL mode if not present
        if 'sslmode' not in db_uri:
            db_uri += "?sslmode=require"
            print("✅ Added SSL mode requirement")
            
        # Create engine
        engine = create_engine(db_uri, echo=False)
        
        # Test connection
        with engine.connect() as connection:
            # Basic connection test
            result = connection.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            print(f"✅ Connection test: {test_value}")
            
            # Get database info
            result = connection.execute(text("SELECT current_database(), current_user"))
            db_info = result.fetchone()
            print(f"✅ Database: {db_info[0]}")
            print(f"✅ User: {db_info[1]}")
            
            # Get PostgreSQL version
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Version: {version[:80]}...")
            
        print("✅ SQLAlchemy connection successful!")
        return engine
        
    except OperationalError as e:
        print(f"❌ Database connection failed: {str(e)}")
        if "password authentication failed" in str(e):
            print("   → Check username/password credentials")
        elif "could not connect to server" in str(e):
            print("   → Check host/port and internet connection")
        elif "database does not exist" in str(e):
            print("   → Check database name")
        return None
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        traceback.print_exc()
        return None

def analyze_existing_tables(engine):
    """Analyze existing database tables"""
    print("\n📊 Analyzing Database Schema...")
    print("=" * 60)
    
    try:
        inspector = inspect(engine)
        
        # Get all schemas
        schemas = inspector.get_schema_names()
        print(f"📋 Available schemas: {schemas}")
        
        # Get all table names (default schema)
        table_names = inspector.get_table_names()
        print(f"\n📋 Found {len(table_names)} tables in public schema:")
        
        if table_names:
            for i, table in enumerate(table_names, 1):
                print(f"   {i:2d}. {table}")
                
                # Get basic column info
                try:
                    columns = inspector.get_columns(table)
                    print(f"       → {len(columns)} columns")
                    
                    # Show primary key columns
                    pk = inspector.get_pk_constraint(table)
                    if pk and pk['constrained_columns']:
                        print(f"       → Primary key: {', '.join(pk['constrained_columns'])}")
                        
                except Exception as e:
                    print(f"       → Error reading columns: {str(e)}")
                    
        else:
            print("   📝 No tables found in public schema")
            
        # Check for tables in other schemas
        for schema in schemas:
            if schema not in ['public', 'information_schema', 'pg_catalog', 'pg_toast']:
                try:
                    schema_tables = inspector.get_table_names(schema=schema)
                    if schema_tables:
                        print(f"\n📋 Tables in '{schema}' schema: {len(schema_tables)}")
                        for table in schema_tables[:5]:  # Show first 5
                            print(f"   - {table}")
                        if len(schema_tables) > 5:
                            print(f"   ... and {len(schema_tables) - 5} more")
                except:
                    pass
            
        return table_names
        
    except Exception as e:
        print(f"❌ Failed to analyze tables: {str(e)}")
        traceback.print_exc()
        return []

def check_required_tables():
    """List required tables for RahaSoft ERP"""
    print("\n🔍 Required RahaSoft ERP Tables...")
    print("=" * 60)
    
    required_tables = {
        'users': 'User accounts and authentication',
        'companies': 'Company/organization information',
        'employees': 'Employee records and details',
        'attendance_records': 'Employee attendance tracking',
        'payrolls': 'Payroll and salary information',
        'products': 'Product inventory management',
        'sale': 'Sales transactions and records',
        'transaction': 'Financial transaction history',
        'support_tickets': 'Customer support system',
        'login_logs': 'User login history and audit',
        'audit_log': 'System audit trail',
        'bank_account': 'Bank account information',
        'leave_requests': 'Employee leave management'
    }
    
    print("Required tables:")
    for i, (table, description) in enumerate(required_tables.items(), 1):
        print(f"   {i:2d}. {table:<20} - {description}")
    
    print(f"\n📊 Total required: {len(required_tables)} tables")
    return list(required_tables.keys())

def analyze_schema_gaps(existing_tables, required_tables):
    """Analyze gaps in database schema"""
    print("\n🔄 Schema Gap Analysis...")
    print("=" * 60)
    
    existing_set = set(existing_tables)
    required_set = set(required_tables)
    
    # Missing tables
    missing_tables = required_set - existing_set
    
    # Extra tables (not required)
    extra_tables = existing_set - required_set
    
    # Existing required tables
    existing_required = existing_set & required_set
    
    print(f"✅ Existing required tables ({len(existing_required)}):")
    if existing_required:
        for table in sorted(existing_required):
            print(f"   ✓ {table}")
    else:
        print("   None found")
    
    print(f"\n❌ Missing tables ({len(missing_tables)}):")
    if missing_tables:
        for table in sorted(missing_tables):
            print(f"   ✗ {table}")
    else:
        print("   None - all required tables exist!")
    
    print(f"\n🔍 Additional tables ({len(extra_tables)}):")
    if extra_tables:
        for table in sorted(extra_tables):
            print(f"   ? {table}")
    else:
        print("   None found")
    
    # Calculate completion percentage
    if required_tables:
        completion = (len(existing_required) / len(required_tables)) * 100
        print(f"\n📈 Schema Completion: {completion:.1f}% ({len(existing_required)}/{len(required_tables)})")
    
    return missing_tables, existing_required

def create_missing_tables_script(missing_tables):
    """Generate script to create missing tables"""
    if not missing_tables:
        print("\n🎉 All required tables exist!")
        return
        
    print("\n📝 Creating Missing Tables...")
    print("=" * 60)
    
    print("Options to create missing tables:")
    print()
    print("1. 🚀 Quick Setup (Recommended):")
    print("   python setup_database.py")
    print()
    print("2. 🔧 Flask Migrations:")
    print("   flask db init")
    print("   flask db migrate -m 'Create initial tables'")
    print("   flask db upgrade")
    print()
    print("3. 🐍 Python Script:")
    print("   from app import app, db")
    print("   with app.app_context():")
    print("       db.create_all()")
    print("       print('Tables created!')")

def test_connection_quality(engine):
    """Test connection quality and performance"""
    print("\n⚡ Connection Quality Test...")
    print("=" * 60)
    
    try:
        with engine.connect() as connection:
            # Test response time
            import time
            start_time = time.time()
            connection.execute(text("SELECT 1"))
            response_time = (time.time() - start_time) * 1000
            print(f"✅ Response time: {response_time:.1f}ms")
            
            # Test concurrent connections
            result = connection.execute(text("SELECT setting FROM pg_settings WHERE name = 'max_connections'"))
            max_conn = result.fetchone()[0]
            print(f"✅ Max connections: {max_conn}")
            
            # Check active connections
            result = connection.execute(text("SELECT count(*) FROM pg_stat_activity"))
            active_conn = result.fetchone()[0]
            print(f"✅ Active connections: {active_conn}")
            
            # Database size
            result = connection.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))"))
            db_size = result.fetchone()[0]
            print(f"✅ Database size: {db_size}")
            
    except Exception as e:
        print(f"❌ Quality test failed: {str(e)}")

def main():
    """Main test execution"""
    print("🚀 RahaSoft ERP - PostgreSQL Connection Test")
    print("=" * 60)
    print("Testing Supabase PostgreSQL database connection...")
    print("Project ID: uiijismqsdjeabuqnxkl")
    print()
    
    # Test connection
    engine = test_sqlalchemy_connection()
    
    if engine:
        # Test connection quality
        test_connection_quality(engine)
        
        # Analyze existing schema
        existing_tables = analyze_existing_tables(engine)
        
        # Check required tables
        required_tables = check_required_tables()
        
        # Analyze gaps
        missing_tables, existing_required = analyze_schema_gaps(existing_tables, required_tables)
        
        # Generate creation script
        create_missing_tables_script(missing_tables)
        
        engine.dispose()
        
        # Summary
        print(f"\n🎯 Connection Test Summary:")
        print(f"   Status: ✅ Connected to Supabase PostgreSQL")
        print(f"   Existing Tables: {len(existing_tables)}")
        print(f"   Required Tables: {len(required_tables)}")
        print(f"   Missing Tables: {len(missing_tables)}")
        if required_tables:
            completion = (len(existing_required) / len(required_tables)) * 100
            print(f"   Completion: {completion:.1f}%")
        
        if missing_tables:
            print(f"\n⚠️  Next Step: Create {len(missing_tables)} missing tables")
            print("   Run: python setup_database.py")
        else:
            print(f"\n🎉 Database is ready! All tables exist.")
        
    else:
        print("\n❌ Connection failed - cannot analyze database schema")
        print("\nTroubleshooting steps:")
        print("1. Check internet connection")
        print("2. Verify Supabase project is active")
        print("3. Confirm database credentials in .env file")
        print("4. Try installing psycopg2: pip install psycopg2-binary")

if __name__ == "__main__":
    main()
