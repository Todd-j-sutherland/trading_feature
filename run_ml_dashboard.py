#!/usr/bin/env python3
"""
Quick ML Dashboard Runner
Runs the ML progression dashboard to showcase machine learning success rates over time
"""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
app_dir = Path(__file__).parent / "paper-trading-app"
sys.path.append(str(app_dir))

def run_ml_dashboard():
    """Run the ML progression dashboard"""
    try:
        # Try to run the full professional dashboard
        from app.dashboard.main import main
        print("🚀 Starting Professional Dashboard with ML Progression...")
        print("📊 The ML Progression tab shows:")
        print("   • Accuracy trends over time") 
        print("   • Confidence progression")
        print("   • Trading success rate (your 20-30% ML contribution)")
        print("   • Model improvement analysis")
        print("   • Daily performance metrics")
        print()
        print("🌐 Opening dashboard at http://localhost:8501")
        main()
        
    except ImportError as e:
        print(f"❌ Error importing dashboard components: {e}")
        print("💡 Try running from the paper-trading-app directory:")
        print("   cd paper-trading-app")
        print("   streamlit run app/dashboard/main.py")
        
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        print("💡 Alternative commands:")
        print("   streamlit run paper-trading-app/app/dashboard/main.py")
        print("   python -m streamlit run paper-trading-app/app/dashboard/ml_trading_dashboard.py")

if __name__ == "__main__":
    run_ml_dashboard()