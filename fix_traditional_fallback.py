# Read the file
with open("enhanced_ml_system/analyzers/enhanced_morning_analyzer_with_ml.py", "r") as f:
    content = f.read()

# Replace the hardcoded fallback with traditional signal usage
old_code = """                        if not self.enhanced_pipeline.has_sufficient_training_data():
                            # Use traditional signals until we have 100+ samples
                            ml_prediction = {
                                \"optimal_action\": \"HOLD\",
                                \"confidence_scores\": {\"average\": 0.5},
                                \"model_version\": \"traditional_emergency_v1\"
                            }
                            self.logger.info(f\"Using traditional signals for {symbol} (insufficient training data)\")"""

new_code = """                        if not self.enhanced_pipeline.has_sufficient_training_data():
                            # Use traditional signals until we have 100+ samples
                            traditional_signal = self._generate_traditional_signal(sentiment_data, technical_result, symbol)
                            ml_prediction = {
                                \"optimal_action\": traditional_signal.get(\"final_signal\", \"HOLD\"),
                                \"confidence_scores\": {\"average\": traditional_signal.get(\"overall_confidence\", 0.5)},
                                \"model_version\": \"traditional_emergency_v1\"
                            }
                            self.logger.info(f\"Using traditional signals for {symbol} (insufficient training data)\")"""

# Replace the code
content = content.replace(old_code, new_code)

# Write back
with open("enhanced_ml_system/analyzers/enhanced_morning_analyzer_with_ml.py", "w") as f:
    f.write(content)

print("✅ Fixed traditional fallback to use real signals")
