#!/usr/bin/env python3
"""
IG Markets Epic Discovery Tool

Finds the correct EPIC codes for ASX bank stocks in IG Markets demo account.
"""

import os
import sys
import requests
import json
import logging
from typing import Dict, List, Optional

# Import our IG client
sys.path.append('/root/test')
from ig_markets_trading_api import IGMarketsAPIClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def search_ig_markets_symbols():
    """Search for ASX bank symbols in IG Markets"""
    
    # Set environment variables
    os.environ['IG_API_KEY'] = 'ac68e6f053799a4a36c75936c088fc4d6cfcfa6e'
    os.environ['IG_USERNAME'] = 'sutho100'
    os.environ['IG_PASSWORD'] = 'Helloworld987543$'
    os.environ['IG_DEMO_MODE'] = 'true'
    
    client = IGMarketsAPIClient()
    
    # Authenticate
    if not client.authenticate():
        logger.error("Authentication failed")
        return
    
    # Search terms for our target stocks
    search_terms = [
        'Commonwealth Bank', 'CBA', 
        'Westpac', 'WBC',
        'ANZ', 'Australia New Zealand Banking',
        'National Australia Bank', 'NAB',
        'Macquarie', 'MQG',
        'Suncorp', 'SUN',
        'QBE'
    ]
    
    logger.info("🔍 Searching IG Markets for ASX bank stocks...")
    
    for term in search_terms:
        try:
            # Use IG Markets search API
            search_url = f"{client.base_url}/markets"
            params = {
                'searchTerm': term,
                'type': 'SHARES'
            }
            
            response = client.session.get(search_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                markets = data.get('markets', [])
                
                logger.info(f"📊 Search results for '{term}': {len(markets)} found")
                
                for market in markets[:5]:  # Show first 5 results
                    epic = market.get('epic')
                    name = market.get('instrumentName')
                    type_info = market.get('instrumentType')
                    
                    if 'AUS' in epic or 'AU.' in epic or '.AX' in name:
                        logger.info(f"  ✅ {epic} - {name} ({type_info})")
                
            else:
                logger.error(f"Search failed for '{term}': {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error searching for '{term}': {e}")
    
    # Try some common EPIC patterns for ASX
    logger.info("\n🔍 Testing common ASX EPIC patterns...")
    
    test_epics = [
        # Different possible formats
        'CBA', 'WBC', 'ANZ', 'NAB', 'MQG', 'SUN', 'QBE',
        'AU.CBA', 'AU.WBC', 'AU.ANZ', 'AU.NAB', 'AU.MQG', 'AU.SUN', 'AU.QBE',
        'CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX',
        'AU.CBA.CASH.IP', 'AU.WBC.CASH.IP', 'AU.ANZ.CASH.IP', 'AU.NAB.CASH.IP',
        'AU.CBA.CHESS.D', 'AU.WBC.CHESS.D', 'AU.ANZ.CHESS.D', 'AU.NAB.CHESS.D'
    ]
    
    for epic in test_epics:
        try:
            market_info = client.get_market_info(epic)
            if market_info:
                instrument = market_info.get('instrument', {})
                snapshot = market_info.get('snapshot', {})
                name = instrument.get('name', 'Unknown')
                bid = snapshot.get('bid')
                ask = snapshot.get('offer')
                status = snapshot.get('marketStatus')
                
                logger.info(f"✅ FOUND: {epic} - {name}")
                logger.info(f"   Price: Bid ${bid}, Ask ${ask}, Status: {status}")
            
        except Exception as e:
            # Silently skip failed EPICs
            pass

if __name__ == "__main__":
    search_ig_markets_symbols()
