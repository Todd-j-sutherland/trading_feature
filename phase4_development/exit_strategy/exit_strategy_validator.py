#!/usr/bin/env python3
"""
Exit Strategy Integration Validator

This module safely validates the exit strategy engine with your existing prediction system
without affecting production. It extends your validation sandbox concept to test exit logic.
"""

import sys
import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from exit_strategy_engine import ExitStrategyEngine, Position, ExitSignal, ExitReason

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExitStrategyValidator:
    """
    Validates exit strategy integration with real prediction data
    but in a completely isolated environment
    """
    
    def __init__(self, production_db_path: str = None, validation_db_path: str = "exit_validation.db"):
        self.production_db_path = production_db_path
        self.validation_db_path = validation_db_path
        self.exit_engine = ExitStrategyEngine(db_path=validation_db_path)
        
        self.setup_validation_database()
        logger.info("✅ Exit Strategy Validator initialized")
    
    def setup_validation_database(self):
        """Set up isolated validation database"""
        conn = sqlite3.connect(self.validation_db_path)
        cursor = conn.cursor()
        
        # Create validation tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exit_validation_scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                entry_price REAL,
                current_price REAL,
                entry_time DATETIME,
                confidence REAL,
                position_type TEXT,
                shares INTEGER,
                market_context TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exit_validation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id INTEGER,
                should_exit BOOLEAN,
                exit_reason TEXT,
                urgency INTEGER,
                exit_confidence REAL,
                details TEXT,
                validation_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scenario_id) REFERENCES exit_validation_scenarios (id)
            )
        ''')
        
        # Copy news_sentiment structure for testing (if production DB available)
        if self.production_db_path and os.path.exists(self.production_db_path):
            try:
                self._copy_reference_data()
            except Exception as e:
                logger.warning(f"Could not copy reference data: {e}")
        
        conn.commit()
        conn.close()
        logger.info("✅ Exit validation database initialized")
    
    def _copy_reference_data(self):
        """Copy recent reference data from production for realistic testing"""
        try:
            # Read from production (read-only)
            prod_conn = sqlite3.connect(f"file:{self.production_db_path}?mode=ro", uri=True)
            
            # Get recent predictions and outcomes for reference
            recent_data = pd.read_sql_query("""
                SELECT p.symbol, p.entry_price, p.confidence, p.prediction_time,
                       p.news_sentiment, p.technical_score,
                       o.outcome_price, o.outcome_time
                FROM predictions p
                LEFT JOIN outcomes o ON p.id = o.prediction_id
                WHERE p.prediction_time > datetime('now', '-30 days')
                ORDER BY p.prediction_time DESC
                LIMIT 100
            """, prod_conn)
            
            # Copy news sentiment for testing
            news_data = pd.read_sql_query("""
                SELECT symbol, headline, sentiment_score, confidence, source, published_date
                FROM news_sentiment 
                WHERE published_date > datetime('now', '-7 days')
                ORDER BY published_date DESC
                LIMIT 50
            """, prod_conn)
            
            prod_conn.close()
            
            # Insert into validation database
            val_conn = sqlite3.connect(self.validation_db_path)
            
            if not recent_data.empty:
                recent_data.to_sql('reference_predictions', val_conn, if_exists='replace', index=False)
                logger.info(f"✅ Copied {len(recent_data)} reference predictions")
            
            if not news_data.empty:
                news_data.to_sql('news_sentiment', val_conn, if_exists='replace', index=False)
                logger.info(f"✅ Copied {len(news_data)} news sentiment records")
            
            val_conn.close()
            
        except Exception as e:
            logger.warning(f"Error copying reference data: {e}")
    
    def create_realistic_test_scenarios(self) -> List[Dict]:
        """Create realistic test scenarios based on actual trading patterns"""
        
        scenarios = [
            {
                'scenario_name': 'Quick_Profit_High_Confidence',
                'symbol': 'CBA.AX',
                'entry_price': 120.00,
                'current_price': 125.40,  # 4.5% profit
                'entry_time': datetime.now() - timedelta(hours=4),
                'confidence': 0.82,
                'position_type': 'BUY',
                'shares': 100,
                'market_context': 'BULLISH',
                'expected_exit': True,
                'expected_reason': ExitReason.PROFIT_TARGET
            },
            
            {
                'scenario_name': 'Stop_Loss_Medium_Confidence',
                'symbol': 'WBC.AX', 
                'entry_price': 25.00,
                'current_price': 24.25,  # -3% loss
                'entry_time': datetime.now() - timedelta(days=1),
                'confidence': 0.68,
                'position_type': 'BUY',
                'shares': 200,
                'market_context': 'NEUTRAL',
                'expected_exit': True,
                'expected_reason': ExitReason.STOP_LOSS
            },
            
            {
                'scenario_name': 'Time_Limit_Stagnant_Position',
                'symbol': 'ANZ.AX',
                'entry_price': 28.00,
                'current_price': 28.05,  # Minimal movement
                'entry_time': datetime.now() - timedelta(days=5, hours=2),
                'confidence': 0.65,
                'position_type': 'BUY',
                'shares': 150,
                'market_context': 'NEUTRAL',
                'expected_exit': True,
                'expected_reason': ExitReason.TIME_LIMIT
            },
            
            {
                'scenario_name': 'Hold_Strong_Position',
                'symbol': 'NAB.AX',
                'entry_price': 32.00,
                'current_price': 32.50,  # 1.56% profit (below target)
                'entry_time': datetime.now() - timedelta(days=2),
                'confidence': 0.78,
                'position_type': 'BUY',
                'shares': 120,
                'market_context': 'BULLISH',
                'expected_exit': False,
                'expected_reason': None
            },
            
            {
                'scenario_name': 'Technical_Breakdown_Exit',
                'symbol': 'MQG.AX',
                'entry_price': 180.00,
                'current_price': 178.50,  # Small loss
                'entry_time': datetime.now() - timedelta(days=1),
                'confidence': 0.72,
                'position_type': 'BUY',
                'shares': 50,
                'market_context': 'BEARISH',
                'expected_exit': True,  # Due to technical breakdown
                'expected_reason': ExitReason.TECHNICAL_BREAKDOWN,
                'technical_data': {
                    'rsi': 82.0,  # Extremely overbought
                    'macd_signal': 'bearish',
                    'price_trend': 'strongly_bearish'
                }
            },
            
            {
                'scenario_name': 'Profitable_SELL_Position',
                'symbol': 'CBA.AX',
                'entry_price': 120.00,
                'current_price': 116.40,  # 3% profit on short
                'entry_time': datetime.now() - timedelta(hours=6),
                'confidence': 0.75,
                'position_type': 'SELL',
                'shares': 100,
                'market_context': 'BEARISH',
                'expected_exit': True,
                'expected_reason': ExitReason.PROFIT_TARGET
            }
        ]
        
        return scenarios
    
    def run_validation_suite(self) -> pd.DataFrame:
        """Run comprehensive exit strategy validation"""
        logger.info("🧪 Starting Exit Strategy Validation Suite")
        
        scenarios = self.create_realistic_test_scenarios()
        results = []
        
        conn = sqlite3.connect(self.validation_db_path)
        cursor = conn.cursor()
        
        for scenario in scenarios:
            logger.info(f"🔍 Testing scenario: {scenario['scenario_name']}")
            
            # Create position object
            position = Position(
                symbol=scenario['symbol'],
                entry_price=scenario['entry_price'],
                current_price=scenario['current_price'],
                entry_time=scenario['entry_time'],
                confidence=scenario['confidence'],
                position_type=scenario['position_type'],
                shares=scenario['shares'],
                market_context=scenario['market_context'],
                original_prediction_id=f"test_{scenario['scenario_name']}"
            )
            
            # Save scenario to database
            cursor.execute('''
                INSERT INTO exit_validation_scenarios 
                (scenario_name, symbol, entry_price, current_price, entry_time,
                 confidence, position_type, shares, market_context)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                scenario['scenario_name'], scenario['symbol'], scenario['entry_price'],
                scenario['current_price'], scenario['entry_time'], scenario['confidence'],
                scenario['position_type'], scenario['shares'], scenario['market_context']
            ))
            
            scenario_id = cursor.lastrowid
            
            # Prepare current data
            current_data = {
                'current_time': datetime.now(),
                'rsi': scenario.get('technical_data', {}).get('rsi', 55.0),
                'macd_signal': scenario.get('technical_data', {}).get('macd_signal', 'neutral'),
                'price_trend': scenario.get('technical_data', {}).get('price_trend', 'sideways')
            }
            
            # Evaluate exit strategy
            exit_signal = self.exit_engine.evaluate_position_exit(position, current_data)
            
            # Save result
            cursor.execute('''
                INSERT INTO exit_validation_results 
                (scenario_id, should_exit, exit_reason, urgency, exit_confidence, details)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                scenario_id, exit_signal.should_exit, exit_signal.reason.value,
                exit_signal.urgency, exit_signal.confidence, exit_signal.details
            ))
            
            # Check if result matches expectation
            matches_expected = (
                exit_signal.should_exit == scenario['expected_exit'] and
                (not scenario['expected_exit'] or exit_signal.reason == scenario['expected_reason'])
            )
            
            # Calculate profit/loss
            if position.position_type == 'BUY':
                profit_pct = ((position.current_price - position.entry_price) / position.entry_price) * 100
            else:  # SELL
                profit_pct = ((position.entry_price - position.current_price) / position.entry_price) * 100
            
            # Add to results
            result = {
                'scenario': scenario['scenario_name'],
                'symbol': scenario['symbol'],
                'position_type': scenario['position_type'],
                'profit_loss_pct': f"{profit_pct:+.1f}%",
                'expected_exit': scenario['expected_exit'],
                'actual_exit': exit_signal.should_exit,
                'exit_reason': exit_signal.reason.value,
                'urgency': exit_signal.urgency,
                'confidence': f"{exit_signal.confidence:.1%}",
                'matches_expected': '✅' if matches_expected else '❌',
                'details': exit_signal.details[:50] + "..." if len(exit_signal.details) > 50 else exit_signal.details
            }
            results.append(result)
            
            match_status = '✅' if matches_expected else '❌'
            logger.info(f"   Expected: {scenario['expected_exit']} | Got: {exit_signal.should_exit} | {match_status}")
        
        conn.commit()
        conn.close()
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        logger.info("✅ Exit strategy validation suite completed")
        return results_df
    
    def analyze_integration_impact(self, results_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the impact of integrating exit strategy with existing system"""
        
        total_scenarios = len(results_df)
        successful_matches = len(results_df[results_df['matches_expected'] == '✅'])
        accuracy = successful_matches / total_scenarios if total_scenarios > 0 else 0
        
        # Analyze exit reasons
        exit_reason_counts = results_df['exit_reason'].value_counts()
        
        # Analyze by position type
        buy_positions = results_df[results_df['position_type'] == 'BUY']
        sell_positions = results_df[results_df['position_type'] == 'SELL']
        
        # Calculate potential impact on existing system
        profitable_exits = len(results_df[
            (results_df['actual_exit'] == True) & 
            (results_df['profit_loss_pct'].str.replace('%', '').astype(float) > 0)
        ])
        
        loss_prevention = len(results_df[
            (results_df['actual_exit'] == True) & 
            (results_df['profit_loss_pct'].str.replace('%', '').astype(float) < 0)
        ])
        
        analysis = {
            'validation_accuracy': accuracy,
            'total_scenarios': total_scenarios,
            'successful_matches': successful_matches,
            'exit_reason_distribution': exit_reason_counts.to_dict(),
            'buy_position_accuracy': len(buy_positions[buy_positions['matches_expected'] == '✅']) / len(buy_positions) if len(buy_positions) > 0 else 0,
            'sell_position_accuracy': len(sell_positions[sell_positions['matches_expected'] == '✅']) / len(sell_positions) if len(sell_positions) > 0 else 0,
            'profitable_exits': profitable_exits,
            'loss_prevention_exits': loss_prevention,
            'integration_readiness': 'READY' if accuracy >= 0.8 else 'NEEDS_TUNING'
        }
        
        return analysis

def main():
    """Run the exit strategy integration validation"""
    print("🧪 Exit Strategy Integration Validator")
    print("=" * 50)
    print("Safely testing exit strategy with realistic scenarios")
    
    # Initialize validator (without production DB for now)
    validator = ExitStrategyValidator()
    
    # Run validation suite
    results = validator.run_validation_suite()
    
    print("\n📊 EXIT STRATEGY VALIDATION RESULTS")
    print("=" * 60)
    print(results.to_string(index=False))
    
    # Analysis
    analysis = validator.analyze_integration_impact(results)
    
    print(f"\n📈 INTEGRATION IMPACT ANALYSIS")
    print("=" * 40)
    print(f"Overall Accuracy: {analysis['validation_accuracy']:.1%}")
    print(f"Total Scenarios: {analysis['total_scenarios']}")
    print(f"Successful Matches: {analysis['successful_matches']}")
    print(f"BUY Position Accuracy: {analysis['buy_position_accuracy']:.1%}")
    print(f"SELL Position Accuracy: {analysis['sell_position_accuracy']:.1%}")
    print(f"Profitable Exits: {analysis['profitable_exits']}")
    print(f"Loss Prevention: {analysis['loss_prevention_exits']}")
    print(f"Integration Status: {analysis['integration_readiness']}")
    
    print(f"\n🎯 EXIT REASON DISTRIBUTION:")
    for reason, count in analysis['exit_reason_distribution'].items():
        print(f"   {reason}: {count}")
    
    print(f"\n🚀 INTEGRATION RECOMMENDATION:")
    if analysis['integration_readiness'] == 'READY':
        print("✅ Exit Strategy Engine is ready for integration!")
        print("   - High validation accuracy")
        print("   - Consistent exit logic")
        print("   - Safe for production testing")
    else:
        print("⚠️  Exit Strategy Engine needs fine-tuning")
        print("   - Some edge cases need adjustment")
        print("   - Recommend additional testing")
        print("   - Review failed scenarios")
    
    print(f"\n🎯 This validates: 'How does it know when to exit the prediction?'")
    print("✅ The exit strategy engine provides systematic, rule-based exits!")

if __name__ == "__main__":
    main()
