# Europe (EURONEXT) Configuration
# For major European financial markets including France, Germany, Netherlands

EUROPE_CONFIG = {
    "region": {
        "name": "Europe",
        "code": "eu",
        "description": "European Union - EURONEXT and major European exchanges",
        "currency": "EUR",
        "timezone": "Europe/Paris"
    },
    
    "market_data": {
        "symbols": {
            # Major European Banks
            "big4_banks": [
                "BNP.PA",   # BNP Paribas (France)
                "ACA.PA",   # Crédit Agricole (France)
                "GLE.PA",   # Société Générale (France)
                "DBK.DE"    # Deutsche Bank (Germany)
            ],
            
            # Additional major financial institutions
            "major_financial": [
                "SAP.DE",    # SAP (Germany)
                "ASML.AS",   # ASML (Netherlands)
                "OR.PA",     # L'Oréal (France)
                "MC.PA",     # LVMH (France)
                "SAN.PA",    # Sanofi (France)
                "AIR.PA",    # Airbus (France)
                "NESN.SW",   # Nestlé (Switzerland)
                "UG.PA",     # Peugeot (France)
                "VOW3.DE",   # Volkswagen (Germany)
                "ALV.DE"     # Allianz (Germany)
            ],
            
            # European Indices
            "market_indices": [
                "^FCHI",     # CAC 40 (France)
                "^GDAXI",    # DAX (Germany)
                "^AEX",      # AEX (Netherlands)
                "^BEL20",    # BEL 20 (Belgium)
                "^STOXX50E"  # EURO STOXX 50
            ]
        },
        
        "trading_hours": {
            "market_open": "09:00",
            "market_close": "17:30",
            "timezone": "Europe/Paris",
            "trading_days": [0, 1, 2, 3, 4],  # Monday-Friday
            "holidays": [
                "2024-01-01",  # New Year's Day
                "2024-03-29",  # Good Friday
                "2024-04-01",  # Easter Monday
                "2024-05-01",  # Labour Day
                "2024-05-09",  # Ascension Day
                "2024-05-20",  # Whit Monday
                "2024-07-14",  # Bastille Day (France)
                "2024-08-15",  # Assumption of Mary
                "2024-10-03",  # German Unity Day
                "2024-11-01",  # All Saints' Day
                "2024-12-25",  # Christmas Day
                "2024-12-26"   # Boxing Day
            ]
        },
        
        "data_sources": {
            "primary_api": "alpha_vantage",
            "backup_apis": ["finnhub", "yahoo_finance", "euronext_api"],
            "real_time_provider": "euronext",
            "currency_api": "ecb_rates"
        },
        
        "cache_settings": {
            "price_cache_ttl": 300,      # 5 minutes during trading
            "daily_cache_ttl": 3600,     # 1 hour for daily data
            "historical_cache_ttl": 86400 # 24 hours for historical
        }
    },
    
    "sentiment": {
        "news_sources": {
            "financial_news": [
                "https://www.lemonde.fr/economie/rss_full.xml",
                "https://www.lefigaro.fr/rss/figaro_economie.xml",
                "https://feeds.reuters.com/reuters/FReuropefinance",
                "https://www.bloomberg.com/feeds/bbnews.rss",
                "https://www.handelsblatt.com/contentexport/feed/schlagzeilen",
                "https://www.ft.com/rss/companies/european-equities"
            ],
            
            "bank_specific": [
                "https://www.bnpparibas.com/rss/group-news",
                "https://www.credit-agricole.com/rss/actualites",
                "https://www.societegenerale.com/rss/news",
                "https://www.db.com/newsroom/rss.xml"
            ],
            
            "market_analysis": [
                "https://www.boursorama.com/rss/",
                "https://www.zonebourse.com/rss/",
                "https://www.boersen-zeitung.de/rss/nachrichten.xml",
                "https://www.euronext.com/rss/news"
            ]
        },
        
        "keywords": {
            "positive": [
                "bénéfice", "croissance", "hausse", "amélioration", "optimiste",
                "dividende", "résultats solides", "expansion", "fusion",
                "acquisition", "perspectives positives", "recommandation d'achat",
                "reprise", "résiliant", "robuste", "dépasse les attentes",
                "profit", "growth", "bullish", "upgrade", "outperform"
            ],
            
            "negative": [
                "perte", "déclin", "baisse", "dégradation", "pessimiste",
                "réduction dividende", "résultats décevants", "suppressions d'emplois",
                "réglementaire", "amende", "scandale", "recommandation de vente",
                "récession", "volatil", "incertitude", "objectifs manqués",
                "loss", "decline", "bearish", "downgrade", "underperform"
            ],
            
            "banking_specific": {
                "positive": [
                    "marge d'intérêt", "croissance crédit", "qualité crédit",
                    "ratio capital", "tier 1", "test de stress réussi",
                    "banque numérique", "partenariat fintech", "économies"
                ],
                "negative": [
                    "créances douteuses", "pertes crédit", "conformité",
                    "blanchiment argent", "capital réglementaire", "contentieux",
                    "risque opérationnel", "risque conduite"
                ]
            }
        },
        
        "big4_symbols": ["BNP.PA", "ACA.PA", "GLE.PA", "DBK.DE"],
        
        "cache_settings": {
            "sentiment_cache_ttl": 1800,  # 30 minutes
            "news_cache_ttl": 900         # 15 minutes
        }
    },
    
    "prediction": {
        "ml_config": {
            "model_types": ["ensemble", "lstm", "xgboost"],
            "features": [
                "technical_indicators", "sentiment_score", "volume_analysis",
                "market_correlation", "economic_indicators", "eur_strength",
                "ecb_policy", "political_stability"
            ],
            "training_period": 252,  # Trading days (1 year)
            "prediction_horizon": 5,  # 5 trading days
            "retrain_frequency": 30   # Days
        },
        
        "thresholds": {
            "buy_threshold": 0.65,
            "sell_threshold": 0.35,
            "strong_buy": 0.80,
            "strong_sell": 0.20
        },
        
        "risk_management": {
            "max_position_size": 0.1,    # 10% of portfolio
            "stop_loss": 0.05,           # 5%
            "take_profit": 0.15,         # 15%
            "diversification_limit": 0.4  # Max 40% in financial sector
        }
    },
    
    "paper_trading": {
        "initial_capital": 100000,  # €100,000
        "currency": "EUR",
        "commission": {
            "rate": 0.001,      # 0.1% (typical European broker)
            "minimum": 3.0,     # €3 minimum
            "maximum": 30.0     # €30 maximum
        },
        
        "trading_rules": {
            "max_daily_trades": 20,
            "max_position_value": 20000,  # €20,000 per position
            "allowed_order_types": ["market", "limit", "stop_loss"],
            "settlement_period": 2        # T+2 settlement
        }
    },
    
    "alerts": {
        "price_movement": {
            "threshold": 0.05,    # 5% price movement
            "timeframe": "1h"     # Within 1 hour
        },
        
        "volume_spike": {
            "multiplier": 3.0,    # 3x average volume
            "timeframe": "30m"    # Within 30 minutes
        },
        
        "sentiment_change": {
            "threshold": 0.3,     # 30% sentiment change
            "timeframe": "2h"     # Within 2 hours
        }
    },
    
    "regulatory": {
        "data_retention": 2555,   # 7 years in days (MiFID II requirement)
        "reporting_frequency": "daily",
        "compliance_checks": ["MiFID_II", "EMIR", "GDPR", "MAR"],
        "audit_trail": True
    },
    
    "localization": {
        "languages": ["fr", "de", "nl", "en"],
        "default_language": "en",
        "currency_format": "€{amount:,.2f}",
        "date_format": "DD/MM/YYYY",
        "time_format": "HH:mm"
    }
}
