#!/usr/bin/env python3
"""
PostgreSQL Connection Test and Schema Analysis
Tests Supabase PostgreSQL connection and analyzes database schema
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import OperationalError
import traceback

# Load environment variables
load_dotenv()

def test_direct_connection():
    """Test direct psycopg2 connection"""
    print("🔌 Testing Direct PostgreSQL Connection...")
    print("=" * 60)
    
    try:
        # Parse connection details from DATABASE_URI
        db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
        if not db_uri:
            print("❌ No SQLALCHEMY_DATABASE_URI found in environment")
            return False
            
        print(f"Database URI: {db_uri}")
        
        # Extract connection details
        # Format: postgresql+psycopg2://user:pass@host:port/dbname
        if 'postgresql' in db_uri:
            # Remove the +psycopg2 part for direct connection
            connection_string = db_uri.replace('postgresql+psycopg2://', 'postgresql://')
            
            conn = psycopg2.connect(connection_string)
            cursor = conn.cursor()
            
            # Test basic queries
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ PostgreSQL Version: {version}")
            
            cursor.execute("SELECT current_database();")
            current_db = cursor.fetchone()[0]
            print(f"✅ Current Database: {current_db}")
            
            cursor.execute("SELECT current_user;")
            current_user = cursor.fetchone()[0]
            print(f"✅ Current User: {current_user}")
            
            cursor.close()
            conn.close()
            print("✅ Direct connection successful!")
            return True
            
    except Exception as e:
        print(f"❌ Direct connection failed: {str(e)}")
        traceback.print_exc()
        return False

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection"""
    print("\n🔗 Testing SQLAlchemy Connection...")
    print("=" * 60)
    
    try:
        db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
        
        # Add SSL mode if not present
        if 'sslmode' not in db_uri:
            db_uri += "?sslmode=require"
            
        engine = create_engine(db_uri)
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            print(f"✅ SQLAlchemy test query result: {test_value}")
            
            # Get database info
            result = connection.execute(text("SELECT current_database(), current_user, version()"))
            db_info = result.fetchone()
            print(f"✅ Database: {db_info[0]}")
            print(f"✅ User: {db_info[1]}")
            print(f"✅ Version: {db_info[2][:50]}...")
            
        print("✅ SQLAlchemy connection successful!")
        return engine
        
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {str(e)}")
        traceback.print_exc()
        return None

def analyze_existing_tables(engine):
    """Analyze existing database tables"""
    print("\n📊 Analyzing Existing Database Schema...")
    print("=" * 60)
    
    try:
        inspector = inspect(engine)
        
        # Get all table names
        table_names = inspector.get_table_names()
        print(f"📋 Found {len(table_names)} existing tables:")
        
        if table_names:
            for i, table in enumerate(table_names, 1):
                print(f"   {i:2d}. {table}")
                
                # Get column info for each table
                columns = inspector.get_columns(table)
                print(f"       Columns: {len(columns)}")
                for col in columns[:3]:  # Show first 3 columns
                    print(f"         - {col['name']} ({col['type']})")
                if len(columns) > 3:
                    print(f"         ... and {len(columns) - 3} more columns")
                print()
        else:
            print("   No tables found in database")
            
        return table_names
        
    except Exception as e:
        print(f"❌ Failed to analyze tables: {str(e)}")
        return []

def check_required_tables():
    """Check which RahaSoft tables are missing"""
    print("🔍 Checking Required RahaSoft ERP Tables...")
    print("=" * 60)
    
    # Required tables for RahaSoft ERP
    required_tables = [
        'users',           # User accounts
        'companies',       # Company information
        'employees',       # Employee records
        'attendance_records',  # Attendance tracking
        'payrolls',        # Payroll information
        'products',        # Product inventory
        'sale',           # Sales records
        'transaction',    # Financial transactions
        'support_tickets', # Customer support
        'login_logs',     # Login history
        'audit_log',      # System audit trail
        'bank_account',   # Bank account info
        'leave_requests'  # Leave management
    ]
    
    print("Required tables for RahaSoft ERP:")
    for i, table in enumerate(required_tables, 1):
        print(f"   {i:2d}. {table}")
    
    print(f"\n📊 Total required tables: {len(required_tables)}")
    return required_tables

