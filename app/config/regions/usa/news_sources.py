"""
USA Financial News Sources Configuration

This module contains comprehensive US financial news sources organized by quality tiers.
Focus on major US financial media, government sources, and market-specific news.
"""

from typing import Dict, List, Any

# USA-Specific News Sources (4-Tier Quality System)
NEWS_SOURCES = {
    "rss_feeds": {
        # Tier 1: Government & Federal Sources (Highest Quality - Score: 1.0)
        "federal_reserve": {
            "url": "https://www.federalreserve.gov/feeds/press_all.xml",
            "name": "Federal Reserve Press Releases",
            "tier": 1,
            "quality_score": 1.0,
            "language": "en",
            "update_frequency": 60,  # minutes
            "focus": ["monetary_policy", "banking_regulation", "financial_stability"],
            "credibility": "highest"
        },
        "sec": {
            "url": "https://www.sec.gov/rss/press-release.xml",
            "name": "Securities and Exchange Commission",
            "tier": 1,
            "quality_score": 1.0,
            "language": "en",
            "update_frequency": 60,
            "focus": ["securities_regulation", "enforcement", "market_oversight"],
            "credibility": "highest"
        },
        "treasury": {
            "url": "https://home.treasury.gov/rss",
            "name": "US Department of Treasury",
            "tier": 1,
            "quality_score": 1.0,
            "language": "en",
            "update_frequency": 60,
            "focus": ["fiscal_policy", "economic_policy", "financial_regulation"],
            "credibility": "highest"
        },
        "fdic": {
            "url": "https://www.fdic.gov/rss/rss.xml",
            "name": "Federal Deposit Insurance Corporation",
            "tier": 1,
            "quality_score": 1.0,
            "language": "en",
            "update_frequency": 60,
            "focus": ["banking_regulation", "deposit_insurance", "bank_failures"],
            "credibility": "highest"
        },
        "occ": {
            "url": "https://www.occ.gov/rss/rss.xml",
            "name": "Office of the Comptroller of the Currency",
            "tier": 1,
            "quality_score": 1.0,
            "language": "en",
            "update_frequency": 60,
            "focus": ["national_bank_regulation", "banking_supervision"],
            "credibility": "highest"
        },
        
        # Tier 2: Major Financial Media (High Quality - Score: 0.8-0.9)
        "wsj_markets": {
            "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
            "name": "Wall Street Journal - Markets",
            "tier": 2,
            "quality_score": 0.95,
            "language": "en",
            "update_frequency": 15,
            "focus": ["markets", "stocks", "trading", "financial_analysis"],
            "credibility": "highest"
        },
        "wsj_economy": {
            "url": "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
            "name": "Wall Street Journal - Economy",
            "tier": 2,
            "quality_score": 0.95,
            "language": "en",
            "update_frequency": 15,
            "focus": ["economy", "business", "corporate_news"],
            "credibility": "highest"
        },
        "bloomberg_markets": {
            "url": "https://feeds.bloomberg.com/markets/news.rss",
            "name": "Bloomberg Markets",
            "tier": 2,
            "quality_score": 0.9,
            "language": "en",
            "update_frequency": 15,
            "focus": ["markets", "finance", "economy", "global_markets"],
            "credibility": "high"
        },
        "financial_times": {
            "url": "https://www.ft.com/markets?format=rss",
            "name": "Financial Times - Markets",
            "tier": 2,
            "quality_score": 0.9,
            "language": "en",
            "update_frequency": 20,
            "focus": ["global_markets", "finance", "economics", "banking"],
            "credibility": "high"
        },
        "reuters_business": {
            "url": "https://feeds.reuters.com/reuters/businessNews",
            "name": "Reuters Business News",
            "tier": 2,
            "quality_score": 0.85,
            "language": "en",
            "update_frequency": 20,
            "focus": ["business", "finance", "markets", "corporate"],
            "credibility": "high"
        },
        "marketwatch": {
            "url": "https://feeds.marketwatch.com/marketwatch/marketpulse/",
            "name": "MarketWatch",
            "tier": 2,
            "quality_score": 0.8,
            "language": "en",
            "update_frequency": 30,
            "focus": ["markets", "stocks", "personal_finance", "investing"],
            "credibility": "high"
        },
        
        # Tier 3: Major News Outlets (Good Quality - Score: 0.6-0.7)
        "cnbc_markets": {
            "url": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
            "name": "CNBC Markets",
            "tier": 3,
            "quality_score": 0.75,
            "language": "en",
            "update_frequency": 30,
            "focus": ["markets", "stocks", "business_news", "economy"],
            "credibility": "medium-high"
        },
        "cnn_business": {
            "url": "http://rss.cnn.com/rss/money_latest.rss",
            "name": "CNN Business",
            "tier": 3,
            "quality_score": 0.7,
            "language": "en",
            "update_frequency": 45,
            "focus": ["business", "economy", "markets", "corporate_news"],
            "credibility": "medium-high"
        },
        "fox_business": {
            "url": "https://moxie.foxbusiness.com/google-publisher/markets.xml",
            "name": "Fox Business",
            "tier": 3,
            "quality_score": 0.65,
            "language": "en",
            "update_frequency": 45,
            "focus": ["business", "markets", "economy", "investing"],
            "credibility": "medium"
        },
        "nytimes_business": {
            "url": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
            "name": "New York Times - Business",
            "tier": 3,
            "quality_score": 0.8,
            "language": "en",
            "update_frequency": 60,
            "focus": ["business", "economy", "finance", "corporate"],
            "credibility": "high"
        },
        "usa_today_money": {
            "url": "http://rssfeeds.usatoday.com/usatoday-money-topstories",
            "name": "USA Today - Money",
            "tier": 3,
            "quality_score": 0.6,
            "language": "en",
            "update_frequency": 60,
            "focus": ["personal_finance", "business", "economy"],
            "credibility": "medium"
        },
        
        # Tier 4: Specialized Financial Sources (Medium Quality - Score: 0.5-0.6)
        "seeking_alpha": {
            "url": "https://seekingalpha.com/feed.xml",
            "name": "Seeking Alpha",
            "tier": 4,
            "quality_score": 0.6,
            "language": "en",
            "update_frequency": 30,
            "focus": ["investment_analysis", "stock_research", "earnings"],
            "credibility": "medium"
        },
        "motley_fool": {
            "url": "https://www.fool.com/feed/",
            "name": "The Motley Fool",
            "tier": 4,
            "quality_score": 0.55,
            "language": "en",
            "update_frequency": 60,
            "focus": ["investment_advice", "stock_analysis", "long_term_investing"],
            "credibility": "medium"
        },
        "zacks": {
            "url": "https://www.zacks.com/rss/articles.xml",
            "name": "Zacks Investment Research",
            "tier": 4,
            "quality_score": 0.6,
            "language": "en",
            "update_frequency": 60,
            "focus": ["stock_research", "earnings_estimates", "investment_strategy"],
            "credibility": "medium"
        },
        "bank_innovation": {
            "url": "https://bankinnovation.net/feed/",
            "name": "Bank Innovation",
            "tier": 4,
            "quality_score": 0.5,
            "language": "en",
            "update_frequency": 60,
            "focus": ["banking_technology", "fintech", "digital_banking"],
            "credibility": "medium"
        },
        "american_banker": {
            "url": "https://www.americanbanker.com/feeds/all",
            "name": "American Banker",
            "tier": 4,
            "quality_score": 0.65,
            "language": "en",
            "update_frequency": 60,
            "focus": ["banking_industry", "regulation", "technology"],
            "credibility": "medium"
        },
        "investopedia": {
            "url": "https://www.investopedia.com/feedbuilder/feed/getfeed?feedName=rss_headline",
            "name": "Investopedia",
            "tier": 4,
            "quality_score": 0.55,
            "language": "en",
            "update_frequency": 60,
            "focus": ["financial_education", "market_analysis", "investing_basics"],
            "credibility": "medium"
        }
    },
    
    # USA-Specific Keywords for Relevance Filtering
    "keywords": {
        "bank_keywords": [
            # Major US Banks
            "JPMorgan", "JPM", "Chase", "Bank of America", "BAC", 
            "Wells Fargo", "WFC", "Citigroup", "Citi", "Goldman Sachs", "GS",
            "Morgan Stanley", "MS", "U.S. Bancorp", "USB", "PNC", "Truist", "TFC",
            
            # Banking Terms
            "banking", "bank", "credit", "loan", "mortgage", "deposit",
            "interest rate", "Federal Reserve", "Fed", "FDIC", "OCC",
            "stress test", "CCAR", "capital ratio", "Dodd-Frank",
            
            # US Banking Specific
            "money center bank", "regional bank", "community bank",
            "systemically important", "G-SIB", "too big to fail"
        ],
        
        "financial_keywords": [
            # Market Terms
            "NYSE", "NASDAQ", "S&P 500", "Dow Jones", "Russell 2000",
            "stocks", "shares", "equities", "market", "trading", "volume",
            "dividend", "earnings", "profit", "revenue", "EPS",
            
            # Economic Terms
            "Federal Reserve", "Fed", "FOMC", "interest rates", "inflation",
            "GDP", "unemployment", "non-farm payrolls", "CPI", "PCE",
            "economic growth", "recession", "stimulus", "fiscal policy",
            
            # Financial Services
            "investment banking", "asset management", "wealth management",
            "brokerage", "insurance", "private equity", "hedge fund",
            "mutual fund", "ETF", "401k", "IRA"
        ],
        
        "sector_keywords": [
            # Financial Sector
            "financial sector", "banking sector", "financials", "XLF",
            "fintech", "digital banking", "neobank", "challenger bank",
            "robo-advisor", "cryptocurrency", "blockchain",
            
            # Regulation
            "SEC", "Federal Reserve", "FDIC", "OCC", "FINRA", "CFTC",
            "Dodd-Frank", "Basel III", "Volcker Rule", "stress test",
            "capital requirements", "liquidity coverage ratio",
            
            # Technology & Innovation
            "artificial intelligence", "machine learning", "big data",
            "cloud computing", "cybersecurity", "digital transformation",
            "mobile banking", "online banking", "payment systems"
        ],
        
        "sentiment_keywords": {
            "positive": [
                "profit", "earnings beat", "growth", "expansion", "strong",
                "outperform", "upgrade", "bullish", "optimistic", "record",
                "dividend increase", "share buyback", "merger", "acquisition"
            ],
            "negative": [
                "loss", "earnings miss", "decline", "fall", "weak", "poor",
                "downgrade", "bearish", "pessimistic", "investigation",
                "lawsuit", "fine", "penalty", "scandal", "regulatory action"
            ],
            "neutral": [
                "stable", "unchanged", "maintain", "steady", "consistent",
                "meets expectations", "in line", "guidance", "outlook"
            ]
        }
    }
}

