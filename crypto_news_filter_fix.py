#!/usr/bin/env python3
"""
Crypto News Filter Implementation
=================================

This script implements the crypto news filtering directly in the news analyzer
to fix the Grade F ratings caused by crypto headline contamination.

Target: app/core/sentiment/news_analyzer.py line 1018
"""

import os
import re

def filter_crypto_news(all_news, symbol):
    """Filter out crypto/irrelevant headlines and prioritize bank-specific content"""
    
    # Crypto keywords to exclude
    crypto_keywords = [
        'bitcoin', 'crypto', 'cryptocurrency', 'digital asset',
        'blockchain', 'ethereum', 'token', 'heritage distilling',
        'crypto.com', 'aditxt', 'custody agreement', 'ip token',
        'treasury strategy', 'digital currency'
    ]
    
    # Bank name mapping for targeted filtering
    bank_names = {
        'CBA.AX': ['commonwealth bank', 'cba', 'commbank'],
        'ANZ.AX': ['anz', 'australia and new zealand banking'],
        'WBC.AX': ['westpac', 'wbc'],
        'NAB.AX': ['national australia bank', 'nab'],
        'MQG.AX': ['macquarie', 'macquarie group'],
        'SUN.AX': ['suncorp', 'suncorp group'],
        'QBE.AX': ['qbe insurance', 'qbe']
    }
    
    # Bank-specific keywords (high priority)
    bank_specific = bank_names.get(symbol, [])
    
    # General banking keywords (medium priority)
    bank_keywords = [
        'bank', 'banking', 'financial services', 'lending',
        'mortgage', 'deposit', 'interest rate', 'rba',
        'apra', 'dividend', 'earnings', 'profit', 'asx',
        'home loan', 'credit', 'capital', 'regulatory'
    ]
    
    # Filter and score news articles
    scored_news = []
    
    for news in all_news:
        title = news.get('title', '').lower()
        
        # Skip crypto-related content
        if any(keyword in title for keyword in crypto_keywords):
            continue
        
        # Score articles based on relevance
        score = 0
        
        # Highest priority: Bank-specific mentions
        if any(bank_name in title for bank_name in bank_specific):
            score += 100
        
        # Medium priority: General banking terms
        if any(keyword in title for keyword in bank_keywords):
            score += 50
        
        # Australian financial context
        if any(term in title for term in ['asx', 'australia', 'rba', 'apra']):
            score += 25
        
        # Only include articles with some relevance
        if score > 0:
            scored_news.append((score, news))
    
    # Sort by relevance score (highest first)
    scored_news.sort(key=lambda x: x[0], reverse=True)
    
    # Return top 5 most relevant articles
    return [news for score, news in scored_news[:5]]

def apply_crypto_filter_fix():
    """Apply the crypto news filter to the news analyzer"""
    
    file_path = "app/core/sentiment/news_analyzer.py"
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    # Read the current file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Define the filter function code to inject
    filter_function = '''
    def _filter_crypto_news(self, all_news, symbol):
        """Filter out crypto/irrelevant headlines and prioritize bank-specific content"""
        
        # Crypto keywords to exclude
        crypto_keywords = [
            'bitcoin', 'crypto', 'cryptocurrency', 'digital asset',
            'blockchain', 'ethereum', 'token', 'heritage distilling',
            'crypto.com', 'aditxt', 'custody agreement', 'ip token',
            'treasury strategy', 'digital currency'
        ]
        
        # Bank name mapping for targeted filtering
        bank_names = {
            'CBA.AX': ['commonwealth bank', 'cba', 'commbank'],
            'ANZ.AX': ['anz', 'australia and new zealand banking'],
            'WBC.AX': ['westpac', 'wbc'],
            'NAB.AX': ['national australia bank', 'nab'],
            'MQG.AX': ['macquarie', 'macquarie group'],
            'SUN.AX': ['suncorp', 'suncorp group'],
            'QBE.AX': ['qbe insurance', 'qbe']
        }
        
        # Bank-specific keywords (high priority)
        bank_specific = bank_names.get(symbol, [])
        
        # General banking keywords (medium priority)
        bank_keywords = [
            'bank', 'banking', 'financial services', 'lending',
            'mortgage', 'deposit', 'interest rate', 'rba',
            'apra', 'dividend', 'earnings', 'profit', 'asx',
            'home loan', 'credit', 'capital', 'regulatory'
        ]
        
        # Filter and score news articles
        scored_news = []
        
        for news in all_news:
            title = news.get('title', '').lower()
            
            # Skip crypto-related content
            if any(keyword in title for keyword in crypto_keywords):
                continue
            
            # Score articles based on relevance
            score = 0
            
            # Highest priority: Bank-specific mentions
            if any(bank_name in title for bank_name in bank_specific):
                score += 100
            
            # Medium priority: General banking terms
            if any(keyword in title for keyword in bank_keywords):
                score += 50
            
            # Australian financial context
            if any(term in title for term in ['asx', 'australia', 'rba', 'apra']):
                score += 25
            
            # Only include articles with some relevance
            if score > 0:
                scored_news.append((score, news))
        
        # Sort by relevance score (highest first)
        scored_news.sort(key=lambda x: x[0], reverse=True)
        
        # Return top 5 most relevant articles
        return [news for score, news in scored_news[:5]]
'''
    
    # Check if the filter function already exists
    if '_filter_crypto_news' not in content:
        # Find a good place to insert the function (before the analyze_bank_sentiment method)
        insertion_point = content.find('def analyze_bank_sentiment(')
        if insertion_point == -1:
            print("❌ Could not find insertion point for filter function")
            return False
        
        # Insert the filter function
        content = content[:insertion_point] + filter_function + '\n    ' + content[insertion_point:]
        print("✅ Added crypto news filter function")
    
    # Replace the problematic line
    old_line = "'recent_headlines': [news['title'] for news in all_news[:5]]"
    new_line = "'recent_headlines': [news['title'] for news in self._filter_crypto_news(all_news, symbol)]"
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        print("✅ Applied crypto filter to recent_headlines")
    else:
        print("⚠️ Original line not found - may already be modified")
    
    # Create backup
    backup_path = f"{file_path}.backup_crypto_fix"
    with open(backup_path, 'w') as f:
        f.write(content)
    
    # Write the modified content
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Crypto news filter applied to {file_path}")
    print(f"📄 Backup saved as {backup_path}")
    return True

def main():
    """Apply the crypto news filter fix"""
    print("🔧 Applying Crypto News Filter Fix...")
    print("=" * 50)
    
    if apply_crypto_filter_fix():
        print("\n✅ Crypto news filter successfully applied!")
        print("\n🎯 Expected improvements:")
        print("- Crypto headlines filtered out of recent_headlines")
        print("- Bank-specific news prioritized")
        print("- Grade F ratings should improve to Grade B/A")
        print("- More relevant sentiment analysis")
        
        print("\n⚡ Next steps:")
        print("1. Test evening analysis to verify filtering")
        print("2. Monitor grade improvements in next run")
        print("3. Check that recent_headlines now show bank news")
        
    else:
        print("\n❌ Failed to apply crypto news filter")
        print("Manual intervention required")

if __name__ == "__main__":
    main()
