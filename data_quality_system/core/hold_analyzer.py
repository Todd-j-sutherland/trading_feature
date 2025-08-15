#!/usr/bin/env python3
"""
Specialized HOLD Position Analyzer
Deep dive analysis of HOLD positions to identify data quality and model issues
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import yfinance as yf
import warnings
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

warnings.filterwarnings('ignore')

class HOLDPositionAnalyzer:
    def __init__(self, db_path=None):
        if db_path is None:
            # Try to find the database automatically
            possible_paths = [
                "../data/trading_predictions.db",
                "../../data/trading_predictions.db",
                "/root/test/data/trading_predictions.db",
                "data/trading_predictions.db"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    self.db_path = path
                    break
            else:
                self.db_path = "../data/trading_predictions.db"
        else:
            self.db_path = db_path
            
        self.hold_data = None
        self.all_data = None
        
    def load_data(self, days_back=30):
        """Load trading data with focus on HOLD positions"""
        conn = sqlite3.connect(self.db_path)
        
        # Load all recent trading data
        self.all_data = pd.read_sql_query(f"""
            SELECT * FROM enhanced_outcomes 
            WHERE created_at >= date('now', '-{days_back} days')
            ORDER BY created_at DESC
        """, conn)
        
        # Filter HOLD positions
        self.hold_data = self.all_data[self.all_data['optimal_action'] == 'HOLD'].copy()
        
        conn.close()
        
        print(f"📊 Loaded {len(self.all_data)} total records")
        print(f"🔒 Found {len(self.hold_data)} HOLD positions ({len(self.hold_data)/len(self.all_data)*100:.1f}%)")
        
        return len(self.hold_data) > 0
    
    def analyze_hold_returns_distribution(self):
        """Analyze the distribution of HOLD position returns"""
        if self.hold_data is None or len(self.hold_data) == 0:
            return {}
        
        hold_returns = self.hold_data['return_pct'].dropna()
        
        analysis = {
            'total_hold_positions': len(self.hold_data),
            'returns_available': len(hold_returns),
            'return_statistics': {
                'mean': hold_returns.mean(),
                'median': hold_returns.median(),
                'std': hold_returns.std(),
                'min': hold_returns.min(),
                'max': hold_returns.max(),
                'win_rate': (hold_returns > 0).sum() / len(hold_returns) if len(hold_returns) > 0 else 0
            }
        }
        
        # Check for suspicious patterns
        analysis['suspicious_patterns'] = []
        
        # 1. Check for identical returns
        return_counts = hold_returns.value_counts()
        if len(return_counts) > 0:
            max_identical = return_counts.max()
            most_common_return = return_counts.index[0]
            
            if max_identical > len(hold_returns) * 0.1:
                analysis['suspicious_patterns'].append({
                    'type': 'identical_returns',
                    'description': f'{max_identical} HOLD positions have identical return of {most_common_return:.3f}%',
                    'severity': 'high'
                })
        
        # 2. Check for unrealistic win rate
        win_rate = analysis['return_statistics']['win_rate']
        if win_rate > 0.8:
            analysis['suspicious_patterns'].append({
                'type': 'unrealistic_win_rate',
                'description': f'HOLD win rate of {win_rate:.1%} seems unrealistic for passive strategy',
                'severity': 'high'
            })
        
        # 3. Check for zero returns (no price movement)
        zero_returns = (hold_returns == 0).sum()
        if zero_returns > len(hold_returns) * 0.3:
            analysis['suspicious_patterns'].append({
                'type': 'excessive_zero_returns',
                'description': f'{zero_returns} HOLD positions have exactly 0% return',
                'severity': 'medium'
            })
        
        return analysis
    
    def analyze_hold_timing_patterns(self):
        """Analyze when HOLD decisions are made"""
        if self.hold_data is None or len(self.hold_data) == 0:
            return {}
        
        # Convert created_at to datetime (handle timezone format)
        try:
            self.hold_data['datetime'] = pd.to_datetime(self.hold_data['created_at'], utc=True)
            self.all_data['datetime'] = pd.to_datetime(self.all_data['created_at'], utc=True)
        except:
            # Fallback: strip timezone and parse
            self.hold_data['datetime'] = pd.to_datetime(self.hold_data['created_at'].str.replace(r'\+\d{2}:\d{2}$', '', regex=True))
            self.all_data['datetime'] = pd.to_datetime(self.all_data['created_at'].str.replace(r'\+\d{2}:\d{2}$', '', regex=True))
        
        # Daily analysis
        hold_daily = self.hold_data.groupby(self.hold_data['datetime'].dt.date).size()
        total_daily = self.all_data.groupby(self.all_data['datetime'].dt.date).size()
        
        daily_hold_rate = (hold_daily / total_daily * 100).fillna(0)
        
        analysis = {
            'daily_patterns': {
                'avg_daily_hold_rate': daily_hold_rate.mean(),
                'max_daily_hold_rate': daily_hold_rate.max(),
                'days_with_100pct_hold': (daily_hold_rate == 100).sum(),
                'days_with_no_hold': (daily_hold_rate == 0).sum()
            }
        }
        
        # Find days with suspicious patterns
        suspicious_days = []
        for date, hold_rate in daily_hold_rate.items():
            if hold_rate == 100 and total_daily[date] >= 3:  # All HOLD with at least 3 trades
                suspicious_days.append({
                    'date': str(date),
                    'hold_rate': hold_rate,
                    'total_trades': total_daily[date]
                })
        
        analysis['suspicious_days'] = suspicious_days
        
        # Hour of day analysis
        hold_hourly = self.hold_data.groupby(self.hold_data['datetime'].dt.hour).size()
        total_hourly = self.all_data.groupby(self.all_data['datetime'].dt.hour).size()
        hourly_hold_rate = (hold_hourly / total_hourly * 100).fillna(0)
        
        analysis['hourly_patterns'] = {
            'hour_with_most_holds': hourly_hold_rate.idxmax(),
            'max_hourly_hold_rate': hourly_hold_rate.max(),
            'hour_with_least_holds': hourly_hold_rate.idxmin(),
            'min_hourly_hold_rate': hourly_hold_rate.min()
        }
        
        return analysis
    
    def analyze_hold_symbol_patterns(self):
        """Analyze which symbols are frequently HOLD"""
        if self.hold_data is None or len(self.hold_data) == 0:
            return {}
        
        # Symbol analysis
        hold_by_symbol = self.hold_data['symbol'].value_counts()
        total_by_symbol = self.all_data['symbol'].value_counts()
        
        symbol_hold_rates = (hold_by_symbol / total_by_symbol * 100).fillna(0)
        
        analysis = {
            'symbol_statistics': {
                'total_unique_symbols': len(symbol_hold_rates),
                'avg_symbol_hold_rate': symbol_hold_rates.mean(),
                'symbols_with_100pct_hold': (symbol_hold_rates == 100).sum(),
                'symbols_with_high_hold': (symbol_hold_rates > 80).sum()
            }
        }
        
        # Find symbols with suspicious HOLD rates
        suspicious_symbols = []
        for symbol, hold_rate in symbol_hold_rates.items():
            if hold_rate > 90 and total_by_symbol[symbol] >= 5:  # High HOLD rate with sufficient data
                suspicious_symbols.append({
                    'symbol': symbol,
                    'hold_rate': hold_rate,
                    'total_trades': total_by_symbol[symbol],
                    'hold_trades': hold_by_symbol.get(symbol, 0)
                })
        
        analysis['suspicious_symbols'] = sorted(suspicious_symbols, 
                                              key=lambda x: x['hold_rate'], 
                                              reverse=True)
        
        return analysis
    
    def analyze_hold_confidence_patterns(self):
        """Analyze confidence scores for HOLD decisions"""
        if self.hold_data is None or len(self.hold_data) == 0:
            return {}
        
        if 'confidence_score' not in self.hold_data.columns:
            return {'error': 'No confidence_score column found'}
        
        hold_confidence = self.hold_data['confidence_score'].dropna()
        all_confidence = self.all_data['confidence_score'].dropna()
        
        analysis = {
            'confidence_statistics': {
                'hold_avg_confidence': hold_confidence.mean(),
                'hold_confidence_std': hold_confidence.std(),
                'overall_avg_confidence': all_confidence.mean(),
                'confidence_difference': hold_confidence.mean() - all_confidence.mean()
            }
        }
        
        # Check for confidence clustering
        conf_rounded = np.round(hold_confidence, 2)
        conf_counts = conf_rounded.value_counts()
        
        if len(conf_counts) > 0:
            max_cluster = conf_counts.max()
            most_common_conf = conf_counts.index[0]
            
            if max_cluster > len(hold_confidence) * 0.2:
                analysis['confidence_clustering'] = {
                    'clustered_value': most_common_conf,
                    'cluster_size': max_cluster,
                    'cluster_percentage': (max_cluster / len(hold_confidence)) * 100
                }
        
        return analysis
    
    def validate_hold_performance_against_market(self, sample_size=20):
        """Validate HOLD performance against actual market data"""
        if self.hold_data is None or len(self.hold_data) == 0:
            return {}
        
        print(f"🔍 Validating {min(sample_size, len(self.hold_data))} HOLD positions against market data...")
        
        sample_holds = self.hold_data.head(sample_size)
        validation_results = []
        
        for _, row in sample_holds.iterrows():
            try:
                symbol = row['symbol']
                entry_date = pd.to_datetime(row['created_at']).date()
                exit_date = entry_date + timedelta(days=1)
                
                # Get market data
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=entry_date - timedelta(days=2), 
                                    end=exit_date + timedelta(days=2))
                
                if len(hist) >= 2:
                    # Find closest prices to entry and exit dates
                    entry_price_market = hist['Close'].iloc[0]
                    exit_price_market = hist['Close'].iloc[-1]
                    market_return = ((exit_price_market - entry_price_market) / entry_price_market) * 100
                    
                    recorded_return = row.get('return_pct', 0)
                    
                    validation_results.append({
                        'symbol': symbol,
                        'recorded_return': recorded_return,
                        'market_return': market_return,
                        'difference': abs(recorded_return - market_return),
                        'entry_price_recorded': row.get('entry_price'),
                        'exit_price_recorded': row.get('exit_price_1d'),
                        'entry_price_market': entry_price_market,
                        'exit_price_market': exit_price_market
                    })
                    
            except Exception as e:
                continue
        
        if validation_results:
            differences = [r['difference'] for r in validation_results]
            large_discrepancies = [r for r in validation_results if r['difference'] > 2.0]  # >2% difference
            
            analysis = {
                'validated_positions': len(validation_results),
                'avg_difference': np.mean(differences),
                'max_difference': np.max(differences),
                'large_discrepancies': len(large_discrepancies),
                'discrepancy_details': large_discrepancies[:5]  # Top 5 discrepancies
            }
            
            return analysis
        
        return {'error': 'No positions could be validated'}
    
    def generate_hold_analysis_report(self):
        """Generate comprehensive HOLD analysis report"""
        print("🔒 Starting Comprehensive HOLD Position Analysis...")
        
        if not self.load_data():
            return {'error': 'No HOLD positions found'}
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'analysis_summary': {
                'total_positions': len(self.all_data),
                'hold_positions': len(self.hold_data),
                'hold_percentage': (len(self.hold_data) / len(self.all_data)) * 100
            }
        }
        
        # Run all analyses
        print("📊 Analyzing return distributions...")
        report['return_analysis'] = self.analyze_hold_returns_distribution()
        
        print("⏰ Analyzing timing patterns...")
        report['timing_analysis'] = self.analyze_hold_timing_patterns()
        
        print("📈 Analyzing symbol patterns...")
        report['symbol_analysis'] = self.analyze_hold_symbol_patterns()
        
        print("🎯 Analyzing confidence patterns...")
        report['confidence_analysis'] = self.analyze_hold_confidence_patterns()
        
        print("✅ Validating against market data...")
        report['market_validation'] = self.validate_hold_performance_against_market()
        
        # Generate recommendations
        recommendations = []
        
        # Check for critical issues
        if report['return_analysis'].get('suspicious_patterns'):
            for pattern in report['return_analysis']['suspicious_patterns']:
                if pattern['severity'] == 'high':
                    recommendations.append(f"CRITICAL: {pattern['description']}")
        
        if report['timing_analysis'].get('suspicious_days'):
            recommendations.append(f"Review {len(report['timing_analysis']['suspicious_days'])} days with 100% HOLD decisions")
        
        if report['symbol_analysis'].get('suspicious_symbols'):
            top_biased = len([s for s in report['symbol_analysis']['suspicious_symbols'] if s['hold_rate'] > 95])
            if top_biased > 0:
                recommendations.append(f"Investigate {top_biased} symbols with >95% HOLD rate")
        
        if report['market_validation'].get('large_discrepancies', 0) > 0:
            recommendations.append(f"Validate {report['market_validation']['large_discrepancies']} HOLD positions with large market discrepancies")
        
        report['recommendations'] = recommendations
        
        # Save report
        os.makedirs("../data/hold_analysis", exist_ok=True)
        report_file = f"../data/hold_analysis/hold_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📁 HOLD analysis report saved: {report_file}")
        
        return report
    
    def print_summary(self, report):
        """Print formatted summary of HOLD analysis"""
        print("\n" + "="*60)
        print(" 🔒 HOLD POSITION ANALYSIS SUMMARY")
        print("="*60)
        
        summary = report['analysis_summary']
        print(f"\n📊 OVERVIEW:")
        print(f"   Total Positions: {summary['total_positions']}")
        print(f"   HOLD Positions: {summary['hold_positions']}")
        print(f"   HOLD Percentage: {summary['hold_percentage']:.1f}%")
        
        # Return analysis
        if 'return_analysis' in report:
            ret_stats = report['return_analysis'].get('return_statistics', {})
            print(f"\n💰 HOLD PERFORMANCE:")
            print(f"   Average Return: {ret_stats.get('mean', 0):.3f}%")
            print(f"   Win Rate: {ret_stats.get('win_rate', 0):.1%}")
            print(f"   Return Std Dev: {ret_stats.get('std', 0):.3f}%")
        
        # Suspicious patterns
        if report.get('recommendations'):
            print(f"\n⚠️  RECOMMENDATIONS:")
            for i, rec in enumerate(report['recommendations'][:5], 1):
                print(f"   {i}. {rec}")
        
        # Market validation
        if 'market_validation' in report and 'avg_difference' in report['market_validation']:
            val = report['market_validation']
            print(f"\n🎯 MARKET VALIDATION:")
            print(f"   Validated Positions: {val['validated_positions']}")
            print(f"   Avg Difference: {val['avg_difference']:.2f}%")
            print(f"   Large Discrepancies: {val['large_discrepancies']}")

def main():
    analyzer = HOLDPositionAnalyzer()
    report = analyzer.generate_hold_analysis_report()
    
    if 'error' not in report:
        analyzer.print_summary(report)
    else:
        print(f"❌ Error: {report['error']}")
    
    return report

if __name__ == "__main__":
    main()
