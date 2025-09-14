#!/usr/bin/env python3
"""
RSS News Scraper for Australian Financial Sources

CRITICAL IMPLEMENTATION: Missing news scraping functionality identified in peer review.
This module implements the missing RSS feed processing that was absent from the 
SentimentService, integrating with settings.py NEWS_SOURCES configuration.

Purpose:
- Process RSS feeds from Australian financial news sources
- Extract and analyze news articles for sentiment analysis
- Integrate with settings.py NEWS_SOURCES configuration
- Provide news volume and quality metrics
- Support for Big 4 banks and financial sector coverage

News Sources (from settings.py):
Tier 1: RBA, ABS, Treasury, APRA (Government/Central Bank)
Tier 2: AFR, Market Index, Investing.com (Financial Media)  
Tier 3: ABC, SMH, The Age, News.com.au (Major Outlets)
Tier 4: Motley Fool, Investor Daily, ABA, Finsia (Specialized)

Features:
- RSS feed parsing with error handling
- Content extraction and cleaning
- Keyword-based relevance filtering
- Source quality scoring
- Time-based article filtering
- Caching to reduce load on news sources
- Australian market focus with banking keywords

Integration:
- Used by SentimentService for comprehensive news analysis
- Supports settings.py NEWS_SOURCES configuration
- Provides data for enhanced sentiment scoring
- Enables multi-source news aggregation

Dependencies:
- feedparser for RSS processing
- requests for HTTP operations
- BeautifulSoup for content extraction
- Settings configuration integration

Output:
- Structured news articles with metadata
- Source quality scoring
- Relevance scoring for financial/banking content
- Comprehensive error handling and logging
"""

import asyncio
import aiohttp
import feedparser
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re
import hashlib
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import time
import json
from dataclasses import dataclass
import sys
import os

# Import settings configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
try:
    from app.config.settings import Settings
    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    Settings = None

@dataclass
class NewsArticle:
    """Structured news article with enhanced metadata"""
    title: str
    description: str
    content: str
    url: str
    source: str
    published_at: datetime
    author: Optional[str] = None
    relevance_score: float = 0.0
    quality_score: float = 0.5
    sentiment_keywords: List[str] = None
    financial_keywords: List[str] = None
    article_id: str = None
    
    def __post_init__(self):
        if self.sentiment_keywords is None:
            self.sentiment_keywords = []
        if self.financial_keywords is None:
            self.financial_keywords = []
        if self.article_id is None:
            self.article_id = self._generate_article_id()
    
    def _generate_article_id(self) -> str:
        """Generate unique article ID"""
        content_hash = hashlib.md5(
            f"{self.title}{self.url}{self.published_at}".encode()
        ).hexdigest()
        return f"news_{content_hash[:12]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at.isoformat(),
            "author": self.author,
            "relevance_score": self.relevance_score,
            "quality_score": self.quality_score,
            "sentiment_keywords": self.sentiment_keywords,
            "financial_keywords": self.financial_keywords,
            "article_id": self.article_id
        }

class NewsScraperError(Exception):
    """Custom exception for news scraping errors"""
    pass

