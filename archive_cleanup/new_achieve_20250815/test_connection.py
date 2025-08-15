#!/usr/bin/env python3
"""Quick connection test for Moomoo OpenD"""

try:
    from moomoo import *
    print("✅ Moomoo SDK imported successfully")
    
    quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)
    ret, data = quote_ctx.get_market_snapshot(['AU.CBA'])
    
    print(f"Connection test result: {ret}")
    if ret == RET_OK:
        print("✅ Connection successful!")
        print(f"CBA data: {data}")
    else:
        print(f"❌ Connection failed: {data}")
    
    quote_ctx.close()
    
except ImportError as e:
    print(f"❌ Moomoo SDK not installed: {e}")
    print("Run: pip install moomoo-api")
except Exception as e:
    print(f"❌ Connection error: {e}")
    print("Make sure OpenD is running and logged in")