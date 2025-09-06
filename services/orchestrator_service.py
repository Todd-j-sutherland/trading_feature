"""
Orchestrator Service - Service Coordination and System Integration

This service handles:
- Coordination between trading and sentiment services
- End-to-end prediction workflow orchestration
- System health monitoring and status
- API gateway functionality
"""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import json
import traceback

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from pydantic import BaseModel
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Local imports with fallbacks
from services.shared.models.trading_models import TradingSignal, PortfolioSummary
from services.shared.models.sentiment_models import SentimentScore
from services.shared.utils.service_client import ServiceClient
from services.shared.utils.logging_utils import setup_logging
from services.shared.config.service_config import get_service_config


# Setup logging
logger = setup_logging("orchestrator_service")
config = get_service_config("orchestrator")

# Initialize FastAPI app (if available)
if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Orchestrator Service",
        description="Service coordination and system integration for ASX trading system",
        version="1.0.0"
    )
else:
    app = None
    logger.warning("FastAPI not available - service will run in compatibility mode")


class OrchestratorServiceCore:
    """Core orchestration functionality (works without external dependencies)"""
    
    def __init__(self):
        # Get service ports from config
        trading_config = get_service_config("trading")
        sentiment_config = get_service_config("sentiment")
        
        self.trading_service_url = f"http://localhost:{trading_config.port}"
        self.sentiment_service_url = f"http://localhost:{sentiment_config.port}"
        
        # Initialize service clients (with fallbacks)
        if REQUESTS_AVAILABLE:
            self.trading_client = ServiceClient(self.trading_service_url)
            self.sentiment_client = ServiceClient(self.sentiment_service_url)
        else:
            self.trading_client = None
            self.sentiment_client = None
            logger.warning("Service clients not available - using fallback mode")
        
        # Service status tracking
        self.service_status = {
            'trading': {'healthy': False, 'last_check': None, 'error': None},
            'sentiment': {'healthy': False, 'last_check': None, 'error': None}
        }
    
    def orchestrate_prediction_workflow(self, symbol: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate complete prediction workflow"""
        try:
            workflow_result = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'steps': [],
                'final_prediction': None,
                'success': False
            }
            
            # Step 1: Get sentiment analysis
            logger.info(f"Step 1: Getting sentiment for {symbol}")
            sentiment_result = self._get_sentiment_data(symbol)
            workflow_result['steps'].append({
                'step': 'sentiment_analysis',
                'success': sentiment_result['success'],
                'data': sentiment_result['data'],
                'error': sentiment_result.get('error')
            })
            
            # Step 2: Generate trading signal
            logger.info(f"Step 2: Generating trading signal for {symbol}")
            signal_data = {
                'symbol': symbol,
                'market_data': market_data,
                'sentiment_score': sentiment_result['data'] if sentiment_result['success'] else None
            }
            
            trading_result = self._generate_trading_signal(signal_data)
            workflow_result['steps'].append({
                'step': 'trading_signal_generation',
                'success': trading_result['success'],
                'data': trading_result['data'],
                'error': trading_result.get('error')
            })
            
            # Step 3: Validate and potentially execute
            if trading_result['success'] and trading_result['data']:
                logger.info(f"Step 3: Validating trading signal for {symbol}")
                validation_result = self._validate_trading_signal(trading_result['data'])
                workflow_result['steps'].append({
                    'step': 'signal_validation',
                    'success': validation_result['success'],
                    'data': validation_result['data'],
                    'error': validation_result.get('error')
                })
                
                if validation_result['success']:
                    workflow_result['final_prediction'] = trading_result['data']
                    workflow_result['success'] = True
            
            return workflow_result
            
        except Exception as e:
            logger.error(f"Error in prediction workflow for {symbol}: {e}")
            return {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'steps': [],
                'final_prediction': None,
                'success': False,
                'error': str(e)
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            # Check all services
            self._check_service_health()
            
            # Get portfolio summary
            portfolio_status = self._get_portfolio_status()
            
            # Calculate overall system health
            healthy_services = sum(1 for status in self.service_status.values() if status['healthy'])
            total_services = len(self.service_status)
            system_health = healthy_services / total_services if total_services > 0 else 0
            
            status = {
                'timestamp': datetime.now().isoformat(),
                'system_health': system_health,
                'overall_status': 'healthy' if system_health >= 0.5 else 'degraded' if system_health > 0 else 'unhealthy',
                'services': self.service_status,
                'portfolio': portfolio_status,
                'orchestrator': {
                    'healthy': True,
                    'requests_available': REQUESTS_AVAILABLE,
                    'fastapi_available': FASTAPI_AVAILABLE,
                    'mode': 'full' if REQUESTS_AVAILABLE else 'compatibility'
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'system_health': 0.0,
                'overall_status': 'error',
                'error': str(e)
            }
    
    def coordinate_batch_analysis(self, symbols: List[str]) -> Dict[str, Any]:
        """Coordinate batch analysis for multiple symbols"""
        try:
            batch_result = {
                'symbols': symbols,
                'timestamp': datetime.now().isoformat(),
                'results': [],
                'summary': {
                    'total_symbols': len(symbols),
                    'successful_predictions': 0,
                    'failed_predictions': 0,
                    'average_confidence': 0.0
                }
            }
            
            total_confidence = 0.0
            
            for symbol in symbols:
                try:
                    # Basic market data (in production, would fetch real data)
                    market_data = {
                        'current_price': 100.0,  # Placeholder
                        'volume': 1000000,       # Placeholder
                        'market_context': 'NEUTRAL'
                    }
                    
                    result = self.orchestrate_prediction_workflow(symbol, market_data)
                    batch_result['results'].append(result)
                    
                    if result['success'] and result['final_prediction']:
                        batch_result['summary']['successful_predictions'] += 1
                        confidence = result['final_prediction'].get('confidence', 0)
                        total_confidence += confidence
                    else:
                        batch_result['summary']['failed_predictions'] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing {symbol} in batch: {e}")
                    batch_result['results'].append({
                        'symbol': symbol,
                        'success': False,
                        'error': str(e)
                    })
                    batch_result['summary']['failed_predictions'] += 1
            
            # Calculate average confidence
            if batch_result['summary']['successful_predictions'] > 0:
                batch_result['summary']['average_confidence'] = (
                    total_confidence / batch_result['summary']['successful_predictions']
                )
            
            return batch_result
            
        except Exception as e:
            logger.error(f"Error in batch analysis: {e}")
            return {
                'symbols': symbols,
                'timestamp': datetime.now().isoformat(),
                'results': [],
                'summary': {
                    'total_symbols': len(symbols),
                    'successful_predictions': 0,
                    'failed_predictions': len(symbols),
                    'average_confidence': 0.0
                },
                'error': str(e)
            }
    
    def _get_sentiment_data(self, symbol: str) -> Dict[str, Any]:
        """Get sentiment data for a symbol"""
        try:
            if self.sentiment_client:
                # ServiceClient.get() returns JSON data directly, not a response object
                data = self.sentiment_client.get(f"/sentiment/{symbol}")
                return {'success': True, 'data': data}
            else:
                # Fallback sentiment analysis
                return {
                    'success': True,
                    'data': {
                        'symbol': symbol,
                        'overall_sentiment': 0.0,
                        'confidence_score': 0.5,
                        'analysis_timestamp': datetime.now().isoformat()
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting sentiment data for {symbol}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _generate_trading_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signal"""
        try:
            # Create a basic trading signal
            signal = {
                'symbol': signal_data['symbol'],
                'action': 'BUY',  # Simplified logic
                'confidence': 65.0,
                'entry_price': signal_data['market_data'].get('current_price', 100.0),
                'position_size': 10000,
                'stop_loss': signal_data['market_data'].get('current_price', 100.0) * 0.98,
                'profit_target': signal_data['market_data'].get('current_price', 100.0) * 1.05,
                'market_context': signal_data['market_data'].get('market_context', 'NEUTRAL'),
                'sentiment_score': signal_data.get('sentiment_score', {}).get('overall_sentiment', 0.0) if signal_data.get('sentiment_score') else 0.0,
                'timestamp': datetime.now().isoformat()
            }
            
            return {'success': True, 'data': signal}
            
        except Exception as e:
            logger.error(f"Error generating trading signal: {e}")
            return {'success': False, 'error': str(e)}
    
    def _validate_trading_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate trading signal"""
        try:
            if self.trading_client:
                payload = {'signal': signal_data, 'validate_only': True}
                # ServiceClient.post() returns JSON data directly, not a response object
                data = self.trading_client.post("/trading/analyze", json=payload)
                return {'success': True, 'data': data}
            else:
                # Fallback validation
                validation = {
                    'is_valid': True,
                    'warnings': [],
                    'errors': [],
                    'risk_metrics': {
                        'position_size': signal_data.get('position_size', 0),
                        'confidence': signal_data.get('confidence', 0)
                    }
                }
                
                # Basic validation checks
                if signal_data.get('confidence', 0) < 60:
                    validation['warnings'].append("Low confidence signal")
                
                return {'success': True, 'data': validation}
                
        except Exception as e:
            logger.error(f"Error validating trading signal: {e}")
            return {'success': False, 'error': str(e)}
    
    def _check_service_health(self):
        """Check health of all services"""
        # Check trading service
        try:
            if self.trading_client:
                response = self.trading_client.get("/health", timeout=5)
                self.service_status['trading'] = {
                    'healthy': response.status_code == 200,
                    'last_check': datetime.now().isoformat(),
                    'error': None if response.status_code == 200 else f"HTTP {response.status_code}"
                }
            else:
                self.service_status['trading'] = {
                    'healthy': False,
                    'last_check': datetime.now().isoformat(),
                    'error': "Service client not available"
                }
        except Exception as e:
            self.service_status['trading'] = {
                'healthy': False,
                'last_check': datetime.now().isoformat(),
                'error': str(e)
            }
        
        # Check sentiment service
        try:
            if self.sentiment_client:
                response = self.sentiment_client.get("/health", timeout=5)
                self.service_status['sentiment'] = {
                    'healthy': response.status_code == 200,
                    'last_check': datetime.now().isoformat(),
                    'error': None if response.status_code == 200 else f"HTTP {response.status_code}"
                }
            else:
                self.service_status['sentiment'] = {
                    'healthy': False,
                    'last_check': datetime.now().isoformat(),
                    'error': "Service client not available"
                }
        except Exception as e:
            self.service_status['sentiment'] = {
                'healthy': False,
                'last_check': datetime.now().isoformat(),
                'error': str(e)
            }
    
    def _get_portfolio_status(self) -> Dict[str, Any]:
        """Get portfolio status"""
        try:
            if self.trading_client:
                # ServiceClient.get() returns JSON data directly, not a response object
                data = self.trading_client.get("/trading/portfolio")
                return data
            else:
                # Fallback portfolio status
                return {
                    'total_positions': 0,
                    'total_value': 0,
                    'available_cash': 100000,
                    'unrealized_pnl': 0,
                    'daily_pnl': 0,
                    'portfolio_risk': 0
                }
                
        except Exception as e:
            logger.error(f"Error getting portfolio status: {e}")
            return {'error': str(e)}


# Initialize service core
orchestrator_service = OrchestratorServiceCore()


# FastAPI endpoints (if available)
if FASTAPI_AVAILABLE and PYDANTIC_AVAILABLE:
    
    class PredictionRequest(BaseModel):
        symbol: str
        market_data: Dict[str, Any] = {}
    
    class BatchAnalysisRequest(BaseModel):
        symbols: List[str]
    
    @app.post("/orchestrate/predict")
    async def orchestrate_prediction(request: PredictionRequest):
        """Orchestrate complete prediction workflow for a symbol"""
        try:
            result = orchestrator_service.orchestrate_prediction_workflow(
                request.symbol, request.market_data
            )
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error in orchestrated prediction: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/orchestrate/batch")
    async def orchestrate_batch_analysis(request: BatchAnalysisRequest):
        """Orchestrate batch analysis for multiple symbols"""
        try:
            result = orchestrator_service.coordinate_batch_analysis(request.symbols)
            return JSONResponse(content=result)
        except Exception as e:
            logger.error(f"Error in batch orchestration: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/system/status")
    async def get_system_status():
        """Get comprehensive system status"""
        try:
            status = orchestrator_service.get_system_status()
            return JSONResponse(content=status)
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        try:
            status = orchestrator_service.get_system_status()
            
            return JSONResponse(content={
                'status': 'healthy',
                'service': 'orchestrator',
                'system_health': status.get('system_health', 0),
                'services_available': len([s for s in status.get('services', {}).values() if s.get('healthy')]),
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    'status': 'unhealthy',
                    'service': 'orchestrator',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
            )


# Legacy compatibility functions
def orchestrate_symbol_prediction(symbol: str, market_data: dict = None) -> dict:
    """Legacy function for orchestrated prediction"""
    return orchestrator_service.orchestrate_prediction_workflow(symbol, market_data or {})


def get_full_system_status() -> dict:
    """Legacy function for system status"""
    return orchestrator_service.get_system_status()


def coordinate_multi_symbol_analysis(symbols: List[str]) -> dict:
    """Legacy function for batch analysis"""
    return orchestrator_service.coordinate_batch_analysis(symbols)


# Main execution
if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        import uvicorn
        logger.info("Starting Orchestrator Service on port 8000")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        logger.info("Orchestrator Service running in compatibility mode (FastAPI not available)")
        print("Orchestrator Service Core initialized successfully")
        
        # Test system status
        status = orchestrator_service.get_system_status()
        print(f"System Status: {status['overall_status']}")
        print(f"System Health: {status['system_health']:.2f}")
        
        # Test a sample prediction
        test_result = orchestrator_service.orchestrate_prediction_workflow("CBA", {'current_price': 168.50})
        print(f"Test prediction success: {test_result['success']}")
