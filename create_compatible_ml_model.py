#!/usr/bin/env python3
"""
Create a simple 5-feature ML model that's compatible with the current news analyzer
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import json
import sqlite3
from datetime import datetime

def create_compatible_model():
    """Create a 5-feature model compatible with news analyzer"""
    
    print("🔧 Creating 5-feature compatible ML model...")
    
    # Define the 5 features that news analyzer provides
    feature_columns = ['sentiment', 'technical', 'volume', 'volatility', 'momentum']
    
    # Generate some realistic training data
    print("📊 Generating training data...")
    np.random.seed(42)  # For reproducibility
    
    # Create synthetic data that mimics real sentiment patterns
    n_samples = 1000
    
    # Generate correlated features
    sentiment = np.random.normal(0, 0.3, n_samples)  # Sentiment scores around 0
    technical = np.random.uniform(0, 1, n_samples)   # Technical confidence 0-1
    volume = np.random.exponential(0.3, n_samples)   # Volume ratio (exp distribution)
    volatility = np.abs(sentiment) + np.random.normal(0, 0.1, n_samples)  # Volatility correlates with sentiment magnitude
    momentum = sentiment * 0.7 + np.random.normal(0, 0.2, n_samples)  # Momentum correlates with sentiment
    
    # Clip values to reasonable ranges
    sentiment = np.clip(sentiment, -1, 1)
    technical = np.clip(technical, 0, 1)
    volume = np.clip(volume, 0, 2)
    volatility = np.clip(volatility, 0, 1)
    momentum = np.clip(momentum, -1, 1)
    
    # Create target variable based on realistic trading logic
    # BUY (1) when: positive sentiment, good technical, reasonable volume
    # SELL (0) when: negative sentiment, poor technical, or extreme volatility
    target = np.zeros(n_samples)
    
    for i in range(n_samples):
        score = 0
        # Sentiment contribution (40%)
        if sentiment[i] > 0.2:
            score += 0.4
        elif sentiment[i] < -0.2:
            score -= 0.4
            
        # Technical contribution (30%)
        if technical[i] > 0.6:
            score += 0.3
        elif technical[i] < 0.4:
            score -= 0.3
            
        # Volume contribution (20%)
        if 0.5 <= volume[i] <= 1.5:  # Normal volume range
            score += 0.2
        elif volume[i] > 2.0:  # Extreme volume
            score -= 0.1
            
        # Volatility penalty (10%)
        if volatility[i] > 0.7:
            score -= 0.1
            
        # Final decision
        target[i] = 1 if score > 0.2 else 0
    
    # Create DataFrame
    X = pd.DataFrame({
        'sentiment': sentiment,
        'technical': technical, 
        'volume': volume,
        'volatility': volatility,
        'momentum': momentum
    })
    
    y = target
    
    print(f"📈 Generated {len(X)} samples with {len(feature_columns)} features")
    print(f"📊 Target distribution: {np.sum(y == 1)} BUY, {np.sum(y == 0)} SELL")
    
    # Split the data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Create and train scaler
    print("🔧 Training scaler...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train.values)  # Use .values to remove feature names
    X_test_scaled = scaler.transform(X_test.values)       # Use .values to remove feature names
    
    # Create and train model
    print("🤖 Training RandomForest model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight='balanced'  # Handle any class imbalance
    )
    
    model.fit(X_train_scaled, y_train)
    
    # Evaluate model
    train_score = model.score(X_train_scaled, y_train)
    test_score = model.score(X_test_scaled, y_test)
    
    print(f"📊 Model performance:")
    print(f"   Training accuracy: {train_score:.3f}")
    print(f"   Test accuracy: {test_score:.3f}")
    
    # Get feature importance
    importance = pd.DataFrame({
        'feature': feature_columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"📈 Feature importance:")
    for _, row in importance.iterrows():
        print(f"   {row['feature']}: {row['importance']:.3f}")
    
    # Save model and scaler
    print("💾 Saving model and scaler...")
    joblib.dump(model, 'data/ml_models/current_model.pkl')
    joblib.dump(scaler, 'data/ml_models/feature_scaler.pkl')
    
    # Create metadata
    metadata = {
        'model_type': 'RandomForestClassifier',
        'features': feature_columns,
        'n_features': len(feature_columns),
        'created_at': datetime.now().isoformat(),
        'performance': {
            'train_accuracy': float(train_score),
            'test_accuracy': float(test_score),
            'best_threshold': 0.5
        },
        'feature_importance': {
            feature: float(importance) 
            for feature, importance in zip(feature_columns, model.feature_importances_)
        },
        'description': 'Simple 5-feature model compatible with news analyzer'
    }
    
    # Save metadata
    with open('data/ml_models/current_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("✅ Model, scaler, and metadata saved successfully!")
    
    # Test the model with sample data
    print("\n🧪 Testing model with sample data...")
    test_data = {
        'sentiment': 0.3,
        'technical': 0.7, 
        'volume': 0.8,
        'volatility': 0.2,
        'momentum': 0.1
    }
    test_features = pd.DataFrame([test_data])  # Use DataFrame with column names
    test_scaled = scaler.transform(test_features.values)  # Use .values to match training
    
    prediction = model.predict(test_scaled)[0]
    proba = model.predict_proba(test_scaled)[0]
    confidence = max(proba)
    
    print(f"   Input: sentiment=0.3, technical=0.7, volume=0.8, volatility=0.2, momentum=0.1")
    print(f"   Prediction: {'BUY' if prediction == 1 else 'SELL'}")
    print(f"   Confidence: {confidence:.3f}")
    
    return True

if __name__ == "__main__":
    success = create_compatible_model()
    if success:
        print("\n🎉 SUCCESS! Compatible 5-feature model created.")
        print("   The news analyzer should now work without feature mismatch errors.")
    else:
        print("\n❌ FAILED to create compatible model.")
