#!/usr/bin/env python3
"""
Database Testing Module for Trading Analysis System
Tests database operations, schema integrity, and data consistency
"""

import unittest
import sqlite3
import tempfile
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

class DatabaseTester:
    """Comprehensive database testing utility"""
    
    def __init__(self, db_path: str):
        """Initialize database tester"""
        self.db_path = db_path
        self.required_tables = {
            'sentiment_history': {
                'columns': ['id', 'symbol', 'timestamp', 'overall_sentiment', 'confidence', 'news_count'],
                'types': ['INTEGER', 'TEXT', 'DATETIME', 'REAL', 'REAL', 'INTEGER']
            },
            'ml_training_data': {
                'columns': ['id', 'symbol', 'timestamp', 'features', 'target'],
                'types': ['INTEGER', 'TEXT', 'DATETIME', 'TEXT', 'REAL']
            },
            'trading_signals': {
                'columns': ['id', 'symbol', 'timestamp', 'signal', 'confidence', 'price'],
                'types': ['INTEGER', 'TEXT', 'DATETIME', 'TEXT', 'REAL', 'REAL']
            }
        }
    
    def validate_database_structure(self) -> Dict[str, Any]:
        """Validate database schema and structure"""
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'tables_found': [],
            'missing_tables': [],
            'schema_issues': []
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            results['tables_found'] = existing_tables
            
            # Check for required tables
            for table_name, table_info in self.required_tables.items():
                if table_name not in existing_tables:
                    results['missing_tables'].append(table_name)
                    results['errors'].append(f"Required table '{table_name}' not found")
                    results['valid'] = False
                else:
                    # Validate table schema
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns_info = cursor.fetchall()
                    
                    existing_columns = [col[1] for col in columns_info]  # Column names
                    existing_types = [col[2] for col in columns_info]    # Column types
                    
                    # Check required columns
                    for required_col in table_info['columns']:
                        if required_col not in existing_columns:
                            error_msg = f"Table '{table_name}' missing required column '{required_col}'"
                            results['schema_issues'].append(error_msg)
                            results['errors'].append(error_msg)
                            results['valid'] = False
            
            conn.close()
            
        except sqlite3.Error as e:
            results['valid'] = False
            results['errors'].append(f"Database connection error: {e}")
        except Exception as e:
            results['valid'] = False
            results['errors'].append(f"Unexpected error validating database: {e}")
        
        return results
    
    def test_data_integrity(self) -> Dict[str, Any]:
        """Test data integrity and consistency"""
        results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'statistics': {}
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Test sentiment_history data integrity
            if self._table_exists(cursor, 'sentiment_history'):
                # Check for invalid sentiment values (should be between -1 and 1)
                cursor.execute("""
                    SELECT COUNT(*) FROM sentiment_history 
                    WHERE overall_sentiment < -1 OR overall_sentiment > 1
                """)
                invalid_sentiment_count = cursor.fetchone()[0]
                
                if invalid_sentiment_count > 0:
                    results['errors'].append(f"Found {invalid_sentiment_count} records with invalid sentiment values")
                    results['valid'] = False
                
                # Check for invalid confidence values (should be between 0 and 1)
                cursor.execute("""
                    SELECT COUNT(*) FROM sentiment_history 
                    WHERE confidence < 0 OR confidence > 1
                """)
                invalid_confidence_count = cursor.fetchone()[0]
                
                if invalid_confidence_count > 0:
                    results['errors'].append(f"Found {invalid_confidence_count} records with invalid confidence values")
                    results['valid'] = False
                
                # Get statistics
                cursor.execute("SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM sentiment_history")
                row = cursor.fetchone()
                results['statistics']['sentiment_records'] = row[0]
                results['statistics']['oldest_record'] = row[1]
                results['statistics']['newest_record'] = row[2]
            
            # Test ml_training_data integrity
            if self._table_exists(cursor, 'ml_training_data'):
                cursor.execute("SELECT COUNT(*) FROM ml_training_data")
                ml_records = cursor.fetchone()[0]
                results['statistics']['ml_training_records'] = ml_records
                
                # Test JSON validity in features column
                cursor.execute("SELECT id, features FROM ml_training_data LIMIT 100")
                invalid_json_count = 0
                for record_id, features_json in cursor.fetchall():
                    try:
                        json.loads(features_json)
                    except json.JSONDecodeError:
                        invalid_json_count += 1
                
                if invalid_json_count > 0:
                    results['warnings'].append(f"Found {invalid_json_count} records with invalid JSON in features")
            
            # Test trading_signals integrity
            if self._table_exists(cursor, 'trading_signals'):
                cursor.execute("SELECT COUNT(*) FROM trading_signals")
                signal_records = cursor.fetchone()[0]
                results['statistics']['trading_signal_records'] = signal_records
                
                # Check for valid signal values
                cursor.execute("""
                    SELECT COUNT(*) FROM trading_signals 
                    WHERE signal NOT IN ('BUY', 'SELL', 'HOLD')
                """)
                invalid_signals = cursor.fetchone()[0]
                
                if invalid_signals > 0:
                    results['errors'].append(f"Found {invalid_signals} records with invalid signal values")
                    results['valid'] = False
            
            conn.close()
            
        except sqlite3.Error as e:
            results['valid'] = False
            results['errors'].append(f"Database error during integrity check: {e}")
        except Exception as e:
            results['valid'] = False
            results['errors'].append(f"Unexpected error during integrity check: {e}")
        
        return results
    
    def test_database_performance(self) -> Dict[str, Any]:
        """Test database performance and identify potential issues"""
        results = {
            'performance_score': 100,
            'issues': [],
            'recommendations': [],
            'timing_results': {}
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Test query performance
            import time
            
            # Test 1: Simple count query
            start_time = time.time()
            cursor.execute("SELECT COUNT(*) FROM sentiment_history")
            cursor.fetchone()
            count_time = time.time() - start_time
            results['timing_results']['count_query'] = count_time
            
            if count_time > 1.0:  # More than 1 second for count is slow
                results['issues'].append("Count queries are slow")
                results['performance_score'] -= 20
                results['recommendations'].append("Consider adding indexes to improve query performance")
            
            # Test 2: Recent records query
            start_time = time.time()
            cursor.execute("""
                SELECT * FROM sentiment_history 
                WHERE timestamp > datetime('now', '-7 days') 
                ORDER BY timestamp DESC 
                LIMIT 100
            """)
            cursor.fetchall()
            recent_query_time = time.time() - start_time
            results['timing_results']['recent_records_query'] = recent_query_time
            
            if recent_query_time > 0.5:
                results['issues'].append("Recent records queries are slow")
                results['performance_score'] -= 15
                results['recommendations'].append("Add index on timestamp column")
            
            # Test 3: Symbol-based query
            start_time = time.time()
            cursor.execute("SELECT * FROM sentiment_history WHERE symbol = 'CBA.AX' LIMIT 50")
            cursor.fetchall()
            symbol_query_time = time.time() - start_time
            results['timing_results']['symbol_query'] = symbol_query_time
            
            if symbol_query_time > 0.3:
                results['issues'].append("Symbol-based queries are slow")
                results['performance_score'] -= 10
                results['recommendations'].append("Add index on symbol column")
            
            # Check database size
            cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
            db_size = cursor.fetchone()[0]
            results['timing_results']['database_size_bytes'] = db_size
            
            if db_size > 100 * 1024 * 1024:  # 100MB
                results['issues'].append("Database is getting large (>100MB)")
                results['recommendations'].append("Consider archiving old data")
            
            conn.close()
            
        except Exception as e:
            results['issues'].append(f"Performance test failed: {e}")
            results['performance_score'] = 0
        
        return results
    
    def _table_exists(self, cursor, table_name: str) -> bool:
        """Check if a table exists"""
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        return cursor.fetchone() is not None
    
    def create_test_data(self, num_records: int = 100) -> Dict[str, Any]:
        """Create test data for testing purposes"""
        results = {
            'success': True,
            'records_created': 0,
            'errors': []
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create test sentiment data
            test_symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX']
            test_data = []
            
            for i in range(num_records):
                symbol = test_symbols[i % len(test_symbols)]
                timestamp = datetime.now() - timedelta(days=i // 4)
                sentiment = (i % 200 - 100) / 100.0  # Range -1 to 1
                confidence = (i % 100) / 100.0  # Range 0 to 1
                news_count = i % 20
                
                test_data.append((symbol, timestamp, sentiment, confidence, news_count))
            
            cursor.executemany("""
                INSERT INTO sentiment_history (symbol, timestamp, overall_sentiment, confidence, news_count)
                VALUES (?, ?, ?, ?, ?)
            """, test_data)
            
            conn.commit()
            results['records_created'] = len(test_data)
            
            conn.close()
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Failed to create test data: {e}")
        
        return results
    
    def cleanup_test_data(self) -> Dict[str, Any]:
        """Clean up test data"""
        results = {
            'success': True,
            'records_deleted': 0,
            'errors': []
        }
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete recent test data (last 7 days)
            cursor.execute("""
                DELETE FROM sentiment_history 
                WHERE timestamp > datetime('now', '-7 days')
            """)
            
            results['records_deleted'] = cursor.rowcount
            conn.commit()
            conn.close()
            
        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Failed to cleanup test data: {e}")
        
        return results


class TestDatabaseIntegration(unittest.TestCase):
    """Integration tests for database operations"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'test_integration.db')
        self.tester = DatabaseTester(self.test_db_path)
        
        # Create test database with schema
        self._create_test_database()
    
    def tearDown(self):
        """Clean up test database"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _create_test_database(self):
        """Create test database with proper schema"""
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        
        # Create sentiment_history table
        cursor.execute('''
            CREATE TABLE sentiment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                overall_sentiment REAL NOT NULL,
                confidence REAL NOT NULL,
                news_count INTEGER DEFAULT 0
            )
        ''')
        
        # Create ml_training_data table
        cursor.execute('''
            CREATE TABLE ml_training_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                features TEXT NOT NULL,
                target REAL NOT NULL
            )
        ''')
        
        # Create trading_signals table
        cursor.execute('''
            CREATE TABLE trading_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                signal TEXT NOT NULL,
                confidence REAL NOT NULL,
                price REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def test_database_structure_validation(self):
        """Test database structure validation"""
        results = self.tester.validate_database_structure()
        
        self.assertTrue(results['valid'], f"Database structure invalid: {results['errors']}")
        self.assertEqual(len(results['missing_tables']), 0, f"Missing tables: {results['missing_tables']}")
        self.assertIn('sentiment_history', results['tables_found'])
        self.assertIn('ml_training_data', results['tables_found'])
        self.assertIn('trading_signals', results['tables_found'])
    
    def test_data_integrity_validation(self):
        """Test data integrity validation"""
        # First create some test data
        create_results = self.tester.create_test_data(50)
        self.assertTrue(create_results['success'], f"Failed to create test data: {create_results['errors']}")
        
        # Now test integrity
        results = self.tester.test_data_integrity()
        
        self.assertTrue(results['valid'], f"Data integrity check failed: {results['errors']}")
        self.assertGreater(results['statistics']['sentiment_records'], 0)
    
    def test_database_performance(self):
        """Test database performance"""
        # Create test data for performance testing
        self.tester.create_test_data(1000)
        
        results = self.tester.test_database_performance()
        
        self.assertGreater(results['performance_score'], 50, "Database performance is too low")
        self.assertIn('count_query', results['timing_results'])
        self.assertIn('database_size_bytes', results['timing_results'])
    
    def test_concurrent_access(self):
        """Test database concurrent access handling"""
        import threading
        import time
        
        errors = []
        
        def insert_data(thread_id):
            try:
                conn = sqlite3.connect(self.test_db_path)
                cursor = conn.cursor()
                
                for i in range(10):
                    cursor.execute("""
                        INSERT INTO sentiment_history (symbol, timestamp, overall_sentiment, confidence, news_count)
                        VALUES (?, ?, ?, ?, ?)
                    """, (f'TEST{thread_id}.AX', datetime.now(), 0.5, 0.7, 5))
                    time.sleep(0.01)  # Small delay
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                errors.append(f"Thread {thread_id} error: {e}")
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=insert_data, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check for errors
        self.assertEqual(len(errors), 0, f"Concurrent access errors: {errors}")
        
        # Verify all data was inserted
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sentiment_history WHERE symbol LIKE 'TEST%.AX'")
        count = cursor.fetchone()[0]
        conn.close()
        
        self.assertEqual(count, 30, f"Expected 30 records, found {count}")


def run_comprehensive_database_tests(db_path: str = None):
    """Run comprehensive database tests"""
    if db_path is None:
        # Create temporary database for testing
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, 'comprehensive_test.db')
    
    print(f"🔍 Running Comprehensive Database Tests")
    print(f"Database: {db_path}")
    print("=" * 60)
    
    tester = DatabaseTester(db_path)
    
    # Test 1: Structure validation
    print("1. Testing Database Structure...")
    structure_results = tester.validate_database_structure()
    if structure_results['valid']:
        print("   ✅ Database structure is valid")
    else:
        print(f"   ❌ Database structure issues: {structure_results['errors']}")
    
    # Test 2: Data integrity
    print("2. Testing Data Integrity...")
    integrity_results = tester.test_data_integrity()
    if integrity_results['valid']:
        print("   ✅ Data integrity is valid")
        print(f"   📊 Statistics: {integrity_results['statistics']}")
    else:
        print(f"   ❌ Data integrity issues: {integrity_results['errors']}")
    
    # Test 3: Performance
    print("3. Testing Database Performance...")
    performance_results = tester.test_database_performance()
    print(f"   📈 Performance Score: {performance_results['performance_score']}/100")
    if performance_results['issues']:
        print(f"   ⚠️ Issues: {performance_results['issues']}")
    if performance_results['recommendations']:
        print(f"   💡 Recommendations: {performance_results['recommendations']}")
    
    print("=" * 60)
    print("✅ Database testing complete!")
    
    return {
        'structure': structure_results,
        'integrity': integrity_results,
        'performance': performance_results
    }


if __name__ == '__main__':
    # Run database tests
    unittest.main(verbosity=2)
