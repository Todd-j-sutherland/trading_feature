#!/usr/bin/env python3
"""
Test Data Fixtures and Test Database Management

This module provides test data fixtures, test database setup/teardown,
and test data management utilities for the trading microservices test suite.

Author: Trading System Testing Team
Date: September 14, 2025
"""

import os
import json
import sqlite3
import tempfile
import shutil
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Any
import uuid
import random

class TestDataFixtures:
    """Comprehensive test data fixtures for trading system testing"""
    
    @staticmethod
    def get_sample_market_data() -> Dict[str, Any]:
        """Generate realistic market data for testing"""
        symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX", "COL.AX", "BHP.AX"]
        
        market_data = {}
        
        for symbol in symbols:
            # Generate realistic stock data
            base_price = random.uniform(50, 150)
            price_change = random.uniform(-2, 2)
            
            market_data[symbol] = {
                "symbol": symbol,
                "current_price": round(base_price + price_change, 2),
                "price_change": round(price_change, 2),
                "price_change_percent": round((price_change / base_price) * 100, 2),
                "volume": random.randint(100000, 5000000),
                "high": round(base_price + abs(price_change) + random.uniform(0, 1), 2),
                "low": round(base_price - abs(price_change) - random.uniform(0, 1), 2),
                "open": round(base_price + random.uniform(-1, 1), 2),
                "previous_close": round(base_price, 2),
                "market_cap": random.randint(10000000000, 200000000000),
                "pe_ratio": round(random.uniform(10, 25), 2),
                "dividend_yield": round(random.uniform(2, 7), 2),
                "rsi": round(random.uniform(30, 70), 2),
                "sma_20": round(base_price + random.uniform(-5, 5), 2),
                "sma_50": round(base_price + random.uniform(-10, 10), 2),
                "timestamp": datetime.now().isoformat()
            }
            
        return market_data
    
    @staticmethod
    def get_sample_sentiment_data() -> Dict[str, Any]:
        """Generate sample sentiment analysis data"""
        symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX"]
        
        sentiment_data = {}
        
        for symbol in symbols:
            sentiment_data[symbol] = {
                "symbol": symbol,
                "sentiment_score": round(random.uniform(-1, 1), 3),
                "news_confidence": round(random.uniform(0.5, 1.0), 3),
                "news_quality_score": round(random.uniform(0.6, 1.0), 3),
                "article_count": random.randint(5, 50),
                "positive_articles": random.randint(0, 25),
                "negative_articles": random.randint(0, 15),
                "neutral_articles": random.randint(5, 20),
                "trending_topics": [
                    "earnings", "dividend", "financial results", "market analysis"
                ][:random.randint(1, 4)],
                "last_updated": datetime.now().isoformat()
            }
            
        return sentiment_data
    
    @staticmethod
    def get_sample_predictions() -> List[Dict[str, Any]]:
        """Generate sample prediction data"""
        symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX"]
        actions = ["BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"]
        
        predictions = []
        
        for i in range(20):  # 20 sample predictions
            symbol = random.choice(symbols)
            action = random.choice(actions)
            
            # Generate weighted confidence based on action
            if action in ["STRONG_BUY", "STRONG_SELL"]:
                confidence = round(random.uniform(0.8, 0.95), 3)
            elif action in ["BUY", "SELL"]:
                confidence = round(random.uniform(0.6, 0.8), 3)
            else:  # HOLD
                confidence = round(random.uniform(0.4, 0.7), 3)
                
            prediction = {
                "prediction_id": str(uuid.uuid4()),
                "symbol": symbol,
                "action": action,
                "confidence": confidence,
                "prediction_date": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
                "prediction_time": (datetime.now() - timedelta(hours=random.randint(0, 24))).strftime("%H:%M:%S"),
                "timestamp": (datetime.now() - timedelta(hours=random.randint(0, 72))).isoformat(),
                "technical_score": round(random.uniform(0, 100), 1),
                "sentiment_score": round(random.uniform(-1, 1), 3),
                "volume_score": round(random.uniform(0, 1), 3),
                "market_context": random.choice(["BULL", "BEAR", "NEUTRAL", "VOLATILE"]),
                "reasoning": f"Technical analysis indicates {action.lower()} signal with {confidence*100:.1f}% confidence",
                "risk_level": random.choice(["LOW", "MEDIUM", "HIGH"]),
                "target_price": round(random.uniform(50, 150), 2),
                "stop_loss": round(random.uniform(40, 140), 2)
            }
            
            predictions.append(prediction)
            
        return predictions
    
    @staticmethod
    def get_sample_trades() -> List[Dict[str, Any]]:
        """Generate sample paper trading data"""
        symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX"]
        trade_types = ["BUY", "SELL"]
        
        trades = []
        
        for i in range(15):  # 15 sample trades
            symbol = random.choice(symbols)
            trade_type = random.choice(trade_types)
            quantity = random.randint(10, 1000)
            price = round(random.uniform(50, 150), 2)
            
            trade = {
                "trade_id": str(uuid.uuid4()),
                "symbol": symbol,
                "trade_type": trade_type,
                "quantity": quantity,
                "price": price,
                "total_value": round(quantity * price, 2),
                "commission": round(quantity * price * 0.001, 2),  # 0.1% commission
                "trade_date": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
                "trade_time": (datetime.now() - timedelta(hours=random.randint(0, 24))).strftime("%H:%M:%S"),
                "timestamp": (datetime.now() - timedelta(hours=random.randint(0, 72))).isoformat(),
                "order_type": random.choice(["MARKET", "LIMIT", "STOP"]),
                "status": random.choice(["EXECUTED", "PENDING", "CANCELLED"]),
                "broker": "IG_MARKETS",
                "account_id": f"ACC{random.randint(1000, 9999)}",
                "reference": f"REF{random.randint(100000, 999999)}",
                "profit_loss": round(random.uniform(-500, 500), 2) if trade_type == "SELL" else 0,
                "notes": f"Paper trading {trade_type.lower()} order for {symbol}"
            }
            
            trades.append(trade)
            
        return trades
    
    @staticmethod
    def get_sample_ml_training_data() -> List[Dict[str, Any]]:
        """Generate sample ML training data"""
        symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX"]
        
        training_data = []
        
        for symbol in symbols:
            for i in range(50):  # 50 training samples per symbol
                # Generate feature vector
                features = {
                    "price_change_1d": round(random.uniform(-5, 5), 2),
                    "price_change_5d": round(random.uniform(-10, 10), 2),
                    "volume_ratio": round(random.uniform(0.5, 2.0), 2),
                    "rsi": round(random.uniform(20, 80), 1),
                    "macd": round(random.uniform(-2, 2), 3),
                    "bollinger_position": round(random.uniform(0, 1), 3),
                    "sentiment_score": round(random.uniform(-1, 1), 3),
                    "market_volatility": round(random.uniform(10, 40), 1),
                    "sector_performance": round(random.uniform(-3, 3), 2)
                }
                
                # Generate target (simplified binary classification)
                target = 1 if random.random() > 0.5 else 0  # 1 = profitable, 0 = not profitable
                
                training_sample = {
                    "sample_id": str(uuid.uuid4()),
                    "symbol": symbol,
                    "features": features,
                    "target": target,
                    "date": (datetime.now() - timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d"),
                    "timestamp": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat(),
                    "feature_version": "v1.0",
                    "data_quality": round(random.uniform(0.8, 1.0), 3)
                }
                
                training_data.append(training_sample)
                
        return training_data

class TestDatabaseManager:
    """Manage test databases for testing purposes"""
    
    def __init__(self, test_dir: str = None):
        self.test_dir = test_dir or tempfile.mkdtemp(prefix="trading_test_")
        self.databases = {}
        
    def create_test_database(self, db_name: str) -> str:
        """Create a test database"""
        db_path = os.path.join(self.test_dir, f"{db_name}.db")
        
        conn = sqlite3.connect(db_path)
        
        # Create tables based on database type
        if db_name == "trading_predictions":
            self._create_predictions_tables(conn)
        elif db_name == "paper_trading":
            self._create_paper_trading_tables(conn)
        elif db_name == "sentiment_analysis":
            self._create_sentiment_tables(conn)
        elif db_name == "ml_training":
            self._create_ml_training_tables(conn)
            
        conn.close()
        
        self.databases[db_name] = db_path
        return db_path
        
    def _create_predictions_tables(self, conn: sqlite3.Connection):
        """Create prediction database tables"""
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                confidence REAL NOT NULL,
                prediction_date TEXT NOT NULL,
                prediction_time TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                technical_score REAL,
                sentiment_score REAL,
                volume_score REAL,
                market_context TEXT,
                reasoning TEXT,
                risk_level TEXT,
                target_price REAL,
                stop_loss REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediction_outcomes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id TEXT NOT NULL,
                actual_outcome TEXT,
                profit_loss REAL,
                accuracy_score REAL,
                evaluation_date TEXT,
                evaluation_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prediction_id) REFERENCES predictions (prediction_id)
            )
        """)
        
        conn.commit()
        
    def _create_paper_trading_tables(self, conn: sqlite3.Connection):
        """Create paper trading database tables"""
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                trade_type TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                total_value REAL NOT NULL,
                commission REAL DEFAULT 0,
                trade_date TEXT NOT NULL,
                trade_time TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                order_type TEXT DEFAULT 'MARKET',
                status TEXT DEFAULT 'EXECUTED',
                broker TEXT DEFAULT 'IG_MARKETS',
                account_id TEXT,
                reference TEXT,
                profit_loss REAL DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                average_cost REAL NOT NULL,
                current_price REAL,
                market_value REAL,
                profit_loss REAL,
                last_updated TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        
    def _create_sentiment_tables(self, conn: sqlite3.Connection):
        """Create sentiment analysis database tables"""
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sentiment_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                sentiment_score REAL NOT NULL,
                news_confidence REAL NOT NULL,
                news_quality_score REAL NOT NULL,
                article_count INTEGER DEFAULT 0,
                positive_articles INTEGER DEFAULT 0,
                negative_articles INTEGER DEFAULT 0,
                neutral_articles INTEGER DEFAULT 0,
                trending_topics TEXT,
                analysis_date TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                source TEXT,
                url TEXT,
                sentiment_score REAL,
                relevance_score REAL,
                published_date TEXT,
                analyzed_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        
    def _create_ml_training_tables(self, conn: sqlite3.Connection):
        """Create ML training database tables"""
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sample_id TEXT UNIQUE NOT NULL,
                symbol TEXT NOT NULL,
                features TEXT NOT NULL,  -- JSON string
                target INTEGER NOT NULL,
                date TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                feature_version TEXT DEFAULT 'v1.0',
                data_quality REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                symbol TEXT,
                accuracy REAL NOT NULL,
                precision_score REAL,
                recall REAL,
                f1_score REAL,
                training_date TEXT NOT NULL,
                validation_date TEXT,
                model_version TEXT,
                parameters TEXT,  -- JSON string
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        
    def populate_test_data(self, db_name: str, fixtures: TestDataFixtures):
        """Populate test database with sample data"""
        if db_name not in self.databases:
            raise ValueError(f"Database {db_name} not created")
            
        db_path = self.databases[db_name]
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            if db_name == "trading_predictions":
                predictions = fixtures.get_sample_predictions()
                for pred in predictions:
                    cursor.execute("""
                        INSERT INTO predictions (
                            prediction_id, symbol, action, confidence, prediction_date,
                            prediction_time, timestamp, technical_score, sentiment_score,
                            volume_score, market_context, reasoning, risk_level,
                            target_price, stop_loss
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        pred["prediction_id"], pred["symbol"], pred["action"],
                        pred["confidence"], pred["prediction_date"], pred["prediction_time"],
                        pred["timestamp"], pred["technical_score"], pred["sentiment_score"],
                        pred["volume_score"], pred["market_context"], pred["reasoning"],
                        pred["risk_level"], pred["target_price"], pred["stop_loss"]
                    ))
                    
            elif db_name == "paper_trading":
                trades = fixtures.get_sample_trades()
                for trade in trades:
                    cursor.execute("""
                        INSERT INTO trades (
                            trade_id, symbol, trade_type, quantity, price, total_value,
                            commission, trade_date, trade_time, timestamp, order_type,
                            status, broker, account_id, reference, profit_loss, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        trade["trade_id"], trade["symbol"], trade["trade_type"],
                        trade["quantity"], trade["price"], trade["total_value"],
                        trade["commission"], trade["trade_date"], trade["trade_time"],
                        trade["timestamp"], trade["order_type"], trade["status"],
                        trade["broker"], trade["account_id"], trade["reference"],
                        trade["profit_loss"], trade["notes"]
                    ))
                    
            elif db_name == "sentiment_analysis":
                sentiment_data = fixtures.get_sample_sentiment_data()
                for symbol, data in sentiment_data.items():
                    cursor.execute("""
                        INSERT INTO sentiment_analysis (
                            symbol, sentiment_score, news_confidence, news_quality_score,
                            article_count, positive_articles, negative_articles,
                            neutral_articles, trending_topics, analysis_date, last_updated
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        symbol, data["sentiment_score"], data["news_confidence"],
                        data["news_quality_score"], data["article_count"],
                        data["positive_articles"], data["negative_articles"],
                        data["neutral_articles"], json.dumps(data["trending_topics"]),
                        datetime.now().strftime("%Y-%m-%d"), data["last_updated"]
                    ))
                    
            elif db_name == "ml_training":
                training_data = fixtures.get_sample_ml_training_data()
                for sample in training_data:
                    cursor.execute("""
                        INSERT INTO training_data (
                            sample_id, symbol, features, target, date, timestamp,
                            feature_version, data_quality
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        sample["sample_id"], sample["symbol"],
                        json.dumps(sample["features"]), sample["target"],
                        sample["date"], sample["timestamp"],
                        sample["feature_version"], sample["data_quality"]
                    ))
                    
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
            
    def get_database_path(self, db_name: str) -> str:
        """Get path to test database"""
        return self.databases.get(db_name)
        
    def cleanup(self):
        """Clean up test databases and temporary directory"""
        for db_path in self.databases.values():
            if os.path.exists(db_path):
                os.unlink(db_path)
                
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            
        self.databases.clear()

class TestRedisManager:
    """Manage test Redis instance for testing"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/15"):  # Use test database 15
        self.redis_url = redis_url
        self.redis_client = None
        
    def setup_test_redis(self):
        """Setup test Redis connection"""
        try:
            self.redis_client = redis.Redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            
            # Clear test database
            self.redis_client.flushdb()
            
            return self.redis_client
            
        except Exception as e:
            print(f"Warning: Could not connect to Redis for testing: {e}")
            return None
            
    def populate_test_cache(self, fixtures: TestDataFixtures):
        """Populate Redis with test cache data"""
        if not self.redis_client:
            return
            
        # Cache market data
        market_data = fixtures.get_sample_market_data()
        for symbol, data in market_data.items():
            cache_key = f"market_data:{symbol}"
            self.redis_client.setex(cache_key, 3600, json.dumps(data))  # 1 hour TTL
            
        # Cache predictions
        predictions = fixtures.get_sample_predictions()
        for prediction in predictions[:5]:  # Cache first 5 predictions
            cache_key = f"prediction:{prediction['symbol']}"
            self.redis_client.setex(cache_key, 1800, json.dumps(prediction))  # 30 min TTL
            
    def cleanup(self):
        """Clean up test Redis data"""
        if self.redis_client:
            self.redis_client.flushdb()
            self.redis_client.close()

