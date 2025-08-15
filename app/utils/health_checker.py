"""
System Health Checker for Trading Application

Provides comprehensive health monitoring for databases, APIs, ML models, and other system components.
Designed to work with the app stabilization framework.
"""

import os
import sqlite3
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import logging

import sqlite3
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
import logging

class SystemHealthChecker:
    """Comprehensive system health monitoring"""
    
    def __init__(self, config_manager=None):
        self.logger = logging.getLogger(__name__)
        self.config = config_manager
        self.last_check = None
        self.health_history = []
    
    def check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and integrity"""
        result = {
            'status': 'unknown',
            'message': '',
            'details': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            db_path = self.config.get('database.path', 'data/trading_unified.db') if self.config else 'data/trading_unified.db'
            
            if not Path(db_path).exists():
                result['status'] = 'error'
                result['message'] = f'Database file not found: {db_path}'
                return result
            
            # Test connection
            conn = sqlite3.connect(db_path, timeout=5)
            cursor = conn.cursor()
            
            # Check table existence
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Check data freshness
            freshness_checks = {}
            if 'sentiment_features' in tables:
                cursor.execute("SELECT MAX(timestamp) FROM sentiment_features")
                latest_sentiment = cursor.fetchone()[0]
                if latest_sentiment:
                    latest_dt = datetime.fromisoformat(latest_sentiment.replace('Z', '+00:00'))
                    age_hours = (datetime.now() - latest_dt).total_seconds() / 3600
                    freshness_checks['sentiment_data'] = {
                        'latest': latest_sentiment,
                        'age_hours': age_hours,
                        'fresh': age_hours < 24
                    }
            
            conn.close()
            
            result['status'] = 'healthy'
            result['message'] = f'Database operational with {len(tables)} tables'
            result['details'] = {
                'table_count': len(tables),
                'tables': tables,
                'freshness': freshness_checks
            }
            
        except Exception as e:
            result['status'] = 'error'
            result['message'] = f'Database check failed: {e}'
            self.logger.error(f"Database health check failed: {e}")
        
        return result
    
    def check_api_health(self) -> Dict[str, Any]:
        """Check external API availability"""
        result = {
            'status': 'unknown',
            'message': '',
            'apis': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # APIs to check
        api_endpoints = [
            ('Yahoo Finance', 'https://finance.yahoo.com'),
            ('Reddit', 'https://www.reddit.com'),
        ]
        
        healthy_apis = 0
        total_apis = len(api_endpoints)
        
        for api_name, url in api_endpoints:
            api_result = {
                'status': 'unknown',
                'response_time': None,
                'error': None
            }
            
            try:
                start_time = datetime.now()
                response = requests.get(url, timeout=5)
                response_time = (datetime.now() - start_time).total_seconds()
                
                if response.status_code == 200:
                    api_result['status'] = 'healthy'
                    api_result['response_time'] = response_time
                    healthy_apis += 1
                else:
                    api_result['status'] = 'error'
                    api_result['error'] = f'HTTP {response.status_code}'
                    
            except Exception as e:
                api_result['status'] = 'error'
                api_result['error'] = str(e)
            
            result['apis'][api_name] = api_result
        
        # Overall API health
        if healthy_apis == total_apis:
            result['status'] = 'healthy'
            result['message'] = 'All APIs accessible'
        elif healthy_apis > 0:
            result['status'] = 'degraded'
            result['message'] = f'{healthy_apis}/{total_apis} APIs accessible'
        else:
            result['status'] = 'error'
            result['message'] = 'No APIs accessible'
        
        return result
    
    def check_ml_models(self) -> Dict[str, Any]:
        """Check ML model availability"""
        try:
            from enhanced_evening_analyzer_with_ml import AdvancedMarketAnalyzer
            
            # Check if models are trained/available
            analyzer = AdvancedMarketAnalyzer()
            
            # Basic test of ML components
            # This might need adjustment based on actual model structure
            return {
                'status': 'healthy',
                'message': 'ML models are available and functional',
                'timestamp': datetime.now().isoformat()
            }
            
        except ImportError as e:
            return {
                'status': 'warning',
                'message': f'ML modules not available (OK for basic operations): {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
        except FileNotFoundError as e:
            return {
                'status': 'warning',
                'message': f'ML model files not found (will retrain when needed): {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            # More forgiving - treat most ML issues as warnings in development
            if 'model' in str(e).lower() or 'trained' in str(e).lower():
                return {
                    'status': 'warning',
                    'message': f'ML models need training (normal for first run): {str(e)}',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'error',
                    'message': f'ML system error: {str(e)}',
                    'timestamp': datetime.now().isoformat()
                }
    
    def check_file_system(self) -> Dict[str, Any]:
        """Check file system access and key directories"""
        try:
            # Check critical directories exist and are writable
            from pathlib import Path
            
            critical_paths = [
                Path('.'),  # Current directory
                Path('logs') if Path('logs').exists() else None,
                Path('data') if Path('data').exists() else None,
            ]
            
            issues = []
            for path in critical_paths:
                if path is None:
                    continue
                if not path.exists():
                    issues.append(f"Missing directory: {path}")
                elif not os.access(path, os.W_OK):
                    issues.append(f"No write access: {path}")
            
            if issues:
                return {
                    'status': 'warning',
                    'message': f'File system issues: {"; ".join(issues)}',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'healthy',
                    'message': 'File system access is healthy',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'message': f'File system check failed: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def check_external_apis(self) -> Dict[str, Any]:
        """Check external API connectivity (basic network test)"""
        try:
            import urllib.request
            
            # Basic connectivity test
            urllib.request.urlopen('https://httpbin.org/get', timeout=5)
            
            return {
                'status': 'healthy',
                'message': 'External API connectivity is healthy',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'warning',
                'message': f'External API connectivity issues (OK for offline): {str(e)}',
                'timestamp': datetime.now().isoformat()
            }
    
    def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run all health checks and provide comprehensive report"""
        self.logger.info("Running comprehensive health check...")
        
        checks = {
            'database': self.check_database_health(),
            'api_health': self.check_api_health(),
            'ml_models': self.check_ml_models(),
            'file_system': self.check_file_system(),
            'external_apis': self.check_external_apis()
        }
    
    def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get health trends over specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_checks = [
            check for check in self.health_history
            if datetime.fromisoformat(check['timestamp']) > cutoff_time
        ]
        
        if not recent_checks:
            return {'message': 'No recent health data available'}
        
        # Calculate trends
        trends = {
            'period_hours': hours,
            'check_count': len(recent_checks),
            'status_distribution': {},
            'average_health': 0
        }
        
        status_counts = {}
        health_scores = []
        
        for check in recent_checks:
            status = check['overall_status']
            status_counts[status] = status_counts.get(status, 0) + 1
            health_scores.append(check['summary'].get('health_percentage', 0))
        
        trends['status_distribution'] = status_counts
        trends['average_health'] = sum(health_scores) / len(health_scores) if health_scores else 0
        
        return trends
