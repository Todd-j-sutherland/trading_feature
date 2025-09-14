#!/usr/bin/env python3
"""
Trading Microservices Manager

Purpose:
This script provides comprehensive management for all trading microservices,
including starting, stopping, monitoring, and health checking all services.
It handles service dependencies and provides a centralized control interface.

Key Features:
- Service dependency management and ordered startup
- Health monitoring and status reporting
- Log aggregation and error tracking
- Performance metrics collection
- Service restart and recovery
- Configuration management

Services Managed:
- Base services: Redis (external dependency)
- Core services: market-data, sentiment, ml-model
- Processing services: prediction, scheduler
- Trading services: paper-trading
- Support services: monitoring, backup (future)

Usage:
python services/management/service_manager.py start
python services/management/service_manager.py stop
python services/management/service_manager.py status
python services/management/service_manager.py health
python services/management/service_manager.py restart [service_name]
python services/management/service_manager.py logs [service_name]

Dependencies:
- Python asyncio for async service calls
- Unix socket communication between services
- Redis for inter-service messaging
- Service files in their respective directories

Integration:
- Integrates with all microservices via Unix sockets
- Provides health dashboard functionality
- Manages service lifecycle and dependencies
"""

import asyncio
import sys
import os
import json
import signal
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess

# Add base service to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.base_service import BaseService

