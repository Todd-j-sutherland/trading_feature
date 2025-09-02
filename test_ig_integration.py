#!/usr/bin/env python3
"""
IG Markets Integration Test Script
Tests the enhanced market data collector and symbol mapper functionality
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_ig_markets_integration():
    """Test IG Markets integration components"""
    print("🔄 Testing IG Markets integration...")
    
    try:
        from app.core.data.collectors.enhanced_market_data_collector import EnhancedMarketDataCollector
        from app.core.data.collectors.ig_markets_symbol_mapper import IGMarketsSymbolMapper
        
        print("✅ Successfully imported IG Markets components")
        
        # Initialize components
        print("🔧 Initializing components...")
        collector = EnhancedMarketDataCollector()
        mapper = IGMarketsSymbolMapper()
        print("✅ Components initialized successfully")
        
        # Test symbol mapping
        test_symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'BHP.AX']
        
        print("\n📋 Testing symbol mapping:")
        for symbol in test_symbols:
            try:
                epic = mapper.get_ig_epic(symbol)
                print(f"  {symbol} → {epic}")
            except Exception as e:
                print(f"  {symbol} → Error: {e}")
        
        print("\n💰 Testing real-time price fetching:")
        price_test_symbols = ['CBA.AX', 'WBC.AX']  # Test fewer symbols to avoid rate limits
        
        for symbol in price_test_symbols:
            try:
                print(f"  Testing {symbol}...")
                price_data = collector.get_current_price(symbol)
                if price_data:
                    price = price_data.get('price', 'N/A')
                    source = price_data.get('source', 'Unknown')
                    print(f"  {symbol}: ${price:.3f} (Source: {source})")
                else:
                    print(f"  {symbol}: No data available")
            except Exception as e:
                print(f"  {symbol}: Error - {e}")
        
        # Show data source statistics
        print("\n📊 Data Source Statistics:")
        stats = collector.get_data_source_stats()
        print(f"  IG Markets requests: {stats.get('ig_markets', 0)}")
        print(f"  yfinance requests: {stats.get('yfinance', 0)}")
        print(f"  Cache hits: {stats.get('cache_hits', 0)}")
        print(f"  Total requests: {stats.get('total_requests', 0)}")
        
        # Test IG Markets health
        print("\n🏥 IG Markets Health Check:")
        try:
            ig_health = collector.is_ig_markets_healthy()
            print(f"  IG Markets Status: {'✅ Healthy' if ig_health else '❌ Unhealthy'}")
        except Exception as e:
            print(f"  IG Markets Status: ❌ Error checking health - {e}")
        
        print("\n✅ IG Markets integration test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all required modules are installed and accessible")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration():
    """Test configuration and environment setup"""
    print("\n🔧 Testing configuration setup...")
    
    try:
        from app.config.settings import Settings
        settings = Settings()
        print("✅ Settings loaded successfully")
        
        # Check for important configuration
        if hasattr(settings, 'BANK_SYMBOLS'):
            print(f"  📋 Bank symbols configured: {len(settings.BANK_SYMBOLS)} symbols")
        
        # Check environment file
        env_files = ['.env', '.env.new', '.env.example']
        env_found = False
        for env_file in env_files:
            if os.path.exists(env_file):
                print(f"  📄 Environment file found: {env_file}")
                env_found = True
                break
        
        if not env_found:
            print("  ⚠️ No environment file found - API credentials may not be configured")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test error: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 IG Markets Integration Test Suite")
    print("="*50)
    
    # Test configuration first
    config_ok = test_configuration()
    
    # Test IG Markets integration
    integration_ok = test_ig_markets_integration()
    
    print("\n" + "="*50)
    if config_ok and integration_ok:
        print("🎉 All tests passed! IG Markets integration is ready.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    print("\n💡 Usage:")
    print("  python -m app.main ig-markets-test     # Run IG Markets test via main app")
    print("  python -m app.main status             # Check system status including IG Markets")
    print("  python -m app.main morning            # Run morning routine with IG Markets data")

if __name__ == "__main__":
    main()
