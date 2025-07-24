#!/usr/bin/env python3
"""
Minimal test that replicates the dashboard's ML tracker creation and component calls
"""

import sys
import traceback
sys.path.insert(0, '/root/test')

def test_dashboard_components():
    """Test the exact same way the dashboard creates and uses ML tracker"""
    
    print('🧪 TESTING DASHBOARD COMPONENTS (Exact Replication)')
    print('=' * 60)
    
    try:
        # Import the same way the dashboard does
        print('📦 Importing components...')
        from app.core.ml.tracking.progression_tracker import MLProgressionTracker
        from app.dashboard.components.trading_performance import enhanced_dashboard_performance_section
        from app.dashboard.components.ml_progression import render_ml_progression_dashboard
        print('✅ All imports successful')
        
        # Create ML tracker the same way the dashboard does
        print('\n🔧 Creating ML tracker...')
        from pathlib import Path
        data_path = Path('/root/test/data/ml_performance')
        ml_tracker = MLProgressionTracker(data_dir=data_path)
        print(f'✅ ML tracker created with {len(ml_tracker.prediction_history)} predictions')
        
        # Test the enhanced_dashboard_performance_section function
        print('\n🔍 Testing enhanced_dashboard_performance_section...')
        
        # We can't actually call streamlit functions, but we can test the data processing
        # Let's manually call the individual functions that enhanced_dashboard_performance_section calls
        
        from app.dashboard.components.trading_performance import (
            display_trading_performance_log,
            display_ml_learning_metrics,
            display_trading_signals_vs_outcomes
        )
        
        print('  Testing display_trading_performance_log...')
        
        # Simulate what streamlit does - create a mock streamlit object
        class MockStreamlit:
            def header(self, text): print(f'HEADER: {text}')
            def warning(self, text): print(f'WARNING: {text}')
            def info(self, text): print(f'INFO: {text}')
            def error(self, text): print(f'ERROR: {text}')
            def subheader(self, text): print(f'SUBHEADER: {text}')
            def dataframe(self, *args, **kwargs): print('DATAFRAME: Data displayed')
            def columns(self, n): return [MockStreamlit() for _ in range(n)]
            def selectbox(self, label, options, **kwargs): return options[0] if options else None
            def metric(self, label, value, delta=None): print(f'METRIC: {label} = {value}')
            def plotly_chart(self, *args, **kwargs): print('CHART: Plotly chart displayed')
        
        # Monkey patch streamlit
        import app.dashboard.components.trading_performance as tp_module
        tp_module.st = MockStreamlit()
        
        # Now try to call the function
        try:
            tp_module.display_trading_performance_log(ml_tracker)
            print('  ✅ display_trading_performance_log completed successfully')
        except Exception as e:
            print(f'  ❌ display_trading_performance_log failed: {e}')
            traceback.print_exc()
            return
        
        print('\n  Testing display_ml_learning_metrics...')
        try:
            tp_module.display_ml_learning_metrics(ml_tracker)
            print('  ✅ display_ml_learning_metrics completed successfully')
        except Exception as e:
            print(f'  ❌ display_ml_learning_metrics failed: {e}')
            traceback.print_exc()
            return
        
        print('\n  Testing display_trading_signals_vs_outcomes...')
        try:
            tp_module.display_trading_signals_vs_outcomes()
            print('  ✅ display_trading_signals_vs_outcomes completed successfully')
        except Exception as e:
            print(f'  ❌ display_trading_signals_vs_outcomes failed: {e}')
            traceback.print_exc()
            return
        
        print('\n🎯 ALL COMPONENT TESTS PASSED!')
        
    except Exception as e:
        print(f'\n💥 CRITICAL ERROR: {str(e)}')
        traceback.print_exc()

if __name__ == '__main__':
    test_dashboard_components()
