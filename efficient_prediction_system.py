#!/usr/bin/env python3
"""
Memory-Efficient Prediction System
Lightweight replacement for memory-intensive continuous collector
Designed for cron-based execution with minimal memory footprint
"""

import sys
import os
import gc
import json
from datetime import datetime
import traceback

# Add path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

class EfficientPredictionSystem:
    """Memory-efficient prediction system for scheduled execution"""
    
    def __init__(self):
        self.log_file = "/root/test/efficient_prediction_log.txt"
        self.symbols = ["CBA.AX", "ANZ.AX", "WBC.AX", "NAB.AX", "MQG.AX", "SUN.AX", "QBE.AX"]
        
    def log_message(self, message, also_print=True):
        """Log message to file and optionally print"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        if also_print:
            print(log_entry)
            
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")
    
    def run_lightweight_predictions(self):
        """Run predictions with minimal memory footprint"""
        try:
            self.log_message("🚀 Starting efficient prediction cycle")
            
            # Import only when needed to minimize memory
            from app.core.data.processors.news_processor import NewsTradingAnalyzer
            
            # Create analyzer with minimal configuration
            analyzer = NewsTradingAnalyzer()
            predictions_made = 0
            
            # Process each symbol individually and clean up
            for symbol in self.symbols:
                try:
                    # Quick analysis for single symbol
                    result = analyzer.analyze_single_bank(symbol, detailed=False)
                    
                    if result and "signal" in result:
                        signal = result.get("signal", "HOLD")
                        confidence = result.get("confidence", 0.5)
                        sentiment = result.get("sentiment_score", 0.0)
                        
                        self.log_message(f"✅ {symbol}: {signal} (conf: {confidence:.3f}, sent: {sentiment:+.3f})")
                        predictions_made += 1
                    else:
                        self.log_message(f"⚠️ {symbol}: No prediction generated")
                        
                    # Force garbage collection after each symbol
                    gc.collect()
                    
                except Exception as e:
                    self.log_message(f"❌ {symbol}: Error - {str(e)}")
                    continue
            
            # Final cleanup
            del analyzer
            gc.collect()
            
            self.log_message(f"🎯 Prediction cycle complete: {predictions_made}/{len(self.symbols)} predictions")
            return True
            
        except Exception as e:
            self.log_message(f"❌ Critical error in prediction cycle: {str(e)}")
            return False
    
    def validate_market_hours(self):
        """Check if we are in ASX market hours (10 AM - 4 PM AEST)"""
        try:
            now = datetime.now()
            hour = now.hour
            
            # Assuming system is in AEST
            if 10 <= hour <= 15:  # 10 AM to 3 PM
                return True
            else:
                self.log_message(f"⏰ Outside market hours (current: {hour:02d}:xx AEST)")
                return False
        except Exception as e:
            self.log_message(f"❌ Error checking market hours: {e}")
            return False

def main():
    """Main execution function for cron scheduling"""
    system = EfficientPredictionSystem()
    
    # Check if we should run (market hours validation)
    if not system.validate_market_hours():
        system.log_message("🕐 Skipping prediction cycle - outside market hours")
        return
    
    # Run the efficient prediction cycle
    success = system.run_lightweight_predictions()
    
    if success:
        system.log_message("✅ Efficient prediction cycle completed successfully")
    else:
        system.log_message("❌ Prediction cycle failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
