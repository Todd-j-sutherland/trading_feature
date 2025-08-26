#!/usr/bin/env python3
"""Simple ML Training to get models working"""

import sqlite3
import json
import pickle
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
import warnings
warnings.filterwarnings("ignore")

def get_training_data():
    """Get all training data from database"""
    conn = sqlite3.connect("predictions.db")
    cursor = conn.cursor()
    
    query = """
    SELECT 
        p.symbol,
        p.predicted_action,
        p.action_confidence,
        p.feature_vector,
        o.actual_return
    FROM predictions p
    JOIN outcomes o ON p.prediction_id = o.prediction_id
    WHERE o.actual_return IS NOT NULL
    """
    
    cursor.execute(query)
    data = cursor.fetchall()
    conn.close()
    
    return data

def parse_feature_vector(fv_str):
    """Parse feature vector string"""
    if not fv_str:
        return [50.0, 50.0, 100.0, 100.0, 100.0, 0.0, 1.0, 50.0, 50.0]
    try:
        return [float(x.strip()) for x in fv_str.split(",")][:9]
    except:
        return [50.0, 50.0, 100.0, 100.0, 100.0, 0.0, 1.0, 50.0, 50.0]

def train_symbol_models(symbol, data):
    """Train models for a single symbol"""
    # Filter data for this symbol
    symbol_data = [row for row in data if row[0] == symbol]
    
    if len(symbol_data) < 5:
        print(f"⚠️ {symbol}: Only {len(symbol_data)} samples")
        return None
    
    # Parse features and targets
    features = []
    returns = []
    
    for row in symbol_data:
        fv = parse_feature_vector(row[3])
        features.append(fv)
        returns.append(row[4])  # actual_return
    
    X = np.array(features)
    y_direction = np.array([1 if r > 0.001 else 0 for r in returns])
    y_magnitude = np.array([abs(r) for r in returns])
    
    # Train direction model
    direction_model = RandomForestClassifier(n_estimators=30, random_state=42)
    direction_model.fit(X, y_direction)
    
    # Train magnitude model  
    magnitude_model = RandomForestRegressor(n_estimators=30, random_state=42)
    magnitude_model.fit(X, y_magnitude)
    
    # Calculate performance
    dir_pred = direction_model.predict(X)
    dir_accuracy = accuracy_score(y_direction, dir_pred)
    
    mag_pred = magnitude_model.predict(X)
    mag_mse = mean_squared_error(y_magnitude, mag_pred)
    
    print(f"✅ {symbol}: {len(symbol_data)} samples, acc: {dir_accuracy:.3f}, mse: {mag_mse:.4f}")
    
    return {
        "direction": direction_model,
        "magnitude": magnitude_model,
        "performance": {
            "direction_accuracy": dir_accuracy,
            "magnitude_mse": mag_mse,
            "samples": len(symbol_data)
        }
    }

def save_models(symbol, models):
    """Save models for a symbol"""
    models_dir = Path("models") / symbol
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Save direction model
    with open(models_dir / "direction_model.pkl", "wb") as f:
        pickle.dump(models["direction"], f)
    
    # Save magnitude model
    with open(models_dir / "magnitude_model.pkl", "wb") as f:
        pickle.dump(models["magnitude"], f)
    
    # Save metadata
    metadata = {
        "symbol": symbol,
        "model_version": "2.1",
        "performance": models["performance"],
        "feature_names": ["rsi", "tech_score", "price_1", "price_2", "price_3", "vol", "volume_ratio", "momentum_1", "momentum_2"]
    }
    
    with open(models_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"💾 {symbol}: Models saved")

def main():
    print("🧠 SIMPLE ML TRAINING")
    print("=" * 40)
    
    # Get all training data
    data = get_training_data()
    print(f"📊 Total training samples: {len(data)}")
    
    # Train models for each symbol
    symbols = ["CBA.AX", "ANZ.AX", "WBC.AX", "NAB.AX", "MQG.AX"]
    success_count = 0
    
    for symbol in symbols:
        models = train_symbol_models(symbol, data)
        if models:
            save_models(symbol, models)
            success_count += 1
    
    print(f"\n🎯 SUMMARY: {success_count}/{len(symbols)} symbols trained successfully")
    
    # Check saved models
    models_dir = Path("models")
    if models_dir.exists():
        saved_models = list(models_dir.glob("*/metadata.json"))
        print(f"💾 Models saved: {len(saved_models)}")

if __name__ == "__main__":
    main()
