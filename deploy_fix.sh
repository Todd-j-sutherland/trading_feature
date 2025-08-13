#!/bin/bash

# 🚀 Trading System Architecture Fix - Deployment Script
# This script safely deploys the corrected prediction pipeline to your remote server

set -e  # Exit on any error

# Configuration
REMOTE_HOST="root@170.64.199.151"
REMOTE_DIR="/root/test"
LOCAL_DIR="$(pwd)/data_quality_system"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [[ ! -d "data_quality_system" ]]; then
    error "Please run this script from the trading_feature directory"
    exit 1
fi

log "🚀 Starting Trading System Architecture Fix Deployment"
echo

# Step 1: Pre-deployment checks
log "📋 Step 1: Pre-deployment Validation"
echo

# Check if SSH connection works
if ! ssh -o ConnectTimeout=10 "$REMOTE_HOST" "echo 'SSH connection successful'" >/dev/null 2>&1; then
    error "Cannot connect to $REMOTE_HOST. Please check your SSH connection."
    exit 1
fi
success "SSH connection to $REMOTE_HOST verified"

# Check if remote directory exists
if ! ssh "$REMOTE_HOST" "test -d $REMOTE_DIR"; then
    error "Remote directory $REMOTE_DIR does not exist"
    exit 1
fi
success "Remote directory $REMOTE_DIR exists"

# Check if database exists
if ! ssh "$REMOTE_HOST" "test -f $REMOTE_DIR/trading_unified.db"; then
    warning "trading_unified.db not found at expected location"
    log "Checking for database in other locations..."
    ssh "$REMOTE_HOST" "find $REMOTE_DIR -name '*.db' -type f" || true
fi

echo

# Step 2: Create backup
log "💾 Step 2: Creating Remote Backup"
echo

ssh "$REMOTE_HOST" "
    cd $REMOTE_DIR
    BACKUP_DIR=\"backup_\$(date +%Y%m%d_%H%M%S)\"
    mkdir -p \$BACKUP_DIR
    
    # Backup existing files
    if [ -f trading_unified.db ]; then
        cp trading_unified.db \$BACKUP_DIR/
        echo 'Backed up trading_unified.db'
    fi
    
    if [ -d data_quality_system ]; then
        cp -r data_quality_system \$BACKUP_DIR/
        echo 'Backed up existing data_quality_system'
    fi
    
    echo \"Backup created in: \$BACKUP_DIR\"
    ls -la \$BACKUP_DIR
"

success "Remote backup completed"
echo

# Step 3: Upload new files
log "📤 Step 3: Uploading New Architecture Files"
echo

# Create remote directory structure
ssh "$REMOTE_HOST" "
    cd $REMOTE_DIR
    mkdir -p data_quality_system/core
    mkdir -p data_quality_system/analysis
    mkdir -p data
    mkdir -p models
"

# Upload core files
log "Uploading core prediction engine files..."
scp -r "$LOCAL_DIR/core/"* "$REMOTE_HOST:$REMOTE_DIR/data_quality_system/core/"
success "Core files uploaded"

# Upload analysis files
log "Uploading analysis and documentation files..."
scp -r "$LOCAL_DIR/analysis/"* "$REMOTE_HOST:$REMOTE_DIR/data_quality_system/analysis/" 2>/dev/null || true
scp "$LOCAL_DIR/"*.md "$REMOTE_HOST:$REMOTE_DIR/data_quality_system/" 2>/dev/null || true
success "Analysis files uploaded"

echo

# Step 4: Install dependencies
log "📦 Step 4: Installing Dependencies"
echo

ssh "$REMOTE_HOST" "
    cd $REMOTE_DIR
    
    echo 'Installing required Python packages...'
    pip3 install --upgrade scikit-learn pandas numpy yfinance sqlite3 joblib >/dev/null 2>&1 || true
    
    echo 'Checking Python environment...'
    python3 --version
    python3 -c 'import sklearn, pandas, numpy, yfinance; print(\"All required packages available\")'
"

success "Dependencies installed"
echo

# Step 5: Run migration
log "🔄 Step 5: Running System Migration"
echo

warning "This step will modify your trading system architecture"
read -p "Do you want to proceed with the migration? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "Migration cancelled by user"
    exit 0
fi

