# Paper Trading App with IG Markets Integration

## Overview

This enhanced paper trading application integrates IG Markets API as the primary real-time data source while maintaining full backward compatibility with the existing system. The integration provides:

- **Real-time ASX market data** via IG Markets professional API
- **Intelligent fallback** to yfinance for reliability
- **Seamless integration** with existing paper trading logic
- **Enhanced monitoring** and statistics tracking
- **Zero-downtime operation** with automatic failover

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                Paper Trading Application                │
├─────────────────────────────────────────────────────────┤
│  Enhanced Service    │  Enhanced Engine  │  Dashboard   │
├─────────────────────────────────────────────────────────┤
│           Enhanced IG Markets Integration               │
├─────────────────────────────────────────────────────────┤
│  IG Markets API      │  Symbol Mapper    │  Cache Mgr   │
├─────────────────────────────────────────────────────────┤
│  Real-time Data      │  yfinance Fallback│  Local Cache │
└─────────────────────────────────────────────────────────┘
```

## Features

### ✅ **Existing Functionality Preserved**
- All original paper trading features work unchanged
- Database schema and structure maintained
- Dashboard and reporting remain functional
- Trading strategies and logic unchanged

### 🚀 **New IG Markets Capabilities**
- Real-time ASX stock prices via professional API
- Symbol mapping (CBA.AX → AA.D.CBA.CASH.IP)
- Multi-source price aggregation
- Health monitoring and statistics
- Automatic failover to yfinance

### 📊 **Enhanced Monitoring**
- Data source usage statistics
- API health checks
- Response time monitoring
- Cache efficiency metrics
- Fallback usage tracking

## Quick Start

### 1. Basic Setup
```bash
# Navigate to paper trading directory
cd paper-trading-app/

# Test IG Markets integration
python run_paper_trading_ig.py test

# Initialize system
python run_paper_trading_ig.py init
```

### 2. Run Paper Trading Service
```bash
# Start enhanced service with IG Markets
python run_paper_trading_ig.py service

# Or use the enhanced service directly
python enhanced_paper_trading_service_with_ig.py
```

### 3. Run Dashboard
```bash
# Start dashboard with IG Markets integration
python run_paper_trading_ig.py dashboard
```

## Component Details

### Enhanced Paper Trading Service
**File**: `enhanced_paper_trading_service_with_ig.py`

- Extends original service with IG Markets integration
- Maintains all existing trading logic
- Adds real-time data source monitoring
- Provides enhanced statistics and health checks

**Key Features**:
- One position per symbol strategy (unchanged)
- IG Markets real-time pricing
- Automatic fallback to yfinance
- Enhanced portfolio summary with data source stats

### Enhanced Trading Engine
**File**: `enhanced_trading_engine_ig.py`

- Monkey patches original trading engine
- Transparent IG Markets integration
- Maintains full API compatibility
- Adds data source health monitoring

**Key Features**:
- Drop-in replacement for original engine
- IG Markets → yfinance fallback chain
- Usage statistics tracking
- Performance monitoring

### IG Markets Integration Layer
**File**: `enhanced_ig_markets_integration.py`

- Core integration with IG Markets API
- Symbol mapping and conversion
- Caching and performance optimization
- Health monitoring and statistics

**Key Features**:
- Professional real-time ASX data
- Symbol mapping (ASX ↔ IG Markets EPICs)
- 5-minute intelligent caching
- Comprehensive error handling

## Configuration

### Environment Variables
Set these in your `.env` file:
```bash
# IG Markets API credentials
IG_USERNAME=your_demo_username
IG_PASSWORD=your_demo_password
IG_API_KEY=your_api_key
IG_DEMO=true

# Optional: Disable IG Markets for testing
# IG_DISABLE=true
```

### Configuration File
**File**: `config.py`

Updated configuration includes:
```python
# IG Markets Integration Settings
IG_MARKETS_CONFIG = {
    'enabled': True,
    'fallback_to_yfinance': True,
    'cache_duration_minutes': 5,
    'health_check_interval_seconds': 600,
    'log_usage_stats': True
}

# Trading Configuration
TRADING_CONFIG = {
    'use_ig_markets': True,
    'ig_markets_priority': True,
    'price_source_timeout_seconds': 10
}
```

## Usage Examples

### Running with IG Markets Integration

```bash
# Test complete system
python run_paper_trading_ig.py test

# Start paper trading service
python run_paper_trading_ig.py service

# Start dashboard
python run_paper_trading_ig.py dashboard
```

### Testing Individual Components

```bash
# Test IG Markets integration only
python enhanced_ig_markets_integration.py

# Test enhanced trading engine
python enhanced_trading_engine_ig.py

# Test enhanced service
python enhanced_paper_trading_service_with_ig.py --test
```

### Monitoring and Statistics

The enhanced system provides comprehensive monitoring:

```python
# Get data source statistics
service = EnhancedPaperTradingServiceWithIG()
stats = service.get_data_source_stats()
print(f"IG Markets requests: {stats['ig_markets_requests']}")
print(f"yfinance requests: {stats['yfinance_requests']}")
print(f"Cache hits: {stats['cache_hits']}")

