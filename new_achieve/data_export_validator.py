#!/usr/bin/env python3
"""
Data Export and Validation Tool
Exports all database tables and validates values against expectations
"""

import sqlite3
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import numpy as np

class DatabaseExporter:
    """Export and validate database contents"""
    
    def __init__(self, local_db_path="data/trading_predictions.db", remote_host="root@170.64.199.151"):
        self.local_db_path = local_db_path
        self.remote_host = remote_host
        self.remote_db_path = "/root/test/data/trading_predictions.db"
        self.export_dir = "data_exports"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create export directory
        os.makedirs(self.export_dir, exist_ok=True)
        
    def export_remote_database(self):
        """Export all tables from remote database"""
        print("🌐 Exporting Remote Database Tables")
        print("=" * 50)
        
        # Get table list from remote
        print("📋 Getting table list from remote database...")
        import subprocess
        
        # Get table names
        cmd = f'ssh {self.remote_host} "cd /root/test && sqlite3 {self.remote_db_path} \".tables\""'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Failed to get table list: {result.stderr}")
            return {}
        
        tables = result.stdout.strip().split()
        print(f"✅ Found {len(tables)} tables: {', '.join(tables)}")
        
        exported_data = {}
        
        for table in tables:
            print(f"\n📊 Exporting table: {table}")
            
            # Export table data
            cmd = f'ssh {self.remote_host} "cd /root/test && sqlite3 -header -csv {self.remote_db_path} \\"SELECT * FROM {table};\\"" > {self.export_dir}/remote_{table}_{self.timestamp}.csv'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Load the exported CSV
                try:
                    df = pd.read_csv(f"{self.export_dir}/remote_{table}_{self.timestamp}.csv")
                    exported_data[table] = df
                    print(f"   ✅ Exported {len(df)} rows")
                    
                    # Save summary
                    self._save_table_summary(table, df, "remote")
                    
                except Exception as e:
                    print(f"   ❌ Failed to read exported data: {e}")
            else:
                print(f"   ❌ Export failed: {result.stderr}")
        
        return exported_data
    
    def export_local_database(self):
        """Export all tables from local database if it exists"""
        print("\n💻 Exporting Local Database Tables")
        print("=" * 50)
        
        if not os.path.exists(self.local_db_path):
            print(f"⚠️ Local database not found at {self.local_db_path}")
            return {}
        
        try:
            conn = sqlite3.connect(self.local_db_path)
            
            # Get table names
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"✅ Found {len(tables)} tables: {', '.join(tables)}")
            
            exported_data = {}
            
            for table in tables:
                print(f"\n📊 Exporting table: {table}")
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                    exported_data[table] = df
                    
                    # Save to CSV
                    csv_path = f"{self.export_dir}/local_{table}_{self.timestamp}.csv"
                    df.to_csv(csv_path, index=False)
                    
                    print(f"   ✅ Exported {len(df)} rows to {csv_path}")
                    
                    # Save summary
                    self._save_table_summary(table, df, "local")
                    
                except Exception as e:
                    print(f"   ❌ Failed to export {table}: {e}")
            
            conn.close()
            return exported_data
            
        except Exception as e:
            print(f"❌ Failed to connect to local database: {e}")
            return {}
    
    def _save_table_summary(self, table_name, df, source):
        """Save a summary of table contents"""
        summary = {
            'source': source,
            'table_name': table_name,
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'export_timestamp': self.timestamp
        }
        
        # Add sample data and statistics
        if not df.empty:
            summary['sample_rows'] = df.head(3).to_dict('records')
            summary['null_counts'] = df.isnull().sum().to_dict()
            
            # Numeric column statistics
            numeric_columns = df.select_dtypes(include=[np.number]).columns
            if len(numeric_columns) > 0:
                summary['numeric_stats'] = df[numeric_columns].describe().to_dict()
        
        # Save summary
        summary_path = f"{self.export_dir}/{source}_{table_name}_summary_{self.timestamp}.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"   📋 Summary saved to {summary_path}")