# News Source Configurations by Tier
TIER_CONFIGURATIONS = {
    1: {
        "name": "Government & Federal Agencies",
        "description": "Official US government and regulatory sources",
        "quality_score_range": [0.95, 1.0],
        "update_frequency": 60,
        "reliability": "highest",
        "bias_level": "minimal",
        "fact_checking": "excellent"
    },
    2: {
        "name": "Premier Financial Media",
        "description": "Top-tier financial news organizations",
        "quality_score_range": [0.8, 0.95],
        "update_frequency": 15,
        "reliability": "highest",
        "bias_level": "minimal",
        "fact_checking": "excellent"
    },
    3: {
        "name": "Major News Networks",
        "description": "Established news organizations with business coverage",
        "quality_score_range": [0.6, 0.8],
        "update_frequency": 45,
        "reliability": "high",
        "bias_level": "low-medium",
        "fact_checking": "good"
    },
    4: {
        "name": "Specialized Financial",
        "description": "Investment-focused and specialized financial sources",
        "quality_score_range": [0.5, 0.6],
        "update_frequency": 60,
        "reliability": "medium",
        "bias_level": "medium",
        "fact_checking": "variable"
    }
}

# Regional News Preferences for USA
REGIONAL_PREFERENCES = {
    "language": "en",
    "timezone": "America/New_York",
    "business_hours": {
        "start": "09:30",
        "end": "16:00"
    },
    "market_focus": "nyse_nasdaq",
    "currency_focus": "USD",
    "regulatory_focus": ["SEC", "Federal Reserve", "FDIC", "OCC"],
    "major_companies": [
        "JPM", "BAC", "WFC", "C", "GS", "MS", "AAPL", "MSFT", "GOOGL", "AMZN"
    ]
}

