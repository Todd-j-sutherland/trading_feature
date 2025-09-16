
def comprehensive_threshold_validation(prediction_data, features_dict):
    """Comprehensive validation with volume veto power and feature rebalancing"""
    symbol = prediction_data.get('symbol', 'UNKNOWN')
    raw_action = prediction_data.get('action', 'HOLD')
    confidence = prediction_data.get('confidence', 0.0)
    
    # Fix compound actions first
    action = fix_action_parsing(raw_action)
    
    # Extract critical features
    volume_trend = features_dict.get('volume_trend', 0.5)
    technical_score = features_dict.get('technical_score', 0.5)
    news_sentiment = features_dict.get('news_sentiment', 0.5)
    risk_assessment = features_dict.get('risk_assessment', 0.5)
    market_trend = features_dict.get('market_trend', 0.0)
    
    # Enhanced feature weights (volume gets veto power)
    enhanced_weights = {
        'volume_trend': 0.35,      # Increased from ~0.17
        'technical_score': 0.25,   # Decreased from ~0.30
        'news_sentiment': 0.20,    # Decreased from ~0.25
        'risk_assessment': 0.20    # Decreased from ~0.28
    }
    
    # Calculate rebalanced confidence
    rebalanced_confidence = (
        volume_trend * enhanced_weights['volume_trend'] +
        technical_score * enhanced_weights['technical_score'] +
        news_sentiment * enhanced_weights['news_sentiment'] +
        risk_assessment * enhanced_weights['risk_assessment']
    )
    
    # VOLUME VETO POWER - If volume disagrees strongly, override
    if action == 'BUY' and volume_trend < 0.3:
        print(f"VOLUME VETO: {symbol} BUY -> HOLD (volume_trend={volume_trend:.3f} too low)")
        return 'HOLD', max(0.4, rebalanced_confidence * 0.7), {'veto': 'volume_low', 'original_action': action}
    
    if action == 'SELL' and volume_trend > 0.7:
        print(f"VOLUME VETO: {symbol} SELL -> HOLD (volume_trend={volume_trend:.3f} too high)")
        return 'HOLD', max(0.4, rebalanced_confidence * 0.7), {'veto': 'volume_high', 'original_action': action}
    
    # Market context assessment
    market_penalty = 0.0
    if market_trend < -2.0 and action == 'BUY':
        market_penalty = 0.15
        print(f"MARKET PENALTY: {symbol} market_trend={market_trend:.1f}%, reducing BUY confidence")
    elif market_trend > 2.0 and action == 'SELL':
        market_penalty = 0.15
        print(f"MARKET PENALTY: {symbol} market_trend={market_trend:.1f}%, reducing SELL confidence")
    
    # Apply threshold validation with enhanced logic
    if action == 'BUY':
        # Stricter BUY requirements
        min_confidence = 0.65
        if rebalanced_confidence < min_confidence:
            print(f"THRESHOLD FAIL: {symbol} BUY -> HOLD (confidence={rebalanced_confidence:.3f} < {min_confidence})")
            return 'HOLD', rebalanced_confidence, {'threshold_fail': 'buy_confidence_low'}
        
        # Additional BUY validation
        if technical_score < 0.6 or news_sentiment < 0.5:
            print(f"QUALITY FAIL: {symbol} BUY -> HOLD (tech={technical_score:.3f}, news={news_sentiment:.3f})")
            return 'HOLD', rebalanced_confidence * 0.8, {'quality_fail': 'insufficient_support'}
    
    elif action == 'SELL':
        # Stricter SELL requirements
        min_confidence = 0.60
        if rebalanced_confidence < min_confidence:
            print(f"THRESHOLD FAIL: {symbol} SELL -> HOLD (confidence={rebalanced_confidence:.3f} < {min_confidence})")
            return 'HOLD', rebalanced_confidence, {'threshold_fail': 'sell_confidence_low'}
    
    # Apply market penalty
    final_confidence = max(0.3, rebalanced_confidence - market_penalty)
    
    return action, final_confidence, {'validation': 'passed', 'rebalanced': True}

def sector_correlation_check(predictions_batch):
    """Prevent contradictory signals within same sector"""
    sector_groups = defaultdict(list)
    
    for pred in predictions_batch:
        symbol = pred.get('symbol', '')
        action = pred.get('action', 'HOLD')
        
        # Basic sector mapping (extend as needed)
        if any(bank in symbol.upper() for bank in ['CBA', 'ANZ', 'WBC', 'NAB']):
            sector_groups['banking'].append((symbol, action, pred))
        elif any(mining in symbol.upper() for mining in ['BHP', 'RIO', 'FMG', 'NCM']):
            sector_groups['mining'].append((symbol, action, pred))
        # Add more sectors as needed
    
    # Check for sector consistency
    for sector, stocks in sector_groups.items():
        if len(stocks) >= 2:
            actions = [stock[1] for stock in stocks]
            buy_count = actions.count('BUY')
            sell_count = actions.count('SELL')
            
            # If sector is split 50/50, reduce confidence for all
            if buy_count > 0 and sell_count > 0:
                total_signals = buy_count + sell_count
                if total_signals >= 2 and abs(buy_count - sell_count) <= 1:
                    print(f"SECTOR CONFLICT: {sector} split {buy_count}BUY/{sell_count}SELL - reducing confidence")
                    for symbol, action, pred in stocks:
                        if action in ['BUY', 'SELL']:
                            pred['confidence'] = max(0.4, pred['confidence'] * 0.7)
                            pred['sector_conflict'] = True
    
    return predictions_batch

def circuit_breaker_check(predictions_batch):
    """Implement safety limits on BUY signals"""
    total_predictions = len(predictions_batch)
    buy_predictions = [p for p in predictions_batch if p.get('action') == 'BUY']
    buy_rate = len(buy_predictions) / max(1, total_predictions)
    
    # Circuit breaker: max 40% BUY rate
    max_buy_rate = 0.40
    
    if buy_rate > max_buy_rate:
        excess_buys = len(buy_predictions) - int(total_predictions * max_buy_rate)
        
        # Sort by confidence and downgrade lowest confidence BUYs
        buy_predictions.sort(key=lambda x: x.get('confidence', 0.0))
        
        for i in range(excess_buys):
            if i < len(buy_predictions):
                symbol = buy_predictions[i].get('symbol', 'UNKNOWN')
                original_confidence = buy_predictions[i].get('confidence', 0.0)
                print(f"CIRCUIT BREAKER: {symbol} BUY -> HOLD (excess BUY rate={buy_rate:.1%})")
                buy_predictions[i]['action'] = 'HOLD'
                buy_predictions[i]['confidence'] = max(0.4, original_confidence * 0.8)
                buy_predictions[i]['circuit_breaker'] = True
    
    return predictions_batch

def staleness_detection(features_dict, symbol):
    """Detect if features are stale or inconsistent"""
    current_hour = datetime.datetime.now().hour
    
    # Check for obvious staleness indicators
    volume_trend = features_dict.get('volume_trend', 0.5)
    technical_score = features_dict.get('technical_score', 0.5)
    
    # If values are exactly 0.5 (default), likely stale
    stale_indicators = 0
    if abs(volume_trend - 0.5) < 0.001:
        stale_indicators += 1
    if abs(technical_score - 0.5) < 0.001:
        stale_indicators += 1
    
    # During market hours, features should be more varied
    is_market_hours = 9 <= current_hour <= 16
    if is_market_hours and stale_indicators >= 2:
        print(f"STALENESS WARNING: {symbol} has {stale_indicators} default values during market hours")
        return True
    
    return False

