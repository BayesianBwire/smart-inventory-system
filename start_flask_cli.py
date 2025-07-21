#!/usr/bin/env python3
"""
🚀 RahaSoft ERP Flask CLI Runner
==============================
Run this to start the Flask development server
"""

import subprocess
import sys
import os

def run_flask_cli():
    """Run Flask using the CLI commands"""
    print("🚀 RahaSoft ERP - Starting with Flask CLI")
    print("=========================================")
    
    # Set environment variables
    env = os.environ.copy()
    env['FLASK_APP'] = 'app.py'
    env['FLASK_ENV'] = 'development'
    env['FLASK_DEBUG'] = '1'
    
    print("✅ Environment configured:")
    print(f"   FLASK_APP: {env['FLASK_APP']}")
    print(f"   FLASK_ENV: {env['FLASK_ENV']}")
    print(f"   FLASK_DEBUG: {env['FLASK_DEBUG']}")
    print()
    print("🌐 Starting server at: http://127.0.0.1:5000")
    print("🔄 Auto-reload enabled")
    print("🛑 Press Ctrl+C to stop")
    print()
    
    # Run flask command
    try:
        subprocess.run([
            sys.executable, '-m', 'flask', 'run', 
            '--host=127.0.0.1', '--port=5000'
        ], env=env)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")

if __name__ == '__main__':
    run_flask_cli()
