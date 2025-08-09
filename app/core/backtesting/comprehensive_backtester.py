#!/usr/bin/env python3
"""
Comprehensive Backtesting System

Uses all available data sources to create performance visualizations:
- Yahoo Finance historical prices
- News sentiment analysis
- Social media sentiment (if available)
- Technical analysis indicators
- Machine learning predictions
- Combined strategies with smoothed signals
"""

import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score
import warnings
warnings.filterwarnings('ignore')

class ComprehensiveBacktester:
    """Comprehensive backtesting system using all available data sources"""
    
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            self.unified_db = project_root / "data" / "trading_unified.db"
            self.trading_db = project_root / "data" / "trading_data.db"
            self.ml_db = project_root / "data" / "ml_models" / "enhanced_training_data.db"
        
        self.bank_symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX']
        self.results_dir = Path(__file__).parent.parent.parent.parent / "results" / "backtesting"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def fetch_historical_prices(self, symbol: str, period: str = "6mo") -> pd.DataFrame:
        """Fetch historical price data from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            data.reset_index(inplace=True)
            data['Symbol'] = symbol
            return data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def load_sentiment_data(self) -> pd.DataFrame:
        """Load sentiment analysis data from databases"""
        sentiment_data = []
        
        # Try multiple database locations
        for db_path in [self.unified_db, self.trading_db]:
            if db_path.exists():
                try:
                    conn = sqlite3.connect(db_path)
                    
                    # Check for different table names
                    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    if 'enhanced_morning_analysis' in tables:
                        query = """
                        SELECT 
                            timestamp,
                            technical_signals,
                            recommendations,
                            ml_predictions
                        FROM enhanced_morning_analysis
                        ORDER BY timestamp DESC
                        """
                        df = pd.read_sql_query(query, conn)
                        sentiment_data.append(('morning_analysis', df))
                    
                    if 'enhanced_evening_analysis' in tables:
                        query = """
                        SELECT 
                            timestamp,
                            next_day_predictions,
                            model_comparison
                        FROM enhanced_evening_analysis
                        ORDER BY timestamp DESC
                        """
                        df = pd.read_sql_query(query, conn)
                        sentiment_data.append(('evening_analysis', df))
                    
                    conn.close()
                except Exception as e:
                    print(f"Error loading sentiment data from {db_path}: {e}")
        
        return sentiment_data
    
    def extract_signals_from_data(self, data_type: str, df: pd.DataFrame) -> pd.DataFrame:
        """Extract trading signals from complex JSON data"""
        signals_list = []
        
        for _, row in df.iterrows():
            # Convert timestamp handling timezone issues
            timestamp = pd.to_datetime(row['timestamp'], utc=True).tz_localize(None)
            
            if data_type == 'morning_analysis':
                try:
                    import json
                    traditional = json.loads(row['technical_signals']) if isinstance(row['technical_signals'], str) else row['technical_signals']
                    ml_pred = json.loads(row['ml_predictions']) if isinstance(row['ml_predictions'], str) else row['ml_predictions']
                    
                    if isinstance(traditional, dict):
                        for symbol in self.bank_symbols:
                            if symbol in traditional:
                                signal_data = traditional[symbol]
                                signals_list.append({
                                    'timestamp': timestamp,
                                    'symbol': symbol,
                                    'signal_type': 'traditional',
                                    'signal': signal_data.get('final_signal', 'HOLD'),
                                    'confidence': signal_data.get('overall_confidence', 0.5),
                                    'sentiment_score': signal_data.get('sentiment_contribution', 0),
                                    'technical_score': signal_data.get('rsi', 50),
                                    'price': signal_data.get('current_price', 0)
                                })
                    
                    if isinstance(ml_pred, dict):
                        for symbol in self.bank_symbols:
                            if symbol in ml_pred:
                                ml_data = ml_pred[symbol]
                                signals_list.append({
                                    'timestamp': timestamp,
                                    'symbol': symbol,
                                    'signal_type': 'ml',
                                    'signal': ml_data.get('optimal_action', 'HOLD'),
                                    'confidence': ml_data.get('confidence', 0.5),
                                    'sentiment_score': 0,  # ML doesn't separate sentiment
                                    'technical_score': 0,  # ML integrates all features
                                    'price': 0
                                })
                except Exception as e:
                    print(f"Error parsing morning analysis data: {e}")
            
            elif data_type == 'evening_analysis':
                try:
                    import json
                    ml_results = json.loads(row['next_day_predictions']) if isinstance(row['next_day_predictions'], str) else row['next_day_predictions']
                    
                    # Extract bank_predictions from the structure
                    if isinstance(ml_results, dict) and 'bank_predictions' in ml_results:
                        bank_predictions = ml_results['bank_predictions']
                        for symbol in self.bank_symbols:
                            if symbol in bank_predictions:
                                ml_data = bank_predictions[symbol]
                                signals_list.append({
                                    'timestamp': timestamp,
                                    'symbol': symbol,
                                    'signal_type': 'evening_ml',
                                    'signal': ml_data.get('optimal_action', 'HOLD'),
                                    'confidence': ml_data.get('confidence', 0.5),
                                    'sentiment_score': 0,
                                    'technical_score': 0,
                                    'price': 0
                                })
                except Exception as e:
                    print(f"Error parsing evening analysis data: {e}")
        
        return pd.DataFrame(signals_list)
    
    def create_price_visualization(self, symbol: str) -> go.Figure:
        """Create comprehensive price visualization with all signals"""
        # Get historical prices
        price_data = self.fetch_historical_prices(symbol, period="3mo")
        
        if price_data.empty:
            return go.Figure().add_annotation(text=f"No price data available for {symbol}")
        
        # Get sentiment/signal data
        sentiment_data = self.load_sentiment_data()
        
        # Create subplots
        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=[
                f'{symbol} Price & Trading Signals',
                'News Sentiment Score',
                'Technical Indicators (RSI)',
                'ML Confidence & Signal Strength'
            ],
            row_heights=[0.4, 0.2, 0.2, 0.2]
        )
        
        # Plot price data
        fig.add_trace(
            go.Candlestick(
                x=price_data['Date'],
                open=price_data['Open'],
                high=price_data['High'],
                low=price_data['Low'],
                close=price_data['Close'],
                name='Price'
            ),
            row=1, col=1
        )
        
        # Add moving averages
        if len(price_data) > 20:
            price_data['SMA_20'] = price_data['Close'].rolling(20).mean()
            price_data['SMA_50'] = price_data['Close'].rolling(50).mean()
            
            fig.add_trace(
                go.Scatter(
                    x=price_data['Date'],
                    y=price_data['SMA_20'],
                    name='SMA 20',
                    line=dict(color='orange', width=1)
                ),
                row=1, col=1
            )
            
            if len(price_data) > 50:
                fig.add_trace(
                    go.Scatter(
                        x=price_data['Date'],
                        y=price_data['SMA_50'],
                        name='SMA 50',
                        line=dict(color='red', width=1)
                    ),
                    row=1, col=1
                )
        
        # Process and add signal data
        all_signals = []
        for data_type, df in sentiment_data:
            signals = self.extract_signals_from_data(data_type, df)
            signals = signals[signals['symbol'] == symbol]
            all_signals.append(signals)
        
        if all_signals:
            combined_signals = pd.concat(all_signals, ignore_index=True)
            # Convert timestamps to datetime, handling timezone issues
            combined_signals['timestamp'] = pd.to_datetime(combined_signals['timestamp'], utc=True).dt.tz_localize(None)
            combined_signals = combined_signals.sort_values('timestamp')
            
            # Plot trading signals on price chart
            buy_signals = combined_signals[combined_signals['signal'] == 'BUY']
            sell_signals = combined_signals[combined_signals['signal'] == 'SELL']
            
            if not buy_signals.empty:
                fig.add_trace(
                    go.Scatter(
                        x=buy_signals['timestamp'],
                        y=[price_data.loc[price_data['Date'].dt.date == date.date(), 'Close'].iloc[0] 
                           if not price_data.loc[price_data['Date'].dt.date == date.date()].empty 
                           else 0 for date in buy_signals['timestamp']],
                        mode='markers',
                        marker=dict(symbol='triangle-up', size=10, color='green'),
                        name='Buy Signals'
                    ),
                    row=1, col=1
                )
            
            if not sell_signals.empty:
                fig.add_trace(
                    go.Scatter(
                        x=sell_signals['timestamp'],
                        y=[price_data.loc[price_data['Date'].dt.date == date.date(), 'Close'].iloc[0] 
                           if not price_data.loc[price_data['Date'].dt.date == date.date()].empty 
                           else 0 for date in sell_signals['timestamp']],
                        mode='markers',
                        marker=dict(symbol='triangle-down', size=10, color='red'),
                        name='Sell Signals'
                    ),
                    row=1, col=1
                )
            
            # Plot sentiment scores
            sentiment_by_time = combined_signals.groupby('timestamp').agg({
                'sentiment_score': 'mean',
                'confidence': 'mean'
            }).reset_index()
            
            fig.add_trace(
                go.Scatter(
                    x=sentiment_by_time['timestamp'],
                    y=sentiment_by_time['sentiment_score'],
                    mode='lines+markers',
                    name='Sentiment Score',
                    line=dict(color='blue')
                ),
                row=2, col=1
            )
            
            # Plot technical indicators (mock RSI)
            rsi_data = combined_signals[combined_signals['technical_score'] > 0]
            if not rsi_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=rsi_data['timestamp'],
                        y=rsi_data['technical_score'],
                        mode='lines+markers',
                        name='RSI',
                        line=dict(color='purple')
                    ),
                    row=3, col=1
                )
            
            # Add RSI levels
            fig.add_hline(y=70, row=3, col=1, line=dict(color='red', dash='dash'), annotation_text="Overbought")
            fig.add_hline(y=30, row=3, col=1, line=dict(color='green', dash='dash'), annotation_text="Oversold")
            
            # Plot ML confidence
            fig.add_trace(
                go.Scatter(
                    x=sentiment_by_time['timestamp'],
                    y=sentiment_by_time['confidence'],
                    mode='lines+markers',
                    name='ML Confidence',
                    line=dict(color='orange'),
                    fill='tonexty'
                ),
                row=4, col=1
            )
        
        # Update layout
        fig.update_layout(
            title=f'{symbol} Comprehensive Backtesting Analysis',
            height=800,
            showlegend=True,
            xaxis4_title="Date"
        )
        
        # Remove x-axis labels from upper plots
        fig.update_xaxes(showticklabels=False, row=1, col=1)
        fig.update_xaxes(showticklabels=False, row=2, col=1)
        fig.update_xaxes(showticklabels=False, row=3, col=1)
        
        return fig
    
    def create_strategy_comparison(self) -> go.Figure:
        """Create strategy performance comparison"""
        sentiment_data = self.load_sentiment_data()
        
        if not sentiment_data:
            return go.Figure().add_annotation(text="No sentiment data available for comparison")
        
        # Process all signals
        all_strategies = {}
        
        for data_type, df in sentiment_data:
            signals = self.extract_signals_from_data(data_type, df)
            
            if not signals.empty:
                # Group by strategy type
                for strategy in signals['signal_type'].unique():
                    strategy_signals = signals[signals['signal_type'] == strategy]
                    
                    if strategy not in all_strategies:
                        all_strategies[strategy] = []
                    
                    all_strategies[strategy].append(strategy_signals)
        
        # Create comparison visualization
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Signal Distribution by Strategy',
                'Average Confidence by Strategy',
                'Strategy Performance Over Time',
                'Combined Strategy Signals'
            ]
        )
        
        # Plot signal distribution
        if all_strategies:
            strategy_names = list(all_strategies.keys())
            signal_counts = []
            
            for strategy in strategy_names:
                combined_df = pd.concat(all_strategies[strategy], ignore_index=True)
                signal_dist = combined_df['signal'].value_counts()
                signal_counts.append(signal_dist)
            
            # Bar chart for signal distribution
            signals_types = ['BUY', 'SELL', 'HOLD']
            for i, signal_type in enumerate(signals_types):
                counts = [sc.get(signal_type, 0) for sc in signal_counts]
                fig.add_trace(
                    go.Bar(
                        x=strategy_names,
                        y=counts,
                        name=signal_type,
                        marker_color=['green', 'red', 'blue'][i]
                    ),
                    row=1, col=1
                )
            
            # Average confidence by strategy
            avg_confidence = []
            for strategy in strategy_names:
                combined_df = pd.concat(all_strategies[strategy], ignore_index=True)
                avg_conf = combined_df['confidence'].mean()
                avg_confidence.append(avg_conf)
            
            fig.add_trace(
                go.Bar(
                    x=strategy_names,
                    y=avg_confidence,
                    name='Avg Confidence',
                    marker_color='orange'
                ),
                row=1, col=2
            )
            
            # Performance over time (simplified)
            for strategy in strategy_names:
                combined_df = pd.concat(all_strategies[strategy], ignore_index=True)
                combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'], utc=True).dt.tz_localize(None)
                time_series = combined_df.groupby(combined_df['timestamp'].dt.date)['confidence'].mean()
                
                fig.add_trace(
                    go.Scatter(
                        x=list(time_series.index),
                        y=list(time_series.values),
                        mode='lines+markers',
                        name=f'{strategy} Performance'
                    ),
                    row=2, col=1
                )
            
            # Combined strategy (smoothed)
            all_signals_combined = pd.concat([pd.concat(sigs, ignore_index=True) for sigs in all_strategies.values()], ignore_index=True)
            all_signals_combined['timestamp'] = pd.to_datetime(all_signals_combined['timestamp'], utc=True).dt.tz_localize(None)
            
            # Create smoothed composite signal
            daily_composite = all_signals_combined.groupby([
                all_signals_combined['timestamp'].dt.date,
                'symbol'
            ]).agg({
                'confidence': 'mean',
                'sentiment_score': 'mean'
            }).reset_index()
            
            # Calculate composite score
            daily_composite['composite_score'] = (daily_composite['confidence'] * 0.7 + 
                                                abs(daily_composite['sentiment_score']) * 0.3)
            
            # Smooth the composite score
            daily_composite = daily_composite.sort_values('timestamp')
            daily_composite['smoothed_composite'] = daily_composite['composite_score'].rolling(window=3, center=True).mean()
            
            # Plot smoothed composite
            for symbol in self.bank_symbols:
                symbol_data = daily_composite[daily_composite['symbol'] == symbol]
                if not symbol_data.empty:
                    fig.add_trace(
                        go.Scatter(
                            x=symbol_data['timestamp'],
                            y=symbol_data['smoothed_composite'],
                            mode='lines',
                            name=f'{symbol} Composite',
                            line=dict(width=2)
                        ),
                        row=2, col=2
                    )
        
        fig.update_layout(
            title='Trading Strategy Comparison & Performance Analysis',
            height=600,
            showlegend=True
        )
        
        return fig
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            'summary': {},
            'strategy_metrics': {},
            'backtesting_results': {}
        }
        
        # Load and analyze all data
        sentiment_data = self.load_sentiment_data()
        
        if not sentiment_data:
            report['summary']['status'] = 'No data available'
            return report
        
        # Process signals for each strategy
        all_signals = []
        for data_type, df in sentiment_data:
            signals = self.extract_signals_from_data(data_type, df)
            all_signals.append((data_type, signals))
        
        # Calculate basic metrics
        total_signals = sum(len(signals) for _, signals in all_signals)
        
        report['summary'] = {
            'total_signals_generated': total_signals,
            'data_sources': len(sentiment_data),
            'analysis_period': '3 months',
            'symbols_covered': len(self.bank_symbols)
        }
        
        # Strategy-specific metrics
        for data_type, signals in all_signals:
            if not signals.empty:
                strategy_report = {
                    'total_signals': len(signals),
                    'signal_distribution': signals['signal'].value_counts().to_dict(),
                    'average_confidence': signals['confidence'].mean(),
                    'confidence_std': signals['confidence'].std(),
                    'symbols_active': len(signals['symbol'].unique())
                }
                report['strategy_metrics'][data_type] = strategy_report
        
        return report
    
    def run_full_backtest(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run comprehensive backtest for specified symbols"""
        if symbols is None:
            symbols = self.bank_symbols
        
        results = {
            'visualizations': {},
            'performance_report': self.generate_performance_report(),
            'strategy_comparison': None,
            'individual_analyses': {}
        }
        
        # Generate individual symbol analyses
        for symbol in symbols:
            print(f"Processing {symbol}...")
            
            # Create comprehensive visualization
            fig = self.create_price_visualization(symbol)
            
            # Save visualization
            output_file = self.results_dir / f"{symbol}_comprehensive_backtest.html"
            fig.write_html(str(output_file))
            results['visualizations'][symbol] = str(output_file)
            
            # Generate basic performance metrics
            price_data = self.fetch_historical_prices(symbol, period="3mo")
            if not price_data.empty:
                analysis = {
                    'price_change_3m': ((price_data['Close'].iloc[-1] - price_data['Close'].iloc[0]) / price_data['Close'].iloc[0]) * 100,
                    'volatility': price_data['Close'].pct_change().std() * np.sqrt(252) * 100,
                    'max_price': price_data['Close'].max(),
                    'min_price': price_data['Close'].min(),
                    'current_price': price_data['Close'].iloc[-1]
                }
                results['individual_analyses'][symbol] = analysis
        
        # Create strategy comparison
        print("Creating strategy comparison...")
        comparison_fig = self.create_strategy_comparison()
        comparison_file = self.results_dir / "strategy_comparison.html"
        comparison_fig.write_html(str(comparison_file))
        results['strategy_comparison'] = str(comparison_file)
        
        return results

