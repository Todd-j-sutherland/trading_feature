# Trading System Services Architecture

## Overview
This directory contains the services-rich architecture for the trading system. Each service is independently deployable and maintains clear boundaries.

## Services

### 1. Trading Service (`trading-service/`)
Core trading logic including:
- Position management
- Risk management  
- Paper trading
- Signal generation
- Alpaca/Moomoo integration

### 2. Sentiment Service (`sentiment-service/`)
News sentiment analysis including:
- News collection and parsing
- Sentiment scoring
- Market sentiment integration
- Temporal analysis

### 3. ML Service (`ml-service/`)
Machine learning predictions including:
- Model training and management
- Prediction generation
- Ensemble methods
- Performance tracking

### 4. Data Service (`data-service/`)
Data collection and management including:
- Market data collection
- News data aggregation
- Data validation and quality
- Database management

### 5. Dashboard Service (`dashboard-service/`)
User interface and visualization including:
- Web dashboard
- Real-time updates
- Performance metrics
- Trading visualization

## Service Communication

Services communicate through:
- REST APIs for synchronous operations
- Message queues for asynchronous operations
- Shared data models for consistency
- Health checks for monitoring

## Deployment

Each service can be deployed independently using:
- Docker containers
- Environment-specific configuration
- Health monitoring
- Graceful shutdown handling