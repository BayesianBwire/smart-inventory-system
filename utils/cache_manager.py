"""
Redis Caching Layer for RahaSoft ERP
Provides enterprise-grade caching for performance optimization
"""
import redis
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import current_app, request, g
from extensions import db

# Redis Connection Manager
class RedisManager:
    """Centralized Redis connection and configuration management"""
    
    def __init__(self):
        self.redis_client = None
        self.is_enabled = False
    
    def init_app(self, app):
        """Initialize Redis with Flask app"""
        try:
            redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                health_check_interval=30
            )
            
            # Test connection
            self.redis_client.ping()
            self.is_enabled = True
            
            app.logger.info("Redis connection established successfully")
            
        except Exception as e:
            app.logger.warning(f"Redis connection failed: {e}. Caching disabled.")
            self.is_enabled = False
    
    def get_client(self):
        """Get Redis client if available"""
        return self.redis_client if self.is_enabled else None


# Global Redis manager instance
redis_manager = RedisManager()


class CacheConfig:
    """Cache configuration constants"""
    
    # Cache TTL (Time To Live) in seconds
    TTL_SHORT = 300        # 5 minutes
    TTL_MEDIUM = 1800      # 30 minutes
    TTL_LONG = 3600        # 1 hour
    TTL_VERY_LONG = 86400  # 24 hours
    
    # Cache key prefixes
    PREFIX_USER = "user:"
    PREFIX_COMPANY = "company:"
    PREFIX_PRODUCT = "product:"
    PREFIX_CUSTOMER = "customer:"
    PREFIX_INVOICE = "invoice:"
    PREFIX_ANALYTICS = "analytics:"
    PREFIX_SETTINGS = "settings:"
    PREFIX_SESSION = "session:"
    PREFIX_API = "api:"
    PREFIX_SEARCH = "search:"
    
    # Cache categories for bulk invalidation
    CATEGORY_USER_DATA = "user_data"
    CATEGORY_COMPANY_DATA = "company_data"
    CATEGORY_FINANCIAL = "financial"
    CATEGORY_INVENTORY = "inventory"
    CATEGORY_CRM = "crm"
    CATEGORY_ANALYTICS = "analytics"


class CacheManager:
    """Advanced cache management with Redis"""
    
    def __init__(self):
        self.redis = redis_manager.get_client()
    
    def _generate_key(self, key_parts):
        """Generate cache key from parts"""
        if isinstance(key_parts, (list, tuple)):
            key = ":".join(str(part) for part in key_parts)
        else:
            key = str(key_parts)
        return key
    
    def _add_category_tracking(self, key, category):
        """Add key to category set for bulk operations"""
        if self.redis and category:
            category_key = f"category:{category}"
            self.redis.sadd(category_key, key)
            # Set category TTL to prevent infinite growth
            self.redis.expire(category_key, CacheConfig.TTL_VERY_LONG)
    
    def set(self, key, value, ttl=CacheConfig.TTL_MEDIUM, category=None):
        """Set cache value with optional category tracking"""
        if not self.redis:
            return False
        
        try:
            cache_key = self._generate_key(key)
            
            # Serialize value based on type
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = pickle.dumps(value)
            
            # Set with TTL
            result = self.redis.setex(cache_key, ttl, serialized_value)
            
            # Add to category tracking
            self._add_category_tracking(cache_key, category)
            
            return result
        except Exception as e:
            current_app.logger.error(f"Cache set error: {e}")
            return False
    
    def get(self, key):
        """Get cache value"""
        if not self.redis:
            return None
        
        try:
            cache_key = self._generate_key(key)
            value = self.redis.get(cache_key)
            
            if value is None:
                return None
            
            # Try JSON first, then pickle
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return pickle.loads(value.encode('latin1'))
                
        except Exception as e:
            current_app.logger.error(f"Cache get error: {e}")
            return None
    
    def delete(self, key):
        """Delete cache key"""
        if not self.redis:
            return False
        
        try:
            cache_key = self._generate_key(key)
            return self.redis.delete(cache_key) > 0
        except Exception as e:
            current_app.logger.error(f"Cache delete error: {e}")
            return False
    
    def invalidate_category(self, category):
        """Invalidate all keys in a category"""
        if not self.redis:
            return False
        
        try:
            category_key = f"category:{category}"
            keys = self.redis.smembers(category_key)
            
            if keys:
                # Delete all keys in category
                self.redis.delete(*keys)
                # Clear category set
                self.redis.delete(category_key)
                
            return True
        except Exception as e:
            current_app.logger.error(f"Cache category invalidation error: {e}")
            return False
    
    def exists(self, key):
        """Check if key exists in cache"""
        if not self.redis:
            return False
        
        try:
            cache_key = self._generate_key(key)
            return self.redis.exists(cache_key) > 0
        except Exception as e:
            current_app.logger.error(f"Cache exists check error: {e}")
            return False
    
    def extend_ttl(self, key, ttl):
        """Extend TTL for existing key"""
        if not self.redis:
            return False
        
        try:
            cache_key = self._generate_key(key)
            return self.redis.expire(cache_key, ttl)
        except Exception as e:
            current_app.logger.error(f"Cache TTL extension error: {e}")
            return False


