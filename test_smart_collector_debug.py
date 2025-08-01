#!/usr/bin/env python3
"""
Debug Smart Collector - Test why outcomes aren't being recorded
"""
import sqlite3
import json
from datetime import datetime, timedelta

def get_australian_time():
    """Get current time in Australian timezone"""
    # Simplified - just use local time for debugging
    return datetime.now()

def check_enhanced_predictions():
    """Check what predictions exist in enhanced_features table"""
    print("🔍 CHECKING ENHANCED FEATURES PREDICTIONS")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('data/ml_models/enhanced_training_data.db')
        cursor = conn.cursor()
        
        # Check recent predictions (last 24 hours)
        cursor.execute('''
            SELECT symbol, timestamp, sentiment_score, confidence, rsi
            FROM enhanced_features 
            WHERE datetime(timestamp) > datetime('now', '-1 day')
            ORDER BY timestamp DESC
            LIMIT 10
        ''')
        
        recent_predictions = cursor.fetchall()
        
        if recent_predictions:
            print(f"✅ Found {len(recent_predictions)} recent predictions:")
            for pred in recent_predictions:
                symbol, timestamp, sentiment, confidence, rsi = pred
                signal = 'BUY' if rsi < 30 else 'SELL' if rsi > 70 else 'HOLD'
                print(f"   {symbol}: {signal} (conf: {confidence:.2f}, sentiment: {sentiment:.3f}, RSI: {rsi:.1f}) at {timestamp}")
        else:
            print("❌ No recent predictions found in enhanced_features table")
            
        # Check total predictions
        cursor.execute('SELECT COUNT(*) FROM enhanced_features')
        total = cursor.fetchone()[0]
        print(f"\n📊 Total predictions in database: {total}")
        
        # Check for outcomes
        cursor.execute('SELECT COUNT(*) FROM enhanced_outcomes')
        outcomes = cursor.fetchone()[0]
        print(f"📊 Total outcomes in database: {outcomes}")
        
        conn.close()
        return recent_predictions
        
    except Exception as e:
        print(f"❌ Error checking enhanced predictions: {e}")
        return []

def check_smart_collector_signals():
    """Check what signals Smart Collector is tracking"""
    print("\n🤖 CHECKING SMART COLLECTOR SIGNALS")
    print("=" * 50)
    
    try:
        with open('data/ml_models/active_signals.json', 'r') as f:
            signals = json.load(f)
            
        if signals:
            print(f"✅ Found {len(signals)} active signals:")
            for signal_id, signal in signals.items():
                print(f"   {signal_id}: {signal['symbol']} - {signal['signal_type']} (conf: {signal['confidence']:.2f})")
        else:
            print("❌ No active signals found")
            
        return signals
        
    except FileNotFoundError:
        print("❌ No active_signals.json file found")
        return {}
    except Exception as e:
        print(f"❌ Error checking signals: {e}")
        return {}

def analyze_enhanced_quality_criteria():
    """Analyze enhanced features for outcome recording potential"""
    print("\n📊 ANALYZING ENHANCED FEATURES FOR OUTCOME TRACKING")
    print("=" * 50)
    
    try:
        conn = sqlite3.connect('data/ml_models/enhanced_training_data.db')
        cursor = conn.cursor()
        
        # Get recent predictions
        cursor.execute('''
            SELECT symbol, sentiment_score, confidence, rsi, timestamp
            FROM enhanced_features 
            WHERE datetime(timestamp) > datetime('now', '-1 day')
        ''')
        
        predictions = cursor.fetchall()
        
        if not predictions:
            print("❌ No recent predictions to analyze")
            return
            
        print("Enhanced Features Analysis:")
        print("Looking for signals that should have outcomes recorded...")
        print()
        
        buy_signals = 0
        sell_signals = 0
        hold_signals = 0
        older_predictions = 0
        
        now = datetime.now()
        for symbol, sentiment, confidence, rsi, timestamp in predictions:
            signal = 'BUY' if rsi < 30 else 'SELL' if rsi > 70 else 'HOLD'
            pred_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00').replace('+00:00', ''))
            hours_old = (now - pred_time).total_seconds() / 3600
            
            if signal == 'BUY':
                buy_signals += 1
            elif signal == 'SELL':
                sell_signals += 1
            else:
                hold_signals += 1
                
            if hours_old >= 4:  # Predictions older than 4 hours should have outcomes
                older_predictions += 1
                
            print(f"   {symbol}: {signal} | RSI:{rsi:.1f} | conf:{confidence:.2f} | {hours_old:.1f}h old")
        
        print(f"\nSignal Summary:")
        print(f"   BUY signals: {buy_signals}")
        print(f"   SELL signals: {sell_signals}")
        print(f"   HOLD signals: {hold_signals}")
        print(f"   Predictions >4h old: {older_predictions}")
        
        if older_predictions > 0:
            print(f"\n⚠️  ISSUE: {older_predictions} predictions are >4 hours old but have no outcomes!")
            print("   The Smart Collector should have recorded outcomes by now.")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing enhanced criteria: {e}")

def propose_solution():
    """Propose a solution to bridge the gap"""
    print("\n🔧 PROPOSED SOLUTION")
    print("=" * 50)
    
    print("The issue is that Smart Collector and Morning Analysis are separate systems:")
    print()
    print("📋 Current Flow:")
    print("   1. Morning Analysis generates predictions -> morning_analysis.db") 
    print("   2. Smart Collector looks for live signals -> active_signals.json")
    print("   3. No connection between them!")
    print()
    print("🔗 Solution Options:")
    print("   A) Modify Smart Collector to read from morning_analysis.db")
    print("   B) Modify Morning Analysis to write to active_signals.json") 
    print("   C) Create a bridge script that converts predictions to signals")
    print("   D) Lower Smart Collector quality criteria")
    print()
    print("🎯 Recommended: Option A - Smart Collector should monitor morning_analysis.db")

def main():
    print("🐛 SMART COLLECTOR DEBUG ANALYSIS")
    print("=" * 60)
    
    # Check what predictions exist
    predictions = check_enhanced_predictions()
    
    # Check what signals Smart Collector is tracking
    signals = check_smart_collector_signals()
    
    # Analyze why outcomes aren't being recorded
    analyze_enhanced_quality_criteria()
    
    # Propose solution
    propose_solution()
    
    print("\n" + "=" * 60)
    print("🎯 CONCLUSION: Smart Collector needs to monitor enhanced_features.db predictions!")

if __name__ == "__main__":
    main()
