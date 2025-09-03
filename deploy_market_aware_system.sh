#!/bin/bash
"""
Deploy Market-Aware Prediction System to Remote Server
Copies the enhanced files and integrates them into the main application
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 DEPLOYING MARKET-AWARE PREDICTION SYSTEM${NC}"
echo "=================================================="

# Remote server details
REMOTE_SERVER="root@170.64.199.151"
REMOTE_APP_DIR="/root/test/paper-trading-app"

echo -e "${YELLOW}📋 Deployment Plan:${NC}"
echo "   • Copy market-aware predictor to app/core/ml/prediction/"
echo "   • Copy enhanced daily manager to app/services/"
echo "   • Copy enhanced main application"
echo "   • Update module imports"
echo "   • Test integration"

# Check if remote directory exists
echo -e "\n${BLUE}🔍 Checking remote server structure...${NC}"
ssh $REMOTE_SERVER "ls -la $REMOTE_APP_DIR/app/core/ml/prediction/" || {
    echo -e "${RED}❌ Remote prediction directory not found${NC}"
    echo -e "${YELLOW}💡 Creating directory structure...${NC}"
    ssh $REMOTE_SERVER "mkdir -p $REMOTE_APP_DIR/app/core/ml/prediction/"
    ssh $REMOTE_SERVER "mkdir -p $REMOTE_APP_DIR/app/services/"
}

# Copy market-aware predictor
echo -e "\n${BLUE}📁 Copying market-aware predictor...${NC}"
scp "app/core/ml/prediction/market_aware_predictor.py" \
    "$REMOTE_SERVER:$REMOTE_APP_DIR/app/core/ml/prediction/"

# Update prediction module __init__.py
echo -e "${BLUE}📝 Updating prediction module imports...${NC}"
scp "app/core/ml/prediction/__init__.py" \
    "$REMOTE_SERVER:$REMOTE_APP_DIR/app/core/ml/prediction/"

# Copy enhanced daily manager
echo -e "${BLUE}📁 Copying enhanced daily manager...${NC}"
scp "app/services/market_aware_daily_manager.py" \
    "$REMOTE_SERVER:$REMOTE_APP_DIR/app/services/"

# Update services module __init__.py
echo -e "${BLUE}📝 Updating services module imports...${NC}"
scp "app/services/__init__.py" \
    "$REMOTE_SERVER:$REMOTE_APP_DIR/app/services/"

# Copy enhanced main application
echo -e "${BLUE}📁 Copying enhanced main application...${NC}"
scp "app/main_enhanced.py" \
    "$REMOTE_SERVER:$REMOTE_APP_DIR/app/"

# Create deployment summary
echo -e "\n${BLUE}📊 Creating deployment summary...${NC}"
cat > deployment_summary.md << 'EOF'
# Market-Aware Prediction System Deployment

## Files Deployed:
1. `app/core/ml/prediction/market_aware_predictor.py` - Core market-aware prediction logic
2. `app/core/ml/prediction/__init__.py` - Updated module imports  
3. `app/services/market_aware_daily_manager.py` - Enhanced daily manager
4. `app/services/__init__.py` - Updated service imports
5. `app/main_enhanced.py` - Enhanced main application

## Key Features Deployed:
- ✅ Market context analysis (ASX 200 trend)
- ✅ Reduced base confidence (20% → 10%)
- ✅ Dynamic BUY thresholds based on market conditions
- ✅ Enhanced bearish market requirements
- ✅ Emergency market stress filtering
- ✅ Comprehensive logging and database integration

## Usage Commands:
```bash
# Test market context
python -m app.main_enhanced test-market-context

# Test predictor
python -m app.main_enhanced test-predictor

# Market status check
python -m app.main_enhanced market-status

# Generate market-aware signals
python -m app.main_enhanced market-signals

# Enhanced morning routine
python -m app.main_enhanced market-morning
```

## Expected Impact:
- Significantly fewer BUY signals during bearish markets
- Higher quality remaining signals
- Better risk management during market stress
- Market context awareness in all predictions
EOF

scp "deployment_summary.md" "$REMOTE_SERVER:$REMOTE_APP_DIR/"

# Test deployment
echo -e "\n${BLUE}🧪 Testing deployment...${NC}"
echo -e "${YELLOW}Testing Python imports...${NC}"
ssh $REMOTE_SERVER "cd $REMOTE_APP_DIR && python -c \"
try:
    from app.core.ml.prediction import MarketAwarePricePredictor, create_market_aware_predictor
    from app.services import MarketAwareTradingManager
    print('✅ All imports successful')
except Exception as e:
    print(f'❌ Import error: {e}')
\"" || echo -e "${RED}❌ Import test failed${NC}"

# Test market context
echo -e "${YELLOW}Testing market context analysis...${NC}"
ssh $REMOTE_SERVER "cd $REMOTE_APP_DIR && timeout 30 python -m app.main_enhanced test-market-context" || {
    echo -e "${RED}❌ Market context test failed${NC}"
}

# Show remote file structure
echo -e "\n${BLUE}📂 Remote file structure:${NC}"
ssh $REMOTE_SERVER "cd $REMOTE_APP_DIR && find app -name '*market*' -type f"

# Verify database directory exists
echo -e "\n${BLUE}💾 Ensuring database directory exists...${NC}"
ssh $REMOTE_SERVER "cd $REMOTE_APP_DIR && mkdir -p data"

echo -e "\n${GREEN}✅ DEPLOYMENT COMPLETED${NC}"
echo -e "${YELLOW}💡 Next Steps:${NC}"
echo "   1. Test market context: ssh $REMOTE_SERVER 'cd $REMOTE_APP_DIR && python -m app.main_enhanced test-market-context'"
echo "   2. Test predictor: ssh $REMOTE_SERVER 'cd $REMOTE_APP_DIR && python -m app.main_enhanced test-predictor'"
echo "   3. Check market status: ssh $REMOTE_SERVER 'cd $REMOTE_APP_DIR && python -m app.main_enhanced market-status'"
echo "   4. Generate signals: ssh $REMOTE_SERVER 'cd $REMOTE_APP_DIR && python -m app.main_enhanced market-signals'"

echo -e "\n${BLUE}📋 Integration Options:${NC}"
echo "   • Replace existing prediction system with market-aware version"
echo "   • Run market-aware morning routine instead of standard routine"
echo "   • Use market context for manual trading decisions"
echo "   • Monitor BUY signal reduction during bearish markets"
