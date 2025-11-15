/**
 * LocalStorage cache utilities for prompts
 * Provides instant loading on page refresh
 */

const CACHE_PREFIX = 'ai-voice-cache:'
const CACHE_VERSION = 'v1'

export interface CacheItem<T> {
  data: T
  timestamp: number
  version: string
}

export const cache = {
  /**
   * Set cache item with timestamp
   */
  set<T>(key: string, data: T): void {
    try {
      const cacheKey = `${CACHE_PREFIX}${key}`
      const item: CacheItem<T> = {
        data,
        timestamp: Date.now(),
        version: CACHE_VERSION,
      }
      localStorage.setItem(cacheKey, JSON.stringify(item))
    } catch (error) {
      console.warn('Failed to set cache:', error)
    }
  },

  /**
   * Get cache item if not expired
   */
  get<T>(key: string, ttl: number = 5 * 60 * 1000): T | null {
    try {
      const cacheKey = `${CACHE_PREFIX}${key}`
      const cached = localStorage.getItem(cacheKey)

      if (!cached) return null

      const item: CacheItem<T> = JSON.parse(cached)

      // Check version
      if (item.version !== CACHE_VERSION) {
        localStorage.removeItem(cacheKey)
        return null
      }

      // Check TTL
      const age = Date.now() - item.timestamp
      if (age > ttl) {
        localStorage.removeItem(cacheKey)
        return null
      }

      return item.data
    } catch (error) {
      console.warn('Failed to get cache:', error)
      return null
    }
  },

  /**
   * Remove cache item
   */
  remove(key: string): void {
    try {
      const cacheKey = `${CACHE_PREFIX}${key}`
      localStorage.removeItem(cacheKey)
    } catch (error) {
      console.warn('Failed to remove cache:', error)
    }
  },

  /**
   * Clear all cache items
   */
  clear(): void {
    try {
      const keys = Object.keys(localStorage)
      keys.forEach((key) => {
        if (key.startsWith(CACHE_PREFIX)) {
          localStorage.removeItem(key)
        }
      })
    } catch (error) {
      console.warn('Failed to clear cache:', error)
    }
  },

  /**
   * Get cache statistics
   */
  stats(): { size: number; keys: string[] } {
    try {
      const keys = Object.keys(localStorage).filter((k) => k.startsWith(CACHE_PREFIX))
      const size = keys.reduce((acc, key) => {
        const item = localStorage.getItem(key)
        return acc + (item?.length || 0)
      }, 0)

      return {
        size,
        keys: keys.map((k) => k.replace(CACHE_PREFIX, '')),
      }
    } catch (error) {
      return { size: 0, keys: [] }
    }
  },
}

export default cache
