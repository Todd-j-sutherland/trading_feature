#!/usr/bin/env python3
"""
Simplified Backtesting System

A lightweight backtesting system that uses only standard library components
and your existing database data. Creates basic visualizations and analysis.
"""

import sqlite3
import json
import csv
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

class SimpleBacktester:
    """Simplified backtesting system using only standard library"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            self.unified_db = project_root / "data" / "trading_predictions.db"
            self.trading_db = project_root / "data" / "trading_data.db"
        
        self.bank_symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX']
        self.results_dir = Path(__file__).parent.parent.parent.parent / "results" / "backtesting"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def load_database_data(self) -> List[Tuple[str, List[Dict]]]:
        """Load trading data from available databases"""
        all_data = []
        
        for db_path in [self.unified_db, self.trading_db]:
            if not db_path.exists():
                continue
                
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row  # Enable dict-like access
                
                # Get available tables
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Load morning analysis data
                if 'enhanced_morning_analysis' in tables:
                    cursor = conn.execute("""
                        SELECT timestamp, technical_signals, recommendations, ml_predictions
                        FROM enhanced_morning_analysis 
                        ORDER BY timestamp DESC LIMIT 50
                    """)
                    rows = [dict(row) for row in cursor.fetchall()]
                    all_data.append(('morning_analysis', rows))
                
                # Load evening analysis data  
                if 'enhanced_evening_analysis' in tables:
                    cursor = conn.execute("""
                        SELECT timestamp, next_day_predictions, model_comparison
                        FROM enhanced_evening_analysis 
                        ORDER BY timestamp DESC LIMIT 50
                    """)
                    rows = [dict(row) for row in cursor.fetchall()]
                    all_data.append(('evening_analysis', rows))
                
                conn.close()
                
            except Exception as e:
                print(f"Error loading data from {db_path}: {e}")
        
        return all_data
    
    def extract_trading_signals(self, data_type: str, rows: List[Dict]) -> List[Dict]:
        """Extract trading signals from database rows"""
        signals = []
        
        for row in rows:
            timestamp = row['timestamp']
            
            try:
                if data_type == 'morning_analysis':
                    # Parse technical signals (traditional analysis)
                    technical_str = row.get('technical_signals', '{}')
                    technical = json.loads(technical_str) if isinstance(technical_str, str) else technical_str
                    
                    if isinstance(technical, dict):
                        for symbol in self.bank_symbols:
                            if symbol in technical:
                                signal_data = technical[symbol]
                                signals.append({
                                    'timestamp': timestamp,
                                    'symbol': symbol,
                                    'strategy': 'traditional',
                                    'signal': signal_data.get('final_signal', 'HOLD'),
                                    'confidence': signal_data.get('overall_confidence', 0.5),
                                    'sentiment': signal_data.get('sentiment_contribution', 0),
                                    'technical': signal_data.get('rsi', 50),
                                    'price': signal_data.get('current_price', 0)
                                })
                    
                    # Parse ML predictions
                    ml_str = row.get('ml_predictions', '{}')
                    ml_data = json.loads(ml_str) if isinstance(ml_str, str) else ml_str
                    
                    if isinstance(ml_data, dict):
                        for symbol in self.bank_symbols:
                            if symbol in ml_data:
                                ml_signal = ml_data[symbol]
                                signals.append({
                                    'timestamp': timestamp,
                                    'symbol': symbol,
                                    'strategy': 'ml',
                                    'signal': ml_signal.get('optimal_action', 'HOLD'),
                                    'confidence': ml_signal.get('confidence', 0.5),
                                    'sentiment': 0,
                                    'technical': 0,
                                    'price': 0
                                })
                
                elif data_type == 'evening_analysis':
                    # Parse evening ML results from next_day_predictions
                    ml_str = row.get('next_day_predictions', '{}')
                    ml_data = json.loads(ml_str) if isinstance(ml_str, str) else ml_str
                    
                    # Extract bank_predictions from the structure
                    if isinstance(ml_data, dict) and 'bank_predictions' in ml_data:
                        bank_predictions = ml_data['bank_predictions']
                        for symbol in self.bank_symbols:
                            if symbol in bank_predictions:
                                ml_signal = bank_predictions[symbol]
                                signals.append({
                                    'timestamp': timestamp,
                                    'symbol': symbol,
                                    'strategy': 'evening_ml',
                                    'signal': ml_signal.get('optimal_action', 'HOLD'),
                                    'confidence': ml_signal.get('confidence', 0.5),
                                    'sentiment': 0,
                                    'technical': 0,
                                    'price': 0
                                })
            
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error parsing data for {timestamp}: {e}")
                continue
        
        return signals
    
    def calculate_strategy_performance(self, signals: List[Dict]) -> Dict[str, Any]:
        """Calculate basic performance metrics for strategies"""
        if not signals:
            return {}
        
        # Group signals by strategy
        strategies = {}
        for signal in signals:
            strategy = signal['strategy']
            if strategy not in strategies:
                strategies[strategy] = []
            strategies[strategy].append(signal)
        
        # Calculate metrics for each strategy
        performance = {}
        for strategy, strategy_signals in strategies.items():
            signal_counts = {}
            confidence_scores = []
            
            for signal in strategy_signals:
                signal_type = signal['signal']
                confidence = signal['confidence']
                
                signal_counts[signal_type] = signal_counts.get(signal_type, 0) + 1
                confidence_scores.append(confidence)
            
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            performance[strategy] = {
                'total_signals': len(strategy_signals),
                'signal_distribution': signal_counts,
                'average_confidence': avg_confidence,
                'confidence_std': self._calculate_std(confidence_scores),
                'symbols_covered': len(set(s['symbol'] for s in strategy_signals))
            }
        
        return performance
    
    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation manually"""
        if len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return variance ** 0.5
    
    def create_csv_report(self, signals: List[Dict]) -> str:
        """Create CSV report of all signals"""
        csv_file = self.results_dir / "backtesting_signals.csv"
        
        if not signals:
            print("No signals to write to CSV")
            return str(csv_file)
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'symbol', 'strategy', 'signal', 
                'confidence', 'sentiment', 'technical', 'price'
            ])
            writer.writeheader()
            writer.writerows(signals)
        
        return str(csv_file)
    
    def create_summary_report(self, all_signals: List[Dict], performance: Dict[str, Any]) -> str:
        """Create a text summary report"""
        report_file = self.results_dir / "backtesting_summary.txt"
        
        with open(report_file, 'w') as f:
            f.write("COMPREHENSIVE BACKTESTING SUMMARY REPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Overall statistics
            f.write("OVERALL STATISTICS\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total signals analyzed: {len(all_signals)}\n")
            f.write(f"Unique symbols: {len(set(s['symbol'] for s in all_signals))}\n")
            f.write(f"Strategies analyzed: {len(performance)}\n")
            f.write(f"Date range: {min(s['timestamp'] for s in all_signals) if all_signals else 'N/A'} to {max(s['timestamp'] for s in all_signals) if all_signals else 'N/A'}\n\n")
            
            # Signal distribution
            signal_dist = {}
            for signal in all_signals:
                signal_type = signal['signal']
                signal_dist[signal_type] = signal_dist.get(signal_type, 0) + 1
            
            f.write("SIGNAL DISTRIBUTION\n")
            f.write("-" * 20 + "\n")
            for signal_type, count in sorted(signal_dist.items()):
                percentage = (count / len(all_signals)) * 100 if all_signals else 0
                f.write(f"{signal_type}: {count} ({percentage:.1f}%)\n")
            f.write("\n")
            
            # Strategy performance
            f.write("STRATEGY PERFORMANCE\n")
            f.write("-" * 20 + "\n")
            for strategy, metrics in performance.items():
                f.write(f"\n{strategy.upper()}:\n")
                f.write(f"  Total signals: {metrics['total_signals']}\n")
                f.write(f"  Average confidence: {metrics['average_confidence']:.3f}\n")
                f.write(f"  Confidence std dev: {metrics['confidence_std']:.3f}\n")
                f.write(f"  Symbols covered: {metrics['symbols_covered']}\n")
                f.write(f"  Signal breakdown:\n")
                for sig_type, count in metrics['signal_distribution'].items():
                    f.write(f"    {sig_type}: {count}\n")
            
            # Symbol analysis
            f.write("\nSYMBOL ANALYSIS\n")
            f.write("-" * 15 + "\n")
            symbol_stats = {}
            for signal in all_signals:
                symbol = signal['symbol']
                if symbol not in symbol_stats:
                    symbol_stats[symbol] = {'signals': 0, 'avg_confidence': []}
                symbol_stats[symbol]['signals'] += 1
                symbol_stats[symbol]['avg_confidence'].append(signal['confidence'])
            
            for symbol in sorted(symbol_stats.keys()):
                stats = symbol_stats[symbol]
                avg_conf = sum(stats['avg_confidence']) / len(stats['avg_confidence']) if stats['avg_confidence'] else 0
                f.write(f"{symbol}: {stats['signals']} signals, avg confidence: {avg_conf:.3f}\n")
        
        return str(report_file)
    
    def generate_simple_html_chart(self, signals: List[Dict]) -> str:
        """Generate a simple HTML chart using basic HTML/CSS"""
        html_file = self.results_dir / "backtesting_chart.html"
        
        # Group signals by symbol and strategy
        symbol_data = {}
        for signal in signals:
            symbol = signal['symbol']
            if symbol not in symbol_data:
                symbol_data[symbol] = {}
            
            strategy = signal['strategy']
            if strategy not in symbol_data[symbol]:
                symbol_data[symbol][strategy] = []
            
            symbol_data[symbol][strategy].append({
                'timestamp': signal['timestamp'],
                'confidence': signal['confidence'],
                'signal': signal['signal']
            })
        
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Trading Strategy Backtesting Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .symbol-section { margin-bottom: 40px; border: 1px solid #ddd; padding: 20px; }
        .strategy-row { margin: 10px 0; padding: 10px; background: #f5f5f5; }
        .signal-bar { height: 20px; display: inline-block; margin: 2px; padding: 2px 5px; color: white; font-size: 12px; }
        .BUY { background-color: #4CAF50; }
        .SELL { background-color: #f44336; }
        .HOLD { background-color: #ff9800; }
        .confidence { font-weight: bold; }
        .summary { background: #e3f2fd; padding: 15px; margin-bottom: 20px; }
        h1, h2, h3 { color: #333; }
    </style>
</head>
<body>
    <h1>📈 Trading Strategy Backtesting Results</h1>
    <div class="summary">
        <h3>Summary</h3>
        <p><strong>Total Signals:</strong> """ + str(len(signals)) + """</p>
        <p><strong>Symbols Analyzed:</strong> """ + str(len(symbol_data)) + """</p>
        <p><strong>Generated:</strong> """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
    </div>
"""
        
        for symbol, strategies in symbol_data.items():
            html_content += f'<div class="symbol-section">\n<h2>{symbol}</h2>\n'
            
            for strategy, strategy_signals in strategies.items():
                html_content += f'<div class="strategy-row">\n<h3>{strategy.replace("_", " ").title()}</h3>\n'
                html_content += f'<p>Signals: {len(strategy_signals)} | '
                
                # Calculate average confidence
                avg_conf = sum(s['confidence'] for s in strategy_signals) / len(strategy_signals) if strategy_signals else 0
                html_content += f'Average Confidence: <span class="confidence">{avg_conf:.3f}</span></p>\n'
                
                # Create signal bars
                for sig in strategy_signals[-20:]:  # Show last 20 signals
                    confidence_width = int(sig['confidence'] * 100)
                    html_content += f'<div class="signal-bar {sig["signal"]}" style="width: {confidence_width}px;">'
                    html_content += f'{sig["signal"]} ({sig["confidence"]:.2f})</div>\n'
                
                html_content += '</div>\n'
            
            html_content += '</div>\n'
        
        html_content += """
    <div class="summary">
        <h3>Legend</h3>
        <div class="signal-bar BUY">BUY Signal</div>
        <div class="signal-bar SELL">SELL Signal</div>
        <div class="signal-bar HOLD">HOLD Signal</div>
        <p>Bar width represents confidence level (wider = higher confidence)</p>
    </div>
</body>
</html>
"""
        
        with open(html_file, 'w') as f:
            f.write(html_content)
        
        return str(html_file)
    
    def run_simple_backtest(self) -> Dict[str, str]:
        """Run the simplified backtesting analysis"""
        print("📊 Running Simple Backtesting Analysis...")
        
        # Load data
        print("🔄 Loading data from databases...")
        database_data = self.load_database_data()
        
        if not database_data:
            print("❌ No data found in databases")
            return {'error': 'No data available'}
        
        # Extract all signals
        all_signals = []
        for data_type, rows in database_data:
            print(f"   Processing {data_type}: {len(rows)} records")
            signals = self.extract_trading_signals(data_type, rows)
            all_signals.extend(signals)
            print(f"   Extracted {len(signals)} trading signals")
        
        if not all_signals:
            print("❌ No trading signals extracted")
            return {'error': 'No signals found'}
        
        print(f"📈 Total signals extracted: {len(all_signals)}")
        
        # Calculate performance
        print("📊 Calculating strategy performance...")
        performance = self.calculate_strategy_performance(all_signals)
        
        # Generate reports
        print("📝 Generating reports...")
        csv_report = self.create_csv_report(all_signals)
        summary_report = self.create_summary_report(all_signals, performance)
        html_chart = self.generate_simple_html_chart(all_signals)
        
        results = {
            'csv_report': csv_report,
            'summary_report': summary_report,
            'html_chart': html_chart,
            'total_signals': len(all_signals),
            'strategies_analyzed': len(performance)
        }
        
        print(f"\n✅ Simple backtesting completed!")
        print(f"📊 Analyzed {len(all_signals)} signals across {len(performance)} strategies")
        print(f"📁 Results saved to: {self.results_dir}")
        
        return results

def main():
    """Main execution function"""
    backtester = SimpleBacktester()
    results = backtester.run_simple_backtest()
    
    if 'error' not in results:
        print(f"\n📈 Results Summary:")
        print(f"   📊 CSV Report: {results['csv_report']}")
        print(f"   📝 Summary Report: {results['summary_report']}")
        print(f"   🌐 HTML Chart: {results['html_chart']}")
        print(f"\n💡 Open the HTML file in your browser to view the visualization")

if __name__ == "__main__":
    main()