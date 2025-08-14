#!/usr/bin/env python3
"""
Safe ML Analysis Runner
Prevents duplicate ML predictions by coordinating between processes
"""

import sys
import os
from process_coordinator import ProcessCoordinator

def run_safe_ml_analysis(process_name: str):
    """Run ML analysis with process coordination to prevent duplicates"""
    
    coordinator = ProcessCoordinator(process_name)
    
    # Try to acquire process lock
    if not coordinator.acquire_lock():
        print(f"⚠️  {process_name} process already running - skipping to prevent duplicates")
        return False
    
    try:
        # Check if we can run ML analysis
        if not coordinator.can_run_ml_analysis():
            print(f"⚠️  ML analysis already running - skipping to prevent duplicates")
            return False
        
        # Acquire ML analysis lock
        if not coordinator.acquire_ml_analysis_lock():
            print(f"⚠️  Failed to acquire ML analysis lock")
            return False
        
        try:
            # Import and run ML analysis
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
        print("Usage: python safe_ml_runner.py <process_name>")
        print("Example: python safe_ml_runner.py morning")
        print("Example: python safe_ml_runner.py evening")
        return
    
    process_name = sys.argv[1]
    
    if process_name not in ['morning', 'evening']:
        print(f"⚠️  Unknown process: {process_name}")
        print("Valid processes: morning, evening")
        return
    
    success = run_safe_ml_analysis(process_name)
    if success:
        print(f"🎉 {process_name} process completed successfully")
    else:
        print(f"❌ {process_name} process failed or was skipped")

if __name__ == "__main__":
    main()
