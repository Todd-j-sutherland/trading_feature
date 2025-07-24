#!/usr/bin/env python3
"""
Alpaca Configuration Setup for ML Trading System

Sets up Alpaca paper trading integration for continuous ML-based trading.
"""

import os
import logging
from pathlib import Path
import json
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_alpaca_credentials():
    """
    Setup Alpaca credentials for paper trading integration.
    """
    print("🏢 Setting up Alpaca Paper Trading Integration")
    print("=" * 50)
    
    # Check if alpaca-trade-api is installed
    try:
        import alpaca_trade_api as tradeapi
        print("✅ Alpaca Trade API is installed")
    except ImportError:
        print("❌ Alpaca Trade API not installed")
        print("📦 Installing alpaca-trade-api...")
        import subprocess
        subprocess.check_call(["pip", "install", "alpaca-trade-api"])
        print("✅ Alpaca Trade API installed successfully")
    
    # Alpaca paper trading configuration
    print("\n📋 Alpaca Configuration:")
    print("API Key: PKUSIHMBPR2AK2WXJGQI")
    print("Base URL: https://paper-api.alpaca.markets")
    print("✅ SECRET KEY will be configured automatically")
    
    # Create .env file with Alpaca settings
    env_file = Path(__file__).parent / '.env'
    
    print(f"\n📝 Setting up environment file: {env_file}")
    
    # Read existing .env if it exists
    existing_env = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing_env[key] = value
    
    # Alpaca configuration
    alpaca_config = {
        'ALPACA_API_KEY': 'PKUSIHMBPR2AK2WXJGQI',
        'ALPACA_BASE_URL': 'https://paper-api.alpaca.markets',
        'ALPACA_PAPER_TRADING': 'true'
    }
    
    # Update existing environment
    existing_env.update(alpaca_config)
    
    # Set the secret key automatically
    existing_env['ALPACA_SECRET_KEY'] = 'raahOvnkGHEsPg1QuJAdoBGgW0sUC9pMhOzH2YsI'
    print("✅ Secret key configured automatically")
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write("# Trading Analysis System Environment Configuration\n")
        f.write(f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("# Alpaca Paper Trading Configuration\n")
        for key, value in alpaca_config.items():
            f.write(f"{key}={value}\n")
        f.write(f"ALPACA_SECRET_KEY={existing_env['ALPACA_SECRET_KEY']}\n\n")
        
        # Write other existing environment variables
        f.write("# Other Configuration\n")
        for key, value in existing_env.items():
            if not key.startswith('ALPACA_'):
                f.write(f"{key}={value}\n")
    
    print(f"✅ Environment file updated: {env_file}")
    
    return env_file

def test_alpaca_connection():
    """
    Test the Alpaca connection with the configured credentials.
    """
    print("\n🔌 Testing Alpaca Connection...")
    
    try:
        import alpaca_trade_api as tradeapi
        from dotenv import load_dotenv
        
        # Load environment variables
        load_dotenv()
        
        api_key = os.getenv('ALPACA_API_KEY')
        secret_key = os.getenv('ALPACA_SECRET_KEY')
        base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        
        if not api_key or not secret_key:
            print("❌ Missing Alpaca credentials in environment")
            return False
        
        if secret_key == 'YOUR_SECRET_KEY_HERE':
            print("❌ Please update ALPACA_SECRET_KEY in .env file with your real secret key")
            return False
        
        # Initialize API client
        api = tradeapi.REST(
            key_id=api_key,
            secret_key=secret_key,
            base_url=base_url,
            api_version='v2'
        )
        
        # Test connection
        account = api.get_account()
        
        print("✅ Successfully connected to Alpaca!")
        print(f"📊 Account Details:")
        print(f"   Account ID: {account.id}")
        print(f"   Equity: ${float(account.equity):,.2f}")
        print(f"   Buying Power: ${float(account.buying_power):,.2f}")
        print(f"   Cash: ${float(account.cash):,.2f}")
        print(f"   Day Trade Count: {account.daytrade_count}")
        print(f"   Pattern Day Trader: {account.pattern_day_trader}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Check your credentials and try again")
        return False

def create_continuous_trading_service():
    """
    Create a continuous trading service that runs throughout the day.
    """
    trading_service_path = Path(__file__).parent / 'continuous_alpaca_trader.py'
    
    service_content = '''#!/usr/bin/env python3
"""
Continuous Alpaca Trading Service

Runs ML-based trading throughout the day using Alpaca paper trading.
"""

import os
import sys
import time
import logging
from datetime import datetime, time as dt_time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from app.core.trading.alpaca_simulator import AlpacaTradingSimulator
from app.core.commands.ml_trading import MLTradingCommand
from app.config.settings import Settings

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/continuous_alpaca_trading.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ContinuousAlpacaTrader:
    """
    Continuous trading service using Alpaca and ML signals.
    """
    
    def __init__(self):
        self.settings = Settings()
        self.alpaca_simulator = AlpacaTradingSimulator(paper_trading=True)
        self.ml_command = MLTradingCommand()
        self.trading_active = False
        
        # Trading schedule (market hours)
        self.market_open = dt_time(9, 30)  # 9:30 AM EST
        self.market_close = dt_time(16, 0)  # 4:00 PM EST
        
        # Trading frequency
        self.check_interval = 300  # 5 minutes
        self.last_trade_time = None
        self.min_time_between_trades = 1800  # 30 minutes
    
    def is_market_hours(self) -> bool:
        """Check if current time is within market hours."""
        now = datetime.now().time()
        return self.market_open <= now <= self.market_close
    
    def should_trade(self) -> bool:
        """Check if we should execute trades now."""
        if not self.is_market_hours():
            return False
        
        if self.last_trade_time is None:
            return True
        
        time_since_last_trade = (datetime.now() - self.last_trade_time).total_seconds()
        return time_since_last_trade >= self.min_time_between_trades
    
    def execute_ml_trading_cycle(self):
        """Execute one ML trading cycle."""
        try:
            logger.info("🧠 Starting ML trading cycle...")
            
            # Check Alpaca connection
            if not self.alpaca_simulator.is_connected():
                logger.error("❌ Alpaca not connected - skipping trading cycle")
                return
            
            # Get current ML scores
            logger.info("📊 Getting ML trading scores...")
            results = self.ml_command.run_ml_analysis_before_trade()
            
            if 'error' in results:
                logger.error(f"❌ ML analysis failed: {results['error']}")
                return
            
            ml_scores = results.get('ml_scores', {})
            if not ml_scores:
                logger.warning("⚠️ No ML scores available")
                return
            
            logger.info(f"✅ Got ML scores for {len(ml_scores)} banks")
            
            # Execute trading strategy
            logger.info("💹 Executing trading strategy...")
            trading_results = self.alpaca_simulator.execute_ml_trading_strategy(
                ml_scores=ml_scores,
                max_total_exposure=10000  # $10,000 max exposure
            )
            
            # Log results
            summary = trading_results.get('summary', {})
            logger.info(f"📈 Trading cycle complete:")
            logger.info(f"   Orders submitted: {summary.get('total_orders_submitted', 0)}")
            logger.info(f"   Orders skipped: {summary.get('total_orders_skipped', 0)}")
            logger.info(f"   Errors: {summary.get('total_errors', 0)}")
            logger.info(f"   Total exposure: ${summary.get('total_estimated_exposure', 0):,.2f}")
            
            # Update last trade time
            self.last_trade_time = datetime.now()
            
            # Save trading log
            self.save_trading_log(trading_results)
            
        except Exception as e:
            logger.error(f"❌ Error in trading cycle: {e}")
    
    def save_trading_log(self, trading_results):
        """Save trading results to log file."""
        log_file = Path('data/alpaca_trading_log.json')
        log_file.parent.mkdir(exist_ok=True)
        
        # Load existing log
        trading_log = []
        if log_file.exists():
            try:
                with open(log_file, 'r') as f:
                    trading_log = json.load(f)
            except:
                trading_log = []
        
        # Add new entry
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'results': trading_results
        }
        trading_log.append(log_entry)
        
        # Keep only last 100 entries
        trading_log = trading_log[-100:]
        
        # Save log
        with open(log_file, 'w') as f:
            json.dump(trading_log, f, indent=2)
    
    def run_continuous_trading(self):
        """Run continuous trading service."""
        logger.info("🚀 Starting Continuous Alpaca Trading Service")
        logger.info(f"📅 Market hours: {self.market_open} - {self.market_close}")
        logger.info(f"⏱️ Check interval: {self.check_interval} seconds")
        logger.info(f"⏳ Min time between trades: {self.min_time_between_trades} seconds")
        
        try:
            while True:
                current_time = datetime.now()
                
                if self.should_trade():
                    self.execute_ml_trading_cycle()
                elif not self.is_market_hours():
                    logger.info(f"💤 Outside market hours - sleeping...")
                else:
                    time_until_next_trade = self.min_time_between_trades - (current_time - self.last_trade_time).total_seconds()
                    logger.info(f"⏰ Waiting {time_until_next_trade:.0f} seconds until next trading window")
                
                # Sleep until next check
                logger.info(f"😴 Sleeping for {self.check_interval} seconds...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Continuous trading stopped by user")
        except Exception as e:
            logger.error(f"❌ Fatal error in continuous trading: {e}")

def main():
    """Main entry point."""
    trader = ContinuousAlpacaTrader()
    trader.run_continuous_trading()

if __name__ == '__main__':
    main()
'''
    
    with open(trading_service_path, 'w') as f:
        f.write(service_content)
    
    # Make executable
    os.chmod(trading_service_path, 0o755)
    
    print(f"✅ Continuous trading service created: {trading_service_path}")
    return trading_service_path

def main():
    """Main setup function."""
    print("🏢 Alpaca Paper Trading Setup for ML Trading System")
    print("=" * 60)
    
    # Step 1: Setup credentials
    env_file = setup_alpaca_credentials()
    
    # Step 2: Test connection
    if test_alpaca_connection():
        print("\n🎉 Alpaca setup completed successfully!")
        
        # Step 3: Create continuous trading service
        print("\n🔄 Creating continuous trading service...")
        service_path = create_continuous_trading_service()
        
        print("\n📋 Next Steps:")
        print("1. ✅ Alpaca credentials are configured")
        print("2. ✅ Connection tested successfully")
        print("3. ✅ Continuous trading service created")
        print("\n🚀 To start continuous trading:")
        print(f"   python {service_path}")
        print("\n📊 To run manual ML trading:")
        print("   python app/main.py ml-scores")
        print("   python app/main.py pre-trade --symbol CBA.AX")
        
    else:
        print("\n❌ Setup incomplete - please fix connection issues")
        print("💡 You need to get your SECRET KEY from Alpaca dashboard:")
        print("   1. Login to https://app.alpaca.markets/")
        print("   2. Go to 'API Keys' section")
        print("   3. Find your SECRET KEY")
        print(f"   4. Update it in {env_file}")

if __name__ == '__main__':
    main()
