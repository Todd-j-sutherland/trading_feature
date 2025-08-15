#!/usr/bin/env python3
"""
Safe ML Runner with Cleanup
Cleans up recent duplicates AND runs ML analysis with coordination
"""

import sys
from process_coordinator import ProcessCoordinator
from cleanup_duplicate_predictions import cleanup_duplicate_predictions

def run_safe_ml_with_cleanup(process_name: str):
    """Run ML analysis with cleanup and coordination"""
    
    coordinator = ProcessCoordinator(process_name)
    
    # Try to acquire process lock
    if not coordinator.acquire_lock():
        print(f"⚠️  {process_name} process already running - skipping to prevent duplicates")
        return False
    
    try:
        # Step 1: Clean up any existing duplicates first
        print(f"🧹 Cleaning up duplicates before {process_name} analysis...")
        cleanup_duplicate_predictions()
        
        # Step 2: Check if we can run ML analysis
        if not coordinator.can_run_ml_analysis():
            print(f"⚠️  ML analysis already running - skipping to prevent duplicates")
            return False
        
        # Step 3: Acquire ML analysis lock
        if not coordinator.acquire_ml_analysis_lock():
            print(f"⚠️  Failed to acquire ML analysis lock")
            return False
        
        try:
            # Step 4: Import and run ML analysis
            from app.core.ml.trading_manager import MLTradingManager
            
            print(f"🚀 Starting {process_name} ML analysis...")
            manager = MLTradingManager()
            
            # Run the analysis
            result = manager.run_daily_ml_analysis()
            
            print(f"✅ {process_name} ML analysis completed successfully")
            return True
            
        finally:
            coordinator.release_ml_analysis_lock()
    
    finally:
        coordinator.release_lock()
    
    return False

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python safe_ml_runner_with_cleanup.py <process_name>")
        print("Example: python safe_ml_runner_with_cleanup.py morning")
        print("Example: python safe_ml_runner_with_cleanup.py evening")
        print("\nThis script will:")
        print("- Clean up duplicate predictions first")
        print("- Then run ML analysis with coordination")
        return
    
    process_name = sys.argv[1]
    
    if process_name not in ['morning', 'evening']:
        print(f"⚠️  Unknown process: {process_name}")
        print("Valid processes: morning, evening")
        return
    
    success = run_safe_ml_with_cleanup(process_name)
    if success:
        print(f"🎉 {process_name} process with cleanup completed successfully")
    else:
        print(f"❌ {process_name} process failed or was skipped")

if __name__ == "__main__":
    main()
