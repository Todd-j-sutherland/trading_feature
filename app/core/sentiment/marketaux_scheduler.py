#!/usr/bin/env python3
"""
MarketAux Strategic Usage Plan
Optimizes 100 requests/day for maximum trading value
"""

import schedule
import time
from datetime import datetime, timedelta
import logging
from typing import Dict, List
import json
from pathlib import Path

from .marketaux_integration import MarketAuxManager, MarketAuxStrategy

logger = logging.getLogger(__name__)

class MarketAuxScheduler:
    """
    Intelligent scheduler for MarketAux API requests
    Maximizes value from 100 requests/day limit
    """
    
    def __init__(self, api_token: str = None):
        self.manager = MarketAuxManager(api_token)
        self.strategy = MarketAuxStrategy()
        self.schedule_file = Path("data/marketaux_schedule.json")
        
        # Trading calendar - when to be active
        self.trading_days = [0, 1, 2, 3, 4]  # Monday-Friday
        self.trading_hours = {
            'start': 9,    # 9 AM
            'end': 16      # 4 PM
        }
        
        # Event-driven triggers (save requests for important events)
        self.high_priority_events = [
            'RBA_DECISION',
            'BANK_EARNINGS', 
            'REGULATORY_ANNOUNCEMENT',
            'MARKET_CRASH',
            'MAJOR_BANK_NEWS'
        ]
        
        # Request allocation strategy
        self.daily_allocation = {
            'pre_market': {
                'time': '08:30',
                'requests': 1,
                'symbols': ['CBA', 'ANZ', 'WBC', 'NAB'],
                'description': 'Pre-market sentiment for Big 4',
                'priority': 'high'
            },
            'market_open': {
                'time': '10:00', 
                'requests': 1,
                'symbols': ['CBA', 'ANZ', 'WBC', 'NAB', 'MQG', 'QBE'],
                'description': 'Market opening sentiment',
                'priority': 'high'
            },
            'midday_pulse': {
                'time': '12:30',
                'requests': 1,
                'symbols': ['CBA', 'ANZ', 'WBC', 'NAB'],
                'description': 'Midday news check',
                'priority': 'medium'
            },
            'afternoon_update': {
                'time': '14:30',
                'requests': 1,
                'symbols': ['CBA', 'ANZ', 'WBC', 'NAB'],
                'description': 'Afternoon sentiment',
                'priority': 'medium'
            },
            'market_close': {
                'time': '16:15',
                'requests': 1,
                'symbols': ['CBA', 'ANZ', 'WBC', 'NAB', 'MQG', 'QBE'],
                'description': 'Market close summary',
                'priority': 'high'
            },
            'after_hours': {
                'time': '17:30',
                'requests': 1,
                'symbols': ['CBA', 'ANZ', 'WBC', 'NAB'],
                'description': 'After-hours news digest',
                'priority': 'low'
            }
        }
        
        # Reserve requests for events
        self.event_reserve = 10  # Keep 10 requests for unexpected events
        self.scheduled_requests = sum(alloc['requests'] for alloc in self.daily_allocation.values())
        
        logger.info(f"Scheduled requests: {self.scheduled_requests}, Event reserve: {self.event_reserve}")
    
    def setup_schedule(self):
        """Setup the daily schedule for MarketAux requests"""
        
        # Clear existing schedule
        schedule.clear()
        
        # Only schedule on trading days
        for day_name in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']:
            for slot_name, slot_config in self.daily_allocation.items():
                getattr(schedule.every(), day_name).at(slot_config['time']).do(
                    self.execute_scheduled_request,
                    slot_name=slot_name,
                    config=slot_config
                )
        
        # Daily cleanup at end of day
        schedule.every().day.at("23:50").do(self.daily_cleanup)
        
        logger.info("MarketAux schedule configured for trading days")
    
    def execute_scheduled_request(self, slot_name: str, config: Dict):
        """Execute a scheduled sentiment analysis request"""
        
        # Check if it's a trading day
        if datetime.now().weekday() not in self.trading_days:
            logger.info(f"Skipping {slot_name} - not a trading day")
            return
        
        # Check if we have requests available
        if not self.manager.can_make_request(config['requests']):
            logger.warning(f"Skipping {slot_name} - insufficient requests remaining")
            self._log_schedule_event(slot_name, "skipped", "insufficient_requests")
            return
        
        try:
            logger.info(f"Executing {slot_name}: {config['description']}")
            
            # Get sentiment data
            sentiment_data = self.manager.get_sentiment_analysis(
                symbols=config['symbols'],
                strategy=slot_name
            )
            
            if sentiment_data:
                # Log successful request
                self._log_schedule_event(slot_name, "success", {
                    'symbols_analyzed': len(sentiment_data),
                    'avg_sentiment': sum(s.sentiment_score for s in sentiment_data) / len(sentiment_data),
                    'total_news_volume': sum(s.news_volume for s in sentiment_data)
                })
                
                # Store results for ML system
                self._store_sentiment_results(slot_name, sentiment_data)
                
                logger.info(f"{slot_name} completed successfully - {len(sentiment_data)} symbols analyzed")
            else:
                self._log_schedule_event(slot_name, "failed", "no_data_returned")
                logger.warning(f"{slot_name} failed - no data returned")
                
        except Exception as e:
            self._log_schedule_event(slot_name, "error", str(e))
            logger.error(f"Error executing {slot_name}: {e}")
    
    def trigger_event_request(self, event_type: str, symbols: List[str] = None, priority: str = "high"):
        """
        Trigger an event-driven request for breaking news or important events
        
        Args:
            event_type: Type of event (RBA_DECISION, BANK_EARNINGS, etc.)
            symbols: Specific symbols to analyze (default: Big 4 banks)
            priority: Request priority level
        """
        
        if symbols is None:
            symbols = ['CBA', 'ANZ', 'WBC', 'NAB']
        
        # Check if we have emergency requests available
        if not self.manager.can_make_request():
            logger.warning(f"Cannot trigger event request for {event_type} - no requests remaining")
            return None
        
        logger.info(f"Triggering event-driven request: {event_type}")
        
        try:
            sentiment_data = self.manager.get_sentiment_analysis(
                symbols=symbols,
                strategy="event_driven",
                timeframe_hours=1  # Shorter cache for events
            )
            
            if sentiment_data:
                # Log event request
                self._log_schedule_event(f"EVENT_{event_type}", "success", {
                    'symbols_analyzed': len(sentiment_data),
                    'avg_sentiment': sum(s.sentiment_score for s in sentiment_data) / len(sentiment_data),
                    'priority': priority
                })
                
                # Store results with event marker
                self._store_sentiment_results(f"event_{event_type.lower()}", sentiment_data)
                
                logger.info(f"Event request {event_type} completed - {len(sentiment_data)} symbols analyzed")
                return sentiment_data
            else:
                logger.warning(f"Event request {event_type} failed - no data returned")
                return None
                
        except Exception as e:
            logger.error(f"Error executing event request {event_type}: {e}")
            return None
    
    def _store_sentiment_results(self, request_type: str, sentiment_data: List):
        """Store sentiment results for ML system integration"""
        
        results_file = Path(f"data/sentiment_results_{datetime.now().strftime('%Y%m%d')}.json")
        
        # Load existing results or create new
        if results_file.exists():
            with open(results_file, 'r') as f:
                results = json.load(f)
        else:
            results = {}
        
        # Add new results
        timestamp = datetime.now().isoformat()
        results[timestamp] = {
            'request_type': request_type,
            'sentiment_data': [
                {
                    'symbol': s.symbol,
                    'sentiment_score': s.sentiment_score,
                    'confidence': s.confidence,
                    'news_volume': s.news_volume,
                    'source_quality': s.source_quality,
                    'highlights': s.highlights[:3]  # Top 3 highlights
                }
                for s in sentiment_data
            ]
        }
        
        # Save results
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
    
    def _log_schedule_event(self, event_name: str, status: str, details=None):
        """Log schedule events for monitoring and optimization"""
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_name': event_name,
            'status': status,
            'details': details,
            'requests_remaining': self.manager.usage.requests_remaining
        }
        
        # Append to daily log
        log_file = Path(f"data/schedule_log_{datetime.now().strftime('%Y%m%d')}.json")
        
        if log_file.exists():
            with open(log_file, 'r') as f:
                logs = json.load(f)
        else:
            logs = []
        
        logs.append(log_entry)
        
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def daily_cleanup(self):
        """End of day cleanup and reporting"""
        
        # Get usage stats
        stats = self.manager.get_usage_stats()
        
        # Clear old cache
        self.manager.clear_cache(older_than_hours=24)
        
        # Generate daily report
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'requests_used': stats['requests_made'],
            'requests_remaining': stats['requests_remaining'],
            'efficiency': (stats['requests_made'] / stats['daily_limit']) * 100,
            'trading_day': datetime.now().weekday() in self.trading_days
        }
        
        # Save daily report
        report_file = Path(f"data/daily_report_{report['date']}.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Daily cleanup completed - Used {report['requests_used']}/{stats['daily_limit']} requests ({report['efficiency']:.1f}%)")
    
    def get_status_report(self) -> Dict:
        """Get current status and recommendations"""
        
        stats = self.manager.get_usage_stats()
        current_time = datetime.now()
        
        # Calculate efficiency
        hours_elapsed = current_time.hour + (current_time.minute / 60)
        expected_usage = (hours_elapsed / 24) * self.manager.max_daily_requests
        efficiency = stats['requests_made'] / expected_usage if expected_usage > 0 else 0
        
        # Get next scheduled request
        next_request = None
        for slot_name, config in self.daily_allocation.items():
            slot_time = datetime.strptime(config['time'], '%H:%M').time()
            slot_datetime = datetime.combine(current_time.date(), slot_time)
            if slot_datetime > current_time:
                next_request = {
                    'name': slot_name,
                    'time': config['time'],
                    'description': config['description']
                }
                break
        
        return {
            'current_time': current_time.isoformat(),
            'usage_stats': stats,
            'efficiency': efficiency,
            'status': 'optimal' if 0.8 <= efficiency <= 1.2 else 'suboptimal',
            'next_scheduled_request': next_request,
            'can_handle_emergency': stats['requests_remaining'] >= self.event_reserve,
            'recommendations': self._get_recommendations(stats, efficiency)
        }
    
    def _get_recommendations(self, stats: Dict, efficiency: float) -> List[str]:
        """Get optimization recommendations"""
        recommendations = []
        
        if efficiency < 0.5:
            recommendations.append("Usage below expected - consider additional analysis requests")
        elif efficiency > 1.5:
            recommendations.append("Usage above expected - consider optimizing request frequency")
        
        if stats['requests_remaining'] < self.event_reserve:
            recommendations.append("Low request reserves - prioritize only critical events")
        
        if stats['requests_remaining'] < 5:
            recommendations.append("Very low requests remaining - emergency mode only")
        
        return recommendations
    
    def run_scheduler(self):
        """Run the scheduler (blocking call)"""
        logger.info("Starting MarketAux scheduler...")
        
        self.setup_schedule()
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)  # Continue after error

