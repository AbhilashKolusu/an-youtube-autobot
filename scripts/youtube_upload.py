#!/usr/bin/env python3
"""
youtube_upload.py - YouTube Data API uploader
"""

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
from dotenv import load_dotenv

load_dotenv()

def upload_video(video_path, title, description, tags):
    creds = Credentials.from_authorized_user_file('configs/youtube_oauth.json')
    youtube = build('youtube', 'v3', credentials=creds)

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": tags,
                "categoryId": "10"  # Music
            },
            "status": {
                "privacyStatus": "private"  # Or public/scheduled
            }
        },
        media_body=video_path
    )
    response = request.execute()
    print(f"Uploaded video: {response['id']}")

def main():
    upload_video("builds/test/final.mp4", "Test Mix", "Description", ["lo-fi", "music"])

if __name__ == '__main__':
    main()