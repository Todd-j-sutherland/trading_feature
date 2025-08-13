#!/usr/bin/env python3
"""
Model Trainer for Corrected Pipeline
Trains models properly using historical data with temporal splits
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle
import os
from typing import Dict, List, Tuple
import logging
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, classification_report, mean_absolute_error
import warnings
warnings.filterwarnings('ignore')

class ModelTrainer:
    """Trains prediction models using proper temporal methodology"""
    
    def __init__(self, old_db_path: str = "data/trading_unified.db", 
                 new_db_path: str = "data/trading_predictions.db",
                 model_path: str = "models/"):
        self.old_db_path = old_db_path
        self.new_db_path = new_db_path
        self.model_path = model_path
        self.logger = logging.getLogger(__name__)
        
        # Create model directory
        os.makedirs(model_path, exist_ok=True)
    
    def convert_historical_data(self) -> bool:
        """Convert old retrospective labels to proper training data"""
        
        try:
            print("🔄 Converting historical retrospective labels to training data...")
            
            # Load old data
            old_conn = sqlite3.connect(self.old_db_path)
            
            # Get features and outcomes with proper joining
            query = """
            SELECT 
                f.symbol,
                f.timestamp as feature_timestamp,
                f.sentiment_score,
                f.confidence,
                f.news_count,
                f.reddit_sentiment,
                f.rsi,
                f.macd_line,
                f.macd_signal,
                f.macd_histogram,
                f.price_vs_sma20,
                f.price_vs_sma50,
                f.price_vs_sma200,
                f.bollinger_width,
                f.volume_ratio,
                f.atr_14,
                f.volatility_20d,
                f.asx200_change,
                f.vix_level,
                f.asx_market_hours,
                f.monday_effect,
                f.friday_effect,
                o.optimal_action,
                o.return_pct,
                o.price_direction_1d,
                o.confidence_score,
                o.prediction_timestamp
            FROM enhanced_features f
            JOIN enhanced_outcomes o ON f.id = o.feature_id
            WHERE o.return_pct IS NOT NULL
            ORDER BY f.timestamp ASC
            """
            
            df = pd.read_sql_query(query, old_conn)
            old_conn.close()
            
            if len(df) == 0:
                print("❌ No historical data found")
                return False
            
            print(f"📊 Found {len(df)} historical data points")
            
            # Clean and prepare data
            df = self._clean_training_data(df)
            
            # Save as training dataset
            training_file = os.path.join(self.model_path, "historical_training_data.csv")
            df.to_csv(training_file, index=False)
            
            print(f"✅ Converted data saved to: {training_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to convert historical data: {e}")
            return False
    
    def _clean_training_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare training data"""
        
        print("🧹 Cleaning training data...")
        
        # Remove rows with missing critical features
        initial_count = len(df)
        df = df.dropna(subset=['rsi', 'macd_histogram', 'return_pct'])
        
        # Fill remaining missing values
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)
        
        # Convert boolean columns
        bool_columns = ['asx_market_hours', 'monday_effect', 'friday_effect']
        for col in bool_columns:
            if col in df.columns:
                df[col] = df[col].astype(int)
        
        # Create proper target variables
        df['actual_direction'] = np.where(df['return_pct'] > 0, 1, 
                                 np.where(df['return_pct'] < 0, -1, 0))
        
        # Determine optimal action based on retrospective analysis
        # (This is only for training, never for live predictions!)
        df['optimal_action_target'] = df.apply(self._determine_optimal_action_label, axis=1)
        
        print(f"📉 Data cleaned: {initial_count} → {len(df)} rows")
        
        return df
    
    def _determine_optimal_action_label(self, row) -> str:
        """Determine what the optimal action should have been (for training only)"""
        
        return_pct = row['return_pct']
        confidence = row.get('confidence_score', 0.5)
        
        # Conservative labeling for training
        if return_pct > 1.5 and confidence > 0.6:
            return 'BUY'
        elif return_pct < -1.5 and confidence > 0.6:
            return 'SELL'
        elif return_pct > 0.8:
            return 'BUY'
        elif return_pct < -0.8:
            return 'SELL'
        else:
            return 'HOLD'
    
    def train_models(self, test_days: int = 7) -> Dict:
        """Train models with proper temporal validation"""
        
        print("🎯 Training prediction models with temporal validation...")
        
        # Load training data
        training_file = os.path.join(self.model_path, "historical_training_data.csv")
        if not os.path.exists(training_file):
            print("❌ No training data found. Run convert_historical_data() first.")
            return {}
        
        df = pd.read_csv(training_file)
        
        # Temporal split (CRITICAL - never train on recent data!)
        df['feature_timestamp'] = pd.to_datetime(df['feature_timestamp'])
        cutoff_date = df['feature_timestamp'].max() - timedelta(days=test_days)
        
        train_df = df[df['feature_timestamp'] <= cutoff_date]
        test_df = df[df['feature_timestamp'] > cutoff_date]
        
        print(f"📊 Training set: {len(train_df)} samples (up to {cutoff_date.date()})")
        print(f"📊 Test set: {len(test_df)} samples (after {cutoff_date.date()})")
        
        if len(train_df) < 50:
            print("❌ Insufficient training data")
            return {}
        
        # Prepare features
        feature_columns = [
            'sentiment_score', 'confidence', 'news_count', 'reddit_sentiment',
            'rsi', 'macd_line', 'macd_signal', 'macd_histogram',
            'price_vs_sma20', 'price_vs_sma50', 'price_vs_sma200',
            'bollinger_width', 'volume_ratio', 'atr_14', 'volatility_20d',
            'asx200_change', 'vix_level', 'asx_market_hours',
            'monday_effect', 'friday_effect'
        ]
        
        # Ensure all feature columns exist
        for col in feature_columns:
            if col not in df.columns:
                df[col] = 0
        
        X_train = train_df[feature_columns].fillna(0)
        X_test = test_df[feature_columns].fillna(0)
        
        # Train action classification model
        print("🎯 Training action classification model...")
        y_action_train = train_df['optimal_action_target']
        action_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            min_samples_split=10,
            random_state=42,
            class_weight='balanced'
        )
        action_model.fit(X_train, y_action_train)
        
        # Train direction prediction model
        print("🎯 Training direction prediction model...")
        y_direction_train = train_df['actual_direction']
        direction_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            random_state=42
        )
        direction_model.fit(X_train, y_direction_train)
        
        # Train magnitude prediction model
        print("🎯 Training magnitude prediction model...")
        y_magnitude_train = train_df['return_pct']
        magnitude_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=8,
            random_state=42
        )
        magnitude_model.fit(X_train, y_magnitude_train)
        
        # Evaluate models
        results = {}
        
        if len(test_df) > 0:
            print("📊 Evaluating models on test set...")
            
            # Action model evaluation
            y_action_test = test_df['optimal_action_target']
            action_pred = action_model.predict(X_test)
            action_accuracy = accuracy_score(y_action_test, action_pred)
            
            # Direction model evaluation
            y_direction_test = test_df['actual_direction']
            direction_pred = direction_model.predict(X_test)
            direction_accuracy = accuracy_score(y_direction_test, direction_pred)
            
            # Magnitude model evaluation
            y_magnitude_test = test_df['return_pct']
            magnitude_pred = magnitude_model.predict(X_test)
            magnitude_mae = mean_absolute_error(y_magnitude_test, magnitude_pred)
            
            results = {
                'action_accuracy': action_accuracy,
                'direction_accuracy': direction_accuracy,
                'magnitude_mae': magnitude_mae,
                'test_samples': len(test_df),
                'train_samples': len(train_df)
            }
            
            print(f"✅ Action Accuracy: {action_accuracy:.3f}")
            print(f"✅ Direction Accuracy: {direction_accuracy:.3f}")
            print(f"✅ Magnitude MAE: {magnitude_mae:.3f}%")
        
        # Save models
        print("💾 Saving trained models...")
        
        with open(os.path.join(self.model_path, 'action_model.pkl'), 'wb') as f:
            pickle.dump(action_model, f)
        
        with open(os.path.join(self.model_path, 'direction_model.pkl'), 'wb') as f:
            pickle.dump(direction_model, f)
        
        with open(os.path.join(self.model_path, 'magnitude_model.pkl'), 'wb') as f:
            pickle.dump(magnitude_model, f)
        
        # Save feature importance
        self._save_feature_importance(action_model, feature_columns, 'action')
        
        print("✅ Models trained and saved successfully!")
        
        return results
    
    def _save_feature_importance(self, model, feature_columns: List[str], model_type: str):
        """Save feature importance analysis"""
        
        if hasattr(model, 'feature_importances_'):
            importance_df = pd.DataFrame({
                'feature': feature_columns,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            importance_file = os.path.join(self.model_path, f'{model_type}_feature_importance.csv')
            importance_df.to_csv(importance_file, index=False)
            
            print(f"📊 Top 5 features for {model_type} model:")
            for _, row in importance_df.head().iterrows():
                print(f"   {row['feature']}: {row['importance']:.3f}")
    
    def validate_model_performance(self, days_back: int = 14) -> Dict:
        """Validate model performance on recent data"""
        
        print(f"🔍 Validating model performance on last {days_back} days...")
        
        # Load recent prediction data
        try:
            conn = sqlite3.connect(self.new_db_path)
            
            query = """
            SELECT 
                p.predicted_action,
                p.action_confidence,
                p.predicted_direction,
                p.predicted_magnitude,
                o.actual_return,
                o.actual_direction
            FROM predictions p
            JOIN outcomes o ON p.prediction_id = o.prediction_id
            WHERE datetime(p.prediction_timestamp) >= datetime('now', '-{} days')
            """.format(days_back)
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            if len(df) == 0:
                print("❌ No recent prediction data for validation")
                return {}
            
            # Calculate performance metrics
            direction_accuracy = accuracy_score(df['actual_direction'], df['predicted_direction'])
            magnitude_mae = mean_absolute_error(df['actual_return'], df['predicted_magnitude'])
            
            # Trading performance simulation
            trading_results = self._simulate_trading_performance(df)
            
            results = {
                'validation_samples': len(df),
                'direction_accuracy': direction_accuracy,
                'magnitude_mae': magnitude_mae,
                **trading_results
            }
            
            print(f"✅ Direction Accuracy: {direction_accuracy:.3f}")
            print(f"✅ Magnitude MAE: {magnitude_mae:.3f}%")
            print(f"✅ Simulated Return: {trading_results.get('total_return', 0):.2f}%")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return {}
    
    def _simulate_trading_performance(self, df: pd.DataFrame) -> Dict:
        """Simulate trading performance based on predictions"""
        
        total_return = 0
        winning_trades = 0
        losing_trades = 0
        
        for _, row in df.iterrows():
            if row['predicted_action'] == 'BUY':
                trade_return = row['actual_return']
                total_return += trade_return
                if trade_return > 0:
                    winning_trades += 1
                else:
                    losing_trades += 1
            elif row['predicted_action'] == 'SELL':
                trade_return = -row['actual_return']  # Short position
                total_return += trade_return
                if trade_return > 0:
                    winning_trades += 1
                else:
                    losing_trades += 1
        
        total_trades = winning_trades + losing_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        return {
            'total_return': total_return,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate
        }

def main():
    """Main training pipeline"""
    
    logging.basicConfig(level=logging.INFO)
    
    trainer = ModelTrainer()
    
    print("🚀 Starting Model Training Pipeline")
    print("="*50)
    
    # Step 1: Convert historical data
    if trainer.convert_historical_data():
        
        # Step 2: Train models
        results = trainer.train_models()
        
        if results:
            print("\n📊 Training Results:")
            for key, value in results.items():
                print(f"   {key}: {value}")
        
        # Step 3: Validate if we have recent data
        validation_results = trainer.validate_model_performance()
        
        if validation_results:
            print("\n🔍 Validation Results:")
            for key, value in validation_results.items():
                print(f"   {key}: {value}")
    
    print("\n✅ Training pipeline complete!")

if __name__ == "__main__":
    main()
