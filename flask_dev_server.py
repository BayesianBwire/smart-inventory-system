#!/usr/bin/env python3
"""
🚀 RahaSoft ERP - Flask Development Server
==========================================
Standard Flask run implementation for development
"""

import os
import sys
from flask.cli import main

def setup_flask_environment():
    """Set up Flask environment variables for development"""
    os.environ['FLASK_APP'] = 'app.py'
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    print("🚀 RahaSoft ERP - Flask Development Server")
    print("==========================================")
    print(f"✅ Flask App: {os.environ['FLASK_APP']}")
    print(f"✅ Flask Environment: {os.environ['FLASK_ENV']}")
    print(f"✅ Debug Mode: {os.environ['FLASK_DEBUG']}")
    print(f"✅ Server: http://127.0.0.1:5000")
    print()
    print("🌐 Starting Flask development server...")
    print("📊 Access your RahaSoft ERP at: http://localhost:5000")
    print("🔄 Auto-reload enabled - changes will refresh automatically")
    print("🛑 Press Ctrl+C to stop the server")
    print()

if __name__ == '__main__':
    # Set up environment
    setup_flask_environment()
    
    # Run Flask with standard flask run command
    sys.argv = ['flask', 'run', '--host=127.0.0.1', '--port=5000']
    main()
