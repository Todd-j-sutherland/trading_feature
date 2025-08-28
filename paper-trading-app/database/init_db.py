#!/usr/bin/env python3
"""
Database initialization script for Paper Trading App
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import create_database, get_session, init_default_account
from config import DEFAULT_INITIAL_BALANCE

def main():
    """Initialize the paper trading database"""
    print("Initializing Paper Trading Database...")
    
    # Create database and tables
    database_path = "paper_trading.db"
    database_url = f"sqlite:///{database_path}"
    
    try:
        engine = create_database(database_url)
        print(f"✅ Database created: {database_path}")
        
        # Create session and initialize default account
        session = get_session(engine)
        account = init_default_account(session, DEFAULT_INITIAL_BALANCE)
        
        print(f"✅ Default account created with ${DEFAULT_INITIAL_BALANCE:,.2f}")
        print(f"✅ Account ID: {account.id}")
        
        session.close()
        print("✅ Database initialization complete!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
