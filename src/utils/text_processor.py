#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Text Processor
Handles text pre-processing and chunking for TTS
"""

import os
import re
from typing import List, Dict, Any, Optional

class TextProcessor:
    """Processes text for TTS conversion"""
    
    def __init__(self, max_chunk_size: int = 5000):
        """Initialize text processor with maximum chunk size"""
        self.max_chunk_size = max_chunk_size
    
    def read_text_file(self, file_path: str, encoding: str = "utf-8") -> str:
        """Read a text file and return its content"""
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    content = f.read()
                return content
            except Exception as e:
                raise Exception(f"Error reading file {file_path}: {str(e)}")
        except Exception as e:
            raise Exception(f"Error reading file {file_path}: {str(e)}")
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text for TTS conversion"""
        # Replace multiple newlines with single newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Replace tabs with spaces
        text = text.replace("\t", " ")
        
        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)
        
        # Other preprocessing steps can be added here
        
        return text
    
    def split_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks of appropriate size"""
        chunks = []
        current_pos = 0
        text_length = len(text)
        
        while current_pos < text_length:
            # Find a good breaking point
            chunk_end = min(current_pos + self.max_chunk_size, text_length)
            
            # If we're not at the end, find a good break point
            if chunk_end < text_length:
                # Look for paragraph break
                paragraph_break = text.rfind('\n\n', current_pos, chunk_end)
                if paragraph_break != -1 and paragraph_break > current_pos + self.max_chunk_size // 2:
                    chunk_end = paragraph_break + 2  # Include the newlines
                else:
                    # Look for line break
                    line_break = text.rfind('\n', current_pos, chunk_end)
                    if line_break != -1 and line_break > current_pos + self.max_chunk_size // 2:
                        chunk_end = line_break + 1  # Include the newline
                    else:
                        # Look for sentence end
                        sentence_end = max(
                            text.rfind('. ', current_pos, chunk_end),
                            text.rfind('! ', current_pos, chunk_end),
                            text.rfind('? ', current_pos, chunk_end)
                        )
                        if sentence_end != -1 and sentence_end > current_pos + self.max_chunk_size // 2:
                            chunk_end = sentence_end + 2  # Include the period and space
                        else:
                            # Last resort: break at a space
                            space = text.rfind(' ', current_pos, chunk_end)
                            if space != -1 and space > current_pos + self.max_chunk_size // 3:
                                chunk_end = space + 1  # Include the space
            
            # Extract the chunk and add to list
            chunk = text[current_pos:chunk_end].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
            
            # Move to next position
            current_pos = chunk_end
        
        return chunks
    
    def process_file(self, file_path: str) -> List[str]:
        """Process a text file and return chunks ready for TTS"""
        # Read the file
        text = self.read_text_file(file_path)
        
        # Preprocess the text
        processed_text = self.preprocess_text(text)
        
        # Split into chunks
        chunks = self.split_into_chunks(processed_text)
        
        return chunks 