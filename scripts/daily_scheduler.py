#!/usr/bin/env python3
"""
daily_scheduler.py - Run daily automation for all niches
"""

import os
import subprocess
import schedule
import time
from dotenv import load_dotenv

load_dotenv()

def run_niche_pipeline(niche):
    print(f"Running pipeline for niche: {niche}")
    # Set NICHE env var
    env = os.environ.copy()
    env['NICHE'] = niche
    # Run common steps
    subprocess.run(['python3', 'scripts/topics.py'], env=env)
    subprocess.run(['python3', 'scripts/generate_script.py'], env=env)
    
    # Niche-specific content generation
    if niche == 'music-mix':
        subprocess.run(['python3', 'scripts/music_prompt.py'], env=env)
    elif niche == 'ai-news':
        subprocess.run(['python3', f'niches/{niche}/scripts/ai_news_generator.py'], env=env)
    # Add more niche-specific logic here
    
    # The rest is triggered by watch.py when recording is done

def daily_job():
    niches = ['music-mix', 'tech-reviews', 'ai-news']  # Add more as created
    for niche in niches:
        run_niche_pipeline(niche)

if __name__ == "__main__":
    # Schedule daily at 9 AM
    schedule.every().day.at("09:00").do(daily_job)

    print("Scheduler started. Waiting for daily run...")
    while True:
        schedule.run_pending()
        time.sleep(60)