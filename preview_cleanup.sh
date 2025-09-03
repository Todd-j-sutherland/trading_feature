#!/bin/bash
"""
Workspace Cleanup Preview - Shows what will be kept vs removed
"""

echo "🔍 WORKSPACE CLEANUP PREVIEW"
echo "============================="
echo ""

echo "✅ WILL BE KEPT (Core Production System):"
echo "├── app/                                    # Main application"
echo "├── market-aware-paper-trading/             # Market-aware paper trading" 
echo "├── paper-trading-app/                      # Production paper trading"
echo "├── helpers/                                # Utility functions"
echo "├── documentation/                          # Essential docs"
echo "├── data/                                   # Current production data"
echo "├── trading_venv/                           # Python environment"
echo "├── enhanced_efficient_system_market_aware_integrated.py  # Production system"
echo "├── enhanced_efficient_system_market_aware.py            # Standalone system"
echo "├── requirements.txt                        # Dependencies"
echo "├── setup_market_aware_cron.sh             # Cron setup"
echo "├── verify_market_aware_integration.sh     # Verification"
echo "├── evaluate_predictions.sh                # Evaluation script"
echo "├── .env.example                            # Config template"
echo "├── .gitignore                              # Git config"
echo "├── .git/                                   # Git repository"
echo "└── README.md                               # Main readme"
echo ""

echo "🗑️ WILL BE REMOVED (Bloated Experimental Files):"
echo ""

echo "📁 Experimental Subdirectories:"
ls -la | grep "^d" | grep -E "(results|data_quality|frontend|optional|models|utils|enhanced_ml)" | grep -v -E "(paper-trading|helpers)" | sed 's/^/  /'

echo ""
echo "🐍 Temporary Python Files (Will remove 180+ files):"
ls -1 *.py 2>/dev/null | grep -v "enhanced_efficient_system_market_aware" | wc -l | xargs echo "  Total to remove:"
echo "  Examples:"
ls -1 *.py 2>/dev/null | grep -v "enhanced_efficient_system_market_aware" | head -10 | sed 's/^/    /'
echo "    ... and 170+ more temporary files"

echo ""
echo "📄 Redundant Documentation:"
ls -1 *.md 2>/dev/null | grep -v "README.md" | wc -l | xargs echo "  Total to remove:"
echo "  Examples:"
ls -1 *.md 2>/dev/null | grep -v "README.md" | head -5 | sed 's/^/    /'

echo ""
echo "🔧 Shell Scripts (keeping 3, removing others):"
ls -1 *.sh 2>/dev/null | wc -l | xargs echo "  Total scripts:"
echo "  Will keep: setup_market_aware_cron.sh, verify_market_aware_integration.sh, evaluate_predictions.sh"

echo ""
echo "📊 EXPECTED RESULTS:"
echo "Before: $(find . -maxdepth 1 -type f | wc -l) files in root"
echo "After:  ~15 files in root (90% reduction)"
echo ""
echo "Before: $(find . -maxdepth 1 -name "*.py" | wc -l) Python files"
echo "After:  2 Python files (99% reduction)"
echo ""

echo "⚠️  SAFETY MEASURES:"
echo "✅ Complete backup will be created"
echo "✅ Production system preserved"
echo "✅ Remote system unaffected"
echo "✅ Git history maintained"
echo "✅ Rollback available"

echo ""
echo "🚀 Ready to run cleanup? Execute: ./safe_workspace_cleanup.sh"
