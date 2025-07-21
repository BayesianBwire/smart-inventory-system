#!/usr/bin/env python3
"""
Test CSRF functionality
"""
import os
from dotenv import load_dotenv
load_dotenv()

try:
    from app import app, db
    from bs4 import BeautifulSoup
    print("✅ App imported successfully")
    
    with app.test_client() as client:
        # Get CSRF token first
        response = client.get('/register_company')
        soup = BeautifulSoup(response.data, 'html.parser')
        csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
        print(f"✅ CSRF token found: {csrf_token[:20]}...")
        
        # Test with proper CSRF token
        test_data = {
            'csrf_token': csrf_token,
            'name': 'Test Company',
            'email': 'test@example.com',
            'industry': 'technology',
            'founder_username': 'testuser',
            'founder_email': 'founder@example.com',
            'founder_name': 'Test Founder',
            'founder_password': 'testpass123',
            'confirm_password': 'testpass123'
        }
        
        response = client.post('/register_company', data=test_data, follow_redirects=False)
        print(f"POST /register_company with CSRF: {response.status_code}")
        
        if response.status_code >= 400:
            print(f"Error response: {response.data.decode('utf-8')[:500]}")
        elif response.status_code == 302:
            print(f"✅ Redirected to: {response.location}")
            
except ImportError as e:
    print(f"Missing BeautifulSoup4: {e}")
    print("Installing beautifulsoup4...")
    import subprocess
    subprocess.run(['pip', 'install', 'beautifulsoup4'])
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
