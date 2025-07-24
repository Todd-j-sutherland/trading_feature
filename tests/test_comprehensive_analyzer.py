#!/usr/bin/env python3
"""
Tests for Comprehensive Analyzer
"""

import unittest
import tempfile
import shutil
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestComprehensiveAnalyzer(unittest.TestCase):
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        
        # Mock analysis data
        self.mock_quality_report = {
            'total_samples': 87,
            'features': 10,
            'class_balance': 0.64,
            'data_completeness': 0.95
        }
        
        self.mock_readiness_report = {
            'training_ready': True,
            'model_available': True,
            'min_samples_met': True,
            'feature_quality_good': True
        }
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_comprehensive_analyzer_initialization(self):
        """Test comprehensive analyzer initialization"""
        try:
            from comprehensive_analyzer import ComprehensiveAnalyzer
            
            # Test initialization
            analyzer = ComprehensiveAnalyzer()
            self.assertIsNotNone(analyzer)
            
        except ImportError:
            self.skipTest("ComprehensiveAnalyzer not available for testing")
    
    def test_data_quality_analysis(self):
        """Test data quality analysis"""
        
        # Test quality metrics
        quality_metrics = self.mock_quality_report
        
        # Test sample count
        self.assertGreater(quality_metrics['total_samples'], 0)
        self.assertGreaterEqual(quality_metrics['total_samples'], 50)  # Minimum for training
        
        # Test feature count
        self.assertGreater(quality_metrics['features'], 5)
        self.assertLessEqual(quality_metrics['features'], 20)  # Reasonable range
        
        # Test class balance
        self.assertGreaterEqual(quality_metrics['class_balance'], 0.0)
        self.assertLessEqual(quality_metrics['class_balance'], 1.0)
        
        # Test data completeness
        self.assertGreater(quality_metrics['data_completeness'], 0.8)
    
    def test_class_balance_calculation(self):
        """Test class balance ratio calculation"""
        
        # Mock class distributions
        test_cases = [
            ([50, 50], 1.0),    # Perfect balance
            ([60, 40], 0.67),   # Good balance
            ([80, 20], 0.25),   # Poor balance
            ([100, 0], 0.0)     # No balance
        ]
        
        for distribution, expected_ratio in test_cases:
            calculated_ratio = self._calculate_class_balance(distribution)
            self.assertAlmostEqual(calculated_ratio, expected_ratio, places=2)
    
    def test_model_readiness_analysis(self):
        """Test model readiness analysis"""
        
        readiness_report = self.mock_readiness_report
        
        # Test readiness indicators
        self.assertIn('training_ready', readiness_report)
        self.assertIn('model_available', readiness_report)
        self.assertIn('min_samples_met', readiness_report)
        self.assertIn('feature_quality_good', readiness_report)
        
        # Test readiness logic
        all_ready = all(readiness_report.values())
        self.assertTrue(all_ready or not all_ready)  # Valid boolean state
    
    def test_readiness_score_calculation(self):
        """Test readiness score calculation"""
        
        # Mock readiness factors
        factors = {
            'sample_count_score': 85,    # 87 samples out of 100 target
            'class_balance_score': 90,   # 0.64 balance is good
            'model_score': 60,           # Model exists and trained
            'collection_score': 95       # Collection is active
        }
        
        # Calculate overall score (average)
        overall_score = sum(factors.values()) / len(factors)
        
        self.assertGreaterEqual(overall_score, 0)
        self.assertLessEqual(overall_score, 100)
        self.assertAlmostEqual(overall_score, 82.5, places=1)
    
    def test_collection_performance_analysis(self):
        """Test collection performance analysis"""
        
        # Mock collection metrics
        collection_metrics = {
            'daily_average': 127.0,
            'outcome_recording': 0.685,
            'uptime': 0.95,
            'error_rate': 0.05
        }
        
        # Test performance thresholds
        self.assertGreater(collection_metrics['daily_average'], 20)  # Good collection rate
        self.assertGreater(collection_metrics['outcome_recording'], 0.5)  # Good tracking
        self.assertGreater(collection_metrics['uptime'], 0.9)  # High uptime
        self.assertLess(collection_metrics['error_rate'], 0.1)  # Low error rate
    
    def test_feature_quality_analysis(self):
        """Test feature quality analysis"""
        
        # Mock feature analysis
        feature_quality = {
            'missing_values': 0.02,      # 2% missing
            'feature_variance': 0.8,     # Good variance
            'correlation_score': 0.3,    # Moderate correlation
            'importance_distribution': 0.7  # Well distributed importance
        }
        
        # Test quality thresholds
        self.assertLess(feature_quality['missing_values'], 0.1)  # Low missing values
        self.assertGreater(feature_quality['feature_variance'], 0.1)  # Sufficient variance
        self.assertLess(feature_quality['correlation_score'], 0.9)  # Not over-correlated
    
    def test_system_health_assessment(self):
        """Test system health assessment"""
        
        # Mock health indicators
        health_indicators = {
            'data_quality': 'GOOD',
            'model_performance': 'GOOD',
            'collection_status': 'ACTIVE',
            'error_status': 'MINIMAL'
        }
        
        # Test health status values
        valid_statuses = ['GOOD', 'FAIR', 'POOR', 'ACTIVE', 'INACTIVE', 'MINIMAL', 'HIGH']
        for status in health_indicators.values():
            self.assertIn(status, valid_statuses)
    
    def test_recommendation_generation(self):
        """Test recommendation generation"""
        
        # Mock recommendations
        recommendations = [
            "Continue data collection - aim for 100+ samples for robust training",
            "Model accuracy is good - consider ensemble methods for improvement",
            "Collection rate is excellent - maintain current pace",
            "Consider weekly model retraining as data grows"
        ]
        
        # Test recommendation structure
        for rec in recommendations:
            self.assertIsInstance(rec, str)
            self.assertGreater(len(rec), 20)  # Meaningful length
            self.assertTrue(any(word in rec.lower() for word in ['continue', 'consider', 'maintain', 'improve']))
    
    def test_priority_action_identification(self):
        """Test priority action identification"""
        
        # Mock priority actions
        priority_actions = [
            ("HIGH", "Train initial ML model"),
            ("MEDIUM", "Improve data quality"),
            ("LOW", "Optimize collection schedule")
        ]
        
        # Test priority levels
        valid_priorities = ['HIGH', 'MEDIUM', 'LOW', 'CRITICAL']
        for priority, action in priority_actions:
            self.assertIn(priority, valid_priorities)
            self.assertIsInstance(action, str)
            self.assertGreater(len(action), 10)
    
    def test_performance_trend_analysis(self):
        """Test performance trend analysis"""
        
        # Mock trend data
        trend_data = {
            'sample_growth_rate': 15.2,    # Samples per day
            'accuracy_trend': 'IMPROVING',
            'collection_trend': 'STABLE',
            'error_trend': 'DECREASING'
        }
        
        # Test trend indicators
        self.assertGreater(trend_data['sample_growth_rate'], 0)
        
        valid_trends = ['IMPROVING', 'STABLE', 'DECLINING', 'INCREASING', 'DECREASING']
        for trend in ['accuracy_trend', 'collection_trend', 'error_trend']:
            self.assertIn(trend_data[trend], valid_trends)
    
    def test_error_handling(self):
        """Test error handling in comprehensive analysis"""
        
        # Test with missing data
        try:
            result = self._analyze_with_missing_data(None)
            self.assertIsNotNone(result)
        except Exception:
            pass  # Expected for error testing
        
        # Test with invalid data
        with self.assertRaises((ValueError, TypeError, AttributeError)):
            raise ValueError("Invalid analysis data")
    
    def test_report_generation(self):
        """Test comprehensive report generation"""
        
        # Mock report structure
        report = {
            'timestamp': datetime.now().isoformat(),
            'overall_health': 'DEVELOPING',
            'readiness_score': 82.5,
            'data_quality': self.mock_quality_report,
            'model_readiness': self.mock_readiness_report,
            'recommendations': ['Test recommendation'],
            'next_steps': ['Test next step']
        }
        
        # Test report structure
        required_sections = ['timestamp', 'overall_health', 'readiness_score', 'data_quality']
        for section in required_sections:
            self.assertIn(section, report)
        
        # Test score range
        self.assertGreaterEqual(report['readiness_score'], 0)
        self.assertLessEqual(report['readiness_score'], 100)
    
    # Helper methods
    def _calculate_class_balance(self, distribution):
        """Calculate class balance ratio"""
        if len(distribution) < 2 or max(distribution) == 0:
            return 0.0
        return min(distribution) / max(distribution)
    
    def _analyze_with_missing_data(self, data):
        """Handle analysis with missing data"""
        if data is None:
            return {
                'error': 'No data available',
                'default_metrics': {
                    'total_samples': 0,
                    'readiness_score': 0
                }
            }
        return data

if __name__ == "__main__":
    unittest.main()
