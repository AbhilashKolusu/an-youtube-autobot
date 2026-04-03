#!/usr/bin/env python3
"""
youtube_upload.py - YouTube Data API uploader
"""

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
import argparse
import os
import json
import time
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

def log_api_usage(niche, action, cost):
    """Logs API usage to a central CSV file for tracking and dashboarding."""
    log_dir = "logs"
    log_file = os.path.join(log_dir, "api_usage.csv")
    os.makedirs(log_dir, exist_ok=True)
    file_exists = os.path.isfile(log_file)
    with open(log_file, "a") as f:
        if not file_exists:
            f.write("timestamp,niche,action,cost_units\n")
        f.write(f"{datetime.now().isoformat()},{niche},{action},{cost}\n")

def get_seconds_until_reset():
    """Calculates seconds until YouTube API quota resets (Midnight PST / 08:00 UTC)."""
    now = datetime.now(timezone.utc)
    # Reset is at 08:00 UTC (Midnight PST)
    reset_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
    if now >= reset_time:
        reset_time += timedelta(days=1)
    return int((reset_time - now).total_seconds())

def upload_video(niche, video_path, title, description, tags, category_id="10"):
    # Determine the path to the niche-specific OAuth token
    # Defaults to global config if niche-specific one isn't found
    niche_oauth_path = f"niches/{niche}/configs/youtube_oauth.json"
    oauth_file = niche_oauth_path if os.path.exists(niche_oauth_path) else os.path.expandvars(os.getenv('YOUTUBE_OAUTH_TOKEN', 'configs/youtube_oauth.json'))
    
    if not os.path.exists(oauth_file):
        print(f"Error: OAuth file not found for niche '{niche}' at {oauth_file}")
        return

    creds = Credentials.from_authorized_user_file(oauth_file)
    youtube = build('youtube', 'v3', credentials=creds)

    print(f"Agent [{niche}] uploading: {title}")

    # Log the attempt: YouTube video uploads cost ~1600 units
    log_api_usage(niche, "youtube.videos.insert", 1600)

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

    try:
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": category_id
                },
                "status": {
                    "privacyStatus": "private"  # Or public/scheduled
                }
            },
            media_body=media
        )
        response = request.execute()
        print(f"Agent [{niche}] successfully uploaded video ID: {response['id']}")
        return response['id']

    except HttpError as e:
        error_details = json.loads(e.content).get('error', {}).get('errors', [{}])[0]
        if error_details.get('reason') == 'quotaExceeded':
            wait_seconds = get_seconds_until_reset()
            hours = wait_seconds // 3600
            print(f"CRITICAL: Quota exceeded for Agent [{niche}].")
            print(f"Waiting {wait_seconds}s (~{hours}h) until midnight PST reset...")
            time.sleep(wait_seconds)
            # Recursive retry after the wait
            return upload_video(niche, video_path, title, description, tags, category_id)
        else:
            print(f"An HTTP error occurred: {e.resp.status} {e.content}")
        return None

def main():
    parser = argparse.ArgumentParser(description="YouTube Upload Agent")
    parser.add_argument("--niche", required=True, help="The niche/agent name")
    parser.add_argument("--path", required=True, help="Path to the video file")
    parser.add_argument("--episode_id", help="The episode ID to find metadata")
    
    args = parser.parse_args()
    
    # Try to load automated metadata if it exists
    title, description, tags = "New Upload", "", [args.niche]
    metadata_path = f"niches/{args.niche}/builds/{args.episode_id}/metadata.json"
    
    if args.episode_id and os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            meta = json.load(f)
            title = meta.get('title', title)
            description = meta.get('description', description)
            # Ensure tags is a list
            tags = meta.get('tags', "").split(',') if isinstance(meta.get('tags'), str) else meta.get('tags', tags)

    upload_video(
        niche=args.niche,
        video_path=args.path,
        title=title,
        description=description,
        tags=tags
    )

if __name__ == '__main__':
    main()