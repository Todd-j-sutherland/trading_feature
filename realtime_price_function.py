    def get_current_real_time_price(self, symbol: str) -> float:
        """Get current real-time price, preferring intraday data during market hours"""
        try:
            import pytz
            from datetime import datetime
            
            sydney_tz = pytz.timezone("Australia/Sydney")
            now_sydney = datetime.now(sydney_tz)
            hour = now_sydney.hour
            is_market_hours = 10 <= hour < 16 and now_sydney.weekday() < 5
            
            ticker = yf.Ticker(symbol)
            
            if is_market_hours:
                try:
                    intraday = ticker.history(period="1d", interval="1m")
                    if not intraday.empty and len(intraday) > 0:
                        latest_price = float(intraday.Close.iloc[-1])
                        print(f"Real-time price for {symbol}: ${latest_price:.2f}")
                        return latest_price
                except Exception as e:
                    print(f"Intraday data error: {e}")
            
            daily = ticker.history(period="1d")
            if not daily.empty:
                fallback_price = float(daily.Close.iloc[-1])
                print(f"Daily price for {symbol}: ${fallback_price:.2f}")
                return fallback_price
            
            return self.prices[-1] if hasattr(self, "prices") and len(self.prices) > 0 else 0.0
            
        except Exception as e:
            print(f"Error getting current price for {symbol}: {e}")
            return self.prices[-1] if hasattr(self, "prices") and len(self.prices) > 0 else 0.0

