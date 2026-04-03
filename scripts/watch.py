#!/usr/bin/env python3
"""
watch.py - Watch folder → trigger pipeline
"""

import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import subprocess

class Watcher(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_file and event.src_path.endswith('.mp4'):
            print(f"New file detected: {event.src_path}")
            # Trigger pipeline
            episode_id = os.path.basename(os.path.dirname(event.src_path))
            subprocess.run(['python', 'scripts/resolve_edit.py', episode_id])

if __name__ == "__main__":
    path = "recordings/host"
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