# News Processing Configuration for USA
PROCESSING_CONFIG = {
    "relevance_scoring": {
        "bank_keyword_weight": 0.4,
        "financial_keyword_weight": 0.3,
        "sector_keyword_weight": 0.2,
        "sentiment_keyword_weight": 0.1
    },
    "quality_factors": {
        "source_tier_weight": 0.5,
        "article_length_weight": 0.2,
        "recency_weight": 0.2,
        "keyword_density_weight": 0.1
    },
    "filtering": {
        "minimum_relevance_score": 0.3,
        "maximum_article_age_hours": 48,
        "minimum_article_length": 100,
        "duplicate_threshold": 0.85
    },
    "us_specific": {
        "earnings_season_boost": 1.5,  # Amplify during earnings
        "fed_announcement_boost": 2.0,  # Fed announcements are critical
        "sec_filing_boost": 1.3,  # SEC filings important
        "after_hours_penalty": 0.8  # Lower weight for after-hours news
    }
}

def get_news_sources_by_tier(tier: int) -> Dict[str, Any]:
    """Get all news sources for a specific tier"""
    return {
        source_id: source_config 
        for source_id, source_config in NEWS_SOURCES["rss_feeds"].items()
        if source_config["tier"] == tier
    }

def get_federal_sources() -> Dict[str, Any]:
    """Get tier 1 federal government sources"""
    return get_news_sources_by_tier(1)

