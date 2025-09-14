"""
Scheduler Service - Market-Aware Task Scheduling

Purpose:
This service replaces traditional cron scheduling with market-aware scheduling
that understands ASX trading hours, market holidays, and optimal execution times
for trading-related tasks. It manages the orchestration of all trading system tasks.

Key Features:
- ASX market hours awareness (10:00-16:00 AEST)
- Pre-market, during-market, and post-market task scheduling
- Market holiday detection and handling
- Dynamic task prioritization based on market conditions
- Failed task retry with exponential backoff
- Task dependency management
- Real-time task monitoring and logging

Scheduled Tasks:
- Morning analysis (pre-market): 09:30 AEST
- Prediction generation: 09:45 AEST  
- Market monitoring (during market): Every 15 minutes
- Evening analysis (post-market): 17:00 AEST
- Paper trading synchronization: 17:30 AEST
- Daily backup: 02:00 AEST
- Model retraining: Weekends

API Endpoints:
- schedule_task(task_config) - Schedule new task
- cancel_task(task_id) - Cancel scheduled task
- list_tasks() - Get all scheduled tasks
- execute_task(task_id) - Manually execute task
- get_task_status(task_id) - Get task execution status
- set_market_schedule(config) - Update market schedule

Market Awareness:
- Pre-market: 08:00-10:00 (preparation tasks)
- Market hours: 10:00-16:00 (monitoring and execution)
- Post-market: 16:00-18:00 (analysis and reporting)
- Off-hours: 18:00-08:00 (maintenance and training)

Integration:
- Orchestrates all other microservices
- Publishes task execution events
- Integrates with monitoring service for alerts

Dependencies:
- All trading microservices
- Market data for holiday detection
- Redis for task persistence

Related Files:
- cron_market_aware.txt - Previous cron configuration
- market_aware_daily_manager.py - Task management logic
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta, time
import json
from typing import Dict, List, Any, Optional
import pytz
from dataclasses import dataclass, asdict
import uuid
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.base_service import BaseService

@dataclass
class ScheduledTask:
    task_id: str
    name: str
    task_type: str
    schedule_time: str  # HH:MM format
    weekdays: List[int]  # 0=Monday, 6=Sunday
    market_phase: str  # pre_market, market_hours, post_market, off_hours
    service_name: str
    method_name: str
    parameters: Dict[str, Any]
    enabled: bool = True
    last_run: Optional[str] = None
    last_result: Optional[str] = None
    next_run: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    priority: int = 5  # 1=highest, 10=lowest
    timeout_seconds: int = 300
    created_at: str = None
    failure_count: int = 0
    success_count: int = 0
    average_execution_time: float = 0.0
    last_error: Optional[str] = None
    
    def __post_init__(self):
        """Validate task data after initialization"""
        if not self.task_id or not isinstance(self.task_id, str):
            raise ValueError("task_id must be a non-empty string")
        
        if not self.name or not isinstance(self.name, str) or len(self.name.strip()) == 0:
            raise ValueError("name must be a non-empty string")
        
        # Validate schedule_time format
        if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', self.schedule_time):
            raise ValueError("schedule_time must be in HH:MM format")
        
        # Validate weekdays
        if not isinstance(self.weekdays, list) or not all(isinstance(d, int) and 0 <= d <= 6 for d in self.weekdays):
            raise ValueError("weekdays must be a list of integers 0-6")
        
        # Validate market_phase
        valid_phases = {"pre_market", "market_hours", "post_market", "off_hours"}
        if self.market_phase not in valid_phases:
            raise ValueError(f"market_phase must be one of {valid_phases}")
        
        # Validate service and method names
        if not self.service_name or not isinstance(self.service_name, str):
            raise ValueError("service_name must be a non-empty string")
        
        if not self.method_name or not isinstance(self.method_name, str):
            raise ValueError("method_name must be a non-empty string")
        
        # Validate numeric constraints
        if not isinstance(self.priority, int) or not 1 <= self.priority <= 10:
            raise ValueError("priority must be an integer between 1 and 10")
        
        if not isinstance(self.timeout_seconds, int) or self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be a positive integer")
        
        if not isinstance(self.max_retries, int) or self.max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer")

class SchedulerService(BaseService):
    """Market-aware task scheduler for trading system with comprehensive error handling"""
    
    def __init__(self):
        super().__init__("scheduler")
        
        # Australian Eastern Time with validation
        try:
            self.timezone = pytz.timezone('Australia/Sydney')
        except Exception as e:
            self.logger.error(f'"error": "timezone_initialization_failed", "details": "{e}", "action": "using_utc_fallback"')
            self.timezone = pytz.UTC
        
        # Market schedule configuration with validation
        self.market_schedule = {
            "market_open": time(10, 0),    # 10:00 AM
            "market_close": time(16, 0),   # 4:00 PM
            "pre_market_start": time(8, 0), # 8:00 AM
            "post_market_end": time(18, 0), # 6:00 PM
            "trading_days": [0, 1, 2, 3, 4]  # Monday-Friday
        }
        
        # Task storage with thread-safe access patterns
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_history: List[Dict] = []
        self.task_lock = asyncio.Lock()  # For thread-safe operations
        
        # Enhanced metrics tracking
        self.total_executions = 0
        self.total_failures = 0
        self.total_timeouts = 0
        self.average_execution_time = 0.0
        self.last_cleanup_time = datetime.now()
        
        # Market holidays with validation and future-proofing
        self.market_holidays = self._initialize_market_holidays()
        
        # Rate limiting and circuit breaker
        self.max_concurrent_tasks = 10
        self.circuit_breaker_threshold = 5  # failures before circuit opens
        self.circuit_breaker_reset_time = 300  # 5 minutes
        self.circuit_breaker_failures = {}
        
        # Register enhanced methods with input validation
        self.register_handler("schedule_task", self.schedule_task)
        self.register_handler("cancel_task", self.cancel_task)
        self.register_handler("list_tasks", self.list_tasks)
        self.register_handler("execute_task", self.execute_task)
        self.register_handler("get_task_status", self.get_task_status)
        self.register_handler("set_market_schedule", self.set_market_schedule)
        self.register_handler("get_market_status", self.get_market_status)
        self.register_handler("pause_scheduler", self.pause_scheduler)
        self.register_handler("resume_scheduler", self.resume_scheduler)
        self.register_handler("get_scheduler_metrics", self.get_scheduler_metrics)
        self.register_handler("cleanup_tasks", self.cleanup_tasks)
        self.register_handler("validate_task_config", self.validate_task_config)
        
        # Scheduler state with validation
        self.scheduler_running = True
        self.scheduler_paused = False
        self.scheduler_start_time = datetime.now()
        
        # Initialize background tasks with error handling
        asyncio.create_task(self._safe_create_default_tasks())
        asyncio.create_task(self._safe_scheduler_loop())
        asyncio.create_task(self._safe_cleanup_loop())
        asyncio.create_task(self._safe_metrics_update_loop())
    
    def _initialize_market_holidays(self) -> List[str]:
        """Initialize market holidays with current year and validation"""
        current_year = datetime.now().year
        
        # Base holidays - should be updated annually or fetched from API
        holidays = [
            f"{current_year}-01-01",  # New Year's Day
            f"{current_year}-01-26",  # Australia Day
            f"{current_year}-04-25",  # ANZAC Day
            f"{current_year}-12-25",  # Christmas Day
            f"{current_year}-12-26",  # Boxing Day
        ]
        
        # Add next year's holidays for year-end planning
        next_year = current_year + 1
        holidays.extend([
            f"{next_year}-01-01",
            f"{next_year}-01-26",
            f"{next_year}-04-25",
            f"{next_year}-12-25",
            f"{next_year}-12-26",
        ])
        
        # TODO: Integrate with holiday API for dynamic holiday detection
        # Note: Easter dates and Queen's Birthday change yearly
        
        return holidays
    
    async def _safe_create_default_tasks(self):
        """Safely create default tasks with error handling"""
        try:
            await self._create_default_tasks()
        except Exception as e:
            self.logger.error(f'"error": "default_tasks_creation_failed", "details": "{e}", "action": "scheduler_degraded"')
    
    async def _safe_scheduler_loop(self):
        """Safely run scheduler loop with error handling"""
        try:
            await self._scheduler_loop()
        except Exception as e:
            self.logger.error(f'"error": "scheduler_loop_critical_failure", "details": "{e}", "action": "scheduler_stopped"')
            self.scheduler_running = False
    
    async def _safe_cleanup_loop(self):
        """Background cleanup loop for task history and metrics"""
        while self.scheduler_running:
            try:
                await self._cleanup_task_history()
                await self._cleanup_circuit_breakers()
                await asyncio.sleep(3600)  # Run cleanup every hour
            except Exception as e:
                self.logger.error(f'"error": "cleanup_loop_error", "details": "{e}", "action": "continuing"')
                await asyncio.sleep(3600)
    
    async def _safe_metrics_update_loop(self):
        """Background metrics update loop"""
        while self.scheduler_running:
            try:
                await self._update_scheduler_metrics()
                await asyncio.sleep(300)  # Update metrics every 5 minutes
            except Exception as e:
                self.logger.error(f'"error": "metrics_update_error", "details": "{e}", "action": "continuing"')
                await asyncio.sleep(300)
    
    async def _create_default_tasks(self):
        """Create default trading system tasks"""
        default_tasks = [
            {
                "name": "Morning Market Analysis",
                "task_type": "morning_analysis",
                "schedule_time": "09:30",
                "weekdays": [0, 1, 2, 3, 4],  # Monday-Friday
                "market_phase": "pre_market",
                "service_name": "prediction",
                "method_name": "generate_predictions",
                "parameters": {"symbols": ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX"], "force_refresh": True},
                "priority": 1
            },
            {
                "name": "Market Data Refresh",
                "task_type": "market_data_refresh", 
                "schedule_time": "09:45",
                "weekdays": [0, 1, 2, 3, 4],
                "market_phase": "pre_market",
                "service_name": "market-data",
                "method_name": "refresh_all_data",
                "parameters": {},
                "priority": 2
            },
            {
                "name": "Big 4 Sentiment Analysis",
                "task_type": "sentiment_analysis",
                "schedule_time": "09:50",
                "weekdays": [0, 1, 2, 3, 4],
                "market_phase": "pre_market",
                "service_name": "sentiment",
                "method_name": "get_big4_sentiment",
                "parameters": {},
                "priority": 3
            },
            {
                "name": "Evening Analysis",
                "task_type": "evening_analysis",
                "schedule_time": "17:00",
                "weekdays": [0, 1, 2, 3, 4],
                "market_phase": "post_market",
                "service_name": "prediction",
                "method_name": "generate_predictions",
                "parameters": {"symbols": ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX"], "force_refresh": True},
                "priority": 2
            },
            {
                "name": "Paper Trading Sync",
                "task_type": "paper_trading_sync",
                "schedule_time": "17:30",
                "weekdays": [0, 1, 2, 3, 4],
                "market_phase": "post_market",
                "service_name": "paper-trading",
                "method_name": "sync_positions",
                "parameters": {},
                "priority": 4
            },
            {
                "name": "Daily System Backup",
                "task_type": "system_backup",
                "schedule_time": "02:00",
                "weekdays": [0, 1, 2, 3, 4, 5, 6],  # Every day
                "market_phase": "off_hours",
                "service_name": "backup",
                "method_name": "create_backup",
                "parameters": {"backup_type": "daily"},
                "priority": 7
            },
            {
                "name": "Market Monitoring",
                "task_type": "market_monitoring",
                "schedule_time": "10:15",  # First monitoring after market open
                "weekdays": [0, 1, 2, 3, 4],
                "market_phase": "market_hours",
                "service_name": "market-data",
                "method_name": "get_market_data",
                "parameters": {"symbols": ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX"]},
                "priority": 3,
                "recurring_interval": 15  # Repeat every 15 minutes during market hours
            }
        ]
        
        for task_config in default_tasks:
            await self.schedule_task(**task_config)
    
    async def schedule_task(self, name: str, task_type: str, schedule_time: str, 
                          weekdays: List[int], market_phase: str, service_name: str,
                          method_name: str, parameters: Dict[str, Any], **kwargs):
        """Schedule a new task with comprehensive validation"""
        async with self.task_lock:
            try:
                # Input validation
                if not isinstance(name, str) or len(name.strip()) == 0:
                    return {"error": "Task name must be a non-empty string"}
                
                name = name.strip()
                if len(name) > 100:
                    return {"error": "Task name too long (max 100 characters)"}
                
                # Validate task_type
                if not isinstance(task_type, str) or len(task_type.strip()) == 0:
                    return {"error": "Task type must be a non-empty string"}
                
                # Validate schedule_time format
                if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', schedule_time):
                    return {"error": "schedule_time must be in HH:MM format"}
                
                # Validate weekdays
                if not isinstance(weekdays, list) or not weekdays:
                    return {"error": "weekdays must be a non-empty list"}
                
                for day in weekdays:
                    if not isinstance(day, int) or not 0 <= day <= 6:
                        return {"error": "weekdays must contain integers 0-6 (Monday=0, Sunday=6)"}
                
                # Validate market_phase
                valid_phases = {"pre_market", "market_hours", "post_market", "off_hours"}
                if market_phase not in valid_phases:
                    return {"error": f"market_phase must be one of {valid_phases}"}
                
                # Validate service and method names
                if not isinstance(service_name, str) or len(service_name.strip()) == 0:
                    return {"error": "service_name must be a non-empty string"}
                
                if not isinstance(method_name, str) or len(method_name.strip()) == 0:
                    return {"error": "method_name must be a non-empty string"}
                
                # Sanitize service and method names (alphanumeric, dash, underscore only)
                if not re.match(r'^[a-zA-Z0-9_-]+$', service_name):
                    return {"error": "service_name contains invalid characters"}
                
                if not re.match(r'^[a-zA-Z0-9_]+$', method_name):
                    return {"error": "method_name contains invalid characters"}
                
                # Validate parameters
                if not isinstance(parameters, dict):
                    return {"error": "parameters must be a dictionary"}
                
                # Validate optional parameters
                priority = kwargs.get('priority', 5)
                if not isinstance(priority, int) or not 1 <= priority <= 10:
                    return {"error": "priority must be an integer between 1 and 10"}
                
                timeout_seconds = kwargs.get('timeout_seconds', 300)
                if not isinstance(timeout_seconds, int) or timeout_seconds <= 0 or timeout_seconds > 3600:
                    return {"error": "timeout_seconds must be between 1 and 3600"}
                
                max_retries = kwargs.get('max_retries', 3)
                if not isinstance(max_retries, int) or not 0 <= max_retries <= 10:
                    return {"error": "max_retries must be between 0 and 10"}
                
                # Check for duplicate task names
                existing_names = {task.name for task in self.scheduled_tasks.values()}
                if name in existing_names:
                    return {"error": f"Task with name '{name}' already exists"}
                
                # Generate task ID
                task_id = str(uuid.uuid4())
                
                # Create task with validation
                try:
                    task = ScheduledTask(
                        task_id=task_id,
                        name=name,
                        task_type=task_type.strip(),
                        schedule_time=schedule_time,
                        weekdays=sorted(list(set(weekdays))),  # Remove duplicates and sort
                        market_phase=market_phase,
                        service_name=service_name.strip(),
                        method_name=method_name.strip(),
                        parameters=parameters,
                        created_at=datetime.now().isoformat(),
                        priority=priority,
                        timeout_seconds=timeout_seconds,
                        max_retries=max_retries,
                        **{k: v for k, v in kwargs.items() if k not in ['priority', 'timeout_seconds', 'max_retries']}
                    )
                except ValueError as e:
                    return {"error": f"Task validation failed: {str(e)}"}
                
                # Calculate next run time
                next_run = self._calculate_next_run(task)
                if next_run is None:
                    return {"error": "Unable to calculate next run time - check market_phase and schedule"}
                
                task.next_run = next_run
                
                # Store task
                self.scheduled_tasks[task_id] = task
                
                # Persist to Redis if available
                if self.redis_client:
                    try:
                        self.redis_client.hset("scheduler:tasks", task_id, json.dumps(asdict(task)))
                    except Exception as e:
                        self.logger.warning(f'"task_id": "{task_id}", "error": "{e}", "action": "task_persist_failed"')
                
                self.logger.info(f'"task_id": "{task_id}", "name": "{name}", "next_run": "{task.next_run}", "action": "task_scheduled"')
                
                return {
                    "task_id": task_id,
                    "name": name,
                    "status": "scheduled",
                    "next_run": task.next_run,
                    "market_phase": market_phase,
                    "priority": priority
                }
                
            except Exception as e:
                self.logger.error(f'"name": "{name}", "error": "{e}", "action": "task_schedule_failed"')
                return {"error": f"Internal error: {str(e)}"}
    
    def _calculate_next_run(self, task: ScheduledTask) -> Optional[str]:
        """Calculate next run time for a task with comprehensive validation"""
        try:
            now = datetime.now(self.timezone)
            
            # Parse schedule time with validation
            try:
                hour, minute = map(int, task.schedule_time.split(':'))
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    self.logger.error(f'"task_id": "{task.task_id}", "error": "invalid_time_values", "action": "next_run_calculation_failed"')
                    return None
                schedule_time = time(hour, minute)
            except (ValueError, AttributeError) as e:
                self.logger.error(f'"task_id": "{task.task_id}", "error": "time_parsing_failed", "details": "{e}", "action": "next_run_calculation_failed"')
                return None
            
            # Find next valid run date (check up to 14 days ahead)
            for days_ahead in range(15):
                try:
                    candidate_date = now.date() + timedelta(days=days_ahead)
                    candidate_weekday = candidate_date.weekday()
                    
                    # Check if day is in weekdays list
                    if candidate_weekday not in task.weekdays:
                        continue
                    
                    # Check if it's a market holiday
                    date_str = candidate_date.strftime("%Y-%m-%d")
                    if date_str in self.market_holidays:
                        self.logger.debug(f'"task_id": "{task.task_id}", "date": "{date_str}", "action": "skipping_market_holiday"')
                        continue
                    
                    # Create candidate datetime with timezone awareness
                    try:
                        candidate_datetime = datetime.combine(candidate_date, schedule_time)
                        candidate_datetime = self.timezone.localize(candidate_datetime)
                    except Exception as e:
                        self.logger.error(f'"task_id": "{task.task_id}", "error": "datetime_localization_failed", "details": "{e}"')
                        continue
                    
                    # If it's today, make sure time hasn't passed
                    if days_ahead == 0 and candidate_datetime <= now:
                        continue
                    
                    # Validate market phase timing
                    if self._is_valid_market_phase_time(candidate_datetime, task.market_phase):
                        return candidate_datetime.isoformat()
                    else:
                        self.logger.debug(f'"task_id": "{task.task_id}", "datetime": "{candidate_datetime}", "market_phase": "{task.market_phase}", "action": "invalid_market_phase_time"')
                
                except Exception as e:
                    self.logger.error(f'"task_id": "{task.task_id}", "days_ahead": {days_ahead}, "error": "{e}", "action": "candidate_date_calculation_error"')
                    continue
            
            self.logger.warning(f'"task_id": "{task.task_id}", "action": "no_valid_run_time_found_in_14_days"')
            return None  # No valid run time found in next 14 days
            
        except Exception as e:
            self.logger.error(f'"task_id": "{task.task_id}", "error": "{e}", "action": "next_run_calculation_critical_error"')
            return None
    
    def _is_valid_market_phase_time(self, dt: datetime, market_phase: str) -> bool:
        """Check if datetime is valid for the specified market phase with validation"""
        try:
            time_of_day = dt.time()
            
            if market_phase == "pre_market":
                return (self.market_schedule["pre_market_start"] <= time_of_day < 
                       self.market_schedule["market_open"])
            elif market_phase == "market_hours":
                return (self.market_schedule["market_open"] <= time_of_day < 
                       self.market_schedule["market_close"])
            elif market_phase == "post_market":
                return (self.market_schedule["market_close"] <= time_of_day < 
                       self.market_schedule["post_market_end"])
            elif market_phase == "off_hours":
                return (time_of_day >= self.market_schedule["post_market_end"] or 
                       time_of_day < self.market_schedule["pre_market_start"])
            else:
                self.logger.warning(f'"market_phase": "{market_phase}", "action": "unknown_market_phase"')
                return True  # Default allow for unknown phases
                
        except Exception as e:
            self.logger.error(f'"datetime": "{dt}", "market_phase": "{market_phase}", "error": "{e}", "action": "market_phase_validation_error"')
            return False
    
    async def _scheduler_loop(self):
        """Main scheduler loop with enhanced error handling and circuit breaker"""
        self.logger.info(f'"action": "scheduler_loop_started"')
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.scheduler_running:
            loop_start_time = datetime.now()
            
            try:
                if not self.scheduler_paused:
                    # Check if we're not hitting the concurrent task limit
                    if len(self.running_tasks) >= self.max_concurrent_tasks:
                        self.logger.warning(f'"running_tasks": {len(self.running_tasks)}, "max_concurrent": {self.max_concurrent_tasks}, "action": "task_limit_reached"')
                    else:
                        await self._check_and_execute_tasks()
                
                consecutive_errors = 0  # Reset error counter on success
                
                # Variable sleep based on market phase
                sleep_duration = self._get_optimal_sleep_duration()
                await asyncio.sleep(sleep_duration)
                
            except Exception as e:
                consecutive_errors += 1
                self.logger.error(f'"error": "{e}", "consecutive_errors": {consecutive_errors}, "action": "scheduler_loop_error"')
                
                if consecutive_errors >= max_consecutive_errors:
                    self.logger.critical(f'"consecutive_errors": {consecutive_errors}, "action": "scheduler_loop_paused_due_to_errors"')
                    self.scheduler_paused = True
                    
                    # Publish critical alert
                    self.publish_event("scheduler_critical_error", {
                        "consecutive_errors": consecutive_errors,
                        "last_error": str(e),
                        "scheduler_paused": True
                    }, priority="urgent")
                
                # Exponential backoff for errors
                error_sleep = min(300, 30 * (2 ** min(consecutive_errors - 1, 3)))
                await asyncio.sleep(error_sleep)
    
    def _get_optimal_sleep_duration(self) -> int:
        """Get optimal sleep duration based on current market phase"""
        try:
            now = datetime.now(self.timezone)
            current_time = now.time()
            
            # More frequent checks during market hours
            if (self.market_schedule["market_open"] <= current_time <= 
                self.market_schedule["market_close"]):
                return 30  # 30 seconds during market hours
            elif (self.market_schedule["pre_market_start"] <= current_time < 
                  self.market_schedule["market_open"]):
                return 45  # 45 seconds pre-market
            elif (self.market_schedule["market_close"] < current_time <= 
                  self.market_schedule["post_market_end"]):
                return 45  # 45 seconds post-market
            else:
                return 60  # 60 seconds off-hours
                
        except Exception:
            return 60  # Default fallback
    
    async def _check_and_execute_tasks(self):
        """Check for tasks that need to be executed with enhanced safety"""
        now = datetime.now(self.timezone)
        tasks_to_execute = []
        
        async with self.task_lock:
            for task_id, task in self.scheduled_tasks.items():
                if not task.enabled:
                    continue
                
                if not task.next_run:
                    continue
                
                # Skip tasks in circuit breaker state
                if self._is_circuit_breaker_open(task.service_name):
                    continue
                
                # Check if task is due
                try:
                    next_run_dt = datetime.fromisoformat(task.next_run)
                    # Add small buffer (30 seconds) to account for scheduling precision
                    if next_run_dt <= now + timedelta(seconds=30):
                        tasks_to_execute.append((task_id, task))
                except (ValueError, TypeError) as e:
                    self.logger.error(f'"task_id": "{task_id}", "error": "invalid_next_run_time", "details": "{e}", "action": "task_skip"')
                    # Try to recalculate next run time
                    task.next_run = self._calculate_next_run(task)
        
        # Sort by priority (lower number = higher priority)
        tasks_to_execute.sort(key=lambda x: (x[1].priority, x[1].next_run))
        
        # Execute tasks with concurrency control
        for task_id, task in tasks_to_execute:
            if len(self.running_tasks) >= self.max_concurrent_tasks:
                self.logger.warning(f'"task_id": "{task_id}", "action": "task_delayed_due_to_concurrency_limit"')
                break
            
            if task_id not in self.running_tasks:
                self.logger.info(f'"task_id": "{task_id}", "name": "{task.name}", "priority": {task.priority}, "action": "task_execution_started"')
                
                # Create async task for execution
                execution_task = asyncio.create_task(self._execute_task_async(task_id, task))
                self.running_tasks[task_id] = execution_task
    
    def _is_circuit_breaker_open(self, service_name: str) -> bool:
        """Check if circuit breaker is open for a service"""
        if service_name not in self.circuit_breaker_failures:
            return False
        
        failure_data = self.circuit_breaker_failures[service_name]
        
        # Check if circuit breaker should reset
        if (datetime.now().timestamp() - failure_data["last_failure"] > 
            self.circuit_breaker_reset_time):
            del self.circuit_breaker_failures[service_name]
            return False
        
        return failure_data["failure_count"] >= self.circuit_breaker_threshold
    
    def _record_service_failure(self, service_name: str):
        """Record a service failure for circuit breaker logic"""
        now = datetime.now().timestamp()
        
        if service_name in self.circuit_breaker_failures:
            self.circuit_breaker_failures[service_name]["failure_count"] += 1
            self.circuit_breaker_failures[service_name]["last_failure"] = now
        else:
            self.circuit_breaker_failures[service_name] = {
                "failure_count": 1,
                "last_failure": now
            }
        
        if self.circuit_breaker_failures[service_name]["failure_count"] >= self.circuit_breaker_threshold:
            self.logger.warning(f'"service": "{service_name}", "failure_count": {self.circuit_breaker_failures[service_name]["failure_count"]}, "action": "circuit_breaker_opened"')
            
            self.publish_event("circuit_breaker_opened", {
                "service_name": service_name,
                "failure_count": self.circuit_breaker_failures[service_name]["failure_count"]
            }, priority="high")
    
    async def _execute_task_async(self, task_id: str, task: ScheduledTask):
        """Execute a task asynchronously"""
        execution_start = datetime.now()
        
        try:
            # Call the service method
            result = await asyncio.wait_for(
                self.call_service(task.service_name, task.method_name, **task.parameters),
                timeout=task.timeout_seconds
            )
            
            execution_time = (datetime.now() - execution_start).total_seconds()
            
            # Update task state
            task.last_run = execution_start.isoformat()
            task.last_result = "success"
            task.retry_count = 0
            
            # Calculate next run for recurring tasks
            if hasattr(task, 'recurring_interval') and getattr(task, 'recurring_interval'):
                # For recurring tasks during market hours
                if task.market_phase == "market_hours":
                    next_run_time = execution_start + timedelta(minutes=getattr(task, 'recurring_interval'))
                    if next_run_time.time() < self.market_schedule["market_close"]:
                        task.next_run = next_run_time.isoformat()
                    else:
                        # Schedule for next trading day
                        task.next_run = self._calculate_next_run(task)
                else:
                    task.next_run = self._calculate_next_run(task)
            else:
                task.next_run = self._calculate_next_run(task)
            
            # Log successful execution
            self.logger.info(f'"task_id": "{task_id}", "name": "{task.name}", "execution_time": {execution_time:.2f}, "action": "task_completed"')
            
            # Publish success event
            self.publish_event("task_completed", {
                "task_id": task_id,
                "task_name": task.name,
                "execution_time": execution_time,
                "result": "success"
            })
            
            # Add to history
            self.task_history.append({
                "task_id": task_id,
                "name": task.name,
                "executed_at": execution_start.isoformat(),
                "execution_time": execution_time,
                "result": "success",
                "details": str(result)[:500]  # Truncate large results
            })
            
        except asyncio.TimeoutError:
            await self._handle_task_failure(task_id, task, "timeout", execution_start)
        except Exception as e:
            await self._handle_task_failure(task_id, task, str(e), execution_start)
        finally:
            # Remove from running tasks
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
    
    async def _handle_task_failure(self, task_id: str, task: ScheduledTask, error: str, execution_start: datetime):
        """Handle task execution failure with retry logic"""
        execution_time = (datetime.now() - execution_start).total_seconds()
        task.retry_count += 1
        
        if task.retry_count <= task.max_retries:
            # Schedule retry with exponential backoff
            retry_delay = min(300, 30 * (2 ** (task.retry_count - 1)))  # Max 5 minutes
            retry_time = datetime.now() + timedelta(seconds=retry_delay)
            task.next_run = retry_time.isoformat()
            
            self.logger.warning(f'"task_id": "{task_id}", "error": "{error}", "retry_count": {task.retry_count}, "retry_in": {retry_delay}, "action": "task_retry_scheduled"')
        else:
            # Max retries exceeded
            task.last_result = f"failed_after_{task.max_retries}_retries"
            task.next_run = self._calculate_next_run(task)  # Schedule for next regular time
            task.retry_count = 0
            
            self.logger.error(f'"task_id": "{task_id}", "error": "{error}", "action": "task_failed_max_retries"')
            
            # Publish failure event
            self.publish_event("task_failed", {
                "task_id": task_id,
                "task_name": task.name,
                "error": error,
                "retry_count": task.max_retries
            }, priority="high")
        
        # Add to history
        self.task_history.append({
            "task_id": task_id,
            "name": task.name,
            "executed_at": execution_start.isoformat(),
            "execution_time": execution_time,
            "result": "failed",
            "error": error,
            "retry_count": task.retry_count
        })
    
    async def cancel_task(self, task_id: str):
        """Cancel a scheduled task"""
        if task_id in self.scheduled_tasks:
            # Cancel running task if active
            if task_id in self.running_tasks:
                self.running_tasks[task_id].cancel()
                del self.running_tasks[task_id]
            
            # Remove from schedule
            task_name = self.scheduled_tasks[task_id].name
            del self.scheduled_tasks[task_id]
            
            # Remove from Redis
            if self.redis_client:
                try:
                    self.redis_client.hdel("scheduler:tasks", task_id)
                except Exception:
                    pass
            
            self.logger.info(f'"task_id": "{task_id}", "name": "{task_name}", "action": "task_cancelled"')
            
            return {"status": "cancelled", "task_id": task_id}
        else:
            return {"error": "Task not found", "task_id": task_id}
    
    async def list_tasks(self, status_filter: str = None):
        """List all scheduled tasks"""
        tasks_list = []
        
        for task_id, task in self.scheduled_tasks.items():
            task_info = {
                "task_id": task_id,
                "name": task.name,
                "task_type": task.task_type,
                "schedule_time": task.schedule_time,
                "market_phase": task.market_phase,
                "enabled": task.enabled,
                "next_run": task.next_run,
                "last_run": task.last_run,
                "last_result": task.last_result,
                "priority": task.priority,
                "running": task_id in self.running_tasks
            }
            
            if status_filter:
                if status_filter == "running" and not task_info["running"]:
                    continue
                elif status_filter == "scheduled" and task_info["running"]:
                    continue
                elif status_filter == "failed" and task.last_result != "failed":
                    continue
            
            tasks_list.append(task_info)
        
        # Sort by next run time
        tasks_list.sort(key=lambda x: x["next_run"] or "9999-12-31")
        
        return {
            "total_tasks": len(tasks_list),
            "running_tasks": len(self.running_tasks),
            "tasks": tasks_list
        }
    
    async def execute_task(self, task_id: str, force: bool = False):
        """Manually execute a task"""
        if task_id not in self.scheduled_tasks:
            return {"error": "Task not found", "task_id": task_id}
        
        if task_id in self.running_tasks and not force:
            return {"error": "Task already running", "task_id": task_id}
        
        task = self.scheduled_tasks[task_id]
        
        self.logger.info(f'"task_id": "{task_id}", "name": "{task.name}", "action": "manual_task_execution"')
        
        # Execute task immediately
        execution_task = asyncio.create_task(self._execute_task_async(task_id, task))
        self.running_tasks[task_id] = execution_task
        
        return {"status": "executing", "task_id": task_id, "task_name": task.name}
    
    async def get_task_status(self, task_id: str):
        """Get detailed status of a specific task"""
        if task_id not in self.scheduled_tasks:
            return {"error": "Task not found", "task_id": task_id}
        
        task = self.scheduled_tasks[task_id]
        
        # Get recent history for this task
        recent_history = [h for h in self.task_history if h["task_id"] == task_id][-5:]
        
        return {
            "task_id": task_id,
            "name": task.name,
            "task_type": task.task_type,
            "enabled": task.enabled,
            "running": task_id in self.running_tasks,
            "next_run": task.next_run,
            "last_run": task.last_run,
            "last_result": task.last_result,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "priority": task.priority,
            "recent_history": recent_history
        }
    
    async def set_market_schedule(self, config: Dict[str, Any]):
        """Update market schedule configuration"""
        try:
            if "market_open" in config:
                hour, minute = map(int, config["market_open"].split(':'))
                self.market_schedule["market_open"] = time(hour, minute)
            
            if "market_close" in config:
                hour, minute = map(int, config["market_close"].split(':'))
                self.market_schedule["market_close"] = time(hour, minute)
            
            if "trading_days" in config:
                self.market_schedule["trading_days"] = config["trading_days"]
            
            # Recalculate next run times for all tasks
            for task in self.scheduled_tasks.values():
                task.next_run = self._calculate_next_run(task)
            
            self.logger.info(f'"action": "market_schedule_updated", "config": {config}')
            
            return {"status": "updated", "market_schedule": {
                "market_open": self.market_schedule["market_open"].strftime("%H:%M"),
                "market_close": self.market_schedule["market_close"].strftime("%H:%M"),
                "trading_days": self.market_schedule["trading_days"]
            }}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def get_market_status(self):
        """Get current market status"""
        now = datetime.now(self.timezone)
        current_time = now.time()
        current_weekday = now.weekday()
        current_date = now.date().strftime("%Y-%m-%d")
        
        # Determine market phase
        if current_weekday not in self.market_schedule["trading_days"]:
            market_phase = "weekend"
        elif current_date in self.market_holidays:
            market_phase = "holiday"
        elif current_time < self.market_schedule["pre_market_start"]:
            market_phase = "off_hours"
        elif current_time < self.market_schedule["market_open"]:
            market_phase = "pre_market"
        elif current_time < self.market_schedule["market_close"]:
            market_phase = "market_hours"
        elif current_time < self.market_schedule["post_market_end"]:
            market_phase = "post_market"
        else:
            market_phase = "off_hours"
        
        # Calculate next market event
        next_event = None
        next_event_time = None
        
        if market_phase == "pre_market":
            next_event = "market_open"
            next_event_time = datetime.combine(now.date(), self.market_schedule["market_open"])
        elif market_phase == "market_hours":
            next_event = "market_close"
            next_event_time = datetime.combine(now.date(), self.market_schedule["market_close"])
        
        return {
            "current_time": now.isoformat(),
            "market_phase": market_phase,
            "is_trading_day": current_weekday in self.market_schedule["trading_days"],
            "is_holiday": current_date in self.market_holidays,
            "next_event": next_event,
            "next_event_time": next_event_time.isoformat() if next_event_time else None,
            "market_schedule": {
                "open": self.market_schedule["market_open"].strftime("%H:%M"),
                "close": self.market_schedule["market_close"].strftime("%H:%M")
            }
        }
    
    async def pause_scheduler(self):
        """Pause task execution"""
        self.scheduler_paused = True
        self.logger.info(f'"action": "scheduler_paused"')
        return {"status": "paused"}
    
    async def resume_scheduler(self):
        """Resume task execution"""
        self.scheduler_paused = False
        self.logger.info(f'"action": "scheduler_resumed"')
        return {"status": "resumed"}
    
    async def health_check(self):
        """Enhanced health check with scheduler metrics"""
        base_health = await super().health_check()
        
        # Add scheduler-specific health metrics
        scheduler_health = {
            **base_health,
            "scheduler_running": self.scheduler_running,
            "scheduler_paused": self.scheduler_paused,
            "total_scheduled_tasks": len(self.scheduled_tasks),
            "running_tasks": len(self.running_tasks),
            "enabled_tasks": sum(1 for t in self.scheduled_tasks.values() if t.enabled),
            "task_history_size": len(self.task_history),
            "market_status": await self.get_market_status()
        }
        
        # Check for task failures
        recent_failures = [h for h in self.task_history[-10:] if h.get("result") == "failed"]
        if len(recent_failures) > 5:
            scheduler_health["status"] = "degraded"
            scheduler_health["warning"] = f"High failure rate: {len(recent_failures)} failures in last 10 executions"
        
        return scheduler_health
    
    async def get_scheduler_metrics(self):
        """Get comprehensive scheduler performance metrics"""
        uptime = (datetime.now() - self.scheduler_start_time).total_seconds()
        
        # Calculate success rate
        success_rate = 0
        if self.total_executions > 0:
            success_rate = ((self.total_executions - self.total_failures) / self.total_executions) * 100
        
        # Task distribution by market phase
        phase_distribution = {"pre_market": 0, "market_hours": 0, "post_market": 0, "off_hours": 0}
        for task in self.scheduled_tasks.values():
            if task.market_phase in phase_distribution:
                phase_distribution[task.market_phase] += 1
        
        # Service distribution
        service_distribution = {}
        for task in self.scheduled_tasks.values():
            service_distribution[task.service_name] = service_distribution.get(task.service_name, 0) + 1
        
        return {
            "uptime_seconds": round(uptime, 2),
            "total_scheduled_tasks": len(self.scheduled_tasks),
            "running_tasks": len(self.running_tasks),
            "enabled_tasks": sum(1 for t in self.scheduled_tasks.values() if t.enabled),
            "total_executions": self.total_executions,
            "total_failures": self.total_failures,
            "total_timeouts": self.total_timeouts,
            "success_rate": round(success_rate, 2),
            "average_execution_time": round(self.average_execution_time, 2),
            "task_history_size": len(self.task_history),
            "scheduler_paused": self.scheduler_paused,
            "circuit_breaker_active_services": list(self.circuit_breaker_failures.keys()),
            "phase_distribution": phase_distribution,
            "service_distribution": service_distribution,
            "last_cleanup": self.last_cleanup_time.isoformat()
        }
    
    async def cleanup_tasks(self, older_than_hours: int = 168):  # Default 7 days
        """Clean up old task history and completed tasks"""
        if not isinstance(older_than_hours, int) or older_than_hours <= 0:
            return {"error": "older_than_hours must be a positive integer"}
        
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        # Clean up task history
        original_history_size = len(self.task_history)
        self.task_history = [
            h for h in self.task_history
            if datetime.fromisoformat(h["executed_at"]) > cutoff_time
        ]
        
        cleaned_history = original_history_size - len(self.task_history)
        
        # Clean up disabled tasks that haven't run recently
        disabled_tasks_removed = 0
        tasks_to_remove = []
        
        for task_id, task in self.scheduled_tasks.items():
            if (not task.enabled and 
                task.last_run and 
                datetime.fromisoformat(task.last_run) < cutoff_time):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.scheduled_tasks[task_id]
            disabled_tasks_removed += 1
            
            # Remove from Redis
            if self.redis_client:
                try:
                    self.redis_client.hdel("scheduler:tasks", task_id)
                except Exception:
                    pass
        
        self.last_cleanup_time = datetime.now()
        
        self.logger.info(f'"cleaned_history": {cleaned_history}, "removed_disabled_tasks": {disabled_tasks_removed}, "action": "cleanup_completed"')
        
        return {
            "cleaned_history_entries": cleaned_history,
            "removed_disabled_tasks": disabled_tasks_removed,
            "current_history_size": len(self.task_history),
            "current_task_count": len(self.scheduled_tasks)
        }
    
    async def validate_task_config(self, task_config: dict):
        """Validate a task configuration without scheduling it"""
        required_fields = ["name", "task_type", "schedule_time", "weekdays", "market_phase", "service_name", "method_name", "parameters"]
        
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check required fields
        for field in required_fields:
            if field not in task_config:
                validation_results["errors"].append(f"Missing required field: {field}")
                validation_results["valid"] = False
        
        if not validation_results["valid"]:
            return validation_results
        
        # Validate individual fields
        try:
            # Name validation
            name = task_config["name"]
            if not isinstance(name, str) or len(name.strip()) == 0:
                validation_results["errors"].append("name must be a non-empty string")
            elif len(name) > 100:
                validation_results["errors"].append("name too long (max 100 characters)")
            
            # Schedule time validation
            schedule_time = task_config["schedule_time"]
            if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', schedule_time):
                validation_results["errors"].append("schedule_time must be in HH:MM format")
            
            # Weekdays validation
            weekdays = task_config["weekdays"]
            if not isinstance(weekdays, list) or not weekdays:
                validation_results["errors"].append("weekdays must be a non-empty list")
            else:
                for day in weekdays:
                    if not isinstance(day, int) or not 0 <= day <= 6:
                        validation_results["errors"].append("weekdays must contain integers 0-6")
                        break
            
            # Market phase validation
            market_phase = task_config["market_phase"]
            valid_phases = {"pre_market", "market_hours", "post_market", "off_hours"}
            if market_phase not in valid_phases:
                validation_results["errors"].append(f"market_phase must be one of {valid_phases}")
            
            # Service name validation
            service_name = task_config["service_name"]
            if not re.match(r'^[a-zA-Z0-9_-]+$', service_name):
                validation_results["errors"].append("service_name contains invalid characters")
            
            # Method name validation
            method_name = task_config["method_name"]
            if not re.match(r'^[a-zA-Z0-9_]+$', method_name):
                validation_results["errors"].append("method_name contains invalid characters")
            
            # Parameters validation
            parameters = task_config["parameters"]
            if not isinstance(parameters, dict):
                validation_results["errors"].append("parameters must be a dictionary")
            
            # Optional field validations
            if "priority" in task_config:
                priority = task_config["priority"]
                if not isinstance(priority, int) or not 1 <= priority <= 10:
                    validation_results["errors"].append("priority must be an integer between 1 and 10")
            
            if "timeout_seconds" in task_config:
                timeout = task_config["timeout_seconds"]
                if not isinstance(timeout, int) or timeout <= 0 or timeout > 3600:
                    validation_results["errors"].append("timeout_seconds must be between 1 and 3600")
            
        except Exception as e:
            validation_results["errors"].append(f"Validation error: {str(e)}")
        
        # Add warnings for potential issues
        if validation_results["valid"]:
            # Check for potentially problematic configurations
            if task_config.get("timeout_seconds", 300) > 1800:  # 30 minutes
                validation_results["warnings"].append("Long timeout may block other tasks")
            
            if len(task_config.get("weekdays", [])) == 7:
                validation_results["warnings"].append("Task scheduled for all days including weekends")
        
        validation_results["valid"] = len(validation_results["errors"]) == 0
        
        return validation_results
    
    async def _cleanup_task_history(self):
        """Internal cleanup for task history"""
        if len(self.task_history) > 10000:  # Keep last 10,000 entries
            self.task_history = self.task_history[-10000:]
            self.logger.info(f'"action": "task_history_trimmed", "remaining_entries": {len(self.task_history)}')
    
    async def _cleanup_circuit_breakers(self):
        """Clean up expired circuit breaker entries"""
        now = datetime.now().timestamp()
        expired_services = []
        
        for service_name, failure_data in self.circuit_breaker_failures.items():
            if now - failure_data["last_failure"] > self.circuit_breaker_reset_time:
                expired_services.append(service_name)
        
        for service_name in expired_services:
            del self.circuit_breaker_failures[service_name]
            self.logger.info(f'"service": "{service_name}", "action": "circuit_breaker_reset"')
    
    async def _update_scheduler_metrics(self):
        """Update scheduler performance metrics"""
        # Calculate average execution time from recent history
        recent_executions = [
            h for h in self.task_history[-100:]  # Last 100 executions
            if h.get("execution_time") and h.get("result") == "success"
        ]
        
        if recent_executions:
            total_time = sum(h["execution_time"] for h in recent_executions)
            self.average_execution_time = total_time / len(recent_executions)

async def main():
    service = SchedulerService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
