#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Settings Tab
UI tab for application settings and configuration
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, Optional

from src.models.config import AppConfig
from src.utils.logger import Logger

class SettingsTab:
    """Tab for application settings"""
    
    def __init__(self, parent, config, logger):
        """Initialize the settings tab"""
        self.parent = parent
        self.config = config
        self.logger = logger
        
        # Create the tab frame
        self.frame = ttk.Frame(parent)
        self._setup_ui()
        
        # Load current settings
        self._load_settings()
    
    def _setup_ui(self):
        """Set up the UI components"""
        main_frame = ttk.Frame(self.frame, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # TTS Settings
        tts_frame = ttk.LabelFrame(main_frame, text="Tùy Chọn Xử Lý", padding=10)
        tts_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Chunk size
        chunk_frame = ttk.Frame(tts_frame)
        chunk_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(chunk_frame, text="Kích thước phân đoạn (ký tự):").pack(side=tk.LEFT)
        
        self.chunk_size_var = tk.IntVar(value=5000)
        self.chunk_size_entry = ttk.Spinbox(
            chunk_frame,
            from_=1000,
            to=10000,
            increment=500,
            textvariable=self.chunk_size_var,
            width=10
        )
        self.chunk_size_entry.pack(side=tk.RIGHT)
        
        # Voice parameters
        voice_param_frame = ttk.Frame(tts_frame)
        voice_param_frame.pack(fill=tk.X, pady=10)
        
        # Stability
        stability_frame = ttk.Frame(voice_param_frame)
        stability_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(stability_frame, text="Độ Ổn Định Mặc Định:").pack(side=tk.LEFT)
        
        self.stability_var = tk.DoubleVar(value=0.5)
        self.stability_scale = ttk.Scale(
            stability_frame,
            from_=0.0,
            to=1.0,
            variable=self.stability_var,
            orient=tk.HORIZONTAL
        )
        self.stability_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.stability_label = ttk.Label(stability_frame, text="0.5")
        self.stability_label.pack(side=tk.RIGHT)
        
        self.stability_var.trace_add("write", self._update_stability_label)
        
        # Similarity boost
        similarity_frame = ttk.Frame(voice_param_frame)
        similarity_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(similarity_frame, text="Độ Tương Đồng Mặc Định:").pack(side=tk.LEFT)
        
        self.similarity_var = tk.DoubleVar(value=0.5)
        self.similarity_scale = ttk.Scale(
            similarity_frame,
            from_=0.0,
            to=1.0,
            variable=self.similarity_var,
            orient=tk.HORIZONTAL
        )
        self.similarity_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.similarity_label = ttk.Label(similarity_frame, text="0.5")
        self.similarity_label.pack(side=tk.RIGHT)
        
        self.similarity_var.trace_add("write", self._update_similarity_label)
        
        # Output Settings
        output_frame = ttk.LabelFrame(main_frame, text="Tùy Chọn Đầu Ra", padding=10)
        output_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Output format
        format_frame = ttk.Frame(output_frame)
        format_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(format_frame, text="Định Dạng Âm Thanh:").pack(side=tk.LEFT)
        
        self.format_var = tk.StringVar(value="mp3")
        self.format_combobox = ttk.Combobox(
            format_frame,
            textvariable=self.format_var,
            values=["mp3", "wav", "ogg"],
            state="readonly",
            width=10
        )
        self.format_combobox.pack(side=tk.RIGHT)
        
        # UI Settings
        ui_frame = ttk.LabelFrame(main_frame, text="Tùy Chọn Giao Diện", padding=10)
        ui_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Language
        lang_frame = ttk.Frame(ui_frame)
        lang_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(lang_frame, text="Ngôn Ngữ:").pack(side=tk.LEFT)
        
        self.lang_var = tk.StringVar(value="vi")
        self.lang_combobox = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_var,
            values=["vi", "en"],
            state="readonly",
            width=10
        )
        self.lang_combobox.pack(side=tk.RIGHT)
        
        # Theme
        theme_frame = ttk.Frame(ui_frame)
        theme_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(theme_frame, text="Giao Diện:").pack(side=tk.LEFT)
        
        self.theme_var = tk.StringVar(value="default")
        self.theme_combobox = ttk.Combobox(
            theme_frame,
            textvariable=self.theme_var,
            values=["default", "light", "dark"],
            state="readonly",
            width=10
        )
        self.theme_combobox.pack(side=tk.RIGHT)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.save_btn = ttk.Button(
            btn_frame,
            text="Lưu Cài Đặt",
            command=self._save_settings
        )
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.reset_btn = ttk.Button(
            btn_frame,
            text="Đặt Lại Mặc Định",
            command=self._reset_settings
        )
        self.reset_btn.pack(side=tk.LEFT, padx=5)
    
    def _update_stability_label(self, *args):
        """Update the stability value label"""
        self.stability_label.config(text=f"{self.stability_var.get():.1f}")
    
    def _update_similarity_label(self, *args):
        """Update the similarity value label"""
        self.similarity_label.config(text=f"{self.similarity_var.get():.1f}")
    
    def _load_settings(self):
        """Load settings from config"""
        # TTS settings
        self.chunk_size_var.set(self.config.get("chunk_size", 5000))
        self.stability_var.set(self.config.get("stability", 0.5))
        self.similarity_var.set(self.config.get("similarity_boost", 0.5))
        
        # Output settings
        self.format_var.set(self.config.get("output_format", "mp3"))
        
        # UI settings
        self.lang_var.set(self.config.get("language", "vi"))
        self.theme_var.set(self.config.get("theme", "default"))
    
    def _save_settings(self):
        """Save settings to config"""
        # Validate settings
        try:
            chunk_size = int(self.chunk_size_var.get())
            if chunk_size < 1000 or chunk_size > 10000:
                raise ValueError("Kích thước phân đoạn phải từ 1000 đến 10000")
        except:
            messagebox.showerror("Lỗi", "Kích thước phân đoạn không hợp lệ")
            return
        
        # Update config
        settings = {
            # TTS settings
            "chunk_size": chunk_size,
            "stability": self.stability_var.get(),
            "similarity_boost": self.similarity_var.get(),
            
            # Output settings
            "output_format": self.format_var.get(),
            
            # UI settings
            "language": self.lang_var.get(),
            "theme": self.theme_var.get()
        }
        
        # Save to config
        self.config.update(settings)
        
        self.logger.success("Đã lưu cài đặt")
        messagebox.showinfo("Thành Công", "Đã lưu cài đặt")
    
    def _reset_settings(self):
        """Reset settings to defaults"""
        confirm = messagebox.askyesno(
            "Xác Nhận", 
            "Bạn có chắc chắn muốn đặt lại tất cả cài đặt về mặc định không?"
        )
        
        if confirm:
            # Reset config
            self.config.settings = self.config.DEFAULT_CONFIG.copy()
            self.config.save_config()
            
            # Reload settings
            self._load_settings()
            
            self.logger.info("Đã đặt lại cài đặt về mặc định")
            messagebox.showinfo("Thành Công", "Đã đặt lại cài đặt về mặc định") 