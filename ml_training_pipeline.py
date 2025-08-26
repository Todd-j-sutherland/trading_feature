#!/usr/bin/env python3
"""
ML Training Pipeline for Evening Routine
Builds and trains models using prediction/outcome data
"""

import sqlite3
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
import warnings
warnings.filterwarnings("ignore")

class MLTrainingPipeline:
    """Complete ML training pipeline for evening routine"""
    
    def __init__(self, db_path="predictions.db"):
        self.db_path = db_path
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
        # Symbols to train
        self.symbols = ["CBA.AX", "ANZ.AX", "WBC.AX", "NAB.AX", "MQG.AX"]
        
        print(f"🧠 ML Training Pipeline initialized")
        print(f"📁 Models directory: {self.models_dir}")
        
    def extract_training_data(self, symbol=None):
        """Extract training data from predictions and outcomes"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT 
                p.symbol,
                p.predicted_action,
                p.action_confidence,
                p.feature_vector,
                o.actual_return,
                o.actual_direction,
                p.prediction_timestamp,
                o.evaluation_timestamp
            FROM predictions p
            JOIN outcomes o ON p.prediction_id = o.prediction_id
            WHERE o.actual_return IS NOT NULL
            """
            
            if symbol:
                query += f" AND p.symbol = {symbol}"
            
            query += " ORDER BY p.prediction_timestamp"
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            print(f"📊 Extracted {len(df)} training samples")
            if symbol:
                print(f"   🎯 Symbol: {symbol}")
            else:
                print(f"   📈 Symbols: {df[symbol].value_counts().to_dict()}")
                
            return df
            
        except Exception as e:
            print(f"❌ Error extracting training data: {e}")
            return pd.DataFrame()
    
    def parse_feature_vector(self, feature_vector_str):
        """Parse feature vector string into numerical array"""
        try:
            if not feature_vector_str or feature_vector_str == "":
                # Return default feature vector
                return np.array([50.0, 50.0, 100.0, 100.0, 100.0, 0.0, 1.0, 50.0, 50.0])
            
            # Parse comma-separated values
            features = [float(x.strip()) for x in feature_vector_str.split(",")]
            
            # Ensure we have 9 features (pad or truncate if necessary)
            while len(features) < 9:
                features.append(0.0)
            
            return np.array(features[:9])
            
        except Exception as e:
            print(f"⚠️ Error parsing feature vector {feature_vector_str}: {e}")
            return np.array([50.0, 50.0, 100.0, 100.0, 100.0, 0.0, 1.0, 50.0, 50.0])
    
    def prepare_features_targets(self, df):
        """Prepare feature matrix and target variables"""
        try:
            # Parse feature vectors
            features = []
            for fv in df[feature_vector]:
                features.append(self.parse_feature_vector(fv))
            
            X = np.array(features)
            
            # Direction targets (1 for up, 0 for down/sideways)
            y_direction = (df[actual_return] > 0.001).astype(int)
            
            # Magnitude targets (absolute return)
            y_magnitude = df[actual_return].abs()
            
            # Confidence targets (how accurate was the confidence?)
            predicted_up = (df[predicted_action] == BUY).astype(int)
            actual_up = (df[actual_return] > 0.001).astype(int)
            confidence_accuracy = (predicted_up == actual_up).astype(float)
            
            print(f"✅ Features prepared: {X.shape}")
            print(f"   📈 Direction targets: {sum(y_direction)}/{len(y_direction)} positive")
            print(f"   💰 Magnitude range: {y_magnitude.min():.4f} - {y_magnitude.max():.4f}")
            print(f"   �� Confidence accuracy: {confidence_accuracy.mean():.3f}")
            
            return X, y_direction, y_magnitude, confidence_accuracy
            
        except Exception as e:
            print(f"❌ Error preparing features: {e}")
            return None, None, None, None
    
    def train_models(self, symbol, X, y_direction, y_magnitude, confidence_accuracy):
        """Train direction, magnitude, and confidence models"""
        try:
            if len(X) < 5:
                print(f"⚠️ {symbol}: Insufficient data ({len(X)} samples)")
                return None
            
            # Split data
            test_size = min(0.3, max(0.1, 1.0 / len(X)))
            X_train, X_test, y_dir_train, y_dir_test = train_test_split(
                X, y_direction, test_size=test_size, random_state=42
            )
            _, _, y_mag_train, y_mag_test = train_test_split(
                X, y_magnitude, test_size=test_size, random_state=42
            )
            _, _, y_conf_train, y_conf_test = train_test_split(
                X, confidence_accuracy, test_size=test_size, random_state=42
            )
            
            models = {}
            performance = {}
            
            # Direction model (classification)
            direction_model = RandomForestClassifier(n_estimators=50, random_state=42)
            direction_model.fit(X_train, y_dir_train)
            dir_pred = direction_model.predict(X_test)
            dir_accuracy = accuracy_score(y_dir_test, dir_pred)
            
            models[direction] = direction_model
            performance[direction_accuracy] = dir_accuracy
            
            # Magnitude model (regression)
            magnitude_model = RandomForestRegressor(n_estimators=50, random_state=42)
            magnitude_model.fit(X_train, y_mag_train)
            mag_pred = magnitude_model.predict(X_test)
            mag_mse = mean_squared_error(y_mag_test, mag_pred)
            
            models[magnitude] = magnitude_model
            performance[magnitude_mse] = mag_mse
            
            # Confidence model (regression)
            confidence_model = RandomForestRegressor(n_estimators=50, random_state=42)
            confidence_model.fit(X_train, y_conf_train)
            conf_pred = confidence_model.predict(X_test)
            conf_mse = mean_squared_error(y_conf_test, conf_pred)
            
            models[confidence] = confidence_model
            performance[confidence_mse] = conf_mse
            
            print(f"✅ {symbol}: Models trained")
            print(f"   📈 Direction accuracy: {dir_accuracy:.3f}")
            print(f"   💰 Magnitude MSE: {mag_mse:.4f}")
            print(f"   🎯 Confidence MSE: {conf_mse:.4f}")
            
            return models, performance
            
        except Exception as e:
            print(f"❌ Error training models for {symbol}: {e}")
            return None, None
    
    def save_models(self, symbol, models, performance):
        """Save trained models and metadata"""
        try:
            symbol_dir = self.models_dir / symbol
            symbol_dir.mkdir(exist_ok=True)
            
            # Save models
            for model_type, model in models.items():
                model_path = symbol_dir / f"{model_type}_model.pkl"
                with open(model_path, wb) as f:
                    pickle.dump(model, f)
            
            # Save metadata
            metadata = {
                symbol: symbol,
                trained_at: datetime.now().isoformat(),
                performance: performance,
                model_version: 2.1,
                feature_names: [
                    rsi, tech_score, price_1, price_2, price_3,
                    volatility, volume_ratio, momentum_1, momentum_2
                ]
            }
            
            metadata_path = symbol_dir / "metadata.json"
            with open(metadata_path, w) as f:
                json.dump(metadata, f, indent=2)
            
            print(f"💾 {symbol}: Models saved to {symbol_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving models for {symbol}: {e}")
            return False
    
    def train_all_models(self):
        """Train models for all symbols"""
        print(f"🚀 Starting ML model training for all symbols")
        print(f"=" * 50)
        
        results = {}
        
        for symbol in self.symbols:
            print(f"\n🎯 Training models for {symbol}")
            print(f"-" * 30)
            
            # Extract data for this symbol
            df = self.extract_training_data(symbol)
            
            if len(df) < 5:
                print(f"⚠️ {symbol}: Insufficient training data ({len(df)} samples)")
                results[symbol] = {"status": "insufficient_data", "samples": len(df)}
                continue
            
            # Prepare features and targets
            X, y_direction, y_magnitude, confidence_accuracy = self.prepare_features_targets(df)
            
            if X is None:
                print(f"❌ {symbol}: Failed to prepare features")
                results[symbol] = {"status": "feature_error"}
                continue
            
            # Train models
            models, performance = self.train_models(symbol, X, y_direction, y_magnitude, confidence_accuracy)
            
            if models is None:
                print(f"❌ {symbol}: Model training failed")
                results[symbol] = {"status": "training_error"}
                continue
            
            # Save models
            if self.save_models(symbol, models, performance):
                results[symbol] = {
                    status: success,
                    samples: len(df),
                    performance: performance
                }
            else:
                results[symbol] = {"status": "save_error"}
        
        # Summary
        print(f"\n🎯 TRAINING SUMMARY")
        print(f"=" * 50)
        
        successful = 0
        for symbol, result in results.items():
            status = result[status]
            if status == success:
                successful += 1
                perf = result[performance]
                print(f"✅ {symbol}: {result[samples]} samples, acc: {perf[direction_accuracy]:.3f}")
            else:
                print(f"❌ {symbol}: {status}")
        
        print(f"\n📊 Successfully trained: {successful}/{len(self.symbols)} symbols")
        
        return results

def main():
    """Main training function"""
    print("🧠 ML TRAINING PIPELINE")
    print("=" * 50)
    
    pipeline = MLTrainingPipeline()
    results = pipeline.train_all_models()
    
    return results

if __name__ == "__main__":
    main()
