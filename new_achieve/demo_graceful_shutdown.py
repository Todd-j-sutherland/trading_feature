#!/usr/bin/env python3
"""
Graceful Shutdown Demo
Demonstrates how to test the graceful shutdown functionality
"""

import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.utils.graceful_shutdown import setup_graceful_shutdown, register_cleanup, is_shutdown_requested

def demo_background_service():
    """Simulate a background service that can be gracefully shut down"""
    
    # Setup graceful shutdown
    shutdown_handler = setup_graceful_shutdown()
    
    # Register cleanup function
    def cleanup_demo():
        print("🧹 Demo service cleanup completed")
        
    register_cleanup(cleanup_demo)
    
    print("🚀 Demo service started")
    print("💡 Press Ctrl+C to test graceful shutdown")
    
    # Simulate continuous work
    counter = 0
    while not is_shutdown_requested():
        counter += 1
        print(f"🔄 Working... iteration {counter}")
        time.sleep(2)
        
        # Check for shutdown every few iterations
        if counter % 10 == 0:
            print("💡 Still running... Use Ctrl+C to stop gracefully")
    
    print("✅ Demo service completed")

if __name__ == "__main__":
    print("🎯 GRACEFUL SHUTDOWN DEMO")
    print("=" * 40)
    demo_background_service()
