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
  private cacheTimeoutMs = 5000; // 5 seconds cache

  /**
   * Get data from cache or make request if not pending/cached
   */
  async getOrFetch(key: string, fetchFn: () => Promise<any>): Promise<any> {
    // Check if we have a valid cached result
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeoutMs) {
      return cached.data;
    }

    // Check if there's already a pending request for this key
    const pending = this.pendingRequests.get(key);
    if (pending) {
      return pending.promise;
    }

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

    // Clear old pending requests (older than 30 seconds)
    for (const [key, value] of this.pendingRequests.entries()) {
      if (now - value.timestamp > 30000) {
        this.pendingRequests.delete(key);
      }
    }
  }

  /**
   * Get cache stats for debugging
   */
  getStats(): { cacheSize: number; pendingSize: number } {
    return {
      cacheSize: this.cache.size,
      pendingSize: this.pendingRequests.size
    };
  }
}

// Global request cache instance
export const requestCache = new RequestCache();

// Cleanup expired entries every 30 seconds
setInterval(() => {
  requestCache.cleanup();
}, 30000);
