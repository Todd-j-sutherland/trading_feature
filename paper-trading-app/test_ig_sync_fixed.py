#!/usr/bin/env python3
import asyncio
from datetime import datetime
from ig_sync_engine import ig_sync_engine

async def test_sync_functionality():
    print("=" * 60)
    print("TESTING IG MARKETS SYNC WITH FIXED $32 TAKE PROFIT")
    print("=" * 60)
    
    test_trades = [
        {"id": "TEST_001", "symbol": "CBA.AX", "side": "BUY", "quantity": 100, "entry_price": 168.50},
        {"id": "TEST_002", "symbol": "NAB.AX", "side": "BUY", "quantity": 200, "entry_price": 28.50},
        {"id": "TEST_003", "symbol": "WBC.AX", "side": "BUY", "quantity": 150, "entry_price": 30.00}
    ]
    
    print(f"Testing {len(test_trades)} sample trades...")
    print(f"Fixed take profit price: ${ig_sync_engine.take_profit_price:.2f}")
    print(f"Stop loss percentage: {ig_sync_engine.stop_loss_pct * 100:.1f}%")
    print("-" * 60)
    
    for i, trade in enumerate(test_trades, 1):
        print(f"\n[{i}] Processing trade: {trade[\"symbol\"]}")
        print(f"    {trade[\"side\"]} {trade[\"quantity\"]} shares @ ${trade[\"entry_price\"]:.2f}")
        print(f"    Position value: ${trade[\"quantity\"] * trade[\"entry_price\"]:,.2f}")
        
        success = await ig_sync_engine.sync_paper_position_to_ig(trade)
        
        if success:
            print(f"    ✓ Successfully synced to IG demo account")
        else:
            print(f"    ✗ Failed to sync (may not meet criteria)")
        
        print(f"    Take profit logic:")
        if trade["side"] == "BUY" and trade["entry_price"] < ig_sync_engine.take_profit_price:
            profit_potential = ig_sync_engine.take_profit_price - trade["entry_price"]
            profit_pct = (profit_potential / trade["entry_price"]) * 100
            print(f"      → Take profit SET at ${ig_sync_engine.take_profit_price:.2f}")
            print(f"      → Potential profit: ${profit_potential:.2f} ({profit_pct:.1f}%)")
        else:
            print(f"      → Take profit NOT set (entry ${trade[\"entry_price\"]:.2f} vs target ${ig_sync_engine.take_profit_price:.2f})")
    
    print("\n" + "=" * 60)
    print("FINAL SYNC STATUS")
    print("=" * 60)
    
    status = ig_sync_engine.get_sync_status()
    positions = ig_sync_engine.get_synced_positions()
    
    print(f"Total synced positions: {status[\"total_synced_positions\"]}")
    print(f"Active positions: {status[\"active_positions\"]}")
    print(f"Demo mode: {status[\"demo_mode\"]}")
    print(f"Sync enabled: {status[\"sync_enabled\"]}")
    
    if positions:
        print(f"\nDetailed positions:")
        for pos in positions:
            print(f"  - {pos[\"symbol\"]}: {pos[\"side\"]} {pos[\"quantity\"]} @ ${pos[\"entry_price\"]:.2f}")
            print(f"    IG Position ID: {pos[\"ig_position_id\"]}")
            print(f"    Status: {pos[\"status\"]}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE - Check dashboard at http://170.64.199.151:8503")
    print("=" * 60)

if __name__ == "__main__":
    print("Starting IG Markets sync test...")
    asyncio.run(test_sync_functionality())
