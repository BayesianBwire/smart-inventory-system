from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

# Core extensions
db = SQLAlchemy()
mail = Mail()

# Import enterprise extensions - only utilities, not routes/models
try:
    from utils.cache_manager import redis_manager
    print("✅ Redis cache manager imported successfully")
except ImportError as e:
    print(f"⚠️ Warning: Redis cache manager not available: {e}")
    # Create a dummy redis_manager to prevent errors
    class DummyRedisManager:
        def init_app(self, app): pass
        def get(self, key): return None
        def set(self, key, value, timeout=None): return True
        def delete(self, key): return True
        def invalidate_category(self, category): return True
    
    redis_manager = DummyRedisManager()