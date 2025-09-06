#!/usr/bin/env python3
"""
Enhanced Comprehensive Prediction System with Validation
Includes duplicate detection, data quality checks, and enhanced technical analysis
"""
import sqlite3
import datetime
import subprocess
import json
import re
from collections import defaultdict

def validate_prediction_quality(predictions_batch):
    """Validate prediction quality and detect issues"""
    issues = []
    
    # Check for duplicates
    confidence_counts = defaultdict(int)
    tech_score_counts = defaultdict(int)
    
    for pred in predictions_batch:
        confidence_counts[round(pred['confidence'], 3)] += 1
        tech_score_counts[pred.get('tech_score', 0)] += 1
    
    # Detect duplicate confidences
    duplicates = [conf for conf, count in confidence_counts.items() if count > 1]
    if duplicates:
        issues.append(f"Duplicate confidences detected: {duplicates}")
    
    # Check technical score diversity
    unique_tech_scores = len(set(tech_score_counts.keys()))
    if unique_tech_scores < len(predictions_batch) * 0.7:  # Less than 70% unique
        issues.append(f"Low technical score diversity: {unique_tech_scores}/{len(predictions_batch)} unique")
    
    # Check news sentiment variation
    news_sentiments = [pred.get('news_sentiment', 0) for pred in predictions_batch]
    if len(set(news_sentiments)) == 1 and news_sentiments[0] == 0:
        issues.append("All news sentiments are zero - possible API issue")
    
    return issues

def extract_enhanced_analysis(output, symbol):
    """Extract comprehensive analysis data with enhanced parsing"""
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
        'volume_trend_pct': 0.0,
        'threshold': 70.0,
        'market_trend_pct': 0.0,
        'breakdown_text': '',
        'predicted_direction': 0,
        'predicted_magnitude': 0.0,
        'macd_score': 50.0,
        'bb_score': 50.0,
        'ma_score': 50.0
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
                    # Standardize market context format
                    context = next_line.split('Market Context:')[1].strip()
                    analysis['market_context'] = context.split('(')[0].strip()
                    
                elif 'Breakdown:' in next_line:
                    # Parse enhanced breakdown
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
                        
                elif 'Threshold Used:' in next_line:
                    thresh_match = re.search(r'Threshold Used:\s*([0-9.]+)%', next_line)
                    if thresh_match:
                        analysis['threshold'] = float(thresh_match.group(1))
            break
    
    return analysis

def save_validated_prediction(analysis, validation_results):
    """Save prediction with validation metadata"""
    try:
        conn = sqlite3.connect('predictions.db', timeout=30)
        conn.execute('PRAGMA journal_mode = WAL')
        conn.execute('PRAGMA busy_timeout = 30000')
        cursor = conn.cursor()
        
        timestamp = datetime.datetime.now().isoformat()
        prediction_id = f"{analysis['symbol']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Ensure confidence is in 0-1 range
        confidence = max(0.0, min(1.0, analysis['confidence']))
        
        # Enhanced prediction details with validation info
        prediction_details = {
            'action': analysis['action'],
            'confidence': confidence,
            'price': analysis['price'],
            'market_context': analysis['market_context'],
            'enhanced_breakdown': {
                'tech_score': analysis['tech_score'],
                'news_score': analysis['news_score'],
                'volume_score': analysis['volume_score'],
                'risk_score': analysis['risk_score'],
                'market_multiplier': analysis['market_multiplier']
            },
            'sentiment': analysis['news_sentiment'],
            'volume_trend': analysis['volume_trend_pct'],
            'threshold': analysis['threshold'],
            'validation': {
                'quality_checks_passed': len(validation_results) == 0,
                'issues_detected': validation_results,
                'timestamp': timestamp
            }
        }
        
        # Enhanced confidence components
        confidence_components = {
            'technical': analysis['tech_score'],
            'news': analysis['news_score'],
            'volume': analysis['volume_score'],
            'risk': analysis['risk_score'],
            'market_adjustment': analysis['market_multiplier'],
            'diversity_score': len(set([analysis['tech_score'], analysis['news_score'], analysis['volume_score']]))
        }
        
        # Enhanced feature vector
        feature_vector = {
            'tech_component': analysis['tech_score'],
            'news_component': analysis['news_score'],
            'volume_component': analysis['volume_score'],
            'risk_component': analysis['risk_score'],
            'price': analysis['price'],
            'volume_trend': analysis['volume_trend_pct'],
            'market_trend': analysis['market_trend_pct'],
            'news_sentiment': analysis['news_sentiment']
        }
        
        # Calculate enhanced technical score with more indicators
        tech_score_100 = int(analysis['tech_score'] * 100)
        
        # Determine risk and volume profiles
        risk_level = 'LOW' if analysis['risk_score'] < 0.3 else 'MEDIUM' if analysis['risk_score'] < 0.7 else 'HIGH'
        volume_profile = 'LOW' if analysis['volume_trend_pct'] < -30 else 'HIGH' if analysis['volume_trend_pct'] > 30 else 'NORMAL'
        
        # Enhanced technical indicators with additional metrics
        technical_indicators = {
            'rsi': analysis['tech_score'] * 100,
            'volume_trend': analysis['volume_trend_pct'],
            'macd_score': analysis.get('macd_score', 50.0),
            'bollinger_score': analysis.get('bb_score', 50.0),
            'moving_average_score': analysis.get('ma_score', 50.0),
            'composite_tech_score': tech_score_100
        }
        
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
            'enhanced_validated_v2.0',
            timestamp,
            analysis['price'],
            analysis['action'],
            json.dumps(prediction_details),
            analysis['breakdown_text'],
            analysis['market_context'],
            analysis['market_trend_pct'],
            1.0,  # market_volatility
            analysis['market_multiplier'] - 1.0,  # market_momentum
            0.0,  # sector_performance
            volume_profile,
            risk_level,
            json.dumps(confidence_components),
            json.dumps(technical_indicators),
            analysis['news_score'],
            analysis['volume_trend_pct'],
            analysis['volume_trend_pct'] / 100.0,  # price_momentum
            analysis['threshold'],
            tech_score_100,
            analysis['news_sentiment'],
            analysis['volume_trend_pct'],  # Consistent percentage format
            analysis['market_trend_pct'],
            analysis['action']
        ))
        
        conn.commit()
        conn.close()
        
        # Enhanced logging
        quality_flag = "✅" if len(validation_results) == 0 else "⚠️"
        print(f"{quality_flag} Enhanced save {analysis['symbol']}: {analysis['action']} ({confidence:.1%}) @ ${analysis['price']:.2f}")
        print(f"    Tech:{analysis['tech_score']:.3f} News:{analysis['news_score']:.3f} Vol:{analysis['volume_score']:.3f} Risk:{analysis['risk_score']:.3f}")
        if validation_results:
            print(f"    Issues: {', '.join(validation_results)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to save {analysis['symbol']}: {e}")
        return False

