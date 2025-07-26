#!/usr/bin/env python3
"""
Enhanced Multi-Bank Data Collection and Analysis System

This module collects comprehensive data for multiple Australian bank symbols,
generates diverse sentiment scenarios, and provides ML predictions.

Australian Bank Symbols Covered:
- Big 4: CBA.AX, ANZ.AX, WBC.AX, NAB.AX  
- Investment: MQG.AX (Macquarie Group)
- Regional: BOQ.AX (Bank of Queensland), BEN.AX (Bendigo Bank)
- Insurance: SUN.AX (Suncorp), QBE.AX (QBE Insurance)
- Finance: AMP.AX (AMP Limited), ASX.AX (ASX Limited)
"""

import logging
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import sqlite3
import json
import time
import random
from typing import Dict, List, Tuple, Optional
import sys
import os

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline

class MultiBankDataCollector:
    """Comprehensive data collector for multiple Australian bank symbols"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.setup_logging()
        
        # Enhanced Australian financial institutions
        self.bank_symbols = {
            # Big 4 Banks
            'CBA.AX': {
                'name': 'Commonwealth Bank',
                'sector': 'Major Bank',
                'market_cap': 'Large',
                'sentiment_bias': 'neutral'
            },
            'ANZ.AX': {
                'name': 'ANZ Bank',
                'sector': 'Major Bank', 
                'market_cap': 'Large',
                'sentiment_bias': 'slightly_positive'
            },
            'WBC.AX': {
                'name': 'Westpac',
                'sector': 'Major Bank',
                'market_cap': 'Large', 
                'sentiment_bias': 'neutral'
            },
            'NAB.AX': {
                'name': 'National Australia Bank',
                'sector': 'Major Bank',
                'market_cap': 'Large',
                'sentiment_bias': 'slightly_negative'
            },
            
            # Investment Banking
            'MQG.AX': {
                'name': 'Macquarie Group',
                'sector': 'Investment Bank',
                'market_cap': 'Large',
                'sentiment_bias': 'positive'
            },
            
            # Regional Banks
            'BOQ.AX': {
                'name': 'Bank of Queensland',
                'sector': 'Regional Bank',
                'market_cap': 'Medium',
                'sentiment_bias': 'neutral'
            },
            'BEN.AX': {
                'name': 'Bendigo Bank',
                'sector': 'Regional Bank',
                'market_cap': 'Small',
                'sentiment_bias': 'positive'
            },
            
            # Insurance & Finance
            'SUN.AX': {
                'name': 'Suncorp',
                'sector': 'Insurance',
                'market_cap': 'Medium',
                'sentiment_bias': 'neutral'
            },
            'QBE.AX': {
                'name': 'QBE Insurance',
                'sector': 'Insurance',
                'market_cap': 'Large',
                'sentiment_bias': 'negative'
            },
            'AMP.AX': {
                'name': 'AMP Limited',
                'sector': 'Wealth Management',
                'market_cap': 'Medium',
                'sentiment_bias': 'negative'
            },
            
            # Financial Services
            'ASX.AX': {
                'name': 'ASX Limited',
                'sector': 'Exchange',
                'market_cap': 'Large',
                'sentiment_bias': 'positive'
            }
        }
        
        # Initialize ML pipeline
        self.ml_pipeline = EnhancedMLTrainingPipeline()
        
        # Database setup
        self.db_path = 'data/multi_bank_analysis.db'
        self.init_database()
        
    def setup_logging(self):
        """Configure logging for the collector"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data/multi_bank_collector.log'),
                logging.StreamHandler()
            ]
        )
        
    def init_database(self):
        """Initialize database tables for multi-bank analysis"""
        os.makedirs('data', exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Bank performance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bank_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    bank_name TEXT NOT NULL,
                    sector TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    current_price REAL,
                    price_change_1d REAL,
                    price_change_5d REAL,
                    price_change_30d REAL,
                    volume REAL,
                    market_cap_tier TEXT,
                    
                    -- Technical indicators
                    rsi REAL,
                    macd_signal TEXT,
                    sma_20 REAL,
                    sma_50 REAL,
                    bollinger_position TEXT,
                    
                    -- Sentiment analysis
                    sentiment_score REAL,
                    sentiment_confidence REAL,
                    news_count INTEGER,
                    sentiment_category TEXT,
                    
                    -- ML predictions
                    predicted_direction TEXT,
                    predicted_magnitude REAL,
                    prediction_confidence REAL,
                    optimal_action TEXT,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # News sentiment table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS news_sentiment_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    headline TEXT NOT NULL,
                    sentiment_score REAL,
                    confidence REAL,
                    category TEXT,
                    source TEXT,
                    timestamp TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ML model performance tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ml_performance_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    prediction_date TEXT NOT NULL,
                    predicted_direction TEXT,
                    predicted_magnitude REAL,
                    actual_direction TEXT,
                    actual_magnitude REAL,
                    accuracy_score REAL,
                    model_version TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            self.logger.info("Database initialized successfully")
    
    def generate_diverse_sentiment_scenarios(self, symbol: str, count: int = 5) -> List[Dict]:
        """Generate diverse sentiment scenarios for a bank symbol"""
        bank_info = self.bank_symbols[symbol]
        bank_name = bank_info['name']
        sector = bank_info['sector']
        bias = bank_info['sentiment_bias']
        
        # Sentiment templates with diverse scenarios
        sentiment_templates = {
            'very_positive': [
                f"{bank_name} announces record quarterly profit beating analyst expectations",
                f"{bank_name} successfully launches innovative digital banking platform",
                f"{bank_name} wins major industry award for customer service excellence",
                f"{bank_name} expands international operations with strategic acquisition",
                f"{bank_name} reports strong mortgage growth and improved net interest margins"
            ],
            'positive': [
                f"{bank_name} increases dividend payout following solid earnings",
                f"{bank_name} strengthens capital position with successful bond issuance",
                f"{bank_name} partners with fintech to enhance digital offerings",
                f"{bank_name} reports improved operational efficiency metrics",
                f"{bank_name} receives regulatory approval for new business venture"
            ],
            'neutral': [
                f"{bank_name} releases quarterly update meeting market expectations",
                f"{bank_name} announces new branch locations in regional areas",
                f"{bank_name} updates shareholders on strategic transformation progress",
                f"{bank_name} participates in industry sustainability initiative",
                f"{bank_name} maintains stable credit ratings from major agencies"
            ],
            'negative': [
                f"{bank_name} faces increased scrutiny over lending practices",
                f"{bank_name} reports higher than expected loan loss provisions",
                f"{bank_name} dealing with customer complaints over service disruptions",
                f"{bank_name} under investigation for potential compliance issues",
                f"{bank_name} experiencing pressure from rising funding costs"
            ],
            'very_negative': [
                f"{bank_name} hit with major regulatory fine for misconduct",
                f"{bank_name} suffers significant data breach affecting thousands",
                f"{bank_name} announces major restructuring with job losses",
                f"{bank_name} faces class action lawsuit from shareholders",
                f"{bank_name} reports unexpected quarterly loss amid market turmoil"
            ]
        }
        
        # Sentiment score ranges
        sentiment_ranges = {
            'very_positive': (0.6, 0.9),
            'positive': (0.2, 0.6),
            'neutral': (-0.2, 0.2),
            'negative': (-0.6, -0.2),
            'very_negative': (-0.9, -0.6)
        }
        
        scenarios = []
        categories = list(sentiment_templates.keys())
        
        # Apply sentiment bias
        if bias == 'positive':
            weights = [0.3, 0.3, 0.2, 0.15, 0.05]  # Favor positive
        elif bias == 'negative':
            weights = [0.05, 0.15, 0.2, 0.3, 0.3]  # Favor negative  
        elif bias == 'slightly_positive':
            weights = [0.2, 0.3, 0.3, 0.15, 0.05]
        elif bias == 'slightly_negative':
            weights = [0.05, 0.15, 0.3, 0.3, 0.2]
        else:  # neutral
            weights = [0.15, 0.25, 0.3, 0.25, 0.05]
        
        for i in range(count):
            # Select sentiment category based on bias
            category = np.random.choice(categories, p=weights)
            
            # Select random headline from category
            headline = random.choice(sentiment_templates[category])
            
            # Generate sentiment score within range
            score_min, score_max = sentiment_ranges[category]
            sentiment_score = round(random.uniform(score_min, score_max), 3)
            
            # Generate confidence (higher for extreme sentiments)
            if category in ['very_positive', 'very_negative']:
                confidence = round(random.uniform(0.8, 0.95), 3)
            elif category in ['positive', 'negative']:
                confidence = round(random.uniform(0.6, 0.8), 3)
            else:
                confidence = round(random.uniform(0.4, 0.7), 3)
            
            scenarios.append({
                'headline': headline,
                'sentiment_score': sentiment_score,
                'confidence': confidence,
                'category': category,
                'symbol': symbol,
                'bank_name': bank_name,
                'timestamp': datetime.now().isoformat()
            })
            
        return scenarios
    
    def collect_market_data(self, symbol: str, period: str = '1mo') -> Optional[pd.DataFrame]:
        """Collect market data for a symbol"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval='1d')
            
            if data.empty:
                self.logger.warning(f"No market data available for {symbol}")
                return None
                
            return data
            
        except Exception as e:
            self.logger.error(f"Error collecting market data for {symbol}: {e}")
            return None
    
    def analyze_bank_comprehensive(self, symbol: str) -> Dict:
        """Perform comprehensive analysis for a single bank"""
        bank_info = self.bank_symbols[symbol]
        
        # Collect market data
        market_data = self.collect_market_data(symbol)
        if market_data is None:
            return {'error': f'No market data available for {symbol}'}
        
        # Calculate technical indicators
        latest_data = market_data.iloc[-1]
        
        # Price metrics
        current_price = round(latest_data['Close'], 2)
        if len(market_data) >= 2:
            price_change_1d = round(((current_price - market_data.iloc[-2]['Close']) / market_data.iloc[-2]['Close']) * 100, 2)
        else:
            price_change_1d = 0
            
        if len(market_data) >= 5:
            price_change_5d = round(((current_price - market_data.iloc[-6]['Close']) / market_data.iloc[-6]['Close']) * 100, 2)
        else:
            price_change_5d = 0
            
        if len(market_data) >= 20:
            price_change_30d = round(((current_price - market_data.iloc[-21]['Close']) / market_data.iloc[-21]['Close']) * 100, 2)
        else:
            price_change_30d = 0
        
        # Technical indicators
        closes = market_data['Close']
        
        # RSI calculation
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = round(100 - (100 / (1 + rs)).iloc[-1], 2)
        
        # Moving averages
        sma_20 = round(closes.rolling(20).mean().iloc[-1], 2) if len(closes) >= 20 else current_price
        sma_50 = round(closes.rolling(50).mean().iloc[-1], 2) if len(closes) >= 50 else current_price
        
        # Bollinger Bands position
        if len(closes) >= 20:
            bb_middle = closes.rolling(20).mean()
            bb_std = closes.rolling(20).std()
            bb_upper = bb_middle + (bb_std * 2)
            bb_lower = bb_middle - (bb_std * 2)
            
            if current_price > bb_upper.iloc[-1]:
                bb_position = 'Above Upper'
            elif current_price < bb_lower.iloc[-1]:
                bb_position = 'Below Lower'
            else:
                bb_position = 'Within Bands'
        else:
            bb_position = 'Insufficient Data'
        
        # MACD signal
        macd_signal = 'BUY' if rsi < 30 else 'SELL' if rsi > 70 else 'HOLD'
        
        # Generate sentiment scenarios
        sentiment_scenarios = self.generate_diverse_sentiment_scenarios(symbol, count=3)
        
        # Use most recent sentiment for ML prediction
        primary_sentiment = sentiment_scenarios[0]
        
        # Prepare sentiment data for ML
        sentiment_data = {
            'overall_sentiment': primary_sentiment['sentiment_score'],
            'confidence': primary_sentiment['confidence'],
            'news_count': len(sentiment_scenarios),
            'sentiment_components': {
                'financial': primary_sentiment['sentiment_score'],
                'operational': primary_sentiment['sentiment_score'] * 0.8,
                'market': primary_sentiment['sentiment_score'] * 1.1
            },
            'timestamp': primary_sentiment['timestamp']
        }
        
        # Get ML prediction
        try:
            ml_prediction = self.ml_pipeline.predict_enhanced(sentiment_data, symbol)
            predicted_direction = ml_prediction.get('optimal_action', 'HOLD')
            predicted_magnitude = ml_prediction.get('magnitude_predictions', {}).get('1d', 0.0)
            prediction_confidence = ml_prediction.get('confidence_scores', {}).get('average', 0.5)
        except Exception as e:
            self.logger.error(f"ML prediction failed for {symbol}: {e}")
            predicted_direction = 'HOLD'
            predicted_magnitude = 0.0
            prediction_confidence = 0.3
        
        # Compile comprehensive analysis
        analysis = {
            'symbol': symbol,
            'bank_name': bank_info['name'],
            'sector': bank_info['sector'],
            'timestamp': datetime.now().isoformat(),
            
            # Price data
            'current_price': current_price,
            'price_change_1d': price_change_1d,
            'price_change_5d': price_change_5d,
            'price_change_30d': price_change_30d,
            'volume': int(latest_data['Volume']),
            'market_cap_tier': bank_info['market_cap'],
            
            # Technical indicators
            'rsi': rsi,
            'macd_signal': macd_signal,
            'sma_20': sma_20,
            'sma_50': sma_50,
            'bollinger_position': bb_position,
            
            # Sentiment analysis
            'sentiment_score': primary_sentiment['sentiment_score'],
            'sentiment_confidence': primary_sentiment['confidence'],
            'news_count': len(sentiment_scenarios),
            'sentiment_category': primary_sentiment['category'],
            'all_sentiment_scenarios': sentiment_scenarios,
            
            # ML predictions
            'predicted_direction': predicted_direction,
            'predicted_magnitude': predicted_magnitude,
            'prediction_confidence': prediction_confidence,
            'optimal_action': predicted_direction
        }
        
        return analysis
    
    def collect_all_banks_data(self) -> List[Dict]:
        """Collect comprehensive data for all bank symbols"""
        all_analyses = []
        
        self.logger.info(f"Starting comprehensive analysis for {len(self.bank_symbols)} banks")
        
        for symbol in self.bank_symbols.keys():
            self.logger.info(f"Analyzing {symbol}...")
            
            try:
                analysis = self.analyze_bank_comprehensive(symbol)
                
                if 'error' not in analysis:
                    all_analyses.append(analysis)
                    
                    # Store in database
                    self.store_analysis_to_db(analysis)
                    
                    self.logger.info(f"✅ {symbol}: Price=${analysis['current_price']}, "
                                   f"Sentiment={analysis['sentiment_score']:.2f}, "
                                   f"Action={analysis['optimal_action']}")
                else:
                    self.logger.warning(f"❌ {symbol}: {analysis['error']}")
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error analyzing {symbol}: {e}")
                continue
        
        self.logger.info(f"Completed analysis for {len(all_analyses)} banks")
        return all_analyses
    
    def store_analysis_to_db(self, analysis: Dict):
        """Store analysis results in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Store main performance data
                cursor.execute('''
                    INSERT INTO bank_performance (
                        symbol, bank_name, sector, timestamp, current_price,
                        price_change_1d, price_change_5d, price_change_30d, volume,
                        market_cap_tier, rsi, macd_signal, sma_20, sma_50,
                        bollinger_position, sentiment_score, sentiment_confidence,
                        news_count, sentiment_category, predicted_direction,
                        predicted_magnitude, prediction_confidence, optimal_action
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis['symbol'], analysis['bank_name'], analysis['sector'],
                    analysis['timestamp'], analysis['current_price'],
                    analysis['price_change_1d'], analysis['price_change_5d'],
                    analysis['price_change_30d'], analysis['volume'],
                    analysis['market_cap_tier'], analysis['rsi'],
                    analysis['macd_signal'], analysis['sma_20'], analysis['sma_50'],
                    analysis['bollinger_position'], analysis['sentiment_score'],
                    analysis['sentiment_confidence'], analysis['news_count'],
                    analysis['sentiment_category'], analysis['predicted_direction'],
                    analysis['predicted_magnitude'], analysis['prediction_confidence'],
                    analysis['optimal_action']
                ))
                
                # Store sentiment scenarios
                for scenario in analysis['all_sentiment_scenarios']:
                    cursor.execute('''
                        INSERT INTO news_sentiment_analysis (
                            symbol, headline, sentiment_score, confidence,
                            category, source, timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        analysis['symbol'], scenario['headline'],
                        scenario['sentiment_score'], scenario['confidence'],
                        scenario['category'], 'Generated', scenario['timestamp']
                    ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error storing analysis to database: {e}")
    
    def get_summary_statistics(self) -> Dict:
        """Get summary statistics from collected data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Overall performance summary
                df = pd.read_sql_query('''
                    SELECT 
                        symbol, bank_name, sector, current_price,
                        price_change_1d, sentiment_score, predicted_direction,
                        optimal_action, timestamp
                    FROM bank_performance 
                    ORDER BY timestamp DESC
                ''', conn)
                
                if df.empty:
                    return {'error': 'No data available'}
                
                # Get latest data for each bank
                latest_data = df.groupby('symbol').first().reset_index()
                
                summary = {
                    'total_banks_analyzed': len(latest_data),
                    'analysis_timestamp': latest_data['timestamp'].iloc[0] if not latest_data.empty else None,
                    
                    # Price performance
                    'avg_price_change_1d': round(latest_data['price_change_1d'].mean(), 2),
                    'best_performer': {
                        'symbol': latest_data.loc[latest_data['price_change_1d'].idxmax(), 'symbol'],
                        'change': round(latest_data['price_change_1d'].max(), 2)
                    },
                    'worst_performer': {
                        'symbol': latest_data.loc[latest_data['price_change_1d'].idxmin(), 'symbol'],
                        'change': round(latest_data['price_change_1d'].min(), 2)
                    },
                    
                    # Sentiment analysis
                    'avg_sentiment': round(latest_data['sentiment_score'].mean(), 3),
                    'most_positive_sentiment': {
                        'symbol': latest_data.loc[latest_data['sentiment_score'].idxmax(), 'symbol'],
                        'sentiment': round(latest_data['sentiment_score'].max(), 3)
                    },
                    'most_negative_sentiment': {
                        'symbol': latest_data.loc[latest_data['sentiment_score'].idxmin(), 'symbol'],
                        'sentiment': round(latest_data['sentiment_score'].min(), 3)
                    },
                    
                    # ML predictions
                    'action_distribution': latest_data['optimal_action'].value_counts().to_dict(),
                    'sector_performance': latest_data.groupby('sector')['price_change_1d'].mean().round(2).to_dict(),
                    
                    # Recent data sample
                    'recent_analyses': latest_data[['symbol', 'bank_name', 'current_price', 
                                                  'price_change_1d', 'sentiment_score', 
                                                  'optimal_action']].to_dict('records')
                }
                
                return summary
                
        except Exception as e:
            self.logger.error(f"Error generating summary statistics: {e}")
            return {'error': str(e)}

def main():
    """Main execution function"""
    print("🏦 Enhanced Multi-Bank Data Collection System")
    print("=" * 60)
    
    # Initialize collector
    collector = MultiBankDataCollector()
    
    # Collect comprehensive data for all banks
    print(f"📊 Analyzing {len(collector.bank_symbols)} Australian financial institutions...")
    all_analyses = collector.collect_all_banks_data()
    
    if not all_analyses:
        print("❌ No data collected")
        return
    
    # Generate summary statistics
    print("\n📈 Generating summary statistics...")
    summary = collector.get_summary_statistics()
    
    if 'error' in summary:
        print(f"❌ Error generating summary: {summary['error']}")
        return
    
    # Display results
    print(f"\n🎯 ANALYSIS SUMMARY")
    print(f"{'='*50}")
    print(f"📊 Banks Analyzed: {summary['total_banks_analyzed']}")
    print(f"⏰ Analysis Time: {summary['analysis_timestamp']}")
    print(f"📈 Avg 1D Change: {summary['avg_price_change_1d']}%")
    print(f"😊 Avg Sentiment: {summary['avg_sentiment']}")
    
    print(f"\n🏆 TOP PERFORMERS:")
    print(f"   📈 Best: {summary['best_performer']['symbol']} (+{summary['best_performer']['change']}%)")
    print(f"   📉 Worst: {summary['worst_performer']['symbol']} ({summary['worst_performer']['change']}%)")
    
    print(f"\n💭 SENTIMENT ANALYSIS:")
    print(f"   😊 Most Positive: {summary['most_positive_sentiment']['symbol']} ({summary['most_positive_sentiment']['sentiment']})")
    print(f"   😟 Most Negative: {summary['most_negative_sentiment']['symbol']} ({summary['most_negative_sentiment']['sentiment']})")
    
    print(f"\n🤖 ML PREDICTIONS:")
    for action, count in summary['action_distribution'].items():
        print(f"   {action}: {count} banks")
    
    print(f"\n🏢 SECTOR PERFORMANCE:")
    for sector, performance in summary['sector_performance'].items():
        print(f"   {sector}: {performance}%")
    
    print(f"\n💾 Data saved to: {collector.db_path}")
    print(f"📋 Log file: data/multi_bank_collector.log")
    print(f"\n✅ Multi-bank analysis completed successfully!")

if __name__ == "__main__":
    main()
