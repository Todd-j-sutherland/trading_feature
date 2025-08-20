
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
