#!/usr/bin/env python3
"""
Quick verification that business intelligence URLs work correctly
"""

from app import app

with app.test_request_context():
    from flask import url_for
    
    print("=== Testing Business Intelligence URL Building ===")
    
    try:
        # Test the dashboards listing URL (used in dashboard template)
        dashboards_url = url_for('business_intelligence.dashboards')
        print(f"✅ business_intelligence.dashboards: {dashboards_url}")
    except Exception as e:
        print(f"❌ Error with dashboards URL: {e}")
    
    try:
        # Test the specific dashboard URL (requires dashboard_id)
        dashboard_url = url_for('business_intelligence.view_dashboard', dashboard_id=1)
        print(f"✅ business_intelligence.view_dashboard: {dashboard_url}")
    except Exception as e:
        print(f"❌ Error with view_dashboard URL: {e}")
    
    try:
        # This should fail - testing the old incorrect endpoint
        old_url = url_for('business_intelligence.dashboard')
        print(f"❌ business_intelligence.dashboard (shouldn't work): {old_url}")
    except Exception as e:
        print(f"✅ Expected error for old endpoint: {e}")
    
    print("\n✅ URL testing completed!")
