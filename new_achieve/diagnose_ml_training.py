#!/usr/bin/env python3
"""
Diagnose ML training issues and force a training run
"""

import sqlite3
import json
import sys
import os
from datetime import datetime

def diagnose_training_issues():
    """Diagnose why ML training isn't happening"""
    
    print("🔍 ML Training Diagnostic Report")
    print("=" * 50)
    
    # Environment info
    import platform
    print(f"🖥️  Environment: {platform.system()} {platform.release()}")
    print(f"📍 Working directory: {os.getcwd()}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    
    # Check database
    db_path = './data/trading_unified.db'
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    # Database file info
    db_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
    print(f"💾 Database size: {db_size:.2f} MB")
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Check training samples
        cursor = conn.execute("SELECT COUNT(*) FROM enhanced_outcomes")
        sample_count = cursor.fetchone()[0]
        print(f"📊 Training samples available: {sample_count}")
        
        # Check latest training from ALL performance tables
        print("\n📊 Training Records from All Tables:")
        
        # Check model_performance_enhanced
        cursor = conn.execute("""
            SELECT training_date, training_samples, direction_accuracy_1h 
            FROM model_performance_enhanced 
            ORDER BY training_date DESC LIMIT 1
        """)
        enhanced_training = cursor.fetchone()
        
        if enhanced_training:
            print(f"🧠 Enhanced Model Performance:")
            print(f"   Last training: {enhanced_training[0]}")
            print(f"   Samples used: {enhanced_training[1]}")
            print(f"   Accuracy: {enhanced_training[2]:.3f}")
            
            # Calculate hours since last training
            last_time = datetime.fromisoformat(enhanced_training[0])
            now = datetime.now()
            hours_ago = (now - last_time).total_seconds() / 3600
            print(f"   Hours ago: {hours_ago:.1f}")
        else:
            print("❌ No enhanced training records found")
        
        # Check model_performance table (basic)
        try:
            cursor = conn.execute("""
                SELECT timestamp, accuracy, samples_used 
                FROM model_performance 
                ORDER BY timestamp DESC LIMIT 1
            """)
            basic_training = cursor.fetchone()
            
            if basic_training:
                print(f"\n🔧 Basic Model Performance:")
                print(f"   Last training: {basic_training[0]}")
                print(f"   Samples used: {basic_training[2] if basic_training[2] else 'N/A'}")
                print(f"   Accuracy: {basic_training[1]:.3f}")
                
                last_time = datetime.fromisoformat(basic_training[0])
                hours_ago = (now - last_time).total_seconds() / 3600
                print(f"   Hours ago: {hours_ago:.1f}")
            else:
                print("ℹ️ No basic training records found")
        except Exception as e:
            print(f"ℹ️ Basic training table not accessible: {e}")
        
        # Check ml_performance_tracking
        try:
            cursor = conn.execute("""
                SELECT created_at, training_samples, accuracy 
                FROM ml_performance_tracking 
                ORDER BY created_at DESC LIMIT 1
            """)
            tracking_record = cursor.fetchone()
            
            if tracking_record:
                print(f"\n📈 ML Performance Tracking:")
                print(f"   Last record: {tracking_record[0]}")
                print(f"   Samples: {tracking_record[1] if tracking_record[1] else 'N/A'}")
                print(f"   Accuracy: {tracking_record[2]:.3f if tracking_record[2] else 'N/A'}")
                
                last_time = datetime.fromisoformat(tracking_record[0])
                hours_ago = (now - last_time).total_seconds() / 3600
                print(f"   Hours ago: {hours_ago:.1f}")
            else:
                print("ℹ️ No tracking records found")
        except Exception as e:
            print(f"ℹ️ ML tracking table not accessible: {e}")
        
        # Check enhanced evening analysis
        cursor = conn.execute("""
            SELECT COUNT(*) FROM enhanced_evening_analysis 
            WHERE timestamp > datetime('now', '-7 days')
        """)
        recent_analyses = cursor.fetchone()[0]
        print(f"📈 Enhanced analyses (last 7 days): {recent_analyses}")
        
        # Check for recent analysis failures
        cursor = conn.execute("""
            SELECT timestamp, model_training 
            FROM enhanced_evening_analysis 
            ORDER BY timestamp DESC LIMIT 3
        """)
        
        recent_results = cursor.fetchall()
        if recent_results:
            print("\n🔍 Recent Analysis Results:")
            for timestamp, model_training in recent_results:
                training_data = json.loads(model_training) if model_training else {}
                success = training_data.get('training_successful', False)
                attempted = training_data.get('training_attempted', False)
                error = training_data.get('error', 'No error')
                
                status = "✅ Success" if success else "❌ Failed" if attempted else "⏭️ Skipped"
                print(f"   {timestamp}: {status}")
                if not success and attempted:
                    print(f"      Error: {error}")
                    
                # Show more details for successful trainings
                if success:
                    samples = training_data.get('training_data_stats', {}).get('total_samples', 'N/A')
                    performance = training_data.get('performance_metrics', {})
                    if performance:
                        accuracy = performance.get('overall_accuracy', 'N/A')
                        print(f"      Samples: {samples}, Accuracy: {accuracy}")
        
        # Additional check: Show what training approach is being used
        print("\n🔧 Current Training System Analysis:")
        
        # Check if there are any recent enhanced_morning_analysis entries
        try:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM enhanced_morning_analysis 
                WHERE timestamp > datetime('now', '-1 days')
            """)
            morning_count = cursor.fetchone()[0]
            print(f"📅 Morning analyses (last 24h): {morning_count}")
        except:
            print("📅 Morning analyses: Table not found")
        
        # Check system status
        print(f"\n🎯 Key Metrics:")
        print(f"   Available samples: {sample_count}")
        
        # Determine if training should happen based on conditions
        if enhanced_training:
            new_samples = sample_count - enhanced_training[1]
            hours_since = (datetime.now() - datetime.fromisoformat(enhanced_training[0])).total_seconds() / 3600
            
            should_train = new_samples >= 5 or hours_since >= 12
            print(f"   New samples since last training: {new_samples}")
            print(f"   Hours since last training: {hours_since:.1f}")
            print(f"   Should trigger retraining: {'✅ YES' if should_train else '❌ NO'}")
            
            if should_train:
                if new_samples >= 5:
                    print(f"      Reason: {new_samples} new samples (≥5 threshold)")
                if hours_since >= 12:
                    print(f"      Reason: {hours_since:.1f} hours (≥12h threshold)")
        else:
            print(f"   Should trigger training: ✅ YES (no previous training found)")
        
        conn.close()
        
        # Check if enhanced system can be imported
        print("\n🧪 Testing Enhanced ML System Import:")
        try:
            from enhanced_ml_system.analyzers.enhanced_evening_analyzer_with_ml import EnhancedEveningAnalyzer
            print("✅ Enhanced ML system can be imported")
            return True
        except Exception as e:
            print(f"❌ Enhanced ML system import failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def force_training_run():
    """Force a training run to happen now"""
    
    print("\n🚀 Forcing ML Training Run")
    print("=" * 30)
    
    try:
        # Try enhanced training first
        try:
            from enhanced_ml_system.analyzers.enhanced_evening_analyzer_with_ml import EnhancedEveningAnalyzer
            
            print("🧠 Running Enhanced ML Training...")
            analyzer = EnhancedEveningAnalyzer()
            
            # Run the training method directly
            training_results = analyzer._train_enhanced_models()
            
            print(f"Training attempted: {training_results.get('training_attempted', False)}")
            print(f"Training successful: {training_results.get('training_successful', False)}")
            
            if training_results.get('error'):
                print(f"Error: {training_results['error']}")
            
            if training_results.get('training_successful'):
                print("✅ Enhanced ML training completed!")
                
                # Show performance metrics
                performance = training_results.get('performance_metrics', {})
                if performance:
                    print("📊 Performance Metrics:")
                    for key, value in performance.items():
                        if isinstance(value, (int, float)):
                            print(f"   {key}: {value:.3f}")
                
                return True
            else:
                print("❌ Enhanced ML training failed")
                return False
                
        except Exception as e:
            print(f"❌ Enhanced training failed: {e}")
            print("\n🔄 Falling back to basic training...")
            
            # Try basic training as fallback
            try:
                # Import basic training components
                sys.path.append('.')
                from app.services.ml_service import MLService
                
                print("🔧 Running Basic ML Training...")
                ml_service = MLService()
                
                # This might work with basic training
                result = ml_service.train_models()
                
                if result:
                    print("✅ Basic ML training completed!")
                    return True
                else:
                    print("❌ Basic ML training also failed")
                    return False
                    
            except Exception as e2:
                print(f"❌ Basic training also failed: {e2}")
                return False
            
    except Exception as e:
        print(f"❌ Training failed: {e}")
        return False

def suggest_solutions():
    """Suggest solutions based on diagnosis"""
    
    print("\n💡 Suggested Solutions")
    print("=" * 25)
    
    print("1. 🔄 Run evening routine manually:")
    print("   python -m app.main evening")
    
    print("\n2. 🛠️ Fix NaN data issues:")
    print("   python fix_nan_training_data.py")
    
    print("\n3. 📦 Check dependencies on remote:")
    print("   pip install pandas numpy scikit-learn")
    
    print("\n4. 🔍 Check logs for errors:")
    print("   tail -f logs/trading_system.log")
    
    print("\n5. 🚀 Force immediate training:")
    print("   python diagnose_ml_training.py --force")

if __name__ == "__main__":
    
    if "--force" in sys.argv:
        # Just run forced training
        force_training_run()
    else:
        # Full diagnostic
        if diagnose_training_issues():
            print(f"\n{'='*50}")
            
            # Ask if user wants to force training
            try:
                response = input("\n🚀 Would you like to force a training run now? (y/n): ")
                if response.lower().startswith('y'):
                    force_training_run()
                else:
                    suggest_solutions()
            except:
                # If running in non-interactive environment
                suggest_solutions()
        else:
            suggest_solutions()
