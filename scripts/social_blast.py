#!/usr/bin/env python3
"""
social_blast.py - Zapier/Make trigger via webhook
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def post_to_social(platform, message, url):
    webhook_url = os.getenv(f'{platform.upper()}_WEBHOOK_URL')
    if webhook_url:
        requests.post(webhook_url, json={"text": message, "url": url})

def main():
    video_url = "https://youtu.be/test"
    post_to_social("discord", "New mix out!", video_url)
    # Similarly for others

if __name__ == '__main__':
    main()