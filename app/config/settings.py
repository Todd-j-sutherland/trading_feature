"""
Enhanced configuration settings for Trading Analysis System
Centralized configuration with environment variable support and validation
"""

import os
from datetime import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Centralized configuration for the trading analysis system"""
    
    # Application Info
    APP_NAME = "Trading Analysis System"
    VERSION = "2.0.0"
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Paths - Updated to use /root/test/data as primary data location
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = Path('/root/test/data')  # Changed to consolidated data location
    LOGS_DIR = BASE_DIR / 'logs'
    REPORTS_DIR = BASE_DIR / 'reports'
    CACHE_DIR = DATA_DIR / 'cache'
    MODELS_DIR = DATA_DIR / 'ml_models'
    
    # Ensure directories exist
    for directory in [DATA_DIR, LOGS_DIR, REPORTS_DIR, CACHE_DIR, MODELS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # ASX Bank Symbols (Primary Focus)
    BANK_SYMBOLS = [
        'CBA.AX',  # Commonwealth Bank
        'WBC.AX',  # Westpac
        'ANZ.AX',  # ANZ
        'NAB.AX',  # National Australia Bank
        'MQG.AX',  # Macquarie Group
        'SUN.AX',  # Suncorp Group
        'QBE.AX'   # QBE Insurance Group
    ]

    BANK_NAMES = {
        'CBA.AX': 'Commonwealth Bank',
        'WBC.AX': 'Westpac',
        'ANZ.AX': 'ANZ',
        'NAB.AX': 'National Australia Bank',
        'MQG.AX': 'Macquarie Group',
        'SUN.AX': 'Suncorp Group',
        'QBE.AX': 'QBE Insurance Group'
    }
    
    # Extended financial symbols for broader analysis
    EXTENDED_SYMBOLS = [
        'BEN.AX',  # Bendigo Bank
        'BOQ.AX',  # Bank of Queensland
        'IFL.AX',  # IOOF Holdings
        'HUB.AX'   # HUB24
    ]
    
    # Market indices for context
    MARKET_INDICES = {
        'ASX200': '^AXJO',
        'ALL_ORDS': '^AORD',
        'FINANCIALS': '^AXFJ',
        'BANKS': '^AXBK'
    }
    
    # Trading Hours (Sydney/Melbourne time)
    MARKET_OPEN = time(10, 0)    # 10:00 AM AEST/AEDT
    MARKET_CLOSE = time(16, 0)   # 4:00 PM AEST/AEDT
    PRE_MARKET = time(7, 0)      # 7:00 AM
    POST_MARKET = time(17, 0)    # 5:00 PM
    
    # Analysis Parameters
    DEFAULT_ANALYSIS_PERIOD = os.getenv('DEFAULT_ANALYSIS_PERIOD', '3mo')
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '70'))
    RISK_TOLERANCE = os.getenv('RISK_TOLERANCE', 'medium')  # low, medium, high
    
    # Enhanced ML Configuration
    ML_CONFIG = {
        'models': {
            'sentiment_ensemble': {
                'enabled': True,
                'models': ['transformers', 'statistical', 'lexicon'],
                'weights': [0.5, 0.3, 0.2],
                'confidence_threshold': 0.7
            },
            'price_prediction': {
                'enabled': True,
                'lookback_periods': [5, 10, 20],
                'prediction_horizon': 5,
                'ensemble_size': 3
            },
            'risk_assessment': {
                'enabled': True,
                'volatility_window': 20,
                'var_confidence': 0.95,
                'stress_test_scenarios': 5
            }
        },
        'training': {
            'min_samples': 100,
            'validation_split': 0.2,
            'retrain_frequency_days': 7,
            'auto_retrain': True
        }
    }
    
    # Technical Analysis Settings
    TECHNICAL_INDICATORS = {
        'RSI': {'period': 14, 'overbought': 70, 'oversold': 30},
        'MACD': {'fast': 12, 'slow': 26, 'signal': 9},
        'BB': {'period': 20, 'std': 2},
        'SMA': {'periods': [20, 50, 200]},
        'EMA': {'periods': [12, 26]},
        'ATR': {'period': 14},
        'VOLUME': {'ma_period': 20},
        'VWAP': {'enabled': True},
        'STOCH': {'k_period': 14, 'smooth_k': 3, 'smooth_d': 3}
    }
    
    # Enhanced Risk Management
    RISK_PARAMETERS = {
        'max_position_size': float(os.getenv('MAX_POSITION_SIZE', '0.25')),
        'stop_loss_atr_multiplier': float(os.getenv('STOP_LOSS_ATR', '2.0')),
        'take_profit_ratio': float(os.getenv('TAKE_PROFIT_RATIO', '2.0')),
        'max_daily_loss': float(os.getenv('MAX_DAILY_LOSS', '0.06')),
        'max_open_positions': int(os.getenv('MAX_OPEN_POSITIONS', '3')),
        'correlation_limit': 0.7,  # Max correlation between positions
        'sector_limit': 0.5,       # Max allocation to single sector
        'var_limit': 0.02          # 2% daily VaR limit
    }
    
    # Alert and Signal Thresholds
    ALERT_THRESHOLDS = {
        'sentiment': {
            'strong_positive': 80,
            'positive': 60,
            'neutral_high': 55,
            'neutral_low': 45,
            'negative': 40,
            'strong_negative': 20
        },
        'technical': {
            'strong_buy': 75,
            'buy': 60,
            'hold_high': 55,
            'hold_low': 45,
            'sell': 40,
            'strong_sell': 25
        },
        'risk': {
            'high_volatility': 0.03,  # 3% daily volatility
            'unusual_volume': 2.0,    # 2x average volume
            'price_gap': 0.05,        # 5% price gap
            'correlation_spike': 0.8   # High correlation warning
        }
    }
    
    # Enhanced Sentiment Analysis Configuration
    SENTIMENT_CONFIG = {
        'weights': {
            'news_sentiment': 0.4,
            'technical_momentum': 0.3,
            'market_sentiment': 0.2,
            'fundamental_score': 0.1
        },
        'sources': {
            'news_weight': 0.6,
            'social_weight': 0.2,
            'analyst_weight': 0.2
        },
        'time_decay': {
            'news_half_life_hours': 24,
            'social_half_life_hours': 6,
            'technical_half_life_hours': 48
        },
        'confidence_factors': {
            'min_news_items': 3,
            'min_social_mentions': 10,
            'source_diversity_bonus': 1.2
        }
    }
    
    # Data Sources Configuration
    DATA_SOURCES = {
        'market_data': {
            'primary': 'yfinance',
            'backup': 'alpha_vantage',
            'update_frequency_minutes': 15
        },
        'news': {
            'sources': ['abc', 'afr', 'reuters', 'smh'],
            'update_frequency_minutes': 30,
            'sentiment_analysis': True
        },
        'economic': {
            'sources': ['rba', 'abs', 'asx'],
            'update_frequency_hours': 6
        }
    }
    
    # Comprehensive News Sources (Australian Focus)
    NEWS_SOURCES = {
        'rss_feeds': {
            # Tier 1: Government & Central Bank
            'rba': 'https://www.rba.gov.au/rss/rss-cb.xml',
            'abs': 'https://www.abs.gov.au/rss.xml',
            'treasury': 'https://treasury.gov.au/rss',
            'apra': 'https://www.apra.gov.au/rss.xml',
            
            # Tier 2: Major Financial Media
            'afr_companies': 'https://www.afr.com/rss/companies',
            'afr_markets': 'https://www.afr.com/rss/markets',
            'market_index': 'https://www.marketindex.com.au/rss/asx-news',
            'investing_au': 'https://au.investing.com/rss/news_301.rss',
            'business_news': 'https://www.businessnews.com.au/rssfeed/latest.rss',
            
            # Tier 3: Major News Outlets
            'abc_business': 'https://www.abc.net.au/news/feed/2942460/rss.xml',
            'smh_business': 'https://www.smh.com.au/rss/business.xml',
            'the_age_business': 'https://www.theage.com.au/rss/business.xml',
            'news_com_au': 'https://www.news.com.au/content-feeds/latest-news-business/',
            
            # Tier 4: Specialized Financial
            'motley_fool_au': 'https://www.fool.com.au/feed/',
            'investor_daily': 'https://www.investordaily.com.au/feed/',
            'aba_news': 'https://ausbanking.org.au/feed/',
            'finsia': 'https://www.finsia.com/insights/feed'
        },
        'keywords': {
            'banking': ['bank', 'banking', 'finance', 'credit', 'loan', 'mortgage'],
            'regulation': ['APRA', 'ASIC', 'regulation', 'compliance', 'capital'],
            'monetary': ['RBA', 'interest rate', 'cash rate', 'monetary policy'],
            'market': ['ASX', 'share price', 'dividend', 'earnings', 'profit']
        }
    }
    
    # Enhanced Bank Profiles
    BANK_PROFILES = {
        'CBA.AX': {
            'name': 'Commonwealth Bank',
            'sector_weight': 0.30,
            'market_cap_tier': 'large',
            'dividend_months': [2, 8],
            'financial_year_end': 6,
            'primary_segments': ['retail', 'business', 'institutional'],
            'geographic_focus': ['australia', 'new_zealand'],
            'key_metrics': ['net_interest_margin', 'cost_to_income', 'credit_losses']
        },
        'WBC.AX': {
            'name': 'Westpac Banking Corporation',
            'sector_weight': 0.20,
            'market_cap_tier': 'large',
            'dividend_months': [5, 11],
            'financial_year_end': 9,
            'primary_segments': ['consumer', 'business', 'specialist'],
            'geographic_focus': ['australia', 'new_zealand'],
            'key_metrics': ['net_interest_margin', 'cost_to_income', 'credit_losses']
        },
        'ANZ.AX': {
            'name': 'Australia and New Zealand Banking Group',
            'sector_weight': 0.20,
            'market_cap_tier': 'large',
            'dividend_months': [5, 11],
            'financial_year_end': 9,
            'primary_segments': ['australia_retail', 'institutional', 'new_zealand'],
            'geographic_focus': ['australia', 'new_zealand', 'pacific'],
            'key_metrics': ['net_interest_margin', 'cost_to_income', 'credit_losses']
        },
        'NAB.AX': {
            'name': 'National Australia Bank',
            'sector_weight': 0.20,
            'market_cap_tier': 'large',
            'dividend_months': [5, 11],
            'financial_year_end': 9,
            'primary_segments': ['personal', 'business', 'corporate'],
            'geographic_focus': ['australia'],
            'key_metrics': ['net_interest_margin', 'cost_to_income', 'credit_losses']
        },
        'MQG.AX': {
            'name': 'Macquarie Group Limited',
            'sector_weight': 0.08,
            'market_cap_tier': 'large',
            'dividend_months': [6, 12],
            'financial_year_end': 3,
            'primary_segments': ['investment_banking', 'asset_management', 'retail'],
            'geographic_focus': ['global'],
            'key_metrics': ['fee_income', 'trading_revenue', 'assets_under_management']
        },
        'SUN.AX': {
            'name': 'Suncorp Group Limited',
            'sector_weight': 0.02,
            'market_cap_tier': 'mid',
            'dividend_months': [3, 9],
            'financial_year_end': 6,
            'primary_segments': ['banking', 'insurance'],
            'geographic_focus': ['australia'],
            'key_metrics': ['net_interest_margin', 'insurance_margin', 'cost_to_income']
        }
    }
    
    # Cache and Performance Settings
    CACHE_SETTINGS = {
        'duration_minutes': int(os.getenv('CACHE_DURATION_MINUTES', '15')),
        'max_size_mb': int(os.getenv('MAX_CACHE_SIZE_MB', '100')),
        'cleanup_frequency_hours': 24,
        'enable_redis': os.getenv('REDIS_URL') is not None
    }
    
    # Logging Configuration
    LOGGING_CONFIG = {
        'level': os.getenv('LOG_LEVEL', 'INFO'),
        'file': str(LOGS_DIR / 'trading_analysis.log'),
        'max_file_size_mb': 50,
        'backup_count': 5,
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }
    
    # API Configuration (optional external services)
    API_CONFIG = {
        'alpha_vantage': {
            'key': os.getenv('ALPHA_VANTAGE_KEY', ''),
            'enabled': bool(os.getenv('ALPHA_VANTAGE_KEY'))
        },
        'news_api': {
            'key': os.getenv('NEWS_API_KEY', ''),
            'enabled': bool(os.getenv('NEWS_API_KEY'))
        },
        'twitter': {
            'bearer_token': os.getenv('TWITTER_BEARER_TOKEN', ''),
            'enabled': bool(os.getenv('TWITTER_BEARER_TOKEN'))
        }
    }
    
    # Notification Settings
    NOTIFICATION_CONFIG = {
        'discord': {
            'webhook_url': os.getenv('DISCORD_WEBHOOK_URL', ''),
            'enabled': bool(os.getenv('DISCORD_WEBHOOK_URL'))
        },
        'telegram': {
            'bot_token': os.getenv('TELEGRAM_BOT_TOKEN', ''),
            'chat_id': os.getenv('TELEGRAM_CHAT_ID', ''),
            'enabled': bool(os.getenv('TELEGRAM_BOT_TOKEN'))
        },
        'email': {
            'smtp_server': os.getenv('SMTP_SERVER', ''),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'username': os.getenv('EMAIL_USERNAME', ''),
            'password': os.getenv('EMAIL_PASSWORD', ''),
            'enabled': bool(os.getenv('EMAIL_USERNAME'))
        }
    }
    
    # Dashboard Configuration
    DASHBOARD_CONFIG = {
        'host': os.getenv('DASHBOARD_HOST', 'localhost'),
        'port': int(os.getenv('DASHBOARD_PORT', '8501')),
        'auto_refresh_seconds': int(os.getenv('AUTO_REFRESH_SECONDS', '300')),
        'theme': os.getenv('DASHBOARD_THEME', 'dark'),
        'charts_library': 'plotly'
    }
    
    # Backtesting Configuration
    BACKTEST_CONFIG = {
        'initial_capital': float(os.getenv('BACKTEST_CAPITAL', '100000')),
        'commission_rate': float(os.getenv('COMMISSION_RATE', '0.001')),
        'slippage_rate': float(os.getenv('SLIPPAGE_RATE', '0.0005')),
        'benchmark': '^AXJO',
        'rebalance_frequency': 'monthly'
    }
    
    @classmethod
    def get_bank_info(cls, symbol: str) -> Dict[str, Any]:
        """Get comprehensive bank information"""
        return cls.BANK_PROFILES.get(symbol, {})
    
    @classmethod
    def get_bank_name(cls, symbol: str) -> str:
        """Get bank display name"""
        return cls.BANK_PROFILES.get(symbol, {}).get('name', symbol)
    
    @classmethod
    def is_dividend_month(cls, symbol: str) -> bool:
        """Check if current month is dividend month for symbol"""
        from datetime import datetime
        current_month = datetime.now().month
        div_months = cls.BANK_PROFILES.get(symbol, {}).get('dividend_months', [])
        return current_month in div_months
    
    @classmethod
    def get_risk_parameters(cls) -> Dict[str, float]:
        """Get risk parameters based on risk tolerance"""
        base_params = cls.RISK_PARAMETERS.copy()
        
        risk_multipliers = {
            'low': {'position_size': 0.6, 'stop_loss': 0.8, 'var_limit': 0.7},
            'medium': {'position_size': 1.0, 'stop_loss': 1.0, 'var_limit': 1.0},
            'high': {'position_size': 1.4, 'stop_loss': 1.2, 'var_limit': 1.3}
        }
        
        multiplier = risk_multipliers.get(cls.RISK_TOLERANCE, risk_multipliers['medium'])
        
        return {
            'max_position_size': base_params['max_position_size'] * multiplier['position_size'],
            'stop_loss_atr_multiplier': base_params['stop_loss_atr_multiplier'] * multiplier['stop_loss'],
            'var_limit': base_params['var_limit'] * multiplier['var_limit'],
            **{k: v for k, v in base_params.items() if k not in ['max_position_size', 'stop_loss_atr_multiplier', 'var_limit']}
        }
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate configuration and return any issues"""
        issues = []
        
        # Check required directories
        for dir_name, dir_path in [
            ('Data', cls.DATA_DIR),
            ('Logs', cls.LOGS_DIR),
            ('Reports', cls.REPORTS_DIR)
        ]:
            if not dir_path.exists():
                issues.append(f"Missing {dir_name} directory: {dir_path}")
        
        # Validate risk parameters
        if not 0 < cls.RISK_PARAMETERS['max_position_size'] <= 1:
            issues.append("Invalid max_position_size - must be between 0 and 1")
        
        if cls.RISK_PARAMETERS['max_daily_loss'] >= 0.2:
            issues.append("Max daily loss seems too high (>=20%)")
        
        # Check symbol availability
        if not cls.BANK_SYMBOLS:
            issues.append("No bank symbols configured")
        
        return issues
