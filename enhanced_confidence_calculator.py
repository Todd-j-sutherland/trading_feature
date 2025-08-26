import re

def create_enhanced_confidence_logic():
    return """            # Enhanced confidence calculation using multiple factors
            base_confidence = 0.3
            
            # Factor 1: Technical Score (0-40 points)
            tech_factor = min(tech_score / 100 * 0.4, 0.4)
            
            # Factor 2: RSI positioning (0-20 points)
            rsi_factor = 0.0
            if 30 <= rsi <= 70:  # Healthy range
                rsi_factor = 0.15
            elif 70 < rsi <= 80:  # Strong momentum
                rsi_factor = 0.20
            elif 20 < rsi < 30:   # Oversold opportunity
                rsi_factor = 0.18
            elif rsi > 80:        # Overbought risk
                rsi_factor = 0.05
            elif rsi < 20:        # Extreme oversold
                rsi_factor = 0.10
            
            # Factor 3: Price momentum from feature vector
            feature_parts = tech_data["feature_vector"].split(",")
            momentum = float(feature_parts[5]) if len(feature_parts) > 5 else 0
            momentum_factor = min(abs(momentum) / 5.0 * 0.15, 0.15)  # Up to 15 points
            
            # Factor 4: Volatility consideration
            volatility = float(feature_parts[6]) if len(feature_parts) > 6 else 1
            volatility_factor = 0.05 if volatility < 1.5 else (-0.05 if volatility > 3.0 else 0)
            
            # Factor 5: Moving average relationship
            ma5 = float(feature_parts[2]) if len(feature_parts) > 2 else current_price
            ma20 = float(feature_parts[3]) if len(feature_parts) > 3 else current_price
            ma_factor = 0.0
            if current_price > ma5 > ma20:  # Strong uptrend
                ma_factor = 0.10
            elif current_price > ma5 and current_price > ma20:  # Uptrend
                ma_factor = 0.05
            elif current_price < ma5 < ma20:  # Strong downtrend
                ma_factor = -0.05
            
            # Calculate final confidence
            confidence = base_confidence + tech_factor + rsi_factor + momentum_factor + volatility_factor + ma_factor
            confidence = max(0.2, min(confidence, 0.95))  # Clamp between 20% and 95%
            
            # Adjust action based on enhanced confidence
            if confidence < 0.35:
                action = "HOLD"
            elif confidence > 0.65 and tech_score > 60:
                action = "BUY"
            elif confidence > 0.75:
                action = "STRONG_BUY" if tech_score > 70 else "BUY"
            else:
                action = "HOLD\""""

# Read current file
with open("enhanced_efficient_system.py", "r") as f:
    content = f.read()

# Find and replace the old confidence logic
old_logic = """            # Decision logic
            confidence = 0.4
            action = "HOLD"
            
            if tech_score > 65 and rsi > 50:
                action = "BUY"
                confidence = 0.6 + (tech_score - 65) / 100
            elif tech_score < 40:
                action = "HOLD"
                confidence = 0.5
            elif 30 < rsi < 70 and tech_score > 55:
                action = "BUY"
                confidence = 0.5 + (tech_score - 55) / 200
            
            confidence = min(confidence, 0.8)"""

new_logic = create_enhanced_confidence_logic()

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    print("✅ Enhanced confidence calculation logic")
else:
    print("❌ Could not find old logic to replace")

# Write back
with open("enhanced_efficient_system.py", "w") as f:
    f.write(content)

print("✅ Enhanced confidence calculation implemented")
