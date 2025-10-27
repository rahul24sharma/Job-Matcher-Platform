import redis
import json
import logging
import datetime
from decimal import Decimal
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=1, 
        decode_responses=True
    )
    redis_client.ping()
    logger.info("[CACHE] Redis connected successfully (DB 1).")
except Exception as e:
    logger.error(f"[CACHE] Redis connection failed: {e}")
    redis_client = None

def json_serializer(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)

def cache_get(key: str):
    """Retrieve a value from cache and safely decode JSON."""
    if not redis_client:
        logger.warning("[CACHE] Redis client not available.")
        return None
    try:
        value = redis_client.get(key)
        if value:
            logger.info(f"[CACHE] Cache HIT for key: {key}")
            return json.loads(value)
        logger.info(f"[CACHE] Cache MISS for key: {key}")
        return None
    except Exception as e:
        logger.error(f"[CACHE] Cache get error for key '{key}': {e}")
        return None

def cache_set(key: str, value, ttl: int = 3600):
    """Store a value in cache with safe serialization."""
    if not redis_client:
        logger.warning("[CACHE] Redis client not available.")
        return False
    try:
        json_value = json.dumps(value, default=json_serializer)
        success = redis_client.setex(key, ttl, json_value)
        logger.info(f"[CACHE] Key '{key}' saved successfully (TTL={ttl}s).")
        return success
    except Exception as e:
        logger.error(f"[CACHE] Cache set error for key '{key}': {e}")
        return False

def cache_delete(key: str):
    """Delete a value from cache."""
    if not redis_client:
        logger.warning("[CACHE] Redis client not available.")
        return False
    try:
        deleted = redis_client.delete(key) > 0
        if deleted:
            logger.info(f"[CACHE] Key '{key}' deleted.")
        else:
            logger.info(f"[CACHE] Key '{key}' not found for deletion.")
        return deleted
    except Exception as e:
        logger.error(f"[CACHE] Cache delete error for key '{key}': {e}")
        return False

class CacheManager:
    def get(self, key: str):
        return cache_get(key)

    def set(self, key: str, value, ttl: int = 3600):
        return cache_set(key, value, ttl)

    def delete(self, key: str):
        return cache_delete(key)

    def delete_pattern(self, pattern: str):
        """Delete all keys matching a given pattern."""
        if not redis_client:
            return 0
        try:
            keys = redis_client.keys(pattern)
            if not keys:
                return 0
            deleted_count = redis_client.delete(*keys)
            logger.info(f"[CACHE] Deleted {deleted_count} keys matching pattern '{pattern}'")
            return deleted_count
        except Exception as e:
            logger.error(f"[CACHE] Pattern delete error: {e}")
            return 0

cache_manager = CacheManager()
