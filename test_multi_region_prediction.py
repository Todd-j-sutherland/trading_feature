#!/usr/bin/env python3
"""
Test script for multi-region prediction service
"""
import asyncio
import sys
import os

# Add current directory to path to import services
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_multi_region_prediction():
    """Test multi-region prediction service functionality"""
    
    print("=" * 80)
    print("MULTI-REGION PREDICTION SERVICE TEST")
    print("=" * 80)
    
    try:
        # Import the service
        from services.prediction.prediction_service import PredictionService
        
        # Test 1: Initialize service with ASX region
        print("\n1. Testing ASX Region Initialization...")
        asx_service = PredictionService(default_region="asx")
        
        # Check current region
        region_info = await asx_service.get_current_region()
        print(f"   Current region: {region_info}")
        
        # Get available regions
        available_regions = await asx_service.get_available_regions()
        print(f"   Available regions: {available_regions}")
        
        # Get region symbols
        asx_symbols = await asx_service.get_region_symbols("asx")
        print(f"   ASX symbols: {asx_symbols.get('default_symbols', [])[:5]}...")
        
        # Test 2: Switch to USA region
        if available_regions.get('multi_region_available'):
            print("\n2. Testing Region Switch to USA...")
            switch_result = await asx_service.set_region("usa")
            print(f"   Switch result: {switch_result}")
            
            # Get USA symbols
            usa_symbols = await asx_service.get_region_symbols("usa")
            print(f"   USA symbols: {usa_symbols.get('default_symbols', [])[:5]}...")
            
            # Test 3: Generate predictions for USA
            print("\n3. Testing USA Predictions...")
            usa_predictions = await asx_service.generate_predictions(
                symbols=["JPM", "BAC"], 
                force_refresh=True
            )
            print(f"   USA predictions generated: {len(usa_predictions.get('predictions', {}))}")
            print(f"   Summary: {usa_predictions.get('summary', {})}")
            
            # Test 4: Generate predictions with region parameter (switch back)
            print("\n4. Testing Region Parameter in Predictions...")
            asx_predictions = await asx_service.generate_predictions(
                symbols=["CBA.AX", "ANZ.AX"], 
                region="asx",
                force_refresh=True
            )
            print(f"   ASX predictions generated: {len(asx_predictions.get('predictions', {}))}")
            print(f"   Summary: {asx_predictions.get('summary', {})}")
            
        else:
            print("\n2. Multi-region not available - testing fallback mode...")
            # Test fallback predictions
            fallback_predictions = await asx_service.generate_predictions(
                symbols=["CBA.AX", "ANZ.AX"], 
                force_refresh=True
            )
            print(f"   Fallback predictions generated: {len(fallback_predictions.get('predictions', {}))}")
            print(f"   Summary: {fallback_predictions.get('summary', {})}")
        
        # Test 5: Configuration info
        print("\n5. Testing Configuration Information...")
        config_info = await asx_service.get_prediction_config()
        print(f"   Cache TTL: {config_info.get('cache_ttl_seconds')}s")
        print(f"   Max symbols per request: {config_info.get('max_symbols_per_request')}")
        print(f"   Current region: {config_info.get('current_region', 'N/A')}")
        print(f"   Config source: {config_info.get('config_source', 'Unknown')}")
        
        print("\n" + "=" * 80)
        print("✅ Multi-region prediction service test completed successfully!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_config_manager_only():
    """Test just the config manager without the service"""
    
    print("\n" + "=" * 80)
    print("CONFIG MANAGER STANDALONE TEST")
    print("=" * 80)
    
    try:
        from app.config.regions.config_manager import ConfigManager
        
        # Test config manager
        config_manager = ConfigManager()
        
        print(f"Available regions: {config_manager.get_available_regions()}")
        
        # Test ASX configuration
        config_manager.set_region("asx")
        asx_symbols = config_manager.get_symbols()
        print(f"ASX symbols: {asx_symbols[:5]}...")
        
        # Test USA configuration
        config_manager.set_region("usa")
        usa_symbols = config_manager.get_symbols()
        print(f"USA symbols: {usa_symbols[:5]}...")
        
        print("✅ Config Manager test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Config Manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Multi-Region Trading Prediction System")
    print("=" * 60)
    
    # Test config manager first
    config_success = asyncio.run(test_config_manager_only())
    
    if config_success:
        # Test full service if config manager works
        service_success = asyncio.run(test_multi_region_prediction())
        
        if service_success:
            print("\n🎉 All tests passed! Multi-region system is working.")
        else:
            print("\n⚠️  Config manager works but service has issues.")
    else:
        print("\n⚠️  Config manager has issues - service may fall back to settings.py")
        # Try service anyway to test fallback
        service_success = asyncio.run(test_multi_region_prediction())
