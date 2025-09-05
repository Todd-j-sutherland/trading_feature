#!/usr/bin/env python3
"""
Signal Handler Module for Graceful Shutdown
Provides signal handling utilities for the trading system
"""

import signal
import sys
import os
import logging
import atexit
from typing import Set, Callable, Optional
from threading import Event

logger = logging.getLogger(__name__)

class GracefulShutdownHandler:
    """Handles graceful shutdown for the trading system"""
    
    def __init__(self):
        self.shutdown_event = Event()
        self.cleanup_functions: Set[Callable] = set()
        self.shutdown_in_progress = False
        self._original_handlers = {}
        
    def register_cleanup_function(self, cleanup_func: Callable):
        """Register a cleanup function to be called on shutdown"""
        self.cleanup_functions.add(cleanup_func)
        
    def unregister_cleanup_function(self, cleanup_func: Callable):
        """Unregister a cleanup function"""
        self.cleanup_functions.discard(cleanup_func)
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            signal_name = signal.Signals(signum).name
            logger.info(f"Received {signal_name} signal. Initiating graceful shutdown...")
            print(f"\n🛑 Received {signal_name} signal. Shutting down gracefully...")
            self.initiate_shutdown()
            
        # Store original handlers
        self._original_handlers[signal.SIGINT] = signal.signal(signal.SIGINT, signal_handler)
        self._original_handlers[signal.SIGTERM] = signal.signal(signal.SIGTERM, signal_handler)
        
        # Register atexit handler
        atexit.register(self.cleanup)
        
        logger.info("Signal handlers registered for graceful shutdown")
        
    def restore_signal_handlers(self):
        """Restore original signal handlers"""
        for sig, handler in self._original_handlers.items():
            if handler is not None:
                signal.signal(sig, handler)
        self._original_handlers.clear()
        
    def initiate_shutdown(self):
        """Initiate the shutdown process"""
        if self.shutdown_in_progress:
            return
            
        self.shutdown_in_progress = True
        self.shutdown_event.set()
        
        # Call all registered cleanup functions
        self.cleanup()
        
        # Exit gracefully
        logger.info("Graceful shutdown completed")
        sys.exit(0)
        
    def cleanup(self):
        """Run all cleanup functions"""
        if not self.cleanup_functions:
            return
            
        print("🧹 Running cleanup functions...")
        
        for cleanup_func in self.cleanup_functions.copy():
            try:
                cleanup_func()
            except Exception as e:
                logger.error(f"Error in cleanup function {cleanup_func.__name__}: {e}")
                print(f"⚠️ Cleanup warning: {e}")
                
        self.cleanup_functions.clear()
        print("✅ Cleanup completed")
        
    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested"""
        return self.shutdown_event.is_set()
        
    def wait_for_shutdown(self, timeout: Optional[float] = None) -> bool:
        """Wait for shutdown signal"""
        return self.shutdown_event.wait(timeout)

# Global instance
_shutdown_handler = None

def get_shutdown_handler() -> GracefulShutdownHandler:
    """Get the global shutdown handler instance"""
    global _shutdown_handler
    if _shutdown_handler is None:
        _shutdown_handler = GracefulShutdownHandler()
    return _shutdown_handler

def setup_graceful_shutdown():
    """Setup graceful shutdown for the current process"""
    handler = get_shutdown_handler()
    handler.setup_signal_handlers()
    return handler

def register_cleanup(cleanup_func: Callable):
    """Register a cleanup function"""
    handler = get_shutdown_handler()
    handler.register_cleanup_function(cleanup_func)

def is_shutdown_requested() -> bool:
    """Check if shutdown has been requested"""
    handler = get_shutdown_handler()
    return handler.is_shutdown_requested()

def wait_for_shutdown(timeout: Optional[float] = None) -> bool:
    """Wait for shutdown signal"""
    handler = get_shutdown_handler()
    return handler.wait_for_shutdown(timeout)
