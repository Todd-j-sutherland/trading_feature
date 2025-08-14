"""
Enhanced Confidence Metrics Module
Provides comprehensive confidence analysis for trading system components
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple

DATABASE_PATH = "data/trading_unified.db"

def compute_enhanced_confidence_metrics() -> Dict[str, Any]:
    """
    Compute comprehensive confidence metrics for all system components
    Returns detailed confidence breakdown for feature creation, outcome recording, 
    training process, and overall integration
    """
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        
        # Feature Creation Confidence
        feature_confidence = compute_feature_creation_confidence(conn)
        
        # Outcome Recording Confidence  
        outcome_confidence = compute_outcome_recording_confidence(conn)
        
        # Training Process Confidence
        training_confidence = compute_training_process_confidence(conn)
        
        # Overall Integration Confidence
        integration_confidence = compute_overall_integration_confidence(
            feature_confidence, outcome_confidence, training_confidence, conn
        )
        
        conn.close()
        
        return {
            'feature_creation': feature_confidence,
            'outcome_recording': outcome_confidence,
            'training_process': training_confidence,
            'overall_integration': integration_confidence,
            'last_updated': datetime.now().isoformat(),
            'component_summary': {
                'total_features': feature_confidence.get('total_records', 0),
                'completed_outcomes': outcome_confidence.get('total_outcomes', 0),
                'training_samples': training_confidence.get('training_samples', 0),
                'overall_score': integration_confidence.get('confidence', 0.0)
            }
        }
        
    except Exception as e:
        print(f"Error computing enhanced confidence metrics: {e}")
        return create_fallback_confidence_metrics()


def compute_feature_creation_confidence(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Analyze confidence in feature creation process"""
    
    try:
        # Get feature creation statistics (Fixed for SQLite compatibility)
        query = """
        SELECT 
            COUNT(*) as total_features,
            COUNT(DISTINCT symbol) as symbols_covered,
            AVG(CASE WHEN confidence IS NOT NULL THEN 1 ELSE 0 END) as confidence_coverage,
            AVG(confidence) as avg_confidence,
            COUNT(CASE WHEN timestamp >= datetime('now', '-7 days') THEN 1 END) as recent_features,
            MIN(timestamp) as first_feature,
            MAX(timestamp) as latest_feature
        FROM enhanced_features
        WHERE timestamp >= datetime('now', '-30 days')
        """
        
        result = pd.read_sql_query(query, conn).iloc[0]
        
        # Calculate quality metrics
        completeness = min(1.0, result['total_features'] / 100.0)  # Target: 100+ features/month
        coverage = min(1.0, result['symbols_covered'] / 7.0)  # Target: 7 symbols
        confidence_quality = result['confidence_coverage'] if result['confidence_coverage'] else 0.0
        
        # Temporal consistency (steady feature creation)
        temporal_consistency = min(1.0, result['recent_features'] / 50.0)  # Target: 50+ recent
        
        # Overall quality score  
        quality_score = np.mean([completeness, coverage, confidence_quality, temporal_consistency])
        
        # Confidence based on quality metrics
        if quality_score >= 0.8:
            confidence = 0.9
        elif quality_score >= 0.6:
            confidence = 0.75
        elif quality_score >= 0.4:
            confidence = 0.6
        else:
            confidence = 0.4
            
        return {
            'confidence': confidence,
            'quality_score': quality_score,
            'total_records': int(result['total_features']),
            'symbols_covered': int(result['symbols_covered']),
            'confidence_coverage': float(result['confidence_coverage']),
            'avg_confidence': float(result['avg_confidence']) if result['avg_confidence'] else 0.0,
            'recent_activity': int(result['recent_features']),
            'metrics': {
                'completeness': completeness,
                'symbol_coverage': coverage,
                'confidence_quality': confidence_quality,
                'temporal_consistency': temporal_consistency
            }
        }
        
    except Exception as e:
        print(f"Error in feature creation confidence: {e}")
        return {'confidence': 0.5, 'quality_score': 0.5, 'total_records': 0, 'error': str(e)}


