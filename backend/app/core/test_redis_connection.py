# test_redis_connection.py

import redis
import json

# Test direct Redis connection
try:
    r = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)
    
    # Test 1: Ping
    print("Testing Redis connection...")
    print(f"Ping response: {r.ping()}")
    
    # Test 2: Set a test value
    print("\nSetting test value...")
    r.setex("test:hello", 60, json.dumps({"message": "Hello Redis!"}))
    
    # Test 3: Get the value
    print("Getting test value...")
    value = r.get("test:hello")
    print(f"Got: {value}")
    
    # Test 4: Check what's in Redis
    print("\nAll keys in DB 1:")
    keys = r.keys("*")
    print(keys)
    
except Exception as e:
    print(f"Error: {e}")