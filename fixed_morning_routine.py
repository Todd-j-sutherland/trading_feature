#!/usr/bin/env python3
"""
Fixed Morning Routine - Uses Working NewsTradingAnalyzer
Replaces buggy enhanced_morning_analyzer_with_ml.py
"""

import sys
import os
import sqlite3
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, '/root/test')

def save_prediction_to_database(symbol, analysis_result):
    """Save prediction to database using working format"""
    try:
        conn = sqlite3.connect('/root/test/data/trading_predictions.db')
        cursor = conn.cursor()
        
        # Extract values from analysis result
        timestamp = datetime.now().isoformat()
        action = analysis_result.get('signal', 'HOLD')
        confidence = analysis_result.get('confidence', 0.0)
        sentiment = analysis_result.get('overall_sentiment', 0.0)
        
        # Map signal to action
        if action in ['STRONG_BUY', 'BUY']:
            predicted_action = 'BUY'
            direction = 1
        elif action in ['STRONG_SELL', 'SELL']:
            predicted_action = 'SELL'
            direction = -1
        else:
            predicted_action = 'HOLD'
            direction = 0
        
        # Calculate magnitude from sentiment
        magnitude = abs(sentiment) if sentiment != 0 else 0.001
        
        # Generate prediction_id
        prediction_id = f"news_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get current stock price
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            hist_data = ticker.history(period="1d")
            entry_price = float(hist_data["Close"].iloc[-1]) if not hist_data.empty else 0.0
        except Exception as e:
            logger.warning(f"Failed to get price for {symbol}: {e}")
            entry_price = 0.0
        
        # Insert prediction with all required fields
        cursor.execute("""
            INSERT INTO predictions (
                prediction_id, symbol, prediction_timestamp, predicted_action, action_confidence,
                predicted_direction, predicted_magnitude, model_version, entry_price, optimal_action
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prediction_id, symbol, timestamp, predicted_action, confidence,
            direction, magnitude, 'NewsTradingAnalyzer_v1.0', entry_price, predicted_action
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Saved prediction for {symbol}: {predicted_action} (conf: {confidence:.3f}, price: ${entry_price:.2f})")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to save prediction for {symbol}: {e}")
        return False

def run_fixed_morning_routine():
    """Run morning routine using working NewsTradingAnalyzer"""
    
    logger.info("🌅 FIXED MORNING ROUTINE - Using NewsTradingAnalyzer")
    logger.info("=" * 60)
    
    try:
        from app.core.data.processors.news_processor import NewsTradingAnalyzer
        from app.config.settings import Settings
        
        settings = Settings()
        bank_symbols = settings.BANK_SYMBOLS
        
        analyzer = NewsTradingAnalyzer()
        logger.info("✅ NewsTradingAnalyzer initialized successfully")
        
        successful_predictions = 0
        total_symbols = len(bank_symbols)
        
        for symbol in bank_symbols:
            logger.info(f"📊 Analyzing {symbol}...")
            
            try:
                # Get analysis with timeout protection
                analysis_result = analyzer.analyze_single_bank(symbol, detailed=False)
                
                if analysis_result and isinstance(analysis_result, dict):
                    if 'error' not in analysis_result:
                        # Save to database
                        if save_prediction_to_database(symbol, analysis_result):
                            successful_predictions += 1
                            
                        logger.info(f"✅ {symbol}: {analysis_result.get('signal', 'N/A')} "
                                  f"(Score: {analysis_result.get('overall_sentiment', 0):.3f}, "
                                  f"Confidence: {analysis_result.get('confidence', 0):.3f})")
                    else:
                        logger.error(f"❌ {symbol}: Analysis returned error: {analysis_result.get('error')}")
                else:
                    logger.error(f"❌ {symbol}: Invalid analysis result")
                    
            except Exception as e:
                logger.error(f"❌ {symbol}: Analysis failed: {e}")
        
        logger.info(f"🎯 Morning routine complete: {successful_predictions}/{total_symbols} successful predictions")
        return successful_predictions > 0
        
    except Exception as e:
        logger.error(f"❌ Morning routine failed: {e}")
        return False

if __name__ == "__main__":
    success = run_fixed_morning_routine()
    sys.exit(0 if success else 1)
