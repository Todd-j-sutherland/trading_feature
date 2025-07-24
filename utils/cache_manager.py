#!/usr/bin/env python3
"""
Simple Cache Manager - Dummy implementation for compatibility
"""

class CacheManager:
    """Simple in-memory cache manager"""
    
    def __init__(self):
        self.cache = {}
    
    def get(self, key):
        """Get cached value"""
        return self.cache.get(key)
    
    def set(self, key, value, expiry_minutes=60):
        """Set cached value (expiry ignored in this simple implementation)"""
        self.cache[key] = value
    
    def clear(self):
        """Clear all cached values"""
        self.cache.clear()
    
    def remove(self, key):
        """Remove specific cached value"""
        if key in self.cache:
            del self.cache[key]
