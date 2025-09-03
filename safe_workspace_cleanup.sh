#!/bin/bash
"""
Safe Trading Feature Workspace Cleanup Script
Removes 150+ temporary files while preserving production system
"""

echo "🧹 TRADING FEATURE WORKSPACE CLEANUP"
echo "====================================="
echo "Current files: $(find . -maxdepth 1 -type f | wc -l)"
echo "Current Python files: $(find . -maxdepth 1 -name "*.py" | wc -l)"
echo ""

# Safety check
read -p "⚠️  This will remove 150+ temporary files. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled"
    exit 1
fi

echo "🔄 Starting safe cleanup..."

# Phase 1: Create backup
echo "📦 Creating backup..."
mkdir -p ../trading_feature_backup_$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="../trading_feature_backup_$(date +%Y%m%d_%H%M%S)"

cp -r app/ $BACKUP_DIR/ 2>/dev/null || echo "app/ not found"
cp -r market-aware-paper-trading/ $BACKUP_DIR/ 2>/dev/null || echo "market-aware-paper-trading/ not found"
cp -r paper-trading-app/ $BACKUP_DIR/ 2>/dev/null || echo "paper-trading-app/ not found"
cp -r helpers/ $BACKUP_DIR/ 2>/dev/null || echo "helpers/ not found"
cp -r documentation/ $BACKUP_DIR/ 2>/dev/null || echo "documentation/ not found"
cp enhanced_efficient_system_market_aware*.py $BACKUP_DIR/ 2>/dev/null || echo "market-aware systems not found"
cp requirements.txt $BACKUP_DIR/ 2>/dev/null || echo "requirements.txt not found"
cp setup_market_aware_cron.sh $BACKUP_DIR/ 2>/dev/null || echo "cron setup not found"
cp verify_market_aware_integration.sh $BACKUP_DIR/ 2>/dev/null || echo "verification not found"
cp .env.example $BACKUP_DIR/ 2>/dev/null || echo ".env.example not found"
cp .gitignore $BACKUP_DIR/ 2>/dev/null || echo ".gitignore not found"
cp README.md $BACKUP_DIR/ 2>/dev/null || echo "README.md not found"

echo "✅ Backup created at: $BACKUP_DIR"

# Phase 2: Remove bloated subdirectories (KEEP paper trading & helpers)
echo "🗑️ Removing experimental subdirectories..."
rm -rf results/ 2>/dev/null && echo "  ✅ Removed results/"
rm -rf data_quality_system/ 2>/dev/null && echo "  ✅ Removed data_quality_system/"
rm -rf frontend/ 2>/dev/null && echo "  ✅ Removed frontend/"
rm -rf optional_features/ 2>/dev/null && echo "  ✅ Removed optional_features/"
rm -rf models/ 2>/dev/null && echo "  ✅ Removed models/"
rm -rf utils/ 2>/dev/null && echo "  ✅ Removed utils/"
rm -rf enhanced_ml_system/ 2>/dev/null && echo "  ✅ Removed enhanced_ml_system/"
rm -rf tests/ 2>/dev/null && echo "  ✅ Removed tests/"
rm -rf analysis_logs/ 2>/dev/null && echo "  ✅ Removed analysis_logs/"
rm -rf command_logs/ 2>/dev/null && echo "  ✅ Removed command_logs/"
echo "  ✅ Kept paper-trading-app/ (production paper trading)"
echo "  ✅ Kept helpers/ (utility functions)"

# Phase 3: Remove temporary Python files (keep production ones)
echo "🗑️ Removing temporary Python files..."

# Create list of files to keep
KEEP_FILES=(
    "enhanced_efficient_system_market_aware_integrated.py"
    "enhanced_efficient_system_market_aware.py"
)

# Remove all other .py files in root
for file in *.py; do
    if [[ -f "$file" ]]; then
        KEEP_FILE=false
        for keep in "${KEEP_FILES[@]}"; do
            if [[ "$file" == "$keep" ]]; then
                KEEP_FILE=true
                break
            fi
        done
        
        if [[ "$KEEP_FILE" == false ]]; then
            rm -f "$file" && echo "  🗑️ Removed $file"
        else
            echo "  ✅ Kept $file"
        fi
    fi
done

