#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API Key Manager
Manages the secure storage and retrieval of API keys
"""

import os
import json
import base64
from typing import Dict, List, Optional, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class ApiKeyManager:
    """Manages API keys with secure storage and encryption"""
    
    def __init__(self, file_path: str = "api_keys.json"):
        """Initialize the API Key Manager"""
        self.file_path = file_path
        self.keys = {}
        self.current_key = None
        
        # Generate encryption key
        self._generate_encryption_key()
        
        # Load existing keys if file exists
        if os.path.exists(self.file_path):
            self.load_keys()
    
    def _generate_encryption_key(self):
        """Generate an encryption key for securing API keys"""
        # A simple password-based key derivation
        # In a production app, this should be more securely handled
        password = b"elevenlabs_tts_app_secure_key"
        salt = b"elevenlabs_salt"
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self.cipher = Fernet(key)
    
    def add_key(self, key_name: str, api_key: str) -> bool:
        """Add a new API key"""
        if not key_name or not api_key:
            return False
        
        # Encrypt the API key
        encrypted_key = self.cipher.encrypt(api_key.encode()).decode()
        
        # Store the encrypted key
        self.keys[key_name] = {
            "key": encrypted_key,
            "date_added": "",  # Could use datetime here
        }
        
        # Set as current if no current key
        if not self.current_key:
            self.current_key = key_name
        
        # Save keys to file
        self.save_keys()
        return True
    
    def remove_key(self, key_name: str) -> bool:
        """Remove an API key"""
        if key_name in self.keys:
            del self.keys[key_name]
            
            # Update current key if removed
            if self.current_key == key_name:
                self.current_key = next(iter(self.keys)) if self.keys else None
            
            # Save changes
            self.save_keys()
            return True
        return False
    
    def get_key(self, key_name: str) -> Optional[str]:
        """Get the decrypted API key"""
        if key_name in self.keys:
            encrypted_key = self.keys[key_name]["key"]
            try:
                decrypted_key = self.cipher.decrypt(encrypted_key.encode()).decode()
                return decrypted_key
            except:
                return None
        return None
    
    def get_current_key(self) -> Optional[str]:
        """Get the current API key"""
        if self.current_key:
            return self.get_key(self.current_key)
        return None
    
    def set_current_key(self, key_name: str) -> bool:
        """Set the current API key"""
        if key_name in self.keys:
            self.current_key = key_name
            self.save_keys()
            return True
        return False
    
    def get_key_names(self) -> List[str]:
        """Get the list of key names"""
        return list(self.keys.keys())
    
    def get_total_credits(self, api_client) -> Dict[str, Any]:
        """
        Get total credits from all API keys, without counting duplicates
        
        Returns a dictionary with:
        - total_remaining: Total remaining credits across all unique API keys
        - total_limit: Total credit limit across all unique API keys
        - unique_keys: Number of unique API keys
        - duplicates: Number of duplicate API keys
        """
        if not api_client:
            return {
                "total_remaining": 0,
                "total_limit": 0,
                "unique_keys": 0,
                "duplicates": 0
            }
        
        # Store unique API keys to avoid counting duplicates
        unique_api_keys = set()
        key_details = {}
        duplicates = 0
        
        # Get all API keys
        for key_name in self.keys:
            api_key = self.get_key(key_name)
            if api_key:
                if api_key in unique_api_keys:
                    duplicates += 1
                    continue
                
                unique_api_keys.add(api_key)
                
                # Create a temporary client with this key
                temp_client = api_client.__class__(api_key)
                
                # Get user info
                info = temp_client.get_user_info()
                
                # Skip if error
                if "error" in info:
                    continue
                
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
                
                # Store key details
                key_details[key_name] = {
                    "remaining": character_remaining,
                    "limit": character_limit
                }
        
        # Calculate totals
        total_remaining = sum(key["remaining"] for key in key_details.values())
        total_limit = sum(key["limit"] for key in key_details.values())
        
        return {
            "total_remaining": total_remaining,
            "total_limit": total_limit,
            "unique_keys": len(unique_api_keys),
            "duplicates": duplicates,
            "key_details": key_details
        }
    
    def save_keys(self) -> bool:
        """Save keys to file"""
        try:
            data = {
                "keys": self.keys,
                "current": self.current_key
            }
            
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            return True
        except:
            return False
    
    def load_keys(self) -> bool:
        """Load keys from file"""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.keys = data.get("keys", {})
            self.current_key = data.get("current")
            return True
        except:
            # If loading fails, initialize empty keys
            self.keys = {}
            self.current_key = None
            return False 