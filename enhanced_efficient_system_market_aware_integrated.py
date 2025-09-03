#!/usr/bin/env python3
"""
Market-Aware Enhanced Efficient System
Integrates market context analysis with existing prediction system

This replaces enhanced_efficient_system_news_volume.py with market-aware capabilities
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    # Import market-aware daily manager
    from app.services.market_aware_daily_manager import create_market_aware_manager
    
    def main():
        """Main execution with market-aware analysis"""
        print("🚀 MARKET-AWARE ENHANCED PREDICTION SYSTEM")
        print("=" * 60)
        
        try:
            # Create market-aware manager
            manager = create_market_aware_manager(dry_run=False)
            
            # Run enhanced morning routine (includes market context + existing system)
            manager.enhanced_morning_routine()
            
            print("✅ Market-aware prediction cycle completed successfully")
            
        except Exception as e:
            print(f"❌ Market-aware system error: {e}")
            # Fallback to original system
            fallback_to_original_system()
    
    def fallback_to_original_system():
        """Fallback to original enhanced system if market-aware fails"""
        print("🔄 Falling back to original enhanced system...")
        
        try:
            # Import and run original system
            original_system_path = project_root / "enhanced_efficient_system_news_volume.py"
            if original_system_path.exists():
                import subprocess
                result = subprocess.run([sys.executable, str(original_system_path)], 
                                      cwd=project_root, capture_output=True, text=True)
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(f"Stderr: {result.stderr}")
            else:
                print("❌ Original system not found - manual intervention required")
                
        except Exception as e:
            print(f"❌ Fallback system also failed: {e}")

    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"❌ Market-aware system not available: {e}")
    print("🔄 Running standalone market-aware system...")
    
    # If market-aware daily manager import fails, use standalone system
    try:
        # Copy the enhanced standalone system from paper-trading-app
        standalone_path = project_root / "enhanced_efficient_system_market_aware.py"
        if standalone_path.exists():
            import subprocess
            result = subprocess.run([sys.executable, str(standalone_path)], 
                                  cwd=project_root, capture_output=True, text=True)
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(f"Stderr: {result.stderr}")
        else:
            print("❌ Standalone market-aware system not found")
            
    except Exception as e:
        print(f"❌ All market-aware systems failed: {e}")
        print("❌ Manual intervention required")
