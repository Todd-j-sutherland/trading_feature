#!/usr/bin/env python3
"""
Test the enhanced paper trading simulator with all components
"""

import sys
import os
sys.path.append('.')

try:
    from app.core.trading.paper_trading_simulator import PaperTradingSimulator
    
    print("🧪 Testing Enhanced Paper Trading Simulator")
    print("=" * 60)
    
    # Initialize simulator
    print("⚙️ Initializing enhanced simulator...")
    simulator = PaperTradingSimulator(initial_capital=25000.0)
    
    # Test single symbol evaluation to see all components
    print("📊 Testing comprehensive evaluation for CBA.AX...")
    analysis = simulator.evaluate_trading_opportunity('CBA.AX')
    
    # Display what components were gathered
    print("\n🔍 Analysis Components Retrieved:")
    
    components = {
        'News Analysis': analysis.get('news_analysis', {}),
        'Technical Analysis': analysis.get('technical_analysis', {}),
        'ML Analysis': analysis.get('ml_analysis', {}),
        'Economic Context': analysis.get('economic_context', {})
    }
    
    for component_name, component_data in components.items():
        if 'error' in component_data:
            print(f"   ❌ {component_name}: {component_data['error']}")
        elif component_data:
            print(f"   ✅ {component_name}: Working")
            
            # Show specific details
            if component_name == 'News Analysis':
                sentiment = component_data.get('sentiment_score', 0)
                confidence = component_data.get('confidence', 0)
                print(f"      📰 Sentiment: {sentiment:+.3f}, Confidence: {confidence:.2f}")
                
            elif component_name == 'Technical Analysis':
                rsi = component_data.get('indicators', {}).get('rsi', 0)
                recommendation = component_data.get('recommendation', 'N/A')
                print(f"      📊 RSI: {rsi:.1f}, Recommendation: {recommendation}")
                
            elif component_name == 'ML Analysis':
                ml_score = component_data.get('overall_ml_score', 0)
                recommendation = component_data.get('trading_recommendation', 'N/A')
                print(f"      🧠 ML Score: {ml_score:.1f}/100, Recommendation: {recommendation}")
                
            elif component_name == 'Economic Context':
                regime = component_data.get('market_regime', {}).get('regime', 'N/A')
                sentiment = component_data.get('economic_sentiment_score', 0)
                print(f"      🌍 Market Regime: {regime}, Economic Sentiment: {sentiment:+.3f}")
        else:
            print(f"   ⚠️ {component_name}: No data returned")
    
    # Show final decision
    print(f"\n🎯 Final Trading Decision:")
    print(f"   Recommended Action: {analysis.get('recommended_action', 'N/A')}")
    print(f"   Base Confidence: {analysis.get('confidence', 0):.2f}")
    print(f"   Enhanced Confidence: {analysis.get('enhanced_confidence', 0):.2f}")
    print(f"   Signal Alignment: {analysis.get('signal_alignment_score', 0)}/2")
    
    print(f"\n✅ Enhanced analysis test completed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("This indicates missing dependencies")
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()