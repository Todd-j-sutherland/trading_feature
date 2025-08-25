
        # EMERGENCY PATCH: Check if ML is disabled
        if not ML_ENABLED:
            self.logger.info("🚨 ML DISABLED - Using emergency traditional signals")
            emergency_predictions = {}
            
            for symbol in self.banks.keys():
                # Get current price using existing robust method
                current_price = self._get_current_price_robust(symbol)
                if current_price > 0:
                    traditional_pred = self._emergency_traditional_signals(symbol, current_price)
                    emergency_predictions[symbol] = traditional_pred
                    self.logger.info(f"🔧 {symbol}: Traditional -> {traditional_pred['optimal_action']} (conf: {traditional_pred['confidence_scores']['average']:.3f})")
            
            # Replace ML predictions with traditional ones
            ml_preds = emergency_predictions
            self.logger.info(f"✅ Generated {len(emergency_predictions)} traditional predictions")
        else:
            # Original ML prediction code would go here
            pass
