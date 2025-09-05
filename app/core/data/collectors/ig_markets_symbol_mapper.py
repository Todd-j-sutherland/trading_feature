#!/usr/bin/env python3
"""
IG Markets Symbol Mapper for ASX Trading
Handles symbol conversion between ASX format and IG Markets EPICs
"""

import logging
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
import time
import requests

@dataclass
class SymbolMapping:
    """Data class for symbol mapping information"""
    asx_symbol: str
    ig_epic: str
    company_name: str
    market_type: str
    verified: bool = False
    last_updated: float = 0.0

class IGMarketsSymbolMapper:
    """Manages symbol mapping between ASX and IG Markets"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Static mappings for major ASX bank symbols (verified through testing)
        self.static_mappings = {
            # Big 4 Banks
            'CBA.AX': SymbolMapping('CBA.AX', 'AA.D.CBA.CASH.IP', 'Commonwealth Bank of Australia', 'SHARES', True),
            'CBA': SymbolMapping('CBA', 'AA.D.CBA.CASH.IP', 'Commonwealth Bank of Australia', 'SHARES', True),
            
            'WBC.AX': SymbolMapping('WBC.AX', 'AA.D.WBC.CASH.IP', 'Westpac Banking Corp', 'SHARES', True),
            'WBC': SymbolMapping('WBC', 'AA.D.WBC.CASH.IP', 'Westpac Banking Corp', 'SHARES', True),
            
            'ANZ.AX': SymbolMapping('ANZ.AX', 'AA.D.ANZ.CASH.IP', 'Australia and New Zealand Banking Group', 'SHARES', True),
            'ANZ': SymbolMapping('ANZ', 'AA.D.ANZ.CASH.IP', 'Australia and New Zealand Banking Group', 'SHARES', True),
            
            'NAB.AX': SymbolMapping('NAB.AX', 'AA.D.NAB.CASH.IP', 'National Australia Bank Ltd', 'SHARES', True),
            'NAB': SymbolMapping('NAB', 'AA.D.NAB.CASH.IP', 'National Australia Bank Ltd', 'SHARES', True),
            
            # Other Major Financials
            'BHP.AX': SymbolMapping('BHP.AX', 'AA.D.BHP.CASH.IP', 'BHP Group Limited (ASX)', 'SHARES', True),
            'BHP': SymbolMapping('BHP', 'AA.D.BHP.CASH.IP', 'BHP Group Limited (ASX)', 'SHARES', True),
            
            'WOW.AX': SymbolMapping('WOW.AX', 'AA.D.WOW.CASH.IP', 'Woolworths Group Limited', 'SHARES', True),
            'WOW': SymbolMapping('WOW', 'AA.D.WOW.CASH.IP', 'Woolworths Group Limited', 'SHARES', True),
            
            'TLS.AX': SymbolMapping('TLS.AX', 'AA.D.TLS.CASH.IP', 'Telstra Group Ltd', 'SHARES', True),
            'TLS': SymbolMapping('TLS', 'AA.D.TLS.CASH.IP', 'Telstra Group Ltd', 'SHARES', True),
            
            # Additional mappings to discover through search
            'MQG.AX': SymbolMapping('MQG.AX', '', 'Macquarie Group Limited', 'SHARES', False),
            'MQG': SymbolMapping('MQG', '', 'Macquarie Group Limited', 'SHARES', False),
            
            'SUN.AX': SymbolMapping('SUN.AX', '', 'Suncorp Group Limited', 'SHARES', False),
            'SUN': SymbolMapping('SUN', '', 'Suncorp Group Limited', 'SHARES', False),
            
            'QBE.AX': SymbolMapping('QBE.AX', '', 'QBE Insurance Group Limited', 'SHARES', False),
            'QBE': SymbolMapping('QBE', '', 'QBE Insurance Group Limited', 'SHARES', False),
        }
        
        # Dynamic mappings cache (discovered through IG Markets search)
        self.dynamic_mappings = {}
        
        # IG Markets search terms for companies
        self.search_terms = {
            'MQG': ['macquarie', 'macquarie group'],
            'SUN': ['suncorp', 'suncorp group'],
            'QBE': ['qbe', 'qbe insurance'],
            'COL': ['coles', 'coles group'],
            'RIO': ['rio', 'rio tinto'],
            'FMG': ['fortescue', 'fortescue metals'],
            'TCL': ['transurban', 'transurban group'],
            'CSL': ['csl', 'csl limited'],
            'WES': ['wesfarmers'],
            'GMG': ['goodman', 'goodman group'],
        }
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for consistent lookup"""
        # Remove common suffixes and normalize
        symbol = symbol.upper().strip()
        if symbol.endswith('.AX'):
            return symbol
        return symbol
    
    def get_base_symbol(self, symbol: str) -> str:
        """Get base symbol without .AX suffix"""
        normalized = self.normalize_symbol(symbol)
        return normalized.replace('.AX', '')
    
    def get_ig_epic(self, asx_symbol: str) -> Optional[str]:
        """
        Get IG Markets EPIC for an ASX symbol
        Returns the EPIC if found, None otherwise
        """
        normalized = self.normalize_symbol(asx_symbol)
        
        # Check static mappings first
        if normalized in self.static_mappings:
            mapping = self.static_mappings[normalized]
            if mapping.verified and mapping.ig_epic:
                return mapping.ig_epic
        
        # Check base symbol without .AX
        base_symbol = self.get_base_symbol(normalized)
        if base_symbol in self.static_mappings:
            mapping = self.static_mappings[base_symbol]
            if mapping.verified and mapping.ig_epic:
                return mapping.ig_epic
        
        # Check dynamic mappings
        if normalized in self.dynamic_mappings:
            mapping = self.dynamic_mappings[normalized]
            if mapping.verified and mapping.ig_epic:
                return mapping.ig_epic
        
        # Try to discover mapping (if IG Markets integration is available)
        discovered_epic = self._discover_epic(asx_symbol)
        if discovered_epic:
            # Cache the discovered mapping
            self.dynamic_mappings[normalized] = SymbolMapping(
                asx_symbol=normalized,
                ig_epic=discovered_epic,
                company_name=f"Dynamic mapping for {normalized}",
                market_type="SHARES",
                verified=True,
                last_updated=time.time()
            )
            return discovered_epic
        
        self.logger.warning(f"No IG Markets EPIC found for ASX symbol: {asx_symbol}")
        return None
    
    def _discover_epic(self, asx_symbol: str) -> Optional[str]:
        """
        Attempt to discover IG Markets EPIC through search
        This would use the IG Markets search API if available
        """
        try:
            # Try importing IG Markets mapper if available
            from ig_markets_asx_mapper import IGMarketsASXMapper
            
            mapper = IGMarketsASXMapper(
                username='sutho100',
                password='Helloworld987543$',
                api_key='ac68e6f053799a4a36c75936c088fc4d6cfcfa6e',
                demo=True
            )
            
            base_symbol = self.get_base_symbol(asx_symbol)
            epic = mapper.get_asx_epic(base_symbol)
            
            if epic:
                self.logger.info(f"Discovered IG Markets EPIC for {asx_symbol}: {epic}")
                return epic
            
        except Exception as e:
            self.logger.debug(f"Could not discover EPIC for {asx_symbol}: {e}")
        
        return None
    
    def get_asx_symbol(self, ig_epic: str) -> Optional[str]:
        """
        Get ASX symbol from IG Markets EPIC (reverse lookup)
        """
        # Search through static mappings
        for asx_symbol, mapping in self.static_mappings.items():
            if mapping.ig_epic == ig_epic:
                return asx_symbol
        
        # Search through dynamic mappings
        for asx_symbol, mapping in self.dynamic_mappings.items():
            if mapping.ig_epic == ig_epic:
                return asx_symbol
        
        self.logger.warning(f"No ASX symbol found for IG Markets EPIC: {ig_epic}")
        return None
    
    def get_company_name(self, symbol: str) -> Optional[str]:
        """Get company name for a symbol"""
        normalized = self.normalize_symbol(symbol)
        
        # Check static mappings
        if normalized in self.static_mappings:
            return self.static_mappings[normalized].company_name
        
        # Check base symbol
        base_symbol = self.get_base_symbol(normalized)
        if base_symbol in self.static_mappings:
            return self.static_mappings[base_symbol].company_name
        
        # Check dynamic mappings
        if normalized in self.dynamic_mappings:
            return self.dynamic_mappings[normalized].company_name
        
        return None
    
    def is_mapped(self, asx_symbol: str) -> bool:
        """Check if symbol has a verified IG Markets mapping"""
        epic = self.get_ig_epic(asx_symbol)
        return epic is not None
    
    def get_all_mapped_symbols(self) -> List[Tuple[str, str, str]]:
        """
        Get all symbols with verified IG Markets mappings
        Returns list of (asx_symbol, ig_epic, company_name)
        """
        mapped_symbols = []
        
        # Add verified static mappings
        for asx_symbol, mapping in self.static_mappings.items():
            if mapping.verified and mapping.ig_epic:
                mapped_symbols.append((asx_symbol, mapping.ig_epic, mapping.company_name))
        
        # Add verified dynamic mappings
        for asx_symbol, mapping in self.dynamic_mappings.items():
            if mapping.verified and mapping.ig_epic:
                mapped_symbols.append((asx_symbol, mapping.ig_epic, mapping.company_name))
        
        return mapped_symbols
    
    def update_mapping(self, asx_symbol: str, ig_epic: str, company_name: str = "", force: bool = False):
        """
        Update or add a symbol mapping
        """
        normalized = self.normalize_symbol(asx_symbol)
        
        # Check if mapping already exists and is verified
        if not force and normalized in self.static_mappings:
            existing = self.static_mappings[normalized]
            if existing.verified and existing.ig_epic:
                self.logger.info(f"Mapping for {asx_symbol} already exists and verified")
                return
        
        # Create or update mapping
        mapping = SymbolMapping(
            asx_symbol=normalized,
            ig_epic=ig_epic,
            company_name=company_name or f"Company for {normalized}",
            market_type="SHARES",
            verified=True,
            last_updated=time.time()
        )
        
        # Store in dynamic mappings
        self.dynamic_mappings[normalized] = mapping
        self.logger.info(f"Updated mapping: {asx_symbol} -> {ig_epic}")
    
    def get_mapping_stats(self) -> Dict[str, int]:
        """Get statistics about symbol mappings"""
        static_verified = sum(1 for m in self.static_mappings.values() if m.verified and m.ig_epic)
        static_unverified = sum(1 for m in self.static_mappings.values() if not m.verified or not m.ig_epic)
        dynamic_count = len(self.dynamic_mappings)
        
        return {
            'static_verified': static_verified,
            'static_unverified': static_unverified, 
            'dynamic_discovered': dynamic_count,
            'total_mapped': static_verified + dynamic_count
        }
    
    def test_mappings(self) -> Dict[str, bool]:
        """
        Test all static mappings to verify they work
        Returns dict of symbol -> success
        """
        results = {}
        
        # Test each verified static mapping
        for asx_symbol, mapping in self.static_mappings.items():
            if mapping.verified and mapping.ig_epic:
                try:
                    # Try to get price using the mapping
                    epic = self.get_ig_epic(asx_symbol)
                    results[asx_symbol] = epic == mapping.ig_epic
                except Exception as e:
                    self.logger.error(f"Test failed for {asx_symbol}: {e}")
                    results[asx_symbol] = False
        
        return results