class AustralianFinancialNewsScraper:
    """RSS News Scraper for Australian Financial Sources with settings.py integration"""
    
    def __init__(self, cache_duration: int = 1800):  # 30 minutes default cache
        """Initialize with enhanced configuration service integration"""
        self.logger = logging.getLogger(__name__)
        self.cache_duration = cache_duration
        self.article_cache: Dict[str, Dict] = {}
        self.source_cache: Dict[str, List[NewsArticle]] = {}
        self.last_fetch_times: Dict[str, datetime] = {}
        
        # Configuration loaded from enhanced config service
        self.config_loaded = False
        self.news_sources = {}
        self.keywords = {}
        
        # Initialize with fallback configuration first
        self._initialize_fallback_config()
        
        # Will load from enhanced config service when first used
        
    async def _load_enhanced_config(self):
        """Load configuration from enhanced configuration service"""
        if self.config_loaded:
            return
            
        try:
            # Import here to avoid circular imports
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from services.base_service import BaseService
            
            # Create temporary service client for config
            temp_service = BaseService("temp-config-client")
            
            # Load enhanced news sources configuration
            enhanced_news_config = await temp_service.call_service(
                "enhanced-config", 
                "get_news_sources"
            )
            
            if enhanced_news_config and 'sources' in enhanced_news_config:
                self.news_sources = enhanced_news_config['sources']
                self.keywords = enhanced_news_config.get('keywords', {})
                self.source_quality_scores = enhanced_news_config.get('quality_scores', {})
                self.source_quality_tiers = enhanced_news_config.get('source_quality_tiers', {})
                self.update_frequencies = enhanced_news_config.get('update_frequencies', {})
                
                self.config_loaded = True
                self.logger.info("Loaded enhanced news configuration from config service")
            else:
                self.logger.warning("Enhanced config service available but no news sources found")
                
        except Exception as e:
            self.logger.warning(f"Could not load from enhanced config service: {e}")
            # Keep using fallback configuration
            
    def _initialize_fallback_config(self):
        """Initialize fallback configuration"""
        # Load configuration from settings.py or fallback
        if SETTINGS_AVAILABLE:
            self.news_sources = Settings.NEWS_SOURCES.get('rss_feeds', {})
            self.keywords = Settings.NEWS_SOURCES.get('keywords', {})
            self.logger.info("Loaded news sources from settings.py configuration")
        else:
            self.logger.warning("Settings.py not available - using fallback configuration")
            self.news_sources = self._get_fallback_sources()
            self.keywords = self._get_fallback_keywords()
        
        # Set default quality scores and tiers for fallback
        self.source_quality_scores = self._get_fallback_quality_scores()
        self.source_quality_tiers = self._get_fallback_quality_tiers()
        self.update_frequencies = self._get_fallback_update_frequencies()
        
        # Validate configuration
        if not self.news_sources:
            raise NewsScraperError("No news sources configured")
        
        # Initialize session for HTTP requests
        self.session = None
        
        self.logger.info(f"Initialized with {len(self.news_sources)} news sources")
    
    def _get_fallback_quality_scores(self) -> Dict[str, float]:
        """Fallback quality scores for news sources"""
        return {
            # Tier 1: Government & Central Bank (Highest Quality)
            'rba': 1.0, 'abs': 1.0, 'treasury': 1.0, 'apra': 1.0,
            # Tier 2: Major Financial Media (High Quality)
            'afr_companies': 0.9, 'afr_markets': 0.9, 'market_index': 0.8, 
            'investing_au': 0.8, 'business_news': 0.8,
            # Tier 3: Major News Outlets (Good Quality)
            'abc_business': 0.7, 'smh_business': 0.7, 'the_age_business': 0.7, 'news_com_au': 0.6,
            # Tier 4: Specialized Financial (Medium Quality)
            'motley_fool_au': 0.6, 'investor_daily': 0.6, 'aba_news': 0.7, 'finsia': 0.6
        }
    
    def _get_fallback_quality_tiers(self) -> Dict[str, List[str]]:
        """Fallback quality tiers for news sources"""
        return {
            'tier_1': ['rba', 'abs', 'treasury', 'apra'],
            'tier_2': ['afr_companies', 'afr_markets', 'market_index', 'investing_au', 'business_news'],
            'tier_3': ['abc_business', 'smh_business', 'the_age_business', 'news_com_au'],
            'tier_4': ['motley_fool_au', 'investor_daily', 'aba_news', 'finsia']
        }
    
    def _get_fallback_update_frequencies(self) -> Dict[str, int]:
        """Fallback update frequencies for news sources (in minutes)"""
        return {
            'tier_1': 60,  # Every hour for government sources
            'tier_2': 30,  # Every 30 minutes for financial media
            'tier_3': 45,  # Every 45 minutes for major news
            'tier_4': 60   # Every hour for specialized sources
        }
    
    def _get_fallback_sources(self) -> Dict[str, str]:
        """Fallback news sources if settings.py unavailable"""
        return {
            'rba': 'https://www.rba.gov.au/rss/rss-cb.xml',
            'afr_companies': 'https://www.afr.com/rss/companies',
            'afr_markets': 'https://www.afr.com/rss/markets',
            'abc_business': 'https://www.abc.net.au/news/feed/2942460/rss.xml',
            'smh_business': 'https://www.smh.com.au/rss/business.xml'
        }
    
    def _get_fallback_keywords(self) -> Dict[str, List[str]]:
        """Fallback keywords if settings.py unavailable"""
        return {
            'banking': ['bank', 'banking', 'finance', 'credit', 'loan', 'mortgage'],
            'regulation': ['APRA', 'ASIC', 'regulation', 'compliance', 'capital'],
            'monetary': ['RBA', 'interest rate', 'cash rate', 'monetary policy'],
            'market': ['ASX', 'share price', 'dividend', 'earnings', 'profit']
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'TradingAnalysisBot/1.0 (+https://example.com/contact)'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_all_news(self, max_age_hours: int = 24, 
                           force_refresh: bool = False) -> Dict[str, List[NewsArticle]]:
        """Fetch news from all configured sources with enhanced configuration"""
        if not self.session:
            raise NewsScraperError("Session not initialized. Use async context manager.")
        
        # Load enhanced configuration if not already loaded
        if not self.config_loaded:
            await self._load_enhanced_config()
        
        all_news = {}
        successful_sources = 0
        failed_sources = 0
        
        self.logger.info(f"Fetching news from {len(self.news_sources)} sources")
        
        # Create tasks for all sources
        tasks = []
        for source_name, source_config in self.news_sources.items():
            # Handle both old and new config formats
            if isinstance(source_config, dict):
                rss_url = source_config.get('url', source_config.get('rss_url', ''))
            else:
                rss_url = source_config
                
            if rss_url:
                task = asyncio.create_task(
                    self._fetch_source_news(source_name, rss_url, max_age_hours, force_refresh),
                    name=f"fetch_{source_name}"
            )
            tasks.append((source_name, task))
        
        # Execute all tasks with error isolation
        for source_name, task in tasks:
            try:
                articles = await task
                if articles:
                    all_news[source_name] = articles
                    successful_sources += 1
                    self.logger.info(f"Successfully fetched {len(articles)} articles from {source_name}")
                else:
                    self.logger.warning(f"No articles fetched from {source_name}")
                    failed_sources += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to fetch from {source_name}: {e}")
                failed_sources += 1
                all_news[source_name] = []
        
        self.logger.info(f"News fetch completed: {successful_sources} successful, {failed_sources} failed")
        
        return all_news
    
    async def _fetch_source_news(self, source_name: str, rss_url: str, 
                                max_age_hours: int, force_refresh: bool) -> List[NewsArticle]:
        """Fetch news from a single RSS source with caching"""
        
        # Check cache first
        if not force_refresh and source_name in self.source_cache:
            last_fetch = self.last_fetch_times.get(source_name)
            if last_fetch and (datetime.now() - last_fetch).seconds < self.cache_duration:
                self.logger.debug(f"Using cached data for {source_name}")
                return self.source_cache[source_name]
        
        try:
            # Validate URL
            if not rss_url or not isinstance(rss_url, str):
                raise NewsScraperError(f"Invalid RSS URL for {source_name}")
            
            # Fetch RSS feed with timeout
            self.logger.debug(f"Fetching RSS from {source_name}: {rss_url}")
            
            async with self.session.get(rss_url) as response:
                if response.status != 200:
                    raise NewsScraperError(f"HTTP {response.status} for {source_name}")
                
                content = await response.text()
                
                if not content or len(content) < 100:  # Sanity check
                    raise NewsScraperError(f"Invalid RSS content from {source_name}")
            
            # Parse RSS feed
            feed = feedparser.parse(content)
            
            if feed.bozo and feed.bozo_exception:
                self.logger.warning(f"RSS parsing warning for {source_name}: {feed.bozo_exception}")
            
            if not hasattr(feed, 'entries') or not feed.entries:
                self.logger.warning(f"No entries found in RSS feed for {source_name}")
                return []
            
            # Process articles
            articles = []
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            for entry in feed.entries[:50]:  # Limit to 50 most recent
                try:
                    article = await self._process_rss_entry(entry, source_name, cutoff_time)
                    if article:
                        articles.append(article)
                except Exception as e:
                    self.logger.warning(f"Failed to process entry from {source_name}: {e}")
                    continue
            
            # Cache results
            self.source_cache[source_name] = articles
            self.last_fetch_times[source_name] = datetime.now()
            
            return articles
            
        except Exception as e:
            self.logger.error(f"Error fetching from {source_name}: {e}")
            return []
    
    async def _process_rss_entry(self, entry, source_name: str, 
                               cutoff_time: datetime) -> Optional[NewsArticle]:
        """Process individual RSS entry into NewsArticle"""
        
        try:
            # Extract basic information
            title = self._clean_text(getattr(entry, 'title', ''))
            description = self._clean_text(getattr(entry, 'summary', ''))
            url = getattr(entry, 'link', '')
            
            # Validate required fields
            if not title or not url:
                return None
            
            # Parse publication date
            published_at = self._parse_publish_date(entry)
            if not published_at or published_at < cutoff_time:
                return None
            
            # Extract additional content if available
            content = self._extract_content(entry)
            author = getattr(entry, 'author', None)
            
            # Create article
            article = NewsArticle(
                title=title,
                description=description,
                content=content,
                url=url,
                source=source_name,
                published_at=published_at,
                author=author
            )
            
            # Calculate scores
            article.quality_score = self._calculate_quality_score(article, source_name)
            article.relevance_score = self._calculate_relevance_score(article)
            
            # Extract keywords
            article.financial_keywords = self._extract_financial_keywords(article)
            article.sentiment_keywords = self._extract_sentiment_keywords(article)
            
            return article
            
        except Exception as e:
            self.logger.warning(f"Error processing RSS entry: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and sanitize text content"""
        if not text:
            return ""
        
        # Remove HTML tags
        if '<' in text and '>' in text:
            soup = BeautifulSoup(text, 'html.parser')
            text = soup.get_text()
        
        # Clean whitespace and special characters
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Limit length for safety
        return text[:5000]
    
    def _parse_publish_date(self, entry) -> Optional[datetime]:
        """Parse publication date from RSS entry"""
        try:
            # Try common RSS date fields
            for date_field in ['published', 'updated', 'created']:
                if hasattr(entry, date_field):
                    date_str = getattr(entry, date_field)
                    if date_str:
                        # Parse using feedparser's time_struct
                        if hasattr(entry, f'{date_field}_parsed'):
                            time_struct = getattr(entry, f'{date_field}_parsed')
                            if time_struct:
                                return datetime(*time_struct[:6])
            
            # Fallback to current time if no date found
            return datetime.now()
            
        except Exception as e:
            self.logger.warning(f"Date parsing error: {e}")
            return datetime.now()
    
    def _extract_content(self, entry) -> str:
        """Extract full content from RSS entry"""
        content_fields = ['content', 'description', 'summary']
        
        for field in content_fields:
            if hasattr(entry, field):
                content_data = getattr(entry, field)
                
                if isinstance(content_data, list) and content_data:
                    # Handle structured content
                    content_item = content_data[0]
                    if hasattr(content_item, 'value'):
                        return self._clean_text(content_item.value)
                elif isinstance(content_data, str):
                    return self._clean_text(content_data)
        
        return ""
    
    def _calculate_quality_score(self, article: NewsArticle, source_name: str) -> float:
        """Calculate quality score for article"""
        base_quality = self.source_quality_scores.get(source_name, 0.5)
        
        # Adjust based on content length
        content_length = len(article.title) + len(article.description) + len(article.content)
        
        if content_length > 1000:
            length_bonus = 0.2
        elif content_length > 500:
            length_bonus = 0.1
        else:
            length_bonus = 0.0
        
        # Adjust based on recency
        hours_old = (datetime.now() - article.published_at).total_seconds() / 3600
        if hours_old < 6:
            recency_bonus = 0.2
        elif hours_old < 24:
            recency_bonus = 0.1
        else:
            recency_bonus = 0.0
        
        # Author bonus
        author_bonus = 0.1 if article.author else 0.0
        
        quality = base_quality + length_bonus + recency_bonus + author_bonus
        return min(1.0, max(0.0, quality))
    
    def _calculate_relevance_score(self, article: NewsArticle) -> float:
        """Calculate relevance score for financial/banking content"""
        content = f"{article.title} {article.description} {article.content}".lower()
        
        relevance_score = 0.0
        total_keywords = 0
        
        # Score based on keyword categories
        for category, keywords in self.keywords.items():
            category_matches = 0
            for keyword in keywords:
                count = content.count(keyword.lower())
                category_matches += count
                total_keywords += len(keywords)
            
            # Weight categories differently
            weights = {
                'banking': 0.4,
                'regulation': 0.3,
                'monetary': 0.3,
                'market': 0.2
            }
            
            category_weight = weights.get(category, 0.1)
            category_score = min(1.0, category_matches / len(keywords))
            relevance_score += category_score * category_weight
        
        # Big 4 bank mentions bonus
        big4_banks = ['commonwealth bank', 'cba', 'anz', 'westpac', 'wbc', 'nab', 'national australia bank']
        for bank in big4_banks:
            if bank in content:
                relevance_score += 0.1
        
        return min(1.0, max(0.0, relevance_score))
    
    def _extract_financial_keywords(self, article: NewsArticle) -> List[str]:
        """Extract financial keywords from article"""
        content = f"{article.title} {article.description} {article.content}".lower()
        found_keywords = []
        
        for category, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword.lower() in content:
                    found_keywords.append(keyword)
        
        return list(set(found_keywords))  # Remove duplicates
    
    def _extract_sentiment_keywords(self, article: NewsArticle) -> List[str]:
        """Extract sentiment-bearing keywords from article"""
        positive_words = [
            'growth', 'profit', 'increase', 'strong', 'positive', 'good', 'excellent',
            'outperform', 'buy', 'bullish', 'upgrade', 'beat', 'exceed', 'optimistic',
            'recovery', 'expansion', 'gain', 'boost', 'improve'
        ]
        
        negative_words = [
            'loss', 'decline', 'decrease', 'weak', 'negative', 'poor', 'bad',
            'underperform', 'sell', 'bearish', 'downgrade', 'miss', 'below', 'pessimistic',
            'recession', 'contraction', 'fall', 'drop', 'concern', 'risk'
        ]
        
        content = f"{article.title} {article.description} {article.content}".lower()
        sentiment_keywords = []
        
        for word in positive_words + negative_words:
            if word in content:
                sentiment_keywords.append(word)
        
        return sentiment_keywords
    
    async def get_banking_news(self, max_age_hours: int = 24) -> List[NewsArticle]:
        """Get news specifically relevant to banking sector"""
        all_news = await self.fetch_all_news(max_age_hours)
        
        banking_articles = []
        for source_articles in all_news.values():
            for article in source_articles:
                # Filter for banking relevance
                if article.relevance_score >= 0.3:  # Minimum relevance threshold
                    banking_articles.append(article)
        
        # Sort by relevance and quality
        banking_articles.sort(
            key=lambda x: (x.relevance_score * 0.6 + x.quality_score * 0.4), 
            reverse=True
        )
        
        return banking_articles
    
    async def get_symbol_news(self, symbol: str, max_age_hours: int = 24) -> List[NewsArticle]:
        """Get news for specific symbol/company"""
        # Map symbols to company names for search
        symbol_map = {
            'CBA.AX': ['commonwealth bank', 'cba'],
            'ANZ.AX': ['anz', 'australia new zealand banking'],
            'NAB.AX': ['nab', 'national australia bank'],
            'WBC.AX': ['westpac', 'wbc'],
            'MQG.AX': ['macquarie', 'mqg'],
            'COL.AX': ['coles'],
            'BHP.AX': ['bhp', 'bhp billiton']
        }
        
        search_terms = symbol_map.get(symbol, [symbol.replace('.AX', '').lower()])
        all_news = await self.fetch_all_news(max_age_hours)
        
        relevant_articles = []
        for source_articles in all_news.values():
            for article in source_articles:
                content = f"{article.title} {article.description} {article.content}".lower()
                
                # Check if any search term appears in content
                for term in search_terms:
                    if term in content:
                        relevant_articles.append(article)
                        break
        
        # Sort by quality and recency
        relevant_articles.sort(
            key=lambda x: (x.quality_score * 0.7 + (1.0 - min(1.0, (datetime.now() - x.published_at).total_seconds() / 86400)) * 0.3),
            reverse=True
        )
        
        return relevant_articles
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get caching statistics"""
        total_cached_articles = sum(len(articles) for articles in self.source_cache.values())
        
        return {
            "cached_sources": len(self.source_cache),
            "total_cached_articles": total_cached_articles,
            "cache_duration_seconds": self.cache_duration,
            "last_fetch_times": {
                source: time.isoformat() 
                for source, time in self.last_fetch_times.items()
            }
        }

# Example usage and testing
async def main():
    """Example usage of the news scraper"""
    async with AustralianFinancialNewsScraper() as scraper:
        print("Fetching all news...")
        all_news = await scraper.fetch_all_news(max_age_hours=24)
        
        total_articles = sum(len(articles) for articles in all_news.values())
        print(f"Fetched {total_articles} articles from {len(all_news)} sources")
        
        # Get banking-specific news
        banking_news = await scraper.get_banking_news()
        print(f"Found {len(banking_news)} banking-relevant articles")
        
        # Get CBA-specific news
        cba_news = await scraper.get_symbol_news("CBA.AX")
        print(f"Found {len(cba_news)} CBA-specific articles")
        
        # Show sample articles
        if banking_news:
            print(f"\nSample banking article:")
            article = banking_news[0]
            print(f"Title: {article.title}")
            print(f"Source: {article.source}")
            print(f"Relevance: {article.relevance_score:.2f}")
            print(f"Quality: {article.quality_score:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
