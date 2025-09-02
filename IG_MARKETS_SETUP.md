# IG Markets Real-Time Data Integration Setup

## Overview

✅ **Implemented**: IG Markets real-time price fetcher with demo account support
🎯 **Priority**: IG Markets → Alpha Vantage → yfinance (with delay warnings)
💰 **Advantage**: Real-time ASX data using your existing IG demo account

## Getting IG Markets API Access

### Step 1: Get API Key from IG Markets

1. **Log into your IG demo account**
2. **Navigate to**: Account settings → API access
3. **Create API key** or use existing one
4. **Note down**: Username, Password, API Key

### Step 2: Set Environment Variables

Add these to your `.env` file on the remote server:

```bash
# On remote server
cd /root/test
nano .env

# Add these lines:
IG_USERNAME=your_ig_demo_username
IG_PASSWORD=your_ig_demo_password
IG_API_KEY=your_ig_api_key
```

### Step 3: Test IG Markets Integration

```bash
cd /root/test
export IG_USERNAME=your_username
export IG_PASSWORD=your_password
export IG_API_KEY=your_api_key
python3 ig_markets_fetcher.py
```

## IG Markets API Advantages

### Real-Time Data

- ✅ **Zero delay** during ASX trading hours
- ✅ **Bid/Ask spreads** for better price accuracy
- ✅ **Professional market data** (same as trading platform)
- ✅ **Demo account access** (no real money required)

### ASX Coverage

- ✅ **Full ASX coverage** including all major stocks
- ✅ **Market depth** and order book data
- ✅ **Extended hours** trading data
- ✅ **Corporate actions** and dividends

### API Features

- ✅ **RESTful API** with JSON responses
- ✅ **Rate limiting** handled gracefully
- ✅ **Authentication** with session tokens
- ✅ **Error handling** and status codes

## Current Data Source Priority

1. **IG Markets** (Real-time, demo account) 🥇
2. **Alpha Vantage** (Real-time, requires API key) 🥈
3. **yfinance** (20+ min delay, free fallback) 🥉

## Integration with Paper Trading

The enhanced paper trading service will now:

1. **Check IG Markets first** for real-time prices
2. **Log data source** and freshness for each trade
3. **Use real-time bid/ask** for more accurate entry/exit
4. **Cache prices** to avoid excessive API calls
5. **Fallback gracefully** if IG Markets unavailable

## Testing Your Setup

### Quick Test

```bash
cd /root/test
python3 -c "
from real_time_price_fetcher import get_current_price_with_source_info
result = get_current_price_with_source_info('WBC.AX')
print(f'Price: ${result[\"price\"]:.2f}')
print(f'Source: {result[\"source\"]}')
print(f'Delay: {result.get(\"delay_minutes\", 0)} minutes')
"
```

### Expected Output with IG Markets

```
Price: $38.65
Source: ig_markets
Delay: 0 minutes
```

### Expected Output without IG Markets (fallback)

```
Price: $38.65
Source: yfinance
Delay: 20.3 minutes
```

## Paper Trading Performance

### Before IG Markets Integration

- Data source: yfinance only
- Delay: 20+ minutes during trading hours
- Accuracy: Lower (delayed prices)
- Market data: Close prices only

### After IG Markets Integration

- Data source: IG Markets real-time
- Delay: 0 minutes during trading hours
- Accuracy: Higher (bid/ask spreads)
- Market data: Professional grade

## Troubleshooting

### Common Issues

1. **Authentication Failed**

   - Check username/password for demo account
   - Verify API key is correct
   - Ensure demo account is active

2. **Symbol Not Found**

   - IG uses different EPICs than ASX codes
   - System will auto-search for matching markets
   - Check IG platform for exact symbol names

3. **Rate Limiting**
   - IG has generous rate limits for demo accounts
   - System includes 30-second caching
   - Fallback to other sources if needed

### Getting Help

- **IG Markets Support**: Demo account questions
- **API Documentation**: Available in IG platform
- **System Logs**: Check paper trading service logs

## Next Steps

1. ✅ Set up IG Markets credentials
2. ✅ Test real-time price fetching
3. ✅ Run enhanced paper trading service
4. ✅ Monitor $20 profit targets with real-time data
5. ✅ Compare performance vs delayed data

This integration gives you professional-grade real-time ASX data using your existing IG demo account!