def main():
    """Main execution function"""
    backtester = ComprehensiveBacktester()
    
    print("Starting comprehensive backtesting analysis...")
    print(f"Results will be saved to: {backtester.results_dir}")
    
    # Run full backtest
    results = backtester.run_full_backtest()
    
    # Print summary
    print("\n" + "="*50)
    print("BACKTESTING RESULTS SUMMARY")
    print("="*50)
    
    if results['performance_report']['summary']:
        summary = results['performance_report']['summary']
        print(f"Total Signals Generated: {summary.get('total_signals_generated', 0)}")
        print(f"Data Sources Used: {summary.get('data_sources', 0)}")
        print(f"Symbols Analyzed: {summary.get('symbols_covered', 0)}")
        print(f"Analysis Period: {summary.get('analysis_period', 'N/A')}")
    
    print(f"\nVisualization files created:")
    for symbol, file_path in results['visualizations'].items():
        print(f"  {symbol}: {file_path}")
    
    if results['strategy_comparison']:
        print(f"  Strategy Comparison: {results['strategy_comparison']}")
    
    print(f"\nIndividual Performance Analysis:")
    for symbol, analysis in results['individual_analyses'].items():
        print(f"  {symbol}:")
        print(f"    3-month return: {analysis.get('price_change_3m', 0):.2f}%")
        print(f"    Volatility: {analysis.get('volatility', 0):.2f}%")
        print(f"    Current price: ${analysis.get('current_price', 0):.2f}")
    
    return results

if __name__ == "__main__":
    main()