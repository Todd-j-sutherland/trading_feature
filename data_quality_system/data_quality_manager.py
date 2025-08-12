#!/usr/bin/env python3
"""
Comprehensive Data Quality Management System
Integrates all quality detection, analysis, and fixing capabilities
"""

import os
import json
import argparse
from datetime import datetime
import subprocess
import sys

# Add core directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))

class DataQualityManager:
    def __init__(self):
        self.reports_dir = "../data/quality_reports"
        self.fixes_dir = "../data/fix_reports"
        self.ml_monitoring_dir = "../data/ml_monitoring"
        
        # Ensure directories exist
        for dir_path in [self.reports_dir, self.fixes_dir, self.ml_monitoring_dir]:
            os.makedirs(dir_path, exist_ok=True)
    
    def run_quick_analysis(self):
        """Run quick statistical analysis"""
        print("🔍 Running Quick Data Quality Analysis...")
        
        try:
            from core.intelligent_analyzer import IntelligentDataQualityAnalyzer
            analyzer = IntelligentDataQualityAnalyzer()
            report = analyzer.run_comprehensive_analysis()
            return report
        except Exception as e:
            print(f"❌ Quick analysis failed: {e}")
            return None
    
    def run_ml_monitoring(self, train_new=False):
        """Run ML-powered monitoring"""
        print("🤖 Running ML-Powered Quality Monitoring...")
        
        try:
            from core.ml_monitor import MLDataQualityMonitor
            monitor = MLDataQualityMonitor()
            
            if train_new:
                print("🧠 Training new ML models...")
                monitor.train_anomaly_detection_models()
            
            report = monitor.run_continuous_monitoring()
            return report
        except Exception as e:
            print(f"❌ ML monitoring failed: {e}")
            return None
    
    def run_auto_fixes(self, live_mode=False):
        """Run automated fixes"""
        print(f"🔧 Running Auto-Fixes ({'LIVE' if live_mode else 'DRY RUN'})...")
        
        try:
            from core.smart_fixer import SmartDataQualityFixer
            fixer = SmartDataQualityFixer()
            report = fixer.run_intelligent_auto_fix(dry_run=not live_mode)
            return report
        except Exception as e:
            print(f"❌ Auto-fix failed: {e}")
            return None
    
    def generate_executive_summary(self, reports):
        """Generate high-level executive summary"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'system_status': 'unknown',
            'critical_issues': 0,
            'total_anomalies': 0,
            'fixes_applied': 0,
            'data_quality_score': 0,
            'recommendations': [],
            'next_actions': []
        }
        
        # Analyze reports
        if 'quick_analysis' in reports and reports['quick_analysis']:
            qa_report = reports['quick_analysis']
            summary['total_anomalies'] += qa_report['summary']['total_anomalies_detected']
            summary['critical_issues'] += qa_report['summary']['critical_issues']
            summary['data_quality_score'] = qa_report['summary']['data_quality_score']
            
            # Extract recommendations
            for rec in qa_report.get('recommendations', []):
                if rec['priority'] in ['critical', 'high']:
                    summary['recommendations'].append(rec['description'])
        
        if 'ml_monitoring' in reports and reports['ml_monitoring']:
            ml_report = reports['ml_monitoring']
            summary['total_anomalies'] += ml_report['summary']['total_anomalies']
            summary['critical_issues'] += ml_report['summary']['critical_alerts']
            
            # Update score with ML insights
            ml_score = ml_report['summary']['data_quality_score']
            summary['data_quality_score'] = (summary['data_quality_score'] + ml_score) / 2
        
        if 'auto_fixes' in reports and reports['auto_fixes']:
            fix_report = reports['auto_fixes']
            summary['fixes_applied'] = fix_report['total_fixes']
        
        # Determine system status
        if summary['critical_issues'] > 0:
            summary['system_status'] = 'critical'
        elif summary['total_anomalies'] > 5:
            summary['system_status'] = 'warning'
        elif summary['data_quality_score'] > 80:
            summary['system_status'] = 'excellent'
        else:
            summary['system_status'] = 'good'
        
        # Generate next actions
        if summary['critical_issues'] > 0:
            summary['next_actions'].append('Address critical data quality issues immediately')
        if summary['fixes_applied'] > 0:
            summary['next_actions'].append('Verify applied fixes and rerun analysis')
        if summary['data_quality_score'] < 70:
            summary['next_actions'].append('Investigate data collection and processing pipeline')
        
        summary['next_actions'].append('Schedule regular automated quality monitoring')
        
        return summary
    
    def create_monitoring_dashboard_data(self, reports):
        """Create data structure for dashboard visualization"""
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'status_overview': {
                'system_health': 'unknown',
                'data_quality_score': 0,
                'critical_alerts': 0,
                'total_records': 0
            },
            'anomaly_breakdown': {},
            'trending_metrics': {},
            'recommendations': []
        }
        
        # Populate from reports
        if 'quick_analysis' in reports and reports['quick_analysis']:
            qa = reports['quick_analysis']
            dashboard_data['status_overview']['total_records'] = qa['summary']['total_records_analyzed']
            dashboard_data['status_overview']['data_quality_score'] = qa['summary']['data_quality_score']
            
            # Categorize anomalies
            for anomaly_type, anomalies in qa['anomalies'].items():
                for anomaly in anomalies:
                    severity = anomaly.get('severity', 'medium')
                    if severity not in dashboard_data['anomaly_breakdown']:
                        dashboard_data['anomaly_breakdown'][severity] = 0
                    dashboard_data['anomaly_breakdown'][severity] += 1
        
        # Add ML insights
        if 'ml_monitoring' in reports and reports['ml_monitoring']:
            ml = reports['ml_monitoring']
            dashboard_data['trending_metrics']['ml_quality_score'] = ml['summary']['data_quality_score']
            dashboard_data['trending_metrics']['ml_anomalies'] = ml['summary']['total_anomalies']
        
        return dashboard_data
    
    def run_comprehensive_analysis(self, mode='standard'):
        """Run comprehensive data quality analysis"""
        print("\n" + "="*60)
        print(" 🎯 COMPREHENSIVE DATA QUALITY ANALYSIS")
        print("="*60)
        
        reports = {}
        
        # 1. Quick Statistical Analysis
        reports['quick_analysis'] = self.run_quick_analysis()
        
        # 2. ML-Powered Monitoring
        train_ml = (mode == 'full')
        reports['ml_monitoring'] = self.run_ml_monitoring(train_new=train_ml)
        
        # 3. Generate Fixes (dry run by default)
        auto_fix = (mode == 'fix')
        reports['auto_fixes'] = self.run_auto_fixes(live_mode=auto_fix)
        
        # 4. Create Executive Summary
        executive_summary = self.generate_executive_summary(reports)
        
        # 5. Create Dashboard Data
        dashboard_data = self.create_monitoring_dashboard_data(reports)
        
        # Save comprehensive report
        comprehensive_report = {
            'timestamp': datetime.now().isoformat(),
            'mode': mode,
            'executive_summary': executive_summary,
            'dashboard_data': dashboard_data,
            'detailed_reports': reports
        }
        
        report_file = f"{self.reports_dir}/comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(comprehensive_report, f, indent=2)
        
        # Print Executive Summary
        self.print_executive_summary(executive_summary)
        
        print(f"\n📁 Comprehensive report saved: {report_file}")
        
        return comprehensive_report
    
    def print_executive_summary(self, summary):
        """Print formatted executive summary"""
        print(f"\n📊 EXECUTIVE SUMMARY")
        print(f"   System Status: {summary['system_status'].upper()}")
        print(f"   Data Quality Score: {summary['data_quality_score']:.1f}/100")
        print(f"   Critical Issues: {summary['critical_issues']}")
        print(f"   Total Anomalies: {summary['total_anomalies']}")
        print(f"   Fixes Applied: {summary['fixes_applied']}")
        
        if summary['recommendations']:
            print(f"\n💡 TOP RECOMMENDATIONS:")
            for i, rec in enumerate(summary['recommendations'][:3], 1):
                print(f"   {i}. {rec}")
        
        if summary['next_actions']:
            print(f"\n📋 NEXT ACTIONS:")
            for action in summary['next_actions']:
                print(f"   • {action}")
    
    def setup_automated_monitoring(self):
        """Set up automated monitoring scripts"""
        print("⚙️ Setting up automated monitoring...")
        
        # Create daily monitoring script
        daily_script = """#!/bin/bash
