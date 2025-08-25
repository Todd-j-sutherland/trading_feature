# Fix the confidence extraction in _save_predictions_if_available method
import re

# Read the file
with open("enhanced_morning_analyzer_with_ml.py", "r") as f:
    content = f.read()

# Find and replace the confidence extraction logic
old_confidence_logic =  # Fix: Use the real ML confidence from confidence_scores.average, fallback -9999 indicates missing data
