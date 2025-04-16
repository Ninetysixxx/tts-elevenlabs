#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Logger Utility
Handles logging for the application
"""

import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

class Logger:
    """Application logger"""
    
    def __init__(self, max_entries: int = 1000):
        """Initialize the logger"""
        self.max_entries = max_entries
        self.entries = []
        self.callbacks = []
    
    def add_callback(self, callback: Callable[[str, str], None]) -> None:
        """Add a callback function to be called when a new log entry is added"""
        self.callbacks.append(callback)
    
    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message with a specific level"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{level}] {message}"
        
        # Add to entries
        self.entries.append(entry)
        
        # Trim if exceeds max entries
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
        
        # Call callbacks
        for callback in self.callbacks:
            try:
                callback(message, level)
            except:
                pass
    
    def info(self, message: str) -> None:
        """Log an info message"""
        self.log(message, "INFO")
    
    def warning(self, message: str) -> None:
        """Log a warning message"""
        self.log(message, "WARNING")
    
    def error(self, message: str) -> None:
        """Log an error message"""
        self.log(message, "ERROR")
    
    def success(self, message: str) -> None:
        """Log a success message"""
        self.log(message, "SUCCESS")
    
    def clear(self) -> None:
        """Clear all log entries"""
        self.entries = []
    
    def get_entries(self) -> List[str]:
        """Get all log entries"""
        return self.entries
    
    def get_recent_entries(self, count: int) -> List[str]:
        """Get the most recent log entries"""
        return self.entries[-count:] if count < len(self.entries) else self.entries
    
    def save_to_file(self, file_path: str) -> bool:
        """Save log entries to a file"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for entry in self.entries:
                    f.write(f"{entry}\n")
            return True
        except:
            return False 