def create_expectation_documentation():
    """Create comprehensive expectation documentation for all tables"""
    
    expectations = {
        "database_expectations": {
            "last_updated": datetime.now().isoformat(),
            "purpose": "Define expected value ranges and patterns for database validation",
            "validation_rules": {
                "general": {
                    "no_null_primary_keys": True,
                    "timestamps_recent": "Within last 30 days for active data",
                    "no_extreme_outliers": "Values should be within 3 standard deviations"
                }
            }
        },
        
        "table_expectations": {
            "predictions": {
                "description": "Core prediction data from TruePredictionEngine",
                "expected_columns": [
                    "prediction_id", "symbol", "prediction_timestamp", 
                    "predicted_action", "action_confidence", "predicted_direction",
                    "predicted_magnitude", "feature_vector"
                ],
                "value_expectations": {
                    "symbol": {
                        "type": "string",
                        "pattern": "^[A-Z]{3,4}\\.AX$",
                        "examples": ["ANZ.AX", "CBA.AX", "WBC.AX", "NAB.AX"],
                        "invalid_examples": ["", "ABC", "XYZ.US"]
                    },
                    "predicted_action": {
                        "type": "string",
                        "allowed_values": ["BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"],
                        "invalid_examples": ["", "NEUTRAL", "WAIT", "UNKNOWN"]
                    },
                    "action_confidence": {
                        "type": "float",
                        "range": [0.0, 1.0],
                        "typical_range": [0.3, 0.8],
                        "suspicious_values": ["exactly 0.5 repeatedly", "always > 0.9", "always < 0.1"]
                    },
                    "predicted_direction": {
                        "type": "integer",
                        "allowed_values": [-1, 1],
                        "meaning": "-1 = DOWN, 1 = UP",
                        "invalid_examples": [0, 2, -2]
                    },
                    "predicted_magnitude": {
                        "type": "float",
                        "range": [-10.0, 10.0],
                        "typical_range": [-2.0, 2.0],
                        "unit": "percentage",
                        "suspicious_values": ["always 0.0", "extreme values > 5%"]
                    },
                    "feature_vector": {
                        "type": "json_array",
                        "expected_length": 20,
                        "element_types": "float",
                        "suspicious_patterns": [
                            "All zeros",
                            "Repeated identical values",
                            "Missing array elements",
                            "Non-numeric values"
                        ],
                        "feature_order": [
                            "sentiment_score", "confidence", "news_count", 
                            "reddit_sentiment", "rsi", "macd_line", "macd_signal",
                            "macd_histogram", "price_vs_sma20", "price_vs_sma50",
                            "price_vs_sma200", "bollinger_width", "volume_ratio",
                            "atr_14", "volatility_20d", "current_price",
                            "asx200_change", "vix_level", "market_hours", "day_effects"
                        ]
                    }
                },
                "feature_vector_expectations": {
                    "sentiment_score": {
                        "index": 0,
                        "range": [-1.0, 1.0],
                        "typical_range": [-0.3, 0.3],
                        "meaning": "Overall sentiment score",
                        "red_flags": ["always 0.0", "always extreme values"]
                    },
                    "rsi": {
                        "index": 4,
                        "range": [0.0, 100.0],
                        "typical_range": [20.0, 80.0],
                        "meaning": "Relative Strength Index",
                        "red_flags": ["always 50.0", "always extreme values", "outside 0-100"]
                    },
                    "macd_line": {
                        "index": 5,
                        "range": [-10.0, 10.0],
                        "typical_range": [-2.0, 2.0],
                        "meaning": "MACD line value",
                        "red_flags": ["always 0.0", "unrealistic extreme values"]
                    },
                    "current_price": {
                        "index": 15,
                        "range": [1.0, 200.0],
                        "typical_range": [20.0, 120.0],
                        "meaning": "Current stock price in AUD",
                        "red_flags": ["always 0.0", "unrealistic prices < $5 or > $150"]
                    }
                }
            },
            
            "outcomes": {
                "description": "Actual outcomes for predictions after evaluation",
                "expected_columns": [
                    "outcome_id", "prediction_id", "evaluation_timestamp",
                    "entry_price", "exit_price", "actual_return", "holding_period"
                ],
                "value_expectations": {
                    "actual_return": {
                        "type": "float",
                        "range": [-20.0, 20.0],
                        "typical_range": [-5.0, 5.0],
                        "unit": "percentage",
                        "red_flags": ["always 0.0", "extreme values > 10%"]
                    },
                    "entry_price": {
                        "type": "float",
                        "range": [1.0, 200.0],
                        "red_flags": ["0.0 values", "unrealistic prices"]
                    },
                    "exit_price": {
                        "type": "float", 
                        "range": [1.0, 200.0],
                        "red_flags": ["0.0 values", "identical to entry_price always"]
                    }
                }
            }
        },
        
        "validation_checks": {
            "data_quality_checks": [
                {
                    "name": "No Static RSI Values",
                    "description": "RSI should not be consistently 50.0",
                    "query": "Check if RSI values in feature_vector[4] are always 50.0",
                    "red_flag": "More than 80% of predictions have RSI = 50.0"
                },
                {
                    "name": "No Static MACD Values", 
                    "description": "MACD should not be consistently 0.0",
                    "query": "Check if MACD values in feature_vector[5] are always 0.0",
                    "red_flag": "More than 80% of predictions have MACD = 0.0"
                },
                {
                    "name": "Realistic Confidence Distribution",
                    "description": "Confidence should vary and not cluster at defaults",
                    "red_flag": "Too many predictions with confidence exactly 0.5"
                },
                {
                    "name": "Price Consistency",
                    "description": "Current prices should be realistic for ASX stocks",
                    "red_flag": "Prices consistently 0.0 or unrealistic values"
                },
                {
                    "name": "Action Distribution Balance",
                    "description": "Should have variety in predicted actions",
                    "red_flag": "More than 90% of one action type"
                }
            ],
            
            "temporal_checks": [
                {
                    "name": "Recent Data",
                    "description": "Predictions should be recent",
                    "red_flag": "No predictions in last 24 hours"
                },
                {
                    "name": "Consistent Timestamps", 
                    "description": "Timestamps should be logical",
                    "red_flag": "Future timestamps or very old data"
                }
            ],
            
            "cross_reference_checks": [
                {
                    "name": "Prediction-Outcome Consistency",
                    "description": "Outcomes should reference valid predictions", 
                    "red_flag": "Orphaned outcomes or missing predictions"
                }
            ]
        }
    }
    
    # Save expectations document
    expectations_path = f"data_exports/database_expectations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(expectations_path, 'w') as f:
        json.dump(expectations, f, indent=2, default=str)
    
    print(f"📋 Expectations document created: {expectations_path}")
    return expectations_path

