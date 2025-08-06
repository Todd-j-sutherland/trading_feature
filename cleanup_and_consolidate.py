#!/usr/bin/env python3
"""
Comprehensive Cleanup and Database Consolidation Script

This script will:
1. Consolidate multiple SQLite databases into a single unified schema
2. Migrate JSON data to SQL tables for better performance
3. Clean up redundant files and old model versions
4. Establish proper data retention policies

Run with: python cleanup_and_consolidate.py --dry-run (to preview)
Run with: python cleanup_and_consolidate.py --execute (to actually run)
"""

import os
import sqlite3
import json
import shutil
import glob
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TradingSystemConsolidator:
    def __init__(self, dry_run=True):
        self.dry_run = dry_run
        self.root_dir = Path(__file__).parent
        self.data_dir = self.root_dir / "data"
        self.unified_db_path = self.data_dir / "trading_unified.db"
        self.archive_dir = self.root_dir / "archive" / f"cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if not self.dry_run:
            self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    def create_unified_schema(self):
        """Create unified database schema for all trading data"""
        logger.info("🏗️ Creating unified database schema...")
        
        schema_sql = """
        -- Unified Trading Database Schema
        
        -- Bank sentiment and analysis data
        CREATE TABLE IF NOT EXISTS bank_sentiment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            sentiment_score REAL,
            confidence REAL,
            news_count INTEGER,
            stage_1_score REAL,
            stage_2_score REAL,
            economic_context TEXT,
            UNIQUE(symbol, timestamp)
        );
        
        -- ML model predictions and features
        CREATE TABLE IF NOT EXISTS ml_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            prediction_type TEXT, -- 'direction', 'magnitude', 'confidence'
            predicted_value REAL,
            actual_value REAL,
            confidence_score REAL,
            model_version TEXT,
            features TEXT, -- JSON string of features used
            status TEXT DEFAULT 'pending', -- pending, completed, cancelled
            UNIQUE(symbol, timestamp, prediction_type)
        );
        
        -- Trading signals and recommendations
        CREATE TABLE IF NOT EXISTS trading_signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            signal_type TEXT, -- BUY, SELL, HOLD
            strength REAL,
            ml_confidence REAL,
            technical_score REAL,
            sentiment_score REAL,
            economic_regime TEXT,
            reasoning TEXT,
            executed BOOLEAN DEFAULT FALSE
        );
        
        -- Position tracking and outcomes
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            entry_date DATETIME NOT NULL,
            exit_date DATETIME,
            position_type TEXT, -- LONG, SHORT
            entry_price REAL,
            exit_price REAL,
            position_size INTEGER,
            ml_confidence REAL,
            sentiment_at_entry REAL,
            exit_reason TEXT,
            profit_loss REAL,
            return_percentage REAL
        );
        
        -- Market data cache (replaces JSON cache)
        CREATE TABLE IF NOT EXISTS market_data_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT NOT NULL UNIQUE,
            data TEXT NOT NULL, -- JSON string
            expiry_date DATETIME NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- ML model metadata and performance
        CREATE TABLE IF NOT EXISTS ml_models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            version TEXT NOT NULL,
            file_path TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            accuracy REAL,
            precision_score REAL,
            recall_score REAL,
            is_current BOOLEAN DEFAULT FALSE,
            model_type TEXT, -- direction, magnitude, ensemble
            UNIQUE(model_name, version)
        );
        
        -- News articles and analysis
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            title TEXT NOT NULL,
            content TEXT,
            url TEXT UNIQUE,
            published_date DATETIME,
            source TEXT,
            sentiment_score REAL,
            confidence REAL,
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- System performance metrics
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            category TEXT -- memory, performance, accuracy, etc.
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_bank_sentiment_symbol_time ON bank_sentiment(symbol, timestamp);
        CREATE INDEX IF NOT EXISTS idx_ml_predictions_symbol_time ON ml_predictions(symbol, timestamp);
        CREATE INDEX IF NOT EXISTS idx_trading_signals_symbol_time ON trading_signals(symbol, timestamp);
        CREATE INDEX IF NOT EXISTS idx_positions_symbol_entry ON positions(symbol, entry_date);
        CREATE INDEX IF NOT EXISTS idx_cache_key ON market_data_cache(cache_key);
        CREATE INDEX IF NOT EXISTS idx_cache_expiry ON market_data_cache(expiry_date);
        CREATE INDEX IF NOT EXISTS idx_models_current ON ml_models(is_current);
        CREATE INDEX IF NOT EXISTS idx_news_symbol_date ON news_articles(symbol, published_date);
        """
        
        if not self.dry_run:
            conn = sqlite3.connect(self.unified_db_path)
            conn.executescript(schema_sql)
            conn.close()
            logger.info(f"✅ Created unified database: {self.unified_db_path}")
        else:
            logger.info("📋 Would create unified database schema")
    
    def consolidate_databases(self):
        """Consolidate existing databases into unified schema"""
        logger.info("🔄 Consolidating existing databases...")
        
        db_files = list(self.data_dir.glob("*.db")) + list(self.data_dir.glob("**/*.db"))
        
        for db_file in db_files:
            if db_file.name == "trading_unified.db":
                continue
                
            logger.info(f"📊 Processing database: {db_file}")
            
            if not self.dry_run:
                try:
                    # Connect to source database
                    source_conn = sqlite3.connect(db_file)
                    target_conn = sqlite3.connect(self.unified_db_path)
                    
                    # Get table names from source
                    cursor = source_conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    
                    for (table_name,) in tables:
                        # Try to migrate common table patterns
                        if 'sentiment' in table_name.lower():
                            self._migrate_sentiment_data(source_conn, target_conn, table_name)
                        elif 'prediction' in table_name.lower():
                            self._migrate_prediction_data(source_conn, target_conn, table_name)
                        elif 'position' in table_name.lower() or 'outcome' in table_name.lower():
                            self._migrate_position_data(source_conn, target_conn, table_name)
                        else:
                            logger.info(f"⚠️ Skipping unknown table: {table_name}")
                    
                    source_conn.close()
                    target_conn.close()
                    
                    # Archive original database
                    archive_path = self.archive_dir / "databases" / db_file.name
                    archive_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(db_file), str(archive_path))
                    logger.info(f"📦 Archived database: {db_file.name}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {db_file}: {e}")
            else:
                logger.info(f"📋 Would consolidate: {db_file}")
    
    def migrate_json_to_sql(self):
        """Migrate JSON cache files to SQL tables"""
        logger.info("📄 Migrating JSON data to SQL...")
        
        json_files = list(self.data_dir.glob("**/*.json"))
        
        if not self.dry_run:
            conn = sqlite3.connect(self.unified_db_path)
        
        for json_file in json_files:
            logger.info(f"📄 Processing JSON: {json_file}")
            
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                if not self.dry_run:
                    # Determine cache key and expiry
                    cache_key = json_file.stem
                    expiry_date = datetime.now() + timedelta(hours=24)  # 24 hour default TTL
                    
                    # Insert into cache table
                    conn.execute("""
                        INSERT OR REPLACE INTO market_data_cache 
                        (cache_key, data, expiry_date) 
                        VALUES (?, ?, ?)
                    """, (cache_key, json.dumps(data), expiry_date))
                    
                    # Archive original JSON
                    archive_path = self.archive_dir / "json" / json_file.name
                    archive_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(json_file), str(archive_path))
                    logger.info(f"📦 Migrated and archived: {json_file.name}")
                else:
                    logger.info(f"📋 Would migrate: {json_file}")
                    
            except Exception as e:
                logger.error(f"❌ Error processing {json_file}: {e}")
        
        if not self.dry_run:
            conn.commit()
            conn.close()
    
    def cleanup_ml_models(self):
        """Clean up old ML model versions, keep only recent ones"""
        logger.info("🤖 Cleaning up ML model versions...")
        
        models_dir = self.data_dir / "ml_models" / "models"
        if not models_dir.exists():
            return
        
        # Group models by type
        model_groups = {}
        for model_file in models_dir.glob("*.pkl"):
            if model_file.name.startswith("current_"):
                continue  # Skip current symlinks
                
            # Extract model type and date from filename
            parts = model_file.stem.split("_")
            if len(parts) >= 3:
                model_type = "_".join(parts[:-2])  # e.g., "direction_model_enhanced"
                date_part = "_".join(parts[-2:])   # e.g., "20250804_190354"
                
                if model_type not in model_groups:
                    model_groups[model_type] = []
                
                model_groups[model_type].append((model_file, date_part))
        
        # Keep only 3 most recent versions of each model type
        for model_type, models in model_groups.items():
            # Sort by date (newest first)
            models.sort(key=lambda x: x[1], reverse=True)
            
            if len(models) > 3:
                models_to_remove = models[3:]  # Remove all but 3 most recent
                
                for model_file, date_part in models_to_remove:
                    logger.info(f"🗑️ Removing old model: {model_file.name}")
                    
                    if not self.dry_run:
                        # Archive before removing
                        archive_path = self.archive_dir / "old_models" / model_file.name
                        archive_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(model_file), str(archive_path))
                        
                        # Also archive corresponding metadata if exists
                        metadata_file = model_file.with_suffix('.json')
                        if metadata_file.exists():
                            metadata_archive = self.archive_dir / "old_models" / metadata_file.name
                            shutil.move(str(metadata_file), str(metadata_archive))
                    else:
                        logger.info(f"📋 Would remove: {model_file.name}")
    
    def cleanup_redundant_files(self):
        """Remove redundant Python files identified in analysis"""
        logger.info("🧹 Cleaning up redundant files...")
        
        redundant_patterns = [
            "dashboard*.py",  # Root level dashboard files
            "*_broken*.py",   # Broken versions
            "*_temp.py",      # Temporary files  
            "*_demo.py",      # Demo scripts
            "test_*debug*.py", # Debug test files
            "debug_*.py",     # Debug scripts
            "analyze_*.py",   # One-off analysis scripts
            "previous_*.py",  # Previous versions
        ]
        
        # Files to definitely keep (whitelist)
        keep_files = {
            "app/dashboard/enhanced_main.py",
            "app/main.py",
            "tests/test_*.py",  # Proper test files in tests/
            "enhanced_ml_system/analyzers/enhanced_evening_analyzer_with_ml.py"  # Might be used
        }
        
        for pattern in redundant_patterns:
            files_to_remove = list(self.root_dir.glob(pattern))
            
            for file_path in files_to_remove:
                # Check if file should be kept
                relative_path = file_path.relative_to(self.root_dir)
                should_keep = any(
                    str(relative_path).startswith(keep_pattern.split('*')[0]) 
                    for keep_pattern in keep_files
                    if '*' in keep_pattern
                ) or str(relative_path) in keep_files
                
                if should_keep:
                    logger.info(f"⚡ Keeping important file: {relative_path}")
                    continue
                
                logger.info(f"🗑️ Removing redundant file: {relative_path}")
                
                if not self.dry_run:
                    # Archive before removing
                    archive_path = self.archive_dir / "redundant_files" / relative_path
                    archive_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(file_path), str(archive_path))
                else:
                    logger.info(f"📋 Would remove: {relative_path}")
    
    def _migrate_sentiment_data(self, source_conn, target_conn, table_name):
        """Helper to migrate sentiment data"""
        try:
            cursor = source_conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Map to unified schema (basic mapping)
            for row in rows:
                row_dict = dict(zip(columns, row))
                
                target_conn.execute("""
                    INSERT OR IGNORE INTO bank_sentiment 
                    (symbol, timestamp, sentiment_score, confidence, news_count)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    row_dict.get('symbol', 'UNKNOWN'),
                    row_dict.get('timestamp', datetime.now()),
                    row_dict.get('sentiment_score', 0.0),
                    row_dict.get('confidence', 0.0),
                    row_dict.get('news_count', 0)
                ))
            
            target_conn.commit()
            logger.info(f"✅ Migrated {len(rows)} sentiment records")
            
        except Exception as e:
            logger.error(f"❌ Error migrating sentiment data: {e}")
    
    def _migrate_prediction_data(self, source_conn, target_conn, table_name):
        """Helper to migrate prediction data"""
        try:
            cursor = source_conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            for row in rows:
                row_dict = dict(zip(columns, row))
                
                target_conn.execute("""
                    INSERT OR IGNORE INTO ml_predictions 
                    (symbol, timestamp, prediction_type, predicted_value, confidence_score, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    row_dict.get('symbol', 'UNKNOWN'),
                    row_dict.get('timestamp', datetime.now()),
                    row_dict.get('prediction_type', 'unknown'),
                    row_dict.get('predicted_value', 0.0),
                    row_dict.get('confidence', 0.0),
                    row_dict.get('status', 'completed')
                ))
            
            target_conn.commit()
            logger.info(f"✅ Migrated {len(rows)} prediction records")
            
        except Exception as e:
            logger.error(f"❌ Error migrating prediction data: {e}")
    
    def _migrate_position_data(self, source_conn, target_conn, table_name):
        """Helper to migrate position/outcome data"""
        try:
            cursor = source_conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            for row in rows:
                row_dict = dict(zip(columns, row))
                
                target_conn.execute("""
                    INSERT OR IGNORE INTO positions 
                    (symbol, entry_date, exit_date, entry_price, exit_price, 
                     position_size, ml_confidence, exit_reason, profit_loss)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row_dict.get('symbol', 'UNKNOWN'),
                    row_dict.get('entry_date', datetime.now()),
                    row_dict.get('exit_date'),
                    row_dict.get('entry_price', 0.0),
                    row_dict.get('exit_price'),
                    row_dict.get('position_size', 0),
                    row_dict.get('confidence_at_entry', 0.0),
                    row_dict.get('exit_reason', 'unknown'),
                    row_dict.get('profit_loss', 0.0)
                ))
            
            target_conn.commit()
            logger.info(f"✅ Migrated {len(rows)} position records")
            
        except Exception as e:
            logger.error(f"❌ Error migrating position data: {e}")
    
    def run_full_cleanup(self):
        """Run complete cleanup and consolidation process"""
        logger.info("🚀 Starting comprehensive cleanup and consolidation...")
        
        if self.dry_run:
            logger.info("🔍 DRY RUN MODE - No changes will be made")
        else:
            logger.info("⚠️ LIVE MODE - Changes will be made")
        
        try:
            # Step 1: Create unified schema
            self.create_unified_schema()
            
            # Step 2: Consolidate databases
            self.consolidate_databases()
            
            # Step 3: Migrate JSON to SQL
            self.migrate_json_to_sql()
            
            # Step 4: Clean up old ML models
            self.cleanup_ml_models()
            
            # Step 5: Remove redundant files
            self.cleanup_redundant_files()
            
            logger.info("✅ Cleanup and consolidation completed successfully!")
            
            if not self.dry_run:
                logger.info(f"📦 All archived files saved to: {self.archive_dir}")
                logger.info(f"🗄️ Unified database created at: {self.unified_db_path}")
                
                # Calculate space saved
                total_size = sum(
                    f.stat().st_size for f in self.archive_dir.rglob('*') if f.is_file()
                )
                logger.info(f"💾 Estimated space saved: {total_size / 1024 / 1024:.1f} MB")
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description="Cleanup and consolidate trading system")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Preview changes without executing (default)")
    parser.add_argument("--execute", action="store_true", 
                       help="Actually execute the cleanup")
    
    args = parser.parse_args()
    
    # If --execute is specified, turn off dry_run
    dry_run = not args.execute
    
    consolidator = TradingSystemConsolidator(dry_run=dry_run)
    consolidator.run_full_cleanup()

if __name__ == "__main__":
    main()