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

class SchedulerService(BaseService):
    """Market-aware task scheduler for trading system"""
    
    def __init__(self):
        super().__init__("scheduler")
        
        # Australian Eastern Time
        self.timezone = pytz.timezone('Australia/Sydney')
        
        # Market schedule configuration
        self.market_schedule = {
            "market_open": time(10, 0),    # 10:00 AM
            "market_close": time(16, 0),   # 4:00 PM
            "pre_market_start": time(8, 0), # 8:00 AM
            "post_market_end": time(18, 0), # 6:00 PM
            "trading_days": [0, 1, 2, 3, 4]  # Monday-Friday
        }
        
        # Task storage
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_history: List[Dict] = []
        
        # Market holidays (simplified - would integrate with holiday API)
        self.market_holidays = [
            "2024-01-01",  # New Year's Day
            "2024-01-26",  # Australia Day
            "2024-03-29",  # Good Friday
            "2024-04-01",  # Easter Monday
            "2024-04-25",  # ANZAC Day
            "2024-06-10",  # Queen's Birthday
            "2024-12-25",  # Christmas Day
            "2024-12-26",  # Boxing Day
        ]
        
        # Register methods
        self.register_handler("schedule_task", self.schedule_task)
        self.register_handler("cancel_task", self.cancel_task)
        self.register_handler("list_tasks", self.list_tasks)
        self.register_handler("execute_task", self.execute_task)
        self.register_handler("get_task_status", self.get_task_status)
        self.register_handler("set_market_schedule", self.set_market_schedule)
        self.register_handler("get_market_status", self.get_market_status)
        self.register_handler("pause_scheduler", self.pause_scheduler)
        self.register_handler("resume_scheduler", self.resume_scheduler)
        
        # Scheduler state
        self.scheduler_running = True
        self.scheduler_paused = False
        
        # Create default tasks
        asyncio.create_task(self._create_default_tasks())
        
        # Start scheduler loop
        asyncio.create_task(self._scheduler_loop())
    
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
        """Schedule a new task"""
        try:
            task_id = str(uuid.uuid4())
            
            task = ScheduledTask(
                task_id=task_id,
                name=name,
                task_type=task_type,
                schedule_time=schedule_time,
                weekdays=weekdays,
                market_phase=market_phase,
                service_name=service_name,
                method_name=method_name,
                parameters=parameters,
                created_at=datetime.now().isoformat(),
                **kwargs
            )
            
            # Calculate next run time
            task.next_run = self._calculate_next_run(task)
            
            self.scheduled_tasks[task_id] = task
            
            # Persist to Redis if available
            if self.redis_client:
                try:
                    self.redis_client.hset("scheduler:tasks", task_id, json.dumps(asdict(task)))
                except Exception as e:
                    self.logger.error(f'"task_id": "{task_id}", "error": "{e}", "action": "task_persist_failed"')
            
            self.logger.info(f'"task_id": "{task_id}", "name": "{name}", "next_run": "{task.next_run}", "action": "task_scheduled"')
            
            return {
                "task_id": task_id,
                "name": name,
                "status": "scheduled",
                "next_run": task.next_run
            }
            
        except Exception as e:
            self.logger.error(f'"name": "{name}", "error": "{e}", "action": "task_schedule_failed"')
            return {"error": str(e)}
    
    def _calculate_next_run(self, task: ScheduledTask) -> str:
        """Calculate next run time for a task"""
        now = datetime.now(self.timezone)
        
        # Parse schedule time
        try:
            hour, minute = map(int, task.schedule_time.split(':'))
            schedule_time = time(hour, minute)
        except ValueError:
            return None
        
        # Find next valid run date
        for days_ahead in range(8):  # Check next 7 days
            candidate_date = now.date() + timedelta(days=days_ahead)
            candidate_weekday = candidate_date.weekday()
            
            # Check if day is in weekdays list
            if candidate_weekday not in task.weekdays:
                continue
            
            # Check if it's a market holiday
            if candidate_date.strftime("%Y-%m-%d") in self.market_holidays:
                continue
            
            # Create candidate datetime
            candidate_datetime = datetime.combine(candidate_date, schedule_time)
            candidate_datetime = self.timezone.localize(candidate_datetime)
            
            # If it's today, make sure time hasn't passed
            if days_ahead == 0 and candidate_datetime <= now:
                continue
            
            # Validate market phase timing
            if self._is_valid_market_phase_time(candidate_datetime, task.market_phase):
                return candidate_datetime.isoformat()
        
        return None  # No valid run time found in next 7 days
    
    def _is_valid_market_phase_time(self, dt: datetime, market_phase: str) -> bool:
        """Check if datetime is valid for the specified market phase"""
        time_of_day = dt.time()
        
        if market_phase == "pre_market":
            return self.market_schedule["pre_market_start"] <= time_of_day < self.market_schedule["market_open"]
        elif market_phase == "market_hours":
            return self.market_schedule["market_open"] <= time_of_day < self.market_schedule["market_close"]
        elif market_phase == "post_market":
            return self.market_schedule["market_close"] <= time_of_day < self.market_schedule["post_market_end"]
        elif market_phase == "off_hours":
            return (time_of_day >= self.market_schedule["post_market_end"] or 
                   time_of_day < self.market_schedule["pre_market_start"])
        
        return True  # Default allow
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        self.logger.info(f'"action": "scheduler_loop_started"')
        
        while self.scheduler_running:
            try:
                if not self.scheduler_paused:
                    await self._check_and_execute_tasks()
                
                # Sleep for 60 seconds before next check
                await asyncio.sleep(60)
                
            except Exception as e:
                self.logger.error(f'"error": "{e}", "action": "scheduler_loop_error"')
                await asyncio.sleep(60)
    
    async def _check_and_execute_tasks(self):
        """Check for tasks that need to be executed"""
        now = datetime.now(self.timezone)
        current_time_str = now.isoformat()
        
        tasks_to_execute = []
        
        for task_id, task in self.scheduled_tasks.items():
            if not task.enabled:
                continue
            
            if not task.next_run:
                continue
            
            # Check if task is due
            try:
                next_run_dt = datetime.fromisoformat(task.next_run)
                if next_run_dt <= now:
                    tasks_to_execute.append((task_id, task))
            except ValueError:
                self.logger.error(f'"task_id": "{task_id}", "error": "invalid_next_run_time", "action": "task_skip"')
        
        # Sort by priority (lower number = higher priority)
        tasks_to_execute.sort(key=lambda x: x[1].priority)
        
        # Execute tasks
        for task_id, task in tasks_to_execute:
            if task_id not in self.running_tasks:
                self.logger.info(f'"task_id": "{task_id}", "name": "{task.name}", "action": "task_execution_started"')
                
                # Create async task for execution
                execution_task = asyncio.create_task(self._execute_task_async(task_id, task))
                self.running_tasks[task_id] = execution_task
    
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

async def main():
    service = SchedulerService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
