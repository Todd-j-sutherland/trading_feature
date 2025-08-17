#!/usr/bin/env python3
"""
Enhanced Deep Analysis with Comprehensive Logging
Export all logs and error details to files for evaluation
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

class ComprehensiveAnalyzer:
    """Enhanced analyzer with detailed logging and error capture"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.logs_dir = self.project_root / "analysis_logs"
        self.logs_dir.mkdir(exist_ok=True)
        
        # Setup comprehensive logging
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.setup_logging()
        
        self.issues = []
        self.errors = []
        self.warnings = []
        
    def setup_logging(self):
        """Setup comprehensive logging to multiple files"""
        # Main analysis log
        main_log = self.logs_dir / f"analysis_main_{self.timestamp}.log"
        
        # Error-specific log
        error_log = self.logs_dir / f"errors_{self.timestamp}.log"
        
        # Database-specific log
        db_log = self.logs_dir / f"database_{self.timestamp}.log"
        
        # Command execution log
        cmd_log = self.logs_dir / f"commands_{self.timestamp}.log"
        
        # Setup logger
        self.logger = logging.getLogger('comprehensive_analyzer')
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Main log handler
        main_handler = logging.FileHandler(main_log)
        main_handler.setLevel(logging.DEBUG)
        main_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        main_handler.setFormatter(main_format)
        self.logger.addHandler(main_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
        # Store log files for reference
        self.log_files = {
            'main': main_log,
            'errors': error_log,
            'database': db_log,
            'commands': cmd_log
        }
        
        print(f"📁 Logs will be saved to: {self.logs_dir}")
        print(f"📄 Main log: {main_log}")
        
    def log_error(self, component: str, error: str, details: str = "", exception: Exception = None):
        """Log error with full details"""
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'component': component,
            'error': error,
            'details': details,
            'exception': str(exception) if exception else None,
            'traceback': traceback.format_exc() if exception else None
        }
        
        self.errors.append(error_entry)
        self.logger.error(f"[{component}] {error}: {details}")
        
        if exception:
            self.logger.error(f"Exception: {str(exception)}")
            self.logger.debug(f"Traceback: {traceback.format_exc()}")
        
        # Write to error-specific log
        with open(self.log_files['errors'], 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"TIMESTAMP: {error_entry['timestamp']}\n")
            f.write(f"COMPONENT: {component}\n")
            f.write(f"ERROR: {error}\n")
            f.write(f"DETAILS: {details}\n")
            if exception:
                f.write(f"EXCEPTION: {str(exception)}\n")
                f.write(f"TRACEBACK:\n{traceback.format_exc()}\n")
            f.write(f"{'='*60}\n")

    def test_database_comprehensive(self):
        """Comprehensive database testing with detailed error logging"""
        print("\n🔍 COMPREHENSIVE DATABASE ANALYSIS")
        print("=" * 50)
        
        db_path = self.project_root / "data" / "trading_predictions.db"
        
        # Write to database log
        with open(self.log_files['database'], 'w') as f:
            f.write(f"DATABASE ANALYSIS - {datetime.now().isoformat()}\n")
            f.write(f"Database Path: {db_path}\n")
            f.write("=" * 60 + "\n\n")
        
        if not db_path.exists():
            self.log_error('database', 'Database file not found', str(db_path))
            return False
        
        try:
            # Test basic connection
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            with open(self.log_files['database'], 'a') as f:
                f.write("✅ Database connection successful\n\n")
            
            # Get schema information
            cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='predictions'")
            schema = cursor.fetchone()
            
            if schema:
                with open(self.log_files['database'], 'a') as f:
                    f.write("PREDICTIONS TABLE SCHEMA:\n")
                    f.write("-" * 30 + "\n")
                    f.write(f"{schema[0]}\n\n")
                print("✅ Predictions table found")
            else:
                self.log_error('database', 'Predictions table not found', '')
                return False
            
            # Check indexes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='predictions'")
            indexes = cursor.fetchall()
            
            with open(self.log_files['database'], 'a') as f:
                f.write("INDEXES:\n")
                f.write("-" * 10 + "\n")
                for idx in indexes:
                    f.write(f"  • {idx[0]}\n")
                f.write("\n")
            
            print(f"📋 Found {len(indexes)} indexes on predictions table")
            
            # Test data leakage constraint in detail
            print("\n🔍 Testing data leakage protection...")
            
            # Check if enhanced_features table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='enhanced_features'")
            features_table = cursor.fetchone()
            
            if features_table:
                cursor.execute("SELECT COUNT(*) FROM enhanced_features")
                feature_count = cursor.fetchone()[0]
                print(f"📊 Enhanced features table: {feature_count} records")
                
                with open(self.log_files['database'], 'a') as f:
                    f.write(f"Enhanced features table: {feature_count} records\n")
                
                # Check feature timestamps
                cursor.execute("SELECT symbol, timestamp FROM enhanced_features ORDER BY timestamp DESC LIMIT 5")
                recent_features = cursor.fetchall()
                
                with open(self.log_files['database'], 'a') as f:
                    f.write("RECENT FEATURES:\n")
                    f.write("-" * 20 + "\n")
                    for symbol, timestamp in recent_features:
                        f.write(f"  {symbol}: {timestamp}\n")
                    f.write("\n")
                
                # Now test insertion with detailed error capture
                test_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                test_id = f"TEST_{datetime.now().strftime('%H%M%S')}"
                
                try:
                    cursor.execute('''
                    INSERT INTO predictions (
                        prediction_id, symbol, prediction_timestamp, predicted_action,
                        action_confidence, predicted_direction, predicted_magnitude,
                        model_version, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        test_id,
                        'TEST.AX',
                        test_timestamp,
                        'BUY',
                        0.85,
                        1,
                        0.85,
                        'test_v1.0',
                        datetime.now().isoformat()
                    ))
                    
                    # Clean up test data
                    cursor.execute("DELETE FROM predictions WHERE prediction_id = ?", (test_id,))
                    conn.commit()
                    
                    print("✅ Database insertion test: PASSED")
                    with open(self.log_files['database'], 'a') as f:
                        f.write("✅ Database insertion test: PASSED\n")
                
                except Exception as e:
                    error_msg = str(e)
                    print(f"❌ Database insertion test: FAILED - {error_msg}")
                    
                    with open(self.log_files['database'], 'a') as f:
                        f.write(f"❌ Database insertion test: FAILED - {error_msg}\n")
                        f.write("DETAILED ERROR ANALYSIS:\n")
                        f.write("-" * 25 + "\n")
                        
                        if "Data leakage detected" in error_msg:
                            f.write("This is the data leakage protection trigger.\n")
                            f.write("Checking for future features...\n")
                            
                            # Check for future features
                            future_time = (datetime.now() + timedelta(minutes=30)).strftime('%Y-%m-%d %H:%M:%S')
                            cursor.execute('''
                            SELECT symbol, timestamp FROM enhanced_features 
                            WHERE symbol = 'TEST.AX' 
                            AND datetime(timestamp) > datetime(?)
                            ''', (test_timestamp,))
                            
                            future_features = cursor.fetchall()
                            if future_features:
                                f.write(f"Found {len(future_features)} future features:\n")
                                for symbol, timestamp in future_features:
                                    f.write(f"  {symbol}: {timestamp}\n")
                            else:
                                f.write("No future features found for TEST.AX\n")
                                f.write("This suggests the trigger is overly sensitive.\n")
                        
                        f.write("\n")
                    
                    self.log_error('database', 'Insertion test failed', error_msg, e)
            
            else:
                print("⚠️ Enhanced features table not found")
                with open(self.log_files['database'], 'a') as f:
                    f.write("⚠️ Enhanced features table not found\n")
            
            conn.close()
            return True
            
        except Exception as e:
            self.log_error('database', 'Database analysis failed', str(e), e)
            return False

    def test_commands_with_logging(self):
        """Test system commands with comprehensive logging"""
        print("\n🔍 TESTING SYSTEM COMMANDS WITH DETAILED LOGGING")
        print("=" * 60)
        
        commands = [
            ('status', 'Quick status check', 60),
            ('morning', 'Morning routine (with timeout)', 180),
        ]
        
        for cmd, description, timeout in commands:
            print(f"\n🧪 Testing: {description}")
            
            # Create individual log file for this command
            cmd_log_file = self.logs_dir / f"command_{cmd}_{self.timestamp}.log"
            
            try:
                # Execute with virtual environment
                full_cmd = f"cd {self.project_root} && source venv/bin/activate && python -m app.main {cmd}"
                
                with open(cmd_log_file, 'w') as f:
                    f.write(f"COMMAND EXECUTION LOG - {datetime.now().isoformat()}\n")
                    f.write(f"Command: {full_cmd}\n")
                    f.write(f"Timeout: {timeout} seconds\n")
                    f.write("=" * 60 + "\n\n")
                
                result = subprocess.run(
                    full_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                
                # Log full output
                with open(cmd_log_file, 'a') as f:
                    f.write(f"RETURN CODE: {result.returncode}\n\n")
                    f.write("STDOUT:\n")
                    f.write("-" * 10 + "\n")
                    f.write(result.stdout)
                    f.write("\n\n")
                    f.write("STDERR:\n")
                    f.write("-" * 10 + "\n")
                    f.write(result.stderr)
                    f.write("\n\n")
                
                if result.returncode == 0:
                    print(f"  ✅ {cmd}: Success")
                    
                    # Check for warnings in output
                    output_text = result.stdout + result.stderr
                    warning_patterns = ['WARNING', 'Warning:', 'WARN', 'warning']
                    warnings_found = []
                    
                    for pattern in warning_patterns:
                        if pattern in output_text:
                            warning_lines = [line.strip() for line in output_text.split('\n') if pattern.lower() in line.lower()]
                            warnings_found.extend(warning_lines)
                    
                    if warnings_found:
                        print(f"  ⚠️ Found {len(warnings_found)} warnings")
                        with open(cmd_log_file, 'a') as f:
                            f.write("WARNINGS DETECTED:\n")
                            f.write("-" * 20 + "\n")
                            for warning in warnings_found:
                                f.write(f"  • {warning}\n")
                            f.write("\n")
                        
                        for warning in warnings_found:
                            self.warnings.append({
                                'command': cmd,
                                'warning': warning,
                                'log_file': str(cmd_log_file)
                            })
                
                else:
                    print(f"  ❌ {cmd}: Failed with code {result.returncode}")
                    self.log_error(f'command_{cmd}', f'Command failed with code {result.returncode}', result.stderr)
                
            except subprocess.TimeoutExpired:
                print(f"  ⏱️ {cmd}: Timeout ({timeout}s)")
                with open(cmd_log_file, 'a') as f:
                    f.write(f"COMMAND TIMED OUT after {timeout} seconds\n")
                
                self.log_error(f'command_{cmd}', f'Command timeout', f'Exceeded {timeout} seconds')
                
            except Exception as e:
                print(f"  💥 {cmd}: Exception - {e}")
                self.log_error(f'command_{cmd}', 'Command execution error', str(e), e)

    def test_package_imports_detailed(self):
        """Test package imports with detailed error logging"""
        print("\n🔍 DETAILED PACKAGE IMPORT TESTING")
        print("=" * 50)
        
        import_log = self.logs_dir / f"imports_{self.timestamp}.log"
        
        with open(import_log, 'w') as f:
            f.write(f"PACKAGE IMPORT TESTING - {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")
        
        # Critical packages for ML system
        packages = [
            ('pandas', 'Core data processing'),
            ('numpy', 'Numerical computing'),
            ('scikit-learn', 'Machine learning'),
            ('transformers', 'NLP transformers'),
            ('matplotlib', 'Plotting'),
            ('beautifulsoup4', 'Web scraping'),
            ('feedparser', 'RSS/news parsing'),
            ('yfinance', 'Financial data'),
            ('streamlit', 'Dashboard'),
            ('fastapi', 'Web API'),
            ('sqlite3', 'Database (built-in)'),
        ]
        
        successful_imports = 0
        failed_imports = []
        
        for package, description in packages:
            try:
                if package == 'scikit-learn':
                    import sklearn
                elif package == 'beautifulsoup4':
                    import bs4
                else:
                    __import__(package)
                
                print(f"✅ {package}: Available ({description})")
                successful_imports += 1
                
                with open(import_log, 'a') as f:
                    f.write(f"✅ {package}: AVAILABLE - {description}\n")
                    
            except ImportError as e:
                print(f"❌ {package}: Missing - {e}")
                failed_imports.append((package, str(e)))
                
                with open(import_log, 'a') as f:
                    f.write(f"❌ {package}: MISSING - {e}\n")
                
                self.log_error('imports', f'Missing package: {package}', str(e), e)
        
        with open(import_log, 'a') as f:
            f.write(f"\nSUMMARY:\n")
            f.write(f"Successful: {successful_imports}/{len(packages)}\n")
            f.write(f"Failed: {len(failed_imports)}\n")
        
        print(f"\n📊 Import Summary: {successful_imports}/{len(packages)} successful")
        
        return successful_imports, failed_imports

    def test_remote_system_detailed(self):
        """Test remote system with detailed logging"""
        print("\n🔍 DETAILED REMOTE SYSTEM TESTING")
        print("=" * 50)
        
        remote_log = self.logs_dir / f"remote_{self.timestamp}.log"
        
        with open(remote_log, 'w') as f:
            f.write(f"REMOTE SYSTEM TESTING - {datetime.now().isoformat()}\n")
            f.write("=" * 60 + "\n\n")
        
        try:
            # Test SSH connectivity
            ssh_test = subprocess.run(
                ["ssh", "-o", "ConnectTimeout=10", "root@170.64.199.151", "echo 'SSH connection test'"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if ssh_test.returncode == 0:
                print("✅ SSH connection successful")
                with open(remote_log, 'a') as f:
                    f.write("✅ SSH connection successful\n")
            else:
                print("❌ SSH connection failed")
                with open(remote_log, 'a') as f:
                    f.write(f"❌ SSH connection failed: {ssh_test.stderr}\n")
                return False
            
            # Test remote database
            db_test = subprocess.run([
                "ssh", "root@170.64.199.151",
                "sqlite3 /root/data/trading_predictions.db 'SELECT COUNT(*) FROM predictions; SELECT COUNT(*) FROM enhanced_features;'"
            ], capture_output=True, text=True, timeout=30)
            
            if db_test.returncode == 0:
                lines = db_test.stdout.strip().split('\n')
                pred_count = lines[0] if lines else '0'
                feature_count = lines[1] if len(lines) > 1 else '0'
                
                print(f"✅ Remote database: {pred_count} predictions, {feature_count} features")
                with open(remote_log, 'a') as f:
                    f.write(f"✅ Remote database: {pred_count} predictions, {feature_count} features\n")
            else:
                print("❌ Remote database test failed")
                with open(remote_log, 'a') as f:
                    f.write(f"❌ Remote database test failed: {db_test.stderr}\n")
            
            # Test remote Python environment
            venv_test = subprocess.run([
                "ssh", "root@170.64.199.151",
                "source /root/trading_venv/bin/activate && python -c 'import pandas, numpy, sklearn; print(\"Environment OK\")'"
            ], capture_output=True, text=True, timeout=30)
            
            if venv_test.returncode == 0:
                print("✅ Remote Python environment operational")
                with open(remote_log, 'a') as f:
                    f.write("✅ Remote Python environment operational\n")
            else:
                print("❌ Remote Python environment issues")
                with open(remote_log, 'a') as f:
                    f.write(f"❌ Remote Python environment issues: {venv_test.stderr}\n")
            
            return True
            
        except Exception as e:
            self.log_error('remote', 'Remote system test failed', str(e), e)
            return False

    def generate_comprehensive_report(self):
        """Generate comprehensive analysis report"""
        print("\n📊 GENERATING COMPREHENSIVE REPORT")
        print("=" * 50)
        
        report_file = self.logs_dir / f"comprehensive_report_{self.timestamp}.json"
        summary_file = self.logs_dir / f"analysis_summary_{self.timestamp}.md"
        
        # Create comprehensive report data
        report_data = {
            'analysis_timestamp': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'errors': self.errors,
            'warnings': self.warnings,
            'log_files': {k: str(v) for k, v in self.log_files.items()},
            'analysis_duration': 'completed'
        }
        
        # Save JSON report
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        # Create markdown summary
        summary = f"""# 🎯 COMPREHENSIVE SYSTEM ANALYSIS REPORT

**Analysis Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Project Root:** {self.project_root}

---

## 📊 EXECUTIVE SUMMARY

- **Total Errors:** {len(self.errors)}
- **Total Warnings:** {len(self.warnings)}
- **Log Files Generated:** {len(self.log_files)}

---

## 🚨 ERRORS DETECTED ({len(self.errors)})

"""
        
        for i, error in enumerate(self.errors, 1):
            summary += f"""### Error {i}: {error['component']}
- **Error:** {error['error']}
- **Details:** {error['details']}
- **Timestamp:** {error['timestamp']}

"""
            if error['exception']:
                summary += f"- **Exception:** {error['exception']}\n\n"
        
        summary += f"""---

## ⚠️ WARNINGS DETECTED ({len(self.warnings)})

"""
        
        for i, warning in enumerate(self.warnings, 1):
            if isinstance(warning, dict) and 'warning' in warning:
                summary += f"""### Warning {i}
- **Warning:** {warning['warning']}
- **Command:** {warning.get('command', 'Unknown')}

"""
        
        summary += f"""---

## 📁 LOG FILES GENERATED

"""
        
        for log_type, log_path in self.log_files.items():
            summary += f"- **{log_type.title()} Log:** `{log_path}`\n"
        
        summary += f"""
- **Comprehensive Report:** `{report_file}`

---

## 💡 NEXT STEPS

1. **Review Error Logs:** Check the error-specific log file for detailed error analysis
2. **Database Issues:** Review the database log for constraint and schema issues
3. **Command Issues:** Check individual command logs for execution problems
4. **Import Issues:** Review the imports log for missing package details

---

**Generated:** {datetime.now().isoformat()}
"""
        
        with open(summary_file, 'w') as f:
            f.write(summary)
        
        print(f"📄 Comprehensive report: {report_file}")
        print(f"📋 Summary report: {summary_file}")
        
        return str(summary_file)

    def run_comprehensive_analysis(self):
        """Run complete analysis with detailed logging"""
        print("🚀 COMPREHENSIVE SYSTEM ANALYSIS WITH DETAILED LOGGING")
        print("=" * 70)
        print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Logs Directory: {self.logs_dir}")
        print("=" * 70)
        
        try:
            # Test 1: Package imports
            successful_imports, failed_imports = self.test_package_imports_detailed()
            
            # Test 2: Database analysis
            db_success = self.test_database_comprehensive()
            
            # Test 3: Command testing
            self.test_commands_with_logging()
            
            # Test 4: Remote system
            remote_success = self.test_remote_system_detailed()
            
            # Generate comprehensive report
            summary_file = self.generate_comprehensive_report()
            
            print("\n" + "=" * 70)
            print("🎯 COMPREHENSIVE ANALYSIS COMPLETE")
            print("=" * 70)
            print(f"📊 Total Errors: {len(self.errors)}")
            print(f"⚠️ Total Warnings: {len(self.warnings)}")
            print(f"📁 Logs Location: {self.logs_dir}")
            print(f"📋 Summary Report: {summary_file}")
            
            # Display key findings
            if self.errors:
                print(f"\n🚨 KEY ERRORS TO INVESTIGATE:")
                for error in self.errors[:3]:  # Show top 3
                    print(f"   • [{error['component']}] {error['error']}")
            
            if self.warnings:
                print(f"\n⚠️ WARNINGS TO REVIEW:")
                for warning in self.warnings[:3]:  # Show top 3
                    if isinstance(warning, dict) and 'warning' in warning:
                        print(f"   • {warning['warning']}")
            
            print(f"\n💡 Review the detailed logs in {self.logs_dir} for complete analysis")
            
        except Exception as e:
            self.log_error('analyzer', 'Analysis framework failed', str(e), e)
            print(f"💥 Analysis failed: {e}")
            traceback.print_exc()

def main():
    """Run comprehensive analysis"""
    analyzer = ComprehensiveAnalyzer()
    analyzer.run_comprehensive_analysis()

if __name__ == "__main__":
    main()
