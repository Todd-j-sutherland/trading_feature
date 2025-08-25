
def _traditional_fallback_signals(self, symbol, current_price):
    """
    Traditional signals fallback when ML has insufficient training data
    This runs automatically until 100+ balanced samples are collected
    """
    try:
        import yfinance as yf
        
        # Get technical data
        data = yf.download(symbol, period="30d", interval="1d", progress=False)
        if data.empty:
            return {
                'optimal_action': 'HOLD',
                'confidence_scores': {'average': 0.5},
                'magnitude_predictions': {'1d': 0.0},
                'reasoning': 'Fallback: No data available'
            }
        
        # Simple technical analysis
        close_prices = data['Close']
        volume = data['Volume']
        
        # RSI calculation
        delta = close_prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50
        
        # Moving averages
        sma_5 = float(close_prices.rolling(window=5).mean().iloc[-1])
        sma_20 = float(close_prices.rolling(window=20).mean().iloc[-1])
        
        # Price momentum
        price_change = ((current_price - close_prices.iloc[-6]) / close_prices.iloc[-6]) * 100 if len(close_prices) > 5 else 0
        
        # Volume analysis
        avg_volume = volume.rolling(window=10).mean().iloc[-1]
        volume_ratio = volume.iloc[-1] / avg_volume if avg_volume > 0 else 1.0
        
        # Balanced traditional signals (ensures all action types)
        confidence = 0.6
        
        # BUY conditions (encourage BUY signals)
        if (current_rsi < 35) and (sma_5 > sma_20) and (volume_ratio > 1.2):
            return {
                'optimal_action': 'BUY',
                'confidence_scores': {'average': 0.75},
                'magnitude_predictions': {'1d': max(0.02, abs(price_change)/100)},
                'reasoning': f'Traditional BUY: Oversold RSI ({current_rsi:.1f}) + momentum + volume'
            }
        elif (current_rsi < 40) and (price_change > 1.5):
            return {
                'optimal_action': 'BUY',
                'confidence_scores': {'average': 0.7},
                'magnitude_predictions': {'1d': max(0.015, abs(price_change)/100)},
                'reasoning': f'Traditional BUY: Low RSI + positive momentum ({price_change:.1f}%)'
            }
        
        # SELL conditions
        elif (current_rsi > 70) and (sma_5 < sma_20):
            return {
                'optimal_action': 'SELL',
                'confidence_scores': {'average': 0.75},
                'magnitude_predictions': {'1d': max(0.02, abs(price_change)/100)},
                'reasoning': f'Traditional SELL: Overbought RSI ({current_rsi:.1f}) + downward trend'
            }
        elif (current_rsi > 75):
            return {
                'optimal_action': 'SELL',
                'confidence_scores': {'average': 0.7},
                'magnitude_predictions': {'1d': max(0.015, abs(price_change)/100)},
                'reasoning': f'Traditional SELL: Very overbought RSI ({current_rsi:.1f})'
            }
        
        # HOLD (default)
        else:
            return {
                'optimal_action': 'HOLD',
                'confidence_scores': {'average': confidence},
                'magnitude_predictions': {'1d': min(0.01, abs(price_change)/100)},
                'reasoning': f'Traditional HOLD: Neutral (RSI: {current_rsi:.1f}, Change: {price_change:.1f}%)'
            }
            
    except Exception as e:
        self.logger.error(f"Traditional fallback error for {symbol}: {e}")
        return {
            'optimal_action': 'HOLD',
            'confidence_scores': {'average': 0.5},
            'magnitude_predictions': {'1d': 0.0},
            'reasoning': f'Traditional ERROR: {str(e)}'
        }
