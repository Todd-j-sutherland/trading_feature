# Alpha Vantage Integration Setup Guide

## Current Status

✅ **Implemented**: Hybrid real-time price fetcher with Alpha Vantage support
✅ **Working**: yfinance fallback with delay monitoring (~20 minutes currently)
✅ **Updated**: Enhanced paper trading service with $20 profit targets
⚠️ **Limited**: Demo Alpha Vantage API key only works for US stocks

## Getting Real-Time ASX Data with Alpha Vantage

### Step 1: Get Free Alpha Vantage API Key

1. Visit: https://www.alphavantage.co/support/#api-key
2. Fill out the form (it's free)
3. You'll get an API key immediately via email
4. Free tier includes: 25 requests per day, 5 requests per minute

### Step 2: Update Environment Variable

Replace the demo key in your .env file:
```bash
# On remote server
cd /root/test
nano .env

# Replace this line:
ALPHA_VANTAGE_API_KEY=demo

# With your real key:
ALPHA_VANTAGE_API_KEY=YOUR_ACTUAL_KEY_HERE
```

### Step 3: Test Real-Time ASX Data

```bash
cd /root/test
export ALPHA_VANTAGE_API_KEY=YOUR_ACTUAL_KEY_HERE
python3 real_time_price_fetcher.py
```

## Current Performance

### Data Delays (as of Sept 2, 2025 15:48 AEST)
- **yfinance**: ~20 minutes delay during trading hours
- **Alpha Vantage** (with real key): Real-time quotes
- **Prediction system**: Still using timestamp from computation time

### Paper Trading Improvements
- ✅ Fixed timezone issues (no more 300+ minute hold times)
- ✅ Updated to $20 profit targets
- ✅ Real-time price monitoring every 60 seconds
- ✅ Data source and delay logging
- ✅ One position per symbol enforcement

## Alternative: Free Real-Time Sources

If Alpha Vantage free tier is too limited, other options include:

1. **Yahoo Finance API** (direct, not yfinance library)
2. **ASX API** (if available)
3. **IEX Cloud** (free tier)
4. **Finnhub** (free tier)

## Impact on Trading Strategy

### Before Fixes
- Hold times: 300+ minutes (timezone bugs)
- Profit target: $5
- Data freshness: Unknown/inconsistent
- Price checks: Manual/inconsistent

### After Fixes
- Hold times: Accurate (timezone-aware)
- Profit target: $20
- Data freshness: Monitored with warnings
- Price checks: Every 60 seconds
- Real-time capability: Ready for Alpha Vantage

## Next Steps

1. Get Alpha Vantage API key for real-time ASX data
2. Update prediction system timestamps to use actual data time
3. Consider upgrading to paid API for higher limits if needed
4. Monitor paper trading performance with new $20 targets

## Technical Notes

The real-time price fetcher will:
- Try Alpha Vantage first (real-time if available)
- Fall back to yfinance with delay warnings
- Log data source and freshness for each price fetch
- Handle API limits gracefully

This ensures the paper trading system always has price data while preferring the most current source available.
