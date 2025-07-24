#!/usr/bin/env python3
"""
Centralized Bank Symbol Management
Provides consistent symbol lists across the entire trading system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.config.settings import Settings

class BankSymbols:
    """
    Centralized management of bank symbols to ensure consistency
    across all modules in the trading system
    """
    
    # Primary ASX Bank Symbols (Major 4 + Financial Services)
    MAJOR_BANKS = [
        'CBA.AX',  # Commonwealth Bank of Australia
        'WBC.AX',  # Westpac Banking Corporation  
        'ANZ.AX',  # Australia and New Zealand Banking Group
        'NAB.AX',  # National Australia Bank
    ]
    
    # Additional Financial Services
    ADDITIONAL_FINANCIALS = [
        'MQG.AX',  # Macquarie Group Limited
        'SUN.AX',  # Suncorp Group Limited  
        'QBE.AX',  # QBE Insurance Group Limited
    ]
    
    # All Primary Trading Symbols
    ALL_SYMBOLS = MAJOR_BANKS + ADDITIONAL_FINANCIALS
    
    # Extended universe (smaller banks and financials)
    EXTENDED_SYMBOLS = [
        'BEN.AX',  # Bendigo and Adelaide Bank
        'BOQ.AX',  # Bank of Queensland
        'IFL.AX',  # IOOF Holdings Limited
        'AMP.AX',  # AMP Limited
        'CWN.AX',  # Crown Resorts (Financial services exposure)
    ]
    
    # Complete universe
    COMPLETE_UNIVERSE = ALL_SYMBOLS + EXTENDED_SYMBOLS
    
    # Bank Names for Display
    BANK_NAMES = {
        'CBA.AX': 'Commonwealth Bank of Australia',
        'WBC.AX': 'Westpac Banking Corporation',
        'ANZ.AX': 'Australia and New Zealand Banking Group',
        'NAB.AX': 'National Australia Bank',
        'MQG.AX': 'Macquarie Group Limited',
        'SUN.AX': 'Suncorp Group Limited',
        'QBE.AX': 'QBE Insurance Group Limited',
        'BEN.AX': 'Bendigo and Adelaide Bank',
        'BOQ.AX': 'Bank of Queensland',
        'IFL.AX': 'IOOF Holdings Limited',
        'AMP.AX': 'AMP Limited',
        'CWN.AX': 'Crown Resorts Limited'
    }
    
    # Bank Categories for Analysis
    CATEGORIES = {
        'big_four': ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX'],
        'investment_banks': ['MQG.AX'],
        'regional_banks': ['BEN.AX', 'BOQ.AX'],
        'insurance': ['QBE.AX', 'SUN.AX'],
        'wealth_management': ['AMP.AX', 'IFL.AX'],
        'diversified_financials': ['MQG.AX', 'SUN.AX']
    }
    
    @classmethod
    def get_symbols_by_category(cls, category: str) -> list:
        """Get symbols by category"""
        return cls.CATEGORIES.get(category, [])
    
    @classmethod
    def get_symbol_name(cls, symbol: str) -> str:
        """Get display name for a symbol"""
        return cls.BANK_NAMES.get(symbol, symbol)
    
    @classmethod
    def is_major_bank(cls, symbol: str) -> bool:
        """Check if symbol is one of the major 4 banks"""
        return symbol in cls.MAJOR_BANKS
    
    @classmethod
    def is_financial_stock(cls, symbol: str) -> bool:
        """Check if symbol is in our financial universe"""
        return symbol in cls.COMPLETE_UNIVERSE
    
    @classmethod
    def get_trading_symbols(cls, include_extended: bool = False) -> list:
        """
        Get list of symbols for trading analysis
        
        Args:
            include_extended: If True, include smaller banks and financials
            
        Returns:
            List of symbol strings
        """
        if include_extended:
            return cls.COMPLETE_UNIVERSE
        else:
            return cls.ALL_SYMBOLS
    
    @classmethod
    def validate_symbol(cls, symbol: str) -> bool:
        """Validate if a symbol is supported"""
        return symbol in cls.COMPLETE_UNIVERSE

# Convenience functions for backwards compatibility
def get_default_symbols():
    """Get the default set of symbols for analysis"""
    return BankSymbols.ALL_SYMBOLS

def get_major_bank_symbols():
    """Get just the major 4 bank symbols"""
    return BankSymbols.MAJOR_BANKS

def get_all_financial_symbols():
    """Get all financial symbols including extended universe"""
    return BankSymbols.COMPLETE_UNIVERSE

# Usage examples and testing
if __name__ == "__main__":
    print("Bank Symbol Management System")
    print("=" * 40)
    
    print(f"\nMajor Banks ({len(BankSymbols.MAJOR_BANKS)}):")
    for symbol in BankSymbols.MAJOR_BANKS:
        print(f"  {symbol}: {BankSymbols.get_symbol_name(symbol)}")
    
    print(f"\nAdditional Financials ({len(BankSymbols.ADDITIONAL_FINANCIALS)}):")
    for symbol in BankSymbols.ADDITIONAL_FINANCIALS:
        print(f"  {symbol}: {BankSymbols.get_symbol_name(symbol)}")
    
    print(f"\nAll Primary Symbols ({len(BankSymbols.ALL_SYMBOLS)}):")
    for symbol in BankSymbols.ALL_SYMBOLS:
        print(f"  {symbol}: {BankSymbols.get_symbol_name(symbol)}")
    
    print(f"\nExtended Universe ({len(BankSymbols.COMPLETE_UNIVERSE)}):")
    for symbol in BankSymbols.COMPLETE_UNIVERSE:
        print(f"  {symbol}: {BankSymbols.get_symbol_name(symbol)}")
    
    print(f"\nSymbol Categories:")
    for category, symbols in BankSymbols.CATEGORIES.items():
        print(f"  {category}: {symbols}")
    
    # Test validation
    test_symbols = ['CBA.AX', 'INVALID.AX', 'MQG.AX']
    print(f"\nValidation Tests:")
    for symbol in test_symbols:
        valid = BankSymbols.validate_symbol(symbol)
        print(f"  {symbol}: {'✅ Valid' if valid else '❌ Invalid'}")
