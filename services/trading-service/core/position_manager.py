"""
Position Manager - Handles trading position lifecycle.
"""

from typing import List, Optional, Dict
from datetime import datetime
import uuid
import json
import os

from shared.models import TradingPosition


class PositionManager:
    """Manages trading positions."""
    
    def __init__(self, data_file: str = "positions.json"):
        self.data_file = data_file
        self.positions: Dict[str, TradingPosition] = {}
        self._load_positions()
    
    def _load_positions(self):
        """Load positions from persistence."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    for pos_id, pos_data in data.items():
                        # Convert dict back to TradingPosition
                        pos_data['entry_time'] = datetime.fromisoformat(pos_data['entry_time'])
                        self.positions[pos_id] = TradingPosition(**pos_data)
            except Exception as e:
                print(f"Error loading positions: {e}")
    
    def _save_positions(self):
        """Save positions to persistence."""
        try:
            data = {}
            for pos_id, position in self.positions.items():
                pos_dict = position.__dict__.copy()
                pos_dict['entry_time'] = position.entry_time.isoformat()
                data[pos_id] = pos_dict
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving positions: {e}")
    
    def open_position(self, symbol: str, quantity: int, entry_price: float, position_type: str) -> TradingPosition:
        """Open a new trading position."""
        position_id = str(uuid.uuid4())
        
        position = TradingPosition(
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            current_price=entry_price,
            entry_time=datetime.utcnow(),
            position_type=position_type,
            unrealized_pnl=0.0
        )
        
        self.positions[position_id] = position
        self._save_positions()
        
        return position
    
    def close_position(self, position_id: str, exit_price: float) -> TradingPosition:
        """Close a trading position."""
        if position_id not in self.positions:
            raise ValueError(f"Position {position_id} not found")
        
        position = self.positions[position_id]
        
        # Calculate PnL
        if position.position_type == "LONG":
            pnl = (exit_price - position.entry_price) * position.quantity
        else:  # SHORT
            pnl = (position.entry_price - exit_price) * position.quantity
        
        position.realized_pnl = pnl
        position.current_price = exit_price
        
        # Remove from active positions
        del self.positions[position_id]
        self._save_positions()
        
        return position
    
    def update_position_prices(self, symbol: str, current_price: float):
        """Update current prices for positions in a symbol."""
        for position in self.positions.values():
            if position.symbol == symbol:
                position.current_price = current_price
                
                # Calculate unrealized PnL
                if position.position_type == "LONG":
                    position.unrealized_pnl = (current_price - position.entry_price) * position.quantity
                else:  # SHORT
                    position.unrealized_pnl = (position.entry_price - current_price) * position.quantity
        
        self._save_positions()
    
    def get_positions(self, symbol: Optional[str] = None) -> List[TradingPosition]:
        """Get positions, optionally filtered by symbol."""
        positions = list(self.positions.values())
        
        if symbol:
            positions = [pos for pos in positions if pos.symbol == symbol]
        
        return positions
    
    def get_all_positions(self) -> List[TradingPosition]:
        """Get all positions."""
        return list(self.positions.values())
    
    def get_position_count(self, symbol: Optional[str] = None) -> int:
        """Get count of positions."""
        if symbol:
            return len([pos for pos in self.positions.values() if pos.symbol == symbol])
        return len(self.positions)
    
    def get_total_exposure(self, symbol: Optional[str] = None) -> float:
        """Get total exposure (position value)."""
        positions = self.get_positions(symbol)
        return sum(abs(pos.quantity * pos.current_price) for pos in positions)