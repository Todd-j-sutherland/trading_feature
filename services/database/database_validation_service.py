#!/usr/bin/env python3
"""
Database Schema Validation Service

This service validates and ensures compatibility across all trading system databases:
- paper_trading.db
- predictions.db  
- trading_predictions.db
- data/enhanced_outcomes.db
- data/ig_markets_paper_trades.db
- data/sentiment_analysis.db

Key Functions:
- Schema validation and compatibility checking
- Data migration between database versions
- Database health monitoring
- Backup and recovery validation
- Cross-database relationship integrity
- Performance optimization recommendations
"""
import asyncio
import sys
import os
import sqlite3
import json
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import hashlib

# Add project paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.base_service import BaseService

# Import settings with fallback
try:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config"))
    from settings import Settings
except ImportError:
    class Settings:
        DATABASE_CONFIG = {}

@dataclass
class DatabaseInfo:
    """Database information structure"""
    name: str
    path: str
    exists: bool
    size_mb: float
    table_count: int
    row_count: int
    last_modified: str
    schema_version: str
    health_status: str
    issues: List[str]

@dataclass
class SchemaValidation:
    """Schema validation result"""
    database: str
    table: str
    is_valid: bool
    expected_columns: List[str]
    actual_columns: List[str]
    missing_columns: List[str]
    extra_columns: List[str]
    issues: List[str]

@dataclass
class CrossDatabaseCheck:
    """Cross-database relationship check"""
    relationship_name: str
    source_db: str
    source_table: str
    target_db: str
    target_table: str
    orphaned_records: int
    integrity_issues: List[str]
    is_valid: bool

