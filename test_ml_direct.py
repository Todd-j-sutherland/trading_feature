#!/usr/bin/env python3
import pickle
import numpy as np
import yfinance as yf

# Load models directly
print("Loading models...")
with open("models/current_direction_model.pkl", "rb") as f:
    direction_model = pickle.load(f)
    
with open("models/current_magnitude_model.pkl", "rb") as f:
    magnitude_model = pickle.load(f)
    
with open("models/feature_scaler.pkl", "rb") as f:
    scaler = pickle.load(f)

print("Models loaded successfully")

# Simple feature creation
features = np.array([1.0, 100.0, 101.0, 1.5, 0.02, 50.0, 100]).reshape(1, -1)
print(f"Features shape: {features.shape}")

# Test prediction
features_scaled = scaler.transform(features)
direction_prob = direction_model.predict_proba(features_scaled)[0]
predicted_direction = direction_model.predict(features_scaled)[0]
magnitude = abs(magnitude_model.predict(features_scaled)[0])

print(f"Direction: {"UP" if predicted_direction == 1 else "DOWN"}")
print(f"Magnitude: {magnitude}")
print("ML prediction test successful")
