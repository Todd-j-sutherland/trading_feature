#!/usr/bin/env python3
import sqlite3
import datetime
import subprocess
import json
import re

def extract_comprehensive_analysis(output, symbol):
    """Extract comprehensive analysis data from the market-aware system output"""
    lines = output.split('\n')
    analysis = {
        'symbol': symbol,
        'action': 'HOLD',
        'confidence': 0.5,
        'price': 0.0,
        'market_context': 'NEUTRAL',
        'tech_score': 0.0,
        'news_score': 0.0,
        'volume_score': 0.0,
        'risk_score': 0.0,
        'market_multiplier': 1.0,
        'news_sentiment': 0.0,
        'volume_trend': 0.0,
        'volume_trend_pct': 0.0,
        'threshold': 70.0,
        'market_trend_pct': 0.0,
        'breakdown_text': '',
        'predicted_direction': 0,
        'predicted_magnitude': 0.0
    }
    
    # Extract market overview first
    for line in lines:
        if '5-day Trend:' in line:
            trend_match = re.search(r'5-day Trend:\s*([+-]?[0-9.]+)%', line)
            if trend_match:
                analysis['market_trend_pct'] = float(trend_match.group(1))
    
    # Find the enhanced analysis section for this symbol
    for i, line in enumerate(lines):
        if f'{symbol} Enhanced Analysis:' in line:
            # Parse the next several lines
            for j in range(i+1, min(i+15, len(lines))):
                next_line = lines[j]
                
                if 'Action:' in next_line:
                    analysis['action'] = next_line.split('Action:')[1].strip().split()[0]
                    analysis['predicted_direction'] = 1 if analysis['action'] == 'BUY' else 0
                    
                elif 'Confidence:' in next_line:
                    conf_match = re.search(r'([0-9.]+)%', next_line)
                    if conf_match:
                        confidence_pct = float(conf_match.group(1))
                        analysis['confidence'] = confidence_pct / 100.0
                        analysis['predicted_magnitude'] = analysis['confidence']
                        
                elif 'Price:' in next_line:
                    price_match = re.search(r'\$([0-9,.]+)', next_line)
                    if price_match:
                        analysis['price'] = float(price_match.group(1).replace(',', ''))
                        
                elif 'Market Context:' in next_line:
                    analysis['market_context'] = next_line.split('Market Context:')[1].strip()
                    
                elif 'Breakdown:' in next_line:
                    # Parse breakdown like "Tech:0.356 + News:0.045 + Vol:0.030 + Risk:0.000 × Market:1.00 = 0.431"
                    analysis['breakdown_text'] = next_line.split('Breakdown:')[1].strip()
                    
                    tech_match = re.search(r'Tech:([0-9.]+)', next_line)
                    if tech_match:
                        analysis['tech_score'] = float(tech_match.group(1))
                    
                    news_match = re.search(r'News:([0-9.]+)', next_line)
                    if news_match:
                        analysis['news_score'] = float(news_match.group(1))
                    
                    vol_match = re.search(r'Vol:([0-9.]+)', next_line)
                    if vol_match:
                        analysis['volume_score'] = float(vol_match.group(1))
                    
                    risk_match = re.search(r'Risk:([0-9.]+)', next_line)
                    if risk_match:
                        analysis['risk_score'] = float(risk_match.group(1))
                    
                    market_match = re.search(r'Market:([0-9.]+)', next_line)
                    if market_match:
                        analysis['market_multiplier'] = float(market_match.group(1))
                        
                elif 'News Sentiment:' in next_line:
                    sent_match = re.search(r'News Sentiment:\s*([+-]?[0-9.]+)', next_line)
                    if sent_match:
                        analysis['news_sentiment'] = float(sent_match.group(1))
                        
                elif 'Volume Trend:' in next_line:
                    vol_trend_match = re.search(r'Volume Trend:\s*([+-]?[0-9.]+)%', next_line)
                    if vol_trend_match:
                        analysis['volume_trend_pct'] = float(vol_trend_match.group(1))
                        # Standardize: always store as percentage for consistency
                        analysis['volume_trend'] = analysis['volume_trend_pct']
                        
                elif 'Threshold Used:' in next_line:
                    thresh_match = re.search(r'Threshold Used:\s*([0-9.]+)%', next_line)
                    if thresh_match:
                        analysis['threshold'] = float(thresh_match.group(1))
            break
    
    return analysis

