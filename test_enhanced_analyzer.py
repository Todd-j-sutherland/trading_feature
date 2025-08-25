import sys
sys.path.insert(0, "/root/test")

from enhanced_morning_analyzer_with_ml import EnhancedMorningAnalyzer

print("TESTING ENHANCED ANALYZER WITH FIXED PRICE INTEGRATION")
print("=" * 60)

# Create analyzer
analyzer = EnhancedMorningAnalyzer()

# Test with one symbol
symbol = "CBA.AX"
print(f"Testing {symbol}...")

try:
    # This will test our price integration fix
    result = analyzer.analyze_symbol(symbol)
    print(f"Analysis completed for {symbol}")
    print(f"Analysis keys: {list(result.keys()) if result else None}")
    
    if result:
        confidence = result.get("confidence", "N/A")
        entry_price = result.get("entry_price", "N/A")
        print(f"Confidence: {confidence}")
        print(f"Entry Price: {entry_price}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
