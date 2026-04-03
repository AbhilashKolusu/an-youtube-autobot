#!/usr/bin/env python3
"""
watch.py - Watch folder → trigger pipeline
"""

import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

WATCH_FOLDER = os.path.expandvars(os.getenv('WATCH_FOLDER', 'recordings/host'))

class Watcher(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_file and event.src_path.endswith('.mp4'):
            print(f"New file detected: {event.src_path}")
            # Logic to extract niche name from the path (e.g., recordings/host/music-mix/ep01/host.mp4)
            path_parts = event.src_path.split(os.sep)
            # Adjust index based on your actual recording folder structure
            niche = path_parts[-3] if len(path_parts) > 3 else "default"
            episode_id = path_parts[-2]

            print(f"Triggering pipeline for Agent: {niche}, Episode: {episode_id}")
            subprocess.run(['python3', 'scripts/resolve_edit.py', episode_id, niche])

if __name__ == "__main__":
    path = WATCH_FOLDER
    event_handler = Watcher()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()