"""
YouTube Data API v3 + YouTube Analytics API tools for CrewAI agents.

Quota budget (default 10,000 units/day):
  search.list          = 100 units
  videos.insert        = 1,600 units
  videos.list          = 1 unit
  thumbnails.set       = 50 units
  reports.query        = 1 unit
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from crewai.tools import tool
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials


def _yt_client(niche: str):
    oauth_path = (
        f"niches/{niche}/configs/youtube_oauth.json"
        if os.path.exists(f"niches/{niche}/configs/youtube_oauth.json")
        else os.getenv("YOUTUBE_OAUTH_TOKEN", "configs/youtube_oauth.json")
    )
    creds = Credentials.from_authorized_user_file(oauth_path)
    return build("youtube", "v3", credentials=creds)


def _analytics_client(niche: str):
    oauth_path = (
        f"niches/{niche}/configs/youtube_oauth.json"
        if os.path.exists(f"niches/{niche}/configs/youtube_oauth.json")
        else os.getenv("YOUTUBE_OAUTH_TOKEN", "configs/youtube_oauth.json")
    )
    creds = Credentials.from_authorized_user_file(oauth_path)
    return build("youtubeAnalytics", "v2", credentials=creds)


@tool("YouTube Trending Search")
def search_trending(query: str, max_results: int = 10) -> list[dict]:
    """Search YouTube for trending videos matching a query.

    Returns a list of dicts with keys: videoId, title, viewCount, publishedAt.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    youtube = build("youtube", "v3", developerKey=api_key)
    response = youtube.search().list(
        q=query,
        part="snippet",
        type="video",
        order="viewCount",
        publishedAfter=(datetime.now(timezone.utc) - timedelta(days=7)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
        maxResults=max_results,
    ).execute()

    results = []
    for item in response.get("items", []):
        results.append(
            {
                "videoId": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "channelTitle": item["snippet"]["channelTitle"],
                "publishedAt": item["snippet"]["publishedAt"],
            }
        )
    return results


def upload_video(
    niche: str,
    video_path: str,
    title: str,
    description: str,
    tags: list[str],
    thumbnail_path: str | None = None,
    category_id: str = "22",
    schedule_at: str | None = None,
) -> dict[str, Any]:
    """Upload a video to YouTube.

    Args:
        niche: Channel niche identifier (for OAuth selection).
        video_path: Local path to the MP4 file.
        title: Video title (max 100 chars).
        description: Video description.
        tags: List of tag strings.
        thumbnail_path: Optional path to thumbnail JPG/PNG.
        category_id: YouTube category ID (22 = People & Blogs).
        schedule_at: ISO 8601 datetime string to schedule public release.

    Returns:
        dict with videoId and status.
    """
    youtube = _yt_client(niche)

    privacy = "private"
    publish_at = None
    if schedule_at:
        privacy = "private"
        publish_at = schedule_at

    body: dict[str, Any] = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
            **({"publishAt": publish_at} if publish_at else {}),
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = request.execute()
    video_id = response["id"]

    if thumbnail_path and os.path.exists(thumbnail_path):
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path),
        ).execute()

    return {"videoId": video_id, "privacyStatus": privacy}


@tool("YouTube Video Analytics")
def get_video_analytics(niche: str, video_id: str, days_back: int = 7) -> dict:
    """Fetch per-video performance metrics from YouTube Analytics API.

    Returns views, watchTimeMinutes, averageViewDurationSeconds, ctr, impressions.
    """
    analytics = _analytics_client(niche)
    end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    start_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")

    response = analytics.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        metrics="views,estimatedMinutesWatched,averageViewDuration,impressions,impressionsClickThroughRate",
        filters=f"video=={video_id}",
        dimensions="day",
    ).execute()

    return response


@tool("YouTube Channel Benchmarks")
def get_channel_benchmarks(niche: str, days_back: int = 30) -> dict:
    """Fetch channel-level averages to use as performance benchmarks.

    Returns average CTR, average view duration, avg views per video over the period.
    """
    analytics = _analytics_client(niche)
    end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    start_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).strftime("%Y-%m-%d")

    response = analytics.reports().query(
        ids="channel==MINE",
        startDate=start_date,
        endDate=end_date,
        metrics="views,estimatedMinutesWatched,averageViewDuration,impressions,impressionsClickThroughRate",
    ).execute()

    return response
