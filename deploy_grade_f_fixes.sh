#!/bin/bash
# Deployment script for Grade F quality fixes

echo "🚀 DEPLOYING GRADE F QUALITY FIXES"
echo "=================================="

# Check Python environment
echo "🐍 Checking Python environment..."
python3 --version
pip3 --version

# Install transformers and PyTorch if not available
echo "📦 Installing missing dependencies..."
pip3 install transformers torch --quiet

# Test installations
echo "🧪 Testing installations..."
python3 -c "import transformers; print('✅ Transformers available')" 2>/dev/null || echo "❌ Transformers still not available"
python3 -c "import torch; print('✅ PyTorch available')" 2>/dev/null || echo "❌ PyTorch still not available"

# Backup original news_analyzer.py
echo "💾 Creating backup..."
cp app/core/sentiment/news_analyzer.py app/core/sentiment/news_analyzer.py.backup_$(date +%Y%m%d_%H%M%S)

echo "✅ Deployment preparation complete"
echo "Next steps:"
echo "1. Apply quality assessment improvements to news_analyzer.py"
echo "2. Restart evening analysis to test fixes"
echo "3. Monitor quality grades for improvement"
