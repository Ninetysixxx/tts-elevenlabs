#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Key Tab
UI tab for managing API keys
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from src.utils.api_key_manager import ApiKeyManager
from src.utils.logger import Logger

class ApiKeyTab:
    """Tab for managing API keys"""
    
    def __init__(self, parent, api_key_manager, logger, on_key_change_callback=None):
        """Initialize the API key tab"""
        self.parent = parent
        self.api_key_manager = api_key_manager
        self.logger = logger
        self.on_key_change = on_key_change_callback
        
        # Create the tab frame
        self.frame = ttk.Frame(parent)
        self._setup_ui()
        
        # Update the UI with keys
        self._refresh_key_list()
    
    def _setup_ui(self):
        """Set up the UI components"""
        main_frame = ttk.Frame(self.frame, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel: Key list
        left_frame = ttk.LabelFrame(main_frame, text="Danh Sách API Key")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Key list with scrollbar
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.key_listbox = tk.Listbox(list_frame, height=10)
        self.key_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.key_listbox.bind("<<ListboxSelect>>", self._on_key_select)
        
        key_scrollbar = ttk.Scrollbar(list_frame, command=self.key_listbox.yview)
        key_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.key_listbox.config(yscrollcommand=key_scrollbar.set)
        
        # Buttons below list
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.set_current_btn = ttk.Button(
            btn_frame,
            text="Đặt làm Mặc Định",
            command=self._set_current_key
        )
        self.set_current_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.refresh_btn = ttk.Button(
            btn_frame,
            text="Làm Mới",
            command=self._refresh_key_list
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        self.remove_btn = ttk.Button(
            btn_frame,
            text="Xóa",
            command=self._remove_key
        )
        self.remove_btn.pack(side=tk.RIGHT)
        
        # Right panel: Add key
        right_frame = ttk.LabelFrame(main_frame, text="Thêm API Key Mới")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Add key form
        form_frame = ttk.Frame(right_frame, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Key name
        name_frame = ttk.Frame(form_frame)
        name_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(name_frame, text="Tên Key:").pack(anchor=tk.W)
        
        self.key_name_var = tk.StringVar()
        self.key_name_entry = ttk.Entry(name_frame, textvariable=self.key_name_var)
        self.key_name_entry.pack(fill=tk.X, pady=5)
        
        # API key
        key_frame = ttk.Frame(form_frame)
        key_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(key_frame, text="API Key:").pack(anchor=tk.W)
        
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ttk.Entry(key_frame, textvariable=self.api_key_var, show="*")
        self.api_key_entry.pack(fill=tk.X, pady=5)
        
        # Show/hide key
        self.show_key_var = tk.BooleanVar(value=False)
        self.show_key_check = ttk.Checkbutton(
            key_frame, 
            text="Hiện Key",
            variable=self.show_key_var,
            command=self._toggle_key_visibility
        )
        self.show_key_check.pack(anchor=tk.W)
        
        # Add button
        self.add_btn = ttk.Button(
            form_frame,
            text="Thêm Key",
            command=self._add_key
        )
        self.add_btn.pack(pady=10)
        
        # Instructions
        instruction_frame = ttk.LabelFrame(form_frame, text="Hướng Dẫn")
        instruction_frame.pack(fill=tk.X, pady=10)
        
        instructions = (
            "1. Truy cập https://elevenlabs.io/\n"
            "2. Đăng nhập và vào trang cài đặt\n"
            "3. Tìm phần API Key\n"
            "4. Sao chép API Key và dán vào đây"
        )
        
        ttk.Label(instruction_frame, text=instructions, justify=tk.LEFT).pack(
            pady=10, padx=10, anchor=tk.W
        )
    
    def _toggle_key_visibility(self):
        """Toggle the visibility of the API key"""
        if self.show_key_var.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")
    
    def _refresh_key_list(self):
        """Refresh the list of API keys"""
        # Clear the list
        self.key_listbox.delete(0, tk.END)
        
        # Get key names
        key_names = self.api_key_manager.get_key_names()
        
        # Add to listbox
        for name in key_names:
            self.key_listbox.insert(tk.END, name)
            
            # Mark current key
            if name == self.api_key_manager.current_key:
                index = key_names.index(name)
                self.key_listbox.itemconfig(index, {'bg': '#e6f2ff'})
    
    def _on_key_select(self, event):
        """Handle key selection in listbox"""
        # No action needed now
        pass
    
    def _add_key(self):
        """Add a new API key"""
        name = self.key_name_var.get().strip()
        key = self.api_key_var.get().strip()
        
        if not name:
            messagebox.showerror("Lỗi", "Vui lòng nhập tên cho API key")
            return
        
        if not key:
            messagebox.showerror("Lỗi", "Vui lòng nhập API key")
            return
        
        # Check if name already exists
        if name in self.api_key_manager.get_key_names():
            overwrite = messagebox.askyesno(
                "Xác nhận", 
                f"API key với tên '{name}' đã tồn tại. Bạn có muốn ghi đè không?"
            )
            if not overwrite:
                return
        
        # Add the key
        if self.api_key_manager.add_key(name, key):
            self.logger.success(f"Đã thêm API key: {name}")
            
            # Clear inputs
            self.key_name_var.set("")
            self.api_key_var.set("")
            
            # Refresh list
            self._refresh_key_list()
            
            # Set as current key if no current key
            if not self.api_key_manager.current_key or self.api_key_manager.current_key != name:
                self.api_key_manager.set_current_key(name)
            
            # Notify about key change
            if self.on_key_change:
                self.on_key_change(name, key)
        else:
            self.logger.error(f"Không thể thêm API key: {name}")
            messagebox.showerror("Lỗi", "Không thể thêm API key")
    
    def _remove_key(self):
        """Remove the selected API key"""
        selected = self.key_listbox.curselection()
        
        if not selected:
            messagebox.showerror("Lỗi", "Vui lòng chọn một API key để xóa")
            return
        
        key_name = self.key_listbox.get(selected[0])
        
        # Confirm deletion
        confirm = messagebox.askyesno(
            "Xác nhận", 
            f"Bạn có chắc chắn muốn xóa API key '{key_name}'?"
        )
        
        if confirm:
            # Remove the key
            if self.api_key_manager.remove_key(key_name):
                self.logger.success(f"Đã xóa API key: {key_name}")
                
                # Refresh list
                self._refresh_key_list()
                
                # If current key was removed, notify about change
                if self.on_key_change:
                    current_key = self.api_key_manager.get_current_key()
                    if current_key:
                        self.on_key_change(
                            self.api_key_manager.current_key,
                            current_key
                        )
            else:
                self.logger.error(f"Không thể xóa API key: {key_name}")
                messagebox.showerror("Lỗi", "Không thể xóa API key")
    
    def _set_current_key(self):
        """Set the selected key as current"""
        selected = self.key_listbox.curselection()
        
        if not selected:
            messagebox.showerror("Lỗi", "Vui lòng chọn một API key để đặt làm mặc định")
            return
        
        key_name = self.key_listbox.get(selected[0])
        
        # Set as current
        if self.api_key_manager.set_current_key(key_name):
            self.logger.success(f"Đã đặt API key '{key_name}' làm mặc định")
            
            # Refresh list to update highlighting
            self._refresh_key_list()
            
            # Notify about key change
            if self.on_key_change:
                self.on_key_change(
                    key_name,
                    self.api_key_manager.get_key(key_name)
                )
        else:
            self.logger.error(f"Không thể đặt API key '{key_name}' làm mặc định")
            messagebox.showerror("Lỗi", "Không thể đặt API key làm mặc định") 