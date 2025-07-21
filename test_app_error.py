#!/usr/bin/env python3
"""
Test script to identify the source of Internal Server Error
"""
import os
from dotenv import load_dotenv
load_dotenv()

try:
    from app import app, db
    print("✅ App imported successfully")
    
    with app.test_client() as client:
        print("🔍 Testing routes...")
        
        # Test welcome page
        response = client.get('/welcome')
        print(f"Welcome page: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.data}")
        
        # Test register company page
        response = client.get('/register_company')
        print(f"Register company page: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.data}")
            
        # Test root page
        response = client.get('/')
        print(f"Root page: {response.status_code}")
        if response.status_code not in [200, 302]:
            print(f"Error: {response.data}")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
