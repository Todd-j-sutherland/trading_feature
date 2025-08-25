
    def _emergency_traditional_signals(self, symbol, current_price):
        """Emergency traditional signals to replace biased ML"""
        
        try:
            import yfinance as yf
            
            # Get technical data
            data = yf.download(symbol, period="30d", interval="1d", progress=False)
            if data.empty:
                return {
                    'optimal_action': 'HOLD',
                    'confidence_scores': {'average': 0.5},
                    'magnitude_predictions': {'1d': 0.0},
                    'reasoning': 'Emergency traditional: No data available'
                }
            
            # Simple RSI calculation
            close_prices = data['Close']
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1] if len(rsi) > 0 else 50
            
            # Moving averages
            sma_5 = close_prices.rolling(window=5).mean().iloc[-1]
            sma_20 = close_prices.rolling(window=20).mean().iloc[-1]
            
            # Price momentum
            price_change = ((current_price - close_prices.iloc[-6]) / close_prices.iloc[-6]) * 100 if len(close_prices) > 5 else 0
            
            # Volume analysis
            volume = data['Volume']
            avg_volume = volume.rolling(window=10).mean().iloc[-1]
            volume_ratio = volume.iloc[-1] / avg_volume if avg_volume > 0 else 1.0
            
            # Traditional signals (BALANCED approach)
            confidence = 0.6
            magnitude = abs(price_change) / 100  # Convert to decimal
            
            # BUY conditions (encourage more BUY signals)
            if current_rsi < 35 and sma_5 > sma_20 and volume_ratio > 1.2:
                return {
                    'optimal_action': 'BUY',
                    'confidence_scores': {'average': min(0.8, confidence + 0.15)},
                    'magnitude_predictions': {'1d': max(0.02, magnitude)},
                    'reasoning': f'Traditional BUY: Oversold RSI ({current_rsi:.1f}) + upward trend + volume'
                }
            elif current_rsi < 40 and price_change > 1.5 and volume_ratio > 1.1:
                return {
                    'optimal_action': 'BUY',
                    'confidence_scores': {'average': 0.7},
                    'magnitude_predictions': {'1d': max(0.015, magnitude)},
                    'reasoning': f'Traditional BUY: Low RSI + momentum ({price_change:.1f}%)'
                }
            elif current_rsi < 45 and sma_5 > sma_20 * 1.02:  # 5-day clearly above 20-day
                return {
                    'optimal_action': 'BUY',
                    'confidence_scores': {'average': 0.65},
                    'magnitude_predictions': {'1d': max(0.01, magnitude)},
                    'reasoning': f'Traditional BUY: Moderate RSI + strong upward trend'
                }
            
            # SELL conditions (more conservative)
            elif current_rsi > 70 and sma_5 < sma_20:
                return {
                    'optimal_action': 'SELL',
                    'confidence_scores': {'average': min(0.8, confidence + 0.1)},
                    'magnitude_predictions': {'1d': max(0.02, magnitude)},
                    'reasoning': f'Traditional SELL: Overbought RSI ({current_rsi:.1f}) + downward trend'
                }
            elif current_rsi > 75 and price_change < -2:
                return {
                    'optimal_action': 'SELL',
                    'confidence_scores': {'average': 0.75},
                    'magnitude_predictions': {'1d': max(0.02, magnitude)},
                    'reasoning': f'Traditional SELL: High RSI + negative momentum ({price_change:.1f}%)'
                }
            
            # HOLD (neutral conditions)
            else:
                return {
                    'optimal_action': 'HOLD',
                    'confidence_scores': {'average': confidence},
                    'magnitude_predictions': {'1d': min(0.01, magnitude)},
                    'reasoning': f'Traditional HOLD: Neutral (RSI: {current_rsi:.1f}, Change: {price_change:.1f}%)'
                }
                
        except Exception as e:
            self.logger.error(f"Traditional signals error for {symbol}: {e}")
            return {
                'optimal_action': 'HOLD',
                'confidence_scores': {'average': 0.5},
                'magnitude_predictions': {'1d': 0.0},
                'reasoning': f'Traditional ERROR: {str(e)}'
            }
