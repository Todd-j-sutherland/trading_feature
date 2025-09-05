#!/usr/bin/env python3
"""
Quick Symbol Verification Test
"""

import sys
sys.path.append('app/config')

try:
    from settings import Settings
    print(f"✅ Settings loaded successfully")
    print(f"📊 BANK_SYMBOLS: {Settings.BANK_SYMBOLS}")
    print(f"📈 Number of bank symbols: {len(Settings.BANK_SYMBOLS)}")
    
    if hasattr(Settings, 'EXTENDED_SYMBOLS'):
        print(f"📋 EXTENDED_SYMBOLS: {len(Settings.EXTENDED_SYMBOLS)} symbols")
    
    # Test enhanced system symbol selection
    from enhanced_efficient_system_market_aware import SETTINGS_AVAILABLE
    
    if SETTINGS_AVAILABLE:
        symbols = Settings.BANK_SYMBOLS.copy()
        print(f"🎯 Enhanced system will use: {len(symbols)} symbols")
        print(f"   Symbols: {symbols}")
    else:
        print("❌ Settings not available in enhanced system")
        
except Exception as e:
    print(f"❌ Error: {e}")
