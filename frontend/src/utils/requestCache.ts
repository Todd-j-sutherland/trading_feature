/**
 * Request deduplication and caching utility
 * Prevents multiple concurrent requests for the same endpoint
 */

interface PendingRequest {
  promise: Promise<any>;
  timestamp: number;
}

class RequestCache {
  private pendingRequests: Map<string, PendingRequest> = new Map();
  private cache: Map<string, { data: any; timestamp: number }> = new Map();
  private cacheTimeoutMs = 15 * 60 * 1000; // 15 minutes cache for ML data

  /**
   * Get data from cache or make request if not pending/cached
   * @param key Cache key
   * @param fetchFn Function to fetch new data
   * @param customCacheTime Optional custom cache time in milliseconds
   */
  async getOrFetch(key: string, fetchFn: () => Promise<any>, customCacheTime?: number): Promise<any> {
    const cacheTime = customCacheTime || this.cacheTimeoutMs;
    
    // Check if we have a valid cached result
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < cacheTime) {
      console.log(`📦 Cache hit for ${key} (age: ${Math.round((Date.now() - cached.timestamp) / 1000)}s)`);
      return cached.data;
    }

    // Check if there's already a pending request for this key
    const pending = this.pendingRequests.get(key);
    if (pending) {
      console.log(`⏳ Request already pending for ${key}`);
      return pending.promise;
    }

    console.log(`🌐 Making new request for ${key}`);
    // Create new request
    const promise = fetchFn()
      .then(data => {
        // Cache the result
        this.cache.set(key, { data, timestamp: Date.now() });
        // Remove from pending
        this.pendingRequests.delete(key);
        return data;
      })
      .catch(error => {
        // Remove from pending on error
        this.pendingRequests.delete(key);
        throw error;
      });

    // Store as pending
    this.pendingRequests.set(key, { promise, timestamp: Date.now() });

    return promise;
  }

  /**
   * Clear all pending requests and cache
   */
  clear(): void {
    this.pendingRequests.clear();
    this.cache.clear();
  }

  /**
   * Clear expired cache entries
   */
  cleanup(): void {
    const now = Date.now();
    
    // Clear expired cache entries
    for (const [key, value] of this.cache.entries()) {
      if (now - value.timestamp > this.cacheTimeoutMs) {
        this.cache.delete(key);
      }
    }

    // Clear old pending requests (older than 2 minutes)
    for (const [key, value] of this.pendingRequests.entries()) {
      if (now - value.timestamp > 120000) {
        this.pendingRequests.delete(key);
      }
    }
  }

  /**
   * Get cache stats for debugging
   */
  getStats(): { cacheSize: number; pendingSize: number; cacheEntries: Array<{key: string; age: number}> } {
    const now = Date.now();
    const cacheEntries = Array.from(this.cache.entries()).map(([key, value]) => ({
      key,
      age: Math.round((now - value.timestamp) / 1000) // Age in seconds
    }));
    
    return {
      cacheSize: this.cache.size,
      pendingSize: this.pendingRequests.size,
      cacheEntries
    };
  }

  /**
   * Force refresh a specific cache key
   */
  invalidate(key: string): void {
    this.cache.delete(key);
    this.pendingRequests.delete(key);
    console.log(`🗑️ Invalidated cache for ${key}`);
  }

  /**
   * Get cache expiry constants for different data types
   */
  static getCacheTime(dataType: 'ml_predictions' | 'price_data' | 'technical_indicators'): number {
    switch (dataType) {
      case 'ml_predictions':
        return 15 * 60 * 1000; // 15 minutes - ML predictions are stable
      case 'price_data':
        return 2 * 60 * 1000;  // 2 minutes - Price data updates more frequently
      case 'technical_indicators':
        return 5 * 60 * 1000;  // 5 minutes - Technical indicators mid-frequency
      default:
        return 15 * 60 * 1000;
    }
  }
}

// Export the class as well for static method access
export { RequestCache };

// Global request cache instance
export const requestCache = new RequestCache();

// Cleanup expired entries every 5 minutes
setInterval(() => {
  requestCache.cleanup();
}, 5 * 60 * 1000);
