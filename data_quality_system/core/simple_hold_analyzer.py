#!/usr/bin/env python3
"""
Simplified HOLD Position Analyzer
Focus on core patterns without complex datetime parsing
"""

import sqlite3
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

class SimpleHOLDAnalyzer:
    def __init__(self, db_path="data/trading_predictions.db"):
        self.db_path = db_path
        self.hold_data = None
        self.all_data = None
        
    def load_data(self, days_back=30):
        """Load trading data with focus on HOLD positions"""
        if not os.path.exists(self.db_path):
            print(f"❌ Database not found: {self.db_path}")
            return False
            
        conn = sqlite3.connect(self.db_path)
        
        # Load all recent trading data
        self.all_data = pd.read_sql_query(f"""
            SELECT * FROM enhanced_outcomes 
            ORDER BY created_at DESC 
            LIMIT 1000
        """, conn)
        
        # Filter HOLD positions
        self.hold_data = self.all_data[self.all_data['optimal_action'] == 'HOLD'].copy()
        
        conn.close()
        
        print(f"📊 Loaded {len(self.all_data)} total records")
        print(f"🔒 Found {len(self.hold_data)} HOLD positions ({len(self.hold_data)/len(self.all_data)*100:.1f}%)")
        
        return len(self.hold_data) > 0
    
    def analyze_hold_returns(self):
        """Analyze HOLD position returns"""
        if self.hold_data is None or len(self.hold_data) == 0:
            return {}
        
        # Get return data
        hold_returns = self.hold_data['return_pct'].dropna()
        all_returns = self.all_data['return_pct'].dropna()
        
        analysis = {
            'total_hold_positions': len(self.hold_data),
            'returns_with_data': len(hold_returns),
            'hold_statistics': {
                'mean_return': hold_returns.mean(),
                'median_return': hold_returns.median(),
                'std_return': hold_returns.std(),
                'min_return': hold_returns.min(),
                'max_return': hold_returns.max(),
                'win_rate': (hold_returns > 0).sum() / len(hold_returns) if len(hold_returns) > 0 else 0,
                'zero_returns': (hold_returns == 0).sum(),
                'negative_returns': (hold_returns < 0).sum(),
                'positive_returns': (hold_returns > 0).sum()
            },
            'comparison_to_all': {
                'hold_avg': hold_returns.mean(),
                'all_avg': all_returns.mean(),
                'hold_better': hold_returns.mean() > all_returns.mean()
            }
        }
        
        # Check for suspicious patterns
        issues = []
        
        # 1. Identical returns
        if len(hold_returns) > 0:
            return_counts = hold_returns.value_counts()
            max_identical = return_counts.max()
            
            if max_identical > len(hold_returns) * 0.15:  # >15% identical
                most_common = return_counts.index[0]
                issues.append(f"⚠️  {max_identical} positions have identical return of {most_common:.3f}%")
        
        # 2. Too many zero returns
        zero_pct = analysis['hold_statistics']['zero_returns'] / len(hold_returns) * 100 if len(hold_returns) > 0 else 0
        if zero_pct > 30:
            issues.append(f"⚠️  {zero_pct:.1f}% of HOLD positions have exactly 0% return")
        
        # 3. Unrealistic win rate
        win_rate = analysis['hold_statistics']['win_rate']
        if win_rate > 0.8:
            issues.append(f"⚠️  HOLD win rate of {win_rate:.1%} seems unrealistic")
        
        analysis['issues'] = issues
        return analysis
    
    def analyze_hold_symbols(self):
        """Analyze which symbols are frequently HOLD"""
        if self.hold_data is None or len(self.hold_data) == 0:
            return {}
        
        # Symbol frequency
        hold_by_symbol = self.hold_data['symbol'].value_counts()
        total_by_symbol = self.all_data['symbol'].value_counts()
        
        # Calculate HOLD rates per symbol
        symbol_hold_rates = {}
        for symbol in total_by_symbol.index:
            hold_count = hold_by_symbol.get(symbol, 0)
            total_count = total_by_symbol[symbol]
            hold_rate = (hold_count / total_count) * 100
            
            if total_count >= 3:  # Only include symbols with sufficient data
                symbol_hold_rates[symbol] = {
                    'hold_count': hold_count,
                    'total_count': total_count,
                    'hold_rate': hold_rate
                }
        
        # Find symbols with extreme HOLD rates
        high_hold_symbols = {k: v for k, v in symbol_hold_rates.items() if v['hold_rate'] > 90}
        no_hold_symbols = {k: v for k, v in symbol_hold_rates.items() if v['hold_rate'] == 0}
        
        analysis = {
            'total_symbols': len(symbol_hold_rates),
            'symbols_with_high_hold': len(high_hold_symbols),
            'symbols_with_no_hold': len(no_hold_symbols),
            'high_hold_details': dict(list(high_hold_symbols.items())[:10]),  # Top 10
            'symbol_statistics': {
                'avg_hold_rate': np.mean([v['hold_rate'] for v in symbol_hold_rates.values()]),
                'median_hold_rate': np.median([v['hold_rate'] for v in symbol_hold_rates.values()]),
                'max_hold_rate': max([v['hold_rate'] for v in symbol_hold_rates.values()]) if symbol_hold_rates else 0
            }
        }
        
        return analysis
    
    def analyze_hold_confidence(self):
        """Analyze confidence scores for HOLD decisions"""
        if self.hold_data is None or len(self.hold_data) == 0:
            return {}
        
        if 'confidence_score' not in self.hold_data.columns:
            return {'error': 'No confidence_score column found'}
        
        hold_conf = self.hold_data['confidence_score'].dropna()
        all_conf = self.all_data['confidence_score'].dropna()
        
        if len(hold_conf) == 0:
            return {'error': 'No confidence scores available'}
        
        analysis = {
            'confidence_stats': {
                'hold_avg_confidence': hold_conf.mean(),
                'hold_median_confidence': hold_conf.median(),
                'hold_std_confidence': hold_conf.std(),
                'all_avg_confidence': all_conf.mean(),
                'confidence_difference': hold_conf.mean() - all_conf.mean()
            }
        }
        
        # Check for confidence clustering
        conf_rounded = np.round(hold_conf, 2)
        conf_counts = conf_rounded.value_counts()
        
        if len(conf_counts) > 0:
            max_cluster = conf_counts.max()
            most_common_conf = conf_counts.index[0]
            
            if max_cluster > len(hold_conf) * 0.2:  # >20% clustering
                analysis['confidence_clustering'] = {
                    'clustered_value': most_common_conf,
                    'cluster_size': max_cluster,
                    'cluster_percentage': (max_cluster / len(hold_conf)) * 100
                }
        
        return analysis
    
    def generate_summary_report(self):
        """Generate comprehensive HOLD analysis report"""
        print("🔒 Starting HOLD Position Analysis...")
        
        if not self.load_data():
            return {'error': 'No HOLD positions found'}
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'overview': {
                'total_positions': len(self.all_data),
                'hold_positions': len(self.hold_data),
                'hold_percentage': (len(self.hold_data) / len(self.all_data)) * 100
            }
        }
        
        print("📊 Analyzing returns...")
        report['returns'] = self.analyze_hold_returns()
        
        print("📈 Analyzing symbols...")
        report['symbols'] = self.analyze_hold_symbols()
        
        print("🎯 Analyzing confidence...")
        report['confidence'] = self.analyze_hold_confidence()
        
        # Generate recommendations
        recommendations = []
        
        if report['returns'].get('issues'):
            recommendations.extend(report['returns']['issues'])
        
        if report['symbols']['symbols_with_high_hold'] > 5:
            recommendations.append(f"🔍 Investigate {report['symbols']['symbols_with_high_hold']} symbols with >90% HOLD rate")
        
        if 'confidence_clustering' in report['confidence']:
            cluster = report['confidence']['confidence_clustering']
            recommendations.append(f"🎯 {cluster['cluster_percentage']:.1f}% of HOLD decisions have confidence {cluster['clustered_value']}")
        
        report['recommendations'] = recommendations
        
        return report
    
    def print_summary(self, report):
        """Print formatted summary"""
        print("\n" + "="*60)
        print(" 🔒 HOLD POSITION ANALYSIS SUMMARY")
        print("="*60)
        
        overview = report['overview']
        print(f"\n📊 OVERVIEW:")
        print(f"   Total Positions: {overview['total_positions']}")
        print(f"   HOLD Positions: {overview['hold_positions']}")
        print(f"   HOLD Percentage: {overview['hold_percentage']:.1f}%")
        
        # Returns
        if 'returns' in report and 'hold_statistics' in report['returns']:
            stats = report['returns']['hold_statistics']
            print(f"\n💰 HOLD PERFORMANCE:")
            print(f"   Average Return: {stats['mean_return']:.3f}%")
            print(f"   Win Rate: {stats['win_rate']:.1%}")
            print(f"   Positive: {stats['positive_returns']}, Zero: {stats['zero_returns']}, Negative: {stats['negative_returns']}")
            
            if report['returns']['comparison_to_all']['hold_better']:
                print(f"   ✅ HOLD avg ({stats['mean_return']:.3f}%) > Overall avg ({report['returns']['comparison_to_all']['all_avg']:.3f}%)")
            else:
                print(f"   ❌ HOLD avg ({stats['mean_return']:.3f}%) < Overall avg ({report['returns']['comparison_to_all']['all_avg']:.3f}%)")
        
        # Symbols
        if 'symbols' in report:
            symbols = report['symbols']
            print(f"\n📈 SYMBOL ANALYSIS:")
            print(f"   Symbols Analyzed: {symbols['total_symbols']}")
            print(f"   High HOLD Rate (>90%): {symbols['symbols_with_high_hold']}")
            print(f"   Average Symbol HOLD Rate: {symbols['symbol_statistics']['avg_hold_rate']:.1f}%")
        
        # Recommendations
        if report.get('recommendations'):
            print(f"\n⚠️  FINDINGS:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"   {i}. {rec}")
        
        if not report.get('recommendations'):
            print(f"\n✅ No major issues detected in HOLD positions")

def main():
    analyzer = SimpleHOLDAnalyzer()
    report = analyzer.generate_summary_report()
    
    if 'error' not in report:
        analyzer.print_summary(report)
        
        # Save report
        os.makedirs("data/hold_analysis", exist_ok=True)
        report_file = f"data/hold_analysis/simple_hold_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📁 Report saved: {report_file}")
    else:
        print(f"❌ Error: {report['error']}")

if __name__ == "__main__":
    main()
