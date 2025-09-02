#!/usr/bin/env python3
"""
Validate Paper Trading Data Against IG Markets
Compare paper trading dashboard values with IG Markets real-time data
"""

import sys
import os
import logging
from datetime import datetime
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add paper trading app to path
paper_trading_path = os.path.join(os.path.dirname(__file__), 'paper-trading-app')
sys.path.append(paper_trading_path)

def validate_paper_trading_vs_ig_markets():
    """Compare paper trading positions with IG Markets current data"""
    
    logger.info("🔍 PAPER TRADING DATA VALIDATION")
    logger.info("=" * 60)
    logger.info(f"⏰ Validation Time: {datetime.now()}")
    logger.info("=" * 60)
    
    try:
        # Import paper trading service
        from enhanced_paper_trading_service_with_ig import EnhancedPaperTradingServiceWithIG
        
        # Initialize service
        service = EnhancedPaperTradingServiceWithIG()
        
        # Get portfolio summary
        logger.info("📊 PAPER TRADING PORTFOLIO SUMMARY")
        portfolio = service.get_enhanced_portfolio_summary()
        
        account = portfolio.get('account', {})
        positions = portfolio.get('positions', [])
        
        logger.info(f"💰 Portfolio Value: ${account.get('portfolio_value', 0):,.2f}")
        logger.info(f"💵 Cash Balance: ${account.get('cash_balance', 0):,.2f}")
        logger.info(f"📈 Total P&L: ${account.get('total_pnl', 0):+,.2f} ({account.get('total_pnl_pct', 0):+.2f}%)")
        logger.info(f"📊 Active Positions: {len(positions)}")
        
        # Validate each position against IG Markets
        if positions:
            logger.info("\n🔍 POSITION VALIDATION AGAINST IG MARKETS")
            logger.info("-" * 60)
            
            total_discrepancies = 0
            
            for i, pos in enumerate(positions, 1):
                symbol = pos['symbol']
                paper_price = pos.get('current_price', 0)
                quantity = pos['quantity']
                paper_value = pos.get('market_value', 0)
                paper_pnl = pos.get('unrealized_pnl', 0)
                
                logger.info(f"\n📍 Position {i}: {symbol}")
                logger.info(f"   📊 Paper Trading Data:")
                logger.info(f"      • Quantity: {quantity:,} shares")
                logger.info(f"      • Current Price: ${paper_price:.2f}")
                logger.info(f"      • Market Value: ${paper_value:,.2f}")
                logger.info(f"      • Unrealized P&L: ${paper_pnl:+,.2f}")
                
                # Get IG Markets current price
                try:
                    if hasattr(service, 'enhanced_price_source') and service.enhanced_price_source:
                        ig_price = service.enhanced_price_source.get_current_price(symbol)
                        
                        if ig_price is not None:
                            ig_value = quantity * ig_price
                            price_diff = ig_price - paper_price
                            value_diff = ig_value - paper_value
                            price_diff_pct = (price_diff / paper_price * 100) if paper_price > 0 else 0
                            
                            logger.info(f"   📊 IG Markets Data:")
                            logger.info(f"      • Current Price: ${ig_price:.2f}")
                            logger.info(f"      • Market Value: ${ig_value:,.2f}")
                            
                            logger.info(f"   🔍 Comparison:")
                            logger.info(f"      • Price Difference: ${price_diff:+.2f} ({price_diff_pct:+.2f}%)")
                            logger.info(f"      • Value Difference: ${value_diff:+,.2f}")
                            
                            # Check for significant discrepancies
                            if abs(price_diff_pct) > 1.0:  # More than 1% difference
                                logger.warning(f"   ⚠️ SIGNIFICANT PRICE DISCREPANCY DETECTED!")
                                total_discrepancies += 1
                            else:
                                logger.info(f"   ✅ Price data looks consistent")
                        else:
                            logger.warning(f"   ❌ Could not get IG Markets price for {symbol}")
                    else:
                        logger.warning(f"   ❌ IG Markets integration not available")
                        
                except Exception as e:
                    logger.error(f"   ❌ Error validating {symbol}: {e}")
            
            # Summary
            logger.info(f"\n📋 VALIDATION SUMMARY")
            logger.info(f"   • Total Positions Checked: {len(positions)}")
            logger.info(f"   • Significant Discrepancies: {total_discrepancies}")
            
            if total_discrepancies == 0:
                logger.info("   ✅ All positions look consistent with IG Markets data")
            else:
                logger.warning(f"   ⚠️ {total_discrepancies} positions have significant discrepancies")
        
        else:
            logger.info("📊 No active positions to validate")
        
        # Check IG Markets health
        logger.info(f"\n🔍 IG MARKETS INTEGRATION HEALTH")
        logger.info(f"   • IG Markets Enabled: {service.ig_markets_enabled}")
        
        if service.ig_markets_enabled and hasattr(service, 'enhanced_price_source'):
            try:
                health = service.enhanced_price_source.is_ig_markets_healthy()
                logger.info(f"   • IG Markets Health: {'✅ Healthy' if health else '❌ Unhealthy'}")
                
                # Test data for major banks
                test_symbols = ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX']
                logger.info(f"   • Testing major bank symbols:")
                
                for symbol in test_symbols:
                    try:
                        price = service.enhanced_price_source.get_current_price(symbol)
                        if price:
                            logger.info(f"      • {symbol}: ${price:.2f} ✅")
                        else:
                            logger.warning(f"      • {symbol}: No data ❌")
                    except Exception as e:
                        logger.error(f"      • {symbol}: Error - {e}")
            except Exception as e:
                logger.error(f"   ❌ IG Markets health check failed: {e}")
        
        # Recent trading activity
        logger.info(f"\n📈 RECENT TRADING ACTIVITY")
        try:
            recent_trades = service.get_recent_trades(limit=5)
            if recent_trades:
                logger.info(f"   • Last {len(recent_trades)} trades:")
                for trade in recent_trades:
                    action = trade.get('action', 'Unknown')
                    symbol = trade.get('symbol', 'Unknown')
                    quantity = trade.get('quantity', 0)
                    price = trade.get('price', 0)
                    timestamp = trade.get('timestamp', 'Unknown')
                    logger.info(f"      • {timestamp}: {action} {quantity} {symbol} @ ${price:.2f}")
            else:
                logger.info("   • No recent trades found")
        except Exception as e:
            logger.warning(f"   ⚠️ Could not retrieve recent trades: {e}")
        
    except ImportError as e:
        logger.error(f"❌ Failed to import paper trading service: {e}")
        logger.info("💡 Make sure you're running this from the correct directory")
        return False
    except Exception as e:
        logger.error(f"❌ Validation error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    logger.info("\n" + "=" * 60)
    logger.info("🎯 VALIDATION COMPLETE")
    logger.info("=" * 60)
    return True

def check_database_consistency():
    """Check paper trading database for any obvious inconsistencies"""
    logger.info("\n🗄️ DATABASE CONSISTENCY CHECK")
    logger.info("-" * 40)
    
    try:
        # Add paper trading app to path
        paper_trading_path = os.path.join(os.path.dirname(__file__), 'paper-trading-app')
        sys.path.append(paper_trading_path)
        
        from database.models import get_session, create_database
        from sqlalchemy import text
        
        # Connect to paper trading database
        paper_db_path = os.path.join(paper_trading_path, "paper_trading.db")
        engine = create_database(f"sqlite:///{paper_db_path}")
        session = get_session(engine)
        
        # Check for basic data integrity
        logger.info("📊 Database Statistics:")
        
        # Count records
        result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result.fetchall()]
        logger.info(f"   • Tables: {', '.join(tables)}")
        
        for table in tables:
            try:
                result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.fetchone()[0]
                logger.info(f"   • {table}: {count} records")
            except Exception as e:
                logger.warning(f"   • {table}: Error counting - {e}")
        
        # Check for recent activity
        try:
            result = session.execute(text("""
                SELECT COUNT(*) FROM trades 
                WHERE timestamp > datetime('now', '-24 hours')
            """))
            recent_trades = result.fetchone()[0]
            logger.info(f"   • Recent trades (24h): {recent_trades}")
        except Exception as e:
            logger.warning(f"   • Could not check recent trades: {e}")
        
        # Check for negative balances or impossible values
        try:
            result = session.execute(text("""
                SELECT cash_balance, portfolio_value 
                FROM accounts 
                ORDER BY id DESC LIMIT 1
            """))
            account_data = result.fetchone()
            if account_data:
                cash, portfolio = account_data
                logger.info(f"   • Current cash balance: ${cash:,.2f}")
                logger.info(f"   • Portfolio value: ${portfolio:,.2f}")
                
                if cash < 0:
                    logger.warning(f"   ⚠️ Negative cash balance detected!")
                if portfolio < 0:
                    logger.warning(f"   ⚠️ Negative portfolio value detected!")
            else:
                logger.warning("   ⚠️ No account data found")
        except Exception as e:
            logger.warning(f"   • Could not check account balances: {e}")
        
        session.close()
        
    except Exception as e:
        logger.error(f"❌ Database check failed: {e}")

def main():
    """Main validation function"""
    print("🔍 Paper Trading Data Validation Tool")
    print("=" * 50)
    
    # Run validation
    success = validate_paper_trading_vs_ig_markets()
    
    # Check database consistency
    check_database_consistency()
    
    if success:
        print("\n✅ Validation completed successfully!")
        print("💡 Check the logs above for any discrepancies or issues")
    else:
        print("\n❌ Validation encountered errors")
        print("💡 Check the error messages above for details")

if __name__ == "__main__":
    main()
