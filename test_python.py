#!/usr/bin/env python3
"""
Simple test script to verify Python environment
"""
import sys
import os
from pathlib import Path

print("Python Test Script")
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current working directory: {os.getcwd()}")
print(f"Python path: {sys.path[:3]}...")

# Test imports
try:
    import pandas
    print("✅ pandas available")
except ImportError:
    print("❌ pandas not available")

try:
    import requests
    print("✅ requests available")
except ImportError:
    print("❌ requests not available")

try:
    from app.main import main
    print("✅ app.main import successful")
    print("🚀 Ready to run trading application")
except ImportError as e:
    print(f"❌ app.main import failed: {e}")

print("\nEnvironment test completed")
