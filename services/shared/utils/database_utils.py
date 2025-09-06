"""Database utilities for trading services with backwards compatibility"""

import sqlite3
import time
import os
from typing import Optional, Callable, Any, Dict
from contextlib import contextmanager


def get_db_connection(db_path: str, wal_mode: bool = True) -> sqlite3.Connection:
    """Get database connection with proper configuration"""
    
    # Ensure directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    # Create connection
    conn = sqlite3.connect(db_path)
    
    # Enable WAL mode for better concurrency (critical for production)
    if wal_mode:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=memory")
    
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys=ON")
    
    return conn


def safe_db_operation(operation: Callable, retries: int = 3, retry_delay: float = 0.1) -> Any:
    """Execute database operation with retry logic for lock handling"""
    
    for attempt in range(retries):
        try:
            return operation()
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < retries - 1:
                # Exponential backoff
                wait_time = retry_delay * (2 ** attempt)
                time.sleep(wait_time)
                continue
            else:
                raise
        except Exception:
            # Other exceptions should not be retried
            raise


@contextmanager
def db_transaction(db_path: str):
    """Database transaction context manager with automatic rollback"""
    conn = None
    try:
        conn = get_db_connection(db_path)
        conn.execute("BEGIN TRANSACTION")
        yield conn
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


@contextmanager 
def db_cursor(db_path: str):
    """Database cursor context manager"""
    conn = None
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


class DatabaseManager:
    """Database manager for services with connection pooling"""
    
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure database and directory exist"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        # Create database if it doesn't exist
        if not os.path.exists(self.db_path):
            conn = get_db_connection(self.db_path)
            conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> Any:
        """Execute a query and return results"""
        def operation():
            with db_cursor(self.db_path) as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                return cursor.rowcount
        
        return safe_db_operation(operation)
    
    def execute_many(self, query: str, params_list: list) -> int:
        """Execute query with multiple parameter sets"""
        def operation():
            with db_cursor(self.db_path) as cursor:
                cursor.executemany(query, params_list)
                return cursor.rowcount
        
        return safe_db_operation(operation)
    
    def fetch_one(self, query: str, params: tuple = ()) -> Optional[tuple]:
        """Fetch single row"""
        def operation():
            with db_cursor(self.db_path) as cursor:
                cursor.execute(query, params)
                return cursor.fetchone()
        
        return safe_db_operation(operation)
    
    def fetch_all(self, query: str, params: tuple = ()) -> list:
        """Fetch all rows"""
        def operation():
            with db_cursor(self.db_path) as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        
        return safe_db_operation(operation)
    
    def insert_and_get_id(self, query: str, params: tuple = ()) -> int:
        """Insert row and return the ID"""
        def operation():
            with db_cursor(self.db_path) as cursor:
                cursor.execute(query, params)
                return cursor.lastrowid
        
        return safe_db_operation(operation)
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """
        result = self.fetch_one(query, (table_name,))
        return result is not None
    
    def get_table_schema(self, table_name: str) -> list:
        """Get table schema information"""
        query = f"PRAGMA table_info({table_name})"
        return self.fetch_all(query)
    
    def vacuum_database(self):
        """Vacuum database to reclaim space"""
        def operation():
            conn = get_db_connection(self.db_path)
            conn.execute("VACUUM")
            conn.close()
        
        safe_db_operation(operation)
    
    def get_database_size(self) -> Dict[str, Any]:
        """Get database size information"""
        if not os.path.exists(self.db_path):
            return {'size_bytes': 0, 'size_mb': 0}
        
        size_bytes = os.path.getsize(self.db_path)
        size_mb = size_bytes / (1024 * 1024)
        
        return {
            'size_bytes': size_bytes,
            'size_mb': round(size_mb, 2),
            'path': self.db_path
        }


class LegacyDatabaseAdapter:
    """Adapter for legacy database compatibility"""
    
    def __init__(self, primary_db: str, legacy_dbs: Optional[list] = None):
        self.primary_db = DatabaseManager(primary_db)
        self.legacy_dbs = {}
        
        if legacy_dbs:
            for db_path in legacy_dbs:
                name = os.path.basename(db_path).replace('.db', '')
                self.legacy_dbs[name] = DatabaseManager(db_path)
    
    def sync_data(self, table_name: str, from_db: str, to_db: str = 'primary'):
        """Sync data between databases"""
        source_db = self.legacy_dbs.get(from_db) if from_db != 'primary' else self.primary_db
        target_db = self.primary_db if to_db == 'primary' else self.legacy_dbs.get(to_db)
        
        if not source_db or not target_db:
            raise ValueError(f"Database not found: {from_db} -> {to_db}")
        
        # Get all data from source
        data = source_db.fetch_all(f"SELECT * FROM {table_name}")
        
        if data:
            # Get column count
            columns = len(data[0])
            placeholders = ','.join(['?' for _ in range(columns)])
            
            # Insert into target (using INSERT OR REPLACE for conflict handling)
            insert_query = f"INSERT OR REPLACE INTO {table_name} VALUES ({placeholders})"
            target_db.execute_many(insert_query, data)
    
    def migrate_legacy_data(self):
        """Migrate data from legacy databases to primary"""
        for db_name, db_manager in self.legacy_dbs.items():
            try:
                # Get all tables in legacy database
                tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
                tables = db_manager.fetch_all(tables_query)
                
                for (table_name,) in tables:
                    if not table_name.startswith('sqlite_'):
                        self.sync_data(table_name, db_name, 'primary')
                        
            except Exception as e:
                print(f"Warning: Failed to migrate from {db_name}: {str(e)}")


# Global database paths for backwards compatibility
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', '..', 'data', 'trading_predictions.db'
)

PAPER_TRADING_DB_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', '..', 'ig_markets_paper_trading', 'data', 'paper_trading.db'
)


def get_default_db_manager() -> DatabaseManager:
    """Get default database manager for trading predictions"""
    return DatabaseManager(DEFAULT_DB_PATH)


def get_paper_trading_db_manager() -> DatabaseManager:
    """Get database manager for paper trading"""
    return DatabaseManager(PAPER_TRADING_DB_PATH)
