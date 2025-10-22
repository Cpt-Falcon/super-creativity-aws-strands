"""
Global web cache using SQLite for cross-run persistence and efficiency.

Caches                 # Search results cache table - REMOVED, using URL-based caching insteads to maximize cache effectiveness across multiple
search backends and queries that fetch the same content.
"""
import sqlite3
import hashlib
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import logging
from urllib.parse import urlparse
import threading

logger = logging.getLogger(__name__)


class GlobalWebCache:
    """
    SQLite-based web cache that persists across all runs.
    Stores URL content as the primary cache key for maximum effectiveness.
    
    Strategy: Cache by actual URL fetched, not by search query.
    This allows multiple queries to benefit from the same URL content.
    
    Thread-safe with proper connection handling.
    """
    
    def __init__(self, cache_dir: Path):
        """
        Initialize the global web cache.
        
        Args:
            cache_dir: Directory to store the SQLite database
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.cache_dir / "global_web_cache.db"
        self._lock = threading.RLock()  # Thread-safe access
        self._init_database()
        
        logger.info(f"Global web cache initialized at {self.db_path} (URL-based caching)")
    
    def _get_connection(self):
        """Get a thread-safe SQLite connection."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.isolation_level = None  # Autocommit mode
        return conn
    
    def _init_database(self):
        """Create database tables if they don't exist."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                # URL content table - PRIMARY CACHE (indexed by actual URL)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS url_cache (
                        url_hash TEXT PRIMARY KEY,
                        url TEXT NOT NULL UNIQUE,
                        content TEXT NOT NULL,
                        content_length INTEGER,
                        status_code INTEGER,
                        timestamp TEXT NOT NULL,
                        hit_count INTEGER DEFAULT 0,
                        last_accessed TEXT,
                        domain TEXT
                    )
                """)
                
                # Query mapping table - tracks which queries used which URLs
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS query_url_map (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        url_hash TEXT NOT NULL,
                        search_backend TEXT,
                        timestamp TEXT NOT NULL,
                        FOREIGN KEY(url_hash) REFERENCES url_cache(url_hash),
                        UNIQUE(query, url_hash, search_backend)
                    )
                """)
                
                # Create indices for better performance
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_url_hash 
                    ON url_cache(url_hash)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_url_domain 
                    ON url_cache(domain)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_query_map 
                    ON query_url_map(query)
                """)
                
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_url_map_hash 
                    ON query_url_map(url_hash)
                """)
                
                conn.commit()
                logger.debug("Database tables initialized")
            
            except Exception as e:
                logger.error(f"Error initializing database: {e}")
                raise
            finally:
                conn.close()
    
    def _make_url_hash(self, url: str) -> str:
        """Create a unique hash for a URL."""
        return hashlib.sha256(url.encode()).hexdigest()
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc or 'unknown'
        except Exception:
            return 'unknown'
    
    def get_url_content(self, url: str) -> Optional[str]:
        """
        Retrieve cached URL content.
        
        Args:
            url: URL to retrieve content for
            
        Returns:
            Cached content if found, None otherwise
        """
        url_hash = self._make_url_hash(url)
        
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT content FROM url_cache 
                    WHERE url_hash = ?
                """, (url_hash,))
                
                result = cursor.fetchone()
                
                if result:
                    # Update hit count and last accessed
                    cursor.execute("""
                        UPDATE url_cache 
                        SET hit_count = hit_count + 1, last_accessed = ?
                        WHERE url_hash = ?
                    """, (datetime.now().isoformat(), url_hash))
                    conn.commit()
                    conn.close()
                    
                    logger.info(f"Cache HIT for URL: {url[:60]}...")
                    return result[0]
                
                conn.close()
                logger.info(f"Cache MISS for URL: {url[:60]}...")
                return None
        
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None
    
    def cache_url_content(self, url: str, content: str, status_code: int = 200):
        """
        Cache URL content with status code.
        
        Args:
            url: URL
            content: Content to cache
            status_code: HTTP status code (default 200)
        """
        url_hash = self._make_url_hash(url)
        timestamp = datetime.now().isoformat()
        content_length = len(content)
        domain = self._get_domain(url)
        
        logger.debug(f"cache_url_content called for: {url[:60]}... (size: {content_length} bytes)")
        
        try:
            with self._lock:
                logger.debug(f"Acquired lock for caching URL")
                conn = self._get_connection()
                cursor = conn.cursor()
                
                try:
                    logger.debug(f"Attempting INSERT for URL hash: {url_hash[:16]}...")
                    cursor.execute("""
                        INSERT INTO url_cache 
                        (url_hash, url, content, content_length, status_code, timestamp, hit_count, last_accessed, domain)
                        VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
                    """, (url_hash, url, content, content_length, status_code, timestamp, timestamp, domain))
                    
                    conn.commit()
                    logger.info(f"Cached URL content: {url[:60]}... ({content_length} bytes)")
                
                except sqlite3.IntegrityError as ie:
                    logger.debug(f"IntegrityError (URL already exists), attempting UPDATE: {ie}")
                    # URL already exists, update it
                    cursor.execute("""
                        UPDATE url_cache 
                        SET content = ?, content_length = ?, status_code = ?, timestamp = ?, last_accessed = ?
                        WHERE url_hash = ?
                    """, (content, content_length, status_code, timestamp, timestamp, url_hash))
                    conn.commit()
                    logger.info(f"Updated cached URL: {url[:60]}...")
                
                finally:
                    conn.close()
        
        except Exception as e:
            logger.error(f"Error caching URL content: {e}", exc_info=True)
    
    def link_query_to_urls(
        self, 
        query: str, 
        urls: List[str], 
        search_backend: str = 'unknown'
    ):
        """
        Link a search query to the URLs it fetched from.
        Useful for analytics and understanding which queries benefit from which URLs.
        
        Args:
            query: The search query
            urls: List of URLs that were fetched for this query
            search_backend: The search backend used (e.g., 'duckduckgo', 'bing')
        """
        timestamp = datetime.now().isoformat()
        
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                try:
                    for url in urls:
                        url_hash = self._make_url_hash(url)
                        
                        try:
                            cursor.execute("""
                                INSERT INTO query_url_map 
                                (query, url_hash, search_backend, timestamp)
                                VALUES (?, ?, ?, ?)
                            """, (query, url_hash, search_backend, timestamp))
                        except sqlite3.IntegrityError:
                            # Mapping already exists, skip
                            pass
                    
                    conn.commit()
                    logger.info(f"Linked query '{query[:40]}...' to {len(urls)} URLs")
                
                finally:
                    conn.close()
        
        except Exception as e:
            logger.error(f"Error linking query to URLs: {e}")
    
    def get_urls_for_query(self, query: str) -> List[Tuple[str, int]]:
        """
        Get all URLs that were used for a particular query.
        Returns URLs with their current hit counts.
        
        Args:
            query: Search query
            
        Returns:
            List of (url, hit_count) tuples
        """
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                try:
                    cursor.execute("""
                        SELECT DISTINCT uc.url, uc.hit_count
                        FROM url_cache uc
                        JOIN query_url_map qum ON uc.url_hash = qum.url_hash
                        WHERE qum.query = ?
                        ORDER BY uc.hit_count DESC
                    """, (query,))
                    
                    results = cursor.fetchall()
                    return results
                
                finally:
                    conn.close()
        
        except Exception as e:
            logger.error(f"Error getting URLs for query: {e}")
            return []
    
    def get_top_urls_by_hits(self, limit: int = 10) -> List[Tuple[str, str, int]]:
        """
        Get the most frequently accessed URLs in cache.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of (url, domain, hit_count) tuples
        """
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                try:
                    cursor.execute("""
                        SELECT url, domain, hit_count
                        FROM url_cache
                        ORDER BY hit_count DESC
                        LIMIT ?
                    """, (limit,))
                    
                    results = cursor.fetchall()
                    return results
                
                finally:
                    conn.close()
        
        except Exception as e:
            logger.error(f"Error getting top URLs: {e}")
            return []
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                try:
                    # URL cache stats
                    cursor.execute("SELECT COUNT(*), SUM(hit_count), SUM(content_length) FROM url_cache")
                    url_count, total_hits, total_size = cursor.fetchone()
                    
                    # Top domains
                    cursor.execute("""
                        SELECT domain, COUNT(*), SUM(hit_count) 
                        FROM url_cache 
                        GROUP BY domain 
                        ORDER BY SUM(hit_count) DESC 
                        LIMIT 10
                    """)
                    top_domains = cursor.fetchall()
                    
                    # Top URLs
                    cursor.execute("""
                        SELECT url, hit_count 
                        FROM url_cache 
                        ORDER BY hit_count DESC 
                        LIMIT 5
                    """)
                    top_urls = cursor.fetchall()
                    
                    # Query stats
                    cursor.execute("""
                        SELECT COUNT(DISTINCT query) FROM query_url_map
                    """)
                    total_queries = cursor.fetchone()[0]
                    
                    return {
                        "url_cache": {
                            "total_urls_cached": url_count or 0,
                            "total_hits": total_hits or 0,
                            "total_size_bytes": total_size or 0,
                            "top_urls": [{"url": u[:60], "hits": h} for u, h in top_urls],
                            "top_domains": [{"domain": d, "count": c, "hits": h} for d, c, h in top_domains]
                        },
                        "query_mappings": {
                            "total_unique_queries": total_queries or 0
                        },
                        "database_path": str(self.db_path)
                    }
                
                finally:
                    conn.close()
        
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "url_cache": {"total_urls_cached": 0, "total_hits": 0, "total_size_bytes": 0},
                "query_mappings": {"total_unique_queries": 0},
                "database_path": str(self.db_path)
            }
    
    def bulk_url_lookup(self, urls: List[str]) -> Dict[str, Optional[str]]:
        """
        Perform bulk URL cache lookup.
        
        Args:
            urls: List of URLs to look up
            
        Returns:
            Dictionary mapping URL to cached content (or None if not cached)
        """
        results = {}
        
        for url in urls:
            results[url] = self.get_url_content(url)
        
        hits = sum(1 for v in results.values() if v is not None)
        logger.info(f"Bulk URL lookup: {hits}/{len(urls)} cache hits")
        
        return results
    
    def bulk_url_cache(self, url_content_map: Dict[str, str]):
        """
        Cache multiple URLs at once.
        
        Args:
            url_content_map: Dictionary mapping URL to content
        """
        try:
            for url, content in url_content_map.items():
                self.cache_url_content(url, content)
            
            logger.info(f"Bulk cached {len(url_content_map)} URLs")
        except Exception as e:
            logger.error(f"Error bulk caching URLs: {e}")
    
    def clear_old_entries(self, days: int = 30):
        """
        Clear cache entries older than specified days.
        
        Args:
            days: Number of days to keep entries
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()
        
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                
                try:
                    cursor.execute("DELETE FROM url_cache WHERE timestamp < ?", (cutoff_iso,))
                    cache_deleted = cursor.rowcount
                    
                    cursor.execute("DELETE FROM query_url_map WHERE timestamp < ?", (cutoff_iso,))
                    query_deleted = cursor.rowcount
                    
                    conn.commit()
                    logger.info(f"Cleared {cache_deleted} cache entries and {query_deleted} query mappings older than {days} days")
                
                finally:
                    conn.close()
        
        except Exception as e:
            logger.error(f"Error clearing old cache entries: {e}")
