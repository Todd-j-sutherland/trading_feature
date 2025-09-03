"""
Manages keywords for filtering and identifying relevant news articles.
"""
import logging

logger = logging.getLogger(__name__)

class KeywordManager:
    """
    Manages and provides keywords for news filtering and analysis.
    """
    def __init__(self):
        self.bank_keywords = {
            'CBA.AX': ['cba', 'commonwealth bank'],
            'WBC.AX': ['wbc', 'westpac'],
            'ANZ.AX': ['anz', 'australia and new zealand bank'],
            'NAB.AX': ['nab', 'national australia bank'],
            'MQG.AX': ['mqg', 'macquarie'],
        }
        self.event_keywords = {
            'dividend': ['dividend', 'payout', 'distribution'],
            'earnings': ['earnings', 'profit', 'revenue', 'results'],
            'scandal': ['scandal', 'misconduct', 'investigation', 'fine'],
        }
        self.risk_keywords = ['risk', 'warning', 'downgrade', 'concern']
        self.sentiment_modifiers = {
            'positive': ['upgrade', 'strong', 'beat', 'outperform'],
            'negative': ['downgrade', 'weak', 'miss', 'underperform'],
        }

    def get_keywords_for_bank(self, symbol: str) -> list:
        """Returns all relevant keywords for a given bank symbol."""
        if symbol not in self.bank_keywords:
            return []
        
        keywords = self.bank_keywords[symbol]
        keywords.extend([kw for sublist in self.event_keywords.values() for kw in sublist])
        keywords.extend(self.risk_keywords)
        keywords.extend([kw for sublist in self.sentiment_modifiers.values() for kw in sublist])
        return list(set(keywords))

    def get_all_keywords(self) -> list:
        """Returns a list of all keywords across all categories."""
        all_kws = []
        for kws in self.bank_keywords.values():
            all_kws.extend(kws)
        for kws in self.event_keywords.values():
            all_kws.extend(kws)
        all_kws.extend(self.risk_keywords)
        for kws in self.sentiment_modifiers.values():
            all_kws.extend(kws)
        return list(set(all_kws))

if __name__ == '__main__':
    manager = KeywordManager()
    print("Keywords for CBA.AX:", manager.get_keywords_for_bank('CBA.AX'))
    print("\nAll keywords:", manager.get_all_keywords())
