"""
Two-Stage Sentiment Analysis System
Optimized for memory-constrained environments with quality retention

Stage 1: Basic sentiment analysis (TextBlob + VADER) - Low memory ~100MB
Stage 2: FinBERT enhancement (Financial domain) - Moderate memory ~800MB

This allows running basic analysis continuously while adding FinBERT insights 
when memory permits or during dedicated analysis windows.
"""

import os
import gc
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TwoStageAnalyzer:
    """
    Memory-optimized sentiment analyzer with two operational stages:
    
    Stage 1 (Basic): TextBlob + VADER - Always available, low memory
    Stage 2 (Enhanced): + FinBERT - Load on demand for financial accuracy
    """
    
    def __init__(self, cache_dir: str = "data/sentiment_cache"):
        self.cache_dir = cache_dir
        self.basic_analyzer = None
        self.finbert_analyzer = None
        self.stage1_results = {}
        self.stage2_results = {}
        
        # Ensure cache directory exists
        os.makedirs(cache_dir, exist_ok=True)
        
        logger.info("TwoStageAnalyzer initialized - Memory-optimized sentiment analysis")
    
    def run_stage1_analysis(self, symbols: List[str], force_reload: bool = False) -> Dict[str, Any]:
        """
        Stage 1: Basic sentiment analysis with TextBlob + VADER
        Memory usage: ~100MB, Fast execution, Good baseline quality
        """
        logger.info(f"🕐 Stage 1: Running basic sentiment analysis for {len(symbols)} symbols...")
        
        try:
            # Load basic analyzer with transformers disabled
            os.environ['SKIP_TRANSFORMERS'] = '1'
            
            from app.core.sentiment.news_analyzer import NewsSentimentAnalyzer
            
            if self.basic_analyzer is None or force_reload:
                self.basic_analyzer = NewsSentimentAnalyzer()
                logger.info("Basic analyzer loaded successfully")
            
            results = {}
            
            for symbol in symbols:
                try:
                    # Use the bank sentiment analysis method
                    result = self.basic_analyzer.analyze_bank_sentiment(symbol)
                    
                    # Extract key metrics for stage 1
                    stage1_data = {
                        'symbol': symbol,
                        'timestamp': datetime.now().isoformat(),
                        'stage': 1,
                        'overall_sentiment': result.get('overall_sentiment', 0),
                        'confidence': result.get('confidence', 0),
                        'news_count': result.get('news_count', 0),
                        'sentiment_components': result.get('sentiment_components', {}),
                        'recent_headlines': result.get('recent_headlines', [])[:3],  # Top 3 only
                        'method': 'textblob_vader'
                    }
                    
                    results[symbol] = stage1_data
                    self.stage1_results[symbol] = stage1_data
                    
                    logger.info(f"   ✅ {symbol}: Stage 1 sentiment {stage1_data['overall_sentiment']:.3f}")
                    
                except Exception as e:
                    logger.error(f"   ❌ Stage 1 error for {symbol}: {e}")
                    results[symbol] = self._create_fallback_result(symbol, 1)
            
            # Save stage 1 results to cache
            self._save_stage_results(results, stage=1)
            
            logger.info(f"✅ Stage 1 complete: {len(results)} symbols analyzed")
            return results
            
        except Exception as e:
            logger.error(f"Stage 1 analysis failed: {e}")
            return {}
        
        finally:
            # Clean up environment
            os.environ.pop('SKIP_TRANSFORMERS', None)
    
    def run_stage2_analysis(self, symbols: List[str], stage1_results: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Stage 2: Enhanced analysis with FinBERT for financial domain accuracy
        Memory usage: ~800MB, Slower execution, High financial sentiment quality
        """
        logger.info(f"🕕 Stage 2: Running FinBERT-enhanced analysis for {len(symbols)} symbols...")
        
        # Free up memory by clearing stage 1 analyzer
        if self.basic_analyzer is not None:
            del self.basic_analyzer
            self.basic_analyzer = None
            gc.collect()
            logger.info("Cleared basic analyzer to free memory")
        
        try:
            # Load FinBERT-only analyzer
            os.environ['FINBERT_ONLY'] = '1'
            
            # Force reload to pick up new environment
            import importlib
            import app.core.sentiment.news_analyzer
            importlib.reload(app.core.sentiment.news_analyzer)
            from app.core.sentiment.news_analyzer import NewsSentimentAnalyzer
            
            self.finbert_analyzer = NewsSentimentAnalyzer()
            
            if not self.finbert_analyzer.transformer_pipelines:
                logger.warning("FinBERT not available, falling back to basic methods")
                return self._fallback_to_stage1(symbols, stage1_results)
            
            logger.info(f"FinBERT loaded: {list(self.finbert_analyzer.transformer_pipelines.keys())}")
            
            results = {}
            
            for symbol in symbols:
                try:
                    # Get enhanced analysis with FinBERT
                    result = self.finbert_analyzer.analyze_bank_sentiment(symbol)
                    
                    # Combine with stage 1 data if available
                    stage1_data = stage1_results.get(symbol, {}) if stage1_results else self.stage1_results.get(symbol, {})
                    
                    # Create enhanced stage 2 result
                    stage2_data = {
                        'symbol': symbol,
                        'timestamp': datetime.now().isoformat(),
                        'stage': 2,
                        'overall_sentiment': result.get('overall_sentiment', 0),
                        'confidence': result.get('confidence', 0),
                        'news_count': result.get('news_count', 0),
                        'sentiment_components': result.get('sentiment_components', {}),
                        'recent_headlines': result.get('recent_headlines', [])[:5],  # More headlines
                        'significant_events': result.get('significant_events', {}),
                        'method': 'finbert_enhanced',
                        'stage1_sentiment': stage1_data.get('overall_sentiment', 0),
                        'sentiment_improvement': result.get('overall_sentiment', 0) - stage1_data.get('overall_sentiment', 0)
                    }
                    
                    results[symbol] = stage2_data
                    self.stage2_results[symbol] = stage2_data
                    
                    logger.info(f"   ✅ {symbol}: Stage 2 sentiment {stage2_data['overall_sentiment']:.3f} "
                              f"(improvement: {stage2_data['sentiment_improvement']:+.3f})")
                    
                except Exception as e:
                    logger.error(f"   ❌ Stage 2 error for {symbol}: {e}")
                    results[symbol] = self._create_fallback_result(symbol, 2)
            
            # Save stage 2 results to cache
            self._save_stage_results(results, stage=2)
            
            logger.info(f"✅ Stage 2 complete: {len(results)} symbols analyzed with FinBERT")
            return results
            
        except Exception as e:
            logger.error(f"Stage 2 analysis failed: {e}")
            return self._fallback_to_stage1(symbols, stage1_results)
        
        finally:
            # Clean up FinBERT to free memory
            if self.finbert_analyzer is not None:
                del self.finbert_analyzer
                self.finbert_analyzer = None
                gc.collect()
                logger.info("Cleared FinBERT analyzer to free memory")
            
            # Clean up environment
            os.environ.pop('FINBERT_ONLY', None)
    
    def run_complete_analysis(self, symbols: List[str], include_stage2: bool = True) -> Dict[str, Any]:
        """
        Run complete two-stage analysis with memory management
        
        Args:
            symbols: List of stock symbols to analyze
            include_stage2: Whether to run FinBERT enhancement (set False for memory-constrained)
        
        Returns:
            Combined results from both stages
        """
        logger.info(f"🚀 Running complete two-stage analysis for {len(symbols)} symbols...")
        
        # Stage 1: Basic analysis
        stage1_results = self.run_stage1_analysis(symbols)
        
        if not include_stage2:
            logger.info("Skipping Stage 2 (FinBERT) due to memory constraints")
            return stage1_results
        
        # Stage 2: FinBERT enhancement
        stage2_results = self.run_stage2_analysis(symbols, stage1_results)
        
        # Combine results (prefer stage 2 if available)
        combined_results = {}
        for symbol in symbols:
            if symbol in stage2_results:
                combined_results[symbol] = stage2_results[symbol]
            elif symbol in stage1_results:
                combined_results[symbol] = stage1_results[symbol]
            else:
                combined_results[symbol] = self._create_fallback_result(symbol, 0)
        
        logger.info(f"✅ Complete analysis finished: {len(combined_results)} symbols")
        return combined_results
    
    def get_cached_results(self, max_age_hours: int = 1) -> Dict[str, Any]:
        """Get recent cached results to avoid recomputation"""
        try:
            stage1_file = os.path.join(self.cache_dir, "stage1_results.json")
            stage2_file = os.path.join(self.cache_dir, "stage2_results.json")
            
            results = {}
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            # Load stage 2 results (prefer these)
            if os.path.exists(stage2_file):
                with open(stage2_file, 'r') as f:
                    stage2_data = json.load(f)
                    for symbol, data in stage2_data.items():
                        if datetime.fromisoformat(data['timestamp']) > cutoff_time:
                            results[symbol] = data
            
            # Fill gaps with stage 1 results
            if os.path.exists(stage1_file):
                with open(stage1_file, 'r') as f:
                    stage1_data = json.load(f)
                    for symbol, data in stage1_data.items():
                        if symbol not in results and datetime.fromisoformat(data['timestamp']) > cutoff_time:
                            results[symbol] = data
            
            if results:
                logger.info(f"Loaded {len(results)} cached sentiment results")
            
            return results
            
        except Exception as e:
            logger.error(f"Error loading cached results: {e}")
            return {}
    
    def _save_stage_results(self, results: Dict[str, Any], stage: int):
        """Save stage results to cache"""
        try:
            filename = f"stage{stage}_results.json"
            filepath = os.path.join(self.cache_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(results, f, indent=2)
                
            logger.debug(f"Saved stage {stage} results to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving stage {stage} results: {e}")
    
    def _create_fallback_result(self, symbol: str, stage: int) -> Dict[str, Any]:
        """Create fallback result when analysis fails"""
        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'stage': stage,
            'overall_sentiment': 0.0,
            'confidence': 0.1,
            'news_count': 0,
            'sentiment_components': {},
            'recent_headlines': [],
            'method': 'fallback',
            'error': True
        }
    
    def _fallback_to_stage1(self, symbols: List[str], stage1_results: Optional[Dict] = None) -> Dict[str, Any]:
        """Fallback to stage 1 results when stage 2 fails"""
        if stage1_results:
            return stage1_results
        
        # Try to load from cache
        cached = self.get_cached_results(max_age_hours=6)  # More lenient for fallback
        if cached:
            return cached
        
        # Last resort: create fallback results
        return {symbol: self._create_fallback_result(symbol, 1) for symbol in symbols}
    
    def get_memory_status(self) -> Dict[str, Any]:
        """Get current memory usage status"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
        except ImportError:
            logger.warning("psutil not available, memory monitoring disabled")
            memory_mb = 0.0
        except Exception as e:
            logger.warning(f"Could not get memory status: {e}")
            memory_mb = 0.0
        
        return {
            'memory_usage_mb': round(memory_mb, 1),
            'basic_analyzer_loaded': self.basic_analyzer is not None,
            'finbert_analyzer_loaded': self.finbert_analyzer is not None,
            'stage1_cached_symbols': len(self.stage1_results),
            'stage2_cached_symbols': len(self.stage2_results)
        }
