# Multi-Region Trading Configuration System

## Overview

This multi-region configuration system enables the trading platform to operate across different financial markets including ASX (Australia), NYSE/NASDAQ (USA), LSE (UK), TSE (Japan), and others.

## Architecture

### Configuration Structure
```
app/config/regions/
├── base_config.py          # Common configuration shared across all regions
├── asx/                    # Australia configuration
│   ├── market_config.py    # ASX-specific market configuration
│   ├── news_sources.py     # Australian financial news sources
│   ├── symbols.py          # ASX stock symbols and bank profiles
│   └── ml_config.yaml      # Australia-specific ML configuration
├── usa/                    # United States configuration  
│   ├── market_config.py    # NYSE/NASDAQ-specific configuration
│   ├── news_sources.py     # US financial news sources
│   ├── symbols.py          # US stock symbols and bank profiles
│   └── ml_config.yaml      # USA-specific ML configuration
├── uk/                     # United Kingdom configuration
│   ├── market_config.py    # LSE-specific configuration
│   ├── news_sources.py     # UK financial news sources
│   ├── symbols.py          # LSE stock symbols and bank profiles
│   └── ml_config.yaml      # UK-specific ML configuration
└── config_manager.py       # Multi-region configuration manager
```

## Regional Configuration Components

### 1. Base Configuration (base_config.py)
Common settings shared across all regions:
- Technical indicator base parameters
- ML model base configurations
- Common risk assessment parameters
- Universal data quality thresholds

### 2. Market-Specific Configuration (market_config.py)
Region-specific market settings:
- Trading hours and timezone
- Market holidays calendar
- Currency and exchange information
- Regulatory requirements
- Settlement cycles

### 3. News Sources Configuration (news_sources.py)  
Region-specific financial news sources:
- Local financial media outlets
- Government/regulatory sources
- Regional business news
- Language-specific sources
- Quality scoring adapted to region

### 4. Symbols Configuration (symbols.py)
Region-specific financial instruments:
- Major bank symbols
- Financial sector companies
- Market indices
- Exchange-specific symbol formats
- Company profiles and metadata

### 5. ML Configuration (ml_config.yaml)
Region-specific machine learning settings:
- Market-specific feature engineering
- Regional sentiment analysis models
- Local regulatory factors
- Currency-specific volatility models

## Benefits

1. **Scalability**: Easy addition of new markets
2. **Maintainability**: Isolated regional configurations
3. **Flexibility**: Region-specific customization
4. **Performance**: Load only required regional configs
5. **Compliance**: Region-specific regulatory adherence

## Usage Examples

```python
# Load ASX configuration
asx_config = ConfigManager().get_region_config('asx')

# Load USA configuration  
usa_config = ConfigManager().get_region_config('usa')

# Get multi-region news sources
news_sources = ConfigManager().get_all_news_sources(['asx', 'usa'])

# Region-specific market data
asx_data = MarketDataService('asx').get_bank_data()
usa_data = MarketDataService('usa').get_bank_data()
```

## Implementation Strategy

1. **Phase 1**: Extract current ASX configuration into regional structure
2. **Phase 2**: Create USA configuration template and populate
3. **Phase 3**: Build multi-region configuration manager
4. **Phase 4**: Update microservices for multi-region support
5. **Phase 5**: Add additional regions (UK, Japan, etc.)

## Configuration Loading Priority

1. **Region-specific configuration** (highest priority)
2. **Base configuration** (fallback for missing settings)
3. **Default values** (hardcoded fallbacks)

This ensures robust operation even with incomplete regional configurations.
