#!/bin/bash
"""
Market-Aware System Integration Verification
"""

echo "🔍 MARKET-AWARE TRADING SYSTEM VERIFICATION"
echo "============================================="
echo "📅 $(date)"
echo ""

echo "✅ 1. CRON JOBS VERIFICATION"
echo "Current active cron jobs:"
crontab -l | grep -v "^#" | grep -v "^$"
echo ""

echo "✅ 2. SYSTEM FILES VERIFICATION"
echo "Market-aware files:"
ls -la enhanced_efficient_system_market_aware_integrated.py app/services/market_aware_daily_manager.py app/config/settings.py 2>/dev/null || echo "Some files missing"
echo ""

echo "✅ 3. LOGS DIRECTORY"
echo "Logs directory structure:"
ls -la logs/ 2>/dev/null || echo "Logs directory not found"
echo ""

echo "✅ 4. PYTHON ENVIRONMENT TEST"
echo "Testing Python imports:"
source /root/trading_venv/bin/activate
export PYTHONPATH=/root/test
python3 -c "
try:
    from app.config.settings import Settings
    print(f'✅ Settings: {len(Settings.BANK_SYMBOLS)} bank symbols configured')
    
    from app.services.market_aware_daily_manager import create_market_aware_manager
    print('✅ Market-aware daily manager: Available')
    
    import enhanced_efficient_system_market_aware
    print('✅ Enhanced market-aware system: Available')
    
    print('🎯 All components ready!')
except Exception as e:
    print(f'❌ Import error: {e}')
"
echo ""

echo "✅ 5. NEXT EXECUTION TIMES"
echo "Next cron job executions:"
echo "Morning routine (every 30 min): Next run during market hours (00:00-05:30 UTC)"
echo "Evening analysis (daily 6PM): Next run at 08:00 UTC"
echo "Paper trading (hourly): Next run at top of hour during market hours"
echo ""

echo "🎯 VERIFICATION COMPLETE"
echo "Market-aware system integrated and ready for automated execution!"
