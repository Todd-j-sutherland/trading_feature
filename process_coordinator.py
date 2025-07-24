#!/usr/bin/env python3
"""
Process coordinator to prevent duplicate predictions when running main morning/evening
Creates lock files to ensure only one process runs ML analysis at a time
"""

import os
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

class ProcessCoordinator:
    def __init__(self, process_name: str):
        self.process_name = process_name
        self.lock_dir = Path("data/locks")
        self.lock_dir.mkdir(exist_ok=True)
        self.lock_file = self.lock_dir / f"{process_name}.lock"
        self.ml_analysis_lock = self.lock_dir / "ml_analysis.lock"
        
    def acquire_lock(self, timeout_minutes: int = 30) -> bool:
        """Acquire a lock for this process"""
        
        # Check if lock already exists and is recent
        if self.lock_file.exists():
            try:
                with open(self.lock_file, 'r') as f:
                    lock_data = json.load(f)
                
                lock_time = datetime.fromisoformat(lock_data['timestamp'])
                if datetime.now() - lock_time < timedelta(minutes=timeout_minutes):
                    print(f"🔒 Process {self.process_name} already running (locked at {lock_time.strftime('%H:%M:%S')})")
                    return False
                else:
                    print(f"🗑️  Cleaning up stale lock from {lock_time.strftime('%H:%M:%S')}")
                    
            except Exception as e:
                print(f"⚠️  Error reading lock file: {e}")
        
        # Create new lock
        lock_data = {
            'process': self.process_name,
            'timestamp': datetime.now().isoformat(),
            'pid': os.getpid()
        }
        
        with open(self.lock_file, 'w') as f:
            json.dump(lock_data, f, indent=2)
        
        print(f"✅ Acquired lock for {self.process_name}")
        return True
    
    def release_lock(self):
        """Release the lock for this process"""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
                print(f"🔓 Released lock for {self.process_name}")
        except Exception as e:
            print(f"⚠️  Error releasing lock: {e}")
    
    def can_run_ml_analysis(self) -> bool:
        """Check if ML analysis can run (no other process is running it)"""
        
        if self.ml_analysis_lock.exists():
            try:
                with open(self.ml_analysis_lock, 'r') as f:
                    lock_data = json.load(f)
                
                lock_time = datetime.fromisoformat(lock_data['timestamp'])
                # ML analysis should not run if locked within last 10 minutes
                if datetime.now() - lock_time < timedelta(minutes=10):
                    print(f"🚫 ML analysis blocked - running by {lock_data.get('process', 'unknown')} since {lock_time.strftime('%H:%M:%S')}")
                    return False
                else:
                    print(f"🗑️  Cleaning up stale ML analysis lock from {lock_time.strftime('%H:%M:%S')}")
                    self.ml_analysis_lock.unlink()
                    
            except Exception as e:
                print(f"⚠️  Error reading ML analysis lock: {e}")
        
        return True
    
    def acquire_ml_analysis_lock(self) -> bool:
        """Acquire ML analysis lock"""
        
        if not self.can_run_ml_analysis():
            return False
        
        lock_data = {
            'process': self.process_name,
            'timestamp': datetime.now().isoformat(),
            'pid': os.getpid()
        }
        
        with open(self.ml_analysis_lock, 'w') as f:
            json.dump(lock_data, f, indent=2)
        
        print(f"🔬 Acquired ML analysis lock for {self.process_name}")
        return True
    
    def release_ml_analysis_lock(self):
        """Release ML analysis lock"""
        try:
            if self.ml_analysis_lock.exists():
                self.ml_analysis_lock.unlink()
                print(f"🔓 Released ML analysis lock")
        except Exception as e:
            print(f"⚠️  Error releasing ML analysis lock: {e}")

def main():
    """Test the coordinator"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python process_coordinator.py <process_name>")
        print("Example: python process_coordinator.py morning")
        return
    
    process_name = sys.argv[1]
    coordinator = ProcessCoordinator(process_name)
    
    if coordinator.acquire_lock():
        print(f"Running {process_name} process...")
        
        if coordinator.acquire_ml_analysis_lock():
            print("Running ML analysis...")
            time.sleep(2)  # Simulate ML analysis
            coordinator.release_ml_analysis_lock()
        
        time.sleep(1)  # Simulate other work
        coordinator.release_lock()
    else:
        print(f"Cannot run {process_name} - another instance is running")

if __name__ == "__main__":
    main()