def validate_exported_data(data_dict, expectations_path):
    """Validate exported data against expectations"""
    print("\n🔍 Validating Exported Data Against Expectations")
    print("=" * 60)
    
    # Load expectations
    with open(expectations_path, 'r') as f:
        expectations = json.load(f)
    
    validation_results = {
        'validation_timestamp': datetime.now().isoformat(),
        'tables_validated': [],
        'issues_found': [],
        'summary': {}
    }
    
    for table_name, df in data_dict.items():
        print(f"\n📊 Validating table: {table_name}")
        table_issues = []
        
        if table_name in expectations['table_expectations']:
            table_exp = expectations['table_expectations'][table_name]
            
            # Check if it's the predictions table with feature vectors
            if table_name == 'predictions' and 'feature_vector' in df.columns:
                print("   🔍 Analyzing feature vectors for static values...")
                
                # Analyze feature vectors
                feature_issues = analyze_feature_vectors(df)
                table_issues.extend(feature_issues)
                
                # Check action distribution
                action_dist = df['predicted_action'].value_counts()
                print(f"   📈 Action distribution: {action_dist.to_dict()}")
                
                # Check for concerning patterns
                total_predictions = len(df)
                for action, count in action_dist.items():
                    percentage = (count / total_predictions) * 100
                    if percentage > 90:
                        table_issues.append({
                            'type': 'action_distribution',
                            'issue': f'{action} represents {percentage:.1f}% of predictions',
                            'severity': 'high'
                        })
                
                # Check confidence distribution
                confidence_stats = df['action_confidence'].describe()
                print(f"   📊 Confidence stats: mean={confidence_stats['mean']:.3f}, std={confidence_stats['std']:.3f}")
                
                if confidence_stats['std'] < 0.05:
                    table_issues.append({
                        'type': 'confidence_distribution',
                        'issue': f'Very low confidence variance (std={confidence_stats["std"]:.3f})',
                        'severity': 'medium'
                    })
        
        validation_results['tables_validated'].append(table_name)
        validation_results['issues_found'].extend(table_issues)
        
        print(f"   ✅ Found {len(table_issues)} issues in {table_name}")
    
    # Save validation results
    results_path = f"data_exports/validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_path, 'w') as f:
        json.dump(validation_results, f, indent=2, default=str)
    
    print(f"\n📋 Validation results saved: {results_path}")
    return validation_results

