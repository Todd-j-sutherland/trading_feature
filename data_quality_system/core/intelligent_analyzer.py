#!/usr/bin/env python3
"""
Intelligent Data Quality Analyzer
Automatically detects and flags data quality issues using statistical analysis and ML techniques
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import yfinance as yf
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from scipy import stats
import warnings
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

warnings.filterwarnings('ignore')

class IntelligentDataQualityAnalyzer:
    def __init__(self, db_path=None):
        if db_path is None:
            # Try to find the database automatically
            possible_paths = [
                "../data/trading_unified.db",
                "../../data/trading_unified.db",
                "/root/test/data/trading_unified.db",
                "data/trading_unified.db"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    self.db_path = path
                    break
            else:
                self.db_path = "../data/trading_unified.db"  # Default fallback
        else:
            self.db_path = db_path
        self.anomalies = {}
        self.recommendations = []
        
    def load_data(self):
        """Load data from database"""
        conn = sqlite3.connect(self.db_path)
        
        # Load enhanced outcomes
        self.outcomes_df = pd.read_sql_query("""
            SELECT * FROM enhanced_outcomes 
            WHERE created_at >= date('now', '-30 days')
            ORDER BY created_at DESC
        """, conn)
        
        # Load technical analysis if available
        try:
            self.ta_df = pd.read_sql_query("""
                SELECT * FROM technical_analysis 
                WHERE created_at >= date('now', '-30 days')
                ORDER BY created_at DESC
            """, conn)
        except:
            self.ta_df = pd.DataFrame()
            
        conn.close()
        print(f"📊 Loaded {len(self.outcomes_df)} outcome records")
        
    def detect_price_anomalies(self):
        """Detect suspicious price data using statistical methods"""
        anomalies = []
        
        if self.outcomes_df.empty:
            return anomalies
            
        # 1. Detect round number bias (dummy data often uses round numbers)
        round_prices = self.outcomes_df[
            (self.outcomes_df['entry_price'] % 1 == 0) | 
            (self.outcomes_df['entry_price'].isin([100.0, 50.0, 10.0, 1.0]))
        ]
        
        if len(round_prices) > len(self.outcomes_df) * 0.1:  # More than 10% round numbers
            anomalies.append({
                'type': 'round_number_bias',
                'severity': 'high',
                'records': len(round_prices),
                'description': f'{len(round_prices)} records have suspiciously round entry prices',
                'affected_records': round_prices['id'].tolist()
            })
            
        # 2. Detect outlier prices using Isolation Forest
        if len(self.outcomes_df) > 10:
            price_features = self.outcomes_df[['entry_price', 'exit_price_1d']].dropna()
            if len(price_features) > 5:
                iso_forest = IsolationForest(contamination=0.1, random_state=42)
                outliers = iso_forest.fit_predict(price_features)
                outlier_indices = price_features.index[outliers == -1]
                
                if len(outlier_indices) > 0:
                    anomalies.append({
                        'type': 'price_outliers',
                        'severity': 'medium',
                        'records': len(outlier_indices),
                        'description': f'{len(outlier_indices)} records have unusual price patterns',
                        'affected_records': self.outcomes_df.loc[outlier_indices, 'id'].tolist()
                    })
        
        # 3. Detect impossible returns (>1000% or <-100%)
        extreme_returns = self.outcomes_df[
            (abs(self.outcomes_df['return_pct']) > 100) | 
            (self.outcomes_df['return_pct'] < -99)
        ]
        
        if len(extreme_returns) > 0:
            anomalies.append({
                'type': 'extreme_returns',
                'severity': 'critical',
                'records': len(extreme_returns),
                'description': f'{len(extreme_returns)} records have impossible return percentages',
                'affected_records': extreme_returns['id'].tolist()
            })
            
        return anomalies
    
    def detect_missing_data_patterns(self):
        """Detect patterns in missing data that suggest systematic issues"""
        anomalies = []
        
        # Check for systematic missing exit prices
        missing_exits = self.outcomes_df[self.outcomes_df['exit_price_1d'].isna()]
        if len(missing_exits) > len(self.outcomes_df) * 0.05:  # More than 5% missing
            anomalies.append({
                'type': 'missing_exit_prices',
                'severity': 'high',
                'records': len(missing_exits),
                'description': f'{len(missing_exits)} records missing exit prices',
                'affected_records': missing_exits['id'].tolist()
            })
            
        # Check for missing returns
        missing_returns = self.outcomes_df[self.outcomes_df['return_pct'].isna()]
        if len(missing_returns) > 0:
            anomalies.append({
                'type': 'missing_returns',
                'severity': 'critical',
                'records': len(missing_returns),
                'description': f'{len(missing_returns)} records missing return calculations',
                'affected_records': missing_returns['id'].tolist()
            })
            
        return anomalies
    
    def detect_prediction_bias_patterns(self):
        """Detect systematic bias in ML predictions"""
        anomalies = []
        
        if len(self.outcomes_df) < 20:
            return anomalies
            
        # Check action distribution
        action_dist = self.outcomes_df['optimal_action'].value_counts(normalize=True)
        
        # Flag if any action is >80% or <5% of total
        for action, percentage in action_dist.items():
            if percentage > 0.8:
                anomalies.append({
                    'type': 'action_bias_high',
                    'severity': 'high',
                    'records': int(percentage * len(self.outcomes_df)),
                    'description': f'{action} predictions are {percentage:.1%} of all trades (possible overfit)',
                    'action': action
                })
            elif percentage < 0.05 and len(self.outcomes_df) > 100:
                anomalies.append({
                    'type': 'action_bias_low',
                    'severity': 'medium', 
                    'records': int(percentage * len(self.outcomes_df)),
                    'description': f'{action} predictions are only {percentage:.1%} of all trades (possible underfit)',
                    'action': action
                })
                
        # Check confidence score patterns
        if 'confidence_score' in self.outcomes_df.columns:
            conf_stats = self.outcomes_df['confidence_score'].describe()
            if conf_stats['std'] < 0.1:  # Very low variance in confidence
                anomalies.append({
                    'type': 'confidence_low_variance',
                    'severity': 'medium',
                    'description': f'Confidence scores have very low variance (std: {conf_stats["std"]:.3f})',
                    'stats': conf_stats.to_dict()
                })
        
        # Analyze HOLD positions specifically for data quality issues
        hold_anomalies = self.analyze_hold_positions()
        anomalies.extend(hold_anomalies)
                
        return anomalies
    
    def analyze_hold_positions(self):
        """Deep analysis of HOLD positions to detect data quality issues"""
        anomalies = []
        
        # Filter HOLD positions
        hold_positions = self.outcomes_df[self.outcomes_df['optimal_action'] == 'HOLD'].copy()
        
        if len(hold_positions) == 0:
            return anomalies
        
        print(f"🔍 Analyzing {len(hold_positions)} HOLD positions for data quality issues...")
        
        # 1. Check for suspiciously identical HOLD returns
        if 'return_pct' in hold_positions.columns:
            return_counts = hold_positions['return_pct'].value_counts()
            # If many HOLD positions have exactly the same return, it's suspicious
            max_identical_returns = return_counts.max()
            if max_identical_returns > len(hold_positions) * 0.1:  # More than 10% identical
                most_common_return = return_counts.index[0]
                anomalies.append({
                    'type': 'hold_identical_returns',
                    'severity': 'high',
                    'records': max_identical_returns,
                    'description': f'{max_identical_returns} HOLD positions have identical return of {most_common_return:.3f}%',
                    'details': {
                        'return_value': most_common_return,
                        'frequency': max_identical_returns,
                        'percentage_of_holds': (max_identical_returns / len(hold_positions)) * 100
                    },
                    'affected_records': hold_positions[hold_positions['return_pct'] == most_common_return]['id'].tolist()
                })
        
        # 2. Check for HOLD positions with zero or minimal price movement
        if 'entry_price' in hold_positions.columns and 'exit_price_1d' in hold_positions.columns:
            price_data = hold_positions[['entry_price', 'exit_price_1d']].dropna()
            if len(price_data) > 0:
                price_data['price_change_pct'] = ((price_data['exit_price_1d'] - price_data['entry_price']) / price_data['entry_price']) * 100
                
                # Find HOLD positions with almost no price movement (< 0.1%)
                minimal_movement = price_data[abs(price_data['price_change_pct']) < 0.1]
                if len(minimal_movement) > len(hold_positions) * 0.3:  # More than 30% with minimal movement
                    anomalies.append({
                        'type': 'hold_minimal_movement',
                        'severity': 'medium',
                        'records': len(minimal_movement),
                        'description': f'{len(minimal_movement)} HOLD positions have minimal price movement (<0.1%)',
                        'details': {
                            'avg_movement': minimal_movement['price_change_pct'].mean(),
                            'percentage_of_holds': (len(minimal_movement) / len(hold_positions)) * 100
                        },
                        'affected_records': hold_positions.loc[minimal_movement.index, 'id'].tolist()
                    })
        
        # 3. Check for HOLD confidence score clustering
        if 'confidence_score' in hold_positions.columns:
            hold_conf = hold_positions['confidence_score'].dropna()
            if len(hold_conf) > 10:
                # Check if HOLD confidence scores are clustered around specific values
                conf_rounded = np.round(hold_conf, 2)
                conf_counts = conf_rounded.value_counts()
                max_conf_cluster = conf_counts.max()
                
                if max_conf_cluster > len(hold_conf) * 0.2:  # More than 20% with same confidence
                    most_common_conf = conf_counts.index[0]
                    anomalies.append({
                        'type': 'hold_confidence_clustering',
                        'severity': 'medium',
                        'records': max_conf_cluster,
                        'description': f'{max_conf_cluster} HOLD positions clustered around confidence {most_common_conf}',
                        'details': {
                            'confidence_value': most_common_conf,
                            'frequency': max_conf_cluster,
                            'percentage_of_holds': (max_conf_cluster / len(hold_conf)) * 100,
                            'confidence_variance': hold_conf.var()
                        }
                    })
        
        # 4. Check for HOLD positions dominating specific symbols
        if 'symbol' in hold_positions.columns:
            symbol_hold_counts = hold_positions['symbol'].value_counts()
            total_symbol_counts = self.outcomes_df['symbol'].value_counts()
            
            # Find symbols where HOLD is >90% of all actions
            hold_dominated_symbols = []
            for symbol in symbol_hold_counts.index:
                hold_pct = (symbol_hold_counts[symbol] / total_symbol_counts[symbol]) * 100
                if hold_pct > 90 and total_symbol_counts[symbol] >= 5:  # At least 5 trades
                    hold_dominated_symbols.append({
                        'symbol': symbol,
                        'hold_percentage': hold_pct,
                        'total_trades': total_symbol_counts[symbol],
                        'hold_trades': symbol_hold_counts[symbol]
                    })
            
            if len(hold_dominated_symbols) > 0:
                anomalies.append({
                    'type': 'hold_symbol_domination',
                    'severity': 'medium',
                    'records': len(hold_dominated_symbols),
                    'description': f'{len(hold_dominated_symbols)} symbols are >90% HOLD predictions',
                    'details': {
                        'dominated_symbols': hold_dominated_symbols,
                        'avg_hold_percentage': np.mean([s['hold_percentage'] for s in hold_dominated_symbols])
                    }
                })
        
        # 5. Check for HOLD positions with suspiciously perfect market timing
        if 'return_pct' in hold_positions.columns:
            hold_returns = hold_positions['return_pct'].dropna()
            if len(hold_returns) > 10:
                # Check if HOLD positions consistently avoid losses
                positive_holds = (hold_returns > 0).sum()
                hold_win_rate = positive_holds / len(hold_returns)
                
                # Also check if HOLD positions have suspiciously high returns for "do nothing" strategy
                avg_hold_return = hold_returns.mean()
                
                if hold_win_rate > 0.8:  # More than 80% positive HOLD returns
                    anomalies.append({
                        'type': 'hold_unrealistic_performance',
                        'severity': 'high',
                        'records': len(hold_returns),
                        'description': f'HOLD positions show unrealistic {hold_win_rate:.1%} win rate',
                        'details': {
                            'win_rate': hold_win_rate,
                            'avg_return': avg_hold_return,
                            'positive_positions': positive_holds,
                            'total_positions': len(hold_returns)
                        }
                    })
        
        # 6. Check for temporal clustering of HOLD decisions
        if 'created_at' in hold_positions.columns:
            hold_positions['date'] = pd.to_datetime(hold_positions['created_at']).dt.date
            daily_holds = hold_positions['date'].value_counts()
            
            # Check if all decisions on certain days are HOLD
            daily_totals = self.outcomes_df.copy()
            daily_totals['date'] = pd.to_datetime(daily_totals['created_at']).dt.date
            daily_total_counts = daily_totals['date'].value_counts()
            
            all_hold_days = []
            for date in daily_holds.index:
                if date in daily_total_counts.index:
                    hold_pct = (daily_holds[date] / daily_total_counts[date]) * 100
                    if hold_pct == 100 and daily_total_counts[date] >= 3:  # All decisions were HOLD
                        all_hold_days.append({
                            'date': str(date),
                            'total_trades': daily_total_counts[date]
                        })
            
            if len(all_hold_days) > 0:
                anomalies.append({
                    'type': 'hold_temporal_clustering',
                    'severity': 'medium',
                    'records': len(all_hold_days),
                    'description': f'{len(all_hold_days)} days had 100% HOLD decisions',
                    'details': {
                        'all_hold_days': all_hold_days,
                        'total_affected_trades': sum([d['total_trades'] for d in all_hold_days])
                    }
                })
        
        return anomalies
    
    def validate_with_market_data(self, sample_size=10):
        """Validate a sample of data against real market data"""
        anomalies = []
        
        if self.outcomes_df.empty:
            return anomalies
            
        # Sample recent records
        recent_data = self.outcomes_df.head(min(sample_size, len(self.outcomes_df)))
        validation_issues = []
        
        for _, row in recent_data.iterrows():
            try:
                symbol = row['symbol']
                date = pd.to_datetime(row['created_at']).date()
                
                # Get market data for validation
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=date - timedelta(days=5), end=date + timedelta(days=5))
                
                if not hist.empty:
                    market_prices = hist['Close'].values
                    entry_price = row['entry_price']
                    
                    # Check if entry price is reasonable (within 20% of market range)
                    price_range = (market_prices.min() * 0.8, market_prices.max() * 1.2)
                    
                    if not (price_range[0] <= entry_price <= price_range[1]):
                        validation_issues.append({
                            'id': row['id'],
                            'symbol': symbol,
                            'entry_price': entry_price,
                            'market_range': price_range,
                            'issue': 'entry_price_out_of_range'
                        })
                        
            except Exception as e:
                continue
                
        if validation_issues:
            anomalies.append({
                'type': 'market_validation_failed',
                'severity': 'high',
                'records': len(validation_issues),
                'description': f'{len(validation_issues)} records failed market data validation',
                'details': validation_issues
            })
            
        return anomalies
    
    def generate_smart_recommendations(self):
        """Generate intelligent recommendations based on detected anomalies"""
        recommendations = []
        
        for anomaly_type, anomalies in self.anomalies.items():
            for anomaly in anomalies:
                if anomaly['type'] == 'round_number_bias':
                    recommendations.append({
                        'priority': 'high',
                        'action': 'investigate_data_source',
                        'description': 'Review data collection process - round numbers suggest dummy/placeholder data',
                        'automated_fix': 'Run price validation against Yahoo Finance API',
                        'code': 'python3 ../fix_entry_prices_with_yahoo.py'
                    })
                    
                elif anomaly['type'] == 'missing_exit_prices':
                    recommendations.append({
                        'priority': 'high',
                        'action': 'backfill_missing_data',
                        'description': 'Backfill missing exit prices using historical market data',
                        'automated_fix': 'Run exit price backfill script',
                        'code': 'python3 ../fix_exit_prices_with_yahoo.py'
                    })
                    
                elif anomaly['type'] == 'action_bias_high':
                    recommendations.append({
                        'priority': 'medium',
                        'action': 'retrain_model',
                        'description': f'Model showing {anomaly["action"]} bias - consider rebalancing training data',
                        'automated_fix': 'Retrain with balanced sampling',
                        'code': 'python3 ../enhanced_training_pipeline.py --rebalance'
                    })
                    
                elif anomaly['type'] == 'extreme_returns':
                    recommendations.append({
                        'priority': 'critical',
                        'action': 'fix_calculation_logic',
                        'description': 'Return calculations appear incorrect - review price data and formulas',
                        'automated_fix': 'Recalculate returns with validated prices',
                        'code': 'python3 automation/recalculate_returns.py'
                    })
                    
                elif anomaly['type'] == 'hold_identical_returns':
                    recommendations.append({
                        'priority': 'high',
                        'action': 'investigate_hold_calculations',
                        'description': 'Many HOLD positions have identical returns - investigate calculation logic',
                        'automated_fix': 'Review HOLD return calculation and data sources',
                        'code': 'python3 automation/analyze_hold_returns.py'
                    })
                    
                elif anomaly['type'] == 'hold_unrealistic_performance':
                    recommendations.append({
                        'priority': 'high',
                        'action': 'validate_hold_strategy',
                        'description': 'HOLD positions show unrealistic performance - validate against market data',
                        'automated_fix': 'Cross-check HOLD returns with market benchmarks',
                        'code': 'python3 automation/validate_hold_performance.py'
                    })
                    
                elif anomaly['type'] == 'hold_temporal_clustering':
                    recommendations.append({
                        'priority': 'medium',
                        'action': 'review_model_inputs',
                        'description': 'Model defaulting to HOLD on specific days - check input data quality',
                        'automated_fix': 'Analyze feature data for days with 100% HOLD decisions',
                        'code': 'python3 automation/analyze_hold_clustering.py'
                    })
                    
                elif anomaly['type'] == 'hold_symbol_domination':
                    recommendations.append({
                        'priority': 'medium',
                        'action': 'check_symbol_features',
                        'description': 'Some symbols always predicted as HOLD - review symbol-specific features',
                        'automated_fix': 'Analyze feature quality for HOLD-dominated symbols',
                        'code': 'python3 automation/analyze_symbol_bias.py'
                    })
        
        return recommendations
    
    def run_comprehensive_analysis(self):
        """Run all quality checks and generate report"""
        print("🔍 Starting Intelligent Data Quality Analysis...")
        
        # Load data
        self.load_data()
        
        # Run all detection methods
        self.anomalies['price'] = self.detect_price_anomalies()
        self.anomalies['missing'] = self.detect_missing_data_patterns()
        self.anomalies['bias'] = self.detect_prediction_bias_patterns()
        self.anomalies['market'] = self.validate_with_market_data()
        
        # Generate recommendations
        self.recommendations = self.generate_smart_recommendations()
        
        # Create report
        return self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive quality report"""
        total_anomalies = sum(len(anomalies) for anomalies in self.anomalies.values())
        critical_issues = sum(1 for anomalies in self.anomalies.values() 
                            for anomaly in anomalies if anomaly['severity'] == 'critical')
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_records_analyzed': len(self.outcomes_df),
                'total_anomalies_detected': total_anomalies,
                'critical_issues': critical_issues,
                'data_quality_score': max(0, 100 - (total_anomalies * 5) - (critical_issues * 15))
            },
            'anomalies': self.anomalies,
            'recommendations': self.recommendations,
            'next_actions': [
                'Review critical issues immediately',
                'Implement recommended automated fixes',
                'Schedule regular quality monitoring',
                'Consider ML-based anomaly detection for continuous monitoring'
            ]
        }
        
        # Save report
        report_dir = "../data/quality_reports"
        os.makedirs(report_dir, exist_ok=True)
        report_file = f"{report_dir}/data_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report

