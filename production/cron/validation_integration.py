    # ===== ENHANCED VALIDATION INTEGRATION =====
    print(f"\ní´ Applying comprehensive validation to {len(predictions_batch)} predictions")
    
    # Step 1: Apply individual validation to each prediction
    for i, analysis in enumerate(predictions_batch):
        symbol = analysis.get('symbol', 'UNKNOWN')
        
        # Extract features for validation
        features_dict = {
            'volume_trend': analysis.get('volume_trend', 0.5),
            'technical_score': analysis.get('technical_score', 0.5),
            'news_sentiment': analysis.get('news_sentiment', 0.5),
            'risk_assessment': analysis.get('risk_assessment', 0.5),
            'market_trend': analysis.get('market_trend', 0.0)
        }
        
        # Check for staleness
        if staleness_detection(features_dict, symbol):
            analysis['staleness_warning'] = True
        
        # Apply comprehensive threshold validation
        validated_action, validated_confidence, validation_meta = comprehensive_threshold_validation(
            analysis, features_dict
        )
        
        # Update prediction with validated values
        original_action = analysis.get('action')
        original_confidence = analysis.get('confidence')
        
        analysis['action'] = validated_action
        analysis['confidence'] = validated_confidence
        analysis['validation_meta'] = validation_meta
        
        if original_action != validated_action:
            print(f"  í³ {symbol}: {original_action} -> {validated_action} (confidence: {original_confidence:.3f} -> {validated_confidence:.3f})")
    
    # Step 2: Apply batch-level validations
    print(f"\ní´ Applying batch-level validation checks")
    
    # Sector correlation check
    predictions_batch = sector_correlation_check(predictions_batch)
    
    # Circuit breaker check
    predictions_batch = circuit_breaker_check(predictions_batch)
    
    # Summary of changes
    action_counts = {}
    for analysis in predictions_batch:
        action = analysis.get('action', 'HOLD')
        action_counts[action] = action_counts.get(action, 0) + 1
    
    total = len(predictions_batch)
    print(f"\ní³Š Final action distribution:")
    for action, count in sorted(action_counts.items()):
        percentage = (count / total) * 100 if total > 0 else 0
        print(f"  {action}: {count} ({percentage:.1f}%)")
    
    # ===== END ENHANCED VALIDATION =====
