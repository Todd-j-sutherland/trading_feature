#!/usr/bin/env python3
"""
Simple Historical Analysis of Trading Predictions
Analyzes correlation between prediction components and actual price movements
"""

import sqlite3
import json
from datetime import datetime

def analyze_historical_data():
    """Analyze historical trading data and show correlations"""
    
    print("📊 HISTORICAL TRADING ANALYSIS")
    print("=" * 50)
    
    # Connect to database
    conn = sqlite3.connect('trading_predictions.db')
    
    try:
        print("\n🔍 ANALYZING ENHANCED FEATURES vs OUTCOMES")
        print("-" * 45)
        
        # Get enhanced features with outcomes
        query = """
        SELECT 
            ef.symbol,
            ef.timestamp,
            ef.sentiment_score,
            ef.confidence,
            ef.rsi,
            ef.macd_line,
            ef.current_price,
            ef.price_change_1h,
            ef.price_change_4h,
            ef.price_change_1d,
            ef.volume_ratio,
            eo.price_direction_1h,
            eo.price_direction_4h,
            eo.price_direction_1d,
            eo.price_magnitude_1h,
            eo.price_magnitude_4h,
            eo.price_magnitude_1d,
            eo.return_pct
        FROM enhanced_features ef
        LEFT JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
        WHERE eo.id IS NOT NULL
        ORDER BY ef.timestamp DESC
        """
        
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            print("❌ No enhanced features with outcomes found!")
            return
            
        print(f"📈 Found {len(rows)} data points with outcomes")
        
        # Analyze correlations
        sentiment_correct = 0
        rsi_signals = 0
        total_with_sentiment = 0
        total_with_rsi = 0
        
        positive_sentiment_up = 0
        negative_sentiment_down = 0
        rsi_oversold_up = 0
        rsi_overbought_down = 0
        
        price_movements = {
            'positive_returns': [],
            'negative_returns': [],
            'sentiment_scores': [],
            'rsi_values': [],
            'volume_ratios': []
        }
        
        print("\n📋 SAMPLE DATA ANALYSIS:")
        print("Symbol | Timestamp | Sentiment | RSI | Price_1h | Direction | Return%")
        print("-" * 75)
        
        for i, row in enumerate(rows[:10]):  # Show first 10 for sample
            symbol, timestamp, sentiment, confidence, rsi, macd, price, \
            price_1h, price_4h, price_1d, volume_ratio, dir_1h, dir_4h, dir_1d, \
            mag_1h, mag_4h, mag_1d, return_pct = row
            
            print(f"{symbol:6} | {timestamp[:16]:16} | {sentiment:8.3f} | {rsi:6.1f} | {price_1h:8.3f} | {dir_1h:9} | {return_pct:7.3f}")
            
            # Collect data for analysis
            if sentiment is not None:
                total_with_sentiment += 1
                price_movements['sentiment_scores'].append(sentiment)
                
                # Check sentiment prediction accuracy
                if (sentiment > 0 and dir_1h == 1) or (sentiment < 0 and dir_1h == -1):
                    sentiment_correct += 1
                    
                if sentiment > 0 and dir_1h == 1:
                    positive_sentiment_up += 1
                elif sentiment < 0 and dir_1h == -1:
                    negative_sentiment_down += 1
            
            if rsi is not None:
                total_with_rsi += 1
                price_movements['rsi_values'].append(rsi)
                
                # RSI signals
                if rsi < 30 and dir_1h == 1:  # Oversold -> Up
                    rsi_oversold_up += 1
                elif rsi > 70 and dir_1h == -1:  # Overbought -> Down
                    rsi_overbought_down += 1
            
            if return_pct is not None:
                if return_pct > 0:
                    price_movements['positive_returns'].append(return_pct)
                else:
                    price_movements['negative_returns'].append(return_pct)
            
            if volume_ratio is not None:
                price_movements['volume_ratios'].append(volume_ratio)
        
        # Calculate and display correlations
        print(f"\n📊 CORRELATION ANALYSIS:")
        print("-" * 30)
        
        if total_with_sentiment > 0:
            sentiment_accuracy = (sentiment_correct / total_with_sentiment) * 100
            print(f"🎯 Sentiment Prediction Accuracy: {sentiment_accuracy:.1f}% ({sentiment_correct}/{total_with_sentiment})")
            print(f"   📈 Positive sentiment → Up moves: {positive_sentiment_up}")
            print(f"   📉 Negative sentiment → Down moves: {negative_sentiment_down}")
        
        if total_with_rsi > 0:
            rsi_signals = rsi_oversold_up + rsi_overbought_down
            rsi_accuracy = (rsi_signals / total_with_rsi) * 100 if total_with_rsi > 0 else 0
            print(f"🎯 RSI Signal Accuracy: {rsi_accuracy:.1f}% ({rsi_signals}/{total_with_rsi})")
            print(f"   📈 RSI Oversold → Up moves: {rsi_oversold_up}")
            print(f"   📉 RSI Overbought → Down moves: {rsi_overbought_down}")
        
        # Returns analysis
        if price_movements['positive_returns'] and price_movements['negative_returns']:
            avg_positive = sum(price_movements['positive_returns']) / len(price_movements['positive_returns'])
            avg_negative = sum(price_movements['negative_returns']) / len(price_movements['negative_returns'])
            print(f"💰 Average Positive Return: {avg_positive:.3f}%")
            print(f"💸 Average Negative Return: {avg_negative:.3f}%")
        
        print("\n🔍 PREDICTION PERFORMANCE ANALYSIS:")
        print("-" * 40)
        
        # Analyze prediction accuracy
        predictions_query = """
        SELECT 
            p.symbol,
            p.predicted_action,
            p.action_confidence,
            p.predicted_direction,
            o.actual_direction,
            o.actual_return
        FROM predictions p
        LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
        WHERE o.actual_return IS NOT NULL
        """
        
        cursor = conn.execute(predictions_query)
        prediction_rows = cursor.fetchall()
        
        if prediction_rows:
            correct_direction = 0
            total_predictions = len(prediction_rows)
            
            buy_predictions = 0
            hold_predictions = 0
            sell_predictions = 0
            
            buy_success = 0
            hold_success = 0
            sell_success = 0
            
            for pred_row in prediction_rows:
                symbol, action, confidence, pred_dir, actual_dir, actual_return = pred_row
                
                # Count by action
                if action == 'BUY':
                    buy_predictions += 1
                    if actual_return > 0:
                        buy_success += 1
                elif action == 'HOLD':
                    hold_predictions += 1
                    if abs(actual_return) < 0.01:  # Small movement for HOLD
                        hold_success += 1
                elif action == 'SELL':
                    sell_predictions += 1
                    if actual_return < 0:
                        sell_success += 1
                
                # Direction accuracy
                if pred_dir == actual_dir:
                    correct_direction += 1
            
            direction_accuracy = (correct_direction / total_predictions) * 100
            print(f"🎯 Direction Prediction Accuracy: {direction_accuracy:.1f}% ({correct_direction}/{total_predictions})")
            
            print(f"\n📊 ACTION BREAKDOWN:")
            if buy_predictions > 0:
                buy_acc = (buy_success / buy_predictions) * 100
                print(f"   🟢 BUY: {buy_acc:.1f}% success ({buy_success}/{buy_predictions})")
            if hold_predictions > 0:
                hold_acc = (hold_success / hold_predictions) * 100
                print(f"   🟡 HOLD: {hold_acc:.1f}% success ({hold_success}/{hold_predictions})")
            if sell_predictions > 0:
                sell_acc = (sell_success / sell_predictions) * 100
                print(f"   🔴 SELL: {sell_acc:.1f}% success ({sell_success}/{sell_predictions})")
        
        print("\n📈 SYMBOL PERFORMANCE:")
        print("-" * 25)
        
        # Symbol-specific analysis
        symbol_query = """
        SELECT symbol, COUNT(*) as count, AVG(actual_return) as avg_return
        FROM outcomes 
        WHERE actual_return IS NOT NULL
        GROUP BY symbol
        ORDER BY avg_return DESC
        """
        
        cursor = conn.execute(symbol_query)
        symbol_rows = cursor.fetchall()
        
        for symbol, count, avg_return in symbol_rows:
            print(f"{symbol}: {count:3} predictions, {avg_return:6.3f}% avg return")
        
        print(f"\n✅ Analysis complete! Found {len(rows)} feature-outcome pairs")
        print(f"📊 Processed {len(prediction_rows)} predictions with outcomes")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()

if __name__ == "__main__":
    analyze_historical_data()