# Global cache manager instance
cache = CacheManager()


# Caching Decorators
def cached(ttl=CacheConfig.TTL_MEDIUM, category=None, key_generator=None):
    """
    Decorator for caching function results
    
    Args:
        ttl: Cache time-to-live in seconds
        category: Cache category for bulk invalidation
        key_generator: Custom function to generate cache key
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                # Default key generation
                func_name = f"{func.__module__}.{func.__name__}"
                args_str = str(args) + str(sorted(kwargs.items()))
                key_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]
                cache_key = f"func:{func_name}:{key_hash}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl, category=category)
            
            return result
        return wrapper
    return decorator


def cache_user_data(user_id, ttl=CacheConfig.TTL_MEDIUM):
    """Decorator for caching user-specific data"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{CacheConfig.PREFIX_USER}{user_id}:{func.__name__}"
            
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl, category=CacheConfig.CATEGORY_USER_DATA)
            
            return result
        return wrapper
    return decorator


def cache_company_data(company_id, ttl=CacheConfig.TTL_LONG):
    """Decorator for caching company-specific data"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{CacheConfig.PREFIX_COMPANY}{company_id}:{func.__name__}"
            
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl, category=CacheConfig.CATEGORY_COMPANY_DATA)
            
            return result
        return wrapper
    return decorator


# Specialized Cache Classes
class UserSessionCache:
    """Manage user session caching"""
    
    @staticmethod
    def get_user_session(user_id):
        """Get cached user session data"""
        key = f"{CacheConfig.PREFIX_SESSION}{user_id}"
        return cache.get(key)
    
    @staticmethod
    def set_user_session(user_id, session_data, ttl=CacheConfig.TTL_LONG):
        """Cache user session data"""
        key = f"{CacheConfig.PREFIX_SESSION}{user_id}"
        return cache.set(key, session_data, ttl=ttl, category=CacheConfig.CATEGORY_USER_DATA)
    
    @staticmethod
    def invalidate_user_session(user_id):
        """Invalidate user session cache"""
        key = f"{CacheConfig.PREFIX_SESSION}{user_id}"
        return cache.delete(key)


class AnalyticsCache:
    """Manage analytics data caching"""
    
    @staticmethod
    def get_dashboard_data(company_id, user_id, date_range=None):
        """Get cached dashboard analytics"""
        date_suffix = f":{date_range}" if date_range else ""
        key = f"{CacheConfig.PREFIX_ANALYTICS}dashboard:{company_id}:{user_id}{date_suffix}"
        return cache.get(key)
    
    @staticmethod
    def set_dashboard_data(company_id, user_id, data, date_range=None, ttl=CacheConfig.TTL_MEDIUM):
        """Cache dashboard analytics"""
        date_suffix = f":{date_range}" if date_range else ""
        key = f"{CacheConfig.PREFIX_ANALYTICS}dashboard:{company_id}:{user_id}{date_suffix}"
        return cache.set(key, data, ttl=ttl, category=CacheConfig.CATEGORY_ANALYTICS)
    
    @staticmethod
    def get_report_data(report_type, company_id, params_hash):
        """Get cached report data"""
        key = f"{CacheConfig.PREFIX_ANALYTICS}report:{report_type}:{company_id}:{params_hash}"
        return cache.get(key)
    
    @staticmethod
    def set_report_data(report_type, company_id, params_hash, data, ttl=CacheConfig.TTL_LONG):
        """Cache report data"""
        key = f"{CacheConfig.PREFIX_ANALYTICS}report:{report_type}:{company_id}:{params_hash}"
        return cache.set(key, data, ttl=ttl, category=CacheConfig.CATEGORY_ANALYTICS)


class SearchCache:
    """Manage search result caching"""
    
    @staticmethod
    def get_search_results(query, filters=None):
        """Get cached search results"""
        query_hash = hashlib.md5(f"{query}:{filters}".encode()).hexdigest()[:12]
        key = f"{CacheConfig.PREFIX_SEARCH}{query_hash}"
        return cache.get(key)
    
    @staticmethod
    def set_search_results(query, filters, results, ttl=CacheConfig.TTL_SHORT):
        """Cache search results"""
        query_hash = hashlib.md5(f"{query}:{filters}".encode()).hexdigest()[:12]
        key = f"{CacheConfig.PREFIX_SEARCH}{query_hash}"
        return cache.set(key, results, ttl=ttl)


class APIResponseCache:
    """Manage API response caching"""
    
    @staticmethod
    def get_api_response(endpoint, params, company_id):
        """Get cached API response"""
        params_hash = hashlib.md5(str(sorted(params.items())).encode()).hexdigest()[:8]
        key = f"{CacheConfig.PREFIX_API}{company_id}:{endpoint}:{params_hash}"
        return cache.get(key)
    
    @staticmethod
    def set_api_response(endpoint, params, company_id, response, ttl=CacheConfig.TTL_SHORT):
        """Cache API response"""
        params_hash = hashlib.md5(str(sorted(params.items())).encode()).hexdigest()[:8]
        key = f"{CacheConfig.PREFIX_API}{company_id}:{endpoint}:{params_hash}"
        return cache.set(key, response, ttl=ttl, category=CacheConfig.CATEGORY_COMPANY_DATA)


# Cache Warming Functions
class CacheWarmer:
    """Proactively warm up commonly accessed data"""
    
    @staticmethod
    def warm_user_data(user_id):
        """Warm up user-specific cache"""
        from models.user import User
        from models.company import Company
        
        user = User.query.get(user_id)
        if not user:
            return
        
        # Cache user data
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'company_id': user.company_id
        }
        UserSessionCache.set_user_session(user_id, user_data)
        
        # Cache company data if available
        if user.company:
            company_data = {
                'id': user.company.id,
                'name': user.company.name,
                'industry': user.company.industry,
                'settings': user.company.settings
            }
            key = f"{CacheConfig.PREFIX_COMPANY}{user.company.id}"
            cache.set(key, company_data, category=CacheConfig.CATEGORY_COMPANY_DATA)
    
    @staticmethod
    def warm_dashboard_cache(company_id):
        """Warm up dashboard analytics cache"""
        # This would trigger calculation and caching of dashboard metrics
        # Implementation depends on specific analytics functions
        pass


# Cache Invalidation Strategies
class CacheInvalidator:
    """Handle intelligent cache invalidation"""
    
    @staticmethod
    def invalidate_user_cache(user_id):
        """Invalidate all cache entries for a user"""
        patterns = [
            f"{CacheConfig.PREFIX_USER}{user_id}*",
            f"{CacheConfig.PREFIX_SESSION}{user_id}*"
        ]
        
        for pattern in patterns:
            CacheInvalidator._delete_pattern(pattern)
    
    @staticmethod
    def invalidate_company_cache(company_id):
        """Invalidate all cache entries for a company"""
        cache.invalidate_category(CacheConfig.CATEGORY_COMPANY_DATA)
        cache.invalidate_category(CacheConfig.CATEGORY_FINANCIAL)
        cache.invalidate_category(CacheConfig.CATEGORY_INVENTORY)
        cache.invalidate_category(CacheConfig.CATEGORY_CRM)
    
    @staticmethod
    def invalidate_analytics_cache():
        """Invalidate analytics cache"""
        cache.invalidate_category(CacheConfig.CATEGORY_ANALYTICS)
    
    @staticmethod
    def _delete_pattern(pattern):
        """Delete keys matching pattern"""
        if not redis_manager.is_enabled:
            return
        
        try:
            redis_client = redis_manager.get_client()
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
        except Exception as e:
            current_app.logger.error(f"Pattern deletion error: {e}")


# Cache Monitoring
class CacheMonitor:
    """Monitor cache performance and health"""
    
    @staticmethod
    def get_cache_stats():
        """Get cache statistics"""
        if not redis_manager.is_enabled:
            return {'enabled': False}
        
        try:
            redis_client = redis_manager.get_client()
            info = redis_client.info()
            
            return {
                'enabled': True,
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_ratio': CacheMonitor._calculate_hit_ratio(info),
                'total_keys': sum(db_info.get('keys', 0) for db_key, db_info in info.items() if db_key.startswith('db'))
            }
        except Exception as e:
            current_app.logger.error(f"Cache stats error: {e}")
            return {'enabled': True, 'error': str(e)}
    
    @staticmethod
    def _calculate_hit_ratio(info):
        """Calculate cache hit ratio"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        return round((hits / total * 100), 2) if total > 0 else 0
