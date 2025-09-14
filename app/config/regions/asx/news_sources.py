"""
ASX (Australian) Financial News Sources Configuration

This module contains comprehensive Australian financial news sources organized by quality tiers.
Based on your original settings.py NEWS_SOURCES with enhancements for ASX market coverage.
"""

from typing import Dict, List, Any

# ASX-Specific News Sources (4-Tier Quality System)
NEWS_SOURCES = {
    "rss_feeds": {
        # Tier 1: Government & Central Bank Sources (Highest Quality - Score: 1.0)
        "rba": {
            "url": "https://www.rba.gov.au/rss/rss-cb.xml", 
            "name": "Reserve Bank of Australia",
            "tier": 1,
            "quality_score": 1.0,
            "language": "en",
            "update_frequency": 60,  # minutes
            "focus": ["monetary_policy", "financial_stability", "banking"],
            "credibility": "highest"
        },
        "abs": {
            "url": "https://www.abs.gov.au/rss.xml",
            "name": "Australian Bureau of Statistics", 
            "tier": 1,
            "quality_score": 1.0,
            "language": "en",
            "update_frequency": 60,
            "focus": ["economic_data", "employment", "inflation"],
            "credibility": "highest"
        },
        "treasury": {
            "url": "https://treasury.gov.au/rss",
            "name": "Australian Treasury",
            "tier": 1, 
            "quality_score": 1.0,
            "language": "en",
            "update_frequency": 60,
            "focus": ["fiscal_policy", "economic_policy", "financial_regulation"],
            "credibility": "highest"
        },
        "apra": {
            "url": "https://www.apra.gov.au/rss.xml",
            "name": "Australian Prudential Regulation Authority",
            "tier": 1,
            "quality_score": 1.0, 
            "language": "en",
            "update_frequency": 60,
            "focus": ["banking_regulation", "prudential_standards", "financial_institutions"],
            "credibility": "highest"
        },
        
        # Tier 2: Major Financial Media (High Quality - Score: 0.8-0.9)
        "afr_companies": {
            "url": "https://www.afr.com/rss/companies",
            "name": "Australian Financial Review - Companies",
            "tier": 2,
            "quality_score": 0.9,
            "language": "en", 
            "update_frequency": 30,
            "focus": ["companies", "earnings", "corporate_governance", "mergers"],
            "credibility": "high"
        },
        "afr_markets": {
            "url": "https://www.afr.com/rss/markets",
            "name": "Australian Financial Review - Markets",
            "tier": 2,
            "quality_score": 0.9,
            "language": "en",
            "update_frequency": 30, 
            "focus": ["markets", "trading", "asx", "commodities"],
            "credibility": "high"
        },
        "afr_banking": {
            "url": "https://www.afr.com/rss/companies/financial-services",
            "name": "Australian Financial Review - Banking & Finance",
            "tier": 2,
            "quality_score": 0.9,
            "language": "en",
            "update_frequency": 30,
            "focus": ["banking", "financial_services", "fintech", "insurance"],
            "credibility": "high"
        },
        "market_index": {
            "url": "https://www.marketindex.com.au/rss",
            "name": "Market Index Australia",
            "tier": 2,
            "quality_score": 0.8,
            "language": "en",
            "update_frequency": 30,
            "focus": ["market_analysis", "stocks", "asx", "financial_data"],
            "credibility": "high"
        },
        "investing_au": {
            "url": "https://au.investing.com/rss/news.rss",
            "name": "Investing.com Australia",
            "tier": 2,
            "quality_score": 0.8,
            "language": "en", 
            "update_frequency": 30,
            "focus": ["markets", "economics", "commodities", "currencies"],
            "credibility": "high"
        },
        "business_spectator": {
            "url": "https://www.businessspectator.com.au/rss",
            "name": "Business Spectator",
            "tier": 2,
            "quality_score": 0.8,
            "language": "en",
            "update_frequency": 45,
            "focus": ["business_news", "market_analysis", "corporate_strategy"],
            "credibility": "high"
        },
        
        # Tier 3: Major News Outlets (Good Quality - Score: 0.6-0.7)
        "abc_business": {
            "url": "https://www.abc.net.au/news/feed/2942460/rss.xml",
            "name": "ABC News - Business",
            "tier": 3,
            "quality_score": 0.7,
            "language": "en",
            "update_frequency": 45,
            "focus": ["business_news", "economy", "employment", "consumer"],
            "credibility": "medium-high"
        },
        "smh_business": {
            "url": "https://www.smh.com.au/rss/business.xml", 
            "name": "Sydney Morning Herald - Business",
            "tier": 3,
            "quality_score": 0.7,
            "language": "en",
            "update_frequency": 45,
            "focus": ["business_news", "corporate", "markets", "property"],
            "credibility": "medium-high"
        },
        "the_age_business": {
            "url": "https://www.theage.com.au/rss/business.xml",
            "name": "The Age - Business",
            "tier": 3,
            "quality_score": 0.7,
            "language": "en",
            "update_frequency": 45,
            "focus": ["business_news", "markets", "corporate", "economy"],
            "credibility": "medium-high"
        },
        "news_com_au": {
            "url": "https://www.news.com.au/finance/rss",
            "name": "News.com.au - Finance",
            "tier": 3,
            "quality_score": 0.6,
            "language": "en",
            "update_frequency": 60,
            "focus": ["finance", "property", "superannuation", "consumer"],
            "credibility": "medium"
        },
        "nine_finance": {
            "url": "https://www.9news.com.au/rss",
            "name": "Nine News - Finance",
            "tier": 3,
            "quality_score": 0.6,
            "language": "en", 
            "update_frequency": 60,
            "focus": ["finance_news", "business", "property", "consumer"],
            "credibility": "medium"
        },
        
        # Tier 4: Specialized Financial Sources (Medium Quality - Score: 0.6)
        "motley_fool_au": {
            "url": "https://www.fool.com.au/rss/",
            "name": "Motley Fool Australia",
            "tier": 4,
            "quality_score": 0.6,
            "language": "en",
            "update_frequency": 60,
            "focus": ["investment_advice", "stock_analysis", "asx_stocks"],
            "credibility": "medium"
        },
        "investor_daily": {
            "url": "https://www.investordaily.com.au/rss",
            "name": "Investor Daily",
            "tier": 4, 
            "quality_score": 0.6,
            "language": "en",
            "update_frequency": 60,
            "focus": ["investment", "financial_planning", "wealth_management"],
            "credibility": "medium"
        },
        "aba_news": {
            "url": "https://www.ausbanking.org.au/rss",
            "name": "Australian Banking Association",
            "tier": 4,
            "quality_score": 0.7,
            "language": "en",
            "update_frequency": 60,
            "focus": ["banking_industry", "policy", "regulation"],
            "credibility": "medium"
        },
        "finsia": {
            "url": "https://www.finsia.com/rss",
            "name": "Financial Services Institute of Australasia",
            "tier": 4,
            "quality_score": 0.6,
            "language": "en",
            "update_frequency": 60,
            "focus": ["financial_services", "professional_development", "industry_trends"],
            "credibility": "medium"
        },
        "smart_investor": {
            "url": "https://www.smartinvestor.com.au/rss",
            "name": "Smart Investor",
            "tier": 4,
            "quality_score": 0.6,
            "language": "en",
            "update_frequency": 60,
            "focus": ["investment_strategy", "market_analysis", "stock_picks"],
            "credibility": "medium"
        }
    },
    
    # ASX-Specific Keywords for Relevance Filtering
    "keywords": {
        "bank_keywords": [
            # Big 4 Banks
            "CBA", "Commonwealth Bank", "ANZ", "NAB", "National Australia Bank", 
            "Westpac", "WBC", "Macquarie", "MQG",
            
            # Banking Terms
            "banking", "bank", "credit", "loan", "mortgage", "deposit", 
            "interest rate", "APRA", "prudential", "capital ratio",
            "home loan", "business banking", "retail banking",
            
            # Australian Banking Specific
            "Big Four", "major bank", "regional bank", "credit union",
            "building society", "ACCC banking", "bank inquiry"
        ],
        
        "financial_keywords": [
            # Market Terms
            "ASX", "Australian Securities Exchange", "All Ordinaries", "ASX 200",
            "shares", "stocks", "equities", "market", "trading", "volume",
            "dividend", "earnings", "profit", "loss", "revenue",
            
            # Economic Terms  
            "RBA", "cash rate", "inflation", "GDP", "unemployment",
            "economic growth", "recession", "recovery", "stimulus",
            "fiscal policy", "monetary policy",
            
            # Financial Services
            "financial services", "wealth management", "superannuation",
            "insurance", "fund management", "asset management",
            "investment banking", "private equity", "hedge fund"
        ],
        
        "sector_keywords": [
            # Financial Sector
            "financial sector", "banking sector", "insurance sector",
            "fintech", "digital banking", "neobank", "challenger bank",
            
            # Regulation
            "ASIC", "APRA", "ACCC", "financial regulation", "compliance",
            "Basel III", "open banking", "royal commission",
            
            # Technology & Innovation
            "digital transformation", "artificial intelligence", "blockchain",
            "cybersecurity", "data analytics", "cloud computing",
            "mobile banking", "online banking", "digital payments"
        ],
        
        "sentiment_keywords": {
            "positive": [
                "profit", "growth", "expansion", "record", "strong", "robust",
                "improvement", "upgrade", "bullish", "optimistic", "confident",
                "dividend increase", "beat expectations", "outperform"
            ],
            "negative": [
                "loss", "decline", "fall", "drop", "weak", "poor", "disappointing",
                "downgrade", "bearish", "pessimistic", "concern", "worry",
                "dividend cut", "miss expectations", "underperform", "investigation"
            ],
            "neutral": [
                "stable", "unchanged", "maintain", "steady", "consistent",
                "meets expectations", "in line", "as expected"
            ]
        }
    }
}

