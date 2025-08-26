#!/usr/bin/env python3
import subprocess
from datetime import datetime

print(f"🔍 System Monitor - {datetime.now().strftime(%Y-%m-%d %H:%M:%S)}")
print("=" * 50)

# Memory check
try:
    result = subprocess.run(["free", "-h"], capture_output=True, text=True)
    print("💾 Memory Usage:")
    for line in result.stdout.split("\n")[:3]:
        if line.strip():
            print(f"   {line}")
except:
    print("❌ Memory check failed")

print()

# Process check
try:
    result = subprocess.run(["ps", "aux", "--sort=-%mem"], capture_output=True, text=True)
    print("🔄 Top Memory Processes:")
    lines = result.stdout.split("\n")
    for i, line in enumerate(lines):
        if i == 0 or "python" in line.lower():
            if i < 10:  # Top 10 only
                print(f"   {line}")
except:
    print("❌ Process check failed")

print("=" * 50)
