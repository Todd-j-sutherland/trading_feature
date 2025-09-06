"""
Trading Service - Core Position Management and Risk Validation

This service handles:
- Position management and tracking
- Risk validation and compliance
- Trade execution coordination
- Portfolio analysis
"""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
import traceback

try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks
    from fastapi.responses import JSONResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

# Local imports with fallbacks
from services.shared.models.trading_models import (
    TradingSignal, Position, PortfolioSummary, 
    TradingRequest, RiskValidationRequest
)
from services.shared.utils.database_utils import DatabaseManager
from services.shared.utils.logging_utils import setup_logging
from services.shared.config.service_config import get_service_config
from services.shared.config.database_config import get_database_config


# Setup logging
logger = setup_logging("trading_service")
config = get_service_config("trading")
db_config = get_database_config()

# Initialize FastAPI app (if available)
if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Trading Service",
        description="Position management and risk validation for ASX trading system",
        version="1.0.0"
    )
else:
    app = None
    logger.warning("FastAPI not available - service will run in compatibility mode")


class TradingServiceCore:
    """Core trading service functionality (works without FastAPI)"""
    
    def __init__(self):
        self.db_manager = DatabaseManager(db_config.primary_db_path)
        self.paper_trading_db = DatabaseManager(db_config.paper_trading_db_path)
        self.risk_limits = {
            'max_position_size': 15000,  # $15K max position
            'min_position_size': 5000,   # $5K min position  
            'max_risk_per_trade': 0.15,  # 15% max risk
            'stop_loss_percentage': 2.0,  # 2% stop loss
            'max_daily_trades': 10,       # Max trades per day
            'max_portfolio_risk': 0.30    # 30% max portfolio risk
        }
        
    def validate_trading_signal(self, signal: TradingSignal) -> Dict[str, Any]:
        """Validate a trading signal against risk parameters"""
        try:
            validation_result = {
                'is_valid': True,
                'warnings': [],
                'errors': [],
                'risk_metrics': {}
            }
            
            # Position size validation
            if signal.position_size:
                if signal.position_size < self.risk_limits['min_position_size']:
                    validation_result['warnings'].append(
                        f"Position size ${signal.position_size} below minimum ${self.risk_limits['min_position_size']}"
                    )
                
                if signal.position_size > self.risk_limits['max_position_size']:
                    validation_result['errors'].append(
                        f"Position size ${signal.position_size} exceeds maximum ${self.risk_limits['max_position_size']}"
                    )
                    validation_result['is_valid'] = False
            
            # Confidence threshold validation
            min_confidence = 70 if signal.market_context != 'BEARISH' else 80
            if signal.confidence < min_confidence:
                validation_result['warnings'].append(
                    f"Confidence {signal.confidence}% below recommended threshold {min_confidence}%"
                )
            
            # Stop loss validation
            if signal.stop_loss and signal.entry_price:
                stop_loss_pct = abs(signal.entry_price - signal.stop_loss) / signal.entry_price * 100
                validation_result['risk_metrics']['stop_loss_pct'] = stop_loss_pct
                
                if stop_loss_pct > self.risk_limits['stop_loss_percentage']:
                    validation_result['warnings'].append(
                        f"Stop loss {stop_loss_pct:.1f}% exceeds recommended {self.risk_limits['stop_loss_percentage']}%"
                    )
            
            # Daily trading limit check
            today_trades = self._get_daily_trade_count()
            validation_result['risk_metrics']['daily_trades'] = today_trades
            
            if today_trades >= self.risk_limits['max_daily_trades']:
                validation_result['errors'].append(
                    f"Daily trade limit reached: {today_trades}/{self.risk_limits['max_daily_trades']}"
                )
                validation_result['is_valid'] = False
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating trading signal: {e}")
            return {
                'is_valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'risk_metrics': {}
            }
    
    def create_position(self, signal: TradingSignal) -> Optional[Position]:
        """Create a new position from a trading signal"""
        try:
            # Validate signal first
            validation = self.validate_trading_signal(signal)
            if not validation['is_valid']:
                logger.warning(f"Cannot create position - validation failed: {validation['errors']}")
                return None
            
            # Create position object
            position = Position(
                position_id=f"{signal.symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                symbol=signal.symbol,
                action=signal.action,
                shares=signal.shares or self._calculate_shares(signal),
                entry_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                profit_target=signal.profit_target,
                confidence=signal.confidence,
                status='PENDING'
            )
            
            # Save to database
            self._save_position(position)
            
            logger.info(f"Created position: {position.position_id} for {position.symbol}")
            return position
            
        except Exception as e:
            logger.error(f"Error creating position: {e}")
            return None
    
    def get_portfolio_summary(self) -> PortfolioSummary:
        """Get current portfolio summary"""
        try:
            # Get active positions
            positions = self._get_active_positions()
            
            # Calculate summary metrics
            total_value = sum(pos.current_value or 0 for pos in positions)
            unrealized_pnl = sum(pos.unrealized_pnl or 0 for pos in positions)
            invested_amount = sum(pos.entry_price * pos.shares for pos in positions)
            
            portfolio_summary = PortfolioSummary(
                total_positions=len(positions),
                total_value=total_value,
                available_cash=100000 - invested_amount,  # Paper trading account
                invested_amount=invested_amount,
                total_pnl=unrealized_pnl,  # For now, total_pnl = unrealized_pnl
                total_return_pct=(unrealized_pnl / invested_amount * 100) if invested_amount > 0 else 0.0,
                active_positions=len(positions),
                unrealized_pnl=unrealized_pnl,
                daily_pnl=self._get_daily_pnl(),
                portfolio_risk=self._calculate_portfolio_risk(positions)
            )
            
            return portfolio_summary
            
        except Exception as e:
            logger.error(f"Error getting portfolio summary: {e}")
            return PortfolioSummary(
                total_positions=0,
                total_value=0,
                available_cash=100000,
                invested_amount=0,
                total_pnl=0,
                total_return_pct=0.0,
                active_positions=0,
                unrealized_pnl=0,
                daily_pnl=0,
                portfolio_risk=0
            )
    
    def update_positions(self, market_prices: Dict[str, float]) -> int:
        """Update positions with current market prices"""
        try:
            positions = self._get_active_positions()
            updated_count = 0
            
            for position in positions:
                if position.symbol in market_prices:
                    current_price = market_prices[position.symbol]
                    
                    # Update position with current price
                    position.current_price = current_price
                    position.unrealized_pnl = (current_price - position.entry_price) * position.shares
                    
                    # Check stop loss/profit target triggers
                    if self._should_close_position(position):
                        position.status = 'TRIGGERED'
                        logger.info(f"Position {position.position_id} triggered for closure")
                    
                    # Save updated position
                    self._update_position(position)
                    updated_count += 1
            
            logger.info(f"Updated {updated_count} positions with market prices")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
            return 0
    
    def _get_daily_trade_count(self) -> int:
        """Get number of trades executed today"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            query = """
                SELECT COUNT(*) 
                FROM positions 
                WHERE DATE(entry_timestamp) = ? 
                AND status != 'CANCELLED'
            """
            result = self.paper_trading_db.fetch_one(query, (today,))
            return result[0] if result else 0
        except Exception:
            return 0
    
    def _calculate_shares(self, signal: TradingSignal) -> int:
        """Calculate number of shares based on position size and price"""
        if not signal.position_size or not signal.entry_price:
            return 0
        return int(signal.position_size / signal.entry_price)
    
    def _save_position(self, position: Position):
        """Save position to database"""
        query = """
            INSERT INTO positions (
                position_id, symbol, action, shares, entry_price, 
                stop_loss, profit_target, status, entry_timestamp, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            position.position_id, position.symbol, position.action,
            position.shares, position.entry_price, position.stop_loss,
            position.profit_target, position.status, 
            datetime.now().isoformat(), position.confidence
        )
        self.paper_trading_db.execute_query(query, params)
    
    def _get_active_positions(self) -> List[Position]:
        """Get all active positions"""
        query = "SELECT * FROM positions WHERE status IN ('OPEN', 'PENDING', 'TRIGGERED')"
        rows = self.paper_trading_db.fetch_all(query)
        
        positions = []
        for row in rows:
            position = Position(
                position_id=row[0],
                symbol=row[1],
                action=row[2],
                shares=row[3],
                entry_price=row[4],
                current_price=row[5],
                stop_loss=row[6],
                profit_target=row[7],
                status=row[8],
                confidence=row[11] if len(row) > 11 else None
            )
            positions.append(position)
        
        return positions
    
    def _update_position(self, position: Position):
        """Update position in database"""
        query = """
            UPDATE positions 
            SET current_price = ?, pnl = ?, status = ?
            WHERE position_id = ?
        """
        params = (
            position.current_price,
            position.unrealized_pnl,
            position.status,
            position.position_id
        )
        self.paper_trading_db.execute_query(query, params)
    
    def _should_close_position(self, position: Position) -> bool:
        """Check if position should be closed based on stop loss/profit target"""
        if not position.current_price:
            return False
        
        # Check stop loss
        if position.stop_loss:
            if position.action == 'BUY' and position.current_price <= position.stop_loss:
                return True
            elif position.action == 'SELL' and position.current_price >= position.stop_loss:
                return True
        
        # Check profit target
        if position.profit_target:
            if position.action == 'BUY' and position.current_price >= position.profit_target:
                return True
            elif position.action == 'SELL' and position.current_price <= position.profit_target:
                return True
        
        return False
    
    def _get_daily_pnl(self) -> float:
        """Get today's realized P&L"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            query = """
                SELECT COALESCE(SUM(pnl), 0) 
                FROM positions 
                WHERE DATE(exit_timestamp) = ? 
                AND status = 'CLOSED'
            """
            result = self.paper_trading_db.fetch_one(query, (today,))
            return result[0] if result else 0.0
        except Exception:
            return 0.0
    
    def _calculate_portfolio_risk(self, positions: List[Position]) -> float:
        """Calculate portfolio risk as percentage of total value"""
        if not positions:
            return 0.0
        
        try:
            total_invested = sum(pos.entry_price * pos.shares for pos in positions)
            max_loss = sum(
                abs(pos.entry_price - (pos.stop_loss or pos.entry_price * 0.98)) * pos.shares 
                for pos in positions
            )
            
            if total_invested > 0:
                return (max_loss / total_invested) * 100
            return 0.0
            
        except Exception:
            return 0.0


# Initialize service core
trading_service = TradingServiceCore()


# FastAPI endpoints (if available)
if FASTAPI_AVAILABLE and PYDANTIC_AVAILABLE:
    
    class TradingAnalysisRequest(BaseModel):
        signal: dict
        validate_only: bool = False
    
    class PositionUpdateRequest(BaseModel):
        market_prices: Dict[str, float]
    
    @app.post("/trading/analyze")
    async def analyze_trading_signal(request: TradingAnalysisRequest):
        """Analyze and optionally execute a trading signal"""
        try:
            # Convert dict to TradingSignal
            signal = TradingSignal.from_dict(request.signal)
            
            # Validate signal
            validation = trading_service.validate_trading_signal(signal)
            
            if request.validate_only:
                return JSONResponse(content=validation)
            
            # Create position if validation passes
            if validation['is_valid']:
                position = trading_service.create_position(signal)
                return JSONResponse(content={
                    'validation': validation,
                    'position_created': position.to_dict() if position else None
                })
            else:
                return JSONResponse(content={
                    'validation': validation,
                    'position_created': None
                })
                
        except Exception as e:
            logger.error(f"Error analyzing trading signal: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/trading/portfolio")
    async def get_portfolio():
        """Get current portfolio summary"""
        try:
            import json
            summary = trading_service.get_portfolio_summary()
            # Convert to dict
            if hasattr(summary, 'model_dump'):
                data = summary.model_dump()
            else:
                data = summary.__dict__.copy()
                
            # Use json.dumps with default=str to handle datetime objects
            json_data = json.dumps(data, default=str)
            return JSONResponse(content=json.loads(json_data))
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/trading/update-positions")
    async def update_positions(request: PositionUpdateRequest):
        """Update positions with current market prices"""
        try:
            updated_count = trading_service.update_positions(request.market_prices)
            return JSONResponse(content={
                'updated_positions': updated_count,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        try:
            # Test database connection
            portfolio = trading_service.get_portfolio_summary()
            
            return JSONResponse(content={
                'status': 'healthy',
                'service': 'trading',
                'database_connected': True,
                'portfolio_positions': portfolio.total_positions,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    'status': 'unhealthy',
                    'service': 'trading',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
            )


# Legacy compatibility functions
def validate_signal(signal_dict: dict) -> dict:
    """Legacy function for signal validation"""
    try:
        signal = TradingSignal.from_dict(signal_dict)
        return trading_service.validate_trading_signal(signal)
    except Exception as validation_error:
        # Return validation failure result instead of crashing
        return {
            'is_valid': False,
            'errors': [str(validation_error)],
            'signal': signal_dict,
            'validation_timestamp': datetime.now().isoformat()
        }


def create_position_from_signal(signal_dict: dict) -> Optional[dict]:
    """Legacy function for position creation"""
    signal = TradingSignal.from_dict(signal_dict)
    position = trading_service.create_position(signal)
    return position.to_dict() if position else None


def get_current_portfolio() -> dict:
    """Legacy function for portfolio summary"""
    summary = trading_service.get_portfolio_summary()
    return summary.to_dict()


# Main execution
if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        import uvicorn
        logger.info("Starting Trading Service on port 8001")
        uvicorn.run(app, host="0.0.0.0", port=8001)
    else:
        logger.info("Trading Service running in compatibility mode (FastAPI not available)")
        print("Trading Service Core initialized successfully")
        print(f"Portfolio Summary: {trading_service.get_portfolio_summary().to_dict()}")
