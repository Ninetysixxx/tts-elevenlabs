#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Batch Processing Tab
UI tab for batch processing multiple files
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Dict, Any, Optional
import threading

from src.api.elevenlabs_client import ElevenLabsClient
from src.models.batch_processor import BatchProcessor, BatchItem, BatchItemStatus
from src.utils.logger import Logger
from src.models.config import AppConfig
from src.utils.text_processor import TextProcessor

class BatchTab:
    """Tab for batch processing multiple files"""
    
    def __init__(self, parent, api_client, logger, config):
        """Initialize the batch tab"""
        self.parent = parent
        self.api_client = api_client
        self.logger = logger
        self.config = config
        self.text_processor = TextProcessor(
            max_chunk_size=config.get("chunk_size", 5000)
        )
        
        # Create batch processor
        self.batch_processor = BatchProcessor()
        self.batch_processor.set_processor(self._process_batch_item)
        self.batch_processor.set_callbacks(
            on_item_status_changed=self._on_item_status_changed,
            on_batch_completed=self._on_batch_completed
        )
        
        # Create the tab frame
        self.frame = ttk.Frame(parent)
        self._setup_ui()
        
        # Voice data
        self.voices = []
        self.voice_names = []
    
    def _setup_ui(self):
        """Set up the UI components"""
        main_frame = ttk.Frame(self.frame, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel: File list and controls
        left_frame = ttk.LabelFrame(main_frame, text="Danh Sách Tệp")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # File list with scrollbar
        list_frame = ttk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ("input", "output", "status")
        self.file_treeview = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # Define headings
        self.file_treeview.heading("input", text="Tệp Đầu Vào")
        self.file_treeview.heading("output", text="Tệp Đầu Ra")
        self.file_treeview.heading("status", text="Trạng Thái")
        
        # Define column widths
        self.file_treeview.column("input", width=200)
        self.file_treeview.column("output", width=200)
        self.file_treeview.column("status", width=100)
        
        self.file_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        files_scrollbar = ttk.Scrollbar(list_frame, command=self.file_treeview.yview)
        files_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_treeview.config(yscrollcommand=files_scrollbar.set)
        
        # File list buttons
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.add_files_btn = ttk.Button(
            btn_frame,
            text="Thêm Tệp",
            command=self._add_files
        )
        self.add_files_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.remove_file_btn = ttk.Button(
            btn_frame,
            text="Xóa Tệp",
            command=self._remove_file
        )
        self.remove_file_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_files_btn = ttk.Button(
            btn_frame,
            text="Xóa Tất Cả",
            command=self._clear_files
        )
        self.clear_files_btn.pack(side=tk.LEFT, padx=5)
        
        # Right panel: Batch options
        right_frame = ttk.LabelFrame(main_frame, text="Tùy Chọn Xử Lý Hàng Loạt")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Batch options form
        form_frame = ttk.Frame(right_frame, padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Output directory
        output_frame = ttk.Frame(form_frame)
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
        
        # Voice selection
        voice_frame = ttk.Frame(form_frame)
        voice_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(voice_frame, text="Chọn Giọng Nói:").pack(anchor=tk.W)
        
        self.voice_var = tk.StringVar()
        self.voice_combobox = ttk.Combobox(
            voice_frame, 
            textvariable=self.voice_var,
            state="readonly"
        )
        self.voice_combobox.pack(fill=tk.X, pady=5)
        
        # Refresh voices button
        self.refresh_voices_btn = ttk.Button(
            voice_frame,
            text="Làm Mới Danh Sách Giọng Nói",
            command=self._refresh_voices
        )
        self.refresh_voices_btn.pack(pady=5)
        
        # Model selection
        model_frame = ttk.Frame(form_frame)
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
        
        # Batch progress
        progress_frame = ttk.LabelFrame(right_frame, text="Tiến Trình")
        progress_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            orient=tk.HORIZONTAL,
            length=100,
            mode='determinate',
            variable=self.progress_var
        )
        self.progress_bar.pack(fill=tk.X, pady=10, padx=10)
        
        self.status_label = ttk.Label(progress_frame, text="Sẵn sàng")
        self.status_label.pack(pady=(0, 10))
        
        # Control buttons
        control_frame = ttk.Frame(self.frame)
        control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.start_btn = ttk.Button(
            control_frame,
            text="Bắt Đầu Xử Lý",
            command=self._start_batch
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_btn = ttk.Button(
            control_frame,
            text="Tạm Dừng",
            command=self._pause_batch,
            state="disabled"
        )
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(
            control_frame,
            text="Dừng",
            command=self._stop_batch,
            state="disabled"
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Initialize voices
        self._refresh_voices()
    
    def update_api_client(self, api_client):
        """Update the API client reference"""
        self.api_client = api_client
        self._refresh_voices()
    
    def _refresh_voices(self):
        """Refresh the list of available voices"""
        if not self.api_client:
            messagebox.showerror("Lỗi", "Không có API client. Vui lòng cài đặt API key.")
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
    
    def _browse_output_dir(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(
            title="Chọn thư mục đầu ra"
        )
        
        if directory:
            self.output_dir_var.set(directory)
            self.config.set("output_directory", directory)
    
    def _add_files(self):
        """Add files to the batch"""
        filetypes = [
            ("Text files", "*.txt"),
            ("All files", "*.*")
        ]
        
        filenames = filedialog.askopenfilenames(
            title="Chọn các tệp văn bản",
            filetypes=filetypes
        )
        
        if not filenames:
            return
        
        # Get output directory
        output_dir = self.output_dir_var.get()
        if not output_dir:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục đầu ra trước.")
            return
        
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except:
                messagebox.showerror("Lỗi", f"Không thể tạo thư mục đầu ra: {output_dir}")
                return
        
        # Add files to list and batch processor
        for input_file in filenames:
            # Generate output filename
            basename = os.path.basename(input_file)
            output_file = os.path.join(output_dir, os.path.splitext(basename)[0] + ".mp3")
            
            # Add to batch processor
            item = self.batch_processor.add_item(input_file, output_file)
            
            # Add to treeview
            self.file_treeview.insert(
                "", 
                tk.END, 
                values=(
                    os.path.basename(input_file),
                    os.path.basename(output_file),
                    "Chờ xử lý"
                ),
                tags=(str(id(item)),)  # Use item id as tag for reference
            )
        
        self.logger.info(f"Đã thêm {len(filenames)} tệp vào hàng đợi xử lý")
    
    def _remove_file(self):
        """Remove a file from the batch"""
        selected = self.file_treeview.selection()
        if not selected:
            messagebox.showerror("Lỗi", "Vui lòng chọn một tệp để xóa")
            return
        
        # Get item values
        for item_id in selected:
            self.file_treeview.delete(item_id)
        
        # Currently we don't have a way to remove specific items from the batch processor
        # So we'll rebuild the batch from the treeview
        self._rebuild_batch_from_treeview()
    
    def _clear_files(self):
        """Clear all files from the batch"""
        if self.batch_processor.is_running:
            messagebox.showerror("Lỗi", "Không thể xóa danh sách khi đang xử lý")
            return
        
        # Clear treeview
        for item in self.file_treeview.get_children():
            self.file_treeview.delete(item)
        
        # Clear batch processor
        self.batch_processor.clear_all()
        
        self.logger.info("Đã xóa tất cả tệp khỏi hàng đợi xử lý")
    
    def _rebuild_batch_from_treeview(self):
        """Rebuild the batch processor items from treeview"""
        # Only if not running
        if self.batch_processor.is_running:
            return
        
        # Clear batch
        self.batch_processor.clear_all()
        
        # Add items from treeview
        for item_id in self.file_treeview.get_children():
            values = self.file_treeview.item(item_id, "values")
            
            # Get full paths
            input_file = os.path.join(
                os.path.dirname(self.output_dir_var.get()),
                values[0]
            )
            output_file = os.path.join(
                self.output_dir_var.get(),
                values[1]
            )
            
            # Add to batch
            item = self.batch_processor.add_item(input_file, output_file)
            
            # Update tag
            self.file_treeview.item(item_id, tags=(str(id(item)),))
    
    def _start_batch(self):
        """Start batch processing"""
        # Check if we have an API client
        if not self.api_client:
            messagebox.showerror("Lỗi", "Không có API client. Vui lòng cài đặt API key.")
            return
        
        # Check if we have files
        if not self.file_treeview.get_children():
            messagebox.showerror("Lỗi", "Không có tệp nào trong danh sách xử lý")
            return
        
        # Check voice selection
        voice_name = self.voice_var.get()
        if not voice_name:
            messagebox.showerror("Lỗi", "Vui lòng chọn giọng nói")
            return
        
        # Find voice ID
        voice_id = None
        for voice in self.voices:
            if voice["name"] == voice_name:
                voice_id = voice["voice_id"]
                break
        
        if not voice_id:
            messagebox.showerror("Lỗi", "Không tìm thấy ID giọng nói. Vui lòng làm mới danh sách.")
            return
        
        # Prepare options
        options = {
            "voice_id": voice_id,
            "model_id": self.model_var.get(),
            "stability": self.config.get("stability", 0.5),
            "similarity_boost": self.config.get("similarity_boost", 0.5)
        }
        
        # Update UI
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self.stop_btn.config(state="normal")
        self.add_files_btn.config(state="disabled")
        self.remove_file_btn.config(state="disabled")
        self.clear_files_btn.config(state="disabled")
        
        # Start batch processing
        self.batch_processor.start(options)
        self.logger.info("Bắt đầu xử lý hàng loạt")
        self.status_label.config(text="Đang xử lý...")
        
        # Start progress monitor
        self._update_progress()
    
    def _pause_batch(self):
        """Pause batch processing"""
        if self.batch_processor.is_paused:
            # Resume
            self.batch_processor.resume()
            self.pause_btn.config(text="Tạm Dừng")
            self.status_label.config(text="Đang xử lý...")
            self.logger.info("Tiếp tục xử lý hàng loạt")
        else:
            # Pause
            self.batch_processor.pause()
            self.pause_btn.config(text="Tiếp Tục")
            self.status_label.config(text="Đã tạm dừng")
            self.logger.info("Tạm dừng xử lý hàng loạt")
    
    def _stop_batch(self):
        """Stop batch processing"""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn dừng xử lý?"):
            self.batch_processor.cancel()
            self.logger.info("Đã dừng xử lý hàng loạt")
            self._update_ui_after_completion()
    
    def _update_progress(self):
        """Update progress bar and status"""
        if not self.batch_processor.is_running:
            return
        
        # Get batch stats
        stats = self.batch_processor.get_stats()
        
        # Calculate progress percentage
        if stats["total"] > 0:
            completed = stats["completed"] + stats["failed"] + stats["cancelled"]
            progress = int((completed / stats["total"]) * 100)
            self.progress_var.set(progress)
        
        # Update status text
        status_text = (
            f"Đã xử lý: {stats['completed']}/{stats['total']} | "
            f"Lỗi: {stats['failed']} | "
            f"Đang xử lý: {stats['processing']}"
        )
        self.status_label.config(text=status_text)
        
        # Schedule next update
        self.parent.after(500, self._update_progress)
    
    def _update_ui_after_completion(self):
        """Update UI after batch processing is complete"""
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        self.add_files_btn.config(state="normal")
        self.remove_file_btn.config(state="normal")
        self.clear_files_btn.config(state="normal")
        
        # Update status text
        stats = self.batch_processor.get_stats()
        status_text = (
            f"Hoàn thành: {stats['completed']}/{stats['total']} | "
            f"Lỗi: {stats['failed']} | "
            f"Đã hủy: {stats['cancelled']}"
        )
        self.status_label.config(text=status_text)
    
    def _process_batch_item(self, item: BatchItem, options: Dict[str, Any]) -> bool:
        """Process a single batch item"""
        try:
            # Extract options
            voice_id = options.get("voice_id")
            model_id = options.get("model_id", "eleven_turbo_v2")
            stability = options.get("stability", 0.5)
            similarity_boost = options.get("similarity_boost", 0.5)
            
            # Update item status
            item.message = "Đang đọc tệp..."
            
            # Process text file
            text_chunks = self.text_processor.process_file(item.input_file)
            
            if not text_chunks:
                item.message = "Tệp văn bản trống hoặc không thể đọc"
                return False
            
            # Single chunk processing
            if len(text_chunks) == 1:
                item.message = "Đang chuyển đổi văn bản thành âm thanh..."
                
                # Convert text to speech
                success, result = self.api_client.text_to_speech(
                    text=text_chunks[0],
                    voice_id=voice_id,
                    model_id=model_id,
                    stability=stability,
                    similarity_boost=similarity_boost,
                    output_path=item.output_file
                )
                
                if not success:
                    item.message = f"Lỗi: {result}"
                    return False
                
                item.message = "Hoàn thành"
                return True
            
            # Multiple chunks - need to combine
            item.message = f"Đang xử lý {len(text_chunks)} phần..."
            
            # Create temp files for each chunk
            temp_files = []
            
            for i, chunk in enumerate(text_chunks):
                # Update progress
                item.progress = int((i / len(text_chunks)) * 100)
                item.message = f"Đang chuyển đổi phần {i+1}/{len(text_chunks)}..."
                
                # Create temp filename
                temp_file = os.path.join(
                    os.path.dirname(item.output_file),
                    f"{os.path.splitext(os.path.basename(item.input_file))[0]}_part{i+1}.mp3"
                )
                
                # Convert chunk
                success, result = self.api_client.text_to_speech(
                    text=chunk,
                    voice_id=voice_id,
                    model_id=model_id,
                    stability=stability,
                    similarity_boost=similarity_boost,
                    output_path=temp_file
                )
                
                if not success:
                    item.message = f"Lỗi ở phần {i+1}: {result}"
                    return False
                
                temp_files.append(temp_file)
            
            # TODO: Combine audio files
            # For now, just use the first part as the result
            if temp_files:
                import shutil
                shutil.copy(temp_files[0], item.output_file)
            
            item.message = f"Hoàn thành ({len(temp_files)} phần)"
            return True
            
        except Exception as e:
            item.message = f"Lỗi: {str(e)}"
            return False
    
    def _on_item_status_changed(self, item: BatchItem):
        """Handle item status change event"""
        # Find matching item in treeview by tag
        item_tag = str(id(item))
        
        # Find item with matching tag
        for item_id in self.file_treeview.get_children():
            if item_tag in self.file_treeview.item(item_id, "tags"):
                # Update status in treeview
                status_text = ""
                
                if item.status == BatchItemStatus.PENDING:
                    status_text = "Chờ xử lý"
                elif item.status == BatchItemStatus.PROCESSING:
                    status_text = f"Đang xử lý ({item.progress}%)"
                elif item.status == BatchItemStatus.COMPLETED:
                    status_text = "Hoàn thành"
                    # Log success
                    self.logger.success(f"Đã xử lý thành công: {os.path.basename(item.input_file)}")
                elif item.status == BatchItemStatus.FAILED:
                    status_text = f"Lỗi: {item.message}"
                    # Log error
                    self.logger.error(f"Lỗi xử lý {os.path.basename(item.input_file)}: {item.message}")
                elif item.status == BatchItemStatus.CANCELLED:
                    status_text = "Đã hủy"
                
                self.file_treeview.item(
                    item_id, 
                    values=(
                        os.path.basename(item.input_file),
                        os.path.basename(item.output_file),
                        status_text
                    )
                )
                break
    
    def _on_batch_completed(self):
        """Handle batch completion event"""
        self.logger.info("Đã hoàn thành xử lý hàng loạt")
        
        # Update UI
        self._update_ui_after_completion()
        
        # Cập nhật số credits sau khi hoàn thành xử lý hàng loạt
        self._refresh_credits()
        
        # Gọi cập nhật toàn cục
        try:
            # Tìm ứng dụng chính và gọi hàm cập nhật
            app = self.parent.master
            if hasattr(app, 'update_credits'):
                app.update_credits()
        except:
            pass
        
        # Show message
        stats = self.batch_processor.get_stats()
        messagebox.showinfo(
            "Hoàn Thành",
            f"Đã hoàn thành xử lý hàng loạt:\n"
            f"- Thành công: {stats['completed']}\n"
            f"- Lỗi: {stats['failed']}\n"
            f"- Đã hủy: {stats['cancelled']}"
        )
    
    def _refresh_credits(self):
        """Refresh credit information after batch processing"""
        if not self.api_client:
            return
        
        self.logger.info("Đang cập nhật thông tin credits sau khi xử lý...")
        
        def get_user_info():
            info = self.api_client.get_user_info()
            
            # Update UI in main thread
            self.parent.after(0, lambda: self._update_credit_info(info))
        
        # Start in background
        threading.Thread(target=get_user_info, daemon=True).start()
    
    def _update_credit_info(self, info):
        """Update credit information in status bar"""
        if "error" in info:
            self.logger.error(f"Lỗi lấy thông tin credits: {info['error']}")
            return
        
        # Extract credit information
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
        
        # Log thông tin credits mới
        self.logger.info(f"Tài khoản còn {character_remaining:,} / {character_limit:,} credits sau khi xử lý")
    
    def stop_batch(self):
        """Stop batch processing - called externally"""
        if self.batch_processor.is_running:
            self.batch_processor.cancel() 