def create_usage_plan():
    """Create strategic usage plan document"""
    
    plan = {
        "marketaux_strategic_usage_plan": {
            "overview": {
                "daily_limit": 100,
                "recommended_usage": 95,
                "emergency_reserve": 5,
                "focus": "ASX financial sector sentiment"
            },
            "request_allocation": {
                "scheduled_requests": 6,
                "event_driven_reserve": 10,
                "weekly_analysis": 5,
                "buffer": 5
            },
            "daily_schedule": {
                "08:30": "Pre-market Big 4 sentiment",
                "10:00": "Market open extended analysis",
                "12:30": "Midday pulse check",
                "14:30": "Afternoon update",
                "16:15": "Market close summary",
                "17:30": "After-hours digest"
            },
            "optimization_strategies": [
                "Batch multiple symbols in single request",
                "Use 6-hour caching for regular checks",
                "Reserve 10 requests for breaking news",
                "Focus on Big 4 banks for maximum relevance",
                "Skip weekends and market holidays",
                "Prioritize market hours requests"
            ],
            "event_triggers": [
                "RBA interest rate decisions",
                "Major bank earnings releases",
                "Regulatory announcements",
                "Market volatility spikes",
                "Banking sector news"
            ],
            "success_metrics": [
                "90%+ of daily quota utilized efficiently",
                "Zero missed critical events",
                "High correlation with actual price movements",
                "Improved ML model accuracy"
            ]
        }
    }
    
    with open('MARKETAUX_USAGE_PLAN.json', 'w') as f:
        json.dump(plan, f, indent=2)
    
    return plan

if __name__ == "__main__":
    # Create and run scheduler
    scheduler = MarketAuxScheduler()
    
    # Print status
    status = scheduler.get_status_report()
    print("MarketAux Status:", json.dumps(status, indent=2))
    
    # Create usage plan
    plan = create_usage_plan()
    print("Usage plan created: MARKETAUX_USAGE_PLAN.json")
