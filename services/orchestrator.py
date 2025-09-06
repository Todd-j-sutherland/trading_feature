"""
Service Orchestrator - Coordinates between different services.

This serves as the main entry point and coordinator for the services-rich
trading system. It manages service discovery, health monitoring, and 
provides a unified API interface.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio
import httpx
from typing import Dict, Any, List
from datetime import datetime
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from shared.models import TradingSignal
from shared.utils import setup_service_logging, ServiceClient


class ServiceOrchestrator:
    """Orchestrates communication between services."""
    
    def __init__(self):
        self.logger = setup_service_logging("orchestrator")
        
        # Service endpoints
        self.services = {
            "trading": ServiceClient("http://localhost:8001"),
            "sentiment": ServiceClient("http://localhost:8002"),
            "ml": ServiceClient("http://localhost:8003"),
            "data": ServiceClient("http://localhost:8004"),
        }
        
        self.logger.info("Service orchestrator initialized")
    
    async def health_check_all_services(self) -> Dict[str, Any]:
        """Check health of all services."""
        results = {}
        
        for service_name, client in self.services.items():
            try:
                health = client.health_check()
                results[service_name] = {
                    "status": "healthy",
                    "details": health
                }
            except Exception as e:
                results[service_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return results
    
    async def generate_trading_recommendation(self, symbol: str) -> Dict[str, Any]:
        """Generate a comprehensive trading recommendation for a symbol."""
        try:
            # Collect data from different services
            tasks = [
                self._get_sentiment_data(symbol),
                self._get_market_data(symbol),
                self._get_ml_prediction(symbol),
                self._get_portfolio_context()
            ]
            
            sentiment_data, market_data, ml_data, portfolio_context = await asyncio.gather(*tasks)
            
            # Combine all data for signal generation
            combined_data = {
                "sentiment": sentiment_data,
                "technical": market_data.get("technical", {}),
                "ml_prediction": ml_data
            }
            
            # Get trading signal
            signal_response = self.services["trading"].post(f"/signals/{symbol}", combined_data)
            signal = signal_response.get("signal", "HOLD")
            
            # Return comprehensive recommendation
            return {
                "symbol": symbol,
                "recommendation": signal,
                "confidence": self._calculate_overall_confidence(sentiment_data, ml_data),
                "reasoning": self._generate_reasoning(sentiment_data, market_data, ml_data, signal),
                "risk_assessment": self._assess_risk(symbol, portfolio_context),
                "data_sources": {
                    "sentiment": sentiment_data,
                    "market": market_data,
                    "ml_prediction": ml_data,
                    "portfolio": portfolio_context
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating recommendation for {symbol}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _get_sentiment_data(self, symbol: str) -> Dict[str, Any]:
        """Get sentiment data for symbol."""
        try:
            return self.services["sentiment"].get(f"/sentiment/{symbol}")
        except Exception as e:
            self.logger.warning(f"Failed to get sentiment for {symbol}: {e}")
            return {"score": 0.0, "confidence": 0.0, "error": str(e)}
    
    async def _get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get market data for symbol."""
        try:
            return self.services["data"].get(f"/market-data/{symbol}")
        except Exception as e:
            self.logger.warning(f"Failed to get market data for {symbol}: {e}")
            return {"current_price": 0.0, "technical": {}, "error": str(e)}
    
    async def _get_ml_prediction(self, symbol: str) -> Dict[str, Any]:
        """Get ML prediction for symbol."""
        try:
            return self.services["ml"].get(f"/predict/{symbol}")
        except Exception as e:
            self.logger.warning(f"Failed to get ML prediction for {symbol}: {e}")
            return {"predicted_direction": "HOLD", "confidence": 0.0, "error": str(e)}
    
    async def _get_portfolio_context(self) -> Dict[str, Any]:
        """Get current portfolio context."""
        try:
            return self.services["trading"].get("/portfolio")
        except Exception as e:
            self.logger.warning(f"Failed to get portfolio context: {e}")
            return {"total_value": 0.0, "total_positions": 0, "error": str(e)}
    
    def _calculate_overall_confidence(self, sentiment_data: Dict, ml_data: Dict) -> float:
        """Calculate overall confidence score."""
        sentiment_conf = sentiment_data.get("confidence", 0.0)
        ml_conf = ml_data.get("confidence", 0.0)
        
        # Average confidence with ML weighted higher
        return (sentiment_conf * 0.4 + ml_conf * 0.6)
    
    def _generate_reasoning(self, sentiment_data: Dict, market_data: Dict, ml_data: Dict, signal: str) -> List[str]:
        """Generate human-readable reasoning for the recommendation."""
        reasons = []
        
        # Sentiment reasoning
        sentiment_score = sentiment_data.get("score", 0.0)
        if sentiment_score > 0.3:
            reasons.append("Positive market sentiment detected")
        elif sentiment_score < -0.3:
            reasons.append("Negative market sentiment detected")
        else:
            reasons.append("Neutral market sentiment")
        
        # ML reasoning
        ml_direction = ml_data.get("predicted_direction", "HOLD")
        ml_confidence = ml_data.get("confidence", 0.0)
        if ml_confidence > 0.7:
            reasons.append(f"High-confidence ML prediction: {ml_direction}")
        elif ml_confidence > 0.5:
            reasons.append(f"Moderate-confidence ML prediction: {ml_direction}")
        
        # Technical reasoning
        technical = market_data.get("technical", {})
        rsi = technical.get("rsi", 50)
        if rsi > 70:
            reasons.append("RSI indicates overbought conditions")
        elif rsi < 30:
            reasons.append("RSI indicates oversold conditions")
        
        return reasons
    
    def _assess_risk(self, symbol: str, portfolio_context: Dict) -> Dict[str, Any]:
        """Assess risk for the trade."""
        total_positions = portfolio_context.get("total_positions", 0)
        total_value = portfolio_context.get("total_value", 0.0)
        
        # Simple risk assessment
        risk_level = "LOW"
        if total_positions > 10:
            risk_level = "HIGH"
        elif total_positions > 5:
            risk_level = "MEDIUM"
        
        return {
            "level": risk_level,
            "factors": {
                "portfolio_concentration": total_positions,
                "total_exposure": total_value
            },
            "recommendation": "Consider position sizing" if risk_level == "HIGH" else "Standard position size acceptable"
        }


# FastAPI app
app = FastAPI(title="Trading System Orchestrator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Orchestrator instance
orchestrator = ServiceOrchestrator()

@app.get("/health")
async def health_check():
    """Overall system health check."""
    service_health = await orchestrator.health_check_all_services()
    
    healthy_count = sum(1 for s in service_health.values() if s["status"] == "healthy")
    total_count = len(service_health)
    
    return {
        "status": "healthy" if healthy_count == total_count else "degraded",
        "services": service_health,
        "summary": f"{healthy_count}/{total_count} services healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/recommend/{symbol}")
async def get_trading_recommendation(symbol: str):
    """Get comprehensive trading recommendation."""
    return await orchestrator.generate_trading_recommendation(symbol)

@app.get("/services")
async def list_services():
    """List all registered services."""
    return {
        "services": list(orchestrator.services.keys()),
        "endpoints": {
            name: client.base_url for name, client in orchestrator.services.items()
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)