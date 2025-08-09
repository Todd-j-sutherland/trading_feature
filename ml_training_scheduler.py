#!/usr/bin/env python3
"""
Simple ML Training Scheduler - Run this regularly for automatic training
"""

import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta

def should_run_training():
    """Check if training should run based on data and time"""
    
    try:
        conn = sqlite3.connect('./data/trading_unified.db')
        
        # Get total samples
        cursor = conn.execute("SELECT COUNT(*) FROM enhanced_outcomes")
        total_samples = cursor.fetchone()[0]
        
        # Get last training
        cursor = conn.execute("""
            SELECT training_date, training_samples 
            FROM model_performance_enhanced 
            ORDER BY training_date DESC LIMIT 1
        """)
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            print(f"📊 No previous training found. Starting first training.")
            return True, "first_training"
        
        last_training_date, last_samples = result
        new_samples = total_samples - last_samples
        
        # Check time since last training
        last_time = datetime.fromisoformat(last_training_date)
        hours_since = (datetime.now() - last_time).total_seconds() / 3600
        
        print(f"📊 Training Status Check:")
        print(f"   Total samples: {total_samples}")
        print(f"   Last training: {last_training_date}")
        print(f"   New samples: {new_samples}")
        print(f"   Hours since training: {hours_since:.1f}")
        
        # Training triggers
        if new_samples >= 5:
            return True, f"new_samples_{new_samples}"
        elif hours_since >= 12:
            return True, f"time_trigger_{hours_since:.1f}h"
        else:
            return False, f"no_trigger_needed"
            
    except Exception as e:
        print(f"❌ Error checking training status: {e}")
        return True, "error_fallback"

def run_evening_routine():
    """Run the evening routine which includes ML training"""
    
    try:
        print("🌅 Running evening routine with ML training...")
        
        result = subprocess.run([
            sys.executable, "-m", "app.main", "evening"
        ], capture_output=True, text=True, timeout=600)  # 10 minute timeout
        
        if result.returncode == 0:
            print("✅ Evening routine completed successfully")
            return True
        else:
            print(f"❌ Evening routine failed:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Evening routine timed out after 10 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running evening routine: {e}")
        return False

def force_ml_training():
    """Force ML training directly"""
    
    try:
        print("🧠 Force running ML training...")
        
        result = subprocess.run([
            sys.executable, "diagnose_ml_training.py", "--force"
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        if result.returncode == 0:
            print("✅ Forced ML training completed")
            print(result.stdout)
            return True
        else:
            print(f"❌ Forced training failed:")
            print(f"STDERR: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error in forced training: {e}")
        return False

def main():
    print("🤖 ML Training Scheduler")
    print("=" * 30)
    print(f"🕐 Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if training should run
    should_train, reason = should_run_training()
    
    if not should_train:
        print(f"ℹ️ No training needed: {reason}")
        return
    
    print(f"🎯 Training triggered: {reason}")
    
    # Try evening routine first (preferred method)
    if run_evening_routine():
        print("✅ Training completed via evening routine")
    else:
        print("🔄 Evening routine failed, trying direct training...")
        
        # Fallback to direct training
        if force_ml_training():
            print("✅ Training completed via direct method")
        else:
            print("❌ All training methods failed")
            sys.exit(1)
    
    print("🏁 Training scheduler completed successfully")

if __name__ == "__main__":
    main()
