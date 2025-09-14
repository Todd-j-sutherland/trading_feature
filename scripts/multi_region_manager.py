#!/usr/bin/env python3
"""
Multi-Region Trading System Management Dashboard
Enhanced service management with real-time monitoring and region switching
"""

import asyncio
import json
import time
import sys
import subprocess
import signal
from datetime import datetime
from typing import Dict, List, Any
import os

class MultiRegionManager:
    """Enhanced management for multi-region trading system"""
    
    def __init__(self):
        self.regions = ["asx", "usa", "uk", "eu"]
        self.services = {
            "prediction": "trading-prediction",
            "market-data": "trading-market-data", 
            "sentiment": "trading-sentiment"
        }
        self.socket_paths = {
            "prediction": "/tmp/trading_prediction.sock",
            "market-data": "/tmp/trading_market-data.sock",
            "sentiment": "/tmp/trading_sentiment.sock"
        }
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n🛑 Shutting down management dashboard...")
        self.running = False
    
    async def get_systemd_status(self, service_name: str) -> Dict[str, Any]:
        """Get systemd service status"""
        try:
            # Check if service is active
            result = subprocess.run(
                ["systemctl", "is-active", service_name],
                capture_output=True, text=True
            )
            active = result.stdout.strip() == "active"
            
            # Get additional service info
            info_result = subprocess.run(
                ["systemctl", "show", service_name, 
                 "--property=MainPID,ActiveEnterTimestamp,MemoryCurrent,CPUUsageNSec"],
                capture_output=True, text=True
            )
            
            info = {}
            for line in info_result.stdout.strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    info[key] = value
            
            return {
                "active": active,
                "status": result.stdout.strip(),
                "pid": info.get("MainPID", "N/A"),
                "started": info.get("ActiveEnterTimestamp", "N/A"),
                "memory": info.get("MemoryCurrent", "N/A"),
                "cpu_ns": info.get("CPUUsageNSec", "N/A")
            }
            
        except Exception as e:
            return {"error": str(e), "active": False}
    
    async def get_service_health(self, service_key: str) -> Dict[str, Any]:
        """Get service health via Unix socket"""
        try:
            socket_path = self.socket_paths[service_key]
            
            if not os.path.exists(socket_path):
                return {"status": "socket_missing", "error": f"Socket {socket_path} not found"}
            
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(socket_path),
                timeout=5.0
            )
            
            request = {"method": "health", "params": {}}
            writer.write(json.dumps(request).encode())
            await writer.drain()
            
            response_data = await asyncio.wait_for(reader.read(8192), timeout=5.0)
            response = json.loads(response_data.decode())
            
            writer.close()
            await writer.wait_closed()
            
            if response.get("status") == "success":
                return response.get("result", {})
            else:
                return {"status": "unhealthy", "error": response.get("error", "Unknown error")}
                
        except asyncio.TimeoutError:
            return {"status": "timeout", "error": "Service not responding"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_service_region(self, service_key: str) -> str:
        """Get current region for a service"""
        try:
            socket_path = self.socket_paths[service_key]
            
            reader, writer = await asyncio.open_unix_connection(socket_path)
            request = {"method": "get_current_region", "params": {}}
            writer.write(json.dumps(request).encode())
            await writer.drain()
            
            response_data = await asyncio.wait_for(reader.read(8192), timeout=5.0)
            response = json.loads(response_data.decode())
            
            writer.close()
            await writer.wait_closed()
            
            if response.get("status") == "success":
                return response.get("result", {}).get("region", "unknown")
            else:
                return "error"
                
        except Exception:
            return "unreachable"
    
    async def switch_service_region(self, service_key: str, region: str) -> Dict[str, Any]:
        """Switch a service to a different region"""
        try:
            socket_path = self.socket_paths[service_key]
            
            reader, writer = await asyncio.open_unix_connection(socket_path)
            request = {"method": "switch_region", "params": {"region": region}}
            writer.write(json.dumps(request).encode())
            await writer.drain()
            
            response_data = await asyncio.wait_for(reader.read(8192), timeout=10.0)
            response = json.loads(response_data.decode())
            
            writer.close()
            await writer.wait_closed()
            
            return response
            
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def switch_all_services_region(self, region: str) -> Dict[str, Any]:
        """Switch all services to the same region"""
        results = {}
        
        print(f"🌍 Switching all services to {region.upper()} region...")
        
        for service_key in self.services.keys():
            print(f"  Switching {service_key}...")
            result = await self.switch_service_region(service_key, region)
            
            if result.get("status") == "success":
                results[service_key] = "✅ SUCCESS"
                print(f"    ✅ {service_key} switched to {region}")
            else:
                results[service_key] = f"❌ FAILED: {result.get('error', 'Unknown error')}"
                print(f"    ❌ {service_key} failed: {result.get('error', 'Unknown error')}")
        
        return results
    
    def manage_systemd_service(self, action: str, service_name: str = None) -> Dict[str, str]:
        """Manage systemd services"""
        results = {}
        
        if service_name:
            services_to_manage = [service_name]
        else:
            services_to_manage = list(self.services.values())
        
        for service in services_to_manage:
            try:
                result = subprocess.run(
                    ["sudo", "systemctl", action, service],
                    capture_output=True, text=True
                )
                
                if result.returncode == 0:
                    results[service] = f"✅ {action.upper()}"
                else:
                    results[service] = f"❌ FAILED: {result.stderr.strip()}"
                    
            except Exception as e:
                results[service] = f"❌ ERROR: {str(e)}"
        
        return results
    
    def format_memory(self, memory_str: str) -> str:
        """Format memory string for display"""
        try:
            if memory_str == "N/A" or not memory_str.isdigit():
                return "N/A"
            
            memory_bytes = int(memory_str)
            memory_mb = memory_bytes / (1024 * 1024)
            
            if memory_mb > 1024:
                return f"{memory_mb/1024:.1f}GB"
            else:
                return f"{memory_mb:.0f}MB"
                
        except:
            return "N/A"
    
    def format_uptime(self, started_str: str) -> str:
        """Format uptime string for display"""
        try:
            if started_str == "N/A" or not started_str:
                return "N/A"
            
            # Parse systemd timestamp
            from datetime import datetime
            import re
            
            # Extract timestamp (format: "Mon 2024-09-14 10:30:45 UTC")
            match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', started_str)
            if match:
                timestamp_str = match.group()
                started_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                uptime = datetime.now() - started_time
                
                days = uptime.days
                hours = uptime.seconds // 3600
                minutes = (uptime.seconds % 3600) // 60
                
                if days > 0:
                    return f"{days}d {hours}h"
                elif hours > 0:
                    return f"{hours}h {minutes}m"
                else:
                    return f"{minutes}m"
            
            return "N/A"
            
        except:
            return "N/A"
    
    async def display_status_dashboard(self):
        """Display comprehensive status dashboard"""
        while self.running:
            try:
                # Clear screen
                os.system('clear' if os.name == 'posix' else 'cls')
                
                print("🌍 MULTI-REGION TRADING SYSTEM MANAGEMENT DASHBOARD")
                print("=" * 70)
                print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print()
                
                # System Status
                print("📊 SYSTEM STATUS")
                print("-" * 40)
                
                all_healthy = True
                
                for service_key, systemd_name in self.services.items():
                    # Get systemd status
                    systemd_status = await self.get_systemd_status(systemd_name)
                    
                    # Get service health
                    health = await self.get_service_health(service_key)
                    
                    # Get current region
                    region = await self.get_service_region(service_key)
                    
                    # Status indicators
                    if systemd_status.get("active") and health.get("status") == "healthy":
                        status_icon = "🟢"
                        status_text = "HEALTHY"
                    elif systemd_status.get("active"):
                        status_icon = "🟡"
                        status_text = "RUNNING"
                        all_healthy = False
                    else:
                        status_icon = "🔴"
                        status_text = "STOPPED"
                        all_healthy = False
                    
                    # Format memory and uptime
                    memory = self.format_memory(systemd_status.get("memory", "N/A"))
                    uptime = self.format_uptime(systemd_status.get("started", "N/A"))
                    
                    print(f"{status_icon} {service_key:12} | {status_text:8} | "
                          f"Region: {region:4} | Memory: {memory:>6} | "
                          f"Uptime: {uptime:>6}")
                
                # Overall system status
                print()
                if all_healthy:
                    print("✅ OVERALL SYSTEM STATUS: HEALTHY")
                else:
                    print("⚠️  OVERALL SYSTEM STATUS: DEGRADED")
                
                # Regional Information
                print("\n🌍 REGIONAL CONFIGURATIONS")
                print("-" * 40)
                
                try:
                    # Import here to avoid issues if not available
                    sys.path.append('/opt/trading_services')
                    from app.config.regions.config_manager import ConfigManager
                    
                    config_mgr = ConfigManager()
                    available_regions = config_mgr.get_available_regions()
                    
                    for region in self.regions:
                        if region in available_regions:
                            try:
                                config_mgr.set_region(region)
                                config = config_mgr.get_config()
                                
                                region_info = config.get("region", {})
                                currency = region_info.get("currency", "N/A")
                                timezone = region_info.get("timezone", "N/A")
                                
                                # Count services currently on this region
                                services_on_region = 0
                                for svc_key in self.services.keys():
                                    svc_region = await self.get_service_region(svc_key)
                                    if svc_region == region:
                                        services_on_region += 1
                                
                                region_icon = "🔵" if services_on_region > 0 else "⚪"
                                
                                print(f"{region_icon} {region.upper():4} | {currency:3} | "
                                      f"{timezone:20} | Services: {services_on_region}")
                                
                            except Exception as e:
                                print(f"⚪ {region.upper():4} | ERROR: {str(e)[:30]}")
                        else:
                            print(f"❌ {region.upper():4} | Configuration not found")
                            
                except Exception as e:
                    print(f"❌ Region information unavailable: {str(e)}")
                
                # Management Commands
                print(f"\n🔧 MANAGEMENT COMMANDS")
                print("-" * 40)
                print("1. Start all services       | 2. Stop all services")
                print("3. Restart all services     | 4. Switch all to ASX")
                print("5. Switch all to USA        | 6. Switch all to UK")
                print("7. Switch all to EU         | 8. Service logs")
                print("9. Validation test          | 0. Detailed health")
                print("Q. Quit dashboard")
                
                print(f"\n⏰ Auto-refresh in 10 seconds... (Press any key for menu)")
                
                # Wait for input or auto-refresh
                try:
                    # Use select for non-blocking input (Unix-like systems)
                    import select
                    import sys
                    
                    ready, _, _ = select.select([sys.stdin], [], [], 10)
                    
                    if ready:
                        choice = sys.stdin.readline().strip().upper()
                        
                        if choice == 'Q':
                            break
                        elif choice == '1':
                            print("\n🚀 Starting all services...")
                            results = self.manage_systemd_service("start")
                            for service, result in results.items():
                                print(f"  {service}: {result}")
                            input("\nPress Enter to continue...")
                            
                        elif choice == '2':
                            print("\n🛑 Stopping all services...")
                            results = self.manage_systemd_service("stop")
                            for service, result in results.items():
                                print(f"  {service}: {result}")
                            input("\nPress Enter to continue...")
                            
                        elif choice == '3':
                            print("\n🔄 Restarting all services...")
                            results = self.manage_systemd_service("restart")
                            for service, result in results.items():
                                print(f"  {service}: {result}")
                            input("\nPress Enter to continue...")
                            
                        elif choice == '4':
                            results = await self.switch_all_services_region("asx")
                            input("\nPress Enter to continue...")
                            
                        elif choice == '5':
                            results = await self.switch_all_services_region("usa")
                            input("\nPress Enter to continue...")
                            
                        elif choice == '6':
                            results = await self.switch_all_services_region("uk")
                            input("\nPress Enter to continue...")
                            
                        elif choice == '7':
                            results = await self.switch_all_services_region("eu")
                            input("\nPress Enter to continue...")
                            
                        elif choice == '8':
                            print("\nAvailable services:")
                            for i, (key, systemd_name) in enumerate(self.services.items(), 1):
                                print(f"{i}. {key} ({systemd_name})")
                            
                            try:
                                svc_choice = int(input("Enter service number: ")) - 1
                                service_keys = list(self.services.keys())
                                if 0 <= svc_choice < len(service_keys):
                                    service_key = service_keys[svc_choice]
                                    systemd_name = self.services[service_key]
                                    
                                    print(f"\nShowing logs for {service_key} ({systemd_name})...")
                                    print("Press Ctrl+C to return to dashboard")
                                    
                                    subprocess.run(["sudo", "journalctl", "-u", systemd_name, "-f"])
                                    
                            except (ValueError, KeyboardInterrupt):
                                pass
                            
                        elif choice == '9':
                            print("\n🔍 Running validation test...")
                            try:
                                result = subprocess.run([
                                    "python3", "/opt/trading_services/validate_multi_region.py"
                                ], capture_output=True, text=True)
                                
                                print(result.stdout)
                                if result.stderr:
                                    print("Errors:")
                                    print(result.stderr)
                                    
                            except Exception as e:
                                print(f"Validation test failed: {str(e)}")
                            
                            input("\nPress Enter to continue...")
                            
                        elif choice == '0':
                            print("\n🏥 DETAILED HEALTH CHECK")
                            print("=" * 50)
                            
                            for service_key in self.services.keys():
                                print(f"\n📋 {service_key.upper()} SERVICE:")
                                health = await self.get_service_health(service_key)
                                
                                for key, value in health.items():
                                    print(f"  {key}: {value}")
                            
                            input("\nPress Enter to continue...")
                            
                except ImportError:
                    # Fallback for systems without select
                    await asyncio.sleep(10)
                except KeyboardInterrupt:
                    break
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Dashboard error: {str(e)}")
                await asyncio.sleep(5)
        
        print("\n👋 Management dashboard stopped")

async def main():
    """Main function"""
    if len(sys.argv) > 1:
        # Command line mode
        manager = MultiRegionManager()
        command = sys.argv[1].lower()
        
        if command == "start":
            print("🚀 Starting all services...")
            results = manager.manage_systemd_service("start")
            for service, result in results.items():
                print(f"  {service}: {result}")
                
        elif command == "stop":
            print("🛑 Stopping all services...")
            results = manager.manage_systemd_service("stop")
            for service, result in results.items():
                print(f"  {service}: {result}")
                
        elif command == "restart":
            print("🔄 Restarting all services...")
            results = manager.manage_systemd_service("restart")
            for service, result in results.items():
                print(f"  {service}: {result}")
                
        elif command == "status":
            print("📊 Service Status:")
            for service_key, systemd_name in manager.services.items():
                systemd_status = await manager.get_systemd_status(systemd_name)
                health = await manager.get_service_health(service_key)
                region = await manager.get_service_region(service_key)
                
                status = "🟢" if systemd_status.get("active") and health.get("status") == "healthy" else "🔴"
                print(f"  {status} {service_key}: {health.get('status', 'unknown')} (Region: {region})")
                
        elif command in ["asx", "usa", "uk", "eu"]:
            results = await manager.switch_all_services_region(command)
            
        elif command == "dashboard":
            await manager.display_status_dashboard()
            
        else:
            print("Usage: python3 multi_region_manager.py [start|stop|restart|status|asx|usa|uk|eu|dashboard]")
            
    else:
        # Interactive dashboard mode
        manager = MultiRegionManager()
        await manager.display_status_dashboard()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