class ServiceManager:
    """Comprehensive manager for all trading microservices"""
    
    def __init__(self):
        self.services_config = {
            "market-data": {
                "path": "services/market-data/market_data_service.py",
                "dependencies": [],
                "critical": True,
                "startup_delay": 2
            },
            "sentiment": {
                "path": "services/sentiment/sentiment_service.py", 
                "dependencies": [],
                "critical": True,
                "startup_delay": 2
            },
            "ml-model": {
                "path": "services/ml-model/ml_model_service.py",
                "dependencies": [],
                "critical": True,
                "startup_delay": 3
            },
            "prediction": {
                "path": "services/prediction/prediction_service.py",
                "dependencies": ["market-data", "sentiment", "ml-model"],
                "critical": True,
                "startup_delay": 5
            },
            "scheduler": {
                "path": "services/scheduler/scheduler_service.py",
                "dependencies": ["prediction"],
                "critical": True,
                "startup_delay": 3
            },
            "paper-trading": {
                "path": "services/paper-trading/paper_trading_service.py",
                "dependencies": ["prediction", "market-data"],
                "critical": False,
                "startup_delay": 4
            }
        }
        
        # Service process tracking
        self.running_processes = {}
        self.service_health = {}
        self.startup_order = []
        
        # Calculate startup order based on dependencies
        self._calculate_startup_order()
        
        # Base service for communication
        self.base_service = None
    
    def _calculate_startup_order(self):
        """Calculate service startup order based on dependencies"""
        visited = set()
        temp_visited = set()
        self.startup_order = []
        
        def visit(service_name):
            if service_name in temp_visited:
                raise Exception(f"Circular dependency detected involving {service_name}")
            if service_name in visited:
                return
            
            temp_visited.add(service_name)
            
            # Visit dependencies first
            for dependency in self.services_config[service_name]["dependencies"]:
                if dependency in self.services_config:
                    visit(dependency)
            
            temp_visited.remove(service_name)
            visited.add(service_name)
            self.startup_order.append(service_name)
        
        # Visit all services
        for service_name in self.services_config.keys():
            if service_name not in visited:
                visit(service_name)
        
        print(f"Service startup order: {' -> '.join(self.startup_order)}")
    
    async def start_services(self, services: List[str] = None):
        """Start services in dependency order"""
        if services is None:
            services_to_start = self.startup_order
        else:
            # Filter requested services but maintain order
            services_to_start = [s for s in self.startup_order if s in services]
        
        print(f"Starting services: {', '.join(services_to_start)}")
        
        for service_name in services_to_start:
            try:
                await self._start_single_service(service_name)
                
                # Wait for startup delay
                startup_delay = self.services_config[service_name]["startup_delay"]
                print(f"Waiting {startup_delay}s for {service_name} to initialize...")
                await asyncio.sleep(startup_delay)
                
                # Verify service started
                if await self._verify_service_running(service_name):
                    print(f"✅ {service_name} started successfully")
                else:
                    print(f"❌ {service_name} failed to start properly")
                    
            except Exception as e:
                print(f"❌ Failed to start {service_name}: {e}")
                
                # Stop already started services if this is critical
                if self.services_config[service_name]["critical"]:
                    print("Critical service failed, stopping all services...")
                    await self.stop_services()
                    return False
        
        print("🚀 All requested services started")
        return True
    
    async def _start_single_service(self, service_name: str):
        """Start a single service"""
        if service_name in self.running_processes:
            print(f"⚠️  {service_name} is already running")
            return
        
        service_config = self.services_config[service_name]
        service_path = service_config["path"]
        
        # Check if service file exists
        if not os.path.exists(service_path):
            raise Exception(f"Service file not found: {service_path}")
        
        print(f"🚀 Starting {service_name}...")
        
        # Start the service process
        process = subprocess.Popen(
            [sys.executable, service_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        self.running_processes[service_name] = process
        
        # Give process a moment to start
        await asyncio.sleep(1)
        
        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            raise Exception(f"Service died immediately. Error: {stderr}")
    
    async def _verify_service_running(self, service_name: str) -> bool:
        """Verify service is running and responding"""
        max_attempts = 10
        
        for attempt in range(max_attempts):
            try:
                # Initialize base service for communication if not done
                if not self.base_service:
                    self.base_service = BaseService("manager")
                
                # Try to call service health endpoint
                result = await self.base_service.call_service(service_name, "health", timeout=5.0)
                
                if result and result.get("service") == service_name:
                    return True
                    
            except Exception as e:
                # Service might still be starting up
                if attempt < max_attempts - 1:
                    await asyncio.sleep(1)
                    continue
                else:
                    print(f"⚠️  {service_name} not responding after {max_attempts} attempts: {e}")
                    return False
        
        return False
    
    async def stop_services(self, services: List[str] = None):
        """Stop services in reverse dependency order"""
        if services is None:
            services_to_stop = list(reversed(self.startup_order))
        else:
            # Filter requested services but maintain reverse order
            services_to_stop = [s for s in reversed(self.startup_order) if s in services]
        
        print(f"Stopping services: {', '.join(services_to_stop)}")
        
        for service_name in services_to_stop:
            await self._stop_single_service(service_name)
        
        print("🛑 All requested services stopped")
    
    async def _stop_single_service(self, service_name: str):
        """Stop a single service"""
        if service_name not in self.running_processes:
            print(f"⚠️  {service_name} is not running")
            return
        
        process = self.running_processes[service_name]
        
        try:
            print(f"🛑 Stopping {service_name}...")
            
            # Try graceful shutdown first
            if self.base_service:
                try:
                    await self.base_service.call_service(service_name, "graceful_shutdown", timeout=10.0)
                    await asyncio.sleep(2)
                except:
                    pass
            
            # Send SIGTERM
            if process.poll() is None:
                process.terminate()
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                    print(f"✅ {service_name} stopped gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill
                    print(f"⚠️  {service_name} didn't stop gracefully, force killing...")
                    process.kill()
                    process.wait()
                    print(f"🔨 {service_name} force stopped")
            
        except Exception as e:
            print(f"❌ Error stopping {service_name}: {e}")
        finally:
            del self.running_processes[service_name]
    
    async def restart_services(self, services: List[str] = None):
        """Restart services"""
        print("🔄 Restarting services...")
        await self.stop_services(services)
        await asyncio.sleep(2)
        await self.start_services(services)
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "total_services": len(self.services_config),
            "running_services": len(self.running_processes),
            "services": {}
        }
        
        for service_name, config in self.services_config.items():
            service_status = {
                "running": service_name in self.running_processes,
                "critical": config["critical"],
                "dependencies": config["dependencies"],
                "responsive": False,
                "health": None
            }
            
            # Check if process is actually running
            if service_name in self.running_processes:
                process = self.running_processes[service_name]
                if process.poll() is not None:
                    # Process died
                    service_status["running"] = False
                    del self.running_processes[service_name]
            
            # Try to get health info if running
            if service_status["running"]:
                try:
                    if not self.base_service:
                        self.base_service = BaseService("manager")
                    
                    health = await self.base_service.call_service(service_name, "health", timeout=5.0)
                    service_status["responsive"] = True
                    service_status["health"] = health
                    
                except Exception as e:
                    service_status["responsive"] = False
                    service_status["health"] = {"error": str(e)}
            
            status["services"][service_name] = service_status
        
        return status
    
    async def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary of all services"""
        if not self.base_service:
            self.base_service = BaseService("manager")
        
        health_summary = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "services": {},
            "alerts": []
        }
        
        unhealthy_count = 0
        
        for service_name in self.services_config.keys():
            try:
                health = await self.base_service.call_service(service_name, "health", timeout=5.0)
                
                service_health = {
                    "status": health.get("status", "unknown"),
                    "uptime": health.get("uptime", 0),
                    "memory_usage": health.get("memory_usage", 0),
                    "responsive": True
                }
                
                # Check for issues
                if health.get("status") != "healthy":
                    unhealthy_count += 1
                    health_summary["alerts"].append(f"{service_name} is {health.get('status', 'unhealthy')}")
                
                health_summary["services"][service_name] = service_health
                
            except Exception as e:
                unhealthy_count += 1
                health_summary["services"][service_name] = {
                    "status": "unreachable",
                    "error": str(e),
                    "responsive": False
                }
                health_summary["alerts"].append(f"{service_name} is unreachable: {e}")
        
        # Determine overall status
        if unhealthy_count == 0:
            health_summary["overall_status"] = "healthy"
        elif unhealthy_count <= 2:
            health_summary["overall_status"] = "degraded"
        else:
            health_summary["overall_status"] = "unhealthy"
        
        return health_summary
    
    async def show_logs(self, service_name: str = None, lines: int = 50):
        """Show service logs"""
        if service_name and service_name in self.running_processes:
            # Show logs for specific service
            log_file = f"/var/log/trading/{service_name}.log"
            if os.path.exists(log_file):
                subprocess.run(["tail", "-n", str(lines), log_file])
            else:
                print(f"Log file not found for {service_name}")
        else:
            # Show logs for all services
            log_dir = Path("/var/log/trading")
            if log_dir.exists():
                for log_file in log_dir.glob("*.log"):
                    print(f"\n=== {log_file.stem} ===")
                    subprocess.run(["tail", "-n", "10", str(log_file)])
            else:
                print("Log directory not found")
    
    async def run_dashboard(self):
        """Run real-time service dashboard"""
        print("🎛️  Trading Services Dashboard")
        print("Press Ctrl+C to exit\n")
        
        try:
            while True:
                # Clear screen (works on most terminals)
                os.system('cls' if os.name == 'nt' else 'clear')
                
                print("=" * 80)
                print("TRADING MICROSERVICES DASHBOARD")
                print("=" * 80)
                
                # Get service status
                status = await self.get_service_status()
                health = await self.get_health_summary()
                
                # Overall status
                overall_icon = {
                    "healthy": "🟢",
                    "degraded": "🟡", 
                    "unhealthy": "🔴"
                }.get(health["overall_status"], "⚪")
                
                print(f"Overall Status: {overall_icon} {health['overall_status'].upper()}")
                print(f"Running Services: {status['running_services']}/{status['total_services']}")
                print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print()
                
                # Service details
                print("SERVICE DETAILS:")
                print("-" * 80)
                
                for service_name, service_info in status["services"].items():
                    # Status icons
                    running_icon = "🟢" if service_info["running"] else "🔴"
                    responsive_icon = "💚" if service_info.get("responsive", False) else "💔"
                    critical_icon = "⭐" if service_info["critical"] else "  "
                    
                    # Health info
                    health_info = service_info.get("health", {})
                    uptime = health_info.get("uptime", 0) if isinstance(health_info, dict) else 0
                    memory = health_info.get("memory_usage", 0) if isinstance(health_info, dict) else 0
                    
                    # Format memory
                    memory_mb = f"{memory // 1024 // 1024}MB" if memory > 0 else "N/A"
                    uptime_str = f"{int(uptime)}s" if uptime > 0 else "N/A"
                    
                    print(f"{critical_icon}{running_icon} {responsive_icon} {service_name:<15} | "
                          f"Memory: {memory_mb:>8} | Uptime: {uptime_str:>8}")
                    
                    # Show dependencies
                    if service_info["dependencies"]:
                        deps = ", ".join(service_info["dependencies"])
                        print(f"    Dependencies: {deps}")
                    
                    # Show errors
                    if isinstance(health_info, dict) and "error" in health_info:
                        print(f"    ⚠️  Error: {health_info['error']}")
                
                # Alerts
                if health["alerts"]:
                    print("\nALERTS:")
                    print("-" * 80)
                    for alert in health["alerts"]:
                        print(f"⚠️  {alert}")
                
                print(f"\n{overall_icon} System Status: {health['overall_status'].upper()}")
                print("Press Ctrl+C to exit dashboard")
                
                # Wait before next update
                await asyncio.sleep(5)
                
        except KeyboardInterrupt:
            print("\n👋 Dashboard stopped")
    
    def cleanup(self):
        """Cleanup on exit"""
        print("\n🧹 Cleaning up...")
        
        # Stop all running processes
        for service_name, process in self.running_processes.items():
            try:
                print(f"Stopping {service_name}...")
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
        
        print("✅ Cleanup complete")

async def main():
    parser = argparse.ArgumentParser(description="Trading Microservices Manager")
    parser.add_argument("command", choices=[
        "start", "stop", "restart", "status", "health", "logs", "dashboard"
    ])
    parser.add_argument("--service", "-s", help="Specific service name")
    parser.add_argument("--lines", "-n", type=int, default=50, help="Number of log lines")
    
    args = parser.parse_args()
    
    manager = ServiceManager()
    
    # Setup signal handlers for cleanup
    def signal_handler(sig, frame):
        manager.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if args.command == "start":
            services = [args.service] if args.service else None
            success = await manager.start_services(services)
            if success:
                print("✅ Services started successfully")
            else:
                print("❌ Service startup failed")
                sys.exit(1)
        
        elif args.command == "stop":
            services = [args.service] if args.service else None
            await manager.stop_services(services)
        
        elif args.command == "restart":
            services = [args.service] if args.service else None
            await manager.restart_services(services)
        
        elif args.command == "status":
            status = await manager.get_service_status()
            print(json.dumps(status, indent=2))
        
        elif args.command == "health":
            health = await manager.get_health_summary()
            print(json.dumps(health, indent=2))
        
        elif args.command == "logs":
            await manager.show_logs(args.service, args.lines)
        
        elif args.command == "dashboard":
            await manager.run_dashboard()
    
    except KeyboardInterrupt:
        manager.cleanup()
    except Exception as e:
        print(f"❌ Error: {e}")
        manager.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
