#!/usr/bin/env python3
"""
Test company registration form submission
"""
import os
from dotenv import load_dotenv
load_dotenv()

try:
    from app import app, db
    print("✅ App imported successfully")
    
    with app.test_client() as client:
        print("🔍 Testing company registration form...")
        
        # First get the registration page to get CSRF token
        response = client.get('/register_company')
        print(f"GET /register_company: {response.status_code}")
        
        if response.status_code == 200:
            # Try to extract CSRF token from response
            content = response.data.decode('utf-8')
            if 'csrf_token' in content:
                print("✅ CSRF token found in form")
            else:
                print("⚠️ No CSRF token found")
        
        # Test POST with minimal data
        test_data = {
            'company_name': 'Test Company',
            'founder_email': 'test@example.com',
            'founder_password': 'testpass123',
            'founder_password_confirm': 'testpass123'
        }
        
        response = client.post('/register_company', data=test_data, follow_redirects=False)
        print(f"POST /register_company: {response.status_code}")
        
        if response.status_code >= 400:
            print(f"Error response: {response.data.decode('utf-8')[:500]}")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
