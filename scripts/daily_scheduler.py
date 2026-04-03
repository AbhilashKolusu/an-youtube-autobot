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
    # Run the pipeline steps
    subprocess.run(['python3', 'scripts/topics.py'], env=env)
    subprocess.run(['python3', 'scripts/generate_script.py'], env=env)
    # Assume recording is manual, then watch triggers the rest
    # For fully automated, add AI video generation or something

def daily_job():
    niches = ['music-mix', 'tech-reviews']  # Add more as created
    for niche in niches:
        run_niche_pipeline(niche)

if __name__ == "__main__":
    # Schedule daily at 9 AM
    schedule.every().day.at("09:00").do(daily_job)

    print("Scheduler started. Waiting for daily run...")
    while True:
        schedule.run_pending()
        time.sleep(60)