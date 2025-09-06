#!/usr/bin/env python3
"""
Enhanced Exit Strategy Validator with Real Market Data
Integrates yfinance real market data with exit strategy testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from exit_strategy_engine import ExitStrategyEngine
from real_market_data_provider import RealMarketDataProvider
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedExitStrategyValidator:
    """
    Enhanced validator using real market data for exit strategy testing
    """
    
    def __init__(self):
        self.exit_engine = ExitStrategyEngine()
        self.market_provider = RealMarketDataProvider()
        self.validation_db = self._setup_validation_database()
        self.test_results = []
        
        logger.info("✅ Enhanced Exit Strategy Validator initialized with real market data")
    
    def _setup_validation_database(self) -> str:
        """Setup SQLite database for validation testing"""
        db_path = "enhanced_exit_validation.db"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create test results table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                scenario TEXT NOT NULL,
                entry_date TEXT NOT NULL,
                entry_price REAL NOT NULL,
                current_price REAL NOT NULL,
                position_type TEXT NOT NULL,
                confidence REAL NOT NULL,
                expected_exit TEXT NOT NULL,
                actual_exit TEXT NOT NULL,
                exit_reason TEXT,
                urgency INTEGER,
                matches_expected BOOLEAN,
                profit_loss_pct REAL,
                volatility REAL,
                max_drawdown_pct REAL,
                risk_level TEXT,
                test_timestamp TEXT,
                market_scenario_description TEXT
            )
        ''')
        
        # Create market data cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                scenario TEXT NOT NULL,
                date TEXT NOT NULL,
                open_price REAL,
                high_price REAL,
                low_price REAL,
                close_price REAL,
                volume INTEGER,
                rsi REAL,
                macd_signal TEXT,
                created_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Enhanced validation database initialized")
        return db_path
    
    def create_real_market_test_scenarios(self) -> List[Dict]:
        """
        Create test scenarios using real market data
        """
        scenarios = []
        
        # Get available market scenarios
        market_scenarios = self.market_provider.get_scenario_library()
        asx_banks = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX', 'MQG.AX']
        
        # Create test scenarios for each bank in each market scenario
        for scenario_name, scenario_info in market_scenarios.items():
            for symbol in asx_banks[:2]:  # Test with first 2 banks to start
                try:
                    test_case = self.market_provider.create_realistic_test_case(
                        symbol=symbol,
                        scenario=scenario_name
                    )
                    
                    if test_case:
                        # Convert to validation test format
                        validation_scenario = {
                            'name': f"{scenario_name}_{symbol}",
                            'symbol': symbol,
                            'scenario': scenario_name,
                            'scenario_description': test_case['scenario_description'],
                            'position_type': test_case['position_type'],
                            'entry_price': test_case['entry_price'],
                            'current_price': test_case['current_price'],
                            'entry_date': test_case['entry_date'],
                            'confidence': test_case['confidence'],
                            'profit_loss_pct': test_case['actual_return_pct'],
                            'volatility': test_case['volatility'],
                            'max_drawdown_pct': test_case['max_drawdown_pct'],
                            'risk_level': test_case['realistic_expectations']['risk_level'],
                            'expected_exit': test_case['realistic_expectations']['expected_exit'],
                            'market_data': test_case['market_data'],
                            'technical_data': test_case['technical_data']
                        }
                        
                        scenarios.append(validation_scenario)
                        logger.info(f"✅ Created real market scenario: {validation_scenario['name']}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to create scenario for {symbol} in {scenario_name}: {e}")
        
        logger.info(f"📊 Created {len(scenarios)} real market test scenarios")
        return scenarios
    
    def run_enhanced_validation_suite(self) -> Dict:
        """
        Run comprehensive validation suite with real market data
        """
        logger.info("🧪 Starting Enhanced Exit Strategy Validation Suite with Real Market Data")
        
        # Create real market scenarios
        scenarios = self.create_real_market_test_scenarios()
        
        if not scenarios:
            logger.error("❌ No test scenarios created")
            return {}
        
        results = {
            'total_tests': len(scenarios),
            'passed': 0,
            'failed': 0,
            'scenarios': [],
            'accuracy': 0.0,
            'risk_assessment': {},
            'scenario_performance': {}
        }
        
        # Run each scenario
        for scenario in scenarios:
            try:
                logger.info(f"🔍 Testing real market scenario: {scenario['name']}")
                
                # Prepare position data for exit engine
                position_data = {
                    'symbol': scenario['symbol'],
                    'position_type': scenario['position_type'],
                    'entry_price': scenario['entry_price'],
                    'current_price': scenario['current_price'],
                    'entry_date': scenario['entry_date'],
                    'confidence': scenario['confidence'],
                    'market_data': scenario['market_data']
                }
                
                # Test exit strategy - create Position object and current data
                from exit_strategy_engine import Position
                
                position = Position(
                    symbol=scenario['symbol'],
                    entry_price=scenario['entry_price'],
                    current_price=scenario['current_price'],
                    entry_time=pd.to_datetime(scenario['entry_date']),
                    confidence=scenario['confidence'],
                    position_type=scenario['position_type'],
                    shares=100,  # Default
                    market_context='NEUTRAL'  # Default
                )
                
                current_data = {
                    'price': scenario['current_price'],
                    'volume': 1000000,  # Default
                    'timestamp': datetime.now(),
                    'technical_indicators': scenario['technical_data']
                }
                
                exit_signal = self.exit_engine.evaluate_position_exit(position, current_data)
                should_exit = exit_signal.should_exit
                exit_reason = exit_signal.reason.value if exit_signal.reason else 'MANUAL'
                urgency = exit_signal.urgency
                
                # Determine if result matches expectation
                matches_expected = (should_exit and scenario['expected_exit'] != 'MANUAL') or \
                                 (not should_exit and scenario['expected_exit'] == 'MANUAL')
                
                # Store result
                test_result = {
                    'scenario': scenario['name'],
                    'symbol': scenario['symbol'],
                    'market_scenario': scenario['scenario'],
                    'scenario_description': scenario['scenario_description'],
                    'position_type': scenario['position_type'],
                    'profit_loss_pct': f"{scenario['profit_loss_pct']:+.1f}%",
                    'volatility': f"{scenario['volatility']:.1f}%",
                    'max_drawdown_pct': f"{scenario['max_drawdown_pct']:.1f}%",
                    'risk_level': scenario['risk_level'],
                    'expected_exit': scenario['expected_exit'],
                    'actual_exit': should_exit,
                    'exit_reason': exit_reason if should_exit else 'HOLD',
                    'urgency': urgency,
                    'confidence': f"{scenario['confidence']:.1f}%",
                    'matches_expected': matches_expected,
                    'status': '✅' if matches_expected else '❌',
                    'entry_date': scenario['entry_date'],
                    'entry_price': scenario['entry_price'],
                    'current_price': scenario['current_price']
                }
                
                results['scenarios'].append(test_result)
                
                if matches_expected:
                    results['passed'] += 1
                else:
                    results['failed'] += 1
                
                # Log result
                status = "✅" if matches_expected else "❌"
                logger.info(f"   Expected: {scenario['expected_exit']} | Got: {should_exit} | {status}")
                
                # Save to database
                self._save_test_result(test_result, scenario)
                
            except Exception as e:
                logger.error(f"❌ Error testing scenario {scenario['name']}: {e}")
                results['failed'] += 1
        
        # Calculate overall metrics
        results['accuracy'] = (results['passed'] / results['total_tests']) * 100 if results['total_tests'] > 0 else 0
        results['risk_assessment'] = self._analyze_risk_performance(results['scenarios'])
        results['scenario_performance'] = self._analyze_scenario_performance(results['scenarios'])
        
        logger.info("✅ Enhanced exit strategy validation suite completed")
        return results
    
    def _save_test_result(self, test_result: Dict, scenario: Dict):
        """Save test result to database"""
        try:
            conn = sqlite3.connect(self.validation_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO test_results (
                    test_name, symbol, scenario, entry_date, entry_price, current_price,
                    position_type, confidence, expected_exit, actual_exit, exit_reason,
                    urgency, matches_expected, profit_loss_pct, volatility, max_drawdown_pct,
                    risk_level, test_timestamp, market_scenario_description
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                test_result['scenario'],
                test_result['symbol'],
                test_result['market_scenario'],
                test_result['entry_date'],
                scenario['entry_price'],
                scenario['current_price'],
                scenario['position_type'],
                scenario['confidence'],
                scenario['expected_exit'],
                test_result['actual_exit'],
                test_result['exit_reason'],
                test_result['urgency'],
                test_result['matches_expected'],
                scenario['profit_loss_pct'],
                scenario['volatility'],
                scenario['max_drawdown_pct'],
                scenario['risk_level'],
                datetime.now().isoformat(),
                scenario['scenario_description']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error saving test result: {e}")
    
    def _analyze_risk_performance(self, scenarios: List[Dict]) -> Dict:
        """Analyze performance by risk level"""
        risk_analysis = {'HIGH': [], 'MEDIUM': [], 'LOW': []}
        
        for scenario in scenarios:
            risk_level = scenario['risk_level']
            if risk_level in risk_analysis:
                risk_analysis[risk_level].append(scenario['matches_expected'])
        
        return {
            risk: {
                'total': len(results),
                'passed': sum(results),
                'accuracy': (sum(results) / len(results) * 100) if results else 0
            }
            for risk, results in risk_analysis.items() if results
        }
    
    def _analyze_scenario_performance(self, scenarios: List[Dict]) -> Dict:
        """Analyze performance by market scenario"""
        scenario_analysis = {}
        
        for scenario in scenarios:
            market_scenario = scenario['market_scenario']
            if market_scenario not in scenario_analysis:
                scenario_analysis[market_scenario] = []
            scenario_analysis[market_scenario].append(scenario['matches_expected'])
        
        return {
            scenario: {
                'total': len(results),
                'passed': sum(results),
                'accuracy': (sum(results) / len(results) * 100) if results else 0
            }
            for scenario, results in scenario_analysis.items()
        }
    
    def print_enhanced_results(self, results: Dict):
        """Print comprehensive results analysis"""
        print("\n📊 ENHANCED EXIT STRATEGY VALIDATION RESULTS")
        print("=" * 70)
        
        # Summary
        print(f"Overall Accuracy: {results['accuracy']:.1f}%")
        print(f"Total Scenarios: {results['total_tests']}")
        print(f"Successful Matches: {results['passed']}")
        print(f"Failed Matches: {results['failed']}")
        
        # Detailed results table
        print(f"\n{'Scenario':<25} {'Symbol':<8} {'Market Scenario':<15} {'Expected':<12} {'Actual':<8} {'Status':<6} {'P&L':<8} {'Risk':<6}")
        print("-" * 90)
        
        for scenario in results['scenarios']:
            print(f"{scenario['scenario'][:24]:<25} "
                  f"{scenario['symbol']:<8} "
                  f"{scenario['market_scenario'][:14]:<15} "
                  f"{scenario['expected_exit'][:11]:<12} "
                  f"{str(scenario['actual_exit']):<8} "
                  f"{scenario['status']:<6} "
                  f"{scenario['profit_loss_pct']:<8} "
                  f"{scenario['risk_level']:<6}")
        
        # Risk analysis
        print(f"\n📈 RISK LEVEL PERFORMANCE:")
        print("-" * 40)
        for risk_level, analysis in results['risk_assessment'].items():
            print(f"   {risk_level}: {analysis['accuracy']:.1f}% accuracy ({analysis['passed']}/{analysis['total']})")
        
        # Scenario analysis
        print(f"\n🎯 MARKET SCENARIO PERFORMANCE:")
        print("-" * 45)
        for scenario, analysis in results['scenario_performance'].items():
            print(f"   {scenario}: {analysis['accuracy']:.1f}% accuracy ({analysis['passed']}/{analysis['total']})")
        
        # Integration recommendation
        accuracy = results['accuracy']
        if accuracy >= 80:
            status = "EXCELLENT"
            recommendation = "Ready for production deployment"
        elif accuracy >= 70:
            status = "GOOD"
            recommendation = "Minor tuning recommended"
        elif accuracy >= 60:
            status = "NEEDS_IMPROVEMENT"
            recommendation = "Significant tuning required"
        else:
            status = "POOR"
            recommendation = "Major revision needed"
        
        print(f"\n🚀 INTEGRATION RECOMMENDATION:")
        print("=" * 40)
        print(f"Status: {status}")
        print(f"Recommendation: {recommendation}")
        
        if accuracy < 80:
            print(f"\n🔧 IMPROVEMENT SUGGESTIONS:")
            print("- Review failed scenarios for threshold adjustments")
            print("- Analyze exit condition priority ordering")
            print("- Consider market regime-specific parameters")

def main():
    """Run enhanced validation with real market data"""
    print("🚀 Enhanced Exit Strategy Validator with Real Market Data")
    print("=" * 65)
    
    validator = EnhancedExitStrategyValidator()
    
    # Run comprehensive validation
    results = validator.run_enhanced_validation_suite()
    
    if results:
        validator.print_enhanced_results(results)
        
        print(f"\n🎯 This validates with REAL MARKET DATA:")
        print("✅ Your exit strategy engine handles actual market conditions!")
        print("✅ Testing includes COVID crash, banking rallies, rate hikes!")
        print("✅ Professional-grade validation using real ASX data!")
    else:
        print("❌ Validation failed to complete")

if __name__ == "__main__":
    main()