class DatabaseValidationService(BaseService):
    """Comprehensive database schema validation and compatibility service"""

    def __init__(self):
        super().__init__("database-validation")
        
        # Load database configuration
        self._load_database_settings()
        
        # Schema definitions for validation
        self._initialize_schema_definitions()
        
        # Database health tracking
        self.last_validation_time = None
        self.validation_history: List[Dict] = []
        self.database_health: Dict[str, DatabaseInfo] = {}
        
        # Register service methods
        self._register_methods()
    
    def _load_database_settings(self):
        """Load database configuration from settings"""
        try:
            # Core database paths
            self.database_paths = {
                'paper_trading': getattr(Settings, 'PAPER_TRADING_DB', 'paper_trading.db'),
                'predictions': getattr(Settings, 'PREDICTIONS_DB', 'predictions.db'),
                'trading_predictions': getattr(Settings, 'TRADING_PREDICTIONS_DB', 'trading_predictions.db'),
                'enhanced_outcomes': getattr(Settings, 'ENHANCED_OUTCOMES_DB', 'data/enhanced_outcomes.db'),
                'ig_markets': getattr(Settings, 'IG_MARKETS_DB', 'data/ig_markets_paper_trades.db'),
                'sentiment_analysis': getattr(Settings, 'SENTIMENT_DB', 'data/sentiment_analysis.db'),
                'trading_data': getattr(Settings, 'TRADING_DATA_DB', 'trading_data.db')
            }
            
            # Database configuration
            self.db_config = getattr(Settings, 'DATABASE_CONFIG', {
                'validation_interval': 3600,  # 1 hour
                'backup_retention_days': 30,
                'max_database_size_mb': 1000,
                'enable_wal_mode': True,
                'enable_foreign_keys': True,
                'vacuum_threshold_mb': 100
            })
            
            # Validation settings
            self.validation_config = {
                'strict_mode': getattr(Settings, 'DATABASE_STRICT_VALIDATION', False),
                'auto_fix_issues': getattr(Settings, 'DATABASE_AUTO_FIX', False),
                'create_missing_tables': getattr(Settings, 'DATABASE_CREATE_MISSING', True),
                'backup_before_migration': getattr(Settings, 'DATABASE_BACKUP_BEFORE_MIGRATION', True)
            }
            
            self.settings_loaded = True
            self.logger.info(f'"action": "database_settings_loaded", "database_count": {len(self.database_paths)}')
            
        except Exception as e:
            self.logger.error(f'"error": "database_settings_load_failed", "details": "{e}", "action": "using_defaults"')
            self.settings_loaded = False
            
            # Safe defaults
            self.database_paths = {
                'paper_trading': 'paper_trading.db',
                'predictions': 'predictions.db',
                'trading_predictions': 'trading_predictions.db',
                'enhanced_outcomes': 'data/enhanced_outcomes.db',
                'ig_markets': 'data/ig_markets_paper_trades.db',
                'sentiment_analysis': 'data/sentiment_analysis.db'
            }
            self.db_config = {
                'validation_interval': 3600,
                'backup_retention_days': 30,
                'max_database_size_mb': 1000
            }
            self.validation_config = {
                'strict_mode': False,
                'auto_fix_issues': False,
                'create_missing_tables': True
            }
    
    def _initialize_schema_definitions(self):
        """Initialize expected schema definitions for all databases"""
        self.expected_schemas = {
            'paper_trading': {
                'positions': [
                    'position_id', 'symbol', 'side', 'quantity', 'entry_price', 
                    'current_price', 'entry_time', 'position_value', 'pnl', 
                    'pnl_percentage', 'status', 'stop_loss', 'take_profit', 
                    'ig_order_id', 'prediction_confidence', 'prediction_id',
                    'created_at', 'updated_at'
                ],
                'trades': [
                    'trade_id', 'position_id', 'symbol', 'action', 'quantity', 
                    'price', 'timestamp', 'fees', 'trade_value', 'order_type', 
                    'ig_order_id', 'execution_status', 'created_at'
                ],
                'portfolio_history': [
                    'id', 'total_value', 'cash_balance', 'positions_value', 
                    'total_pnl', 'total_pnl_percentage', 'open_positions', 
                    'total_trades', 'win_rate', 'timestamp', 'created_at'
                ],
                'risk_metrics': [
                    'id', 'portfolio_risk', 'var_1day', 'var_5day', 
                    'max_drawdown', 'sharpe_ratio', 'volatility', 
                    'timestamp', 'created_at'
                ]
            },
            'predictions': {
                'predictions': [
                    'id', 'symbol', 'timestamp', 'action', 'confidence', 
                    'technical_score', 'news_score', 'volume_score', 
                    'risk_score', 'market_context', 'prediction_date',
                    'created_at'
                ],
                'prediction_outcomes': [
                    'id', 'prediction_id', 'symbol', 'predicted_action', 
                    'actual_outcome', 'accuracy_score', 'outcome_date',
                    'price_change', 'time_horizon_hours', 'created_at'
                ]
            },
            'trading_predictions': {
                'predictions': [
                    'id', 'symbol', 'prediction_date', 'action', 'confidence',
                    'technical_analysis', 'news_sentiment', 'volume_analysis',
                    'market_conditions', 'risk_assessment', 'created_at'
                ],
                'prediction_history': [
                    'id', 'symbol', 'date', 'prediction', 'actual_outcome',
                    'accuracy', 'created_at'
                ]
            },
            'enhanced_outcomes': {
                'trading_outcomes': [
                    'id', 'position_id', 'symbol', 'entry_date', 'exit_date',
                    'entry_price', 'exit_price', 'quantity', 'pnl', 
                    'pnl_percentage', 'prediction_confidence', 'prediction_accuracy',
                    'market_conditions', 'trade_duration_hours', 'outcome_category',
                    'created_at'
                ],
                'prediction_tracking': [
                    'id', 'prediction_id', 'symbol', 'prediction_date',
                    'confidence_score', 'predicted_action', 'actual_outcome',
                    'position_id', 'accuracy_score', 'market_context', 'created_at'
                ],
                'market_analysis': [
                    'id', 'analysis_date', 'market_phase', 'volatility_index',
                    'trend_direction', 'sector_rotation', 'risk_level',
                    'trading_volume', 'sentiment_score', 'created_at'
                ]
            },
            'ig_markets': {
                'ig_orders': [
                    'id', 'ig_order_id', 'internal_position_id', 'symbol',
                    'side', 'quantity', 'order_type', 'price', 'stop_loss',
                    'take_profit', 'status', 'created_at', 'updated_at', 'ig_response'
                ],
                'ig_positions_sync': [
                    'id', 'sync_timestamp', 'positions_synced', 'errors_count',
                    'sync_status', 'error_details', 'created_at'
                ],
                'ig_market_data': [
                    'id', 'symbol', 'bid_price', 'ask_price', 'last_price',
                    'volume', 'timestamp', 'market_status', 'created_at'
                ]
            },
            'sentiment_analysis': {
                'news_articles': [
                    'id', 'title', 'content', 'source', 'published_date',
                    'url', 'sentiment_score', 'relevance_score', 'symbols',
                    'category', 'created_at'
                ],
                'sentiment_scores': [
                    'id', 'symbol', 'date', 'sentiment_score', 'news_count',
                    'confidence_score', 'source_quality', 'market_impact',
                    'created_at'
                ],
                'news_sources': [
                    'id', 'source_name', 'base_url', 'rss_feed', 'quality_tier',
                    'is_active', 'last_crawled', 'articles_count', 'created_at'
                ]
            },
            'trading_data': {
                'market_data': [
                    'id', 'symbol', 'timestamp', 'open_price', 'high_price',
                    'low_price', 'close_price', 'volume', 'adjusted_close',
                    'created_at'
                ],
                'technical_indicators': [
                    'id', 'symbol', 'date', 'rsi', 'macd', 'signal_line',
                    'bollinger_upper', 'bollinger_lower', 'sma_20', 'sma_50',
                    'volume_sma', 'created_at'
                ]
            }
        }
        
        # Cross-database relationships to validate
        self.cross_db_relationships = [
            {
                'name': 'position_prediction_link',
                'source_db': 'paper_trading',
                'source_table': 'positions',
                'source_column': 'prediction_id',
                'target_db': 'predictions',
                'target_table': 'predictions',
                'target_column': 'id'
            },
            {
                'name': 'trade_position_link',
                'source_db': 'paper_trading',
                'source_table': 'trades',
                'source_column': 'position_id',
                'target_db': 'paper_trading',
                'target_table': 'positions',
                'target_column': 'position_id'
            },
            {
                'name': 'outcome_position_link',
                'source_db': 'enhanced_outcomes',
                'source_table': 'trading_outcomes',
                'source_column': 'position_id',
                'target_db': 'paper_trading',
                'target_table': 'positions',
                'target_column': 'position_id'
            },
            {
                'name': 'prediction_tracking_link',
                'source_db': 'enhanced_outcomes',
                'source_table': 'prediction_tracking',
                'source_column': 'prediction_id',
                'target_db': 'predictions',
                'target_table': 'predictions',
                'target_column': 'id'
            },
            {
                'name': 'ig_order_position_link',
                'source_db': 'ig_markets',
                'source_table': 'ig_orders',
                'source_column': 'internal_position_id',
                'target_db': 'paper_trading',
                'target_table': 'positions',
                'target_column': 'position_id'
            }
        ]
    
    def _register_methods(self):
        """Register all service methods"""
        # Validation operations
        self.register_handler("validate_all_databases", self.validate_all_databases)
        self.register_handler("validate_database", self.validate_database)
        self.register_handler("validate_schema", self.validate_schema)
        self.register_handler("check_cross_database_integrity", self.check_cross_database_integrity)
        
        # Database operations
        self.register_handler("get_database_info", self.get_database_info)
        self.register_handler("get_all_database_info", self.get_all_database_info)
        self.register_handler("fix_database_issues", self.fix_database_issues)
        self.register_handler("optimize_databases", self.optimize_databases)
        
        # Migration and backup
        self.register_handler("create_database_backup", self.create_database_backup)
        self.register_handler("restore_database_backup", self.restore_database_backup)
        self.register_handler("migrate_database_schema", self.migrate_database_schema)
        
        # Monitoring and reporting
        self.register_handler("get_validation_history", self.get_validation_history)
        self.register_handler("get_database_health_report", self.get_database_health_report)
        self.register_handler("schedule_validation", self.schedule_validation)
    
    async def validate_all_databases(self, fix_issues: bool = False):
        """Validate all databases comprehensively"""
        try:
            validation_start = datetime.now()
            validation_results = {
                'validation_id': f"validation_{int(validation_start.timestamp())}",
                'timestamp': validation_start.isoformat(),
                'databases': {},
                'cross_database_checks': [],
                'summary': {},
                'issues_found': 0,
                'issues_fixed': 0,
                'validation_passed': True
            }
            
            self.logger.info(f'"action": "database_validation_started", "fix_issues": {fix_issues}')
            
            # Validate each database
            for db_name, db_path in self.database_paths.items():
                try:
                    db_validation = await self.validate_database(db_name, fix_issues)
                    validation_results['databases'][db_name] = db_validation
                    
                    if not db_validation.get('is_valid', False):
                        validation_results['validation_passed'] = False
                        validation_results['issues_found'] += len(db_validation.get('issues', []))
                        
                except Exception as e:
                    self.logger.error(f'"database": "{db_name}", "error": "{e}", "action": "database_validation_failed"')
                    validation_results['databases'][db_name] = {
                        'is_valid': False,
                        'error': str(e),
                        'issues': [f"Validation failed: {str(e)}"]
                    }
                    validation_results['validation_passed'] = False
                    validation_results['issues_found'] += 1
            
            # Perform cross-database integrity checks
            try:
                cross_db_results = await self.check_cross_database_integrity()
                validation_results['cross_database_checks'] = cross_db_results
                
                for check in cross_db_results:
                    if not check.get('is_valid', False):
                        validation_results['validation_passed'] = False
                        validation_results['issues_found'] += len(check.get('integrity_issues', []))
                        
            except Exception as e:
                self.logger.error(f'"error": "cross_database_check_failed", "details": "{e}"')
                validation_results['cross_database_checks'] = [{
                    'error': str(e),
                    'is_valid': False
                }]
                validation_results['validation_passed'] = False
            
            # Calculate summary
            validation_end = datetime.now()
            validation_duration = (validation_end - validation_start).total_seconds()
            
            validation_results['summary'] = {
                'total_databases': len(self.database_paths),
                'valid_databases': sum(1 for db in validation_results['databases'].values() if db.get('is_valid', False)),
                'invalid_databases': sum(1 for db in validation_results['databases'].values() if not db.get('is_valid', False)),
                'total_issues': validation_results['issues_found'],
                'validation_duration_seconds': validation_duration,
                'validation_passed': validation_results['validation_passed']
            }
            
            # Store validation results
            self.last_validation_time = validation_start
            self.validation_history.append(validation_results)
            
            # Keep only last 100 validations
            if len(self.validation_history) > 100:
                self.validation_history = self.validation_history[-100:]
            
            # Publish validation event
            self.publish_event("database_validation_completed", {
                'validation_id': validation_results['validation_id'],
                'validation_passed': validation_results['validation_passed'],
                'issues_found': validation_results['issues_found'],
                'total_databases': validation_results['summary']['total_databases']
            }, priority="high" if not validation_results['validation_passed'] else "normal")
            
            self.logger.info(f'"validation_id": "{validation_results["validation_id"]}", "validation_passed": {validation_results["validation_passed"]}, "issues_found": {validation_results["issues_found"]}, "duration": {validation_duration:.2f}, "action": "database_validation_completed"')
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "database_validation_critical_failure"')
            return {
                'validation_id': f"failed_{int(datetime.now().timestamp())}",
                'error': str(e),
                'validation_passed': False,
                'issues_found': 1
            }
    
    async def validate_database(self, database_name: str, fix_issues: bool = False):
        """Validate a single database"""
        try:
            if database_name not in self.database_paths:
                return {'error': f'Unknown database: {database_name}', 'is_valid': False}
            
            db_path = self.database_paths[database_name]
            validation_result = {
                'database': database_name,
                'path': db_path,
                'is_valid': True,
                'issues': [],
                'schema_validations': [],
                'database_info': None,
                'fixes_applied': []
            }
            
            # Get database info
            db_info = await self.get_database_info(database_name)
            validation_result['database_info'] = db_info
            
            if not db_info.get('exists', False):
                validation_result['is_valid'] = False
                validation_result['issues'].append(f'Database file does not exist: {db_path}')
                
                if fix_issues and self.validation_config.get('create_missing_tables', True):
                    # Create missing database
                    await self._create_missing_database(database_name)
                    validation_result['fixes_applied'].append('Created missing database')
                    # Re-get database info
                    db_info = await self.get_database_info(database_name)
                    validation_result['database_info'] = db_info
                
                return validation_result
            
            # Validate schema for this database
            if database_name in self.expected_schemas:
                for table_name, expected_columns in self.expected_schemas[database_name].items():
                    schema_validation = await self.validate_schema(database_name, table_name, expected_columns)
                    validation_result['schema_validations'].append(schema_validation)
                    
                    if not schema_validation.get('is_valid', False):
                        validation_result['is_valid'] = False
                        validation_result['issues'].extend(schema_validation.get('issues', []))
                        
                        if fix_issues:
                            # Attempt to fix schema issues
                            fixes = await self._fix_schema_issues(database_name, table_name, schema_validation)
                            validation_result['fixes_applied'].extend(fixes)
            
            # Check database health
            health_issues = await self._check_database_health(database_name)
            if health_issues:
                validation_result['issues'].extend(health_issues)
                if len(health_issues) > 3:  # More than 3 health issues is concerning
                    validation_result['is_valid'] = False
            
            # Check database size limits
            if db_info.get('size_mb', 0) > self.db_config.get('max_database_size_mb', 1000):
                validation_result['issues'].append(f'Database size ({db_info["size_mb"]:.1f}MB) exceeds limit')
                validation_result['is_valid'] = False
            
            self.logger.info(f'"database": "{database_name}", "is_valid": {validation_result["is_valid"]}, "issues": {len(validation_result["issues"])}, "action": "database_validated"')
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f'"database": "{database_name}", "error": "{e}", "action": "database_validation_failed"')
            return {
                'database': database_name,
                'error': str(e),
                'is_valid': False,
                'issues': [f'Validation failed: {str(e)}']
            }
    
    async def validate_schema(self, database_name: str, table_name: str, expected_columns: List[str] = None):
        """Validate schema for a specific table"""
        try:
            if database_name not in self.database_paths:
                return {'error': f'Unknown database: {database_name}', 'is_valid': False}
            
            db_path = self.database_paths[database_name]
            
            if not os.path.exists(db_path):
                return {
                    'database': database_name,
                    'table': table_name,
                    'error': f'Database file does not exist: {db_path}',
                    'is_valid': False
                }
            
            # Use expected columns from schema definitions if not provided
            if expected_columns is None:
                expected_columns = self.expected_schemas.get(database_name, {}).get(table_name, [])
            
            if not expected_columns:
                return {
                    'database': database_name,
                    'table': table_name,
                    'error': 'No expected columns defined for validation',
                    'is_valid': False
                }
            
            # Get actual table schema
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Check if table exists
                cursor.execute('''
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?
                ''', (table_name,))
                
                if not cursor.fetchone():
                    return {
                        'database': database_name,
                        'table': table_name,
                        'is_valid': False,
                        'expected_columns': expected_columns,
                        'actual_columns': [],
                        'missing_columns': expected_columns,
                        'extra_columns': [],
                        'issues': [f'Table {table_name} does not exist']
                    }
                
                # Get table columns
                cursor.execute(f'PRAGMA table_info({table_name})')
                column_info = cursor.fetchall()
                actual_columns = [col[1] for col in column_info]  # col[1] is column name
            
            # Compare schemas
            missing_columns = [col for col in expected_columns if col not in actual_columns]
            extra_columns = [col for col in actual_columns if col not in expected_columns]
            
            is_valid = len(missing_columns) == 0
            issues = []
            
            if missing_columns:
                issues.append(f'Missing columns: {", ".join(missing_columns)}')
            
            if extra_columns and self.validation_config.get('strict_mode', False):
                issues.append(f'Extra columns: {", ".join(extra_columns)}')
                is_valid = False
            
            validation_result = {
                'database': database_name,
                'table': table_name,
                'is_valid': is_valid,
                'expected_columns': expected_columns,
                'actual_columns': actual_columns,
                'missing_columns': missing_columns,
                'extra_columns': extra_columns,
                'issues': issues
            }
            
            self.logger.debug(f'"database": "{database_name}", "table": "{table_name}", "is_valid": {is_valid}, "missing_columns": {len(missing_columns)}, "action": "schema_validated"')
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f'"database": "{database_name}", "table": "{table_name}", "error": "{e}", "action": "schema_validation_failed"')
            return {
                'database': database_name,
                'table': table_name,
                'error': str(e),
                'is_valid': False,
                'issues': [f'Schema validation failed: {str(e)}']
            }
    
    async def check_cross_database_integrity(self):
        """Check integrity across related databases"""
        try:
            integrity_results = []
            
            for relationship in self.cross_db_relationships:
                try:
                    check_result = await self._check_relationship_integrity(relationship)
                    integrity_results.append(check_result)
                    
                except Exception as e:
                    self.logger.error(f'"relationship": "{relationship["name"]}", "error": "{e}", "action": "relationship_check_failed"')
                    integrity_results.append({
                        'relationship_name': relationship['name'],
                        'error': str(e),
                        'is_valid': False,
                        'integrity_issues': [f'Check failed: {str(e)}']
                    })
            
            return integrity_results
            
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "cross_database_integrity_check_failed"')
            return [{'error': str(e), 'is_valid': False}]
    
    async def _check_relationship_integrity(self, relationship: Dict[str, str]):
        """Check integrity of a specific cross-database relationship"""
        try:
            source_db = relationship['source_db']
            source_table = relationship['source_table']
            source_column = relationship['source_column']
            target_db = relationship['target_db']
            target_table = relationship['target_table']
            target_column = relationship['target_column']
            
            source_path = self.database_paths.get(source_db)
            target_path = self.database_paths.get(target_db)
            
            if not source_path or not target_path:
                return {
                    'relationship_name': relationship['name'],
                    'source_db': source_db,
                    'target_db': target_db,
                    'is_valid': False,
                    'integrity_issues': ['Database path not found'],
                    'orphaned_records': 0
                }
            
            if not os.path.exists(source_path) or not os.path.exists(target_path):
                return {
                    'relationship_name': relationship['name'],
                    'source_db': source_db,
                    'target_db': target_db,
                    'is_valid': False,
                    'integrity_issues': ['Database file does not exist'],
                    'orphaned_records': 0
                }
            
            # Check for orphaned records
            orphaned_records = 0
            integrity_issues = []
            
            try:
                if source_path == target_path:
                    # Same database - use single connection
                    with sqlite3.connect(source_path) as conn:
                        cursor = conn.cursor()
                        
                        # Find orphaned records
                        cursor.execute(f'''
                            SELECT COUNT(*) FROM {source_table} s
                            LEFT JOIN {target_table} t ON s.{source_column} = t.{target_column}
                            WHERE s.{source_column} IS NOT NULL 
                            AND t.{target_column} IS NULL
                        ''')
                        
                        orphaned_records = cursor.fetchone()[0]
                else:
                    # Different databases - need separate connections
                    with sqlite3.connect(source_path) as source_conn, sqlite3.connect(target_path) as target_conn:
                        source_cursor = source_conn.cursor()
                        target_cursor = target_conn.cursor()
                        
                        # Get all non-null source values
                        source_cursor.execute(f'''
                            SELECT DISTINCT {source_column} FROM {source_table}
                            WHERE {source_column} IS NOT NULL
                        ''')
                        source_values = [row[0] for row in source_cursor.fetchall()]
                        
                        if source_values:
                            # Check which values exist in target
                            placeholders = ','.join(['?' for _ in source_values])
                            target_cursor.execute(f'''
                                SELECT DISTINCT {target_column} FROM {target_table}
                                WHERE {target_column} IN ({placeholders})
                            ''', source_values)
                            target_values = set(row[0] for row in target_cursor.fetchall())
                            
                            # Count orphaned records
                            orphaned_values = [v for v in source_values if v not in target_values]
                            orphaned_records = len(orphaned_values)
                            
                            if orphaned_records > 0:
                                integrity_issues.append(f'{orphaned_records} orphaned records in {source_table}.{source_column}')
                
            except sqlite3.Error as e:
                integrity_issues.append(f'SQL error during integrity check: {str(e)}')
            
            is_valid = orphaned_records == 0 and len(integrity_issues) == 0
            
            result = {
                'relationship_name': relationship['name'],
                'source_db': source_db,
                'source_table': source_table,
                'target_db': target_db,
                'target_table': target_table,
                'orphaned_records': orphaned_records,
                'integrity_issues': integrity_issues,
                'is_valid': is_valid
            }
            
            if not is_valid:
                self.logger.warning(f'"relationship": "{relationship["name"]}", "orphaned_records": {orphaned_records}, "issues": {len(integrity_issues)}, "action": "integrity_issue_found"')
            
            return result
            
        except Exception as e:
            self.logger.error(f'"relationship": "{relationship["name"]}", "error": "{e}", "action": "relationship_integrity_check_failed"')
            return {
                'relationship_name': relationship['name'],
                'error': str(e),
                'is_valid': False,
                'integrity_issues': [f'Integrity check failed: {str(e)}'],
                'orphaned_records': 0
            }
    
    async def get_database_info(self, database_name: str):
        """Get comprehensive information about a database"""
        try:
            if database_name not in self.database_paths:
                return {'error': f'Unknown database: {database_name}', 'exists': False}
            
            db_path = self.database_paths[database_name]
            
            if not os.path.exists(db_path):
                return {
                    'name': database_name,
                    'path': db_path,
                    'exists': False,
                    'size_mb': 0,
                    'table_count': 0,
                    'row_count': 0,
                    'last_modified': None,
                    'schema_version': 'unknown',
                    'health_status': 'missing',
                    'issues': ['Database file does not exist']
                }
            
            # Get file info
            file_stat = os.stat(db_path)
            size_mb = file_stat.st_size / (1024 * 1024)
            last_modified = datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            
            # Get database info
            table_count = 0
            row_count = 0
            schema_version = 'unknown'
            issues = []
            
            try:
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Get table count
                    cursor.execute('''
                        SELECT COUNT(*) FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ''')
                    table_count = cursor.fetchone()[0]
                    
                    # Get total row count across all tables
                    cursor.execute('''
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ''')
                    tables = cursor.fetchall()
                    
                    for table in tables:
                        try:
                            cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
                            row_count += cursor.fetchone()[0]
                        except sqlite3.Error:
                            issues.append(f'Could not count rows in table {table[0]}')
                    
                    # Try to get schema version if stored
                    try:
                        cursor.execute('PRAGMA user_version')
                        schema_version = str(cursor.fetchone()[0])
                    except sqlite3.Error:
                        pass
                    
                    # Basic health checks
                    try:
                        cursor.execute('PRAGMA integrity_check(10)')
                        integrity_result = cursor.fetchall()
                        if integrity_result[0][0] != 'ok':
                            issues.extend([f'Integrity issue: {row[0]}' for row in integrity_result])
                    except sqlite3.Error as e:
                        issues.append(f'Integrity check failed: {str(e)}')
                        
            except sqlite3.Error as e:
                issues.append(f'Database access error: {str(e)}')
            
            # Determine health status
            if not issues:
                health_status = 'healthy'
            elif len(issues) <= 2:
                health_status = 'degraded'
            else:
                health_status = 'unhealthy'
            
            db_info = {
                'name': database_name,
                'path': db_path,
                'exists': True,
                'size_mb': round(size_mb, 2),
                'table_count': table_count,
                'row_count': row_count,
                'last_modified': last_modified,
                'schema_version': schema_version,
                'health_status': health_status,
                'issues': issues
            }
            
            # Cache database info
            self.database_health[database_name] = DatabaseInfo(**db_info)
            
            return db_info
            
        except Exception as e:
            self.logger.error(f'"database": "{database_name}", "error": "{e}", "action": "get_database_info_failed"')
            return {
                'name': database_name,
                'error': str(e),
                'exists': False,
                'health_status': 'error',
                'issues': [f'Info retrieval failed: {str(e)}']
            }
    
    async def get_all_database_info(self):
        """Get information about all databases"""
        try:
            all_db_info = {}
            
            for db_name in self.database_paths.keys():
                db_info = await self.get_database_info(db_name)
                all_db_info[db_name] = db_info
            
            # Calculate summary statistics
            total_size_mb = sum(db.get('size_mb', 0) for db in all_db_info.values())
            total_tables = sum(db.get('table_count', 0) for db in all_db_info.values())
            total_rows = sum(db.get('row_count', 0) for db in all_db_info.values())
            
            healthy_dbs = sum(1 for db in all_db_info.values() if db.get('health_status') == 'healthy')
            existing_dbs = sum(1 for db in all_db_info.values() if db.get('exists', False))
            
            summary = {
                'total_databases': len(self.database_paths),
                'existing_databases': existing_dbs,
                'healthy_databases': healthy_dbs,
                'total_size_mb': round(total_size_mb, 2),
                'total_tables': total_tables,
                'total_rows': total_rows,
                'last_check': datetime.now().isoformat()
            }
            
            return {
                'databases': all_db_info,
                'summary': summary
            }
            
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "get_all_database_info_failed"')
            return {'error': str(e)}
    
    async def health_check(self):
        """Enhanced health check with database validation metrics"""
        base_health = await super().health_check()
        
        # Add database-specific health metrics
        db_health = {
            **base_health,
            "settings_loaded": self.settings_loaded,
            "databases_configured": len(self.database_paths),
            "last_validation": self.last_validation_time.isoformat() if self.last_validation_time else None,
            "validation_history_size": len(self.validation_history),
            "database_health_summary": {}
        }
        
        # Quick database health summary
        healthy_count = 0
        unhealthy_count = 0
        missing_count = 0
        
        for db_name in self.database_paths.keys():
            if db_name in self.database_health:
                db_status = self.database_health[db_name].health_status
                if db_status == 'healthy':
                    healthy_count += 1
                elif db_status in ['degraded', 'unhealthy']:
                    unhealthy_count += 1
                else:
                    missing_count += 1
            else:
                missing_count += 1
        
        db_health["database_health_summary"] = {
            "healthy": healthy_count,
            "unhealthy": unhealthy_count,
            "missing": missing_count,
            "total": len(self.database_paths)
        }
        
        # Set overall health status
        if missing_count > 0 or unhealthy_count > 1:
            db_health["status"] = "degraded"
            db_health["warning"] = f"Database issues: {missing_count} missing, {unhealthy_count} unhealthy"
        
        return db_health

    # Placeholder methods for additional functionality
    async def fix_database_issues(self, database_name: str = None):
        return {"status": "not_implemented"}
    
    async def optimize_databases(self):
        return {"status": "not_implemented"}
    
    async def create_database_backup(self, database_name: str):
        return {"status": "not_implemented"}
    
    async def restore_database_backup(self, database_name: str, backup_path: str):
        return {"status": "not_implemented"}
    
    async def migrate_database_schema(self, database_name: str, target_version: str):
        return {"status": "not_implemented"}
    
    async def get_validation_history(self, limit: int = 10):
        return {"status": "not_implemented"}
    
    async def get_database_health_report(self):
        return {"status": "not_implemented"}
    
    async def schedule_validation(self, interval_hours: int = 24):
        return {"status": "not_implemented"}

async def main():
    """Main entry point for the database validation service"""
    service = DatabaseValidationService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
