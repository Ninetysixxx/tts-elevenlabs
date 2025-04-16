#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration model for the application
"""

import os
import json
from typing import Dict, Any, Optional

class AppConfig:
    """Application configuration settings"""
    
    DEFAULT_CONFIG = {
        "output_format": "mp3",
        "default_model": "eleven_turbo_v2",
        "default_voice": "",
        "output_directory": "",
        "stability": 0.5,
        "similarity_boost": 0.5,
        "chunk_size": 5000,  # Characters per TTS request
        "language": "vi",    # Default language: Vietnamese
        "theme": "default"
    }
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize with default settings or from config file"""
        self.config_file = config_file
        self.settings = self.DEFAULT_CONFIG.copy()
        
        # Load config if exists
        if os.path.exists(config_file):
            self.load_config()
    
    def get(self, key: str, default=None) -> Any:
        """Get a configuration value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        self.settings[key] = value
        self.save_config()
    
    def update(self, settings: Dict[str, Any]) -> None:
        """Update multiple settings at once"""
        self.settings.update(settings)
        self.save_config()
    
    def load_config(self) -> bool:
        """Load configuration from file"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)
                
            # Update settings with loaded values
            self.settings.update(loaded_config)
            return True
        except:
            # Failed to load, keep defaults
            return False
    
    def save_config(self) -> bool:
        """Save configuration to file"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=2)
            return True
        except:
            return False 