# Daily Data Quality Monitor
# Run this script daily to monitor data quality

cd "$(dirname "$0")"

echo "🔍 Running Daily Data Quality Check..."
echo "Date: $(date)"

# Run comprehensive analysis
python3 data_quality_manager.py --mode standard

# Check if critical issues found
if [ -f "../data/quality_reports/latest_critical_issues.txt" ]; then
    echo "🚨 CRITICAL ISSUES DETECTED - Check reports immediately!"
    # Could send email alert here
fi

echo "✅ Daily quality check complete"
"""
        
        with open('automation/daily_quality_monitor.sh', 'w') as f:
            f.write(daily_script)
        
        os.chmod('automation/daily_quality_monitor.sh', 0o755)
        
        # Create weekly deep analysis script
        weekly_script = """#!/bin/bash
# Weekly Deep Data Quality Analysis
# Run this script weekly for comprehensive analysis with ML training

cd "$(dirname "$0")"

echo "🧠 Running Weekly Deep Analysis..."
echo "Date: $(date)"

# Run full analysis with ML training
python3 data_quality_manager.py --mode full

echo "✅ Weekly deep analysis complete"
"""
        
        with open('automation/weekly_deep_analysis.sh', 'w') as f:
            f.write(weekly_script)
        
        os.chmod('automation/weekly_deep_analysis.sh', 0o755)
        
        print("✅ Created automated monitoring scripts:")
        print("   • automation/daily_quality_monitor.sh - Run daily")
        print("   • automation/weekly_deep_analysis.sh - Run weekly")

def main():
    parser = argparse.ArgumentParser(description='Comprehensive Data Quality Management')
    parser.add_argument('--mode', choices=['standard', 'full', 'fix'], default='standard',
                      help='Analysis mode: standard (quick+ML), full (with ML training), fix (apply fixes)')
    parser.add_argument('--setup', action='store_true', help='Set up automated monitoring')
    
    args = parser.parse_args()
    
    manager = DataQualityManager()
    
    if args.setup:
        manager.setup_automated_monitoring()
        return
    
    # Run analysis
    report = manager.run_comprehensive_analysis(mode=args.mode)
    
    # Provide guidance based on results
    executive = report['executive_summary']
    
    if executive['system_status'] == 'critical':
        print("\n🚨 CRITICAL ISSUES DETECTED!")
        print("   Recommended: Run with --mode fix to apply automatic fixes")
    elif executive['system_status'] == 'warning':
        print("\n⚠️  Data quality issues detected")
        print("   Recommended: Review detailed reports and consider fixes")
    else:
        print("\n✅ System is operating normally")
        print("   Recommended: Continue regular monitoring")

if __name__ == "__main__":
    main()
