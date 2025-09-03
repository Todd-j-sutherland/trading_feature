#!/usr/bin/env python3
"""
Comprehensive keyword list for Australian banking news filtering
Enhanced news relevance detection for trading analysis
"""

# Major Australian Banks - Core names and variations
BANK_KEYWORDS_COMPREHENSIVE = {
    'CBA.AX': [
        'Commonwealth Bank', 'CommBank', 'CBA', 'commonwealth bank of australia',
        'comm bank', 'combank', 'commonwealth', 'cba bank', 'commbank app',
        'netbank', 'commbank netbank', 'commonwealth banking'
    ],
    'WBC.AX': [
        'Westpac', 'WBC', 'westpac bank', 'westpac banking', 'westpac group',
        'westpac banking corporation', 'westpac australia', 'st george',
        'st.george', 'bank of melbourne', 'banksa', 'bank sa', 'westpac app'
    ],
    'ANZ.AX': [
        'ANZ', 'ANZ Bank', 'Australia and New Zealand Banking', 'anz banking',
        'anz group', 'anz australia', 'australia new zealand bank', 'anz plus',
        'anz app', 'anz banking group', 'a.n.z', 'a.n.z.'
    ],
    'NAB.AX': [
        'National Australia Bank', 'NAB', 'nab bank', 'national bank',
        'nab business', 'nab connect', 'ubank', 'mlab', 'nab app',
        'nab private', 'jbwere', 'nabtrade', 'nab trade'
    ],
    'MQG.AX': [
        'Macquarie', 'MQG', 'Macquarie Group', 'macquarie bank',
        'macquarie limited', 'macquarie australia', 'macquarie capital',
        'macquarie investment', 'macquarie wealth', 'macquarie app'
    ],
    'SUN.AX': [
        'Suncorp', 'SUN', 'Suncorp Group', 'suncorp bank', 'suncorp banking',
        'suncorp financial', 'suncorp insurance', 'aami', 'gig', 'vero',
        'suncorp metway', 'suncorp app', 'suncorp business'
    ],
    'QBE.AX': [
        'QBE', 'QBE Insurance', 'QBE Group', 'qbe insurance group',
        'qbe international', 'qbe australia', 'qbe pacific', 'qbe americas',
        'qbe re', 'qbe reinsurance', 'qbe app', 'qbe business'
    ]
}

# Central Bank and Regulators
REGULATORY_KEYWORDS = [
    # RBA
    'RBA', 'Reserve Bank', 'Reserve Bank of Australia', 'reserve bank board',
    'RBA minutes', 'RBA decision', 'monetary policy', 'philip lowe', 'michele bullock',
    'RBA governor', 'cash rate', 'official cash rate', 'interest rate decision',
    'RBA statement', 'monetary policy statement', 'RBA meeting',
    
    # Regulators
    'APRA', 'prudential regulation', 'australian prudential', 'prudential regulator',
    'ASIC', 'securities commission', 'securities and investments', 'corporate regulator',
    'AUSTRAC', 'anti-money laundering', 'AML', 'financial intelligence',
    'ACCC', 'competition commission', 'consumer commission',
    
    # Government/Treasury
    'treasury', 'australian treasury', 'treasurer', 'jim chalmers',
    'financial services minister', 'banking royal commission', 'hayne royal commission'
]

# General Banking & Finance Terms
BANKING_TERMS = [
    # Products & Services
    'mortgage', 'home loan', 'housing loan', 'variable rate', 'fixed rate',
    'personal loan', 'business loan', 'commercial loan', 'credit card',
    'debit card', 'savings account', 'term deposit', 'transaction account',
    'offset account', 'overdraft', 'line of credit', 'refinance', 'refinancing',
    
    # Banking Operations
    'banking', 'retail banking', 'business banking', 'corporate banking',
    'investment banking', 'private banking', 'wealth management', 'funds management',
    'digital banking', 'online banking', 'mobile banking', 'branch', 'ATM',
    
    # Financial Terms
    'interest rate', 'lending rate', 'deposit rate', 'margin', 'spread',
    'net interest margin', 'NIM', 'return on equity', 'ROE', 'tier 1 capital',
    'capital ratio', 'basel iii', 'liquidity', 'provisioning', 'bad debt',
    'impairment', 'write-off', 'dividend', 'franking', 'share buyback'
]

