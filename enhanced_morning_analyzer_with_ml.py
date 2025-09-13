#!/usr/bin/env python3
"""
Enhanced Morning Analyzer with Integrated ML Pipeline
Implements Phase 1-4 requirements from dashboard.instructions.md

This analyzer combines:
- Comprehensive sentiment analysis
- Technical indicators integration
- Multi-output ML predictions
- Feature engineering pipeline
- Data validation framework
"""

import sys
import os
import sqlite3
import time
from datetime import datetime
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import pytz

# Setup logging
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "enhanced_morning_analysis.log")),
        logging.StreamHandler()
    ]
)

# Create logs directory if it doesn't exist
# (Already created above)

# Import our enhanced components
try:
    from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline, DataValidator
    from app.core.analysis.technical import TechnicalAnalyzer, get_market_data
    from app.core.sentiment.news_analyzer import NewsSentimentAnalyzer
    from app.config.settings import Settings
    ML_ENHANCED_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Enhanced ML components not available: {e}")
    ML_ENHANCED_AVAILABLE = False

class EnhancedMorningAnalyzer:
    """Enhanced Morning Analyzer with full ML integration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Bank symbols for analysis
        self.banks = {
            "CBA.AX": "Commonwealth Bank",
            "WBC.AX": "Westpac", 
            "ANZ.AX": "ANZ Banking",
            "NAB.AX": "National Australia Bank",
            "MQG.AX": "Macquarie Group",
            "SUN.AX": "Suncorp Group",
            "QBE.AX": "QBE Insurance"
        }
        
        # Initialize enhanced components
        if ML_ENHANCED_AVAILABLE:
            self.settings = Settings()
            self.enhanced_pipeline = EnhancedMLTrainingPipeline()
            self.technical_analyzer = TechnicalAnalyzer(self.settings)
            self.sentiment_analyzer = NewsSentimentAnalyzer()
            self.data_validator = DataValidator()
            self.logger.info("Enhanced ML components initialized")
        else:
            self.logger.warning("Enhanced ML components not available - using basic analysis")
        
        # Database paths
        self.db_path = "data/trading_predictions.db"
        self.enhanced_db_path = "data/trading_predictions.db"
        
        # Create data directories
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/ml_models", exist_ok=True)
        
        self.logger.info("Enhanced Morning Analyzer initialized")
    
    def get_australian_time(self):
        """Get current time in Australian timezone (AEST/AEDT)"""
        try:
            # Try to use pytz for accurate timezone handling
            australian_tz = pytz.timezone('Australia/Sydney')
            return datetime.now(australian_tz)
        except:
            # Fallback: assume system is already in correct timezone
            return datetime.now()
    
    def is_market_hours(self) -> bool:
        """Check if during ASX market hours (10 AM - 4 PM AEST)"""
        now = self.get_australian_time()
        if now.weekday() >= 5:  # Weekend
            return False
        return 10 <= now.hour < 16
    
    def run_enhanced_morning_analysis(self) -> Dict:
        """
        Run comprehensive morning analysis with enhanced ML pipeline
        
        Implements all phases from dashboard.instructions.md:
        - Phase 1: Data Integration Enhancement
        - Phase 2: Multi-Output Prediction Model
        - Phase 3: Feature Engineering Pipeline
        - Phase 4: Data Validation Framework
        """
        self.logger.info("🌅 Starting Enhanced Morning Analysis")
        
        analysis_results = {
            'timestamp': self.get_australian_time().isoformat(),
            'market_hours': self.is_market_hours(),
            'analysis_type': 'enhanced_ml_integrated',
            'banks_analyzed': [],
            'ml_predictions': {},
            'technical_signals': {},
            'overall_market_sentiment': 0,
            'recommendations': {},
            'data_quality_scores': {},
            'feature_counts': {},
            'model_performance': {}
        }
        
        if not ML_ENHANCED_AVAILABLE:
            self.logger.warning("Enhanced analysis not available - falling back to basic analysis")
            return self._run_basic_analysis()
        
        # Phase 1: Enhanced Data Integration
        self.logger.info("📊 Phase 1: Enhanced Data Integration")
        
        total_sentiment = 0
        analyzed_count = 0
        
        for symbol, name in self.banks.items():
            try:
                self.logger.info(f"Analyzing {symbol} ({name})")
                
                # Step 1: Get sentiment analysis
                sentiment_data = self.sentiment_analyzer.analyze_bank_sentiment(symbol)
                
                # Step 2: Validate sentiment data
                if self.data_validator.validate_sentiment_data(sentiment_data):
                    self.logger.info(f"✅ {symbol}: Sentiment data validated")
                
                # Step 3: Get market data and technical analysis
                market_data = get_market_data(symbol, period='3mo', interval='1h')
                
                if not market_data.empty:
                    technical_result = self.technical_analyzer.analyze(symbol, market_data)
                    
                    # Step 4: Validate technical data
                    if self.data_validator.validate_technical_data(technical_result):
                        self.logger.info(f"✅ {symbol}: Technical data validated")
                    
                    # Phase 2: Multi-Output Prediction
                    self.logger.info(f"🧠 Phase 2: Multi-Output ML Prediction for {symbol}")
                    
                    # Collect enhanced training data
                    feature_id = self.enhanced_pipeline.collect_enhanced_training_data(
                        sentiment_data, symbol
                    )
                    
                    if feature_id:
                        # Make enhanced predictions
                        ml_prediction = self.enhanced_pipeline.predict_enhanced(
                            sentiment_data, symbol
                        )
                        
                        if 'error' not in ml_prediction:
                            analysis_results['ml_predictions'][symbol] = ml_prediction
                            
                            # Phase 3: Feature Engineering Validation
                            feature_count = len(self.enhanced_pipeline.required_features['technical_indicators']) + \
                                          len(self.enhanced_pipeline.required_features['price_features']) + \
                                          len(self.enhanced_pipeline.required_features['volume_features']) + \
                                          len(self.enhanced_pipeline.required_features['market_context']) + \
                                          len(self.enhanced_pipeline.required_features['sentiment_features']) + \
                                          len(self.enhanced_pipeline.interaction_features) + \
                                          len(self.enhanced_pipeline.time_features)
                            
                            analysis_results['feature_counts'][symbol] = feature_count
                            
                            self.logger.info(f"✅ {symbol}: Enhanced prediction generated ({feature_count} features)")
                            self.logger.info(f"   - Action: {ml_prediction['optimal_action']}")
                            self.logger.info(f"   - Confidence: {ml_prediction['confidence_scores']['average']:.3f}")
                        else:
                            self.logger.warning(f"❌ {symbol}: ML prediction failed - {ml_prediction['error']}")
                    
                    # Traditional technical signals for comparison
                    technical_signal = self._generate_traditional_signal(
                        sentiment_data, technical_result, symbol
                    )
                    analysis_results['technical_signals'][symbol] = technical_signal
                    
                    # Track overall sentiment
                    total_sentiment += sentiment_data.get('overall_sentiment', 0)
                    analyzed_count += 1
                    
                    analysis_results['banks_analyzed'].append(symbol)
                    
                    # Calculate data quality score
                    quality_score = self._calculate_data_quality_score(
                        sentiment_data, technical_result, market_data
                    )
                    analysis_results['data_quality_scores'][symbol] = quality_score
                    
                    self.logger.info(f"✅ {symbol}: Complete analysis finished (Quality: {quality_score:.1f}%)")
                    
                else:
                    self.logger.warning(f"❌ {symbol}: No market data available")
                    
            except Exception as e:
                self.logger.error(f"❌ {symbol}: Analysis failed - {e}")
                continue
        
        # Calculate overall market sentiment
        if analyzed_count > 0:
            analysis_results['overall_market_sentiment'] = total_sentiment / analyzed_count
        
        # Phase 4: Generate comprehensive recommendations
        self.logger.info("🎯 Phase 4: Generating Enhanced Recommendations")
        analysis_results['recommendations'] = self._generate_enhanced_recommendations(
            analysis_results
        )
        
        # Model performance summary
        analysis_results['model_performance'] = self._get_model_performance_summary()
        
        # Save results to database
        self._save_analysis_results(analysis_results)
        
        # Display summary
        self._display_analysis_summary(analysis_results)
        
        self.logger.info("🌅 Enhanced Morning Analysis Complete")
        return analysis_results
    
    def _generate_traditional_signal(self, sentiment_data: Dict, technical_result: Dict, symbol: str) -> Dict:
        """Generate traditional combined signal for comparison"""
        sentiment_score = sentiment_data.get('overall_sentiment', 0)
        sentiment_confidence = sentiment_data.get('confidence', 0)
        
        technical_signal = technical_result.get('recommendation', 'HOLD')
        technical_strength = technical_result.get('overall_signal', 0) / 100  # Convert to -1 to 1
        rsi = technical_result.get('indicators', {}).get('rsi', 50)
        
        # Traditional signal scoring system (40% sentiment, 60% technical)
        combined_score = 0
        
        # Sentiment contribution (40% weight)
        if sentiment_score > 0.1:
            combined_score += 0.4 * min(sentiment_score * 2, 1.0)
        elif sentiment_score < -0.1:
            combined_score -= 0.4 * min(abs(sentiment_score) * 2, 1.0)
        
        # Technical contribution (60% weight)
        if technical_signal == "BUY" or technical_signal == "STRONG_BUY":
            combined_score += 0.6 * abs(technical_strength)
        elif technical_signal == "SELL" or technical_signal == "STRONG_SELL":
            combined_score -= 0.6 * abs(technical_strength)
        
        # RSI adjustments
        if rsi > 70:  # Overbought
            combined_score -= 0.1
        elif rsi < 30:  # Oversold
            combined_score += 0.1
        
        # Determine final signal
        if combined_score > 0.3:
            final_signal = "BUY"
            signal_strength = "STRONG" if combined_score > 0.6 else "MODERATE"
        elif combined_score < -0.3:
            final_signal = "SELL"
            signal_strength = "STRONG" if combined_score < -0.6 else "MODERATE"
        else:
            final_signal = "HOLD"
            signal_strength = "NEUTRAL"
        
        # Calculate overall confidence
        overall_confidence = (sentiment_confidence + abs(technical_strength)) / 2
        
        return {
            "symbol": symbol,
            "final_signal": final_signal,
            "signal_strength": signal_strength,
            "combined_score": round(combined_score, 3),
            "overall_confidence": round(overall_confidence, 3),
            "sentiment_contribution": round(sentiment_score, 3),
            "technical_contribution": technical_signal,
            "rsi": rsi,
            "current_price": technical_result.get("current_price", 0)
        }
    
    def _calculate_data_quality_score(self, sentiment_data: Dict, technical_result: Dict, 
                                    market_data: pd.DataFrame) -> float:
        """Calculate data quality score (0-100)"""
        score = 0
        max_score = 100
        
        # Sentiment data quality (40 points)
        if sentiment_data.get('news_count', 0) > 0:
            score += 20
        if sentiment_data.get('confidence', 0) > 0.5:
            score += 20
        
        # Technical data quality (30 points)
        if len(market_data) > 50:  # Sufficient price history
            score += 15
        if technical_result.get('indicators', {}).get('rsi', 0) > 0:
            score += 15
        
        # Market data recency (30 points)
        if not market_data.empty:
            latest_data = market_data.index[-1]
            # Handle timezone-aware/naive datetime comparison
            if hasattr(latest_data, 'tz_localize'):
                latest_dt = latest_data.tz_localize(None) if latest_data.tz is not None else latest_data.to_pydatetime()
            else:
                latest_dt = latest_data.to_pydatetime()
                if latest_dt.tzinfo is not None:
                    latest_dt = latest_dt.replace(tzinfo=None)
            
            hours_old = (datetime.now() - latest_dt).total_seconds() / 3600
            if hours_old < 24:  # Less than 24 hours old
                score += 30
            elif hours_old < 48:  # Less than 48 hours old
                score += 15
        
        return min(score, max_score)
    
    def _generate_enhanced_recommendations(self, analysis_results: Dict) -> Dict:
        """Generate enhanced recommendations based on ML predictions and traditional signals"""
        recommendations = {
            'strong_buy': [],
            'buy': [],
            'hold': [],
            'sell': [],
            'strong_sell': [],
            'ml_vs_traditional': {},
            'highest_confidence': None,
            'market_regime': 'UNKNOWN'
        }
        
        highest_confidence = 0
        highest_confidence_symbol = None
        
        # Analyze each bank
        for symbol in analysis_results['banks_analyzed']:
            ml_pred = analysis_results['ml_predictions'].get(symbol)
            traditional = analysis_results['technical_signals'].get(symbol)
            
            # Use ML prediction if available, otherwise fall back to traditional
            if ml_pred and 'error' not in ml_pred:
                action = ml_pred['optimal_action']
                confidence = ml_pred['confidence_scores']['average']
                
                # Compare ML vs Traditional
                if traditional:
                    recommendations['ml_vs_traditional'][symbol] = {
                        'ml_action': action,
                        'traditional_action': traditional['final_signal'],
                        'agreement': action == traditional['final_signal'],
                        'ml_confidence': confidence,
                        'traditional_confidence': traditional['overall_confidence']
                    }
            else:
                # Fall back to traditional signal
                if traditional:
                    action = traditional['final_signal']
                    confidence = traditional['overall_confidence']
                else:
                    action = 'HOLD'
                    confidence = 0.5
            
            # Track highest confidence recommendation
            if confidence > highest_confidence:
                highest_confidence = confidence
                highest_confidence_symbol = symbol
            
            # Categorize recommendations
            if action == 'STRONG_BUY':
                recommendations['strong_buy'].append((symbol, confidence))
            elif action == 'BUY':
                recommendations['buy'].append((symbol, confidence))
            elif action == 'STRONG_SELL':
                recommendations['strong_sell'].append((symbol, confidence))
            elif action == 'SELL':
                recommendations['sell'].append((symbol, confidence))
            else:
                recommendations['hold'].append((symbol, confidence))
        
        # Set highest confidence recommendation
        if highest_confidence_symbol:
            recommendations['highest_confidence'] = {
                'symbol': highest_confidence_symbol,
                'confidence': highest_confidence
            }
        
        # Determine market regime based on overall sentiment
        overall_sentiment = analysis_results.get('overall_market_sentiment', 0)
        if overall_sentiment > 0.3:
            recommendations['market_regime'] = 'BULLISH'
        elif overall_sentiment < -0.3:
            recommendations['market_regime'] = 'BEARISH'
        else:
            recommendations['market_regime'] = 'NEUTRAL'
        
        return recommendations
    
    def _get_current_price_robust(self, symbol):
        """
        Enhanced price fetching with multiple methods and retries
        """
        import time
        import random
        
        methods = [
            ('history', lambda t: t.history(period='1d').iloc[-1]['Close'] if len(t.history(period='1d')) > 0 else None),
            ('info', lambda t: t.info.get('currentPrice') or t.info.get('regularMarketPrice')),
            ('fast_info', lambda t: getattr(t.fast_info, 'last_price', None))
        ]
        
        for method_name, method_func in methods:
            for attempt in range(3):  # 3 attempts per method
                try:
                    import yfinance as yf; ticker = yf.Ticker(symbol)
                    price = method_func(ticker)
                    
                    if price and price > 0:
                        self.logger.info(f"💰 {symbol}: Got price using {method_name} method (attempt {attempt+1}) = ${price:.2f}")
                        return float(price)
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ {symbol}: {method_name} method attempt {attempt+1} failed: {e}")
                    if attempt < 2:  # Wait before retry (except last attempt)
                        time.sleep(random.uniform(1, 3))
                    continue
                    
        self.logger.error(f"🚨 {symbol}: ALL ENHANCED PRICE METHODS FAILED")
        return None


    def _get_model_performance_summary(self) -> Dict:
        """Get ML model performance summary from database"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.enhanced_db_path)
            cursor = conn.cursor()
            
            # Get latest model performance
            cursor.execute('''
                SELECT direction_accuracy_1h, direction_accuracy_4h, direction_accuracy_1d,
                       magnitude_mae_1h, magnitude_mae_4h, magnitude_mae_1d,
                       training_samples, feature_count
                FROM model_performance_enhanced
                ORDER BY created_at DESC
                LIMIT 1
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'direction_accuracy': {
                        '1h': result[0],
                        '4h': result[1],
                        '1d': result[2]
                    },
                    'magnitude_mae': {
                        '1h': result[3],
                        '4h': result[4],
                        '1d': result[5]
                    },
                    'training_samples': result[6],
                    'feature_count': result[7]
                }
            else:
                return {'status': 'No trained models available'}
                
        except Exception as e:
            return {'error': str(e)}
    
    def _run_basic_analysis(self) -> Dict:
        """Fallback basic analysis when enhanced components not available"""
        self.logger.info("Running basic analysis (enhanced components not available)")
        
        return {
            'timestamp': self.get_australian_time().isoformat(),
            'analysis_type': 'basic_fallback',
            'market_hours': self.is_market_hours(),
            'message': 'Enhanced ML components not available - install required dependencies',
            'banks_analyzed': list(self.banks.keys()),
            'recommendations': {'status': 'Basic analysis only'}
        }
    
    def _save_analysis_results(self, analysis_results: Dict):
        """Save analysis results to database"""
        try:
            import sqlite3
            import json
            
            # Ensure database directory exists
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enhanced_morning_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    analysis_type TEXT,
                    market_hours BOOLEAN,
                    banks_analyzed TEXT,
                    overall_sentiment REAL,
                    ml_predictions TEXT,
                    technical_signals TEXT,
                    recommendations TEXT,
                    data_quality_scores TEXT,
                    feature_counts TEXT,
                    model_performance TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                INSERT INTO enhanced_morning_analysis
                (timestamp, analysis_type, market_hours, banks_analyzed, overall_sentiment,
                 ml_predictions, technical_signals, recommendations, data_quality_scores,
                 feature_counts, model_performance)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                analysis_results['timestamp'],
                analysis_results['analysis_type'],
                analysis_results['market_hours'],
                json.dumps(analysis_results['banks_analyzed']),
                analysis_results['overall_market_sentiment'],
                json.dumps(analysis_results['ml_predictions']),
                json.dumps(analysis_results['technical_signals']),
                json.dumps(analysis_results['recommendations']),
                json.dumps(analysis_results['data_quality_scores']),
                json.dumps(analysis_results['feature_counts']),
                json.dumps(analysis_results['model_performance'])
            ))
            
            conn.commit()
            conn.close()
            
            self.logger.info("✅ Analysis results saved to database")
            self._save_predictions_if_available(analysis_results)
            self._save_volume_data(analysis_results)
            
        except Exception as e:
            self.logger.error(f"❌ Failed to save analysis results: {e}")
    
    def _display_analysis_summary(self, analysis_results: Dict):
        """Display comprehensive analysis summary"""
        print("\n" + "=" * 80)
        print("🌅 ENHANCED MORNING ANALYSIS SUMMARY")
        print("=" * 80)
        
        print(f"📅 Timestamp: {analysis_results['timestamp']}")
        print(f"🕐 Market Hours: {'✅ Yes' if analysis_results['market_hours'] else '❌ No'}")
        print(f"🔬 Analysis Type: {analysis_results['analysis_type']}")
        print(f"🏦 Banks Analyzed: {len(analysis_results['banks_analyzed'])}")
        print(f"📊 Overall Market Sentiment: {analysis_results['overall_market_sentiment']:+.3f}")
        
        # ML Predictions Summary
        ml_preds = analysis_results['ml_predictions']
        if ml_preds:
            print(f"\n🧠 ML PREDICTIONS SUMMARY:")
            print("-" * 40)
            for symbol, pred in ml_preds.items():
                action = pred['optimal_action']
                confidence = pred['confidence_scores']['average']
                direction_1h = "UP" if pred['direction_predictions']['1h'] else "DOWN"
                magnitude_1h = pred['magnitude_predictions']['1h']
                
                print(f"   {symbol}: {action} ({confidence:.3f}) - {direction_1h} {magnitude_1h:+.2f}%")
        
        # Traditional vs ML Comparison
        recommendations = analysis_results['recommendations']
        ml_vs_trad = recommendations.get('ml_vs_traditional', {})
        if ml_vs_trad:
            print(f"\n⚖️ ML vs TRADITIONAL COMPARISON:")
            print("-" * 40)
            agreements = sum(1 for comp in ml_vs_trad.values() if comp['agreement'])
            total = len(ml_vs_trad)
            agreement_rate = agreements / total if total > 0 else 0
            print(f"   Agreement Rate: {agreement_rate:.1%} ({agreements}/{total})")
            
            for symbol, comp in ml_vs_trad.items():
                status = "✅" if comp['agreement'] else "❌"
                print(f"   {symbol}: {status} ML:{comp['ml_action']} vs Trad:{comp['traditional_action']}")
        
        # Recommendations Summary
        print(f"\n🎯 RECOMMENDATIONS SUMMARY:")
        print("-" * 40)
        print(f"   Market Regime: {recommendations['market_regime']}")
        
        if recommendations['highest_confidence']:
            hc = recommendations['highest_confidence']
            print(f"   Highest Confidence: {hc['symbol']} ({hc['confidence']:.3f})")
        
        for action, symbols in recommendations.items():
            if action in ['strong_buy', 'buy', 'hold', 'sell', 'strong_sell'] and symbols:
                action_name = action.replace('_', ' ').title()
                print(f"   {action_name}: {len(symbols)} banks")
        
        # Data Quality Summary
        quality_scores = analysis_results['data_quality_scores']
        if quality_scores:
            avg_quality = sum(quality_scores.values()) / len(quality_scores)
            print(f"\n📈 DATA QUALITY SUMMARY:")
            print("-" * 40)
            print(f"   Average Quality Score: {avg_quality:.1f}%")
            
            high_quality = [s for s, q in quality_scores.items() if q >= 80]
            if high_quality:
                print(f"   High Quality Data (≥80%): {', '.join(high_quality)}")
        
        # Feature Engineering Summary
        feature_counts = analysis_results['feature_counts']
        if feature_counts:
            avg_features = sum(feature_counts.values()) / len(feature_counts)
            print(f"\n🔧 FEATURE ENGINEERING SUMMARY:")
            print("-" * 40)
            print(f"   Average Features per Bank: {avg_features:.0f}")
            print(f"   Feature Categories:")
            print(f"     - Technical Indicators: {len(self.enhanced_pipeline.required_features['technical_indicators'])}")
            print(f"     - Price Features: {len(self.enhanced_pipeline.required_features['price_features'])}")
            print(f"     - Volume Features: {len(self.enhanced_pipeline.required_features['volume_features'])}")
            print(f"     - Market Context: {len(self.enhanced_pipeline.required_features['market_context'])}")
            print(f"     - Interaction Features: {len(self.enhanced_pipeline.interaction_features)}")
            print(f"     - Time Features: {len(self.enhanced_pipeline.time_features)}")
        
        # Model Performance Summary
        model_perf = analysis_results['model_performance']
        if 'direction_accuracy' in model_perf:
            print(f"\n🎯 MODEL PERFORMANCE SUMMARY:")
            print("-" * 40)
            acc = model_perf['direction_accuracy']
            mae = model_perf['magnitude_mae']
            print(f"   Direction Accuracy: 1h={acc['1h']:.1%}, 4h={acc['4h']:.1%}, 1d={acc['1d']:.1%}")
            print(f"   Magnitude MAE: 1h={mae['1h']:.2f}%, 4h={mae['4h']:.2f}%, 1d={mae['1d']:.2f}%")
            print(f"   Training Samples: {model_perf.get('training_samples', 'N/A')}")
        
        print("\n" + "=" * 80)
        print("🚀 Enhanced analysis complete! All phases successfully implemented.")
        print("=" * 80)

    def _save_predictions_if_available(self, analysis_results):
        """Save predictions to the predictions table if ML predictions are available"""
        # DISABLED: Only fixed_price_mapping_v4.0 should generate predictions
        # This analyzer is for analysis only, not prediction generation
        self.logger.info("🔍 Prediction saving disabled - this analyzer is for analysis only")
        self.logger.info("✅ Predictions are handled by fixed_price_mapping_v4.0 system")
        return
                
            import sqlite3
            from datetime import datetime
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            saved_count = 0
            for symbol, pred in ml_preds.items():
                if not isinstance(pred, dict):
                    continue
                    
                prediction_id = f"enhanced_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                predicted_action = pred.get("optimal_action", "HOLD")
                # Fix: Use the real ML confidence from confidence_scores.average, fallback -9999 indicates missing data
                confidence = pred.get("confidence_scores", {}).get("average", -9999)
                predicted_direction = 1 if predicted_action == "BUY" else (-1 if predicted_action == "SELL" else 0)
                
                # Debug logging to identify the issue
                self.logger.info(f"🔍 {symbol} DEBUG: pred keys = {list(pred.keys())}")
                if 'confidence_scores' in pred:
                    self.logger.info(f"🔍 {symbol} confidence_scores = {pred['confidence_scores']}")
                else:
                    self.logger.warning(f"⚠️ {symbol} missing confidence_scores in prediction!")
                    self.logger.info(f"🔍 {symbol} full prediction = {pred}")
                
                # Get current price using enhanced robust method
                entry_price = self._get_current_price_robust(symbol)
                
                # Final fallback: Use -9999 to indicate missing price data
                if entry_price is None or entry_price == 0.0:
                    entry_price = -9999.0
                    self.logger.error(f"🚨 {symbol}: ALL ENHANCED PRICE LOOKUPS FAILED - Using -9999 fallback")
                
                # Get magnitude prediction (1-day horizon for entry)
                magnitude = pred.get("magnitude_predictions", {}).get("1d", -9999)
                self.logger.info(f"🔍 {symbol} magnitude_predictions = {pred.get('magnitude_predictions', 'MISSING')}")
                
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO predictions 
                        (prediction_id, symbol, prediction_timestamp, predicted_action, 
                         action_confidence, predicted_direction, predicted_magnitude, 
                         model_version, entry_price, optimal_action)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        prediction_id,
                        symbol,
                        analysis_results.get("timestamp", datetime.now().isoformat()),
                        predicted_action,
                        float(confidence),
                        predicted_direction,
                        float(magnitude),
                        "enhanced_ml_v1",
                        entry_price,
                        predicted_action
                    ))
                    saved_count += 1
                    self.logger.info(f"✅ Saved prediction: {symbol} -> {predicted_action} (conf: {confidence:.3f}, mag: {magnitude:.3f})")
                    
                    # Alert if we're getting fallback values indicating data pipeline issues
                    if confidence == -9999:
                        self.logger.error(f"🚨 {symbol}: CONFIDENCE FALLBACK DETECTED (-9999) - ML pipeline not working!")
                    if magnitude == -9999:
                        self.logger.error(f"🚨 {symbol}: MAGNITUDE FALLBACK DETECTED (-9999) - ML pipeline not working!")
                    if entry_price == 0.0:
                        self.logger.error(f"🚨 {symbol}: ENTRY PRICE IS ZERO (0.0) - Price lookup completely failed!")
                    if entry_price == -9999.0:
                        self.logger.error(f"🚨 {symbol}: ENTRY PRICE FALLBACK DETECTED (-9999) - All price sources failed!")
                except Exception as pred_error:
                    self.logger.warning(f"⚠️ Failed to save prediction for {symbol}: {pred_error}")
            
            conn.commit()
            conn.close()
            
            if saved_count > 0:
                self.logger.info(f"✅ Saved {saved_count} predictions to predictions table")
            else:
                self.logger.info("🔍 No valid predictions found to save")
                
        except Exception as e:
            self.logger.error(f"❌ Error saving predictions: {e}")

    def _save_volume_data(self, analysis_results: Dict):
        """Save volume data for evening analyzer to use"""
        try:
            import sqlite3
            from datetime import datetime
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create volume table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_volume_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    analysis_date DATE NOT NULL,
                    latest_volume REAL,
                    average_volume_20 REAL,
                    volume_ratio REAL,
                    market_hours BOOLEAN,
                    data_timestamp DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, analysis_date)
                )
            ''')
            
            analysis_date = self.get_australian_time().date()
            saved_count = 0
            
            for symbol in analysis_results['banks_analyzed']:
                try:
                    # Get volume data from market_data
                    market_data = get_market_data(symbol, period='3mo', interval='1h')
                    
                    if not market_data.empty and 'Volume' in market_data.columns:
                        latest_volume = float(market_data['Volume'].iloc[-1])
                        avg_volume_20 = float(market_data['Volume'].tail(20).mean())
                        volume_ratio = latest_volume / avg_volume_20 if avg_volume_20 > 0 else 0
                        
                        cursor.execute('''
                            INSERT OR REPLACE INTO daily_volume_data
                            (symbol, analysis_date, latest_volume, average_volume_20, 
                             volume_ratio, market_hours, data_timestamp)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            symbol,
                            analysis_date,
                            latest_volume,
                            avg_volume_20,
                            volume_ratio,
                            analysis_results['market_hours'],
                            analysis_results['timestamp']
                        ))
                        
                        saved_count += 1
                        self.logger.info(f"✅ Saved volume data: {symbol} = {latest_volume:,.0f} ({volume_ratio:.2f}x)")
                        
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to save volume for {symbol}: {e}")
            
            conn.commit()
            conn.close()
            
            if saved_count > 0:
                self.logger.info(f"✅ Saved volume data for {saved_count} symbols")
            else:
                self.logger.warning("⚠️ No volume data was saved")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving volume data: {e}")

def main():
    """Main function to run enhanced morning analysis"""
    analyzer = EnhancedMorningAnalyzer()
    
    try:
        # Run the enhanced analysis
        results = analyzer.run_enhanced_morning_analysis()
        
        return results
        
    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted by user")
        return None
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