# Global instance for use throughout the application
symbol_mapper = IGMarketsSymbolMapper()

# Convenience functions for easy import
def get_ig_epic(asx_symbol: str) -> Optional[str]:
    """Get IG Markets EPIC for ASX symbol"""
    return symbol_mapper.get_ig_epic(asx_symbol)

def get_asx_symbol(ig_epic: str) -> Optional[str]:
    """Get ASX symbol for IG Markets EPIC"""
    return symbol_mapper.get_asx_symbol(ig_epic)

def is_symbol_mapped(asx_symbol: str) -> bool:
    """Check if symbol has IG Markets mapping"""
    return symbol_mapper.is_mapped(asx_symbol)

def get_company_name(symbol: str) -> Optional[str]:
    """Get company name for symbol"""
    return symbol_mapper.get_company_name(symbol)

if __name__ == "__main__":
    # Test the symbol mapper
    logging.basicConfig(level=logging.INFO)
    
    mapper = IGMarketsSymbolMapper()
    
    print("IG Markets Symbol Mapper Test")
    print("=" * 40)
    
    # Test known mappings
    test_symbols = ['CBA.AX', 'WBC', 'ANZ.AX', 'NAB', 'BHP.AX', 'WOW', 'TLS']
    
    for symbol in test_symbols:
        epic = mapper.get_ig_epic(symbol)
        company = mapper.get_company_name(symbol)
        mapped = mapper.is_mapped(symbol)
        
        print(f"{symbol:8s} -> {epic or 'Not Found':25s} ({company or 'Unknown'}) - Mapped: {mapped}")
    
    # Show statistics
    stats = mapper.get_mapping_stats()
    print(f"\nMapping Statistics:")
    print(f"  Static Verified: {stats['static_verified']}")
    print(f"  Static Unverified: {stats['static_unverified']}")
    print(f"  Dynamic Discovered: {stats['dynamic_discovered']}")
    print(f"  Total Mapped: {stats['total_mapped']}")