def compute_outcome_recording_confidence(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Analyze confidence in outcome recording process"""
    
    try:
        # Get outcome recording statistics (Fixed for SQLite compatibility)
        query = """
        SELECT 
            COUNT(*) as total_outcomes,
            AVG(CASE WHEN return_pct IS NOT NULL THEN 1 ELSE 0 END) as return_coverage,
            AVG(CASE WHEN optimal_action IS NOT NULL THEN 1 ELSE 0 END) as action_coverage,
            AVG(return_pct) as avg_return,
            COUNT(CASE WHEN return_pct > 0 THEN 1 END) * 1.0 / COUNT(*) as win_rate,
            COUNT(CASE WHEN ABS(return_pct) < 0.1 THEN 1 END) * 1.0 / COUNT(*) as reasonable_returns,
            MIN(created_at) as first_outcome,
            MAX(created_at) as latest_outcome
        FROM enhanced_outcomes
        WHERE created_at >= datetime('now', '-30 days')
        """
        
        result = pd.read_sql_query(query, conn).iloc[0]
        
        # Calculate accuracy metrics
        data_completeness = (result['return_coverage'] + result['action_coverage']) / 2.0
        return_reasonableness = result['reasonable_returns']  # Should be high for reasonable returns
        outcome_consistency = 1.0 if 0.4 <= result['win_rate'] <= 0.8 else 0.6  # Reasonable win rate range
        
        # Volume adequacy  
        volume_adequacy = min(1.0, result['total_outcomes'] / 50.0)  # Target: 50+ outcomes/month
        
        # Overall accuracy score
        accuracy_rate = np.mean([data_completeness, return_reasonableness, outcome_consistency, volume_adequacy])
        
        # Confidence based on accuracy
        if accuracy_rate >= 0.8:
            confidence = 0.9
        elif accuracy_rate >= 0.6:
            confidence = 0.75
        elif accuracy_rate >= 0.4:
            confidence = 0.6
        else:
            confidence = 0.4
            
        return {
            'confidence': confidence,
            'accuracy_rate': accuracy_rate,
            'total_outcomes': int(result['total_outcomes']),
            'return_coverage': float(result['return_coverage']),
            'action_coverage': float(result['action_coverage']),
            'avg_return': float(result['avg_return']) if result['avg_return'] else 0.0,
            'win_rate': float(result['win_rate']),
            'metrics': {
                'data_completeness': data_completeness,
                'return_reasonableness': return_reasonableness,
                'outcome_consistency': outcome_consistency,
                'volume_adequacy': volume_adequacy
            }
        }
        
    except Exception as e:
        print(f"Error in outcome recording confidence: {e}")
        return {'confidence': 0.5, 'accuracy_rate': 0.5, 'total_outcomes': 0, 'error': str(e)}


def compute_training_process_confidence(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Analyze confidence in ML training process"""
    
    try:
        # Get training statistics from enhanced_features and enhanced_outcomes (since ml_training_results doesn't exist)
        query = """
        SELECT 
            COUNT(DISTINCT DATE(ef.timestamp)) as total_training_days,
            COUNT(*) as total_features_created,
            COUNT(eo.id) as total_outcomes,
            AVG(CASE WHEN eo.return_pct IS NOT NULL THEN 1.0 ELSE 0.0 END) as outcome_rate,
            COUNT(CASE WHEN eo.return_pct > 0 THEN 1 END) * 1.0 / COUNT(eo.id) as training_win_rate,
            MAX(ef.timestamp) as last_feature_creation,
            COUNT(DISTINCT ef.symbol) as symbols_trained
        FROM enhanced_features ef
        LEFT JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
        WHERE ef.timestamp >= datetime('now', '-30 days')
        """
        
        result = pd.read_sql_query(query, conn).iloc[0]
        
        # Calculate model stability and performance metrics
        model_performance = result['training_win_rate'] if result['training_win_rate'] else 0.0
        sample_adequacy = min(1.0, result['total_features_created'] / 100.0) if result['total_features_created'] else 0.0
        outcome_adequacy = result['outcome_rate'] if result['outcome_rate'] else 0.0
        training_frequency = min(1.0, result['total_training_days'] / 20.0)  # Target: 20+ training days/month
        
        # Model stability based on consistent training
        model_stability = min(1.0, result['symbols_trained'] / 7.0) if result['symbols_trained'] else 0.0  # All 7 symbols
        
        # Overall confidence score
        performance_score = np.mean([model_performance, sample_adequacy, outcome_adequacy, training_frequency, model_stability])
        
        # Confidence based on performance
        if performance_score >= 0.7:
            confidence = 0.85
        elif performance_score >= 0.5:
            confidence = 0.7
        elif performance_score >= 0.3:
            confidence = 0.55
        else:
            confidence = 0.3
            
        return {
            'confidence': confidence,
            'performance_score': performance_score,
            'training_samples': int(result['total_features_created']) if result['total_features_created'] else 0,
            'model_performance': model_performance,
            'model_stability': model_stability,
            'training_frequency': float(result['total_training_days']),
            'last_training': result['last_feature_creation'],
            'metrics': {
                'model_performance': model_performance,
                'sample_adequacy': sample_adequacy,
                'outcome_adequacy': outcome_adequacy,
                'training_frequency': training_frequency,
                'stability': model_stability
            }
        }
        
    except Exception as e:
        print(f"Error in training process confidence: {e}")
        return {'confidence': 0.5, 'performance_score': 0.5, 'training_samples': 0, 'error': str(e)}


def compute_overall_integration_confidence(
    feature_conf: Dict, outcome_conf: Dict, training_conf: Dict, conn: sqlite3.Connection
) -> Dict[str, Any]:
    """Compute overall system integration confidence"""
    
    try:
        # Component weights
        weights = {
            'feature_creation': 0.3,
            'outcome_recording': 0.4,  # Most critical for trading decisions
            'training_process': 0.3
        }
        
        # Get individual confidences
        feature_confidence = feature_conf.get('confidence', 0.0)
        outcome_confidence = outcome_conf.get('confidence', 0.0)
        training_confidence = training_conf.get('confidence', 0.0)
        
        # Weighted overall confidence
        overall_confidence = (
            feature_confidence * weights['feature_creation'] +
            outcome_confidence * weights['outcome_recording'] +
            training_confidence * weights['training_process']
        )
        
        # Integration checks
        data_flow_integrity = check_data_flow_integrity(conn)
        system_coherence = check_system_coherence(feature_conf, outcome_conf, training_conf)
        
        # Apply integration penalties/bonuses
        integration_factor = (data_flow_integrity + system_coherence) / 2.0
        final_confidence = overall_confidence * integration_factor
        
        # Confidence levels
        if final_confidence >= 0.8:
            status = "EXCELLENT"
        elif final_confidence >= 0.65:
            status = "GOOD"
        elif final_confidence >= 0.5:
            status = "ADEQUATE"
        else:
            status = "NEEDS_IMPROVEMENT"
            
        return {
            'confidence': final_confidence,
            'status': status,
            'component_scores': {
                'feature_creation': feature_confidence,
                'outcome_recording': outcome_confidence,
                'training_process': training_confidence
            },
            'integration_metrics': {
                'data_flow_integrity': data_flow_integrity,
                'system_coherence': system_coherence,
                'integration_factor': integration_factor
            },
            'recommendations': generate_confidence_recommendations(
                feature_confidence, outcome_confidence, training_confidence, final_confidence
            )
        }
        
    except Exception as e:
        print(f"Error in overall integration confidence: {e}")
        return {'confidence': 0.5, 'status': 'ERROR', 'error': str(e)}


def check_data_flow_integrity(conn: sqlite3.Connection) -> float:
    """Check integrity of data flow between components"""
    
    try:
        # Check feature -> outcome linking
        query = """
        SELECT 
            COUNT(DISTINCT ef.id) as total_features,
            COUNT(DISTINCT eo.feature_id) as features_with_outcomes,
            COUNT(eo.id) as total_outcomes
        FROM enhanced_features ef
        LEFT JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
        WHERE ef.timestamp >= datetime('now', '-7 days')
        """
        
        result = pd.read_sql_query(query, conn).iloc[0]
        
        if result['total_features'] == 0:
            return 0.5
            
        # Calculate linking ratio
        linking_ratio = result['features_with_outcomes'] / result['total_features']
        
        # Good data flow should have reasonable outcome coverage
        if linking_ratio >= 0.3:  # 30%+ features should have outcomes
            return 0.9
        elif linking_ratio >= 0.2:
            return 0.7
        elif linking_ratio >= 0.1:
            return 0.5
        else:
            return 0.3
            
    except Exception as e:
        print(f"Error checking data flow integrity: {e}")
        return 0.5


def check_system_coherence(feature_conf: Dict, outcome_conf: Dict, training_conf: Dict) -> float:
    """Check coherence between system components"""
    
    try:
        # Check if components have similar confidence levels (coherent system)
        confidences = [
            feature_conf.get('confidence', 0.0),
            outcome_conf.get('confidence', 0.0), 
            training_conf.get('confidence', 0.0)
        ]
        
        # Calculate variance in confidence levels
        conf_variance = np.var(confidences)
        
        # Lower variance = higher coherence
        if conf_variance <= 0.02:
            coherence = 0.95
        elif conf_variance <= 0.05:
            coherence = 0.85
        elif conf_variance <= 0.1:
            coherence = 0.7
        else:
            coherence = 0.5
            
        return coherence
        
    except Exception as e:
        print(f"Error checking system coherence: {e}")
        return 0.5


def generate_confidence_recommendations(
    feature_conf: float, outcome_conf: float, training_conf: float, overall_conf: float
) -> List[str]:
    """Generate recommendations to improve confidence"""
    
    recommendations = []
    
    if overall_conf < 0.6:
        recommendations.append("🔴 Critical: Overall system confidence below 60%")
    
    if feature_conf < 0.6:
        recommendations.append("📊 Improve feature creation: Add more data sources or improve data quality")
    
    if outcome_conf < 0.6:
        recommendations.append("📈 Improve outcome recording: Validate return calculations and action assignments")
        
    if training_conf < 0.6:
        recommendations.append("🤖 Improve ML training: Increase training frequency or improve model parameters")
        
    # Positive recommendations
    if overall_conf >= 0.8:
        recommendations.append("✅ Excellent system confidence - continue current practices")
    elif overall_conf >= 0.65:
        recommendations.append("👍 Good system confidence - minor optimizations suggested")
    
    return recommendations


def create_fallback_confidence_metrics() -> Dict[str, Any]:
    """Create fallback metrics when computation fails"""
    
    return {
        'feature_creation': {'confidence': 0.5, 'quality_score': 0.5, 'total_records': 0},
        'outcome_recording': {'confidence': 0.5, 'accuracy_rate': 0.5, 'total_outcomes': 0},
        'training_process': {'confidence': 0.5, 'performance_score': 0.5, 'training_samples': 0},
        'overall_integration': {
            'confidence': 0.5,
            'status': 'UNKNOWN',
            'component_scores': {'feature_creation': 0.5, 'outcome_recording': 0.5, 'training_process': 0.5},
            'recommendations': ['⚠️ Unable to compute confidence metrics - check system status']
        },
        'last_updated': datetime.now().isoformat(),
        'component_summary': {'total_features': 0, 'completed_outcomes': 0, 'training_samples': 0, 'overall_score': 0.5},
        'error': 'Fallback metrics due to computation error'
    }


if __name__ == "__main__":
    # Test the confidence metrics
    metrics = compute_enhanced_confidence_metrics()
    
    print("=== Enhanced Confidence Metrics ===")
    for component, data in metrics.items():
        if isinstance(data, dict) and 'confidence' in data:
            print(f"{component}: {data['confidence']:.1%}")
    
    print(f"\nOverall Status: {metrics['overall_integration']['status']}")
    print("\nRecommendations:")
    for rec in metrics['overall_integration']['recommendations']:
        print(f"  - {rec}")