class TestConfigManager:
    """Manage test configuration"""
    
    def __init__(self, test_dir: str):
        self.test_dir = test_dir
        self.config_file = os.path.join(test_dir, "test_config.json")
        
    def create_test_config(self, db_manager: TestDatabaseManager, redis_manager: TestRedisManager):
        """Create test configuration file"""
        config = {
            "testing": True,
            "environment": "test",
            "databases": {
                "trading_predictions": db_manager.get_database_path("trading_predictions"),
                "paper_trading": db_manager.get_database_path("paper_trading"),
                "sentiment_analysis": db_manager.get_database_path("sentiment_analysis"),
                "ml_training": db_manager.get_database_path("ml_training")
            },
            "redis": {
                "url": redis_manager.redis_url,
                "test_mode": True
            },
            "services": {
                "socket_base_path": "/tmp/test_trading_",
                "timeout": 10,
                "retry_attempts": 2
            },
            "logging": {
                "level": "DEBUG",
                "file": os.path.join(self.test_dir, "test.log")
            },
            "performance": {
                "cache_ttl": 300,  # 5 minutes for testing
                "max_connections": 10,
                "memory_limit_mb": 256
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
        return self.config_file
        
    def get_config_path(self) -> str:
        """Get test configuration file path"""
        return self.config_file

# Utility function for test setup
def setup_complete_test_environment():
    """Setup complete test environment with all fixtures and databases"""
    
    # Create test directory
    test_dir = tempfile.mkdtemp(prefix="trading_test_complete_")
    
    try:
        # Initialize managers
        fixtures = TestDataFixtures()
        db_manager = TestDatabaseManager(test_dir)
        redis_manager = TestRedisManager()
        config_manager = TestConfigManager(test_dir)
        
        # Setup Redis
        redis_client = redis_manager.setup_test_redis()
        
        # Create and populate databases
        databases = ["trading_predictions", "paper_trading", "sentiment_analysis", "ml_training"]
        
        for db_name in databases:
            db_manager.create_test_database(db_name)
            db_manager.populate_test_data(db_name, fixtures)
            
        # Populate Redis cache
        if redis_client:
            redis_manager.populate_test_cache(fixtures)
            
        # Create test configuration
        config_path = config_manager.create_test_config(db_manager, redis_manager)
        
        return {
            "test_dir": test_dir,
            "fixtures": fixtures,
            "db_manager": db_manager,
            "redis_manager": redis_manager,
            "config_manager": config_manager,
            "config_path": config_path,
            "redis_client": redis_client
        }
        
    except Exception as e:
        # Cleanup on error
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
        raise e

def cleanup_test_environment(test_env: Dict):
    """Cleanup complete test environment"""
    try:
        if "db_manager" in test_env:
            test_env["db_manager"].cleanup()
            
        if "redis_manager" in test_env:
            test_env["redis_manager"].cleanup()
            
        if "test_dir" in test_env and os.path.exists(test_env["test_dir"]):
            shutil.rmtree(test_env["test_dir"])
            
    except Exception as e:
        print(f"Warning: Error during test environment cleanup: {e}")

if __name__ == "__main__":
    """Test the test fixtures and database management"""
    
    print("🧪 Testing Test Data Fixtures and Database Management...")
    
    # Setup test environment
    test_env = setup_complete_test_environment()
    
    try:
        print("✅ Test environment setup complete!")
        print(f"   Test directory: {test_env['test_dir']}")
        print(f"   Config file: {test_env['config_path']}")
        print(f"   Redis available: {test_env['redis_client'] is not None}")
        
        # Test database operations
        db_manager = test_env["db_manager"]
        
        # Test prediction database
        pred_db = db_manager.get_database_path("trading_predictions")
        conn = sqlite3.connect(pred_db)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM predictions")
        pred_count = cursor.fetchone()[0]
        print(f"   Predictions in test DB: {pred_count}")
        
        cursor.execute("SELECT COUNT(*) FROM trades")
        trade_count = cursor.fetchone()[0]
        print(f"   Trades in test DB: {trade_count}")
        
        conn.close()
        
        # Test Redis cache
        if test_env['redis_client']:
            redis_keys = test_env['redis_client'].keys("*")
            print(f"   Redis cache keys: {len(redis_keys)}")
            
        print("✅ All test data fixtures working correctly!")
        
    finally:
        # Cleanup
        cleanup_test_environment(test_env)
        print("🧹 Test environment cleaned up")
