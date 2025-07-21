import sys
import os

# Set Flask environment variables for proper Flask CLI support
os.environ['FLASK_APP'] = 'app.py'
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Activate virtual environment
activate_this = os.path.join(os.path.dirname(__file__), 'venv', 'Scripts', 'activate_this.py')
if os.path.exists(activate_this):
    exec(open(activate_this).read(), dict(__file__=activate_this))

# Import and run app
try:
    from app import app
    print("✅ Flask app imported successfully!")
    print("🚀 Starting RahaSoft ERP on http://127.0.0.1:5000")
    print("📊 Access your modern dashboard after login!")
    app.run(debug=True, host='127.0.0.1', port=5000)
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("🔧 Installing missing dependencies...")
    os.system('pip install flask flask-wtf flask-login flask-sqlalchemy flask-migrate')
    print("🔄 Retrying import...")
    from app import app
    app.run(debug=True, host='127.0.0.1', port=5000)
