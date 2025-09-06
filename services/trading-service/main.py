"""
Trading Service - Core trading logic and position management.

This service handles all trading-related operations including:
- Position tracking and management
- Risk management
- Signal generation and execution
- Paper trading simulation
- Integration with trading platforms (Alpaca, Moomoo, etc.)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
import uvicorn
from datetime import datetime
import sys
import os

# Add shared modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../"))

from shared.models import TradingPosition, TradingSignal, StockPrice
from shared.utils import setup_service_logging, health_check_endpoint
from core.position_manager import PositionManager
from core.risk_manager import RiskManager
from core.signal_generator import SignalGenerator


class TradingService:
    """Main trading service class."""
    
    def __init__(self):
        self.logger = setup_service_logging("trading-service")
        self.position_manager = PositionManager()
        self.risk_manager = RiskManager()
        self.signal_generator = SignalGenerator()
        self.logger.info("Trading service initialized")
    
    def get_positions(self, symbol: Optional[str] = None) -> List[TradingPosition]:
        """Get current trading positions."""
        return self.position_manager.get_positions(symbol)
    
    def open_position(self, symbol: str, quantity: int, price: float, position_type: str) -> TradingPosition:
        """Open a new trading position."""
        # Risk check
        if not self.risk_manager.validate_position(symbol, quantity, price):
            raise HTTPException(status_code=400, detail="Position fails risk management checks")
        
        position = self.position_manager.open_position(symbol, quantity, price, position_type)
        self.logger.info(f"Opened position: {symbol} {quantity} shares at ${price}")
        return position
    
    def close_position(self, position_id: str, price: float) -> TradingPosition:
        """Close an existing position."""
        position = self.position_manager.close_position(position_id, price)
        self.logger.info(f"Closed position: {position.symbol} PnL: ${position.realized_pnl}")
        return position
    
    def generate_signal(self, symbol: str, market_data: Dict[str, Any]) -> TradingSignal:
        """Generate trading signal for a symbol."""
        signal = self.signal_generator.generate_signal(symbol, market_data)
        self.logger.info(f"Generated signal for {symbol}: {signal}")
        return signal
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary statistics."""
        positions = self.position_manager.get_all_positions()
        
        total_value = sum(pos.current_price * pos.quantity for pos in positions)
        total_pnl = sum(pos.unrealized_pnl or 0 for pos in positions)
        
        return {
            "total_positions": len(positions),
            "total_value": total_value,
            "total_pnl": total_pnl,
            "positions": [pos.__dict__ for pos in positions],
            "timestamp": datetime.utcnow().isoformat()
        }


# FastAPI app
app = FastAPI(title="Trading Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service instance
trading_service = TradingService()

# Health check endpoint
@app.get("/health")
async def health_check():
    """Service health check."""
    health_check_func = health_check_endpoint("trading-service", "1.0.0")
    return health_check_func()

@app.get("/positions")
async def get_positions(symbol: Optional[str] = None):
    """Get current positions."""
    try:
        positions = trading_service.get_positions(symbol)
        return {"positions": [pos.__dict__ for pos in positions]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/positions")
async def open_position(
    symbol: str,
    quantity: int,
    price: float,
    position_type: str = "LONG"
):
    """Open a new position."""
    try:
        position = trading_service.open_position(symbol, quantity, price, position_type)
        return {"position": position.__dict__}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/positions/{position_id}")
async def close_position(position_id: str, price: float):
    """Close a position."""
    try:
        position = trading_service.close_position(position_id, price)
        return {"position": position.__dict__}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/signals/{symbol}")
async def generate_signal(symbol: str, market_data: Dict[str, Any]):
    """Generate trading signal."""
    try:
        signal = trading_service.generate_signal(symbol, market_data)
        return {"symbol": symbol, "signal": signal.value}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/portfolio")
async def get_portfolio_summary():
    """Get portfolio summary."""
    try:
        return trading_service.get_portfolio_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)