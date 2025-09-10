#!/usr/bin/env python3
"""
YFinance Data Delay Investigation
Analyzes yfinance data freshness, delays, and optimal cron timing for ASX trading
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import time
import json

class YFinanceDelayAnalyzer:
    """Comprehensive analyzer for yfinance data delays and timing issues"""
    
    def __init__(self):
        self.asx_symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX']
        self.asx_tz = pytz.timezone('Australia/Sydney')
        self.utc_tz = pytz.timezone('UTC')
        
    def get_current_times(self):
        """Get current times in different timezones"""
        now_utc = datetime.now(self.utc_tz)
        now_asx = now_utc.astimezone(self.asx_tz)
        now_local = datetime.now()
        
        return {
            'utc': now_utc,
            'asx': now_asx,
            'local': now_local,
            'utc_str': now_utc.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'asx_str': now_asx.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'local_str': now_local.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def check_asx_market_hours(self, dt=None):
        """Check if ASX market is currently open"""
        if dt is None:
            dt = datetime.now(self.asx_tz)
        elif dt.tzinfo is None:
            dt = self.asx_tz.localize(dt)
        elif dt.tzinfo != self.asx_tz:
            dt = dt.astimezone(self.asx_tz)
        
        # ASX trading hours: 10:00 AM - 4:00 PM AEST/AEDT
        weekday = dt.weekday()  # 0=Monday, 6=Sunday
        hour = dt.hour
        minute = dt.minute
        
        # Check if it's a weekday
        if weekday >= 5:  # Saturday (5) or Sunday (6)
            return False, "Weekend"
        
        # Check market hours (10:00 AM - 4:00 PM)
        market_open = dt.replace(hour=10, minute=0, second=0, microsecond=0)
        market_close = dt.replace(hour=16, minute=0, second=0, microsecond=0)
        
        if dt < market_open:
            return False, f"Before market open (opens at {market_open.strftime('%H:%M')})"
        elif dt > market_close:
            return False, f"After market close (closed at {market_close.strftime('%H:%M')})"
        else:
            return True, f"Market open (closes at {market_close.strftime('%H:%M')})"
    
    def fetch_latest_data(self, symbol, period="2d", interval="1m"):
        """Fetch latest data and analyze timestamps"""
        try:
            print(f"\n📊 Fetching data for {symbol}...")
            ticker = yf.Ticker(symbol)
            
            # Get recent data
            data = ticker.history(period=period, interval=interval)
            
            if data.empty:
                return None, f"No data returned for {symbol}"
            
            # Get the latest timestamp
            latest_timestamp = data.index[-1]
            latest_price = data['Close'].iloc[-1]
            latest_volume = data['Volume'].iloc[-1]
            
            # Convert to different timezones for analysis
            if latest_timestamp.tz is None:
                latest_timestamp = pytz.utc.localize(latest_timestamp)
            
            latest_utc = latest_timestamp.astimezone(self.utc_tz)
            latest_asx = latest_timestamp.astimezone(self.asx_tz)
            
            # Calculate delay from now
            now_utc = datetime.now(self.utc_tz)
            delay_minutes = (now_utc - latest_utc).total_seconds() / 60
            
            # Check if data is from today
            today_asx = datetime.now(self.asx_tz).date()
            data_date_asx = latest_asx.date()
            is_today = data_date_asx == today_asx
            
            # Check market status at data timestamp
            market_open, market_status = self.check_asx_market_hours(latest_asx)
            
            return {
                'symbol': symbol,
                'latest_timestamp_utc': latest_utc,
                'latest_timestamp_asx': latest_asx,
                'latest_timestamp_str': latest_asx.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'latest_price': latest_price,
                'latest_volume': latest_volume,
                'delay_minutes': delay_minutes,
                'is_today': is_today,
                'market_open_at_data_time': market_open,
                'market_status': market_status,
                'data_points': len(data),
                'period_requested': period,
                'interval_requested': interval
            }, None
            
        except Exception as e:
            return None, f"Error fetching {symbol}: {str(e)}"
    
    def analyze_all_symbols(self):
        """Analyze data delays for all ASX symbols"""
        print("🔍 YFinance Data Delay Analysis")
        print("=" * 50)
        
        current_times = self.get_current_times()
        print(f"Current Time (Local): {current_times['local_str']}")
        print(f"Current Time (ASX):   {current_times['asx_str']}")
        print(f"Current Time (UTC):   {current_times['utc_str']}")
        
        # Check current market status
        market_open, market_status = self.check_asx_market_hours()
        print(f"ASX Market Status:    {market_status}")
        print()
        
        results = []
        errors = []
        
        for symbol in self.asx_symbols:
            data, error = self.fetch_latest_data(symbol)
            if data:
                results.append(data)
                print(f"✅ {symbol}:")
                print(f"   Latest Data: {data['latest_timestamp_str']}")
                print(f"   Price: ${data['latest_price']:.2f}")
                print(f"   Volume: {data['latest_volume']:,}")
                print(f"   Delay: {data['delay_minutes']:.1f} minutes")
                print(f"   Today's Data: {'Yes' if data['is_today'] else 'No'}")
                print(f"   Market Status at Data Time: {data['market_status']}")
            else:
                errors.append({'symbol': symbol, 'error': error})
                print(f"❌ {symbol}: {error}")
        
        return results, errors
    
    def analyze_delay_patterns(self, results):
        """Analyze patterns in data delays"""
        if not results:
            print("\n❌ No data to analyze delay patterns")
            return
        
        print(f"\n📈 Delay Pattern Analysis ({len(results)} symbols)")
        print("-" * 40)
        
        delays = [r['delay_minutes'] for r in results]
        
        print(f"Average Delay:    {np.mean(delays):.1f} minutes")
        print(f"Minimum Delay:    {np.min(delays):.1f} minutes")
        print(f"Maximum Delay:    {np.max(delays):.1f} minutes")
        print(f"Delay Std Dev:    {np.std(delays):.1f} minutes")
        
        # Categorize delays
        real_time = [d for d in delays if d < 5]
        delayed = [d for d in delays if 5 <= d <= 30]
        very_delayed = [d for d in delays if d > 30]
        
        print(f"\nDelay Categories:")
        print(f"Real-time (<5 min):   {len(real_time)} symbols")
        print(f"Delayed (5-30 min):   {len(delayed)} symbols")
        print(f"Very delayed (>30 min): {len(very_delayed)} symbols")
        
        # Check data freshness
        today_data = [r for r in results if r['is_today']]
        old_data = [r for r in results if not r['is_today']]
        
        print(f"\nData Freshness:")
        print(f"Today's Data:     {len(today_data)} symbols")
        print(f"Stale Data:       {len(old_data)} symbols")
        
        if old_data:
            print(f"Symbols with stale data:")
            for r in old_data:
                print(f"  {r['symbol']}: {r['latest_timestamp_str']}")
    
    def suggest_cron_timing(self, results):
        """Suggest optimal cron timing based on data delays"""
        print(f"\n⏰ Cron Timing Recommendations")
        print("-" * 35)
        
        if not results:
            print("❌ No data available for timing recommendations")
            return
        
        avg_delay = np.mean([r['delay_minutes'] for r in results])
        max_delay = np.max([r['delay_minutes'] for r in results])
        
        print(f"Current Data Delay: {avg_delay:.1f} min average, {max_delay:.1f} min maximum")
        
        # ASX market hours: 10:00 AM - 4:00 PM AEST/AEDT
        # Current analysis time
        current_asx = datetime.now(self.asx_tz)
        
        # Recommendations for different scenarios
        print(f"\n📋 Scheduling Recommendations:")
        print(f"1. Morning Analysis (Pre-market):")
        print(f"   - Schedule: 9:30 AM ASX (before market open)")
        print(f"   - Rationale: Use previous day's close data")
        print(f"   - Data Source: Previous trading day final prices")
        
        print(f"\n2. Intraday Analysis (During market):")
        delay_buffer = max(30, max_delay + 10)  # At least 30 min buffer
        market_open_plus_buffer = 10 * 60 + delay_buffer  # 10 AM + buffer in minutes
        hours = market_open_plus_buffer // 60
        minutes = market_open_plus_buffer % 60
        print(f"   - Schedule: {hours}:{minutes:02d} AM ASX ({delay_buffer:.0f} min after market open)")
        print(f"   - Rationale: Ensure fresh market data is available")
        print(f"   - Data Source: Live trading data with {delay_buffer:.0f} min delay buffer")
        
        print(f"\n3. Evening Analysis (Post-market):")
        evening_time = 16 + (max_delay + 15) / 60  # 4 PM + delay + buffer
        evening_hours = int(evening_time)
        evening_minutes = int((evening_time - evening_hours) * 60)
        print(f"   - Schedule: {evening_hours}:{evening_minutes:02d} PM ASX")
        print(f"   - Rationale: Full day's data available with {max_delay + 15:.0f} min buffer")
        print(f"   - Data Source: Complete trading session data")
        
        # Weekend analysis
        print(f"\n4. Weekend Analysis:")
        print(f"   - Schedule: Saturday 8:00 AM ASX")
        print(f"   - Rationale: Week's data fully settled")
        print(f"   - Data Source: Complete week trading data")
        
        # Convert to UTC for cron
        print(f"\n🌍 UTC Cron Times (for server scheduling):")
        
        # Morning pre-market (9:30 AM ASX)
        morning_asx = current_asx.replace(hour=9, minute=30, second=0, microsecond=0)
        morning_utc = morning_asx.astimezone(self.utc_tz)
        print(f"Morning:  {morning_utc.strftime('%M %H * * *')} # {morning_utc.strftime('%H:%M UTC')} = 9:30 AM ASX")
        
        # Intraday (market open + buffer)
        intraday_asx = current_asx.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        intraday_utc = intraday_asx.astimezone(self.utc_tz)
        print(f"Intraday: {intraday_utc.strftime('%M %H * * *')} # {intraday_utc.strftime('%H:%M UTC')} = {hours}:{minutes:02d} AM ASX")
        
        # Evening (market close + buffer)
        evening_asx = current_asx.replace(hour=evening_hours, minute=evening_minutes, second=0, microsecond=0)
        evening_utc = evening_asx.astimezone(self.utc_tz)
        print(f"Evening:  {evening_utc.strftime('%M %H * * 1-5')} # {evening_utc.strftime('%H:%M UTC')} = {evening_hours}:{evening_minutes:02d} PM ASX")
        
        # Weekend
        weekend_asx = current_asx.replace(hour=8, minute=0, second=0, microsecond=0)
        weekend_utc = weekend_asx.astimezone(self.utc_tz)
        print(f"Weekend:  {weekend_utc.strftime('%M %H * * 6')} # {weekend_utc.strftime('%H:%M UTC')} = 8:00 AM ASX Saturday")
    
    def test_historical_delays(self, days_back=5):
        """Test historical data to understand delay patterns"""
        print(f"\n📊 Historical Delay Pattern Analysis ({days_back} days)")
        print("-" * 45)
        
        symbol = "CBA.AX"  # Use CBA as representative
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Get several days of minute data to analyze patterns
            data = ticker.history(period=f"{days_back}d", interval="1m")
            
            if data.empty:
                print(f"❌ No historical data available for {symbol}")
                return
            
            print(f"✅ Analyzing {len(data)} data points for {symbol}")
            
            # Analyze last data point of each trading day
            daily_last_points = data.groupby(data.index.date).last()
            
            print(f"\nLast data point each trading day:")
            for date, row in daily_last_points.tail(5).iterrows():
                # Convert timestamp
                if hasattr(row.name, 'tz_localize'):
                    timestamp = row.name.tz_localize('UTC').astimezone(self.asx_tz)
                else:
                    timestamp = pd.Timestamp(row.name).tz_localize('UTC').astimezone(self.asx_tz)
                
                print(f"  {date}: Last data at {timestamp.strftime('%H:%M:%S ASX')}")
                
                # Check if this is close to market close (4:00 PM)
                market_close = timestamp.replace(hour=16, minute=0, second=0)
                minutes_after_close = (timestamp - market_close).total_seconds() / 60
                print(f"           {minutes_after_close:+.0f} minutes from 4:00 PM close")
        
        except Exception as e:
            print(f"❌ Error in historical analysis: {e}")
    
    def save_analysis_report(self, results, errors):
        """Save detailed analysis report"""
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'current_times': self.get_current_times(),
            'market_status': self.check_asx_market_hours(),
            'symbol_analysis': results,
            'errors': errors,
            'summary': {
                'symbols_analyzed': len(results),
                'symbols_with_errors': len(errors),
                'average_delay_minutes': np.mean([r['delay_minutes'] for r in results]) if results else 0,
                'max_delay_minutes': np.max([r['delay_minutes'] for r in results]) if results else 0,
                'symbols_with_today_data': len([r for r in results if r['is_today']]),
                'symbols_with_stale_data': len([r for r in results if not r['is_today']])
            }
        }
        
        filename = f"yfinance_delay_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n💾 Analysis report saved to: {filename}")
        except Exception as e:
            print(f"\n❌ Error saving report: {e}")

def main():
    """Main analysis function"""
    print("🇦🇺 YFinance ASX Data Delay Investigation")
    print("=" * 55)
    
    analyzer = YFinanceDelayAnalyzer()
    
    try:
        # Analyze current data delays
        results, errors = analyzer.analyze_all_symbols()
        
        # Analyze delay patterns
        analyzer.analyze_delay_patterns(results)
        
        # Suggest optimal cron timing
        analyzer.suggest_cron_timing(results)
        
        # Test historical patterns
        analyzer.test_historical_delays()
        
        # Save detailed report
        analyzer.save_analysis_report(results, errors)
        
        print(f"\n🎯 Key Findings:")
        if results:
            avg_delay = np.mean([r['delay_minutes'] for r in results])
            print(f"   • Average yfinance delay: {avg_delay:.1f} minutes")
            print(f"   • This could explain HOLD bias if ML runs before fresh data")
            print(f"   • Recommend adjusting cron times to account for delays")
        
        today_data_count = len([r for r in results if r['is_today']])
        if today_data_count < len(results):
            print(f"   • ⚠️ {len(results) - today_data_count} symbols have stale data")
        
        if errors:
            print(f"   • ❌ {len(errors)} symbols had fetch errors")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check if yfinance is available
    try:
        import yfinance
        main()
    except ImportError:
        print("❌ yfinance not installed. Install with: pip install yfinance")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have internet connectivity and yfinance is properly installed.")