def compare_schemas(existing_tables, required_tables):
    """Compare existing vs required tables"""
    print("\n🔄 Schema Comparison Analysis...")
    print("=" * 60)
    
    existing_set = set(existing_tables)
    required_set = set(required_tables)
    
    # Find missing tables
    missing_tables = required_set - existing_set
    
    # Find extra tables
    extra_tables = existing_set - required_set
    
    # Find matching tables
    matching_tables = existing_set & required_set
    
    print(f"✅ Matching tables ({len(matching_tables)}):")
    for table in sorted(matching_tables):
        print(f"   ✓ {table}")
    
    print(f"\n❌ Missing tables ({len(missing_tables)}):")
    for table in sorted(missing_tables):
        print(f"   ✗ {table}")
    
    print(f"\n🔍 Extra tables ({len(extra_tables)}):")
    for table in sorted(extra_tables):
        print(f"   ? {table}")
    
    # Calculate completion percentage
    completion = (len(matching_tables) / len(required_tables)) * 100
    print(f"\n📈 Schema Completion: {completion:.1f}% ({len(matching_tables)}/{len(required_tables)})")
    
    return missing_tables, extra_tables, matching_tables

def generate_migration_plan(missing_tables):
    """Generate migration plan for missing tables"""
    if not missing_tables:
        print("\n🎉 No migration needed - all tables exist!")
        return
    
    print("\n📝 Migration Plan...")
    print("=" * 60)
    
    print("To create missing tables, you can:")
    print("1. Run Flask database migration:")
    print("   flask db init")
    print("   flask db migrate -m 'Initial migration'")
    print("   flask db upgrade")
    
    print("\n2. Or run the setup_database.py script:")
    print("   python setup_database.py")
    
    print("\n3. Or create tables manually using SQLAlchemy:")
    print("   from app import app, db")
    print("   with app.app_context():")
    print("       db.create_all()")

def main():
    """Main test function"""
    print("🚀 RahaSoft ERP - PostgreSQL Connection & Schema Test")
    print("=" * 60)
    print(f"Testing Supabase PostgreSQL database...")
    print(f"Project ID: uiijismqsdjeabuqnxkl")
    print()
    
    # Test direct connection
    direct_success = test_direct_connection()
    
    # Test SQLAlchemy connection
    engine = test_sqlalchemy_connection()
    
    if engine:
        # Analyze existing schema
        existing_tables = analyze_existing_tables(engine)
        
        # Check required tables
        required_tables = check_required_tables()
        
        # Compare schemas
        missing_tables, extra_tables, matching_tables = compare_schemas(existing_tables, required_tables)
        
        # Generate migration plan
        generate_migration_plan(missing_tables)
        
        engine.dispose()
        
        print(f"\n🎯 Summary:")
        print(f"   Direct Connection: {'✅ Success' if direct_success else '❌ Failed'}")
        print(f"   SQLAlchemy Connection: {'✅ Success' if engine else '❌ Failed'}")
        print(f"   Existing Tables: {len(existing_tables)}")
        print(f"   Required Tables: {len(required_tables)}")
        print(f"   Missing Tables: {len(missing_tables)}")
        print(f"   Schema Completion: {(len(matching_tables)/len(required_tables)*100):.1f}%")
        
    else:
        print("\n❌ Cannot proceed with schema analysis - connection failed")
        print("\nTroubleshooting:")
        print("1. Check your internet connection")
        print("2. Verify Supabase project is active")
        print("3. Confirm database credentials are correct")
        print("4. Check if psycopg2 is installed: pip install psycopg2-binary")

if __name__ == "__main__":
    main()
