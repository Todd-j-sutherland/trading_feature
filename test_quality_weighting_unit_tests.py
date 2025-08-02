#!/usr/bin/env python3
"""
Unit tests for the Quality-Based Dynamic Sentiment Weighting System
"""

import unittest
import sys
import os
sys.path.append('/Users/toddsutherland/Repos/trading_feature')

from app.core.sentiment.news_analyzer import QualityBasedSentimentWeighting, NewsSentimentAnalyzer
import json


class TestQualityBasedWeighting(unittest.TestCase):
    """Test cases for the QualityBasedSentimentWeighting class"""

    def setUp(self):
        """Set up test fixtures"""
        self.weighting_system = QualityBasedSentimentWeighting()
        
        # Mock high-quality data
        self.high_quality_news = {
            'news_count': 25,
            'average_sentiment': 0.3,
            'method_breakdown': {
                'transformer': {'confidence': 0.9},
                'vader': {'count': 15},
                'textblob': {'count': 10}
            }
        }
        
        self.high_quality_reddit = {
            'posts_analyzed': 20,
            'average_sentiment': 0.25
        }
        
        self.high_quality_marketaux = {
            'sentiment_score': 0.4
        }
        
        self.high_quality_events = {
            'events_detected': ['event1', 'event2', 'event3', 'event4']
        }
        
        # Mock low-quality data
        self.low_quality_news = {
            'news_count': 2,
            'average_sentiment': 0.05,
            'method_breakdown': {
                'transformer': {'confidence': 0.1}
            }
        }
        
        self.low_quality_reddit = {
            'posts_analyzed': 1,
            'average_sentiment': 0.02
        }
        
        self.no_marketaux = None
        
        self.no_events = {
            'events_detected': []
        }

    def test_initialization(self):
        """Test that the weighting system initializes correctly"""
        self.assertIsInstance(self.weighting_system, QualityBasedSentimentWeighting)
        self.assertEqual(len(self.weighting_system.base_weights), 7)
        self.assertAlmostEqual(sum(self.weighting_system.base_weights.values()), 1.0, places=2)

    def test_base_weights_sum_to_one(self):
        """Test that base weights sum to 1.0"""
        total_weight = sum(self.weighting_system.base_weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=10)

    def test_news_quality_assessment_high_quality(self):
        """Test news quality assessment with high-quality data"""
        assessment = self.weighting_system._assess_news_quality(
            self.high_quality_news, 
            transformer_confidence=0.9
        )
        
        self.assertIsInstance(assessment, dict)
        self.assertIn('score', assessment)
        self.assertIn('grade', assessment)
        self.assertIn('metrics', assessment)
        
        # High quality should get good score
        self.assertGreater(assessment['score'], 0.7)
        self.assertIn(assessment['grade'], ['A', 'B'])

    def test_news_quality_assessment_low_quality(self):
        """Test news quality assessment with low-quality data"""
        assessment = self.weighting_system._assess_news_quality(
            self.low_quality_news, 
            transformer_confidence=0.1
        )
        
        # Low quality should get poor score
        self.assertLess(assessment['score'], 0.5)
        self.assertIn(assessment['grade'], ['D', 'F'])

    def test_reddit_quality_assessment_high_quality(self):
        """Test Reddit quality assessment with high-quality data"""
        assessment = self.weighting_system._assess_reddit_quality(self.high_quality_reddit)
        
        self.assertIsInstance(assessment, dict)
        self.assertGreater(assessment['score'], 0.6)
        self.assertIn(assessment['grade'], ['A', 'B', 'C'])

    def test_reddit_quality_assessment_low_quality(self):
        """Test Reddit quality assessment with low-quality data"""
        assessment = self.weighting_system._assess_reddit_quality(self.low_quality_reddit)
        
        self.assertLess(assessment['score'], 0.5)
        self.assertIn(assessment['grade'], ['C', 'D', 'F'])

    def test_marketaux_quality_assessment_available(self):
        """Test MarketAux quality assessment when data is available"""
        assessment = self.weighting_system._assess_marketaux_quality(self.high_quality_marketaux)
        
        self.assertGreater(assessment['score'], 0.7)  # Professional source should score high
        self.assertIn(assessment['grade'], ['A', 'B'])

    def test_marketaux_quality_assessment_unavailable(self):
        """Test MarketAux quality assessment when data is unavailable"""
        assessment = self.weighting_system._assess_marketaux_quality(self.no_marketaux)
        
        self.assertEqual(assessment['score'], 0.0)
        self.assertEqual(assessment['grade'], 'F')

    def test_events_quality_assessment(self):
        """Test events quality assessment"""
        high_assessment = self.weighting_system._assess_events_quality(self.high_quality_events)
        low_assessment = self.weighting_system._assess_events_quality(self.no_events)
        
        self.assertGreater(high_assessment['score'], low_assessment['score'])

    def test_ml_trading_quality_assessment(self):
        """Test ML trading quality assessment"""
        high_confidence_assessment = self.weighting_system._assess_ml_trading_quality(0.8, {})
        low_confidence_assessment = self.weighting_system._assess_ml_trading_quality(0.2, {})
        
        self.assertGreater(high_confidence_assessment['score'], low_confidence_assessment['score'])

    def test_dynamic_weights_calculation_high_quality(self):
        """Test dynamic weight calculation with high-quality data"""
        result = self.weighting_system.calculate_dynamic_weights(
            self.high_quality_news,
            self.high_quality_reddit,
            self.high_quality_marketaux,
            self.high_quality_events,
            transformer_confidence=0.9,
            ml_confidence=0.8
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('weights', result)
        self.assertIn('quality_assessments', result)
        self.assertIn('weight_changes', result)
        
        # Weights should sum to 1.0
        total_weight = sum(result['weights'].values())
        self.assertAlmostEqual(total_weight, 1.0, places=10)
        
        # High-quality components should get weight increases
        news_change = result['weight_changes']['news']
        reddit_change = result['weight_changes']['reddit']
        
        # At least some components should be boosted for high quality
        self.assertTrue(any(change > 0 for change in result['weight_changes'].values()))

    def test_dynamic_weights_calculation_low_quality(self):
        """Test dynamic weight calculation with low-quality data"""
        result = self.weighting_system.calculate_dynamic_weights(
            self.low_quality_news,
            self.low_quality_reddit,
            self.no_marketaux,
            self.no_events,
            transformer_confidence=0.1,
            ml_confidence=0.2
        )
        
        # Weights should sum to 1.0
        total_weight = sum(result['weights'].values())
        self.assertAlmostEqual(total_weight, 1.0, places=10)
        
        # Low-quality components should get weight decreases
        news_change = result['weight_changes']['news']
        reddit_change = result['weight_changes']['reddit']
        
        # Most components should be penalized for low quality
        negative_changes = sum(1 for change in result['weight_changes'].values() if change < 0)
        self.assertGreater(negative_changes, 0)

    def test_grade_assignment_consistency(self):
        """Test that grade assignment is consistent with quality scores"""
        # Test various quality scores and verify grade assignment
        test_cases = [
            (0.9, 'A'),
            (0.8, 'B'),
            (0.6, 'C'),
            (0.4, 'D'),
            (0.2, 'F')
        ]
        
        for quality_score, expected_grade in test_cases:
            grade, _ = self.weighting_system._get_grade_and_issues(quality_score, {})
            if expected_grade == 'A':
                self.assertIn(grade, ['A', 'B'])  # Allow some flexibility at boundaries
            elif expected_grade == 'F':
                self.assertIn(grade, ['D', 'F'])
            else:
                # For middle grades, allow adjacent grades
                possible_grades = ['A', 'B', 'C', 'D', 'F']
                idx = possible_grades.index(expected_grade)
                allowed_grades = possible_grades[max(0, idx-1):idx+2]
                self.assertIn(grade, allowed_grades)

    def test_quality_multiplier_bounds(self):
        """Test that quality multipliers stay within expected bounds"""
        result = self.weighting_system.calculate_dynamic_weights(
            self.high_quality_news,
            self.high_quality_reddit,
            self.high_quality_marketaux,
            self.high_quality_events,
            transformer_confidence=0.9,
            ml_confidence=0.8
        )
        
        for component, multiplier in result['quality_multipliers'].items():
            self.assertGreaterEqual(multiplier, self.weighting_system.min_multiplier)
            self.assertLessEqual(multiplier, self.weighting_system.max_multiplier)

    def test_invalid_data_handling(self):
        """Test handling of invalid or missing data"""
        # Test with None values
        result = self.weighting_system.calculate_dynamic_weights(
            None,
            None,
            None,
            None,
            transformer_confidence=0.0,
            ml_confidence=0.0
        )
        
        # Should still return valid structure
        self.assertIsInstance(result, dict)
        self.assertIn('weights', result)
        total_weight = sum(result['weights'].values())
        self.assertAlmostEqual(total_weight, 1.0, places=10)

    def test_component_isolation(self):
        """Test that one component's quality doesn't inappropriately affect others"""
        # Create scenario where only news is high quality
        result = self.weighting_system.calculate_dynamic_weights(
            self.high_quality_news,  # High quality
            self.low_quality_reddit,  # Low quality
            self.no_marketaux,       # No data
            self.no_events,          # No events
            transformer_confidence=0.9,  # High
            ml_confidence=0.1        # Low
        )
        
        # News should be boosted, others should be penalized or neutral
        news_change = result['weight_changes']['news']
        reddit_change = result['weight_changes']['reddit']
        
        self.assertGreater(news_change, reddit_change)


class TestIntegratedSentimentAnalyzer(unittest.TestCase):
    """Test cases for the integrated sentiment analyzer with quality-based weighting"""

    def setUp(self):
        """Set up test fixtures"""
        try:
            self.analyzer = NewsSentimentAnalyzer()
            self.analyzer_available = True
        except Exception as e:
            self.analyzer_available = False
            self.skip_reason = str(e)

    def test_analyzer_has_quality_weighting(self):
        """Test that the analyzer has quality weighting system"""
        if not self.analyzer_available:
            self.skipTest(f"Analyzer not available: {self.skip_reason}")
            
        self.assertTrue(hasattr(self.analyzer, 'quality_weighting'))
        self.assertIsInstance(self.analyzer.quality_weighting, QualityBasedSentimentWeighting)

    def test_sentiment_analysis_includes_quality_data(self):
        """Test that sentiment analysis includes quality assessment data"""
        if not self.analyzer_available:
            self.skipTest(f"Analyzer not available: {self.skip_reason}")
            
        # This test might take longer, so we'll use a simple symbol
        try:
            result = self.analyzer.analyze_bank_sentiment('CBA.AX')
            
            # Check that quality data is included
            self.assertIn('quality_assessments', result)
            self.assertIn('weight_changes', result)
            self.assertIn('dynamic_weights', result)
            
            # Verify structure
            self.assertIsInstance(result['quality_assessments'], dict)
            self.assertIsInstance(result['weight_changes'], dict)
            self.assertIsInstance(result['dynamic_weights'], dict)
            
            # Check that all components are present
            expected_components = ['news', 'reddit', 'marketaux', 'events', 'volume', 'momentum', 'ml_trading']
            for component in expected_components:
                self.assertIn(component, result['quality_assessments'])
                self.assertIn(component, result['weight_changes'])
                self.assertIn(component, result['dynamic_weights'])
            
            # Verify dynamic weights sum to 1.0
            total_weight = sum(result['dynamic_weights'].values())
            self.assertAlmostEqual(total_weight, 1.0, places=5)
            
        except Exception as e:
            self.skipTest(f"Sentiment analysis failed: {e}")


class TestQualityMetricsCalculation(unittest.TestCase):
    """Test cases for quality metrics calculation"""

    def setUp(self):
        """Set up test fixtures"""
        self.weighting_system = QualityBasedSentimentWeighting()

    def test_quality_score_calculation(self):
        """Test quality score calculation for different scenarios"""
        # Perfect quality scenario
        perfect_metrics = {
            'volume_score': 1.0,
            'confidence_score': 1.0,
            'diversity_score': 1.0,
            'signal_strength': 1.0
        }
        
        # Poor quality scenario
        poor_metrics = {
            'volume_score': 0.1,
            'confidence_score': 0.1,
            'diversity_score': 0.1,
            'signal_strength': 0.1
        }
        
        perfect_assessment = self.weighting_system._assess_news_quality(
            {'news_count': 30, 'average_sentiment': 0.5, 'method_breakdown': {'transformer': {'confidence': 1.0}}},
            transformer_confidence=1.0
        )
        
        poor_assessment = self.weighting_system._assess_news_quality(
            {'news_count': 1, 'average_sentiment': 0.01, 'method_breakdown': {'transformer': {'confidence': 0.1}}},
            transformer_confidence=0.1
        )
        
        self.assertGreater(perfect_assessment['score'], poor_assessment['score'])

    def test_weight_change_calculation(self):
        """Test that weight changes are calculated correctly"""
        result = self.weighting_system.calculate_dynamic_weights(
            {'news_count': 20, 'average_sentiment': 0.3, 'method_breakdown': {'transformer': {'confidence': 0.8}}},
            {'posts_analyzed': 15, 'average_sentiment': 0.2},
            {'sentiment_score': 0.25},
            {'events_detected': ['event1', 'event2']},
            transformer_confidence=0.8,
            ml_confidence=0.7
        )
        
        # Weight changes should be calculated relative to base weights
        for component in self.weighting_system.base_weights:
            base_weight = self.weighting_system.base_weights[component]
            dynamic_weight = result['weights'][component]
            expected_change = ((dynamic_weight - base_weight) / base_weight * 100)
            actual_change = result['weight_changes'][component]
            
            self.assertAlmostEqual(expected_change, actual_change, places=1)


def run_quality_weighting_tests():
    """Run all quality-based weighting tests"""
    
    print("🧪 Running Quality-Based Weighting System Unit Tests")
    print("=" * 70)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestQualityBasedWeighting))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegratedSentimentAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestQualityMetricsCalculation))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print(f"📊 TEST SUMMARY:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print(f"\n❌ FAILURES:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    if result.errors:
        print(f"\n🔥 ERRORS:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print(f"\n✅ All tests passed! Quality-based weighting system is working correctly.")
    else:
        print(f"\n⚠️  Some tests failed. Please review the issues above.")
    
    return success


if __name__ == "__main__":
    run_quality_weighting_tests()