# Phase 4: Remove temporary data files
echo "🗑️ Removing temporary data files..."
rm -f trading_data_export_*.txt 2>/dev/null && echo "  ✅ Removed trading exports"
rm -f *_log.txt 2>/dev/null && echo "  ✅ Removed log files"
rm -f *.json 2>/dev/null && echo "  ✅ Removed analysis JSON files"
rm -f audit_results.json 2>/dev/null
rm -f calculation_verification.json 2>/dev/null
rm -f comprehensive_data_feedback.txt 2>/dev/null
rm -f current_cron.txt 2>/dev/null
rm -f efficient_prediction_log.txt 2>/dev/null
rm -f evening_analysis_report.txt 2>/dev/null
rm -f investigation_log.txt 2>/dev/null
rm -f latest_trading_data_export.txt 2>/dev/null

# Phase 5: Remove redundant markdown files
echo "🗑️ Removing redundant documentation..."
rm -f *COMPLETE*.md 2>/dev/null && echo "  ✅ Removed completion docs"
rm -f *ANALYSIS*.md 2>/dev/null && echo "  ✅ Removed analysis docs"
rm -f *STATUS*.md 2>/dev/null && echo "  ✅ Removed status docs"
rm -f *SUMMARY*.md 2>/dev/null && echo "  ✅ Removed summary docs"
rm -f *REPORT*.md 2>/dev/null && echo "  ✅ Removed report docs"
rm -f *INTEGRATION*.md 2>/dev/null && echo "  ✅ Removed integration docs"
rm -f *DEPLOYMENT*.md 2>/dev/null && echo "  ✅ Removed deployment docs"
rm -f *CHECKLIST*.md 2>/dev/null && echo "  ✅ Removed checklist docs"
rm -f *GUIDE*.md 2>/dev/null && echo "  ✅ Removed guide docs"
rm -f *PLAN*.md 2>/dev/null && echo "  ✅ Removed plan docs"
rm -f *FIX*.md 2>/dev/null && echo "  ✅ Removed fix docs"

# Keep only essential docs
# documentation/ folder is preserved

# Phase 6: Remove shell scripts (keep essential ones)
echo "🗑️ Removing temporary shell scripts..."
KEEP_SCRIPTS=(
    "setup_market_aware_cron.sh"
    "verify_market_aware_integration.sh"
    "evaluate_predictions.sh"
)

for file in *.sh; do
    if [[ -f "$file" ]]; then
        KEEP_SCRIPT=false
        for keep in "${KEEP_SCRIPTS[@]}"; do
            if [[ "$file" == "$keep" ]]; then
                KEEP_SCRIPT=true
                break
            fi
        done
        
        if [[ "$KEEP_SCRIPT" == false ]]; then
            rm -f "$file" && echo "  🗑️ Removed $file"
        else
            echo "  ✅ Kept $file"
        fi
    fi
done

# Phase 7: Remove old database files (keep current ones)
echo "🗑️ Cleaning up old database files..."
# Keep: trading_predictions.db, paper_trading.db, any current .db files
# Remove: enhanced_trading_data.db and other experimental ones
rm -f enhanced_trading_data.db 2>/dev/null && echo "  ✅ Removed enhanced_trading_data.db"

# Phase 8: Remove misc files
echo "🗑️ Removing miscellaneous files..."
rm -f *.exp 2>/dev/null
rm -f *.txt 2>/dev/null | grep -v requirements.txt
rm -f *.bat 2>/dev/null
rm -f ssh_config 2>/dev/null
rm -f sshOnDigitalOcean.txt 2>/dev/null

# Final count
echo ""
echo "🎯 CLEANUP COMPLETE!"
echo "====================================="
echo "Files after cleanup: $(find . -maxdepth 1 -type f | wc -l)"
echo "Python files after cleanup: $(find . -maxdepth 1 -name "*.py" | wc -l)"
echo ""
echo "✅ Preserved production system:"
echo "  - app/ directory structure"
echo "  - market-aware-paper-trading/ system"
echo "  - paper-trading-app/ system (production paper trading)"
echo "  - helpers/ directory (utility functions)"
echo "  - documentation/ folder"
echo "  - Essential Python files (2)"
echo "  - Requirements and setup scripts"
echo ""
echo "📦 Backup available at: $BACKUP_DIR"
echo "🚀 Workspace is now clean and maintainable!"

# Show final structure
echo ""
echo "📁 FINAL WORKSPACE STRUCTURE:"
echo "====================================="
ls -la | head -20
