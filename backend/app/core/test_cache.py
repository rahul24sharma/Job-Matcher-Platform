# test_cache.py

from app.core.cache import cache_set, cache_get, cache_delete

# Test 1: Set a value
print("Setting cache value...")
result = cache_set("test:key", {"name": "John", "age": 30}, ttl=60)
print(f"Set result: {result}")

# Test 2: Get the value
print("\nGetting cache value...")
value = cache_get("test:key")
print(f"Got value: {value}")

# Test 3: Delete the value
print("\nDeleting cache value...")
deleted = cache_delete("test:key")
print(f"Deleted: {deleted}")

# Test 4: Try to get deleted value
print("\nGetting deleted value...")
value = cache_get("test:key")
print(f"Got value: {value}")  # Should be None