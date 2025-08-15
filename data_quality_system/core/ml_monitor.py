#!/usr/bin/env python3
"""
ML-Powered Continuous Data Quality Monitor
Uses machine learning to learn normal data patterns and detect anomalies in real-time
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import joblib
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.model_selection import train_test_split
from scipy import stats
import warnings
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

warnings.filterwarnings('ignore')

class MLDataQualityMonitor:
    def __init__(self, db_path=None):
        if db_path is None:
            # Try to find the database automatically
            possible_paths = [
                "../data/trading_predictions.db",
                "../../data/trading_predictions.db",
                "/root/test/data/trading_predictions.db", 
                "data/trading_predictions.db"
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    db_path = path
                    break
            else:
                db_path = "../data/trading_predictions.db"  # Default fallback
        self.db_path = db_path
        self.models = {}
        self.scalers = {}
        self.baseline_stats = {}
        self.model_path = "../data/quality_models"
        
    def load_training_data(self, days_back=90):
        """Load historical data for training quality models"""
        conn = sqlite3.connect(self.db_path)
        
        # Load comprehensive training data
        query = """
        SELECT 
            entry_price,
            exit_price_1d,
            return_pct,
            confidence_score,
            optimal_action,
            LENGTH(symbol) as symbol_length,
            CASE 
                WHEN optimal_action = 'BUY' THEN 1
                WHEN optimal_action = 'SELL' THEN -1
                ELSE 0
            END as action_numeric,
            julianday('now') - julianday(created_at) as days_old,
            CASE WHEN return_pct IS NULL THEN 1 ELSE 0 END as missing_return,
            CASE WHEN exit_price_1d IS NULL THEN 1 ELSE 0 END as missing_exit,
            ABS(entry_price - ROUND(entry_price)) as price_decimal_part
        FROM enhanced_outcomes 
        WHERE created_at >= date('now', '-{} days')
        AND entry_price IS NOT NULL
        """.format(days_back)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Calculate additional features
        df['price_ratio'] = df['exit_price_1d'] / df['entry_price'].replace(0, np.nan)
        df['return_zscore'] = np.abs(stats.zscore(df['return_pct'].dropna()))
        df['confidence_zscore'] = np.abs(stats.zscore(df['confidence_score'].dropna()))
        
        # Flag potential anomalies for training
        df['is_round_price'] = (df['price_decimal_part'] == 0) & (df['entry_price'].isin([1, 5, 10, 50, 100]))
        df['extreme_return'] = (np.abs(df['return_pct']) > 50) | (df['return_pct'] < -90)
        df['suspicious_confidence'] = (df['confidence_score'] == 0) | (df['confidence_score'] == 1)
        
        return df
    
    def train_anomaly_detection_models(self):
        """Train ML models to detect various types of data quality issues"""
        print("🧠 Training ML Data Quality Models...")
        
        df = self.load_training_data()
        
        if len(df) < 50:
            print("❌ Insufficient data for model training")
            return False
        
        # 1. Price Anomaly Detection Model
        price_features = ['entry_price', 'exit_price_1d', 'price_ratio', 'price_decimal_part']
        price_data = df[price_features].dropna()
        
        if len(price_data) > 20:
            # Scale features
            self.scalers['price'] = StandardScaler()
            price_scaled = self.scalers['price'].fit_transform(price_data)
            
            # Train isolation forest for price anomalies
            self.models['price_anomaly'] = IsolationForest(
                contamination=0.1, 
                random_state=42,
                n_estimators=100
            )
            self.models['price_anomaly'].fit(price_scaled)
        
        # 2. Return Pattern Model
        return_features = ['return_pct', 'return_zscore', 'action_numeric', 'days_old']
        return_data = df[return_features].dropna()
        
        if len(return_data) > 20:
            self.scalers['return'] = StandardScaler()
            return_scaled = self.scalers['return'].fit_transform(return_data)
            
            self.models['return_anomaly'] = IsolationForest(
                contamination=0.1,
                random_state=42
            )
            self.models['return_anomaly'].fit(return_scaled)
        
        # 3. Confidence Pattern Model
        conf_features = ['confidence_score', 'confidence_zscore', 'action_numeric']
        conf_data = df[conf_features].dropna()
        
        if len(conf_data) > 20:
            self.scalers['confidence'] = StandardScaler()
            conf_scaled = self.scalers['confidence'].fit_transform(conf_data)
            
            self.models['confidence_anomaly'] = IsolationForest(
                contamination=0.05,
                random_state=42
            )
            self.models['confidence_anomaly'].fit(conf_scaled)
        
        # 4. Data Completeness Model (clustering)
        completeness_features = ['missing_return', 'missing_exit', 'days_old', 'symbol_length']
        completeness_data = df[completeness_features].fillna(0)
        
        if len(completeness_data) > 10:
            self.models['completeness_cluster'] = DBSCAN(eps=0.5, min_samples=2)
            self.models['completeness_cluster'].fit(completeness_data)
        
        # Store baseline statistics
        self.baseline_stats = {
            'entry_price_mean': df['entry_price'].mean(),
            'entry_price_std': df['entry_price'].std(),
            'return_pct_mean': df['return_pct'].mean(),
            'return_pct_std': df['return_pct'].std(),
            'confidence_mean': df['confidence_score'].mean(),
            'confidence_std': df['confidence_score'].std(),
            'round_price_rate': df['is_round_price'].mean(),
            'extreme_return_rate': df['extreme_return'].mean(),
            'training_date': datetime.now().isoformat(),
            'training_samples': len(df)
        }
        
        # Save models
        self.save_models()
        
        print(f"✅ Trained {len(self.models)} ML models on {len(df)} samples")
        return True
    
    def save_models(self):
        """Save trained models and scalers"""
        os.makedirs(self.model_path, exist_ok=True)
        
        # Save models
        for name, model in self.models.items():
            joblib.dump(model, f"{self.model_path}/{name}_model.pkl")
        
        # Save scalers
        for name, scaler in self.scalers.items():
            joblib.dump(scaler, f"{self.model_path}/{name}_scaler.pkl")
        
        # Save baseline stats
        with open(f"{self.model_path}/baseline_stats.json", 'w') as f:
            json.dump(self.baseline_stats, f, indent=2)
    
    def load_models(self):
        """Load pre-trained models"""
        if not os.path.exists(self.model_path):
            return False
        
        try:
            # Load models
            for model_file in os.listdir(self.model_path):
                if model_file.endswith('_model.pkl'):
                    name = model_file.replace('_model.pkl', '')
                    self.models[name] = joblib.load(f"{self.model_path}/{model_file}")
            
            # Load scalers
            for scaler_file in os.listdir(self.model_path):
                if scaler_file.endswith('_scaler.pkl'):
                    name = scaler_file.replace('_scaler.pkl', '')
                    self.scalers[name] = joblib.load(f"{self.model_path}/{scaler_file}")
            
            # Load baseline stats
            if os.path.exists(f"{self.model_path}/baseline_stats.json"):
                with open(f"{self.model_path}/baseline_stats.json", 'r') as f:
                    self.baseline_stats = json.load(f)
            
            return True
        except Exception as e:
            print(f"Error loading models: {e}")
            return False
    
    def detect_real_time_anomalies(self, new_data):
        """Detect anomalies in new data using trained ML models"""
        anomalies = []
        
        if not self.models:
            print("⚠️ No models loaded. Run training first.")
            return anomalies
        
        # Prepare features for new data
        features = self.prepare_features(new_data)
        
        # Price anomaly detection
        if 'price_anomaly' in self.models and 'price' in self.scalers:
            price_features = ['entry_price', 'exit_price_1d', 'price_ratio', 'price_decimal_part']
            price_data = features[price_features].dropna()
            
            if not price_data.empty:
                price_scaled = self.scalers['price'].transform(price_data)
                price_predictions = self.models['price_anomaly'].predict(price_scaled)
                
                anomalous_indices = price_data.index[price_predictions == -1]
                if len(anomalous_indices) > 0:
                    anomalies.append({
                        'type': 'ml_price_anomaly',
                        'severity': 'medium',
                        'affected_records': anomalous_indices.tolist(),
                        'model_confidence': self.models['price_anomaly'].score_samples(price_scaled).min(),
                        'description': f'ML model detected {len(anomalous_indices)} price anomalies'
                    })
        
        # Return anomaly detection
        if 'return_anomaly' in self.models and 'return' in self.scalers:
            return_features = ['return_pct', 'return_zscore', 'action_numeric', 'days_old']
            return_data = features[return_features].dropna()
            
            if not return_data.empty:
                return_scaled = self.scalers['return'].transform(return_data)
                return_predictions = self.models['return_anomaly'].predict(return_scaled)
                
                anomalous_indices = return_data.index[return_predictions == -1]
                if len(anomalous_indices) > 0:
                    anomalies.append({
                        'type': 'ml_return_anomaly',
                        'severity': 'high',
                        'affected_records': anomalous_indices.tolist(),
                        'description': f'ML model detected {len(anomalous_indices)} return anomalies'
                    })
        
        # Statistical drift detection
        drift_alerts = self.detect_statistical_drift(features)
        anomalies.extend(drift_alerts)
        
        return anomalies
    
    def prepare_features(self, df):
        """Prepare features for ML analysis"""
        # Add same features as training data
        df['symbol_length'] = df['symbol'].str.len()
        df['action_numeric'] = df['optimal_action'].map({'BUY': 1, 'SELL': -1, 'HOLD': 0})
        df['days_old'] = (datetime.now() - pd.to_datetime(df['created_at'])).dt.days
        df['missing_return'] = df['return_pct'].isna().astype(int)
        df['missing_exit'] = df['exit_price_1d'].isna().astype(int)
        df['price_decimal_part'] = np.abs(df['entry_price'] - np.round(df['entry_price']))
        df['price_ratio'] = df['exit_price_1d'] / df['entry_price'].replace(0, np.nan)
        
        # Z-scores (use baseline stats)
        if self.baseline_stats:
            df['return_zscore'] = np.abs(
                (df['return_pct'] - self.baseline_stats['return_pct_mean']) / 
                self.baseline_stats['return_pct_std']
            )
            df['confidence_zscore'] = np.abs(
                (df['confidence_score'] - self.baseline_stats['confidence_mean']) / 
                self.baseline_stats['confidence_std']
            )
        
        return df
    
    def detect_statistical_drift(self, current_data):
        """Detect if current data distribution has drifted from baseline"""
        alerts = []
        
        if not self.baseline_stats:
            return alerts
        
        # Check for significant drift in key metrics
        current_stats = {
            'entry_price_mean': current_data['entry_price'].mean(),
            'return_pct_mean': current_data['return_pct'].mean(),
            'confidence_mean': current_data['confidence_score'].mean(),
            'round_price_rate': (current_data['price_decimal_part'] == 0).mean()
        }
        
        # Define drift thresholds (2 standard deviations)
        drift_threshold = 2.0
        
        for metric, current_value in current_stats.items():
            if metric in self.baseline_stats and not pd.isna(current_value):
                baseline_value = self.baseline_stats[metric]
                baseline_std = self.baseline_stats.get(f"{metric.replace('_mean', '_std')}", 0)
                
                if baseline_std > 0:
                    drift_score = abs(current_value - baseline_value) / baseline_std
                    
                    if drift_score > drift_threshold:
                        alerts.append({
                            'type': 'statistical_drift',
                            'severity': 'medium' if drift_score < 3 else 'high',
                            'metric': metric,
                            'drift_score': drift_score,
                            'baseline_value': baseline_value,
                            'current_value': current_value,
                            'description': f'{metric} drifted significantly from baseline'
                        })
        
        return alerts
    
    def run_continuous_monitoring(self, days_back=7):
        """Run continuous monitoring on recent data"""
        print("📊 Running ML-Powered Continuous Data Quality Monitoring...")
        
        # Load models or train if needed
        if not self.load_models():
            print("🔄 No existing models found. Training new models...")
            if not self.train_anomaly_detection_models():
                return None
        
        # Get recent data for analysis
        conn = sqlite3.connect(self.db_path)
        recent_data = pd.read_sql_query(f"""
            SELECT * FROM enhanced_outcomes 
            WHERE created_at >= date('now', '-{days_back} days')
            ORDER BY created_at DESC
        """, conn)
        conn.close()
        
        if recent_data.empty:
            print("📭 No recent data to analyze")
            return None
        
        # Detect anomalies
        anomalies = self.detect_real_time_anomalies(recent_data)
        
        # Generate monitoring report
        report = {
            'timestamp': datetime.now().isoformat(),
            'monitoring_period_days': days_back,
            'records_analyzed': len(recent_data),
            'models_used': list(self.models.keys()),
            'baseline_date': self.baseline_stats.get('training_date'),
            'anomalies_detected': anomalies,
            'summary': {
                'total_anomalies': len(anomalies),
                'critical_alerts': len([a for a in anomalies if a['severity'] == 'high']),
                'data_quality_score': max(0, 100 - len(anomalies) * 10)
            }
        }
        
        # Save monitoring report
        monitor_dir = "../data/ml_monitoring"
        os.makedirs(monitor_dir, exist_ok=True)
        report_file = f"{monitor_dir}/ml_quality_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n🤖 ML Monitoring Results:")
        print(f"   Records Analyzed: {len(recent_data)}")
        print(f"   Anomalies Detected: {len(anomalies)}")
        print(f"   Quality Score: {report['summary']['data_quality_score']}/100")
        print(f"   Report Saved: {report_file}")
        
        return report

def main():
    monitor = MLDataQualityMonitor()
    
    import argparse
    parser = argparse.ArgumentParser(description='ML Data Quality Monitor')
    parser.add_argument('--train', action='store_true', help='Train new models')
    parser.add_argument('--days', type=int, default=7, help='Days of data to analyze')
    
    args = parser.parse_args()
    
    if args.train:
        monitor.train_anomaly_detection_models()
    
    report = monitor.run_continuous_monitoring(days_back=args.days)
    return report

if __name__ == "__main__":
    main()
