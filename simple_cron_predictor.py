#!/usr/bin/env python3
import sqlite3
import datetime
import subprocess
import json
import re

def save_prediction(symbol, action, confidence, price, market_context="NEUTRAL"):
    """Save a single prediction to database"""
    try:
        conn = sqlite3.connect('predictions.db', timeout=30)
        conn.execute('PRAGMA journal_mode = WAL')
        cursor = conn.cursor()
        
        timestamp = datetime.datetime.now().isoformat()
        prediction_id = f"{symbol}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Ensure confidence is in 0-1 range
        conf = max(0.0, min(1.0, confidence / 100.0 if confidence > 1 else confidence))
        
        cursor.execute('''
            INSERT INTO predictions (
                prediction_id, symbol, prediction_timestamp, predicted_action,
                action_confidence, entry_price, model_version, created_at,
                optimal_action, market_context, recommended_action
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prediction_id, symbol, timestamp, action, conf, price,
            'cron_v1.0', timestamp, action, market_context, action
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Saved {symbol}: {action} ({conf:.1%}) at ${price:.2f}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save {symbol}: {e}")
        return False

def run_predictions():
    """Run prediction system and parse results"""
    try:
        # Run the market-aware system
        result = subprocess.run([
            'python3', 'enhanced_efficient_system_market_aware.py'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"❌ Prediction system failed: {result.stderr}")
            return 0
        
        # Parse output for each symbol
        output = result.stdout
        symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX']
        saved_count = 0
        
        for symbol in symbols:
            # Extract analysis for this symbol
            lines = output.split('\n')
            action = 'HOLD'
            confidence = 50.0
            price = 0.0
            market_context = 'NEUTRAL'
            
            # Find the enhanced analysis section for this symbol
            for i, line in enumerate(lines):
                if f'{symbol} Enhanced Analysis:' in line:
                    # Parse the next few lines
                    for j in range(i+1, min(i+8, len(lines))):
                        next_line = lines[j]
                        if 'Action:' in next_line:
                            action = next_line.split('Action:')[1].strip().split()[0]
                        elif 'Confidence:' in next_line:
                            conf_match = re.search(r'([0-9.]+)%', next_line)
                            if conf_match:
                                confidence = float(conf_match.group(1))
                        elif 'Price:' in next_line:
                            price_match = re.search(r'\$([0-9,.]+)', next_line)
                            if price_match:
                                price = float(price_match.group(1).replace(',', ''))
                        elif 'Market Context:' in next_line:
                            market_context = next_line.split('Market Context:')[1].strip()
                    break
            
            # Save if we have valid data
            if price > 0 and action in ['BUY', 'SELL', 'HOLD']:
                if save_prediction(symbol, action, confidence, price, market_context):
                    saved_count += 1
            else:
                print(f"⚠️ Skipping {symbol}: incomplete data (action={action}, price={price})")
        
        return saved_count
        
    except Exception as e:
        print(f"❌ Prediction execution failed: {e}")
        return 0

def main():
    """Main cron function"""
    print(f"🚀 Starting Cron Predictions: {datetime.datetime.now()}")
    
    saved_count = run_predictions()
    
    # Check database status
    try:
        conn = sqlite3.connect('predictions.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM predictions')
        total = cursor.fetchone()[0]
        cursor.execute('SELECT prediction_timestamp FROM predictions ORDER BY prediction_timestamp DESC LIMIT 1')
        latest = cursor.fetchone()[0]
        conn.close()
        
        print(f"📊 Database Status: {total} total predictions, latest: {latest}")
    except Exception as e:
        print(f"❌ Database check failed: {e}")
    
    print(f"✅ Cron Complete: {saved_count}/7 predictions saved")

if __name__ == '__main__':
    main()
