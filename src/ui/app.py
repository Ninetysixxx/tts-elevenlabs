#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main Application UI
Manages all UI components and application flow
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# Import UI tabs
from src.ui.conversion_tab import ConversionTab
from src.ui.api_key_tab import ApiKeyTab
from src.ui.batch_tab import BatchTab
from src.ui.settings_tab import SettingsTab

# Import utilities and models
from src.utils.logger import Logger
from src.utils.api_key_manager import ApiKeyManager
from src.models.config import AppConfig
from src.api.elevenlabs_client import ElevenLabsClient

class TtsApplication:
    """Main application class for the TTS converter"""
    
    def __init__(self):
        """Initialize the application"""
        # Create the main window
        self.root = tk.Tk()
        self.root.title("Chuyển Đổi Văn Bản Thành Âm Thanh ElevenLabs")
        self.root.geometry("900x650")
        self.root.minsize(800, 600)
        
        # Initialize shared resources
        self.logger = Logger()
        self.config = AppConfig()
        self.api_key_manager = ApiKeyManager()
        
        # Initialize API client with current key if available
        current_key = self.api_key_manager.get_current_key()
        self.api_client = ElevenLabsClient(current_key) if current_key else None
        
        # Set up UI
        self._setup_ui()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _setup_ui(self):
        """Set up the main UI components"""
        # Main container frame
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create tab control
        self.tab_control = ttk.Notebook(self.main_frame)
        self.tab_control.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.conversion_tab = ConversionTab(
            self.tab_control, 
            self.api_client, 
            self.api_key_manager, 
            self.logger,
            self.config
        )
        self.api_key_tab = ApiKeyTab(
            self.tab_control, 
            self.api_key_manager, 
            self.logger,
            self._on_api_key_change
        )
        self.batch_tab = BatchTab(
            self.tab_control, 
            self.api_client,
            self.logger,
            self.config
        )
        self.settings_tab = SettingsTab(
            self.tab_control, 
            self.config, 
            self.logger
        )
        
        # Add tabs to notebook
        self.tab_control.add(self.conversion_tab.frame, text="Chuyển Đổi")
        self.tab_control.add(self.api_key_tab.frame, text="Quản Lý API Key")
        self.tab_control.add(self.batch_tab.frame, text="Xử Lý Hàng Loạt")
        self.tab_control.add(self.settings_tab.frame, text="Tùy Chọn Xử Lý")
        
        # Status bar
        self.status_bar = ttk.Frame(self.main_frame)
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
        
        self.status_label = ttk.Label(self.status_bar, text="Sẵn sàng.")
        self.status_label.pack(side=tk.LEFT)
        
        self.version_label = ttk.Label(self.status_bar, text="v1.0")
        self.version_label.pack(side=tk.RIGHT)
    
    def _on_api_key_change(self, key_name: str, api_key: str):
        """Handle API key change events"""
        # Create a new client with the updated key
        self.api_client = ElevenLabsClient(api_key)
        
        # Update the API client in tabs that need it
        self.conversion_tab.update_api_client(self.api_client)
        self.batch_tab.update_api_client(self.api_client)
        
        # Update API key dropdown in conversion tab
        self.conversion_tab._update_api_key_dropdown()
        
        # Validate the key and show status
        def validate_key():
            # Validate in background thread
            valid, data = self.api_client.validate_api_key()
            
            # Update UI in main thread
            self.root.after(0, lambda: self._update_key_status(valid, data))
        
        # Start validation in background
        threading.Thread(target=validate_key, daemon=True).start()
    
    def _update_key_status(self, valid: bool, data: dict, total_credits: dict = None):
        """Update the UI with API key validation results"""
        if valid:
            # Extract credit information from various locations
            subscription = data.get("subscription", {})
            
            # Lấy tổng số credits (character_limit)
            character_limit = subscription.get("character_limit", 0)
            
            # Lấy số đã sử dụng (character_count trong API thực ra là số đã dùng)
            character_used = subscription.get("character_count", 0)
            
            # Tính số còn lại
            character_remaining = character_limit - character_used
            
            # Thử lấy từ data chính nếu không có trong subscription
            if character_limit == 0:
                character_limit = data.get("character_limit", 0) 
                character_used = data.get("character_count", 0)
                character_remaining = character_limit - character_used
            
            # Format credits info cho logging và hiển thị
            credits_info = f"{character_remaining:,} / {character_limit:,}"
            
            # Add total credits info if available
            if total_credits and total_credits.get("unique_keys", 0) > 0:
                total_remaining = total_credits.get("total_remaining", 0)
                unique_keys = total_credits.get("unique_keys", 0)
                duplicates = total_credits.get("duplicates", 0)
                
                # Only show total if we have more than one unique key
                if unique_keys > 1:
                    total_info = f" (Tổng: {total_remaining:,} từ {unique_keys} khóa)"
                    credits_info += total_info
                    
                    # Log if duplicates found
                    if duplicates > 0:
                        self.logger.info(f"Đã phát hiện {duplicates} khóa trùng lặp và đã loại bỏ khỏi tổng số")
            
            self.logger.success(f"API key hợp lệ. Credits còn lại: {credits_info}")
            self.status_label.config(text=f"API key hợp lệ. Credits: {credits_info}")
            
            # Update conversion tab with available voices
            self.conversion_tab.refresh_voices()
        else:
            error_msg = data.get("error", "Lỗi không xác định")
            self.logger.error(f"API key không hợp lệ: {error_msg}")
            self.status_label.config(text="API key không hợp lệ.")
            messagebox.showerror("Lỗi API Key", f"API key không hợp lệ: {error_msg}")
    
    def _on_close(self):
        """Handle application close event"""
        # Perform cleanup
        try:
            # Save config
            self.config.save_config()
            
            # Stop any running batch processes
            if hasattr(self.batch_tab, 'stop_batch'):
                self.batch_tab.stop_batch()
        except:
            pass
        
        # Close the application
        self.root.destroy()
    
    def run(self):
        """Run the application"""
        # Check for API key on startup
        if not self.api_key_manager.get_current_key():
            # No API key, show message
            self.logger.warning("Không tìm thấy API key. Vui lòng thêm một API key để bắt đầu.")
            # Switch to API key tab after delay
            self.root.after(500, lambda: self.tab_control.select(1))
        else:
            # Validate existing key
            self._on_api_key_change(
                self.api_key_manager.current_key,
                self.api_key_manager.get_current_key()
            )
        
        # Start main loop
        self.root.mainloop()

    def update_credits(self):
        """Update credits across the application"""
        if not self.api_client:
            return
        
        def get_credits():
            # Get user info in background
            valid, data = self.api_client.validate_api_key()
            
            # Get total credits from all keys
            total_credits = self.api_key_manager.get_total_credits(self.api_client)
            
            # Update UI in main thread
            self.root.after(0, lambda: self._update_key_status(valid, data, total_credits))
        
        # Start validation in background
        threading.Thread(target=get_credits, daemon=True).start() 