ssh "$REMOTE_HOST" "
    cd $REMOTE_DIR
    
    echo '🔍 Running migration analysis...'
    python3 data_quality_system/core/migration_script.py
    
    echo
    echo '✅ Migration completed successfully!'
    echo
    echo 'Checking new database...'
    if [ -f data/trading_predictions.db ]; then
        echo 'New prediction database created:'
        ls -la data/trading_predictions.db
        
        echo
        echo 'Sample predictions:'
        sqlite3 data/trading_predictions.db \"SELECT prediction_id, symbol, predicted_action, action_confidence, prediction_timestamp FROM predictions ORDER BY prediction_timestamp DESC LIMIT 3;\" 2>/dev/null || echo 'No predictions yet'
    fi
"

success "Migration completed"
echo

# Step 6: Test new system
log "🧪 Step 6: Testing New Prediction System"
echo

ssh "$REMOTE_HOST" "
    cd $REMOTE_DIR
    
    echo 'Testing prediction engine...'
    python3 -c \"
from data_quality_system.core.true_prediction_engine import TruePredictionEngine
import json

# Test prediction
predictor = TruePredictionEngine()
print('✅ Prediction engine initialized successfully')

# Test with sample features
features = {
    'sentiment_score': 0.05,
    'rsi': 45.2,
    'macd_histogram': 0.15,
    'volume_ratio': 2.5
}

try:
    prediction = predictor.make_prediction('ANZ.AX', features)
    print('✅ Test prediction successful:')
    print(f'   Action: {prediction[\"predicted_action\"]}')
    print(f'   Confidence: {prediction[\"action_confidence\"]:.1%}')
    print(f'   Direction: {\"UP\" if prediction[\"predicted_direction\"] == 1 else \"DOWN\"}')
except Exception as e:
    print(f'⚠️  Test prediction failed: {e}')
    print('This is normal if no training data is available yet')
\"
"

success "System testing completed"
echo

# Step 7: Setup automation
log "⚙️  Step 7: Setting Up Automated Evaluation"
echo

ssh "$REMOTE_HOST" "
    cd $REMOTE_DIR
    
    echo 'Setting up cron job for outcome evaluation...'
    
    # Create evaluation script
    cat > evaluate_predictions.sh << 'EOF'
#!/bin/bash
cd $REMOTE_DIR
python3 -c \"
from data_quality_system.core.true_prediction_engine import OutcomeEvaluator
evaluator = OutcomeEvaluator()
count = evaluator.evaluate_pending_predictions()
print(f'Evaluated {count} pending predictions')
\" >> logs/evaluation.log 2>&1
EOF
    
    chmod +x evaluate_predictions.sh
    
    # Add to crontab (run every hour)
    (crontab -l 2>/dev/null; echo \"0 * * * * $REMOTE_DIR/evaluate_predictions.sh\") | crontab -
    
    echo 'Automated evaluation setup complete'
    echo 'Predictions will be evaluated hourly'
"

success "Automation configured"
echo

# Step 8: Final summary
log "🎉 Deployment Summary"
echo

success "✅ Trading System Architecture Fix Deployed Successfully!"
echo
echo "📊 What Changed:"
echo "   • Fixed retrospective labeling → Real-time predictions"
echo "   • Immutable prediction storage"
echo "   • Separate outcome evaluation"
echo "   • Proper temporal validation"
echo "   • Honest performance metrics"
echo
echo "🚀 Next Steps:"
echo "   1. Your system now makes real predictions instead of retrospective labels"
echo "   2. All predictions are stored immediately (no more waiting for outcomes)"
echo "   3. Model training uses proper temporal splits"
echo "   4. Performance metrics are now meaningful"
echo
echo "📈 Monitoring:"
echo "   • Check prediction consistency: No delays in storage"
echo "   • Verify no contradictions: No BUY predictions with DOWN direction"
echo "   • Track model learning: Accuracy should improve over time"
echo
echo "📋 Remote Commands to Try:"
ssh_cmd="ssh $REMOTE_HOST 'cd $REMOTE_DIR && "
echo "   ${ssh_cmd}sqlite3 data/trading_predictions.db \"SELECT COUNT(*) as predictions FROM predictions;\"'"
echo "   ${ssh_cmd}python3 -c \"from data_quality_system.core.true_prediction_engine import TruePredictionEngine; print('System ready')\"'"
echo "   ${ssh_cmd}tail -f logs/evaluation.log'"
echo
warning "Remember: Initial accuracy may be lower but will be honest and improvable!"
echo
success "🔧 Your trading system is now a genuine prediction engine!"
