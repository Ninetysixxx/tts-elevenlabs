#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ElevenLabs API Client
Handles all communication with the ElevenLabs API
"""

import json
import requests
from typing import Dict, List, Optional, Tuple, Any

class ElevenLabsClient:
    """Client for interacting with ElevenLabs API"""
    
    BASE_URL = "https://api.elevenlabs.io/v1"
    
    def __init__(self, api_key: str):
        """Initialize the client with an API key"""
        self.api_key = api_key
        self.headers = {
            "Accept": "application/json",
            "xi-api-key": self.api_key
        }
    
    def validate_api_key(self) -> Tuple[bool, Dict[str, Any]]:
        """Validate the API key and return user information"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/user/subscription",
                headers=self.headers
            )
            
            if response.status_code == 200:
                user_data = response.json()
                return True, user_data
            elif response.status_code == 401:
                return False, {"error": "API Key không hợp lệ hoặc hết hạn"}
            else:
                return False, {"error": f"API Key validation failed: {response.status_code}"}
        except Exception as e:
            return False, {"error": f"Error connecting to ElevenLabs API: {str(e)}"}
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get a list of available voices"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/voices",
                headers=self.headers
            )
            
            if response.status_code == 200:
                voices_data = response.json()
                return voices_data.get("voices", [])
            else:
                return []
        except Exception:
            return []
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get a list of available models"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/models",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return []
        except Exception:
            return []
    
    def text_to_speech(
        self, 
        text: str, 
        voice_id: str, 
        model_id: str = "eleven_turbo_v2",
        output_format: str = "mp3",
        stability: float = 0.5,
        similarity_boost: float = 0.5,
        output_path: str = None
    ) -> Tuple[bool, str]:
        """Convert text to speech using ElevenLabs API"""
        url = f"{self.BASE_URL}/text-to-speech/{voice_id}"
        
        data = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost
            }
        }
        
        headers = self.headers.copy()
        headers["Content-Type"] = "application/json"
        
        try:
            response = requests.post(
                url,
                json=data,
                headers=headers
            )
            
            if response.status_code == 200:
                if output_path:
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    return True, output_path
                else:
                    return True, response.content
            else:
                error_message = f"API Error: {response.status_code}"
                try:
                    error_data = response.json()
                    if "detail" in error_data:
                        error_message = f"API Error: {error_data['detail']}"
                except:
                    pass
                return False, error_message
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get user information including credit usage"""
        try:
            # Try user/subscription endpoint first
            response = requests.get(
                f"{self.BASE_URL}/user/subscription",
                headers=self.headers
            )
            
            if response.status_code == 200:
                subscription_data = response.json()
                
                # Also fetch user info for more complete data
                try:
                    user_response = requests.get(
                        f"{self.BASE_URL}/user",
                        headers=self.headers
                    )
                    
                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        # Merge the data
                        merged_data = {**subscription_data, **user_data}
                        return merged_data
                except:
                    # Return just subscription data if user info fails
                    return subscription_data
                
                return subscription_data
            else:
                # If subscription fails, try user endpoint
                try:
                    user_response = requests.get(
                        f"{self.BASE_URL}/user",
                        headers=self.headers
                    )
                    
                    if user_response.status_code == 200:
                        return user_response.json()
                    else:
                        return {"error": f"Failed to get user info: {user_response.status_code}"}
                except Exception as e:
                    return {"error": f"Error connecting to ElevenLabs API: {str(e)}"}
        except Exception as e:
            return {"error": f"Error connecting to ElevenLabs API: {str(e)}"}
    
    def get_voice_audio(self, voice_id: str, sample_text: str = None) -> Optional[bytes]:
        """Get sample audio for a voice"""
        try:
            # Nếu không có sample_text, sử dụng mẫu mặc định
            if not sample_text:
                sample_text = "Hello, this is a sample voice from ElevenLabs. Xin chào, đây là giọng đọc mẫu từ ElevenLabs."
            
            # Sử dụng text-to-speech API để lấy audio
            model_id = "eleven_turbo_v2"  # Sử dụng model mặc định
            
            url = f"{self.BASE_URL}/text-to-speech/{voice_id}"
            
            data = {
                "text": sample_text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5
                }
            }
            
            headers = self.headers.copy()
            headers["Content-Type"] = "application/json"
            
            response = requests.post(
                url,
                json=data,
                headers=headers
            )
            
            if response.status_code == 200:
                return response.content
            else:
                return None
        except Exception as e:
            print(f"Error getting voice audio: {str(e)}")
            return None 