#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Chuyển Đổi Văn Bản Thành Âm Thanh ElevenLabs
Main application entry point
"""

import os
import sys
from src.ui.app import TtsApplication

def main():
    """Main entry point for the application"""
    app = TtsApplication()
    app.run()

if __name__ == "__main__":
    main() 