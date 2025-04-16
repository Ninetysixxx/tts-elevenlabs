#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Batch Processor for TTS Conversion
Handles processing multiple files in a queue
"""

import os
import threading
import time
from typing import List, Dict, Any, Callable, Optional
from enum import Enum
from queue import Queue

class BatchItemStatus(Enum):
    """Status of a batch item"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BatchItem:
    """Represents a single item in the batch queue"""
    
    def __init__(self, input_file: str, output_file: str):
        """Initialize a batch item"""
        self.input_file = input_file
        self.output_file = output_file
        self.status = BatchItemStatus.PENDING
        self.progress = 0
        self.message = ""
        self.error = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert batch item to dictionary"""
        return {
            "input_file": self.input_file,
            "output_file": self.output_file,
            "status": self.status.value,
            "progress": self.progress,
            "message": self.message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BatchItem':
        """Create a batch item from dictionary"""
        item = cls(data["input_file"], data["output_file"])
        item.status = BatchItemStatus(data["status"])
        item.progress = data["progress"]
        item.message = data["message"]
        return item

class BatchProcessor:
    """Processes a batch of TTS conversion tasks"""
    
    def __init__(self):
        """Initialize the batch processor"""
        self.items: List[BatchItem] = []
        self.queue = Queue()
        self.processing_thread = None
        self.is_running = False
        self.is_paused = False
        self.on_item_status_changed = None
        self.on_batch_completed = None
        self.processor_func = None
    
    def add_item(self, input_file: str, output_file: str) -> BatchItem:
        """Add an item to the batch"""
        item = BatchItem(input_file, output_file)
        self.items.append(item)
        self.queue.put(item)
        return item
    
    def add_items(self, file_pairs: List[Dict[str, str]]) -> None:
        """Add multiple items to the batch"""
        for pair in file_pairs:
            self.add_item(pair["input"], pair["output"])
    
    def clear_completed(self) -> None:
        """Clear completed items from the batch"""
        self.items = [item for item in self.items 
                     if item.status not in (BatchItemStatus.COMPLETED, 
                                          BatchItemStatus.CANCELLED)]
    
    def clear_all(self) -> None:
        """Clear all items from the batch"""
        # Close queue and create a new one
        with self.queue.mutex:
            self.queue.queue.clear()
        self.items = []
    
    def set_processor(self, func: Callable[[BatchItem, Dict[str, Any]], bool]) -> None:
        """Set the processor function to process each item"""
        self.processor_func = func
    
    def set_callbacks(self, 
                     on_item_status_changed: Optional[Callable[[BatchItem], None]] = None,
                     on_batch_completed: Optional[Callable[[], None]] = None) -> None:
        """Set callback functions"""
        self.on_item_status_changed = on_item_status_changed
        self.on_batch_completed = on_batch_completed
    
    def start(self, options: Dict[str, Any] = None) -> bool:
        """Start processing the batch"""
        if self.is_running or not self.processor_func:
            return False
        
        self.is_running = True
        self.is_paused = False
        self.processing_thread = threading.Thread(
            target=self._process_batch,
            args=(options or {},),
            daemon=True
        )
        self.processing_thread.start()
        return True
    
    def pause(self) -> bool:
        """Pause the batch processing"""
        if not self.is_running:
            return False
        
        self.is_paused = True
        return True
    
    def resume(self) -> bool:
        """Resume the batch processing"""
        if not self.is_running or not self.is_paused:
            return False
        
        self.is_paused = False
        return True
    
    def cancel(self) -> bool:
        """Cancel the batch processing"""
        if not self.is_running:
            return False
        
        self.is_running = False
        self.is_paused = False
        
        # Mark remaining items as cancelled
        for item in self.items:
            if item.status in (BatchItemStatus.PENDING, BatchItemStatus.PROCESSING):
                item.status = BatchItemStatus.CANCELLED
                if self.on_item_status_changed:
                    self.on_item_status_changed(item)
        
        # Clear queue
        with self.queue.mutex:
            self.queue.queue.clear()
        
        return True
    
    def _process_batch(self, options: Dict[str, Any]) -> None:
        """Process the batch items in the queue"""
        while self.is_running and not self.queue.empty():
            # Check if paused
            if self.is_paused:
                time.sleep(0.5)  # Sleep while paused
                continue
            
            # Get next item
            item = self.queue.get()
            
            if item.status == BatchItemStatus.PENDING:
                # Update status to processing
                item.status = BatchItemStatus.PROCESSING
                if self.on_item_status_changed:
                    self.on_item_status_changed(item)
                
                try:
                    # Process the item
                    success = self.processor_func(item, options)
                    
                    # Update status based on result
                    if self.is_running:  # Only update if not cancelled
                        item.status = BatchItemStatus.COMPLETED if success else BatchItemStatus.FAILED
                        if self.on_item_status_changed:
                            self.on_item_status_changed(item)
                except Exception as e:
                    # Handle errors
                    item.status = BatchItemStatus.FAILED
                    item.error = str(e)
                    item.message = f"Error: {str(e)}"
                    if self.on_item_status_changed:
                        self.on_item_status_changed(item)
                
                # Mark task as done
                self.queue.task_done()
            
            # Small delay between items
            time.sleep(0.1)
        
        # Mark as not running when complete
        self.is_running = False
        
        # Call batch completed callback
        if self.on_batch_completed:
            self.on_batch_completed()
    
    def get_stats(self) -> Dict[str, int]:
        """Get batch statistics"""
        stats = {
            "total": len(self.items),
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0
        }
        
        for item in self.items:
            if item.status == BatchItemStatus.PENDING:
                stats["pending"] += 1
            elif item.status == BatchItemStatus.PROCESSING:
                stats["processing"] += 1
            elif item.status == BatchItemStatus.COMPLETED:
                stats["completed"] += 1
            elif item.status == BatchItemStatus.FAILED:
                stats["failed"] += 1
            elif item.status == BatchItemStatus.CANCELLED:
                stats["cancelled"] += 1
        
        return stats 