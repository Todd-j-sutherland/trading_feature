import re

with open("enhanced_efficient_system.py", "r") as f:
    content = f.read()

# Fix the INSERT statement to match the correct column order
old_insert = """            cursor.execute(\"\"\"
                INSERT INTO predictions (
                    prediction_id, symbol, prediction_timestamp, predicted_action,
                    predicted_direction, predicted_magnitude,
                    action_confidence, entry_price, feature_vector, model_version, optimal_action
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            \"\"\", (
                prediction_id,
                prediction[\"symbol\"],
                datetime.now().isoformat(),
                prediction[\"action\"],
                prediction[\"confidence\"],
                prediction[\"price\"],
                prediction[\"feature_vector\"],
                prediction[\"predicted_direction\"],
                prediction[\"predicted_magnitude\"],
                \"enhanced_efficient_v1.0\",
                prediction[\"optimal_action\"]
            ))"""

new_insert = """            cursor.execute(\"\"\"
                INSERT INTO predictions (
                    prediction_id, symbol, prediction_timestamp, predicted_action,
                    action_confidence, predicted_direction, predicted_magnitude,
                    feature_vector, model_version, entry_price, optimal_action
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            \"\"\", (
                prediction_id,
                prediction[\"symbol\"],
                datetime.now().isoformat(),
                prediction[\"action\"],
                prediction[\"confidence\"],
                prediction[\"predicted_direction\"],
                prediction[\"predicted_magnitude\"],
                prediction[\"feature_vector\"],
                \"enhanced_efficient_v1.0\",
                prediction[\"price\"],
                prediction[\"optimal_action\"]
            ))"""

# Replace the problematic section
content = content.replace(old_insert, new_insert)

with open("enhanced_efficient_system.py", "w") as f:
    f.write(content)

print("✅ Fixed column order in database insertion")
