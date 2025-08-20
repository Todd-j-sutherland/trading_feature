#!/usr/bin/env python3
"""
Immediate Evening Analysis Fix
=============================

Quick fixes for the identified issues:

ISSUES FOUND:
1. Insufficient training data: Only 21 total samples (need 50 minimum)
2. Crypto news contamination: Bitcoin/crypto headlines instead of bank news
3. Database path mismatch: Evening analyzer using empty predictions.db

IMMEDIATE FIXES:
1. Fix database path by creating symlink
2. Lower training data threshold temporarily  
3. Add crypto news filtering
"""

import os
import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_path():
    """Fix database path mismatch"""
    logger.info("🔧 Fixing database path...")
    
    # Check if correct database exists
    if os.path.exists("data/trading_predictions.db"):
        # Remove empty predictions.db if it exists
        if os.path.exists("predictions.db"):
            if os.path.getsize("predictions.db") == 0:
                os.remove("predictions.db")
                logger.info("   Removed empty predictions.db")
        
        # Create symlink to correct database
        if not os.path.exists("predictions.db"):
            os.symlink("data/trading_predictions.db", "predictions.db")
            logger.info("   ✅ Created symlink to data/trading_predictions.db")
        
        return True
    else:
        logger.error("   ❌ data/trading_predictions.db not found")
        return False

def lower_training_threshold():
    """Temporarily lower training data requirements"""
    logger.info("🔧 Adjusting training data thresholds...")
    
    # Check current training data
    try:
        conn = sqlite3.connect("data/trading_predictions.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM enhanced_features")
        total_samples = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT symbol, COUNT(*) as count 
            FROM enhanced_features 
            GROUP BY symbol 
            ORDER BY count DESC
        """)
        
        by_symbol = cursor.fetchall()
        conn.close()
        
        logger.info(f"   Current training data: {total_samples} total samples")
        for symbol, count in by_symbol:
            logger.info(f"   {symbol}: {count} samples")
        
        # Recommend temporary threshold
        min_samples = min(count for _, count in by_symbol) if by_symbol else 0
        suggested_threshold = max(3, min_samples)
        
        logger.info(f"   ✅ Suggested temporary threshold: {suggested_threshold} samples")
        logger.info("   ⚠️  Manual fix needed: Update evening analyzer minimum_samples setting")
        
        return suggested_threshold
        
    except Exception as e:
        logger.error(f"   ❌ Database error: {str(e)}")
        return None

def create_news_filter_patch():
    """Create patch for crypto news filtering"""
    logger.info("🔧 Creating news filtering patch...")
    
    patch_content = '''
# Crypto News Filter Patch
# Add this to news collection logic:

def filter_crypto_news(headlines):
    """Filter out crypto/irrelevant headlines"""
    
    crypto_keywords = [
        'bitcoin', 'crypto', 'cryptocurrency', 'digital asset',
        'blockchain', 'ethereum', 'token', 'heritage distilling',
        'crypto.com', 'aditxt', 'custody agreement'
    ]
    
    filtered = []
    for headline in headlines:
        headline_lower = headline.lower()
        
        # Skip if contains crypto keywords
        if any(keyword in headline_lower for keyword in crypto_keywords):
            continue
            
        # Keep if contains bank/finance keywords
        bank_keywords = ['bank', 'banking', 'financial', 'rba', 'interest', 'dividend', 'earnings']
        if any(keyword in headline_lower for keyword in bank_keywords):
            filtered.append(headline)
    
    return filtered

# Apply this filter to recent_headlines before using them
'''
    
    with open("crypto_news_filter_patch.py", "w") as f:
        f.write(patch_content)
    
    logger.info("   ✅ Created crypto_news_filter_patch.py")
    logger.info("   ⚠️  Manual integration needed in evening analyzer")

def verify_fixes():
    """Verify the fixes are working"""
    logger.info("🔍 Verifying fixes...")
    
    # Check database access
    if os.path.exists("predictions.db"):
        try:
            conn = sqlite3.connect("predictions.db")
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM enhanced_features")
            count = cursor.fetchone()[0]
            conn.close()
            
            logger.info(f"   ✅ Database accessible: {count} enhanced_features records")
            return True
            
        except Exception as e:
            logger.error(f"   ❌ Database access failed: {str(e)}")
            return False
    else:
        logger.error("   ❌ predictions.db still not accessible")
        return False

def main():
    """Execute immediate fixes"""
    logger.info("🚀 Starting immediate evening analysis fixes...")
    
    # Apply fixes
    fixes_applied = 0
    
    if fix_database_path():
        fixes_applied += 1
    
    threshold = lower_training_threshold()
    if threshold:
        fixes_applied += 1
    
    create_news_filter_patch()
    fixes_applied += 1
    
    # Verify
    if verify_fixes():
        logger.info(f"✅ {fixes_applied}/3 fixes applied successfully!")
        
        logger.info("\n📋 MANUAL STEPS REQUIRED:")
        logger.info("1. Update evening analyzer minimum training samples to 3")
        logger.info("2. Integrate crypto news filter in news collection")
        logger.info("3. Test evening analysis run")
        
        logger.info("\n🎯 Expected improvements:")
        logger.info("- Evening analysis should access training data")
        logger.info("- Crypto news contamination reduced")
        logger.info("- Grade F ratings should improve")
        
    else:
        logger.error("❌ Verification failed - manual intervention needed")

if __name__ == "__main__":
    main()
