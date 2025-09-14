# Complete Multi-Region Microservices Implementation Guide

## Overview

This document provides comprehensive documentation for the complete multi-region microservices trading system, capable of operating across multiple global financial markets including ASX (Australia), USA, UK (LSE), and Europe (EURONEXT).

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Regional Configurations](#regional-configurations)
3. [Microservices Documentation](#microservices-documentation)
4. [Configuration Management](#configuration-management)
5. [Multi-Region Usage Examples](#multi-region-usage-examples)
6. [Deployment Guide](#deployment-guide)
7. [Testing & Validation](#testing--validation)
8. [Monitoring & Operations](#monitoring--operations)
9. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Multi-Region Trading System                  │
├─────────────────────────────────────────────────────────────────┤
│ Configuration Layer                                             │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐     │
│ │ ConfigManager   │ │ Base Config     │ │ Region Configs  │     │
│ │ - Region Switch │ │ - Common        │ │ - ASX/USA/UK/EU │     │
│ │ - Config Merge  │ │ - Defaults      │ │ - Market-Specific│     │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘     │
├─────────────────────────────────────────────────────────────────┤
│ Microservices Layer                                             │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐     │
│ │ Prediction      │ │ Market Data     │ │ Sentiment       │     │
│ │ - ML Models     │ │ - Price Feed    │ │ - News Analysis │     │
│ │ - Multi-Region  │ │ - Volume Data   │ │ - Regional News │     │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘     │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐     │
│ │ Paper Trading   │ │ Scheduler       │ │ ML Training     │     │
│ │ - Broker Sim    │ │ - Market Hours  │ │ - Model Update  │     │
│ │ - Portfolio     │ │ - Time Zones    │ │ - Regional Data │     │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘     │
├─────────────────────────────────────────────────────────────────┤
│ Communication Layer                                             │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐     │
│ │ Unix Sockets    │ │ Redis Events    │ │ BaseService     │     │
│ │ - IPC           │ │ - Pub/Sub       │ │ - Health Check  │     │
│ │ - Low Latency   │ │ - Event Stream  │ │ - Metrics       │     │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features

- **Multi-Region Support**: ASX, USA, UK, Europe markets
- **Dynamic Region Switching**: Runtime configuration changes
- **Intelligent Configuration Merging**: Base + Regional configs
- **Market-Aware Scheduling**: Timezone and market hours awareness
- **Regional Data Isolation**: Separate caches and models per region
- **Backward Compatibility**: Legacy system compatibility

---

## Regional Configurations

### Available Regions

| Region | Code | Markets | Currency | Timezone | Big 4 Banks |
|--------|------|---------|----------|----------|-------------|
| **Australia** | `asx` | ASX | AUD | Australia/Sydney | CBA, ANZ, NAB, WBC |
| **USA** | `usa` | NYSE, NASDAQ | USD | America/New_York | JPM, BAC, WFC, C |
| **UK** | `uk` | LSE (FTSE) | GBP | Europe/London | LLOY, BARC, RBS, HSBA |
| **Europe** | `eu` | EURONEXT | EUR | Europe/Paris | BNP, ACA, GLE, DBK |

### Region Configuration Structure

Each region contains:

```python
REGION_CONFIG = {
    "region": {
        "name": "Region Name",
        "code": "region_code", 
        "currency": "CURRENCY",
        "timezone": "Timezone/Location"
    },
    "market_data": {
        "symbols": {...},           # Region-specific symbols
        "trading_hours": {...},     # Market hours and holidays
        "data_sources": {...}       # APIs and providers
    },
    "sentiment": {
        "news_sources": {...},      # Regional news feeds
        "keywords": {...},          # Language-specific keywords
        "big4_symbols": [...]       # Major banks for sentiment
    },
    "prediction": {
        "ml_config": {...},         # ML model settings
        "thresholds": {...},        # Buy/sell thresholds
        "risk_management": {...}    # Risk parameters
    },
    "paper_trading": {
        "initial_capital": 100000,  # Starting capital
        "currency": "CURRENCY",     # Trading currency
        "commission": {...}         # Broker commission structure
    }
}
```

---

## Microservices Documentation

### 1. Configuration Manager Service

**Purpose**: Central configuration management with multi-region support

**Key Features**:
- Dynamic region switching
- Configuration caching and merging
- Region discovery and validation
- Legacy compatibility

**API Methods**:
```python
# Switch active region
await config_manager.set_region("usa")

# Get current configuration
config = config_manager.get_config()

# Get available regions
regions = config_manager.get_available_regions()

# Merge base + regional configurations
merged = config_manager.merge_configs(base_config, region_config)
```

**Usage Example**:
```python
from app.config.regions.config_manager import ConfigManager

# Initialize with default region
config_mgr = ConfigManager(region="asx")

# Switch to USA market
await config_mgr.set_region("usa")

# Get USA-specific symbols
usa_symbols = config_mgr.get_config()["market_data"]["symbols"]["big4_banks"]
# Result: ["JPM", "BAC", "WFC", "C"]
```

### 2. Prediction Service

**Purpose**: Multi-region ML predictions for stock movements

**Key Features**:
- Region-specific ML models
- Dynamic region switching with restoration
- Per-region prediction caching
- Batch and single predictions

**API Methods**:
```python
# Generate predictions for current region
await prediction_service.generate_predictions(symbols=["CBA.AX"])

# Generate predictions for specific region
await prediction_service.generate_predictions(symbols=["JPM"], region="usa")

# Switch prediction service region
await prediction_service.switch_region("uk")

# Get buy rate for current region
await prediction_service.get_buy_rate()
```

**Multi-Region Usage**:
```python
# Compare predictions across regions
asx_predictions = await prediction_service.generate_predictions(
    symbols=["CBA.AX", "ANZ.AX"], 
    region="asx"
)

usa_predictions = await prediction_service.generate_predictions(
    symbols=["JPM", "BAC"], 
    region="usa"
)

uk_predictions = await prediction_service.generate_predictions(
    symbols=["LLOY.L", "BARC.L"], 
    region="uk"
)
```

### 3. Market Data Service

**Purpose**: Multi-region market data collection and caching

**Key Features**:
- Region-specific data sources
- Market hours awareness
- Currency conversion
- Real-time and historical data

**API Methods**:
```python
# Get market data for current region
await market_data_service.get_market_data("CBA.AX")

# Get market data for specific region  
await market_data_service.get_market_data("JPM", region="usa")

# Check if market is open
await market_data_service.is_market_open(region="uk")

# Get trading hours
await market_data_service.get_trading_hours(region="eu")
```

**Region-Specific Example**:
```python
# Get ASX market data during Australian trading hours
asx_data = await market_data_service.get_market_data("CBA.AX", region="asx")

# Get NYSE data during US trading hours
nyse_data = await market_data_service.get_market_data("JPM", region="usa")

# Check market status across regions
market_status = {}
for region in ["asx", "usa", "uk", "eu"]:
    market_status[region] = await market_data_service.is_market_open(region=region)
```

### 4. Sentiment Analysis Service

**Purpose**: Multi-region news sentiment analysis

**Key Features**:
- Regional news sources
- Multi-language keyword analysis
- Regional sentiment aggregation
- Big 4 banks sentiment per region

**API Methods**:
```python
# Analyze sentiment for current region
await sentiment_service.analyze_sentiment("CBA.AX")

# Analyze sentiment for specific region
await sentiment_service.analyze_sentiment("JPM", region="usa")

# Get Big 4 sentiment for region
await sentiment_service.get_big4_sentiment(region="uk")

# Get market sentiment for region
await sentiment_service.get_market_sentiment(region="eu")
```

**Multi-Language Support**:
```python
# European sentiment with French/German keywords
eu_sentiment = await sentiment_service.analyze_sentiment("BNP.PA", region="eu")
# Uses keywords: "bénéfice", "croissance", "hausse" etc.

# UK sentiment with British financial terms
uk_sentiment = await sentiment_service.analyze_sentiment("LLOY.L", region="uk")
# Uses keywords: "profit", "earnings beat", "tier 1" etc.
```

---

## Configuration Management

### Configuration Hierarchy

```
Base Configuration (Common)
├── Default settings
├── Common thresholds  
├── Standard timeouts
└── Universal parameters
    │
    ▼ (Merged with)
Regional Configuration
├── Market-specific symbols
├── Regional trading hours
├── Local news sources
├── Currency settings
└── Regional risk parameters
    │
    ▼ (Results in)
Runtime Configuration
├── Merged settings
├── Region-specific overrides
├── Cached configuration
└── Active parameters
```

### Configuration Loading Process

1. **Discovery Phase**: Scan `app/config/regions/` for available regions
2. **Loading Phase**: Import region-specific modules dynamically
3. **Merging Phase**: Combine base configuration with regional overrides
4. **Caching Phase**: Store merged configuration for performance
5. **Validation Phase**: Ensure all required parameters are present

### Environment-Specific Configurations

```python
# Development
config_manager = ConfigManager(
    region="asx",
    cache_ttl=60,  # Short cache for development
    debug=True
)

# Production
config_manager = ConfigManager(
    region="asx", 
    cache_ttl=3600,  # 1 hour cache
    debug=False
)
```

---

## Multi-Region Usage Examples

### Example 1: Global Market Analysis

```python
#!/usr/bin/env python3
"""
Global Market Analysis Example
Analyze sentiment and predictions across all regions
"""

import asyncio
from services.base_service import BaseService

class GlobalAnalyzer(BaseService):
    def __init__(self):
        super().__init__("global-analyzer")
        
    async def analyze_global_markets(self):
        """Analyze all global markets"""
        regions = ["asx", "usa", "uk", "eu"]
        results = {}
        
        for region in regions:
            try:
                # Get regional predictions
                predictions = await self.call_service(
                    "prediction", 
                    "generate_predictions", 
                    region=region
                )
                
                # Get regional sentiment
                sentiment = await self.call_service(
                    "sentiment", 
                    "get_big4_sentiment",
                    region=region
                )
                
                # Get market data status
                market_status = await self.call_service(
                    "market-data",
                    "is_market_open",
                    region=region
                )
                
                results[region] = {
                    "predictions": predictions,
                    "sentiment": sentiment,
                    "market_open": market_status,
                    "timestamp": time.time()
                }
                
            except Exception as e:
                results[region] = {"error": str(e)}
                
        return results

# Usage
analyzer = GlobalAnalyzer()
global_data = await analyzer.analyze_global_markets()

print("Global Market Analysis:")
for region, data in global_data.items():
    if "error" not in data:
        buy_rate = data["predictions"]["summary"]["buy_rate"]
        sentiment = data["sentiment"]["big4_average_sentiment"]
        market_open = data["market_open"]
        
        print(f"{region.upper()}: Buy Rate: {buy_rate:.1f}%, "
              f"Sentiment: {sentiment:.3f}, "
              f"Market: {'OPEN' if market_open else 'CLOSED'}")
```

### Example 2: Region-Specific Trading Strategy

```python
#!/usr/bin/env python3
"""
Region-Specific Trading Strategy
Different strategies for different markets
"""

class RegionTradingStrategy:
    def __init__(self):
        self.strategies = {
            "asx": self.asx_strategy,
            "usa": self.usa_strategy, 
            "uk": self.uk_strategy,
            "eu": self.eu_strategy
        }
        
    async def asx_strategy(self):
        """Conservative strategy for ASX (Big 4 banks focus)"""
        symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX"]
        predictions = await self.call_service(
            "prediction", 
            "generate_predictions",
            symbols=symbols,
            region="asx"
        )
        
        # Conservative thresholds for Australian banks
        buy_threshold = 0.75
        strong_buy_threshold = 0.85
        
        trades = []
        for symbol, pred in predictions["predictions"].items():
            confidence = pred.get("confidence", 0)
            if confidence >= strong_buy_threshold:
                trades.append({"symbol": symbol, "action": "STRONG_BUY", "confidence": confidence})
            elif confidence >= buy_threshold:
                trades.append({"symbol": symbol, "action": "BUY", "confidence": confidence})
                
        return trades
        
    async def usa_strategy(self):
        """Aggressive strategy for US markets (higher volatility)"""
        symbols = ["JPM", "BAC", "WFC", "C"]
        predictions = await self.call_service(
            "prediction",
            "generate_predictions", 
            symbols=symbols,
            region="usa"
        )
        
        # More aggressive thresholds for US markets
        buy_threshold = 0.65
        strong_buy_threshold = 0.80
        
        trades = []
        for symbol, pred in predictions["predictions"].items():
            confidence = pred.get("confidence", 0)
            if confidence >= strong_buy_threshold:
                trades.append({"symbol": symbol, "action": "STRONG_BUY", "confidence": confidence})
            elif confidence >= buy_threshold:
                trades.append({"symbol": symbol, "action": "BUY", "confidence": confidence})
                
        return trades

# Usage
strategy = RegionTradingStrategy()

# Execute region-specific strategies
asx_trades = await strategy.asx_strategy()
usa_trades = await strategy.usa_strategy()

print(f"ASX Strategy: {len(asx_trades)} trade signals")
print(f"USA Strategy: {len(usa_trades)} trade signals")
```

### Example 3: Market Hours Awareness

```python
#!/usr/bin/env python3
"""
Market Hours Awareness Example
Schedule tasks based on regional market hours
"""

import asyncio
from datetime import datetime
import pytz

class MarketScheduler:
    def __init__(self):
        self.market_timezones = {
            "asx": "Australia/Sydney",
            "usa": "America/New_York", 
            "uk": "Europe/London",
            "eu": "Europe/Paris"
        }
        
    async def get_active_markets(self):
        """Get currently active markets"""
        active = []
        
        for region, timezone in self.market_timezones.items():
            try:
                is_open = await self.call_service(
                    "market-data",
                    "is_market_open",
                    region=region
                )
                
                if is_open:
                    active.append(region)
                    
            except Exception as e:
                print(f"Error checking {region}: {e}")
                
        return active
        
    async def schedule_market_analysis(self):
        """Schedule analysis only for active markets"""
        active_markets = await self.get_active_markets()
        
        if not active_markets:
            print("No markets currently open")
            return
            
        print(f"Active markets: {', '.join(active_markets)}")
        
        for region in active_markets:
            # Schedule analysis for active market
            try:
                predictions = await self.call_service(
                    "prediction",
                    "generate_predictions",
                    region=region
                )
                
                sentiment = await self.call_service(
                    "sentiment", 
                    "get_big4_sentiment",
                    region=region
                )
                
                print(f"{region.upper()} Analysis Complete - "
                      f"Buy Rate: {predictions['summary']['buy_rate']:.1f}%, "
                      f"Sentiment: {sentiment['big4_average_sentiment']:.3f}")
                      
            except Exception as e:
                print(f"Error analyzing {region}: {e}")

# Usage
scheduler = MarketScheduler()
await scheduler.schedule_market_analysis()
```

---

## Deployment Guide

### 1. Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Create service directories
sudo mkdir -p /opt/trading_services /var/log/trading /tmp/trading_sockets

# Set permissions
sudo chown $USER:$USER /opt/trading_services /var/log/trading /tmp/trading_sockets

# Install Redis
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### 2. Service Configuration

Copy all service files to `/opt/trading_services/`:

```bash
# Copy application
cp -r app/ services/ /opt/trading_services/

# Set up Python environment
python3 -m venv /opt/trading_venv
source /opt/trading_venv/bin/activate
pip install -r requirements.txt
```

### 3. Systemd Service Files

Create systemd service files for each microservice:

```ini
# /etc/systemd/system/trading-prediction.service
[Unit]
Description=Trading Prediction Service (Multi-Region)
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=trading
WorkingDirectory=/opt/trading_services
Environment=PYTHONPATH=/opt/trading_services
Environment=TRADING_REGION=asx
ExecStart=/opt/trading_venv/bin/python services/prediction/prediction_service.py
Restart=always
RestartSec=5
MemoryMax=1G

[Install]
WantedBy=multi-user.target
```

### 4. Multi-Region Service Manager

```python
#!/usr/bin/env python3
"""
Multi-Region Service Manager
Enhanced version supporting region-specific operations
"""

class MultiRegionServiceManager:
    def __init__(self):
        self.regions = ["asx", "usa", "uk", "eu"]
        self.services = ["prediction", "market-data", "sentiment"]
        
    async def health_check_all_regions(self):
        """Check health across all regions"""
        health_status = {}
        
        for region in self.regions:
            health_status[region] = {}
            
            for service in self.services:
                try:
                    # Check service health for specific region
                    health = await self.call_service_region(
                        service, "health", region
                    )
                    health_status[region][service] = health["status"]
                    
                except Exception as e:
                    health_status[region][service] = f"error: {e}"
                    
        return health_status
        
    async def switch_all_services_region(self, target_region: str):
        """Switch all services to target region"""
        results = {}
        
        for service in self.services:
            try:
                result = await self.call_service(
                    service, 
                    "switch_region", 
                    region=target_region
                )
                results[service] = "switched"
                
            except Exception as e:
                results[service] = f"error: {e}"
                
        return results

# Usage
manager = MultiRegionServiceManager()

# Check health across all regions
health = await manager.health_check_all_regions()

# Switch entire system to UK region
switch_results = await manager.switch_all_services_region("uk")
```

---

## Testing & Validation

### 1. Unit Tests

```python
#!/usr/bin/env python3
"""
Multi-Region Configuration Tests
"""

import pytest
from app.config.regions.config_manager import ConfigManager

class TestMultiRegionConfig:
    
    @pytest.fixture
    def config_manager(self):
        return ConfigManager(region="asx")
        
    def test_region_switching(self, config_manager):
        """Test region switching functionality"""
        # Test initial region
        assert config_manager.current_region == "asx"
        
        # Test switching to USA
        config_manager.set_region("usa")
        assert config_manager.current_region == "usa"
        
        # Verify USA symbols are loaded
        config = config_manager.get_config()
        usa_banks = config["market_data"]["symbols"]["big4_banks"]
        assert "JPM" in usa_banks
        assert "BAC" in usa_banks
        
    def test_configuration_merging(self, config_manager):
        """Test base + regional configuration merging"""
        config = config_manager.get_config()
        
        # Should have base configuration
        assert "default_cache_ttl" in config
        
        # Should have regional overrides
        assert "market_data" in config
        assert "sentiment" in config
        
    def test_all_regions_loadable(self, config_manager):
        """Test that all regions can be loaded"""
        regions = ["asx", "usa", "uk", "eu"]
        
        for region in regions:
            config_manager.set_region(region)
            config = config_manager.get_config()
            
            # Each region should have required sections
            assert "market_data" in config
            assert "sentiment" in config
            assert "prediction" in config
            
            # Should have region-specific symbols
            symbols = config["market_data"]["symbols"]
            assert "big4_banks" in symbols
            assert len(symbols["big4_banks"]) >= 4

# Run tests
pytest test_multi_region.py -v
```

### 2. Integration Tests

```python
#!/usr/bin/env python3
"""
Multi-Region Integration Tests
"""

import asyncio
import pytest
from services.prediction.prediction_service import PredictionService

class TestMultiRegionIntegration:
    
    @pytest.mark.asyncio
    async def test_cross_region_predictions(self):
        """Test predictions across different regions"""
        service = PredictionService(default_region="asx")
        
        # Test ASX predictions
        asx_result = await service.generate_predictions(
            symbols=["CBA.AX"], 
            region="asx"
        )
        assert "predictions" in asx_result
        assert "CBA.AX" in asx_result["predictions"]
        
        # Test USA predictions
        usa_result = await service.generate_predictions(
            symbols=["JPM"],
            region="usa" 
        )
        assert "predictions" in usa_result
        assert "JPM" in usa_result["predictions"]
        
        # Verify service returns to original region
        current_region = await service.get_current_region()
        assert current_region["region"] == "asx"
        
    @pytest.mark.asyncio
    async def test_region_isolation(self):
        """Test that regions have isolated caches"""
        service = PredictionService()
        
        # Generate prediction for ASX
        asx_pred = await service.generate_predictions(
            symbols=["CBA.AX"],
            region="asx"
        )
        
        # Generate prediction for USA
        usa_pred = await service.generate_predictions(
            symbols=["JPM"], 
            region="usa"
        )
        
        # Check cache isolation
        asx_cache_key = "prediction:CBA.AX:asx"
        usa_cache_key = "prediction:JPM:usa"
        
        assert asx_cache_key in service.prediction_cache
        assert usa_cache_key in service.prediction_cache
        
        # Verify different cache entries
        assert service.prediction_cache[asx_cache_key] != service.prediction_cache[usa_cache_key]

# Run integration tests
pytest test_integration.py -v
```

### 3. Performance Tests

```python
#!/usr/bin/env python3
"""
Multi-Region Performance Tests
"""

import time
import asyncio
from services.prediction.prediction_service import PredictionService

async def benchmark_region_switching():
    """Benchmark region switching performance"""
    service = PredictionService()
    regions = ["asx", "usa", "uk", "eu"]
    
    # Warm up
    for region in regions:
        await service.switch_region(region)
    
    # Benchmark region switching
    start_time = time.time()
    iterations = 100
    
    for i in range(iterations):
        target_region = regions[i % len(regions)]
        await service.switch_region(target_region)
    
    end_time = time.time()
    avg_switch_time = (end_time - start_time) / iterations
    
    print(f"Average region switch time: {avg_switch_time*1000:.2f}ms")
    assert avg_switch_time < 0.1  # Should be under 100ms

async def benchmark_multi_region_predictions():
    """Benchmark predictions across regions"""
    service = PredictionService()
    
    test_symbols = {
        "asx": ["CBA.AX", "ANZ.AX"],
        "usa": ["JPM", "BAC"], 
        "uk": ["LLOY.L", "BARC.L"],
        "eu": ["BNP.PA", "ACA.PA"]
    }
    
    start_time = time.time()
    
    # Generate predictions for all regions in parallel
    tasks = []
    for region, symbols in test_symbols.items():
        task = service.generate_predictions(symbols=symbols, region=region)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"Multi-region prediction time: {total_time:.2f}s")
    assert total_time < 30  # Should complete within 30 seconds
    
    # Verify all results
    assert len(results) == 4
    for result in results:
        assert "predictions" in result
        assert "summary" in result

# Run performance tests
if __name__ == "__main__":
    asyncio.run(benchmark_region_switching())
    asyncio.run(benchmark_multi_region_predictions())
```

---

## Monitoring & Operations

### 1. Multi-Region Health Dashboard

```python
#!/usr/bin/env python3
"""
Multi-Region Health Dashboard
Real-time monitoring across all regions and services
"""

import asyncio
import time
from datetime import datetime
from services.base_service import BaseService

class MultiRegionDashboard(BaseService):
    def __init__(self):
        super().__init__("dashboard")
        self.regions = ["asx", "usa", "uk", "eu"]
        self.services = ["prediction", "market-data", "sentiment"]
        
    async def collect_health_data(self):
        """Collect health data from all services and regions"""
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "regions": {},
            "services": {},
            "system": {}
        }
        
        # Collect service health
        for service in self.services:
            try:
                health = await self.call_service(service, "health")
                health_data["services"][service] = health
            except Exception as e:
                health_data["services"][service] = {"error": str(e), "status": "unreachable"}
        
        # Collect region-specific data
        for region in self.regions:
            health_data["regions"][region] = {}
            
            try:
                # Get market status
                market_status = await self.call_service(
                    "market-data", "is_market_open", region=region
                )
                
                # Get regional sentiment
                sentiment = await self.call_service(
                    "sentiment", "get_big4_sentiment", region=region
                )
                
                # Get prediction metrics
                prediction_health = await self.call_service(
                    "prediction", "health"
                )
                
                health_data["regions"][region] = {
                    "market_open": market_status,
                    "sentiment": sentiment.get("big4_average_sentiment", 0),
                    "prediction_count": prediction_health.get("prediction_count", 0),
                    "status": "healthy"
                }
                
            except Exception as e:
                health_data["regions"][region] = {
                    "error": str(e),
                    "status": "error"
                }
        
        # System metrics
        import psutil
        health_data["system"] = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent
        }
        
        return health_data
    
    async def display_dashboard(self):
        """Display real-time dashboard"""
        while True:
            try:
                # Clear screen
                print("\033[2J\033[H")
                
                # Get health data
                data = await self.collect_health_data()
                
                print("=" * 80)
                print("MULTI-REGION TRADING SYSTEM DASHBOARD")
                print(f"Last Updated: {data['timestamp']}")
                print("=" * 80)
                
                # System Status
                sys_data = data["system"]
                print(f"System: CPU {sys_data['cpu_percent']:.1f}% | "
                      f"Memory {sys_data['memory_percent']:.1f}% | "
                      f"Disk {sys_data['disk_usage']:.1f}%")
                print()
                
                # Service Status
                print("SERVICES STATUS:")
                for service, health in data["services"].items():
                    status_icon = "🟢" if health.get("status") == "healthy" else "🔴"
                    memory = health.get("memory_usage", 0)
                    if isinstance(memory, int) and memory > 0:
                        memory_mb = memory // 1024 // 1024
                        memory_str = f"{memory_mb}MB"
                    else:
                        memory_str = "N/A"
                    
                    print(f"{status_icon} {service:15} | Memory: {memory_str:>8} | "
                          f"Status: {health.get('status', 'unknown')}")
                print()
                
                # Regional Status
                print("REGIONAL MARKETS:")
                print(f"{'Region':<10} {'Market':<8} {'Sentiment':<10} {'Predictions':<12} {'Status'}")
                print("-" * 60)
                
                for region, info in data["regions"].items():
                    if "error" not in info:
                        market_icon = "🟢" if info["market_open"] else "🔴"
                        sentiment = info["sentiment"]
                        pred_count = info["prediction_count"]
                        status = info["status"]
                        
                        print(f"{region.upper():<10} {market_icon:<8} "
                              f"{sentiment:>+.3f}{'':3} {pred_count:>8} {'':4} {status}")
                    else:
                        print(f"{region.upper():<10} {'ERROR':<8} {'N/A':<10} {'N/A':<12} error")
                
                print("\n" + "=" * 80)
                print("Press Ctrl+C to exit")
                
                await asyncio.sleep(10)  # Update every 10 seconds
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Dashboard error: {e}")
                await asyncio.sleep(5)

async def main():
    dashboard = MultiRegionDashboard()
    await dashboard.display_dashboard()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. Alerting System

```python
#!/usr/bin/env python3
"""
Multi-Region Alerting System
Monitor and alert on system issues across regions
"""

class MultiRegionAlerting(BaseService):
    def __init__(self):
        super().__init__("alerting")
        self.alert_thresholds = {
            "high_cpu": 80,
            "high_memory": 85,
            "low_sentiment": -0.5,
            "high_buy_rate": 80,
            "service_down": 30  # seconds
        }
        
    async def check_system_alerts(self):
        """Check for system-wide alerts"""
        alerts = []
        
        # Check service health
        for service in ["prediction", "market-data", "sentiment"]:
            try:
                health = await self.call_service(service, "health", timeout=5)
                
                if health.get("status") != "healthy":
                    alerts.append({
                        "type": "service_unhealthy",
                        "severity": "critical",
                        "service": service,
                        "details": health.get("last_error", "Unknown error")
                    })
                    
                # Check resource usage
                memory_percent = health.get("memory_usage", 0) / (1024**3) * 100  # Convert to %
                if memory_percent > self.alert_thresholds["high_memory"]:
                    alerts.append({
                        "type": "high_memory_usage",
                        "severity": "warning", 
                        "service": service,
                        "memory_percent": memory_percent
                    })
                    
            except asyncio.TimeoutError:
                alerts.append({
                    "type": "service_timeout",
                    "severity": "critical",
                    "service": service,
                    "timeout_seconds": 5
                })
                
        return alerts
        
    async def check_regional_alerts(self):
        """Check for region-specific alerts"""
        alerts = []
        
        for region in ["asx", "usa", "uk", "eu"]:
            try:
                # Check sentiment alerts
                sentiment = await self.call_service(
                    "sentiment", "get_big4_sentiment", region=region
                )
                
                avg_sentiment = sentiment.get("big4_average_sentiment", 0)
                if avg_sentiment < self.alert_thresholds["low_sentiment"]:
                    alerts.append({
                        "type": "low_sentiment",
                        "severity": "warning",
                        "region": region,
                        "sentiment": avg_sentiment
                    })
                
                # Check buy rate alerts
                buy_rate_data = await self.call_service(
                    "prediction", "get_buy_rate", region=region
                )
                
                buy_rate = buy_rate_data.get("buy_rate", 0)
                if buy_rate > self.alert_thresholds["high_buy_rate"]:
                    alerts.append({
                        "type": "high_buy_rate",
                        "severity": "warning",
                        "region": region,
                        "buy_rate": buy_rate
                    })
                    
            except Exception as e:
                alerts.append({
                    "type": "region_check_failed",
                    "severity": "warning",
                    "region": region,
                    "error": str(e)
                })
                
        return alerts
        
    async def process_alerts(self, alerts):
        """Process and send alerts"""
        if not alerts:
            return
            
        # Group alerts by severity
        critical_alerts = [a for a in alerts if a["severity"] == "critical"]
        warning_alerts = [a for a in alerts if a["severity"] == "warning"]
        
        # Log alerts
        for alert in critical_alerts:
            self.logger.critical(f"CRITICAL ALERT: {alert}")
            
        for alert in warning_alerts:
            self.logger.warning(f"WARNING ALERT: {alert}")
            
        # Publish alerts via Redis
        if critical_alerts:
            self.publish_event("system_alert", {
                "severity": "critical",
                "alerts": critical_alerts,
                "timestamp": time.time()
            }, priority="urgent")
            
        if warning_alerts:
            self.publish_event("system_alert", {
                "severity": "warning", 
                "alerts": warning_alerts,
                "timestamp": time.time()
            }, priority="normal")

async def run_alerting_system():
    """Run the alerting system"""
    alerting = MultiRegionAlerting()
    
    while True:
        try:
            # Check for alerts
            system_alerts = await alerting.check_system_alerts()
            regional_alerts = await alerting.check_regional_alerts()
            
            all_alerts = system_alerts + regional_alerts
            
            if all_alerts:
                await alerting.process_alerts(all_alerts)
                print(f"Processed {len(all_alerts)} alerts")
            
            await asyncio.sleep(60)  # Check every minute
            
        except Exception as e:
            print(f"Alerting system error: {e}")
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(run_alerting_system())
```

---

## Troubleshooting

### Common Issues

#### 1. Region Loading Errors

**Problem**: `RegionNotFoundError: Region 'uk' not found`

**Solution**:
```bash
# Check if region directory exists
ls app/config/regions/uk/

# Verify __init__.py exists and is valid
python -c "from app.config.regions.uk import UKConfig; print('OK')"

# Check ConfigManager discovery
python -c "
from app.config.regions.config_manager import ConfigManager
mgr = ConfigManager()
print(mgr.get_available_regions())
"
```

#### 2. Service Communication Errors

**Problem**: `Service call failed: Connection refused`

**Solution**:
```bash
# Check if services are running
systemctl status trading-prediction
systemctl status trading-market-data
systemctl status trading-sentiment

# Check socket files
ls -la /tmp/trading_*.sock

# Test socket communication
python -c "
import asyncio
from services.base_service import BaseService

async def test():
    service = BaseService('test')
    result = await service.call_service('prediction', 'health')
    print(result)

asyncio.run(test())
"
```

#### 3. Region Switching Issues

**Problem**: Region switches but returns incorrect data

**Solution**:
```python
# Clear configuration cache
config_manager = ConfigManager()
config_manager._config_cache.clear()
config_manager._cache_timestamps.clear()

# Force reload
config_manager.set_region("usa")
config = config_manager.get_config()

# Verify region-specific data
print(config["market_data"]["symbols"]["big4_banks"])
# Should show: ["JPM", "BAC", "WFC", "C"] for USA
```

#### 4. Memory Usage Issues

**Problem**: High memory usage with multiple regions

**Solution**:
```python
# Configure cache limits
config_manager = ConfigManager(cache_ttl=1800)  # 30 minutes

# Clear unused region caches
for service_name in ["prediction", "sentiment"]:
    await service.call_service(service_name, "refresh_sentiment_cache")

# Monitor memory usage
import psutil
process = psutil.Process()
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f}MB")
```

### Performance Optimization

#### 1. Configuration Caching

```python
# Optimal cache settings
config_manager = ConfigManager(
    region="asx",
    cache_ttl=3600  # 1 hour for production
)

# Development settings
config_manager = ConfigManager(
    region="asx", 
    cache_ttl=60   # 1 minute for development
)
```

#### 2. Service Resource Limits

```ini
# /etc/systemd/system/trading-prediction.service
[Service]
MemoryMax=1G           # Limit memory usage
CPUQuota=100%          # Limit CPU usage
TasksMax=50            # Limit number of tasks
```

#### 3. Redis Optimization

```bash
# Redis configuration for multi-region
echo "maxmemory 512mb" >> /etc/redis/redis.conf
echo "maxmemory-policy allkeys-lru" >> /etc/redis/redis.conf

# Restart Redis
sudo systemctl restart redis
```

---

## Conclusion

This comprehensive multi-region microservices system provides:

✅ **Complete Global Market Coverage**: ASX, USA, UK, Europe  
✅ **Dynamic Region Switching**: Runtime configuration changes  
✅ **Intelligent Configuration Management**: Base + Regional merging  
✅ **Market-Aware Operations**: Timezone and trading hours awareness  
✅ **High Performance**: Optimized caching and resource management  
✅ **Production Ready**: Full monitoring, alerting, and error handling  
✅ **Backward Compatibility**: Seamless migration from monolithic system  

The system is now ready for production deployment across multiple global financial markets with comprehensive monitoring, testing, and operational procedures.
