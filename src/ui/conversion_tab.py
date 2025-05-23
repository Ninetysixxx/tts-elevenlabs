#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Conversion Tab
UI tab for basic text-to-speech conversion
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Dict, List, Any, Optional, Callable
import datetime

from src.api.elevenlabs_client import ElevenLabsClient
from src.utils.api_key_manager import ApiKeyManager
from src.utils.logger import Logger
from src.models.config import AppConfig
from src.utils.text_processor import TextProcessor

class ConversionTab:
    """Tab for basic text-to-speech conversion"""
    
    def __init__(self, parent, api_client, api_key_manager, logger, config):
        """Initialize the conversion tab"""
        self.parent = parent
        self.api_client = api_client
        self.api_key_manager = api_key_manager
        self.logger = logger
        self.config = config
        self.text_processor = TextProcessor(
            max_chunk_size=config.get("chunk_size", 5000)
        )
        
        # Create the tab frame
        self.frame = ttk.Frame(parent)
        self._setup_ui()
        
        # Initialize voice list
        self.voices = []
        self.voice_names = []
        self.refresh_voices()
    
    def _setup_ui(self):
        """Set up the UI components"""
        # Main layout with two columns
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left column (API Key, File Selection)
        left_frame = ttk.LabelFrame(main_frame, text="Thiết lập", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # API Key Info
        api_frame = ttk.Frame(left_frame)
        api_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(api_frame, text="Khóa API Hiện Tại:").pack(anchor=tk.W)
        
        api_key_frame = ttk.Frame(api_frame)
        api_key_frame.pack(fill=tk.X, pady=5)
        
        self.api_key_var = tk.StringVar()
        self.api_key_combobox = ttk.Combobox(
            api_key_frame, 
            textvariable=self.api_key_var,
            state="readonly"
        )
        self.api_key_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.validate_btn = ttk.Button(
            api_key_frame, 
            text="Xác Thực Khóa",
            command=self._validate_api_key
        )
        self.validate_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Credits info
        self.credits_frame = ttk.Frame(api_frame)
        self.credits_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.credits_frame, text="Credits:").pack(side=tk.LEFT)
        self.credits_label = ttk.Label(self.credits_frame, text="0 / 0")
        self.credits_label.pack(side=tk.LEFT, padx=(5, 0))
        
        self.total_credits_label = ttk.Label(self.credits_frame, text="Tổng credits khả dụng: 0")
        self.total_credits_label.pack(side=tk.RIGHT)
        
        # File selection
        file_frame = ttk.Frame(left_frame)
        file_frame.pack(fill=tk.X, pady=10)
        
        # Add radio buttons for input type selection
        self.input_type_var = tk.StringVar(value="file")
        input_type_frame = ttk.Frame(file_frame)
        input_type_frame.pack(fill=tk.X, pady=5)
        
        ttk.Radiobutton(
            input_type_frame,
            text="Chọn File",
            variable=self.input_type_var,
            value="file",
            command=self._toggle_input_type
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Radiobutton(
            input_type_frame,
            text="Nhập Trực Tiếp",
            variable=self.input_type_var,
            value="text",
            command=self._toggle_input_type
        ).pack(side=tk.LEFT)
        
        # File selection frame
        self.file_selection_frame = ttk.Frame(file_frame)
        self.file_selection_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.file_selection_frame, text="Tệp Văn Bản Đầu Vào:").pack(anchor=tk.W)
        
        input_file_frame = ttk.Frame(self.file_selection_frame)
        input_file_frame.pack(fill=tk.X, pady=5)
        
        self.input_file_var = tk.StringVar()
        self.input_file_entry = ttk.Entry(
            input_file_frame, 
            textvariable=self.input_file_var
        )
        self.input_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.browse_input_btn = ttk.Button(
            input_file_frame, 
            text="Duyệt",
            command=self._browse_input_file
        )
        self.browse_input_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Word count display for file
        self.word_count_frame = ttk.Frame(self.file_selection_frame)
        self.word_count_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.word_count_frame, text="Số từ:").pack(side=tk.LEFT)
        self.word_count_label = ttk.Label(self.word_count_frame, text="0")
        self.word_count_label.pack(side=tk.LEFT, padx=(5, 0))
        
        self.count_words_btn = ttk.Button(
            self.word_count_frame,
            text="Đếm Từ",
            command=self._count_words
        )
        self.count_words_btn.pack(side=tk.RIGHT)
        
        # Text input frame
        self.text_input_frame = ttk.Frame(file_frame)
        
        ttk.Label(self.text_input_frame, text="Nhập Văn Bản:").pack(anchor=tk.W)
        
        # Text input with scrollbar
        text_scroll_frame = ttk.Frame(self.text_input_frame)
        text_scroll_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.input_text_var = tk.Text(
            text_scroll_frame,
            height=10,
            wrap=tk.WORD
        )
        self.input_text_var.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        text_scrollbar = ttk.Scrollbar(text_scroll_frame, command=self.input_text_var.yview)
        text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.input_text_var.config(yscrollcommand=text_scrollbar.set)
        
        # Word count for text input
        self.text_word_count_frame = ttk.Frame(self.text_input_frame)
        self.text_word_count_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.text_word_count_frame, text="Số từ:").pack(side=tk.LEFT)
        self.text_word_count_label = ttk.Label(self.text_word_count_frame, text="0")
        self.text_word_count_label.pack(side=tk.LEFT, padx=(5, 0))
        
        self.count_text_words_btn = ttk.Button(
            self.text_word_count_frame,
            text="Đếm Từ",
            command=self._count_text_words
        )
        self.count_text_words_btn.pack(side=tk.RIGHT)
        
        # Show default input type on startup
        self._toggle_input_type()
        
        # Output directory
        output_frame = ttk.Frame(left_frame)
        output_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(output_frame, text="Thư Mục Đầu Ra:").pack(anchor=tk.W)
        
        output_dir_frame = ttk.Frame(output_frame)
        output_dir_frame.pack(fill=tk.X, pady=5)
        
        self.output_dir_var = tk.StringVar()
        if self.config.get("output_directory"):
            self.output_dir_var.set(self.config.get("output_directory"))
        
        self.output_dir_entry = ttk.Entry(
            output_dir_frame, 
            textvariable=self.output_dir_var
        )
        self.output_dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.browse_output_btn = ttk.Button(
            output_dir_frame, 
            text="Duyệt",
            command=self._browse_output_dir
        )
        self.browse_output_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Right column (Voice Selection, Log)
        right_frame = ttk.LabelFrame(main_frame, text="Tùy Chọn Giọng Nói", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Voice selection
        voice_frame = ttk.Frame(right_frame)
        voice_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(voice_frame, text="Chọn Giọng Nói:").pack(anchor=tk.W)
        
        # Tạo frame để chứa combobox và nút preview
        voice_select_frame = ttk.Frame(voice_frame)
        voice_select_frame.pack(fill=tk.X, pady=5)
        
        self.voice_var = tk.StringVar()
        self.voice_combobox = ttk.Combobox(
            voice_select_frame, 
            textvariable=self.voice_var,
            state="readonly"
        )
        self.voice_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Thêm nút preview bên cạnh combobox
        self.preview_voice_btn = ttk.Button(
            voice_select_frame,
            text="Nghe thử",
            command=self._preview_voice
        )
        self.preview_voice_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Kết nối sự kiện khi thay đổi giá trị của combobox
        self.voice_combobox.bind("<<ComboboxSelected>>", self._on_voice_selected)
        
        # Thêm tùy chọn nhập ID voice
        custom_voice_frame = ttk.Frame(voice_frame)
        custom_voice_frame.pack(fill=tk.X, pady=5)
        
        self.use_custom_voice_id = tk.BooleanVar(value=False)
        self.custom_voice_checkbox = ttk.Checkbutton(
            custom_voice_frame,
            text="Sử dụng Voice ID tùy chọn",
            variable=self.use_custom_voice_id,
            command=self._toggle_custom_voice_id
        )
        self.custom_voice_checkbox.pack(anchor=tk.W)
        
        self.custom_voice_id_frame = ttk.Frame(voice_frame)
        self.custom_voice_id_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.custom_voice_id_frame, text="Voice ID:").pack(side=tk.LEFT)
        self.custom_voice_id_var = tk.StringVar()
        self.custom_voice_id_entry = ttk.Entry(
            self.custom_voice_id_frame,
            textvariable=self.custom_voice_id_var
        )
        self.custom_voice_id_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Thêm nút nghe thử cho Voice ID tùy chọn
        self.preview_custom_voice_btn = ttk.Button(
            self.custom_voice_id_frame,
            text="Nghe thử",
            command=self._preview_voice
        )
        self.preview_custom_voice_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Ẩn frame nhập Voice ID tùy chọn mặc định
        self.custom_voice_id_frame.pack_forget()
        
        # Model selection
        model_frame = ttk.Frame(right_frame)
        model_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(model_frame, text="Chọn Mô Hình:").pack(anchor=tk.W)
        
        self.model_var = tk.StringVar(value="eleven_turbo_v2")
        self.model_combobox = ttk.Combobox(
            model_frame, 
            textvariable=self.model_var,
            values=["eleven_turbo_v2", "eleven_monolingual_v1"],
            state="readonly"
        )
        self.model_combobox.pack(fill=tk.X, pady=5)
        
        # Advanced options
        advanced_frame = ttk.LabelFrame(right_frame, text="Tùy Chọn Nâng Cao")
        advanced_frame.pack(fill=tk.X, pady=10)
        
        # Stability
        stability_frame = ttk.Frame(advanced_frame)
        stability_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(stability_frame, text="Độ Ổn Định:").pack(side=tk.LEFT)
        
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
        similarity_frame = ttk.Frame(advanced_frame)
        similarity_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(similarity_frame, text="Độ Tương Đồng:").pack(side=tk.LEFT)
        
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
        
        # Activity log
        log_frame = ttk.LabelFrame(self.frame, text="Nhật Ký Hoạt Động")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        self.log_text = tk.Text(log_frame, height=6, wrap=tk.WORD)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        log_scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=log_scrollbar.set)
        
        # Register log callback
        self.logger.add_callback(self._on_log_entry)
        
        # Conversion button
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.convert_btn = ttk.Button(
            btn_frame,
            text="Bắt Đầu Chuyển Đổi",
            command=self._start_conversion
        )
        self.convert_btn.pack(side=tk.LEFT, padx=5)
        
        self.refresh_btn = ttk.Button(
            btn_frame,
            text="Cập Nhật Credits",
            command=self._refresh_credits
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Initialize API key dropdown
        self._update_api_key_dropdown()
    
    def _update_api_key_dropdown(self):
        """Update the API key dropdown with available keys"""
        key_names = self.api_key_manager.get_key_names()
        
        if key_names:
            self.api_key_combobox["values"] = key_names
            
            # Set current key if available
            if self.api_key_manager.current_key in key_names:
                self.api_key_var.set(self.api_key_manager.current_key)
            else:
                self.api_key_var.set(key_names[0])
                
            # Refresh the combobox
            self.api_key_combobox.update()
        else:
            self.api_key_combobox["values"] = []
            self.api_key_var.set("")
    
    def _update_stability_label(self, *args):
        """Update the stability value label"""
        self.stability_label.config(text=f"{self.stability_var.get():.1f}")
    
    def _update_similarity_label(self, *args):
        """Update the similarity value label"""
        self.similarity_label.config(text=f"{self.similarity_var.get():.1f}")
    
    def update_api_client(self, api_client):
        """Update the API client reference"""
        self.api_client = api_client
    
    def refresh_voices(self):
        """Refresh the list of available voices"""
        if not self.api_client:
            return
        
        def fetch_voices():
            # Get voices in background thread
            voices = self.api_client.get_available_voices()
            
            # Update UI in main thread
            self.parent.after(0, lambda: self._update_voices(voices))
        
        # Start background thread
        threading.Thread(target=fetch_voices, daemon=True).start()
    
    def _update_voices(self, voices):
        """Update the voice dropdown with available voices"""
        self.voices = voices
        self.voice_names = [voice["name"] for voice in voices]
        
        if self.voice_names:
            self.voice_combobox["values"] = self.voice_names
            
            # Set default voice
            default_voice = self.config.get("default_voice", "")
            if default_voice and default_voice in self.voice_names:
                self.voice_var.set(default_voice)
            else:
                self.voice_var.set(self.voice_names[0])
    
    def _validate_api_key(self):
        """Validate the current API key"""
        # Get selected API key
        key_name = self.api_key_var.get()
        if not key_name:
            messagebox.showerror("Lỗi", "Vui lòng chọn một API key")
            return
        
        # Set as current key
        api_key = self.api_key_manager.get_key(key_name)
        self.api_key_manager.set_current_key(key_name)
        
        # Create new client and validate
        self.api_client = ElevenLabsClient(api_key)
        
        self.logger.info(f"Đang kiểm tra khóa API: {key_name[:4]}{'*' * 4}")
        
        def validate_key():
            valid, data = self.api_client.validate_api_key()
            
            # Update UI in main thread
            self.parent.after(0, lambda: self._update_validation_result(valid, data))
        
        # Start validation in background
        threading.Thread(target=validate_key, daemon=True).start()
    
    def _update_validation_result(self, valid, data):
        """Update UI with validation result"""
        if valid:
            # Extract credit information
            subscription = data.get("subscription", {})
            
            # Try to get character limit first (tổng số credits)
            character_limit = subscription.get("character_limit", 0)
            
            # Trường hợp ElevenLabs API trả về character_count là số đã dùng
            character_used = subscription.get("character_count", 0)
            
            # Tính số credits còn lại (remaining)
            character_remaining = character_limit - character_used
            
            # Nếu không tìm thấy trong subscription, thử trong data chính
            if character_limit == 0:
                character_limit = data.get("character_limit", 0)
                character_used = data.get("character_count", 0)
                character_remaining = character_limit - character_used
            
            # Cập nhật UI hiển thị số còn lại / tổng số
            self.credits_label.config(text=f"{character_remaining:,} / {character_limit:,}")
            self.total_credits_label.config(text=f"Tổng credits khả dụng: {character_remaining:,}")
            
            # Get tier information
            tier = subscription.get('tier', 'Tài khoản Free')
            
            self.logger.success(f"Đã xác thực khóa API hợp lệ: {tier}")
            self.logger.info(f"Khóa API này có {character_remaining:,} / {character_limit:,} credits")
            
            # Refresh voices
            self.refresh_voices()
        else:
            error_msg = data.get("error", "Lỗi không xác định")
            self.logger.error(f"Lỗi xác thực API key: {error_msg}")
            messagebox.showerror("Lỗi API Key", f"API key không hợp lệ: {error_msg}")
    
    def _refresh_credits(self):
        """Refresh credit information"""
        if not self.api_client:
            messagebox.showerror("Lỗi", "Không có API client. Vui lòng chọn một API key.")
            return
        
        self.logger.info("Đang kiểm tra thông tin credits...")
        
        def get_user_info():
            # Get individual API key info
            info = self.api_client.get_user_info()
            
            # Get total credits from all keys
            total_credits = self.api_key_manager.get_total_credits(self.api_client)
            
            # Update UI in main thread
            self.parent.after(0, lambda: self._update_credit_info(info, total_credits))
        
        # Start in background
        threading.Thread(target=get_user_info, daemon=True).start()
    
    def _update_credit_info(self, info, total_credits=None):
        """Update credit information in UI"""
        if "error" in info:
            self.logger.error(f"Lỗi lấy thông tin credits: {info['error']}")
            return
        
        # Extract credit information from various possible locations
        subscription = info.get("subscription", {})
        
        # Trường hợp ElevenLabs API trả về character_count là số đã dùng
        character_limit = subscription.get("character_limit", 0)
        character_used = subscription.get("character_count", 0)
        
        # Tính số credits còn lại (remaining)
        character_remaining = character_limit - character_used
        
        # Nếu không tìm thấy trong subscription, thử trong dữ liệu chính
        if character_limit == 0:
            character_limit = info.get("character_limit", 0)
            character_used = info.get("character_count", 0)
            character_remaining = character_limit - character_used
        
        # Update UI với số còn lại / tổng số
        self.credits_label.config(text=f"{character_remaining:,} / {character_limit:,}")
        
        # Update total credits if provided
        if total_credits:
            total_remaining = total_credits.get("total_remaining", 0)
            unique_keys = total_credits.get("unique_keys", 0)
            duplicates = total_credits.get("duplicates", 0)
            
            # Update total credits display
            if unique_keys > 0:
                self.total_credits_label.config(
                    text=f"Tổng credits khả dụng: {total_remaining:,} ({unique_keys} khóa khả dụng)"
                )
                
                # Log detailed information
                self.logger.info(f"Tổng credits khả dụng: {total_remaining:,} từ {unique_keys} khóa API khả dụng")
                if duplicates > 0:
                    self.logger.info(f"Đã phát hiện {duplicates} khóa trùng lặp và đã loại bỏ khỏi tổng số")
            else:
                self.total_credits_label.config(text=f"Tổng credits khả dụng: {character_remaining:,}")
        else:
            self.total_credits_label.config(text=f"Tổng credits khả dụng: {character_remaining:,}")
        
        self.logger.info(f"Cập nhật thông tin tài khoản thành công")
        self.logger.info(f"Tài khoản còn {character_remaining:,} / {character_limit:,} credits")
    
    def _browse_input_file(self):
        """Browse for input text file"""
        filetypes = [
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Chọn tệp văn bản",
            filetypes=filetypes
        )
        
        if filename:
            self.input_file_var.set(filename)
            
            # Auto-suggest output directory if not set
            if not self.output_dir_var.get():
                self.output_dir_var.set(os.path.dirname(filename))
                self.config.set("output_directory", os.path.dirname(filename))
    
    def _browse_output_dir(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(
            title="Chọn thư mục đầu ra"
        )
        
        if directory:
            self.output_dir_var.set(directory)
            self.config.set("output_directory", directory)
    
    def _on_log_entry(self, message, level):
        """Handle new log entry and update log text widget"""
        # Format the log entry
        tag = level.lower()
        
        # Add to text widget
        self.log_text.insert(tk.END, message + "\n", (tag,))
        self.log_text.see(tk.END)
        
        # Configure tags for different levels
        if level == "ERROR":
            self.log_text.tag_configure(tag, foreground="red")
        elif level == "WARNING":
            self.log_text.tag_configure(tag, foreground="orange")
        elif level == "SUCCESS":
            self.log_text.tag_configure(tag, foreground="green")
    
    def _toggle_input_type(self):
        """Toggle between file selection and text input"""
        input_type = self.input_type_var.get()
        
        if input_type == "file":
            # Show file selection, hide text input
            self.file_selection_frame.pack(fill=tk.X, pady=5)
            if self.text_input_frame.winfo_manager():
                self.text_input_frame.pack_forget()
        else:
            # Show text input, hide file selection
            if self.file_selection_frame.winfo_manager():
                self.file_selection_frame.pack_forget()
            self.text_input_frame.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def _count_words(self):
        """Count words in the selected file"""
        input_file = self.input_file_var.get()
        if not input_file or not os.path.exists(input_file):
            messagebox.showerror("Lỗi", "Vui lòng chọn tệp văn bản đầu vào hợp lệ.")
            return
        
        try:
            # Read the file content
            text = self.text_processor.read_text_file(input_file)
            
            # Count words
            word_count = len(text.split())
            
            # Update the word count label
            self.word_count_label.config(text=f"{word_count:,}")
            
            self.logger.info(f"Tệp '{os.path.basename(input_file)}' có {word_count:,} từ.")
        except Exception as e:
            self.logger.error(f"Lỗi đếm từ: {str(e)}")
            messagebox.showerror("Lỗi", f"Không thể đếm từ: {str(e)}")
    
    def _count_text_words(self):
        """Count words in the text input"""
        # Get text from the text input
        text = self.input_text_var.get("1.0", tk.END).strip()
        
        # Count words
        word_count = len(text.split())
        
        # Update the word count label
        self.text_word_count_label.config(text=f"{word_count:,}")
        
        self.logger.info(f"Văn bản nhập có {word_count:,} từ.")
    
    def _start_conversion(self):
        """Start the conversion process"""
        # Check if we have an API client
        if not self.api_client:
            messagebox.showerror("Lỗi", "Không có API client. Vui lòng chọn một API key.")
            return
        
        # Get input type
        input_type = self.input_type_var.get()
        
        # Check output directory
        output_dir = self.output_dir_var.get()
        if not output_dir or not os.path.exists(output_dir):
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục đầu ra hợp lệ.")
            return
        
        # Check voice selection
        voice_id = None
        
        # Kiểm tra nếu sử dụng voice ID tùy chọn
        if self.use_custom_voice_id.get():
            voice_id = self.custom_voice_id_var.get().strip()
            if not voice_id:
                messagebox.showerror("Lỗi", "Vui lòng nhập Voice ID tùy chọn.")
                return
            self.logger.info(f"Sử dụng Voice ID tùy chọn: {voice_id}")
        else:
            # Lấy voice ID từ danh sách có sẵn
            voice_name = self.voice_var.get()
            if not voice_name:
                messagebox.showerror("Lỗi", "Vui lòng chọn giọng nói.")
                return
            
            # Find voice ID
            for voice in self.voices:
                if voice["name"] == voice_name:
                    voice_id = voice["voice_id"]
                    break
            
            if not voice_id:
                messagebox.showerror("Lỗi", "Không tìm thấy ID giọng nói. Vui lòng làm mới danh sách.")
                return
        
        # Get text chunks for conversion
        text_chunks = []
        input_file = None  # Only used for file input
        output_filename = ""
        
        if input_type == "file":
            # Check input file
            input_file = self.input_file_var.get()
            if not input_file or not os.path.exists(input_file):
                messagebox.showerror("Lỗi", "Vui lòng chọn tệp văn bản đầu vào hợp lệ.")
                return
                
            # Read text from file
            try:
                # Process text file
                self.logger.info("Đang đọc tệp văn bản...")
                text_chunks = self.text_processor.process_file(input_file)
                
                if not text_chunks:
                    messagebox.showerror("Lỗi", "Tệp văn bản trống hoặc không thể đọc.")
                    return
                    
                # Generate output filename from input file
                input_filename = os.path.basename(input_file)
                output_filename = os.path.splitext(input_filename)[0] + ".mp3"
                
                self.logger.info(f"Đã chia tệp thành {len(text_chunks)} phần")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đọc tệp: {str(e)}")
                return
        else:
            # Get text from input text box
            text_content = self.input_text_var.get("1.0", tk.END).strip()
            
            if not text_content:
                messagebox.showerror("Lỗi", "Vui lòng nhập văn bản để chuyển đổi.")
                return
                
            # Process text content
            processed_text = self.text_processor.preprocess_text(text_content)
            text_chunks = self.text_processor.split_into_chunks(processed_text)
            
            if not text_chunks:
                messagebox.showerror("Lỗi", "Không thể xử lý văn bản đã nhập.")
                return
            
            # Generate a default output filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"text_to_speech_{timestamp}.mp3"
            
            self.logger.info(f"Đã chia văn bản nhập thành {len(text_chunks)} phần")
        
        # Create full output path
        output_file = os.path.join(output_dir, output_filename)
        
        # Disable the convert button
        self.convert_btn.config(state="disabled")
        
        # Start conversion in background
        if input_type == "file":
            self.logger.info(f"Bắt đầu chuyển đổi tệp: {input_file}")
        else:
            self.logger.info(f"Bắt đầu chuyển đổi văn bản đã nhập ({len(''.join(text_chunks))} ký tự)")
        
        def convert():
            try:
                # Get conversion parameters
                model_id = self.model_var.get()
                stability = self.stability_var.get()
                similarity = self.similarity_var.get()
                
                # Convert each chunk
                if len(text_chunks) == 1:
                    # Single chunk - direct conversion
                    self.logger.info("Đang chuyển đổi văn bản thành âm thanh...")
                    success, result = self.api_client.text_to_speech(
                        text=text_chunks[0],
                        voice_id=voice_id,
                        model_id=model_id,
                        stability=stability,
                        similarity_boost=similarity,
                        output_path=output_file
                    )
                    
                    if success:
                        self.parent.after(0, lambda: self._conversion_success(output_file))
                    else:
                        self.parent.after(0, lambda: self._conversion_error(result))
                else:
                    # Multiple chunks - create temp files and combine
                    temp_files = []
                    
                    for i, chunk in enumerate(text_chunks):
                        # Create temp filename
                        temp_file = os.path.join(
                            output_dir, 
                            f"{os.path.splitext(input_filename)[0]}_part{i+1}.mp3"
                        )
                        
                        self.logger.info(f"Đang chuyển đổi phần {i+1}/{len(text_chunks)}...")
                        
                        success, result = self.api_client.text_to_speech(
                            text=chunk,
                            voice_id=voice_id,
                            model_id=model_id,
                            stability=stability,
                            similarity_boost=similarity,
                            output_path=temp_file
                        )
                        
                        if not success:
                            self.parent.after(0, lambda: self._conversion_error(
                                f"Lỗi khi chuyển đổi phần {i+1}: {result}"
                            ))
                            return
                        
                        temp_files.append(temp_file)
                    
                    # TODO: Combine audio files
                    # For now, we'll just use the first part
                    self.parent.after(0, lambda: self._conversion_success(
                        temp_files[0], 
                        message=f"Đã tạo {len(temp_files)} tệp âm thanh riêng biệt. Chức năng kết hợp sẽ được phát triển sau."
                    ))
            
            except Exception as e:
                self.parent.after(0, lambda: self._conversion_error(str(e)))
        
        # Start conversion thread
        threading.Thread(target=convert, daemon=True).start()
    
    def _conversion_success(self, output_file, message=None):
        """Handle successful conversion"""
        self.logger.success(f"Chuyển đổi thành công: {output_file}")
        
        if message:
            self.logger.info(message)
        
        messagebox.showinfo("Thành công", f"Đã chuyển đổi thành công.\nTệp đầu ra: {output_file}")
        
        # Re-enable convert button
        self.convert_btn.config(state="normal")
        
        # Cập nhật số credits sau khi chuyển đổi thành công
        self.logger.info("Đang cập nhật số credits sau khi chuyển đổi...")
        
        # Gọi cập nhật nhanh local
        self._refresh_credits()
        
        # Gọi cập nhật toàn cục
        try:
            # Tìm ứng dụng chính và gọi hàm cập nhật
            app = self.parent.master
            if hasattr(app, 'update_credits'):
                app.update_credits()
        except:
            pass
    
    def _conversion_error(self, error_message):
        """Handle conversion error"""
        self.logger.error(f"Lỗi chuyển đổi: {error_message}")
        messagebox.showerror("Lỗi Chuyển Đổi", f"Lỗi: {error_message}")
        
        # Re-enable convert button
        self.convert_btn.config(state="normal")
    
    def _preview_voice(self):
        """Preview selected voice"""
        # Check if we have an API client
        if not self.api_client:
            messagebox.showerror("Lỗi", "Không có API client. Vui lòng chọn một API key.")
            return
        
        # Get voice ID
        voice_id = None
        
        # Kiểm tra nếu sử dụng voice ID tùy chọn
        if self.use_custom_voice_id.get():
            voice_id = self.custom_voice_id_var.get().strip()
            if not voice_id:
                messagebox.showerror("Lỗi", "Vui lòng nhập Voice ID tùy chọn.")
                return
            self.logger.info(f"Đang nghe thử Voice ID tùy chọn: {voice_id}")
            # Disable custom preview button
            self.preview_custom_voice_btn.config(state="disabled", text="Đang tải...")
        else:
            # Lấy voice ID từ danh sách có sẵn
            voice_name = self.voice_var.get()
            if not voice_name:
                messagebox.showerror("Lỗi", "Vui lòng chọn giọng nói.")
                return
            
            # Find voice ID
            for voice in self.voices:
                if voice["name"] == voice_name:
                    voice_id = voice["voice_id"]
                    break
            
            if not voice_id:
                messagebox.showerror("Lỗi", "Không tìm thấy ID giọng nói. Vui lòng làm mới danh sách.")
                return
            
            # Disable standard preview button
            self.preview_voice_btn.config(state="disabled", text="Đang tải...")
        
        # Start preview in background
        def preview():
            try:
                # Get sample audio
                audio_data = self.api_client.get_voice_audio(voice_id)
                
                if audio_data:
                    # Play in main thread
                    self.parent.after(0, lambda: self._play_audio(audio_data))
                else:
                    # Show error in main thread
                    self.parent.after(0, lambda: self._preview_error("Không thể lấy mẫu giọng nói"))
            except Exception as e:
                # Show error in main thread
                self.parent.after(0, lambda: self._preview_error(str(e)))
            finally:
                # Reset button state in main thread
                self.parent.after(0, self._reset_preview_buttons)
        
        # Start preview thread
        threading.Thread(target=preview, daemon=True).start()
    
    def _reset_preview_buttons(self):
        """Reset preview buttons to default state"""
        self.preview_voice_btn.config(state="normal", text="Nghe thử")
        self.preview_custom_voice_btn.config(state="normal", text="Nghe thử")
    
    def _play_audio(self, audio_data):
        """Handle playing audio"""
        try:
            import tempfile
            import pygame
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            # Initialize pygame mixer
            pygame.mixer.init()
            pygame.mixer.music.load(temp_file_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            # Cleanup
            pygame.mixer.quit()
            
            # Delete temp file
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
            self.logger.info("Phát mẫu giọng nói thành công")
        except Exception as e:
            self.logger.error(f"Lỗi khi phát audio: {str(e)}")
            messagebox.showerror("Lỗi", f"Không thể phát audio: {str(e)}")
    
    def _preview_error(self, error_message):
        """Handle preview error"""
        self.logger.error(f"Lỗi khi nghe thử: {error_message}")
        messagebox.showerror("Lỗi", f"Không thể nghe thử giọng: {error_message}")
    
    def _on_voice_selected(self, event):
        """Handle voice selection"""
        # Ghi log giọng nói đã chọn
        self.logger.info(f"Đã chọn giọng nói: {self.voice_var.get()}")
        
        # Lưu vào cấu hình mặc định
        self.config.set("default_voice", self.voice_var.get())
    
    def _toggle_custom_voice_id(self):
        """Toggle custom voice ID"""
        if self.use_custom_voice_id.get():
            self.custom_voice_id_frame.pack(fill=tk.X, pady=5)
        else:
            self.custom_voice_id_frame.pack_forget() 