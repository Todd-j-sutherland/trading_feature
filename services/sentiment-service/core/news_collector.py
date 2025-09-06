"""
News Collector - Collects news from various sources.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import feedparser
import requests
from bs4 import BeautifulSoup
import re

from shared.models import NewsArticle
from shared.utils import retry_on_failure


class NewsCollector:
    """Collects news from multiple sources."""
    
    def __init__(self):
        self.sources = {
            "abc_news": "https://www.abc.net.au/news/feed/51120/rss.xml",
            "afr": "https://www.afr.com/rss/companies",
            "reuters": "https://feeds.reuters.com/reuters/businessNews",
        }
        
        # Keywords for different symbols
        self.symbol_keywords = {
            "CBA.AX": ["commonwealth bank", "cba", "commbank"],
            "ANZ.AX": ["anz", "australia new zealand banking", "anz bank"],
            "WBC.AX": ["westpac", "wbc", "westpac banking"],
            "NAB.AX": ["national australia bank", "nab", "nab bank"],
            "MQG.AX": ["macquarie", "mqg", "macquarie group"],
        }
    
    @retry_on_failure(max_retries=3)
    def get_recent_news(self, symbol: str, hours: int = 24) -> List[NewsArticle]:
        """Get recent news articles for a symbol."""
        articles = []
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        keywords = self.symbol_keywords.get(symbol, [symbol.replace(".AX", "").lower()])
        
        for source_name, feed_url in self.sources.items():
            try:
                source_articles = self._fetch_from_rss(feed_url, source_name, keywords, cutoff_time)
                articles.extend(source_articles)
            except Exception as e:
                print(f"Error fetching from {source_name}: {e}")
        
        # Sort by publication date (newest first)
        articles.sort(key=lambda x: x.published_at, reverse=True)
        
        return articles
    
    def _fetch_from_rss(self, feed_url: str, source_name: str, keywords: List[str], cutoff_time: datetime) -> List[NewsArticle]:
        """Fetch articles from RSS feed."""
        articles = []
        
        try:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries:
                # Check if article is recent enough
                published_time = self._parse_time(getattr(entry, 'published', ''))
                if not published_time or published_time < cutoff_time:
                    continue
                
                # Check if article is relevant to the keywords
                title = getattr(entry, 'title', '')
                description = getattr(entry, 'description', '')
                content = f"{title} {description}".lower()
                
                if not any(keyword.lower() in content for keyword in keywords):
                    continue
                
                # Create article
                article = NewsArticle(
                    title=title,
                    content=self._clean_content(description),
                    url=getattr(entry, 'link', ''),
                    published_at=published_time,
                    source=source_name,
                    symbols_mentioned=keywords
                )
                
                articles.append(article)
        
        except Exception as e:
            print(f"Error parsing RSS feed {feed_url}: {e}")
        
        return articles
    
    def _parse_time(self, time_str: str) -> datetime:
        """Parse time string to datetime object."""
        if not time_str:
            return None
        
        try:
            # Try common time formats
            for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%a, %d %b %Y %H:%M:%S', '%Y-%m-%dT%H:%M:%S']:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue
            
            # If all formats fail, try with dateutil
            from dateutil import parser
            return parser.parse(time_str)
        except:
            # Return current time if parsing fails
            return datetime.utcnow()
    
    def _clean_content(self, content: str) -> str:
        """Clean HTML content and extract text."""
        if not content:
            return ""
        
        # Remove HTML tags
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def add_source(self, name: str, url: str):
        """Add a new news source."""
        self.sources[name] = url
    
    def add_symbol_keywords(self, symbol: str, keywords: List[str]):
        """Add keywords for a symbol."""
        self.symbol_keywords[symbol] = keywords
    
    def get_all_recent_news(self, hours: int = 24) -> List[NewsArticle]:
        """Get all recent news regardless of symbol."""
        articles = []
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        for source_name, feed_url in self.sources.items():
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    published_time = self._parse_time(getattr(entry, 'published', ''))
                    if not published_time or published_time < cutoff_time:
                        continue
                    
                    article = NewsArticle(
                        title=getattr(entry, 'title', ''),
                        content=self._clean_content(getattr(entry, 'description', '')),
                        url=getattr(entry, 'link', ''),
                        published_at=published_time,
                        source=source_name,
                        symbols_mentioned=[]
                    )
                    
                    articles.append(article)
            
            except Exception as e:
                print(f"Error fetching from {source_name}: {e}")
        
        # Sort by publication date
        articles.sort(key=lambda x: x.published_at, reverse=True)
        
        return articles