def analyze_feature_vectors(df):
    """Analyze feature vectors for static/suspicious values"""
    issues = []
    
    # Parse feature vectors
    feature_data = []
    for idx, row in df.iterrows():
        try:
            if pd.notna(row['feature_vector']) and row['feature_vector']:
                features = json.loads(row['feature_vector'])
                if isinstance(features, list) and len(features) >= 16:
                    feature_data.append({
                        'sentiment': features[0] if len(features) > 0 else 0,
                        'rsi': features[4] if len(features) > 4 else 50,
                        'macd': features[5] if len(features) > 5 else 0,
                        'current_price': features[15] if len(features) > 15 else 0
                    })
        except:
            continue
    
    if not feature_data:
        issues.append({
            'type': 'feature_vector_parsing',
            'issue': 'No valid feature vectors found',
            'severity': 'high'
        })
        return issues
    
    feature_df = pd.DataFrame(feature_data)
    
    # Check for static RSI values
    rsi_static_count = (feature_df['rsi'] == 50.0).sum()
    rsi_static_pct = (rsi_static_count / len(feature_df)) * 100
    print(f"   📊 RSI analysis: {rsi_static_count}/{len(feature_df)} ({rsi_static_pct:.1f}%) are exactly 50.0")
    
    if rsi_static_pct > 50:
        issues.append({
            'type': 'static_rsi',
            'issue': f'{rsi_static_pct:.1f}% of RSI values are static (50.0)',
            'severity': 'high' if rsi_static_pct > 80 else 'medium'
        })
    
    # Check for static MACD values
    macd_static_count = (feature_df['macd'] == 0.0).sum()
    macd_static_pct = (macd_static_count / len(feature_df)) * 100
    print(f"   📊 MACD analysis: {macd_static_count}/{len(feature_df)} ({macd_static_pct:.1f}%) are exactly 0.0")
    
    if macd_static_pct > 50:
        issues.append({
            'type': 'static_macd',
            'issue': f'{macd_static_pct:.1f}% of MACD values are static (0.0)',
            'severity': 'high' if macd_static_pct > 80 else 'medium'
        })
    
    # Check for zero prices
    price_zero_count = (feature_df['current_price'] == 0.0).sum()
    price_zero_pct = (price_zero_count / len(feature_df)) * 100
    print(f"   📊 Price analysis: {price_zero_count}/{len(feature_df)} ({price_zero_pct:.1f}%) are 0.0")
    
    if price_zero_pct > 10:
        issues.append({
            'type': 'zero_prices',
            'issue': f'{price_zero_pct:.1f}% of prices are 0.0',
            'severity': 'medium'
        })
    
    # Print value ranges
    print(f"   📈 RSI range: {feature_df['rsi'].min():.1f} - {feature_df['rsi'].max():.1f}")
    print(f"   📈 MACD range: {feature_df['macd'].min():.3f} - {feature_df['macd'].max():.3f}")
    print(f"   📈 Price range: ${feature_df['current_price'].min():.2f} - ${feature_df['current_price'].max():.2f}")
    
    return issues

def main():
    """Main execution function"""
    print("🔍 Database Export and Validation Tool")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # Initialize exporter
    exporter = DatabaseExporter()
    
    # Create expectations document
    expectations_path = create_expectation_documentation()
    
    # Export remote database
    remote_data = exporter.export_remote_database()
    
    # Export local database if available
    local_data = exporter.export_local_database()
    
    # Validate data
    if remote_data:
        print("\n🔍 Validating Remote Data")
        remote_validation = validate_exported_data(remote_data, expectations_path)
    
    if local_data:
        print("\n🔍 Validating Local Data")  
        local_validation = validate_exported_data(local_data, expectations_path)
    
    print("\n🎉 Export and Validation Complete!")
    print(f"📁 All files saved in: {exporter.export_dir}/")
    print(f"📋 Expectations document: {expectations_path}")
    
    # Summary
    if remote_data:
        print(f"\n📊 Remote Database Summary:")
        for table, df in remote_data.items():
            print(f"   - {table}: {len(df)} rows")
    
    if local_data:
        print(f"\n📊 Local Database Summary:")
        for table, df in local_data.items():
            print(f"   - {table}: {len(df)} rows")

if __name__ == "__main__":
    main()