def save_comprehensive_prediction(analysis):
    """Save prediction to database with all available fields populated"""
    try:
        conn = sqlite3.connect('predictions.db', timeout=30)
        conn.execute('PRAGMA journal_mode = WAL')
        conn.execute('PRAGMA busy_timeout = 30000')
        cursor = conn.cursor()
        
        timestamp = datetime.datetime.now().isoformat()
        prediction_id = f"{analysis['symbol']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Ensure confidence is in 0-1 range
        confidence = max(0.0, min(1.0, analysis['confidence']))
        
        # Create comprehensive prediction details
        prediction_details = {
            'action': analysis['action'],
            'confidence': confidence,
            'price': analysis['price'],
            'market_context': analysis['market_context'],
            'breakdown': {
                'tech_score': analysis['tech_score'],
                'news_score': analysis['news_score'],
                'volume_score': analysis['volume_score'],
                'risk_score': analysis['risk_score'],
                'market_multiplier': analysis['market_multiplier']
            },
            'sentiment': analysis['news_sentiment'],
            'volume_trend': analysis['volume_trend_pct'],
            'threshold': analysis['threshold']
        }
        
        # Create confidence breakdown components
        confidence_components = {
            'technical': analysis['tech_score'],
            'news': analysis['news_score'],
            'volume': analysis['volume_score'],
            'risk': analysis['risk_score'],
            'market_adjustment': analysis['market_multiplier']
        }
        
        # Create feature vector for ML
        feature_vector = {
            'tech_component': analysis['tech_score'],
            'news_component': analysis['news_score'],
            'volume_component': analysis['volume_score'],
            'risk_component': analysis['risk_score'],
            'price': analysis['price'],
            'volume_trend': analysis['volume_trend'],
            'market_trend': analysis['market_trend_pct']
        }
        
        # Calculate technical indicators score (0-100 scale)
        tech_score_100 = int(analysis['tech_score'] * 100)
        
        # Calculate price momentum from volume trend
        price_momentum = analysis['volume_trend'] / 100.0  # Convert percentage to ratio
        
        # Determine risk level
        risk_level = 'LOW' if analysis['risk_score'] < 0.3 else 'MEDIUM' if analysis['risk_score'] < 0.7 else 'HIGH'
        
        # Standardize market context format (remove inconsistent details)
        market_context_clean = analysis['market_context'].split('(')[0].strip()
        analysis['market_context'] = market_context_clean
        
        # Determine volume profile
        volume_profile = 'LOW' if analysis['volume_trend_pct'] < -30 else 'HIGH' if analysis['volume_trend_pct'] > 30 else 'NORMAL'
        
        cursor.execute('''
            INSERT INTO predictions (
                prediction_id, symbol, prediction_timestamp, predicted_action,
                action_confidence, predicted_direction, predicted_magnitude,
                feature_vector, model_version, created_at, entry_price,
                optimal_action, prediction_details, confidence_breakdown,
                market_context, market_trend_pct, market_volatility, market_momentum,
                sector_performance, volume_profile, risk_level, confidence_components,
                technical_indicators, news_impact_score, volume_trend_score,
                price_momentum, buy_threshold_used, tech_score, news_sentiment,
                volume_trend, price_change_pct, recommended_action
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prediction_id,
            analysis['symbol'],
            timestamp,
            analysis['action'],
            confidence,
            analysis['predicted_direction'],
            analysis['predicted_magnitude'],
            json.dumps(feature_vector),
            'market_aware_comprehensive_v1.0',
            timestamp,
            analysis['price'],
            analysis['action'],
            json.dumps(prediction_details),
            analysis['breakdown_text'],
            analysis['market_context'],
            analysis['market_trend_pct'],
            1.0,  # market_volatility (default)
            analysis['market_multiplier'] - 1.0,  # market_momentum (deviation from neutral)
            0.0,  # sector_performance (not available)
            volume_profile,
            risk_level,
            json.dumps(confidence_components),
            json.dumps({'rsi': analysis['tech_score'] * 100, 'volume_trend': analysis['volume_trend_pct']}),
            analysis['news_score'],
            analysis['volume_trend_pct'],
            price_momentum,
            analysis['threshold'],
            tech_score_100,
            analysis['news_sentiment'],
            analysis['volume_trend'],
            analysis['market_trend_pct'],
            analysis['action']
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Comprehensive save {analysis['symbol']}: {analysis['action']} ({confidence:.1%}) @ ${analysis['price']:.2f}")
        print(f"    Tech:{analysis['tech_score']:.3f} News:{analysis['news_score']:.3f} Vol:{analysis['volume_score']:.3f} Risk:{analysis['risk_score']:.3f}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save {analysis['symbol']}: {e}")
        return False

def run_comprehensive_predictions():
    """Run prediction system and save comprehensive data"""
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
        
        print("🔍 Extracting comprehensive analysis data...")
        
        for symbol in symbols:
            analysis = extract_comprehensive_analysis(output, symbol)
            
            # Save if we have valid data
            if analysis['price'] > 0 and analysis['action'] in ['BUY', 'SELL', 'HOLD']:
                if save_comprehensive_prediction(analysis):
                    saved_count += 1
            else:
                print(f"⚠️ Skipping {symbol}: incomplete data")
        
        return saved_count
        
    except Exception as e:
        print(f"❌ Comprehensive prediction execution failed: {e}")
        return 0

def main():
    """Main comprehensive cron function"""
    print(f"🚀 Starting Comprehensive Cron Predictions: {datetime.datetime.now()}")
    print("📊 Enhanced data extraction with full schema population")
    
    saved_count = run_comprehensive_predictions()
    
    # Database status check
    try:
        conn = sqlite3.connect('predictions.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM predictions')
        total = cursor.fetchone()[0]
        cursor.execute('SELECT prediction_timestamp FROM predictions ORDER BY prediction_timestamp DESC LIMIT 1')
        latest = cursor.fetchone()[0]
        
        # Check data completeness of latest predictions
        cursor.execute('''
            SELECT symbol, predicted_action, action_confidence, entry_price, 
                   tech_score, news_sentiment, volume_trend, market_context
            FROM predictions 
            ORDER BY prediction_timestamp DESC LIMIT 7
        ''')
        recent = cursor.fetchall()
        
        print(f"\n📊 Database Status: {total} total predictions, latest: {latest}")
        print("📋 Latest Comprehensive Predictions:")
        for row in recent:
            symbol, action, conf, price, tech, news, vol, context = row
            print(f"   {symbol}: {action} ({conf:.1%}) ${price:.2f} [Tech:{tech} Vol:{vol:.1f}% Context:{context}]")
        
        conn.close()
    except Exception as e:
        print(f"❌ Database check failed: {e}")
    
    print(f"\n✅ Comprehensive Cron Complete: {saved_count}/7 predictions saved with full data")

if __name__ == '__main__':
    main()