# Specific Event/Topic Keywords
EVENT_KEYWORDS = {
    'financial_results': [
        'profit', 'loss', 'earnings', 'results', 'revenue', 'income',
        'quarterly results', 'half year results', 'full year results',
        'financial results', 'trading update', 'guidance', 'outlook',
        'beats expectations', 'misses expectations', 'profit warning',
        'record profit', 'profit drop', 'profit surge'
    ],
    
    'market_activity': [
        'share price', 'stock price', 'shares', 'ASX', 'trading halt',
        'market update', 'trading update', 'acquisition', 'merger',
        'takeover', 'divestment', 'joint venture', 'partnership',
        'capital raising', 'share issue', 'rights issue', 'placement'
    ],
    
    'technology': [
        'digital transformation', 'fintech', 'blockchain', 'crypto',
        'cryptocurrency', 'digital wallet', 'open banking', 'API',
        'cyber security', 'data breach', 'hack', 'outage', 'system failure',
        'app update', 'new app', 'technology investment', 'AI', 'artificial intelligence'
    ],
    
    'customer_related': [
        'customer', 'complaint', 'satisfaction', 'service', 'fees',
        'charges', 'account fee', 'transaction fee', 'penalty', 'refund',
        'compensation', 'remediation', 'class action', 'ombudsman', 'AFCA'
    ],
    
    'scams_fraud': [
        'scam', 'fraud', 'phishing', 'identity theft', 'money laundering',
        'financial crime', 'suspicious transaction', 'security breach',
        'unauthorised transaction', 'card fraud', 'investment scam',
        'romance scam', 'fake', 'fraudulent', 'scammer'
    ],
    
    'regulatory_compliance': [
        'investigation', 'probe', 'inquiry', 'audit', 'compliance',
        'breach', 'violation', 'penalty', 'fine', 'sanction', 'enforcement',
        'regulatory action', 'court case', 'lawsuit', 'legal action',
        'settlement', 'guilty', 'misconduct', 'wrongdoing'
    ],
    
    'economic_indicators': [
        'inflation', 'CPI', 'unemployment', 'GDP', 'economic growth',
        'recession', 'housing market', 'property market', 'auction',
        'clearance rate', 'housing prices', 'credit growth', 'household debt',
        'business confidence', 'consumer confidence', 'retail sales'
    ],
    
    'leadership_governance': [
        'CEO', 'chief executive', 'chairman', 'director', 'board',
        'appointment', 'resignation', 'retire', 'departure', 'succession',
        'leadership change', 'management change', 'restructure', 'reorganisation',
        'executive pay', 'remuneration', 'bonus', 'shareholders', 'AGM'
    ]
}

# Action/Impact Verbs
ACTION_VERBS = [
    # Positive actions
    'announces', 'launches', 'introduces', 'expands', 'grows', 'increases',
    'improves', 'strengthens', 'boosts', 'gains', 'rises', 'surges',
    'outperforms', 'exceeds', 'achieves', 'delivers', 'reports', 'posts',
    
    # Negative actions
    'cuts', 'reduces', 'slashes', 'drops', 'falls', 'declines', 'plunges',
    'warns', 'faces', 'struggles', 'admits', 'reveals', 'exposes',
    'investigates', 'probes', 'charges', 'fines', 'suspends', 'closes',
    
    # Neutral actions
    'considers', 'reviews', 'plans', 'expects', 'forecasts', 'predicts',
    'targets', 'aims', 'seeks', 'explores', 'evaluates', 'monitors'
]

