#!/usr/bin/env python3
"""
Actual ML Training Implementation
Replaces the placeholder enhanced_evening_analyzer_with_ml.py
"""

import os
import sys
import logging
from datetime import datetime, timedelta
import traceback

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/evening_ml_training.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """
    Actual ML training implementation using the enhanced training pipeline
    """
    logger.info("🌅 Starting Enhanced Evening ML Training")
    logger.info("📊 Implementing actual ML model training...")
    
    try:
        # Import the enhanced training pipeline
        from app.core.ml.enhanced_training_pipeline import EnhancedMLTrainingPipeline
        
        # Initialize the training pipeline
        logger.info("🔧 Initializing ML training pipeline...")
        pipeline = EnhancedMLTrainingPipeline()
        
        # Check if we have sufficient training data
        logger.info("📈 Checking training data availability...")
        if not pipeline.has_sufficient_training_data(min_samples=50):
            logger.warning("⚠️  Insufficient training data - need at least 50 samples")
            logger.info("💡 Consider running for a few more days to collect training data")
            return
        
        # Prepare the training dataset
        logger.info("🎯 Preparing enhanced training dataset...")
        X, y = pipeline.prepare_enhanced_training_dataset(min_samples=50)
        
        if X is None or len(X) == 0:
            logger.warning("❌ No training data available")
            return
        
        logger.info(f"📊 Training dataset prepared: {len(X)} samples with {len(X.columns)} features")
        
        # Train the enhanced models
        logger.info("🚀 Training enhanced ML models...")
        models = pipeline.train_enhanced_models(X, y)
        
        if models:
            logger.info("✅ ML model training completed successfully!")
            logger.info(f"🎯 Trained models: {list(models.keys())}")
            
            # Log model performance metrics
            for model_name, model_info in models.items():
                if 'performance' in model_info:
                    perf = model_info['performance']
                    logger.info(f"📊 {model_name} performance:")
                    for metric, value in perf.items():
                        logger.info(f"   {metric}: {value:.3f}")
        else:
            logger.error("❌ ML model training failed")
            
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("💡 Make sure app/core/ml/enhanced_training_pipeline.py is available")
        logger.info("🔄 Falling back to simple training approach...")
        
        # Fallback: Simple training using existing data
        try:
            fallback_training()
        except Exception as fallback_error:
            logger.error(f"❌ Fallback training also failed: {fallback_error}")
            
    except Exception as e:
        logger.error(f"❌ Training failed with error: {e}")
        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        
    logger.info("🎯 Evening ML training completed")

def fallback_training():
    """
    Fallback training method using scikit-learn directly on existing data
    """
    logger.info("🔄 Running fallback ML training...")
    
    import sqlite3
    import pandas as pd
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, mean_absolute_error
    import joblib
    
    # Connect to database
    db_path = "data/trading_predictions.db"
    conn = sqlite3.connect(db_path)
    
    try:
        # Get predictions with outcomes for training
        query = """
        SELECT 
            p.symbol,
            p.predicted_action,
            p.action_confidence,
            p.predicted_direction,
            p.predicted_magnitude,
            p.feature_vector,
            o.actual_return,
            o.actual_direction,
            p.prediction_timestamp
        FROM predictions p
        JOIN outcomes o ON p.prediction_id = o.prediction_id
        WHERE p.feature_vector IS NOT NULL
        AND o.actual_return IS NOT NULL
        ORDER BY p.prediction_timestamp DESC
        LIMIT 500
        """
        
        df = pd.read_sql_query(query, conn)
        logger.info(f"📊 Loaded {len(df)} training samples from database")
        
        if len(df) < 20:
            logger.warning("⚠️  Too few samples for training")
            return
        
        # Parse feature vectors
        features = []
        for feature_str in df['feature_vector']:
            try:
                # Assuming comma-separated features
                feature_values = [float(x) for x in feature_str.split(',')]
                features.append(feature_values)
            except:
                # Use default features if parsing fails
                features.append([50.0] * 10)  # Default technical features
        
        X = np.array(features)
        
        # Prepare targets
        y_direction = df['actual_direction'].values
        y_magnitude = np.abs(df['actual_return'].values)
        
        # Split data
        X_train, X_test, y_dir_train, y_dir_test, y_mag_train, y_mag_test = train_test_split(
            X, y_direction, y_magnitude, test_size=0.2, random_state=42
        )
        
        # Train direction model
        logger.info("🎯 Training direction prediction model...")
        direction_model = RandomForestClassifier(n_estimators=100, random_state=42)
        direction_model.fit(X_train, y_dir_train)
        
        dir_accuracy = accuracy_score(y_dir_test, direction_model.predict(X_test))
        logger.info(f"📊 Direction model accuracy: {dir_accuracy:.3f}")
        
        # Train magnitude model
        logger.info("🎯 Training magnitude prediction model...")
        magnitude_model = RandomForestRegressor(n_estimators=100, random_state=42)
        magnitude_model.fit(X_train, y_mag_train)
        
        mag_mae = mean_absolute_error(y_mag_test, magnitude_model.predict(X_test))
        logger.info(f"📊 Magnitude model MAE: {mag_mae:.3f}")
        
        # Save models
        models_dir = "models"
        os.makedirs(models_dir, exist_ok=True)
        
        direction_path = os.path.join(models_dir, "current_direction_model.pkl")
        magnitude_path = os.path.join(models_dir, "current_magnitude_model.pkl")
        
        joblib.dump(direction_model, direction_path)
        joblib.dump(magnitude_model, magnitude_path)
        
        logger.info(f"✅ Models saved:")
        logger.info(f"   Direction: {direction_path}")
        logger.info(f"   Magnitude: {magnitude_path}")
        logger.info(f"📈 Training completed with {len(df)} samples")
        
    except Exception as e:
        logger.error(f"❌ Fallback training failed: {e}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
