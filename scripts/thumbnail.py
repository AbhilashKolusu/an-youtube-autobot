#!/usr/bin/env python3
"""
thumbnail.py - Canva API thumbnail creator
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

CANVA_TOKEN = os.getenv('CANVA_API_TOKEN')

def create_thumbnail(title, bg_image):
    # Placeholder for Canva API call
    # Create design, add text, download PNG
    print(f"Creating thumbnail for {title}")
    # Save as thumb.png

def main():
    title = "New Lo-Fi Mix"
    bg_image = "assets/bg_lofi.png"
    create_thumbnail(title, bg_image)

if __name__ == '__main__':
    main()