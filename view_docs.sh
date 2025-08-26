#!/bin/bash
# Documentation Viewer for ASX Trading System

DOC_DIR="/root/test/documentation"

case "$1" in
    "quick"|"ref")
        echo "📋 Quick Reference Card"
        echo "======================="
        cat "$DOC_DIR/QUICK_REFERENCE_CARD.md"
        ;;
    "guide"|"user")
        echo "📖 User Guide"
        echo "=============="
        cat "$DOC_DIR/ASX_TRADING_APPLICATION_USER_GUIDE.md"
        ;;
    "arch"|"architecture")
        echo "🏗️ System Architecture"
        echo "======================"
        cat "$DOC_DIR/SYSTEM_ARCHITECTURE.md"
        ;;
    "deploy"|"deployment")
        echo "🚀 Deployment Checklist"
        echo "======================="
        cat "$DOC_DIR/DEPLOYMENT_CHECKLIST.md"
        ;;
    "restart"|"recovery"|"vm")
        echo "🔄 VM Restart & Recovery Guide"
        echo "=============================="
        cat "$DOC_DIR/VM_RESTART_RECOVERY_GUIDE.md"
        ;;
    "fixes"|"fix")
        echo "🔧 Evening Routine ML Training Fix Plan"
        echo "======================================="
        cat "$DOC_DIR/EVENING_ROUTINE_ML_TRAINING_FIX_PLAN.md"
        ;;
    "monday"|"weekly")
        echo "📋 Monday Morning Checklist"
        echo "==========================="
        cat "$DOC_DIR/MONDAY_MORNING_CHECKLIST.md"
        ;;
    "index"|""|"help")
        echo "📚 Documentation Index"
        echo "======================"
        cat "$DOC_DIR/README.md"
        ;;
    *)
        echo "📚 ASX Trading System Documentation Viewer"
        echo "=========================================="
        echo ""
        echo "Usage: ./view_docs.sh [document]"
        echo ""
        echo "Available documents:"
        echo "  quick, ref     - Quick Reference Card"
        echo "  guide, user    - Complete User Guide"  
        echo "  arch           - System Architecture"
        echo "  deploy         - Deployment Checklist"
        echo "  restart, vm    - VM Restart & Recovery Guide"
        echo "  fixes, fix     - ML Training Fix Documentation"
        echo "  monday, weekly - Monday Morning Checklist"
        echo "  index, help    - This documentation index"
        echo ""
        echo "Examples:"
        echo "  ./view_docs.sh quick      # Quick reference"
        echo "  ./view_docs.sh restart    # VM recovery guide"
        echo "  ./view_docs.sh guide      # Full user guide"
        echo "  ./view_docs.sh            # Documentation index"
        ;;
esac