# Negative/Risk Keywords
RISK_KEYWORDS = [
    # Financial risks
    'risk', 'threat', 'concern', 'warning', 'alert', 'crisis', 'trouble',
    'problem', 'issue', 'challenge', 'difficult', 'pressure', 'stress',
    'vulnerable', 'exposure', 'default', 'delinquency', 'arrears',
    
    # Market risks
    'volatility', 'uncertainty', 'downturn', 'correction', 'bear market',
    'sell-off', 'panic', 'contagion', 'bubble', 'crash', 'collapse',
    
    # Operational risks
    'scandal', 'controversy', 'allegation', 'accusation', 'criticism',
    'backlash', 'outcry', 'protest', 'boycott', 'reputation damage',
    'system failure', 'outage', 'disruption', 'error', 'mistake',
    
    # Regulatory risks
    'non-compliance', 'breach', 'violation', 'penalty', 'sanction',
    'suspension', 'ban', 'restriction', 'investigation', 'inquiry',
    'subpoena', 'warrant', 'charge', 'prosecution', 'conviction'
]

# Sentiment Modifiers (to understand context)
SENTIMENT_MODIFIERS = {
    'positive': [
        'strong', 'solid', 'robust', 'healthy', 'positive', 'good',
        'excellent', 'outstanding', 'record', 'best', 'leading', 'top'
    ],
    'negative': [
        'weak', 'poor', 'bad', 'worst', 'concerning', 'worrying',
        'disappointing', 'troubling', 'alarming', 'shocking', 'unprecedented'
    ],
    'intensifiers': [
        'very', 'extremely', 'highly', 'significantly', 'substantially',
        'materially', 'particularly', 'especially', 'notably', 'remarkably'
    ]
}

# Time-sensitive Keywords (for urgency detection)
TIME_KEYWORDS = [
    'today', 'yesterday', 'tomorrow', 'now', 'immediate', 'urgent',
    'breaking', 'just in', 'latest', 'update', 'developing', 'ongoing',
    'this morning', 'this afternoon', 'overnight', 'after hours'
]

