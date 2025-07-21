from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

# Core extensions
db = SQLAlchemy()
mail = Mail()

# Import enterprise extensions
try:
    from utils.cache_manager import redis_manager
    print("✅ Redis cache manager imported successfully")
except ImportError as e:
    print(f"⚠️ Warning: Redis cache manager not available: {e}")
    
try:
    from models.api_framework import api_bp
    print("✅ API framework imported successfully")
except ImportError as e:
    print(f"⚠️ Warning: API framework not available: {e}")