def comprehensive_threshold_validation(prediction_data, features_dict):
    """Comprehensive validation with volume veto power - PRESERVES incoming confidence"""
    symbol = prediction_data.get('symbol', 'UNKNOWN')
    raw_action = prediction_data.get('action', 'HOLD')
    confidence = prediction_data.get('confidence', 0.0)

    # Fix compound actions first
    action = fix_action_parsing(raw_action)

    # Extract critical features with better mapping
    volume_trend = features_dict.get('volume_trend', features_dict.get('volume_score', 0.5))
    technical_score = features_dict.get('technical_score', features_dict.get('tech_score', 0.5))
    news_sentiment = features_dict.get('news_sentiment', features_dict.get('news_score', 0.5))
    risk_assessment = features_dict.get('risk_assessment', features_dict.get('risk_score', 0.5))
    market_trend = features_dict.get('market_trend', features_dict.get('market_trend_pct', 0.0))

    # PRESERVE INCOMING CONFIDENCE - no rebalancing calculation needed
    # The ML-enhanced system already calculated optimal confidence
    print(f"💎 PRESERVING: {symbol} incoming confidence {confidence:.3f} (from ML-enhanced calculation)")

    # VOLUME VETO POWER - Handle both old percentage format and new normalized format
    # Detect format: if abs(volume_trend) > 2.0, it's likely percentage format
    if abs(volume_trend) > 2.0:
        # Old percentage format (-100 to +100) - convert to normalized 0.0-1.0
        # Map -50% to 0.0, 0% to 0.5, +50% to 1.0
        if volume_trend <= -50.0:
            normalized_volume = 0.0
        elif volume_trend >= 50.0:
            normalized_volume = 1.0
        else:
            normalized_volume = (volume_trend + 50.0) / 100.0
        print(f"📊 VOLUME CONVERSION: {symbol} {volume_trend:.1f}% → {normalized_volume:.3f} normalized")
    else:
        # Already normalized format (0.0 to 1.0)
        normalized_volume = volume_trend

    # Apply veto logic with RELAXED thresholds for bullish markets
    if action == 'BUY' and normalized_volume < 0.2:  # Lowered from 0.3 to 0.2
        print(f"🚫 VOLUME VETO: {symbol} BUY -> HOLD (volume={normalized_volume:.3f} < 0.2, original={volume_trend:.3f})")
        return 'HOLD', max(0.4, confidence * 0.7), {'veto': 'volume_low', 'original_action': action}

    if action == 'SELL' and normalized_volume > 0.8:  # Raised from 0.7 to 0.8
        print(f"🚫 VOLUME VETO: {symbol} SELL -> HOLD (volume={normalized_volume:.3f} > 0.8, original={volume_trend:.3f})")
        return 'HOLD', max(0.4, confidence * 0.7), {'veto': 'volume_high', 'original_action': action}

    # Market context assessment
    market_penalty = 0.0
    if market_trend < -2.0 and action == 'BUY':
        market_penalty = 0.15
        print(f"📉 MARKET PENALTY: {symbol} market_trend={market_trend:.1f}%, reducing BUY confidence")
    elif market_trend > 2.0 and action == 'SELL':
        market_penalty = 0.15
        print(f"📈 MARKET PENALTY: {symbol} market_trend={market_trend:.1f}%, reducing SELL confidence")

    # Apply threshold validation with enhanced logic using PRESERVED confidence
    if action == 'BUY':
        # Use original confidence for threshold checks (not rebalanced)
        min_confidence = 0.55  # Minimum threshold for BUY actions
        if confidence < min_confidence:
            print(f"❌ THRESHOLD FAIL: {symbol} BUY -> HOLD (confidence={confidence:.3f} < {min_confidence})")
            return 'HOLD', confidence, {'threshold_fail': 'buy_confidence_low'}

        # Additional BUY validation using features
        if technical_score < 0.6 or news_sentiment < 0.5:
            print(f"❌ QUALITY FAIL: {symbol} BUY -> HOLD (tech={technical_score:.3f}, news={news_sentiment:.3f})")
            return 'HOLD', confidence * 0.8, {'quality_fail': 'insufficient_support'}

    elif action == 'SELL':
        # Use original confidence for threshold checks
        min_confidence = 0.55  # Minimum threshold for SELL actions
        if confidence < min_confidence:
            print(f"❌ THRESHOLD FAIL: {symbol} SELL -> HOLD (confidence={confidence:.3f} < {min_confidence})")
            return 'HOLD', confidence, {'threshold_fail': 'sell_confidence_low'}

    # Apply market penalty to PRESERVED confidence
    final_confidence = max(0.3, confidence - market_penalty)

    print(f"✅ VALIDATION PASSED: {symbol} {action} (confidence: {confidence:.3f} -> {final_confidence:.3f})")
    return action, final_confidence, {'validation': 'passed', 'confidence_preserved': True}