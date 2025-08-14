#!/usr/bin/env python3
"""
MarketAux API Optimization Strategy
Handles 3-article limit across multiple banks efficiently
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

class MarketAuxOptimizer:
    """
    Optimize MarketAux API usage for multiple banks with 3-article limit
    Strategies:
    1. Sequential bank requests (3 articles per bank)
    2. Time-staggered requests to respect rate limits
    3. Priority-based bank ordering
    4. Intelligent caching
    """
    
    def __init__(self, api_client):
        self.api_client = api_client
        self.request_delay = 1.0  # Seconds between requests
        self.priority_banks = ['CBA', 'ANZ', 'WBC', 'NAB']  # Big 4 first
        self.secondary_banks = ['MQG', 'SUN', 'QBE']
        
    def get_optimized_sentiment_data(self, banks: List[str]) -> Dict[str, Any]:
        """
        Fetch sentiment data for multiple banks efficiently
        
        Strategy: Make separate API calls for each bank to get 3 articles each
        instead of sharing 3 articles across all banks
        """
        results = {}
        
        # Prioritize banks - Big 4 first
        prioritized_banks = self._prioritize_banks(banks)
        
        logger.info(f"Fetching sentiment for {len(prioritized_banks)} banks sequentially...")
        
        for i, bank in enumerate(prioritized_banks):
            try:
                logger.info(f"Fetching news for {bank} ({i+1}/{len(prioritized_banks)})")
                
                # Make individual request for this bank (gets 3 articles for this bank)
                bank_sentiment = self.api_client.get_sentiment_analysis(
                    symbols=[bank],
                    strategy="individual_bank",
                    use_cache=True
                )
                
                if bank_sentiment and len(bank_sentiment) > 0:
                    results[bank] = bank_sentiment[0]
                    logger.info(f"✅ Got sentiment data for {bank}")
                else:
                    logger.warning(f"❌ No sentiment data for {bank}")
                    results[bank] = self._create_fallback_sentiment(bank)
                
                # Rate limiting - delay between requests
                if i < len(prioritized_banks) - 1:  # Don't delay after last request
                    time.sleep(self.request_delay)
                    
            except Exception as e:
                logger.error(f"Error fetching sentiment for {bank}: {e}")
                results[bank] = self._create_fallback_sentiment(bank)
        
        return results
    
    def _prioritize_banks(self, banks: List[str]) -> List[str]:
        """
        Order banks by priority - Big 4 first, then others
        """
        prioritized = []
        
        # Add priority banks first (if in the request)
        for bank in self.priority_banks:
            bank_variants = [bank, f"{bank}.AX"]
            for variant in bank_variants:
                if variant in banks and variant not in prioritized:
                    prioritized.append(variant)
        
        # Add remaining banks
        for bank in banks:
            if bank not in prioritized:
                prioritized.append(bank)
                
        return prioritized
    
    def _create_fallback_sentiment(self, bank: str) -> Dict[str, Any]:
        """
        Create fallback sentiment data when API fails
        """
        return {
            'symbol': bank,
            'sentiment_score': 0.0,
            'confidence': 0.3,
            'news_count': 0,
            'sources': [],
            'articles_analyzed': 0,
            'timestamp': datetime.now().isoformat(),
            'method_breakdown': {
                'fallback': {
                    'sentiment': 0.0,
                    'confidence': 0.3,
                    'article_count': 0
                }
            },
            'quality_assessment': {
                'overall_grade': 'F',
                'reliability_score': 0.0,
                'coverage_score': 0.0
            }
        }

class SmartBatchProcessor:
    """
    Alternative strategy: Batch processing with intelligent grouping
    """
    
    def __init__(self, api_client, max_symbols_per_request: int = 2):
        self.api_client = api_client
        self.max_symbols_per_request = max_symbols_per_request
    
    def process_banks_in_batches(self, banks: List[str]) -> Dict[str, Any]:
        """
        Process banks in small batches to maximize article coverage
        
        With 3-article limit:
        - Batch 1: CBA, ANZ (3 articles shared)
        - Batch 2: WBC, NAB (3 articles shared) 
        - Batch 3: MQG, SUN (3 articles shared)
        - Batch 4: QBE (3 articles)
        
        Better than all 7 banks sharing 3 articles total
        """
        results = {}
        
        # Create batches
        batches = self._create_batches(banks, self.max_symbols_per_request)
        
        logger.info(f"Processing {len(banks)} banks in {len(batches)} batches")
        
        for i, batch in enumerate(batches):
            try:
                logger.info(f"Processing batch {i+1}/{len(batches)}: {batch}")
                
                batch_results = self.api_client.get_sentiment_analysis(
                    symbols=batch,
                    strategy=f"batch_{i+1}",
                    use_cache=True
                )
                
                if batch_results:
                    for sentiment_data in batch_results:
                        symbol = sentiment_data.symbol
                        results[symbol] = sentiment_data
                        logger.info(f"✅ Processed {symbol}")
                else:
                    logger.warning(f"❌ No data for batch: {batch}")
                    for symbol in batch:
                        results[symbol] = self._create_fallback_sentiment(symbol)
                
                # Rate limiting between batches
                if i < len(batches) - 1:
                    time.sleep(2.0)  # Longer delay between batches
                    
            except Exception as e:
                logger.error(f"Error processing batch {batch}: {e}")
                for symbol in batch:
                    results[symbol] = self._create_fallback_sentiment(symbol)
        
        return results
    
    def _create_batches(self, items: List[str], batch_size: int) -> List[List[str]]:
        """Create batches from list of items"""
        return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]
    
    def _create_fallback_sentiment(self, bank: str) -> Any:
        """Create fallback sentiment data"""
        # Implementation would match MarketAuxOptimizer._create_fallback_sentiment
        pass

# Integration functions for existing codebase
def optimize_marketaux_requests(api_client, banks: List[str], strategy: str = "individual") -> Dict[str, Any]:
    """
    Drop-in replacement for current MarketAux usage
    
    Args:
        api_client: MarketAux API client
        banks: List of bank symbols
        strategy: "individual" or "batch"
    
    Returns:
        Dict mapping bank symbols to sentiment data
    """
    
    if strategy == "individual":
        optimizer = MarketAuxOptimizer(api_client)
        return optimizer.get_optimized_sentiment_data(banks)
    elif strategy == "batch":
        processor = SmartBatchProcessor(api_client, max_symbols_per_request=2)
        return processor.process_banks_in_batches(banks)
    else:
        raise ValueError(f"Unknown strategy: {strategy}")

if __name__ == "__main__":
    # Simulation test
    print("🔧 MarketAux Optimization Strategy Test")
    print("=" * 50)
    
    test_banks = ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX']
    
    print("\n📊 Current Problem:")
    print(f"Banks to analyze: {len(test_banks)}")
    print(f"MarketAux limit: 3 articles TOTAL")
    print(f"Articles per bank: {3/len(test_banks):.1f} (terrible coverage!)")
    
    print("\n✅ Individual Bank Strategy:")
    print(f"Requests needed: {len(test_banks)}")
    print(f"Articles per bank: 3 (excellent coverage!)")
    print(f"Total articles: {len(test_banks) * 3}")
    print(f"Time required: ~{len(test_banks) * 1.5:.1f} seconds")
    
    print("\n🔄 Batch Strategy (2 banks per request):")
    batches = [test_banks[i:i+2] for i in range(0, len(test_banks), 2)]
    print(f"Batches needed: {len(batches)}")
    print(f"Articles per batch: 3")
    print(f"Banks per batch: 2")
    print(f"Articles per bank: ~1.5 (decent coverage)")
    print(f"Total articles: {len(batches) * 3}")
    print(f"Time required: ~{len(batches) * 2.5:.1f} seconds")
    
    print("\n🎯 Recommendation: Individual Bank Strategy")
    print("- Maximum article coverage per bank")
    print("- Better sentiment quality")
    print("- More reliable predictions")
    print("- Worth the extra API calls")
