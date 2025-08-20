#!/usr/bin/env python3
"""
Targeted System Issue Analysis
Based on deep analysis findings, focus on real issues and provide actionable recommendations
"""

import sqlite3
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def analyze_data_collection_issues():
    """Analyze specific data collection and consistency issues"""
    print("🔍 DATA COLLECTION & CONSISTENCY ANALYSIS")
    print("=" * 50)
    
    issues = []
    recommendations = []
    
    # Check database state
    local_db = Path("data/trading_predictions.db")
    if local_db.exists():
        try:
            conn = sqlite3.connect(str(local_db))
            cursor = conn.cursor()
            
            # Check local data
            cursor.execute("SELECT COUNT(*) FROM predictions")
            local_predictions = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM enhanced_features")
            local_features = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM enhanced_outcomes") 
            local_outcomes = cursor.fetchone()[0]
            
            print(f"📊 Local Database Status:")
            print(f"   Predictions: {local_predictions}")
            print(f"   Enhanced Features: {local_features}")
            print(f"   Enhanced Outcomes: {local_outcomes}")
            
            # Check data freshness
            try:
                cursor.execute("SELECT MAX(created_at) FROM predictions")
                last_prediction = cursor.fetchone()[0]
                if last_prediction:
                    print(f"   Last Prediction: {last_prediction}")
                    last_date = datetime.fromisoformat(last_prediction.replace('Z', '+00:00'))
                    days_old = (datetime.now() - last_date.replace(tzinfo=None)).days
                    if days_old > 1:
                        issues.append(f"⚠️  Local predictions are {days_old} days old")
                        recommendations.append("🔄 Run morning routine to generate fresh predictions")
                else:
                    issues.append("❌ No prediction timestamps found")
            except Exception as e:
                issues.append(f"❌ Error checking prediction freshness: {e}")
            
            conn.close()
            
        except Exception as e:
            issues.append(f"❌ Database connection error: {e}")
    else:
        issues.append("❌ Local database not found")
    
    # Check remote vs local sync
    try:
        print(f"\n🌐 Remote Database Comparison:")
        result = subprocess.run([
            'ssh', 'root@170.64.199.151',
            'cd /root/test && sqlite3 data/trading_predictions.db "SELECT COUNT(*) FROM predictions; SELECT COUNT(*) FROM enhanced_outcomes;"'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            remote_predictions = int(lines[0]) if lines and lines[0].isdigit() else 0
            remote_outcomes = int(lines[1]) if len(lines) > 1 and lines[1].isdigit() else 0
            
            print(f"   Remote Predictions: {remote_predictions}")
            print(f"   Remote Outcomes: {remote_outcomes}")
            
            if local_predictions != remote_predictions:
                issues.append(f"⚠️  Data sync issue: Local({local_predictions}) vs Remote({remote_predictions}) predictions")
                recommendations.append("🔄 Sync databases or run data collection")
                
        else:
            issues.append("❌ Cannot connect to remote database")
            recommendations.append("🔧 Check SSH access and remote system status")
            
    except Exception as e:
        issues.append(f"❌ Remote check failed: {e}")
    
    return issues, recommendations

def analyze_missing_dependencies():
    """Analyze missing dependencies and their impact"""
    print("\n🔍 DEPENDENCY ANALYSIS")
    print("=" * 50)
    
    issues = []
    recommendations = []
    
    # Critical missing packages
    missing_packages = {
        'feedparser': 'Required for RSS/news feed collection',
        'beautifulsoup4': 'Required for web scraping and HTML parsing',
        'lxml': 'Required for XML/HTML parsing (beautifulsoup4 backend)',
        'matplotlib': 'Required for chart generation and visualization'
    }
    
    print("📦 Package Status Check:")
    for package, description in missing_packages.items():
        try:
            __import__(package)
            print(f"   ✅ {package}: Available")
        except ImportError:
            print(f"   ❌ {package}: Missing")
            issues.append(f"❌ Missing {package}: {description}")
            recommendations.append(f"📦 Install {package} for full functionality")
    
    # Check if system can run in degraded mode
    core_available = True
    try:
        import sqlite3, requests, pandas, numpy
        print(f"   ✅ Core packages (sqlite3, requests, pandas, numpy): Available")
    except ImportError as e:
        issues.append(f"❌ Critical core package missing: {e}")
        core_available = False
    
    if core_available and issues:
        recommendations.append("💡 System can run in basic mode without missing packages")
        recommendations.append("🔧 For full ML functionality, create virtual environment and install all packages")
    
    return issues, recommendations

def analyze_system_warnings():
    """Analyze system health warnings from recent runs"""
    print("\n🔍 SYSTEM HEALTH ANALYSIS")
    print("=" * 50)
    
    issues = []
    recommendations = []
    
    # Check log files for patterns
    log_dir = Path("logs")
    if log_dir.exists():
        log_files = list(log_dir.glob("*.log"))
        print(f"📁 Found {len(log_files)} log files")
        
        # Check recent logs for warning patterns
        warning_patterns = [
            'Enhanced ML components not available',
            'Enhanced analysis not available',
            'Temporal guard not found',
            'System health: warning'
        ]
        
        warnings_found = {}
        for log_file in sorted(log_files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                    for pattern in warning_patterns:
                        if pattern in content:
                            if pattern not in warnings_found:
                                warnings_found[pattern] = []
                            warnings_found[pattern].append(log_file.name)
            except Exception:
                pass
        
        if warnings_found:
            print(f"⚠️  Recurring warning patterns found:")
            for pattern, files in warnings_found.items():
                print(f"   • {pattern} (in {len(files)} recent logs)")
                issues.append(f"⚠️  Recurring warning: {pattern}")
                
                # Add specific recommendations based on warning type
                if 'Enhanced ML' in pattern:
                    recommendations.append("🧠 Install missing ML dependencies (feedparser, etc.)")
                elif 'Temporal guard' in pattern:
                    recommendations.append("🛡️  Copy temporal protection files to project root")
                elif 'System health' in pattern:
                    recommendations.append("🏥 Investigate system health check failures")
        else:
            print(f"✅ No recurring warning patterns found")
    else:
        issues.append("❌ Logs directory not found")
        recommendations.append("📁 Create logs directory for better monitoring")
    
    return issues, recommendations

def check_configuration_issues():
    """Check for configuration and setup issues"""
    print("\n🔍 CONFIGURATION ANALYSIS") 
    print("=" * 50)
    
    issues = []
    recommendations = []
    
    # Check critical files
    critical_files = {
        'app/config/settings.py': 'Main configuration',
        'app/services/daily_manager.py': 'Core system manager',
        'enhanced_ml_system/__init__.py': 'ML system initialization',
        'data/trading_predictions.db': 'Main database'
    }
    
    print("📁 Critical Files Check:")
    for file_path, description in critical_files.items():
        full_path = Path(file_path)
        if full_path.exists():
            print(f"   ✅ {file_path}: {description}")
        else:
            print(f"   ❌ {file_path}: Missing")
            issues.append(f"❌ Missing critical file: {file_path}")
            recommendations.append(f"🔧 Create or restore {file_path}")
    
    # Check Python path issues
    try:
        sys.path.insert(0, str(Path.cwd()))
        from app.main import main
        from app.services.daily_manager import TradingSystemManager
        print(f"   ✅ Python imports: Working")
    except ImportError as e:
        issues.append(f"❌ Import error: {e}")
        recommendations.append("🐍 Check Python path and module structure")
    
    return issues, recommendations

def main():
    """Run targeted analysis of real issues"""
    print("🎯 TARGETED SYSTEM ISSUE ANALYSIS")
    print("🔍 Focus on Real Issues & Actionable Solutions")
    print("=" * 60)
    print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    all_issues = []
    all_recommendations = []
    
    # Run targeted analyses
    analyses = [
        analyze_data_collection_issues,
        analyze_missing_dependencies, 
        analyze_system_warnings,
        check_configuration_issues
    ]
    
    for analysis_func in analyses:
        try:
            issues, recommendations = analysis_func()
            all_issues.extend(issues)
            all_recommendations.extend(recommendations)
        except Exception as e:
            all_issues.append(f"❌ Analysis error in {analysis_func.__name__}: {e}")
    
    # Generate executive summary
    print("\n" + "=" * 60)
    print("🎯 EXECUTIVE SUMMARY")
    print("=" * 60)
    
    print(f"📊 Issues Found: {len(all_issues)}")
    print(f"💡 Recommendations: {len(set(all_recommendations))}")
    
    if all_issues:
        print(f"\n🚨 KEY ISSUES:")
        for issue in all_issues:
            print(f"   {issue}")
    
    if all_recommendations:
        print(f"\n💡 PRIORITY ACTIONS:")
        unique_recommendations = list(set(all_recommendations))
        for i, rec in enumerate(unique_recommendations, 1):
            print(f"   {i}. {rec}")
    
    # System health assessment
    critical_issues = len([i for i in all_issues if '❌' in i])
    warning_issues = len([i for i in all_issues if '⚠️' in i])
    
    if critical_issues == 0 and warning_issues == 0:
        health_status = "🟢 HEALTHY"
    elif critical_issues == 0:
        health_status = "🟡 WARNINGS"
    else:
        health_status = "🔴 CRITICAL"
    
    print(f"\n🏥 OVERALL SYSTEM HEALTH: {health_status}")
    print(f"   Critical Issues: {critical_issues}")
    print(f"   Warning Issues: {warning_issues}")
    
    print(f"\n✅ TARGETED ANALYSIS COMPLETE")
    print(f"💡 Focus on the priority actions above for maximum impact")

if __name__ == "__main__":
    main()
