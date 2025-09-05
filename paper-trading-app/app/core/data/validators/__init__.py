"""
Data Validators Module

This module provides access to the comprehensive validation framework components:

Validation Framework Components:
1. Dashboard Validation (helpers/export_and_validate_metrics.py):
   - MetricsValidator class validates dashboard metrics, sentiment data, ML performance
   - Validates ML success rates (0-100%), confidence levels, feature analysis
   - Validates ASX bank data completeness and database health

2. Database Structure Validation (tests/test_data_validation.py):
   - Unit tests for database table data integrity
   - Validates sentiment scores [-1,1], confidence [0,1], RSI [0,100]
   - Tests trading signal types and ML prediction ranges

3. Enhanced ML Validation (app/core/ml/enhanced_training_pipeline.py):
   - DataValidator class for ML features and training data
   - Prevents future data leakage, validates feature quality
   - Range validation for sentiment, technical, and price data

4. Frontend Validation (frontend/src/components/IntegratedMLDashboard.tsx):
   - validation_status integration with visual indicators
   - Color-coded validation results (green=passed, red=failed)

Usage Commands:
- python helpers/export_and_validate_metrics.py  # Primary validation
- python tests/test_data_validation.py           # Database tests  
- python helpers/validate_system.py              # Quick summary
- python run_comprehensive_tests.py              # Full validation

Generated Files (metrics_exports/):
- dashboard_metrics_{timestamp}.json     # Raw data
- validation_results_{timestamp}.json    # Detailed results
- validation_summary_{timestamp}.txt     # Summary report

Quality Thresholds:
- Data quality score: 85% minimum
- Average confidence: 60% minimum  
- News coverage: 70% minimum
- Sentiment reliability: 75% minimum

For complete documentation, see: DATA_VALIDATION_SYSTEM.md
"""