#!/usr/bin/env python3
"""
Database Setup Script
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def create_tables():
    with app.app_context():
        try:
            db.create_all()
            print("✅ Database tables created successfully")
            
            # List created tables
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Created tables: {', '.join(tables)}")
            
        except Exception as e:
            print(f"❌ Error creating tables: {str(e)}")

if __name__ == "__main__":
    create_tables()