class BankNewsFilter:
    """
    Advanced news filtering system for Australian banking news
    """
    
    def __init__(self):
        self.bank_keywords = BANK_KEYWORDS_COMPREHENSIVE
        self.regulatory_keywords = REGULATORY_KEYWORDS
        self.banking_terms = BANKING_TERMS
        self.event_keywords = EVENT_KEYWORDS
        self.action_verbs = ACTION_VERBS
        self.risk_keywords = RISK_KEYWORDS
        self.sentiment_modifiers = SENTIMENT_MODIFIERS
        self.time_keywords = TIME_KEYWORDS
    
    def is_relevant_banking_news(self, title: str, content: str = "", bank_symbol: str = None) -> dict:
        """
        Enhanced check if a news title/content is relevant to Australian banking.
        
        Args:
            title (str): News article title
            content (str): News article content (optional)
            bank_symbol (str, optional): Specific bank symbol to filter for (e.g., 'NAB.AX')
        
        Returns:
            dict: {
                'is_relevant': bool,
                'relevance_score': float,
                'matched_keywords': list,
                'categories': list,
                'urgency_score': float,
                'sentiment_indicators': dict
            }
        """
        text_to_analyze = f"{title} {content}".lower()
        matched_keywords = []
        relevance_score = 0
        categories = []
        urgency_score = 0
        sentiment_indicators = {'positive': [], 'negative': [], 'risk': []}
        
        # Check for specific bank if provided
        if bank_symbol and bank_symbol in self.bank_keywords:
            for keyword in self.bank_keywords[bank_symbol]:
                if keyword.lower() in text_to_analyze:
                    matched_keywords.append(keyword)
                    relevance_score += 3  # High weight for specific bank match
                    categories.append(f'specific_bank_{bank_symbol}')
        else:
            # Check all banks
            for symbol, bank_keywords in self.bank_keywords.items():
                for keyword in bank_keywords:
                    if keyword.lower() in text_to_analyze:
                        matched_keywords.append(keyword)
                        relevance_score += 3
                        categories.append(f'bank_{symbol}')
        
        # Check regulatory keywords
        for keyword in self.regulatory_keywords:
            if keyword.lower() in text_to_analyze:
                matched_keywords.append(keyword)
                relevance_score += 2
                categories.append('regulatory')
        
        # Check banking terms
        for keyword in self.banking_terms:
            if keyword.lower() in text_to_analyze:
                matched_keywords.append(keyword)
                relevance_score += 1
                categories.append('banking_operations')
        
        # Check event keywords
        for event_type, keywords in self.event_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_to_analyze:
                    matched_keywords.append(keyword)
                    relevance_score += 2
                    categories.append(f'event_{event_type}')
        
        # Check action verbs
        for verb in self.action_verbs:
            if verb.lower() in text_to_analyze:
                matched_keywords.append(verb)
                relevance_score += 1
                categories.append('action_verb')
        
        # Check risk keywords (add extra weight for risk-related news)
        for keyword in self.risk_keywords:
            if keyword.lower() in text_to_analyze:
                matched_keywords.append(keyword)
                relevance_score += 2
                categories.append('risk')
                sentiment_indicators['risk'].append(keyword)
        
        # Check time-sensitive keywords (add urgency score)
        for keyword in self.time_keywords:
            if keyword.lower() in text_to_analyze:
                urgency_score += 1
                categories.append('time_sensitive')
        
        # Check sentiment modifiers
        for sentiment_type, modifiers in self.sentiment_modifiers.items():
            for modifier in modifiers:
                if modifier.lower() in text_to_analyze:
                    if sentiment_type in ['positive', 'negative']:
                        sentiment_indicators[sentiment_type].append(modifier)
                    elif sentiment_type == 'intensifiers':
                        urgency_score += 0.5
        
        # Determine overall relevance
        is_relevant = relevance_score >= 3  # Threshold for relevance
        
        # Normalize scores
        relevance_score = min(relevance_score / 10.0, 1.0)  # Normalize to 0-1
        urgency_score = min(urgency_score / 5.0, 1.0)  # Normalize to 0-1
        
        return {
            'is_relevant': is_relevant,
            'relevance_score': relevance_score,
            'matched_keywords': list(set(matched_keywords)),
            'categories': list(set(categories)),
            'urgency_score': urgency_score,
            'sentiment_indicators': sentiment_indicators
        }
    
    def get_bank_specific_keywords(self, bank_symbol: str) -> list:
        """Get keywords specific to a bank symbol"""
        return self.bank_keywords.get(bank_symbol, [])
    
    def get_all_banking_keywords(self) -> list:
        """Get all banking-related keywords for general filtering"""
        all_keywords = []
        for keywords in self.bank_keywords.values():
            all_keywords.extend(keywords)
        all_keywords.extend(self.regulatory_keywords)
        all_keywords.extend(self.banking_terms)
        return list(set(all_keywords))

# Combined keyword function for easy filtering (backwards compatibility)
def is_relevant_banking_news(title, bank_symbol=None):
    """
    Legacy function for backwards compatibility
    """
    filter_system = BankNewsFilter()
    result = filter_system.is_relevant_banking_news(title, bank_symbol=bank_symbol)
    return result['is_relevant'], result['relevance_score'], result['matched_keywords']

# Example usage and testing
if __name__ == "__main__":
    filter_system = BankNewsFilter()
    
    test_titles = [
        "NAB announces record profit amid rising interest rates",
        "RBA holds cash rate steady at 4.35%",
        "Commonwealth Bank faces ASIC investigation over fees",
        "Westpac launches new digital banking platform",
        "Major scam warning for ANZ customers",
        "Macquarie Group CEO to retire next year",
        "Australian housing market shows signs of cooling",
        "Tech stocks surge on Wall Street overnight"  # Should not match
    ]
    
    print("Testing Enhanced Bank News Filter")
    print("=" * 50)
    
    for title in test_titles:
        result = filter_system.is_relevant_banking_news(title)
        print(f"\nTitle: {title}")
        print(f"Relevant: {result['is_relevant']} (Score: {result['relevance_score']:.2f})")
        print(f"Categories: {', '.join(result['categories'])}")
        print(f"Matched keywords: {', '.join(result['matched_keywords'][:5])}")  # Show first 5
        if result['urgency_score'] > 0:
            print(f"Urgency: {result['urgency_score']:.2f}")