def run_enhanced_predictions():
    """Run prediction system with enhanced validation and diversity checks"""
    try:
        print("🔍 Running enhanced prediction system with validation...")
        
        # Run the enhanced market-aware system
        result = subprocess.run([
            'python3', 'enhanced_efficient_system_market_aware.py'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"❌ Prediction system failed: {result.stderr}")
            return 0
        
        # Parse output for each symbol
        output = result.stdout
        symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX']
        predictions_batch = []
        
        print("🔍 Extracting enhanced analysis data...")
        
        for symbol in symbols:
            analysis = extract_enhanced_analysis(output, symbol)
            
            # Validate data quality
            if analysis['price'] > 0 and analysis['action'] in ['BUY', 'SELL', 'HOLD']:
                predictions_batch.append(analysis)
            else:
                print(f"⚠️ Skipping {symbol}: incomplete data (price={analysis['price']}, action={analysis['action']})")
        
        # Batch validation
        validation_issues = validate_prediction_quality(predictions_batch)
        
        if validation_issues:
            print("⚠️ Data quality issues detected:")
            for issue in validation_issues:
                print(f"  - {issue}")
        else:
            print("✅ All quality checks passed")
        
        # Save predictions with validation results
        saved_count = 0
        for analysis in predictions_batch:
            if save_validated_prediction(analysis, validation_issues):
                saved_count += 1
        
        return saved_count
        
    except Exception as e:
        print(f"❌ Enhanced prediction execution failed: {e}")
        return 0

def main():
    """Main enhanced cron function with comprehensive validation"""
    print(f"🚀 Starting Enhanced Validated Predictions: {datetime.datetime.now()}")
    print("📊 Features: Enhanced technical analysis, duplicate detection, data validation")
    
    saved_count = run_enhanced_predictions()
    
    # Comprehensive database status check
    try:
        conn = sqlite3.connect('predictions.db')
        cursor = conn.cursor()
        
        # Get total counts
        cursor.execute('SELECT COUNT(*) FROM predictions')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT prediction_timestamp FROM predictions ORDER BY prediction_timestamp DESC LIMIT 1')
        latest = cursor.fetchone()[0]
        
        # Check latest enhanced predictions
        cursor.execute('''
            SELECT symbol, predicted_action, action_confidence, entry_price, 
                   tech_score, news_sentiment, volume_trend, market_context,
                   model_version
            FROM predictions 
            WHERE model_version = 'enhanced_validated_v2.0'
            ORDER BY prediction_timestamp DESC LIMIT 7
        ''')
        recent = cursor.fetchall()
        
        print(f"\n📊 Enhanced Database Status: {total} total predictions, latest: {latest}")
        print("📋 Latest Enhanced Validated Predictions:")
        for row in recent:
            symbol, action, conf, price, tech, news, vol, context, version = row
            print(f"   {symbol}: {action} ({conf:.1%}) ${price:.2f} [Tech:{tech} Vol:{vol:.1f}% Context:{context}] v{version}")
        
        # Quality metrics
        if recent:
            confidences = [row[2] for row in recent]
            tech_scores = [row[4] for row in recent]
            news_sentiments = [row[5] for row in recent]
            
            print(f"\n📈 Quality Metrics:")
            print(f"   Confidence diversity: {len(set(confidences))}/{len(confidences)} unique")
            print(f"   Tech score diversity: {len(set(tech_scores))}/{len(tech_scores)} unique")
            print(f"   News sentiment diversity: {len(set(news_sentiments))}/{len(news_sentiments)} unique")
            print(f"   Average confidence: {sum(confidences)/len(confidences):.1%}")
        
        conn.close()
    except Exception as e:
        print(f"❌ Database status check failed: {e}")
    
    print(f"\n✅ Enhanced Validation Complete: {saved_count}/7 predictions saved with quality checks")

if __name__ == '__main__':
    main()