def get_premium_financial_sources() -> Dict[str, Any]:
    """Get tier 2 premium financial media sources"""
    return get_news_sources_by_tier(2)

def get_high_priority_sources() -> Dict[str, Any]:
    """Get tier 1 and tier 2 sources for priority processing"""
    high_priority = {}
    for source_id, source_config in NEWS_SOURCES["rss_feeds"].items():
        if source_config["tier"] <= 2:
            high_priority[source_id] = source_config
    return high_priority

def calculate_source_weight(source_id: str) -> float:
    """Calculate processing weight for a news source"""
    if source_id not in NEWS_SOURCES["rss_feeds"]:
        return 0.0
    
    source_config = NEWS_SOURCES["rss_feeds"][source_id]
    tier = source_config["tier"]
    quality_score = source_config["quality_score"]
    
    # Higher weight for better sources
    tier_weights = {1: 1.0, 2: 0.9, 3: 0.7, 4: 0.5}
    
    return tier_weights.get(tier, 0.3) * quality_score

def get_update_schedule() -> Dict[str, int]:
    """Get update frequency schedule for all sources"""
    schedule = {}
    for source_id, source_config in NEWS_SOURCES["rss_feeds"].items():
        schedule[source_id] = source_config["update_frequency"]
    return schedule

def get_banking_focused_sources() -> Dict[str, Any]:
    """Get sources with strong banking industry focus"""
    banking_sources = {}
    for source_id, source_config in NEWS_SOURCES["rss_feeds"].items():
        focus_areas = source_config.get("focus", [])
        if any("bank" in focus.lower() for focus in focus_areas):
            banking_sources[source_id] = source_config
    return banking_sources
