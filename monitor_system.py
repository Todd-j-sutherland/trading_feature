#!/usr/bin/env python3
"""
System Monitoring Script
Tracks memory usage, prediction performance, and system health
"""

import os
import subprocess
import json
from datetime import datetime

def check_memory_usage():
    """Check current system memory usage"""
    try:
        result = subprocess.run(["free", "-m"], capture_output=True, text=True)
        lines = result.stdout.strip().split("\n")
        mem_line = lines[1].split()
        
        total = int(mem_line[1])
        used = int(mem_line[2])
        available = int(mem_line[6])
        
        usage_percent = (used / total) * 100
        
        return {
            "total_mb": total,
            "used_mb": used,
            "available_mb": available,
            "usage_percent": usage_percent
        }
    except Exception as e:
        return {"error": str(e)}

def check_trading_processes():
    """Check for running trading-related processes"""
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        processes = []
        
        for line in result.stdout.split("\n"):
            if any(keyword in line.lower() for keyword in ["trading", "collector", "prediction", "python.*app"]):
                if "grep" not in line and line.strip():
                    parts = line.split()
                    if len(parts) >= 11:
                        processes.append({
                            "pid": parts[1],
                            "cpu": parts[2],
                            "memory": parts[3],
                            "command": " ".join(parts[10:])[:100]
                        })
        
        return processes
    except Exception as e:
        return {"error": str(e)}

def generate_system_report():
    """Generate comprehensive system report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = {
        "timestamp": timestamp,
        "memory": check_memory_usage(),
        "processes": check_trading_processes(),
        "cron_status": "active" if os.path.exists("/root/test/cron_prediction.log") else "inactive"
    }
    
    # Save report
    with open("/root/test/system_monitor_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"🔍 System Monitor Report - {timestamp}")
    print("=" * 50)
    
    mem = report["memory"]
    if "error" not in mem:
        print(f"💾 Memory: {mem[used_mb]}MB / {mem[total_mb]}MB ({mem[usage_percent]:.1f}%)")
        if mem["usage_percent"] > 50:
            print("⚠️ High memory usage detected")
        else:
            print("✅ Memory usage normal")
    else:
        print(f"❌ Memory check failed: {mem[error]}")
    
    processes = report["processes"]
    if isinstance(processes, list):
        print(f"🔄 Trading processes: {len(processes)}")
        for proc in processes:
            print(f"   PID {proc[pid]}: {proc[memory]}% mem, {proc[cpu]}% cpu - {proc[command]}")
    else:
        print(f"❌ Process check failed: {processes.get("error", "Unknown error")}")
    
    print(f"⏰ Cron status: {report[cron_status]}")
    print("=" * 50)

if __name__ == "__main__":
    generate_system_report()
