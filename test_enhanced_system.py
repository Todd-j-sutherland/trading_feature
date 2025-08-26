#!/usr/bin/env python3
"""Test the enhanced efficient system"""

import sys
sys.path.append("/root/test")

# Import and modify the enhanced system
exec(open("enhanced_efficient_system.py").read())

# Create test instance
pred_system = EnhancedPredictionSystem()

# Override market hours check for testing
pred_system.is_market_hours = lambda: True

print("🧪 Testing Enhanced Prediction System...")
pred_system.run_predictions()
print("✅ Test completed")
