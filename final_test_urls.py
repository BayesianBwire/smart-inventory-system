#!/usr/bin/env python3
"""
Final verification of dashboard URL endpoints
"""

from app import app

with app.test_request_context():
    from flask import url_for
    
    print("=== Final Dashboard URL Testing ===")
    
    # Test each URL reference from the dashboard template
    urls_to_test = [
        ('crm.dashboard', 'CRM Dashboard'),
        ('finance.dashboard', 'Finance Dashboard'), 
        ('business_intelligence.dashboards', 'Business Intelligence'),
        ('security.security_dashboard', 'Security Dashboard'),
    ]
    
    for endpoint, name in urls_to_test:
        try:
            url = url_for(endpoint)
            print(f"✅ {name}: {endpoint} → {url}")
        except Exception as e:
            print(f"❌ {name}: {endpoint} → Error: {e}")
    
    print("\n✅ All URL testing completed!")
