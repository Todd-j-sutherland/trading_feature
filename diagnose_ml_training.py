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
    
    # Check database
    db_path = './data/trading_unified.db'
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        
        # Check training samples
        cursor = conn.execute("SELECT COUNT(*) FROM enhanced_outcomes")
        sample_count = cursor.fetchone()[0]
        print(f"📊 Training samples available: {sample_count}")
        
        # Check latest training
        cursor = conn.execute("""
            SELECT training_date, training_samples, direction_accuracy_1h 
            FROM model_performance_enhanced 
            ORDER BY training_date DESC LIMIT 1
        """)
        latest_training = cursor.fetchone()
        
        if latest_training:
            print(f"🕐 Last training: {latest_training[0]}")
            print(f"   Samples used: {latest_training[1]}")
            print(f"   Accuracy: {latest_training[2]:.3f}")
            
            # Calculate hours since last training
            from datetime import datetime
            last_time = datetime.fromisoformat(latest_training[0])
            now = datetime.now()
            hours_ago = (now - last_time).total_seconds() / 3600
            print(f"   Hours ago: {hours_ago:.1f}")
        else:
            print("❌ No training records found")
        
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