# Check health status
health = service.get_price_source_health()
print(f"IG Markets healthy: {health['ig_markets_healthy']}")
```

## Fallback Behavior

The system uses intelligent fallback:

1. **Primary**: IG Markets API for real-time ASX data
2. **Secondary**: yfinance as reliable backup
3. **Tertiary**: Cached data for resilience

### Fallback Triggers
- IG Markets API errors or timeouts
- Network connectivity issues
- API rate limit exceeded
- Invalid or missing data

### Recovery Behavior
- Automatic retry with exponential backoff
- Health check monitoring every 10 minutes
- Automatic recovery when IG Markets becomes available
- Logging and alerting for fallback events

## Symbol Mapping

The system automatically handles symbol conversion:

```python
# ASX symbols → IG Markets EPICs
CBA.AX → AA.D.CBA.CASH.IP    # Commonwealth Bank
WBC.AX → AA.D.WBC.CASH.IP    # Westpac
ANZ.AX → AA.D.ANZ.CASH.IP    # ANZ Bank
NAB.AX → AA.D.NAB.CASH.IP    # National Australia Bank
BHP.AX → AA.D.BHP.CASH.IP    # BHP Billiton
```

### Dynamic Discovery
- Static mapping for major ASX stocks
- Dynamic discovery via IG Markets search API
- Caching for discovered mappings
- Fallback to ASX symbol if mapping fails

## Monitoring and Logging

### Log Files
- `enhanced_paper_trading_with_ig.log` - Main service logs
- `paper_trading_ig_startup.log` - Initialization logs
- Original log files maintained for compatibility

### Key Metrics
- **Response Times**: API latency tracking
- **Success Rates**: Request success/failure ratios
- **Cache Efficiency**: Hit/miss ratios
- **Source Distribution**: IG Markets vs yfinance usage
- **Health Status**: API availability monitoring

### Dashboard Integration
The dashboard displays:
- Data source statistics
- IG Markets health status
- Response time metrics
- Fallback usage patterns

## Troubleshooting

### Common Issues

**1. IG Markets Authentication Fails**
```bash
# Check credentials in .env file
# Verify demo account is active
# Test with IG Markets demo environment
```

**2. No Price Data Available**
```bash
# Check network connectivity
# Verify market hours (ASX: 10:00-16:00 AEST/AEDT)
# Check log files for error details
```

**3. High yfinance Usage**
```bash
# Check IG Markets health status
# Review error logs for API issues
# Verify symbol mapping is working
```

### Debug Commands

```bash
# Test IG Markets connectivity
python -c "
from enhanced_ig_markets_integration import get_enhanced_price_source
source = get_enhanced_price_source()
print('Health:', source.get_health_status())
print('Stats:', source.get_data_source_stats())
"

# Test price fetching
python -c "
from enhanced_ig_markets_integration import get_enhanced_price_source
source = get_enhanced_price_source()
price = source.get_current_price('CBA.AX')
print(f'CBA.AX price: ${price}')
"
```

### Performance Tuning

**1. Cache Configuration**
- Adjust cache duration in `IG_MARKETS_CONFIG`
- Monitor cache hit ratios
- Consider Redis for distributed caching

**2. API Rate Limiting**
- Monitor request frequency
- Implement request queuing if needed
- Use batch requests where possible

**3. Health Check Frequency**
- Adjust `health_check_interval_seconds`
- Balance monitoring vs API usage
- Use backoff strategies for failures

## Migration from Original System

### Zero-Downtime Migration
1. Current system continues running unchanged
2. IG Markets integration can be enabled gradually
3. Fallback ensures continuous operation
4. Full rollback capability maintained

### Migration Steps
1. **Deploy Integration**: Add IG Markets components
2. **Test Integration**: Run comprehensive tests
3. **Enable Gradually**: Start with limited symbols
4. **Monitor Performance**: Track metrics and health
5. **Full Deployment**: Enable for all symbols

### Rollback Procedure
If issues occur, disable IG Markets:
```bash
# Set environment variable
export IG_DISABLE=true

# Or edit config.py
IG_MARKETS_CONFIG['enabled'] = False

# Restart service - will use yfinance only
```

## Production Considerations

### Security
- Store API credentials securely
- Use environment variables for sensitive data
- Implement API key rotation
- Monitor for unauthorized access

### Scalability
- Monitor API rate limits
- Implement connection pooling
- Use distributed caching for high volume
- Consider multiple API keys for scaling

### Reliability
- Set up monitoring alerts
- Implement circuit breaker patterns
- Use health checks for automatic recovery
- Maintain fallback data sources

### Cost Optimization
- Monitor API usage and costs
- Implement intelligent caching
- Use batch requests where possible
- Optimize request frequency

## API Integration Details

### IG Markets API
- **Endpoint**: Demo environment (labs-api.ig.com)
- **Authentication**: OAuth-style with username/password/API key
- **Rate Limits**: Configured per account
- **Data Format**: JSON responses
- **Supported Markets**: ASX, UK, US, and more

### Symbol Format
- **ASX Format**: CBA.AX (ticker.exchange)
- **IG Markets Format**: AA.D.CBA.CASH.IP (epic format)
- **Auto-conversion**: Handled transparently
- **Dynamic Discovery**: Via IG Markets search API

## Support and Maintenance

### Regular Tasks
- Monitor API health and performance
- Review usage statistics and costs
- Update symbol mappings as needed
- Test fallback mechanisms

### Upgrades
- IG Markets API updates
- Symbol mapping additions
- Performance optimizations
- Feature enhancements

### Contact Information
- **Developer**: Todd Sutherland
- **Integration**: IG Markets Paper Trading Enhancement
- **Support**: Check logs and health status first

## Status: Production Ready ✅

The IG Markets integration is fully functional and ready for production use. All components have been thoroughly tested and integrated with the existing paper trading system.

### Success Criteria Met
- ✅ IG Markets API successfully integrated
- ✅ Symbol mapping working for all major ASX stocks
- ✅ Fallback system tested and reliable
- ✅ Zero impact on existing functionality
- ✅ Comprehensive monitoring and logging
- ✅ Production deployment ready
