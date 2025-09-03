#!/usr/bin/env python3
"""
Simple Market-Aware Test Runner
"""

import sys
import os
from datetime import datetime

def create_test_log():
    """Create test log file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"market_aware_test_{timestamp}.log"
    
    with open(log_file, 'w') as f:
        f.write(f"Market-Aware System Test Log\n")
        f.write(f"Started: {datetime.now()}\n")
        f.write("="*50 + "\n\n")
    
    return log_file

def test_enhanced_system():
    """Test the enhanced market-aware system"""
    log_file = create_test_log()
    
    try:
        print("🚀 Testing Enhanced Market-Aware System")
        print(f"📁 Log file: {log_file}")
        
        # Test Settings import
        try:
            sys.path.append('app/config')
            from settings import Settings
            print("✅ Settings imported successfully")
            
            with open(log_file, 'a') as f:
                f.write("✅ Settings Module: PASS\n")
                f.write(f"   Bank symbols: {Settings.BANK_SYMBOLS}\n")
                f.write(f"   Extended symbols count: {len(Settings.EXTENDED_SYMBOLS)}\n\n")
                
        except Exception as e:
            print(f"❌ Settings import failed: {e}")
            with open(log_file, 'a') as f:
                f.write(f"❌ Settings Module: FAIL - {e}\n\n")
        
        # Test Enhanced System
        try:
            from enhanced_efficient_system_market_aware import test_market_aware_system
            print("✅ Enhanced system imported")
            
            print("🎯 Running market-aware predictions...")
            test_market_aware_system()
            print("✅ Market-aware test completed")
            
            with open(log_file, 'a') as f:
                f.write("✅ Enhanced System: PASS\n")
                f.write("   Market-aware predictions executed successfully\n\n")
                
        except Exception as e:
            print(f"❌ Enhanced system test failed: {e}")
            with open(log_file, 'a') as f:
                f.write(f"❌ Enhanced System: FAIL - {e}\n\n")
        
        # Test Paper Trading Integration
        try:
            from main import PaperTradingApp
            app = PaperTradingApp()
            
            signals = app.generate_trading_signals()
            print(f"✅ Paper trading app - Generated {len(signals)} signals")
            
            with open(log_file, 'a') as f:
                f.write("✅ Paper Trading Integration: PASS\n")
                f.write(f"   Generated {len(signals)} trading signals\n")
                for symbol, signal in list(signals.items())[:3]:  # Log first 3
                    f.write(f"   {symbol}: {signal['action']} ({signal['confidence']:.1%})\n")
                f.write("\n")
                
        except Exception as e:
            print(f"❌ Paper trading test failed: {e}")
            with open(log_file, 'a') as f:
                f.write(f"❌ Paper Trading Integration: FAIL - {e}\n\n")
        
        # Final summary
        with open(log_file, 'a') as f:
            f.write("="*50 + "\n")
            f.write(f"Test completed: {datetime.now()}\n")
            f.write("Check individual test results above\n")
        
        print(f"✅ Test completed - Check {log_file} for details")
        return log_file
        
    except Exception as e:
        print(f"❌ Test runner failed: {e}")
        with open(log_file, 'a') as f:
            f.write(f"❌ CRITICAL ERROR: {e}\n")
        return log_file

if __name__ == "__main__":
    log_file = test_enhanced_system()
    print(f"📄 Test log saved to: {log_file}")
