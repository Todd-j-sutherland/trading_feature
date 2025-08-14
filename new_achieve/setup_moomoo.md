# Moomoo API Setup for ASX Paper Trading

This guide will help you set up Moomoo API integration for paper trading ASX stocks in your trading platform.

## Prerequisites

1. **Moomoo Account**: You need an active Moomoo account with Australian market access
2. **Python Environment**: Python 3.7+ with your existing trading environment

## Installation Steps

### 1. Install Moomoo Python SDK

```bash
pip install moomoo-api
```

### 2. Download and Install OpenD Gateway

1. Visit the [Moomoo OpenAPI Download Page](https://www.moomoo.com/download/OpenAPI)
2. Download the appropriate OpenD version for your operating system:
   - **Windows**: OpenD_Win64.exe
   - **macOS**: OpenD_Mac.dmg
   - **Linux**: OpenD_Linux.tar.gz

3. Install OpenD on your system
4. Run OpenD - it will start a local gateway service on `127.0.0.1:11111` by default

### 3. Configure OpenD for Australian Market

1. Launch OpenD application
2. Log in with your Moomoo credentials
3. In OpenD settings, ensure:
   - **Paper Trading**: Enable simulation trading environment
   - **Market Access**: Confirm Australian (AU) market is enabled
   - **Port Configuration**: Note the port number (default: 11111)

### 4. Verify Connection

Run this test script to verify your setup:

```python
from moomoo import *

# Test quote connection
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
try:
    # Test with an ASX stock (CBA)
    ret, data = quote_ctx.get_market_snapshot(['AU.CBA'])
    if ret == RET_OK:
        print("✅ Quote connection successful")
        print(f"CBA Quote: {data}")
    else:
        print(f"❌ Quote error: {data}")
finally:
    quote_ctx.close()

# Test trading connection
trd_ctx = OpenSecTradeContext(
    filter_trdmarket=TrdMarket.AU,
    host='127.0.0.1', 
    port=11111,
    security_firm=SecurityFirm.FUTUAU
)
try:
    # Get account info
    ret, data = trd_ctx.accinfo_query(trd_env=TrdEnv.SIMULATE)
    if ret == RET_OK:
        print("✅ Trading connection successful")
        print(f"Paper Trading Account: {data}")
    else:
        print(f"❌ Trading error: {data}")
finally:
    trd_ctx.close()
```

### 5. Configure Your Trading System

Your trading system is already configured to use Moomoo! The `MoomooMLTrader` class in `app/core/trading/moomoo_integration.py` handles:

- **Paper Trading**: Automatically uses `TrdEnv.SIMULATE` for safe testing
- **ASX Symbol Conversion**: Converts `CBA.AX` format to `AU.CBA` format
- **ML Integration**: Compatible with your existing ML scoring system
- **Risk Management**: Includes position sizing and risk controls

### 6. Test with Your Trading System

Run these commands to test the integration:

```bash
# Test ML trading scores with Moomoo
python -m app.main ml-scores

# Test paper trading session (dry run)
python -m app.main ml-trading

# Test actual paper trading execution
python -m app.main ml-trading --execute
```

## Important Configuration Notes

### ASX Bank Symbols Mapping
Your system uses these ASX symbols which are automatically converted:
- `CBA.AX` → `AU.CBA` (Commonwealth Bank)
- `WBC.AX` → `AU.WBC` (Westpac)
- `ANZ.AX` → `AU.ANZ` (ANZ Bank)
- `NAB.AX` → `AU.NAB` (National Australia Bank)
- `MQG.AX` → `AU.MQG` (Macquarie Group)

### Paper Trading Environment
- All trades execute in simulation mode (`TrdEnv.SIMULATE`)
- No real money is used
- Positions and P&L are tracked in the simulation environment
- Performance metrics are saved to `data/moomoo/ml_trades.json`

### Market Hours
- OpenD must be running during market hours for real-time data
- ASX trading hours: 10:00 AM - 4:00 PM AEST
- OpenD can run 24/7 but real-time quotes are only available during market hours

## Troubleshooting

### Common Issues

1. **"Moomoo SDK not available"**
   - Solution: Run `pip install moomoo-api`

2. **Connection errors to OpenD**
   - Ensure OpenD is running
   - Check firewall settings allow local connections
   - Verify port 11111 is not blocked

3. **Authentication errors**
   - Verify Moomoo account credentials in OpenD
   - Ensure Australian market access is enabled in your Moomoo account

4. **No ASX data available**
   - Confirm OpenD is logged in with Australian market access
   - Check that `SecurityFirm.FUTUAU` is configured correctly

### Getting Help

- Moomoo API Documentation: https://openapi.moomoo.com/moomoo-api-doc/en/
- OpenD User Guide: Available in the OpenD application
- Australian Market Support: Contact Moomoo AU support if you need market access

## Next Steps

1. **Start OpenD**: Keep OpenD running in the background
2. **Run Paper Trading**: Use `python -m app.main ml-trading --execute` to start paper trading
3. **Monitor Performance**: Check ML trading performance with `python -m app.main trading-history`
4. **Review Results**: Access the dashboard to view your paper trading results

Your Moomoo integration is now ready for ASX paper trading!