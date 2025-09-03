import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import json
import sys
import os

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IGSyncEngine:
    def __init__(self):
        self.sync_enabled = True
        self.demo_mode = True
        self.synced_positions = {}
        self.failed_syncs = []
        
        # Configuration
        self.take_profit_price = 32.00  # Fixed take profit at 2
        self.stop_loss_pct = 0.02       # 2% stop loss
        self.min_position_value = 1000  # Minimum 000 position
        
        logger.info('IG Sync Engine initialized with fixed take profit at 2.00')
    
    def should_sync_position(self, symbol: str, position_value: float) -> bool:
        allowed_symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'BHP.AX', 'RIO.AX']
        
        if symbol not in allowed_symbols:
            return False
        if position_value < self.min_position_value:
            return False
        return True
    
    async def sync_paper_position_to_ig(self, trade_data: Dict) -> bool:
        try:
            symbol = trade_data['symbol']
            side = trade_data['side']
            quantity = int(trade_data['quantity'])
            entry_price = trade_data['entry_price']
            position_value = quantity * entry_price
            
            if not self.should_sync_position(symbol, position_value):
                logger.info(f'Position {symbol} not eligible for sync')
                return False
            
            logger.info(f'Syncing {side} {quantity} {symbol} @  to IG demo')
            
            # Simulate IG order creation
            position_id = f'IG_{symbol}_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
            
            # Store synced position
            self.synced_positions[position_id] = {
                'paper_trade_id': trade_data.get('id'),
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'entry_price': entry_price,
                'ig_position_id': position_id,
                'sync_timestamp': datetime.now().isoformat(),
                'status': 'OPEN'
            }
            
            # Set up exit orders
            await self.setup_exit_orders(position_id, symbol, side, entry_price, quantity)
            
            logger.info(f'Successfully synced position {position_id} to IG demo')
            return True
            
        except Exception as e:
            logger.error(f'Error syncing position to IG: {e}')
            return False
    
    async def setup_exit_orders(self, position_id: str, symbol: str, side: str, entry_price: float, quantity: int):
        try:
            # Stop loss order
            stop_loss_pct = self.stop_loss_pct
            if side == 'BUY':
                stop_price = entry_price * (1 - stop_loss_pct)
            else:
                stop_price = entry_price * (1 + stop_loss_pct)
            
            logger.info(f'Stop loss set for {position_id} @ ')
            
            # Take profit order - FIXED PRICE AT 2
            take_profit_price = self.take_profit_price
            
            # Only set take profit if it makes sense for the position
            if side == 'BUY' and entry_price < take_profit_price:
                logger.info(f'Take profit set for {position_id} @  (Fixed)')
            elif side == 'SELL' and entry_price > take_profit_price:
                logger.info(f'Take profit set for {position_id} @  (Fixed)')
            else:
                logger.info(f'Take profit not set - entry price  vs target ')
                
        except Exception as e:
            logger.error(f'Error setting up exit orders for {position_id}: {e}')
    
    def get_sync_status(self) -> Dict:
        return {
            'sync_enabled': self.sync_enabled,
            'demo_mode': self.demo_mode,
            'total_synced_positions': len(self.synced_positions),
            'active_positions': len([p for p in self.synced_positions.values() if p['status'] == 'OPEN']),
            'failed_syncs': len(self.failed_syncs),
            'take_profit_price': self.take_profit_price,
            'last_sync': datetime.now().isoformat()
        }
    
    def get_synced_positions(self) -> List[Dict]:
        return list(self.synced_positions.values())

# Global instance
ig_sync_engine = IGSyncEngine()
