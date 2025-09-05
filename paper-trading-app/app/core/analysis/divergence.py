"""
Divergence Detection System

Identifies banks that are performing significantly different from the sector average.
This helps identify potential outperformers and underperformers for trading opportunities.
"""

import logging
from typing import Dict, List, Tuple, Any
from statistics import mean, stdev
import math

logger = logging.getLogger(__name__)

class DivergenceDetector:
    """
    Detects divergence between individual bank sentiment and sector average.
    """
    
    def __init__(self, divergence_threshold: float = 0.15, confidence_threshold: float = 0.6):
        """
        Initialize the divergence detector.
        
        Args:
            divergence_threshold: Minimum difference to consider divergent
            confidence_threshold: Minimum confidence for divergence signals
        """
        self.divergence_threshold = divergence_threshold
        self.confidence_threshold = confidence_threshold
        logger.info(f"DivergenceDetector initialized with threshold={divergence_threshold}")
        
    def analyze_sector_divergence(self, bank_analyses: Dict[str, Dict]) -> Dict[str, Any]:
        """
        Analyze divergence across all banks in the sector.
        
        Args:
            bank_analyses: Dictionary of bank analyses {symbol: analysis_result}
            
        Returns:
            Dict containing divergence analysis results
        """
        logger.info("Analyzing sector-wide divergence patterns...")
        
        # Extract sentiment scores and confidences
        valid_analyses = {}
        sentiment_scores = []
        confidences = []
        
        for symbol, analysis in bank_analyses.items():
            sentiment = analysis.get('overall_sentiment', 0)
            confidence = analysis.get('confidence', 0)
            
            if confidence >= self.confidence_threshold:
                valid_analyses[symbol] = {
                    'sentiment': sentiment,
                    'confidence': confidence,
                    'signal': analysis.get('signal', 'HOLD')
                }
                sentiment_scores.append(sentiment)
                confidences.append(confidence)
        
        if len(sentiment_scores) < 2:
            logger.warning("Insufficient data for divergence analysis")
            return {
                'sector_average': 0.0,
                'sector_volatility': 0.0,
                'divergent_banks': {},
                'summary': 'Insufficient data for analysis'
            }
        
        # Calculate sector metrics
        sector_average = mean(sentiment_scores)
        sector_volatility = stdev(sentiment_scores) if len(sentiment_scores) > 1 else 0.0
        avg_confidence = mean(confidences)
        
        logger.info(f"Sector average sentiment: {sector_average:.3f}, volatility: {sector_volatility:.3f}")
        
        # Identify divergent banks
        divergent_banks = {}
        for symbol, data in valid_analyses.items():
            divergence = self._calculate_divergence(
                data['sentiment'], 
                sector_average, 
                sector_volatility,
                data['confidence']
            )
            
            if abs(divergence['divergence_score']) >= self.divergence_threshold:
                divergent_banks[symbol] = divergence
                logger.info(f"Divergent bank detected: {symbol} (score: {divergence['divergence_score']:+.3f})")
        
        # Generate summary
        summary = self._generate_divergence_summary(divergent_banks, sector_average)
        
        return {
            'sector_average': round(sector_average, 4),
            'sector_volatility': round(sector_volatility, 4),
            'average_confidence': round(avg_confidence, 4),
            'analyzed_banks': len(valid_analyses),
            'divergent_banks': divergent_banks,
            'most_bullish': self._find_extreme(divergent_banks, 'positive'),
            'most_bearish': self._find_extreme(divergent_banks, 'negative'),
            'summary': summary
        }
    
    def _calculate_divergence(self, sentiment: float, sector_avg: float, 
                            sector_vol: float, confidence: float) -> Dict[str, Any]:
        """
        Calculate divergence metrics for a single bank.
        
        Args:
            sentiment: Bank's sentiment score
            sector_avg: Sector average sentiment
            sector_vol: Sector volatility
            confidence: Analysis confidence
            
        Returns:
            Dict with divergence metrics
        """
        raw_divergence = sentiment - sector_avg
        
        # Normalize by sector volatility if available
        if sector_vol > 0:
            normalized_divergence = raw_divergence / sector_vol
        else:
            normalized_divergence = raw_divergence
        
        # Adjust for confidence
        adjusted_divergence = normalized_divergence * confidence
        
        # Determine divergence type
        if adjusted_divergence > self.divergence_threshold:
            divergence_type = 'positive_outlier'
            opportunity = 'outperformer'
        elif adjusted_divergence < -self.divergence_threshold:
            divergence_type = 'negative_outlier'
            opportunity = 'underperformer'
        else:
            divergence_type = 'normal'
            opportunity = 'in_line'
        
        # Calculate significance
        significance = min(abs(adjusted_divergence) / self.divergence_threshold, 3.0)
        
        return {
            'divergence_score': round(adjusted_divergence, 4),
            'raw_divergence': round(raw_divergence, 4),
            'normalized_divergence': round(normalized_divergence, 4),
            'divergence_type': divergence_type,
            'opportunity': opportunity,
            'significance': round(significance, 2),
            'confidence': round(confidence, 4)
        }
    
    def _find_extreme(self, divergent_banks: Dict, direction: str) -> Tuple[str, Dict]:
        """
        Find the most extreme divergent bank in the specified direction.
        
        Args:
            divergent_banks: Dictionary of divergent banks
            direction: 'positive' or 'negative'
            
        Returns:
            Tuple of (symbol, divergence_data) or ('N/A', {})
        """
        if not divergent_banks:
            return ('N/A', {})
        
        if direction == 'positive':
            extreme_bank = max(
                divergent_banks.items(),
                key=lambda x: x[1]['divergence_score'],
                default=('N/A', {})
            )
            if extreme_bank[1].get('divergence_score', 0) > 0:
                return extreme_bank
        else:  # negative
            extreme_bank = min(
                divergent_banks.items(),
                key=lambda x: x[1]['divergence_score'],
                default=('N/A', {})
            )
            if extreme_bank[1].get('divergence_score', 0) < 0:
                return extreme_bank
        
        return ('N/A', {})
    
    def _generate_divergence_summary(self, divergent_banks: Dict, sector_avg: float) -> str:
        """
        Generate a human-readable summary of divergence analysis.
        
        Args:
            divergent_banks: Dictionary of divergent banks
            sector_avg: Sector average sentiment
            
        Returns:
            Summary string
        """
        if not divergent_banks:
            return f"No significant divergence detected. Sector average: {sector_avg:+.3f}"
        
        positive_count = sum(1 for data in divergent_banks.values() 
                           if data['divergence_score'] > 0)
        negative_count = len(divergent_banks) - positive_count
        
        summary_parts = [f"Sector average: {sector_avg:+.3f}."]
        
        if positive_count > 0:
            summary_parts.append(f"{positive_count} bank(s) showing positive divergence.")
        
        if negative_count > 0:
            summary_parts.append(f"{negative_count} bank(s) showing negative divergence.")
        
        # Add most significant divergence
        most_significant = max(
            divergent_banks.items(),
            key=lambda x: abs(x[1]['divergence_score']),
            default=('N/A', {})
        )
        
        if most_significant[0] != 'N/A':
            bank, data = most_significant
            score = data['divergence_score']
            summary_parts.append(
                f"Most significant: {bank} ({score:+.3f}, {data['opportunity']})."
            )
        
        return " ".join(summary_parts)
    
    def generate_trading_signals(self, divergence_analysis: Dict) -> List[Dict[str, Any]]:
        """
        Generate trading signals based on divergence analysis.
        
        Args:
            divergence_analysis: Results from analyze_sector_divergence
            
        Returns:
            List of trading signal dictionaries
        """
        signals = []
        divergent_banks = divergence_analysis.get('divergent_banks', {})
        
        for symbol, data in divergent_banks.items():
            if data['significance'] >= 1.5:  # High significance threshold
                
                if data['divergence_type'] == 'positive_outlier':
                    signal_type = 'BUY'
                    reasoning = f"Positive divergence vs sector (score: {data['divergence_score']:+.3f})"
                elif data['divergence_type'] == 'negative_outlier':
                    signal_type = 'SELL'
                    reasoning = f"Negative divergence vs sector (score: {data['divergence_score']:+.3f})"
                else:
                    continue
                
                signals.append({
                    'symbol': symbol,
                    'signal': signal_type,
                    'divergence_score': data['divergence_score'],
                    'significance': data['significance'],
                    'confidence': data['confidence'],
                    'reasoning': reasoning,
                    'opportunity_type': data['opportunity']
                })
        
        # Sort by significance
        signals.sort(key=lambda x: x['significance'], reverse=True)
        
        logger.info(f"Generated {len(signals)} divergence-based trading signals")
        return signals

if __name__ == '__main__':
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Mock data for testing
    mock_analyses = {
        'CBA.AX': {'overall_sentiment': 0.3, 'confidence': 0.8, 'signal': 'BUY'},
        'WBC.AX': {'overall_sentiment': 0.1, 'confidence': 0.7, 'signal': 'HOLD'},
        'ANZ.AX': {'overall_sentiment': -0.2, 'confidence': 0.9, 'signal': 'SELL'},
        'NAB.AX': {'overall_sentiment': 0.05, 'confidence': 0.6, 'signal': 'HOLD'},
        'MQG.AX': {'overall_sentiment': 0.4, 'confidence': 0.85, 'signal': 'BUY'},
    }
    
    detector = DivergenceDetector()
    result = detector.analyze_sector_divergence(mock_analyses)
    
    import json
    print(json.dumps(result, indent=2))
    
    signals = detector.generate_trading_signals(result)
    print("\nTrading Signals:")
    for signal in signals:
        print(f"  {signal['symbol']}: {signal['signal']} (Significance: {signal['significance']:.2f})")