# News Source Configurations by Tier
TIER_CONFIGURATIONS = {
    1: {
        "name": "Government & Central Bank",
        "description": "Official government and central bank sources",
        "quality_score_range": [0.95, 1.0],
        "update_frequency": 60,
        "reliability": "highest",
        "bias_level": "minimal",
        "fact_checking": "excellent"
    },
    2: {
        "name": "Major Financial Media", 
        "description": "Established financial news organizations",
        "quality_score_range": [0.8, 0.9],
        "update_frequency": 30,
        "reliability": "high",
        "bias_level": "low",
        "fact_checking": "good"
    },
    3: {
        "name": "General Business News",
        "description": "Major news outlets with business coverage", 
        "quality_score_range": [0.6, 0.7],
        "update_frequency": 45,
        "reliability": "medium-high",
        "bias_level": "medium",
        "fact_checking": "adequate"
    },
    4: {
        "name": "Specialized Financial",
        "description": "Specialized financial and investment sources",
        "quality_score_range": [0.5, 0.6],
        "update_frequency": 60,
        "reliability": "medium", 
        "bias_level": "medium-high",
        "fact_checking": "variable"
    }
}

# Regional News Preferences for Australia
REGIONAL_PREFERENCES = {
    "language": "en",
    "timezone": "Australia/Sydney",
    "business_hours": {
        "start": "09:00",
        "end": "17:00"
    },
    "market_focus": "asx",
    "currency_focus": "AUD",
    "regulatory_focus": ["ASIC", "APRA", "RBA", "Treasury"],
    "major_companies": [
        "CBA", "ANZ", "NAB", "WBC", "MQG", "BHP", "RIO", "CSL", "WOW", "TLS"
    ]
}

# News Processing Configuration for ASX
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
    }
}

def get_news_sources_by_tier(tier: int) -> Dict[str, Any]:
    """Get all news sources for a specific tier"""
    return {
        source_id: source_config 
        for source_id, source_config in NEWS_SOURCES["rss_feeds"].items()
        if source_config["tier"] == tier
    }

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
    tier_weights = {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.4}
    
    return tier_weights.get(tier, 0.2) * quality_score

def get_update_schedule() -> Dict[str, int]:
    """Get update frequency schedule for all sources"""
    schedule = {}
    for source_id, source_config in NEWS_SOURCES["rss_feeds"].items():
        schedule[source_id] = source_config["update_frequency"]
    return schedule
