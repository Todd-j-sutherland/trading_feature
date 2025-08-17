#!/usr/bin/env python3
"""
Deep System Analysis Tool
Comprehensive analysis of app.main and the entire trading system to identify:
- Data collection issues
- Warning/error patterns in logs
- Database inconsistencies
- System weak spots and root issues
"""

import os
import sys
import sqlite3
import subprocess
import json
import logging
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class DeepSystemAnalyzer:
    """Comprehensive system analyzer"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.data_dir = self.project_root / "data"
        self.log_dir = self.project_root / "logs"
        self.issues = []
        self.warnings = []
        self.critical_issues = []
        
        # Ensure logs directory exists
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup analysis logging
        self.setup_analysis_logging()
    
    def setup_analysis_logging(self):
        """Setup logging for analysis"""
        log_file = self.log_dir / f"deep_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.analysis_log = log_file
        
    def add_issue(self, severity: str, component: str, description: str, details: str = ""):
        """Add an issue to the analysis"""
        issue = {
            'timestamp': datetime.now().isoformat(),
            'severity': severity,
            'component': component,
            'description': description,
            'details': details
        }
        
        if severity == 'CRITICAL':
            self.critical_issues.append(issue)
        elif severity == 'WARNING':
            self.warnings.append(issue)
        else:
            self.issues.append(issue)
        
        self.logger.log(
            logging.CRITICAL if severity == 'CRITICAL' else 
            logging.WARNING if severity == 'WARNING' else 
            logging.INFO,
            f"[{component}] {description}: {details}"
        )
    
    def analyze_app_main_structure(self) -> Dict[str, Any]:
        """Analyze app.main structure and dependencies"""
        print("🔍 ANALYZING APP.MAIN STRUCTURE")
        print("=" * 50)
        
        results = {
            'imports': [],
            'dependencies': [],
            'missing_imports': [],
            'command_handlers': [],
            'error_handling': []
        }
        
        app_main_path = self.project_root / "app" / "main.py"
        
        if not app_main_path.exists():
            self.add_issue('CRITICAL', 'app.main', 'Main entry point not found', str(app_main_path))
            return results
        
        try:
            # Check imports
            with open(app_main_path, 'r') as f:
                content = f.read()
            
            # Extract import lines
            import_lines = [line.strip() for line in content.split('\n') if line.strip().startswith('from ') or line.strip().startswith('import ')]
            results['imports'] = import_lines
            
            # Check if critical imports exist
            critical_modules = [
                'app.services.daily_manager',
                'app.config.settings',
                'app.utils.error_handler',
                'app.utils.health_checker'
            ]
            
            for module in critical_modules:
                if not any(module in imp for imp in import_lines):
                    self.add_issue('WARNING', 'app.main', 'Missing critical import', module)
                else:
                    # Check if the actual file exists
                    module_path = self.project_root / module.replace('.', '/') + '.py'
                    if not module_path.exists():
                        self.add_issue('CRITICAL', 'app.main', 'Imported module not found', str(module_path))
                        results['missing_imports'].append(module)
            
            # Extract command handlers
            commands = ['morning', 'evening', 'status', 'weekly', 'news', 'divergence', 'economic', 'backtest']
            for cmd in commands:
                if f"'{cmd}'" in content:
                    results['command_handlers'].append(cmd)
            
            print(f"✅ Found {len(results['imports'])} imports")
            print(f"✅ Found {len(results['command_handlers'])} command handlers")
            print(f"⚠️  Missing imports: {len(results['missing_imports'])}")
            
        except Exception as e:
            self.add_issue('CRITICAL', 'app.main', 'Failed to analyze structure', str(e))
        
        return results
    
    def test_data_collection_components(self) -> Dict[str, Any]:
        """Test data collection components"""
        print("\n🔍 TESTING DATA COLLECTION COMPONENTS")
        print("=" * 50)
        
        results = {
            'data_collectors': {},
            'database_status': {},
            'api_connections': {}
        }
        
        # Test database connectivity
        db_path = self.data_dir / "trading_predictions.db"
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path), timeout=5)
                cursor = conn.cursor()
                
                # Check database structure
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                results['database_status']['tables'] = tables
                results['database_status']['status'] = 'connected'
                
                # Check data freshness
                for table in ['predictions', 'enhanced_outcomes', 'enhanced_features']:
                    if table in tables:
                        try:
                            cursor.execute(f"SELECT COUNT(*), MAX(created_at) FROM {table}")
                            count, last_update = cursor.fetchone()
                            results['database_status'][table] = {
                                'count': count,
                                'last_update': last_update
                            }
                            
                            # Check data freshness (warn if older than 7 days)
                            if last_update:
                                try:
                                    last_date = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
                                    days_old = (datetime.now() - last_date.replace(tzinfo=None)).days
                                    if days_old > 7:
                                        self.add_issue('WARNING', 'database', f'{table} data is stale', f'{days_old} days old')
                                except:
                                    pass
                                    
                        except Exception as e:
                            self.add_issue('WARNING', 'database', f'Error checking {table}', str(e))
                
                conn.close()
                print(f"✅ Database connected: {len(tables)} tables found")
                
            except Exception as e:
                self.add_issue('CRITICAL', 'database', 'Database connection failed', str(e))
                results['database_status']['status'] = 'failed'
                results['database_status']['error'] = str(e)
        else:
            self.add_issue('CRITICAL', 'database', 'Database file not found', str(db_path))
        
        # Test data collector imports
        data_collectors = [
            'app.core.data.collectors.market_data',
            'app.core.data.collectors.news_collector',
            'enhanced_ml_system.analyzers.enhanced_morning_analyzer_with_ml',
            'enhanced_ml_system.analyzers.enhanced_evening_analyzer_with_ml'
        ]
        
        for collector in data_collectors:
            try:
                module_path = self.project_root / collector.replace('.', '/') + '.py'
                if module_path.exists():
                    results['data_collectors'][collector] = 'available'
                    print(f"✅ Data collector available: {collector}")
                else:
                    results['data_collectors'][collector] = 'missing'
                    self.add_issue('WARNING', 'data_collection', 'Data collector missing', collector)
                    print(f"❌ Data collector missing: {collector}")
            except Exception as e:
                results['data_collectors'][collector] = 'error'
                self.add_issue('WARNING', 'data_collection', 'Error checking collector', f"{collector}: {e}")
        
        return results
    
    def run_system_commands_and_capture_logs(self) -> Dict[str, Any]:
        """Run system commands and capture all logs for analysis"""
        print("\n🔍 RUNNING SYSTEM COMMANDS & CAPTURING LOGS")
        print("=" * 50)
        
        results = {
            'command_outputs': {},
            'log_analysis': {},
            'errors_found': [],
            'warnings_found': []
        }
        
        # Commands to test
        test_commands = [
            ('status', 'Quick status check'),
            ('morning', 'Morning routine'),
            ('evening', 'Evening routine'),
        ]
        
        for command, description in test_commands:
            print(f"\n🧪 Testing: {description}")
            
            # Create log file for this command
            log_file = self.log_dir / f"test_{command}_{datetime.now().strftime('%H%M%S')}.log"
            
            try:
                # Run command and capture output using local venv
                cmd = f"cd {self.project_root} && source venv/bin/activate && python -m app.main {command}"
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120  # 2 minute timeout
                )
                
                # Save output to log file
                with open(log_file, 'w') as f:
                    f.write(f"Command: {cmd}\n")
                    f.write(f"Return code: {result.returncode}\n")
                    f.write(f"STDOUT:\n{result.stdout}\n")
                    f.write(f"STDERR:\n{result.stderr}\n")
                
                results['command_outputs'][command] = {
                    'return_code': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'log_file': str(log_file)
                }
                
                # Analyze output for errors/warnings
                output_text = result.stdout + result.stderr
                
                # Look for error patterns
                error_patterns = [
                    'ERROR', 'Error:', 'Exception:', 'Traceback', 'Failed to', 
                    'ConnectionError', 'ImportError', 'ModuleNotFoundError',
                    'sqlite3.OperationalError', 'KeyError', 'AttributeError'
                ]
                
                warning_patterns = [
                    'WARNING', 'Warning:', 'WARN', 'Deprecated', 'FutureWarning',
                    'UserWarning', 'DeprecationWarning'
                ]
                
                for pattern in error_patterns:
                    if pattern in output_text:
                        error_lines = [line.strip() for line in output_text.split('\n') if pattern in line]
                        for line in error_lines:
                            results['errors_found'].append({
                                'command': command,
                                'pattern': pattern,
                                'line': line,
                                'log_file': str(log_file)
                            })
                            self.add_issue('CRITICAL', f'command_{command}', f'Error pattern found: {pattern}', line)
                
                for pattern in warning_patterns:
                    if pattern in output_text:
                        warning_lines = [line.strip() for line in output_text.split('\n') if pattern in line]
                        for line in warning_lines:
                            results['warnings_found'].append({
                                'command': command,
                                'pattern': pattern,
                                'line': line,
                                'log_file': str(log_file)
                            })
                            self.add_issue('WARNING', f'command_{command}', f'Warning pattern found: {pattern}', line)
                
                if result.returncode == 0:
                    print(f"  ✅ {command}: Completed successfully")
                else:
                    print(f"  ❌ {command}: Failed with code {result.returncode}")
                    self.add_issue('CRITICAL', f'command_{command}', 'Command failed', f'Exit code: {result.returncode}')
                
            except subprocess.TimeoutExpired:
                self.add_issue('CRITICAL', f'command_{command}', 'Command timeout', f'Exceeded 120 seconds')
                print(f"  ⏱️  {command}: Timeout (>120s)")
            except Exception as e:
                self.add_issue('CRITICAL', f'command_{command}', 'Command execution error', str(e))
                print(f"  💥 {command}: Execution error - {e}")
        
        print(f"\n📊 Log Analysis Summary:")
        print(f"  🔍 Commands tested: {len(test_commands)}")
        print(f"  ❌ Errors found: {len(results['errors_found'])}")
        print(f"  ⚠️  Warnings found: {len(results['warnings_found'])}")
        
        return results
    
    def analyze_database_consistency(self) -> Dict[str, Any]:
        """Deep analysis of database consistency and data quality"""
        print("\n🔍 ANALYZING DATABASE CONSISTENCY & QUALITY")
        print("=" * 50)
        
        results = {
            'schema_analysis': {},
            'data_consistency': {},
            'referential_integrity': {},
            'data_quality_issues': []
        }
        
        db_path = self.data_dir / "trading_predictions.db"
        if not db_path.exists():
            self.add_issue('CRITICAL', 'database', 'Database not found', str(db_path))
            return results
        
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"📊 Analyzing {len(tables)} tables...")
            
            for table in tables:
                if table == 'sqlite_sequence':
                    continue
                    
                print(f"  🔍 Analyzing table: {table}")
                
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table})")
                schema = cursor.fetchall()
                results['schema_analysis'][table] = {
                    'columns': len(schema),
                    'schema': schema
                }
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                results['schema_analysis'][table]['row_count'] = row_count
                
                if row_count == 0:
                    self.add_issue('WARNING', 'database', f'Table {table} is empty', '')
                    continue
                
                # Check for NULL values in important columns
                for col_info in schema:
                    col_name = col_info[1]
                    col_type = col_info[2]
                    not_null = col_info[3]
                    
                    if not_null:  # Column should not be NULL
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col_name} IS NULL")
                        null_count = cursor.fetchone()[0]
                        if null_count > 0:
                            issue = f"Table {table}, column {col_name}: {null_count} NULL values in NOT NULL column"
                            results['data_quality_issues'].append(issue)
                            self.add_issue('CRITICAL', 'database', 'NULL values in NOT NULL column', issue)
                
                # Check for duplicate primary keys (if any)
                try:
                    # Find primary key column
                    pk_columns = [col[1] for col in schema if col[5] == 1]  # col[5] is pk flag
                    if pk_columns:
                        pk_col = pk_columns[0]
                        cursor.execute(f"SELECT {pk_col}, COUNT(*) FROM {table} GROUP BY {pk_col} HAVING COUNT(*) > 1")
                        duplicates = cursor.fetchall()
                        if duplicates:
                            issue = f"Table {table}: {len(duplicates)} duplicate primary keys"
                            results['data_quality_issues'].append(issue)
                            self.add_issue('CRITICAL', 'database', 'Duplicate primary keys', issue)
                except Exception as e:
                    pass  # Skip if no PK or other issues
                
                # Check data types consistency
                for col_info in schema:
                    col_name = col_info[1]
                    col_type = col_info[2].upper()
                    
                    if 'INT' in col_type:
                        # Check if all values are actually integers
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col_name} IS NOT NULL AND TYPEOF({col_name}) != 'integer'")
                        bad_types = cursor.fetchone()[0]
                        if bad_types > 0:
                            issue = f"Table {table}, column {col_name}: {bad_types} non-integer values in INTEGER column"
                            results['data_quality_issues'].append(issue)
                            self.add_issue('WARNING', 'database', 'Data type mismatch', issue)
                    
                    elif 'REAL' in col_type or 'FLOAT' in col_type:
                        # Check for non-numeric values
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col_name} IS NOT NULL AND TYPEOF({col_name}) NOT IN ('real', 'integer')")
                        bad_types = cursor.fetchone()[0]
                        if bad_types > 0:
                            issue = f"Table {table}, column {col_name}: {bad_types} non-numeric values in REAL column"
                            results['data_quality_issues'].append(issue)
                            self.add_issue('WARNING', 'database', 'Data type mismatch', issue)
                
                # Check timestamp columns for reasonable dates
                timestamp_columns = [col[1] for col in schema if 'timestamp' in col[1].lower() or 'created_at' in col[1].lower() or 'date' in col[1].lower()]
                for ts_col in timestamp_columns:
                    try:
                        # Check for future dates (more than 1 day in future)
                        future_cutoff = (datetime.now() + timedelta(days=1)).isoformat()
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {ts_col} > ?", (future_cutoff,))
                        future_count = cursor.fetchone()[0]
                        
                        # Check for very old dates (more than 2 years ago)
                        old_cutoff = (datetime.now() - timedelta(days=730)).isoformat()
                        cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {ts_col} < ?", (old_cutoff,))
                        old_count = cursor.fetchone()[0]
                        
                        if future_count > 0:
                            issue = f"Table {table}, column {ts_col}: {future_count} future timestamps"
                            results['data_quality_issues'].append(issue)
                            self.add_issue('WARNING', 'database', 'Future timestamps', issue)
                        
                        if old_count > 0:
                            issue = f"Table {table}, column {ts_col}: {old_count} very old timestamps (>2 years)"
                            results['data_quality_issues'].append(issue)
                            self.add_issue('INFO', 'database', 'Old timestamps', issue)
                    except Exception as e:
                        pass  # Skip timestamp analysis if format issues
            
            conn.close()
            
            print(f"✅ Database analysis complete")
            print(f"  📊 Tables analyzed: {len([t for t in tables if t != 'sqlite_sequence'])}")
            print(f"  ❌ Data quality issues: {len(results['data_quality_issues'])}")
            
        except Exception as e:
            self.add_issue('CRITICAL', 'database', 'Database analysis failed', str(e))
            print(f"❌ Database analysis failed: {e}")
        
        return results
    
    def analyze_system_dependencies(self) -> Dict[str, Any]:
        """Analyze system dependencies and potential issues"""
        print("\n🔍 ANALYZING SYSTEM DEPENDENCIES")
        print("=" * 50)
        
        results = {
            'python_packages': {},
            'missing_packages': [],
            'version_conflicts': [],
            'file_dependencies': {}
        }
        
        # Check for requirements.txt
        req_files = ['requirements.txt', 'requirements-dev.txt', 'requirements-prod.txt']
        requirements = []
        
        for req_file in req_files:
            req_path = self.project_root / req_file
            if req_path.exists():
                try:
                    with open(req_path, 'r') as f:
                        req_content = f.read()
                        requirements.extend([line.strip() for line in req_content.split('\n') if line.strip() and not line.startswith('#')])
                    print(f"✅ Found requirements: {req_file}")
                except Exception as e:
                    self.add_issue('WARNING', 'dependencies', f'Error reading {req_file}', str(e))
        
        # Test critical packages
        critical_packages = [
            'sqlite3', 'requests', 'pandas', 'numpy', 'streamlit',
            'yfinance', 'beautifulsoup4', 'lxml', 'matplotlib', 'plotly'
        ]
        
        for package in critical_packages:
            try:
                if package == 'sqlite3':
                    import sqlite3
                    results['python_packages'][package] = 'built-in'
                else:
                    __import__(package)
                    results['python_packages'][package] = 'available'
                print(f"✅ Package available: {package}")
            except ImportError:
                results['missing_packages'].append(package)
                self.add_issue('WARNING', 'dependencies', f'Missing package: {package}', '')
                print(f"❌ Package missing: {package}")
        
        # Check critical files exist
        critical_files = [
            'app/__init__.py',
            'app/main.py',
            'app/services/daily_manager.py',
            'app/config/settings.py',
            'enhanced_ml_system/__init__.py',
            'enhanced_ml_system/analyzers/enhanced_morning_analyzer_with_ml.py',
            'enhanced_ml_system/analyzers/enhanced_evening_analyzer_with_ml.py'
        ]
        
        for file_path in critical_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                results['file_dependencies'][file_path] = 'exists'
                print(f"✅ Critical file exists: {file_path}")
            else:
                results['file_dependencies'][file_path] = 'missing'
                self.add_issue('CRITICAL', 'dependencies', f'Critical file missing: {file_path}', str(full_path))
                print(f"❌ Critical file missing: {file_path}")
        
        return results
    
    def generate_comprehensive_report(self, all_results: Dict[str, Any]) -> str:
        """Generate a comprehensive analysis report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.log_dir / f"deep_analysis_report_{timestamp}.json"
        summary_file = self.log_dir / f"analysis_summary_{timestamp}.txt"
        
        # Create detailed JSON report
        report_data = {
            'analysis_timestamp': datetime.now().isoformat(),
            'analysis_version': '1.0',
            'project_root': str(self.project_root),
            'results': all_results,
            'issues': {
                'critical': self.critical_issues,
                'warnings': self.warnings,
                'info': self.issues
            },
            'summary': {
                'total_critical_issues': len(self.critical_issues),
                'total_warnings': len(self.warnings),
                'total_info_issues': len(self.issues),
                'overall_health': 'CRITICAL' if self.critical_issues else 'WARNING' if self.warnings else 'HEALTHY'
            }
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        # Create human-readable summary
        summary = f"""
🔍 DEEP SYSTEM ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
={'=' * 60}

🎯 EXECUTIVE SUMMARY
{'-' * 30}
Overall Health: {report_data['summary']['overall_health']}
Critical Issues: {len(self.critical_issues)}
Warnings: {len(self.warnings)}
Info Items: {len(self.issues)}

🚨 CRITICAL ISSUES ({len(self.critical_issues)})
{'-' * 30}
"""
        
        for issue in self.critical_issues:
            summary += f"❌ [{issue['component']}] {issue['description']}\n"
            if issue['details']:
                summary += f"   Details: {issue['details']}\n"
        
        summary += f"""
⚠️  WARNING ISSUES ({len(self.warnings)})
{'-' * 30}
"""
        
        for issue in self.warnings:
            summary += f"⚠️  [{issue['component']}] {issue['description']}\n"
            if issue['details']:
                summary += f"   Details: {issue['details']}\n"
        
        # Add recommendations
        summary += f"""
💡 RECOMMENDATIONS
{'-' * 30}
"""
        
        if self.critical_issues:
            summary += "🔥 IMMEDIATE ACTION REQUIRED:\n"
            for issue in self.critical_issues:
                if 'database' in issue['component']:
                    summary += "   • Fix database connectivity and schema issues\n"
                elif 'command' in issue['component']:
                    summary += "   • Resolve command execution failures\n"
                elif 'dependencies' in issue['component']:
                    summary += "   • Install missing critical dependencies\n"
        
        if self.warnings:
            summary += "\n📋 SHOULD ADDRESS:\n"
            if any('data' in issue['component'] for issue in self.warnings):
                summary += "   • Review data quality and freshness\n"
            if any('import' in issue['description'].lower() for issue in self.warnings):
                summary += "   • Check import dependencies\n"
        
        summary += f"""
📁 DETAILED REPORTS
{'-' * 30}
JSON Report: {report_file}
Analysis Log: {self.analysis_log}
Command Logs: {self.log_dir}/test_*.log

✅ ANALYSIS COMPLETE
Review the detailed reports above for full technical details.
"""
        
        with open(summary_file, 'w') as f:
            f.write(summary)
        
        return str(summary_file)
    
    def run_full_analysis(self):
        """Run complete deep system analysis"""
        print("🚀 STARTING DEEP SYSTEM ANALYSIS")
        print("=" * 60)
        print(f"Project Root: {self.project_root}")
        print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        all_results = {}
        
        try:
            # 1. Analyze app.main structure
            all_results['app_main_analysis'] = self.analyze_app_main_structure()
            
            # 2. Test data collection
            all_results['data_collection_analysis'] = self.test_data_collection_components()
            
            # 3. Run commands and capture logs
            all_results['command_analysis'] = self.run_system_commands_and_capture_logs()
            
            # 4. Analyze database consistency
            all_results['database_analysis'] = self.analyze_database_consistency()
            
            # 5. Check dependencies
            all_results['dependency_analysis'] = self.analyze_system_dependencies()
            
            # 6. Generate comprehensive report
            summary_file = self.generate_comprehensive_report(all_results)
            
            print("\n" + "=" * 60)
            print("🎉 DEEP ANALYSIS COMPLETE")
            print("=" * 60)
            print(f"📊 Critical Issues: {len(self.critical_issues)}")
            print(f"⚠️  Warnings: {len(self.warnings)}")
            print(f"📋 Info Items: {len(self.issues)}")
            print(f"📄 Summary Report: {summary_file}")
            print(f"📁 All logs saved to: {self.log_dir}")
            
            # Display summary
            with open(summary_file, 'r') as f:
                print("\n" + f.read())
                
        except Exception as e:
            self.add_issue('CRITICAL', 'analysis', 'Analysis framework failed', str(e))
            print(f"💥 Analysis failed: {e}")
            traceback.print_exc()

def main():
    """Run deep system analysis"""
    analyzer = DeepSystemAnalyzer()
    analyzer.run_full_analysis()

if __name__ == "__main__":
    main()
