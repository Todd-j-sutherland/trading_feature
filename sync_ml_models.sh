#!/bin/bash

# ML Models Sync Script
# Syncs trained ML models to remote server

echo "🚀 Syncing ML Models to Remote Server..."

# Sync the ML models directory
echo "📁 Syncing data/ml_models directory..."
scp -i ~/.ssh/id_rsa -r data/ml_models root@170.64.199.151:/root/test/data/

if [ $? -eq 0 ]; then
    echo "✅ ML models synced successfully!"
    
    echo "🧪 Testing ML models on remote server..."
    
    # Test the models remotely
    ssh -i ~/.ssh/id_rsa root@170.64.199.151 "
        cd test && 
        source ../trading_venv/bin/activate && 
        export PYTHONPATH=/root/test && 
        python -c \"
from app.core.ml.enhanced_pipeline import EnhancedMLPipeline
pipeline = EnhancedMLPipeline()
print('Remote ML Pipeline initialized with', len(pipeline.models), 'models')
predictions = pipeline.predict({'CBA': {'sentiment_score': 0.65, 'confidence': 0.8, 'news_count': 5}})
print('Remote predictions working:', not 'error' in predictions)
\""
    
    if [ $? -eq 0 ]; then
        echo "✅ Remote ML models are working!"
        echo "🌐 You can now run the dashboard remotely with ML predictions:"
        echo "   ssh -i ~/.ssh/id_rsa root@170.64.199.151"
        echo "   cd test && source ../trading_venv/bin/activate && export PYTHONPATH=/root/test"
        echo "   streamlit run app/dashboard/enhanced_main.py --server.port 8501 --server.address 0.0.0.0"
    else
        echo "❌ Remote ML test failed. Check dependencies on remote server."
    fi
else
    echo "❌ Failed to sync ML models to remote server."
fi
