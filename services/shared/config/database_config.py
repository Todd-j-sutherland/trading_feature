"""Database configuration for trading services"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass 
class DatabaseConfig:
    """Database configuration"""
    primary_db_path: str
    paper_trading_db_path: str
    
    # Connection settings
    wal_mode: bool = True
    connection_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 0.1
    
    # Performance settings
    cache_size: int = 10000
    temp_store: str = "memory"
    synchronous: str = "NORMAL"
    
    # Maintenance settings
    auto_vacuum: bool = True
    vacuum_interval_hours: int = 24
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """Create database configuration from environment variables"""
        
        # Default paths (relative to project root)
        default_primary = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'data', 'trading_predictions.db'
        )
        default_paper_trading = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', 'ig_markets_paper_trading', 'data', 'paper_trading.db'
        )
        
        return cls(
            primary_db_path=os.getenv("PRIMARY_DB_PATH", default_primary),
            paper_trading_db_path=os.getenv("PAPER_TRADING_DB_PATH", default_paper_trading),
            wal_mode=os.getenv("DB_WAL_MODE", "true").lower() == "true",
            connection_timeout=int(os.getenv("DB_CONNECTION_TIMEOUT", "30")),
            retry_attempts=int(os.getenv("DB_RETRY_ATTEMPTS", "3")),
            retry_delay=float(os.getenv("DB_RETRY_DELAY", "0.1")),
            cache_size=int(os.getenv("DB_CACHE_SIZE", "10000")),
            temp_store=os.getenv("DB_TEMP_STORE", "memory"),
            synchronous=os.getenv("DB_SYNCHRONOUS", "NORMAL"),
            auto_vacuum=os.getenv("DB_AUTO_VACUUM", "true").lower() == "true",
            vacuum_interval_hours=int(os.getenv("DB_VACUUM_INTERVAL_HOURS", "24"))
        )
    
    def get_connection_params(self) -> Dict[str, Any]:
        """Get connection parameters for SQLite"""
        params = {}
        
        if self.wal_mode:
            params["journal_mode"] = "WAL"
            params["synchronous"] = self.synchronous
            params["cache_size"] = self.cache_size
            params["temp_store"] = self.temp_store
        
        if self.auto_vacuum:
            params["auto_vacuum"] = "INCREMENTAL"
        
        return params
    
    def get_absolute_path(self, relative_path: str) -> str:
        """Convert relative database path to absolute"""
        if os.path.isabs(relative_path):
            return relative_path
        
        # Convert relative to absolute from project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return os.path.abspath(os.path.join(project_root, relative_path))


# Database schemas for backwards compatibility
TRADING_PREDICTIONS_SCHEMA = {
    'predictions': """
        CREATE TABLE IF NOT EXISTS predictions (
            prediction_id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            prediction_timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            confidence REAL NOT NULL,
            entry_price REAL,
            target_price REAL,
            prediction_details TEXT
        )
    """,
    'outcomes': """
        CREATE TABLE IF NOT EXISTS outcomes (
            outcome_id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id TEXT NOT NULL,
            evaluation_timestamp TEXT NOT NULL,
            outcome_type TEXT,
            success_rate REAL,
            actual_return REAL,
            FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id)
        )
    """,
    'market_aware_predictions': """
        CREATE TABLE IF NOT EXISTS market_aware_predictions (
            prediction_id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            current_price REAL,
            predicted_price REAL,
            price_change_pct REAL,
            confidence REAL,
            market_context TEXT,
            market_trend_pct REAL,
            buy_threshold_used REAL,
            recommended_action TEXT,
            tech_score REAL,
            news_sentiment REAL,
            volume_trend REAL,
            prediction_details TEXT,
            model_used TEXT
        )
    """,
    'enhanced_features': """
        CREATE TABLE IF NOT EXISTS enhanced_features (
            feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            sentiment_score REAL,
            news_volume INTEGER,
            reddit_sentiment REAL,
            rsi_14 REAL,
            moving_avg_10 REAL,
            moving_avg_20 REAL,
            moving_avg_50 REAL,
            macd_line REAL,
            macd_signal REAL,
            bollinger_upper REAL,
            bollinger_lower REAL,
            volume_ratio REAL,
            momentum_score REAL,
            market_context TEXT,
            features_json TEXT
        )
    """
}

PAPER_TRADING_SCHEMA = {
    'positions': """
        CREATE TABLE IF NOT EXISTS positions (
            position_id TEXT PRIMARY KEY,
            symbol TEXT NOT NULL,
            action TEXT NOT NULL,
            shares INTEGER NOT NULL,
            entry_price REAL NOT NULL,
            current_price REAL,
            stop_loss REAL,
            profit_target REAL,
            status TEXT DEFAULT 'OPEN',
            entry_timestamp TEXT NOT NULL,
            exit_timestamp TEXT,
            pnl REAL,
            confidence REAL
        )
    """,
    'account_balance': """
        CREATE TABLE IF NOT EXISTS account_balance (
            balance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            balance REAL NOT NULL,
            available_funds REAL NOT NULL,
            invested_amount REAL NOT NULL,
            unrealized_pnl REAL,
            realized_pnl REAL,
            timestamp TEXT NOT NULL
        )
    """,
    'trading_config': """
        CREATE TABLE IF NOT EXISTS trading_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """
}

# Create indexes for performance
TRADING_PREDICTIONS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_predictions_timestamp ON predictions(prediction_timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_predictions_symbol ON predictions(symbol)",
    "CREATE INDEX IF NOT EXISTS idx_outcomes_prediction_id ON outcomes(prediction_id)",
    "CREATE INDEX IF NOT EXISTS idx_outcomes_eval_time ON outcomes(evaluation_timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_enhanced_features_symbol_time ON enhanced_features(symbol, timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_market_aware_timestamp ON market_aware_predictions(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_market_aware_symbol ON market_aware_predictions(symbol)"
]

PAPER_TRADING_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol)",
    "CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status)",
    "CREATE INDEX IF NOT EXISTS idx_positions_entry_time ON positions(entry_timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_account_balance_time ON account_balance(timestamp)"
]


class DatabaseSchemaManager:
    """Manages database schema creation and updates"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
    
    def ensure_trading_schema(self):
        """Ensure trading predictions database has correct schema"""
        from ..utils.database_utils import DatabaseManager
        
        db = DatabaseManager(self.config.primary_db_path)
        
        # Create tables
        for table_name, schema in TRADING_PREDICTIONS_SCHEMA.items():
            db.execute_query(schema)
        
        # Create indexes
        for index_sql in TRADING_PREDICTIONS_INDEXES:
            try:
                db.execute_query(index_sql)
            except Exception as e:
                print(f"Warning: Could not create index: {e}")
    
    def ensure_paper_trading_schema(self):
        """Ensure paper trading database has correct schema"""
        from ..utils.database_utils import DatabaseManager
        
        db = DatabaseManager(self.config.paper_trading_db_path)
        
        # Create tables
        for table_name, schema in PAPER_TRADING_SCHEMA.items():
            db.execute_query(schema)
        
        # Create indexes
        for index_sql in PAPER_TRADING_INDEXES:
            try:
                db.execute_query(index_sql)
            except Exception as e:
                print(f"Warning: Could not create index: {e}")
    
    def ensure_all_schemas(self):
        """Ensure all database schemas are up to date"""
        self.ensure_trading_schema()
        self.ensure_paper_trading_schema()


# Global database configuration
database_config = DatabaseConfig.from_env()


def get_database_config() -> DatabaseConfig:
    """Get database configuration"""
    return database_config


def get_primary_db_path() -> str:
    """Get primary database path"""
    return database_config.primary_db_path


def get_paper_trading_db_path() -> str:
    """Get paper trading database path"""
    return database_config.paper_trading_db_path


def ensure_database_schemas():
    """Ensure all database schemas are initialized"""
    schema_manager = DatabaseSchemaManager(database_config)
    schema_manager.ensure_all_schemas()


def get_connection_string(db_type: str = "primary") -> str:
    """Get connection string for database"""
    if db_type == "primary":
        return database_config.primary_db_path
    elif db_type == "paper_trading":
        return database_config.paper_trading_db_path
    else:
        raise ValueError(f"Unknown database type: {db_type}")
