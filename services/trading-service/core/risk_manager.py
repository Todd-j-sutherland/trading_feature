"""
Risk Manager - Handles trading risk management and validation.
"""

from typing import Dict, Any
from datetime import datetime
import json
import os


class RiskManager:
    """Manages trading risk and position validation."""
    
    def __init__(self, config_file: str = "risk_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load risk management configuration."""
        default_config = {
            "max_position_size": 10000,  # Maximum position size in dollars
            "max_portfolio_exposure": 100000,  # Maximum total portfolio exposure
            "max_positions_per_symbol": 3,  # Maximum positions per symbol
            "stop_loss_percentage": 0.05,  # 5% stop loss
            "max_daily_loss": 5000,  # Maximum daily loss in dollars
            "allowed_symbols": ["CBA.AX", "ANZ.AX", "WBC.AX", "NAB.AX", "MQG.AX"],
            "trading_hours": {
                "start": "10:00",
                "end": "16:00",
                "timezone": "AEST"
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"Error loading risk config: {e}")
        
        return default_config
    
    def validate_position(self, symbol: str, quantity: int, price: float) -> bool:
        """Validate if a position meets risk management criteria."""
        # Check symbol is allowed
        if symbol not in self.config["allowed_symbols"]:
            print(f"Symbol {symbol} not in allowed symbols")
            return False
        
        # Check position size
        position_value = abs(quantity * price)
        if position_value > self.config["max_position_size"]:
            print(f"Position size ${position_value} exceeds maximum ${self.config['max_position_size']}")
            return False
        
        # Check trading hours (simplified - in real implementation would check timezone)
        current_hour = datetime.now().hour
        start_hour = int(self.config["trading_hours"]["start"].split(":")[0])
        end_hour = int(self.config["trading_hours"]["end"].split(":")[0])
        
        if not (start_hour <= current_hour < end_hour):
            print(f"Trading outside allowed hours: {current_hour}")
            return False
        
        return True
    
    def calculate_position_risk(self, symbol: str, quantity: int, entry_price: float, current_price: float) -> Dict[str, Any]:
        """Calculate risk metrics for a position."""
        position_value = abs(quantity * current_price)
        price_change = (current_price - entry_price) / entry_price if entry_price > 0 else 0
        
        # Calculate stop loss level
        if quantity > 0:  # LONG position
            stop_loss_price = entry_price * (1 - self.config["stop_loss_percentage"])
        else:  # SHORT position
            stop_loss_price = entry_price * (1 + self.config["stop_loss_percentage"])
        
        return {
            "position_value": position_value,
            "price_change_percent": price_change * 100,
            "stop_loss_price": stop_loss_price,
            "risk_amount": position_value * self.config["stop_loss_percentage"],
            "should_stop_loss": (
                (quantity > 0 and current_price <= stop_loss_price) or
                (quantity < 0 and current_price >= stop_loss_price)
            )
        }
    
    def check_portfolio_risk(self, total_exposure: float, daily_pnl: float) -> Dict[str, Any]:
        """Check overall portfolio risk metrics."""
        exposure_limit_used = (total_exposure / self.config["max_portfolio_exposure"]) * 100
        daily_loss_limit_used = abs(min(0, daily_pnl) / self.config["max_daily_loss"]) * 100
        
        return {
            "total_exposure": total_exposure,
            "exposure_limit_percent": exposure_limit_used,
            "daily_pnl": daily_pnl,
            "daily_loss_limit_percent": daily_loss_limit_used,
            "risk_level": self._calculate_risk_level(exposure_limit_used, daily_loss_limit_used),
            "recommendations": self._get_risk_recommendations(exposure_limit_used, daily_loss_limit_used)
        }
    
    def _calculate_risk_level(self, exposure_percent: float, loss_percent: float) -> str:
        """Calculate overall risk level."""
        max_percent = max(exposure_percent, loss_percent)
        
        if max_percent < 50:
            return "LOW"
        elif max_percent < 80:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _get_risk_recommendations(self, exposure_percent: float, loss_percent: float) -> list:
        """Get risk management recommendations."""
        recommendations = []
        
        if exposure_percent > 80:
            recommendations.append("Consider reducing position sizes - high portfolio exposure")
        
        if loss_percent > 70:
            recommendations.append("Daily loss limit approaching - consider closing losing positions")
        
        if exposure_percent < 30 and loss_percent < 30:
            recommendations.append("Low risk - opportunity to increase position sizes")
        
        return recommendations
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update risk management configuration."""
        self.config.update(new_config)
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving risk config: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """Get current risk management configuration."""
        return self.config.copy()