def main():
    analyzer = IntelligentDataQualityAnalyzer()
    report = analyzer.run_comprehensive_analysis()
    
    print("\n" + "="*60)
    print(" 🤖 INTELLIGENT DATA QUALITY ANALYSIS COMPLETE")
    print("="*60)
    
    print(f"\n📊 SUMMARY:")
    print(f"   Records Analyzed: {report['summary']['total_records_analyzed']}")
    print(f"   Anomalies Found: {report['summary']['total_anomalies_detected']}")
    print(f"   Critical Issues: {report['summary']['critical_issues']}")
    print(f"   Quality Score: {report['summary']['data_quality_score']}/100")
    
    if report['summary']['critical_issues'] > 0:
        print(f"\n🚨 CRITICAL ISSUES DETECTED:")
        for anomaly_type, anomalies in report['anomalies'].items():
            for anomaly in anomalies:
                if anomaly['severity'] == 'critical':
                    print(f"   ❌ {anomaly['description']}")
    
    if report['recommendations']:
        print(f"\n💡 TOP RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'][:3], 1):
            print(f"   {i}. {rec['description']}")
            if 'code' in rec:
                print(f"      Command: {rec['code']}")
    
    # Create report file path
    report_file = f"../data/quality_reports/data_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    print(f"\n📁 Full report saved to: {report_file}")
    
    return report

if __name__ == "__main__":
    main()
