"""
Keyword research tool — YouTube Data API v3 based scoring.

vidIQ does not offer a public API (as of 2026). This tool replicates the
core functionality using the YouTube Data API v3 that you already have:

  keyword_score  — estimates search demand + competition from real YouTube data
  related_keywords — pulls autocomplete suggestions via YouTube's suggest API

Scoring methodology:
  - search_volume proxy: avg view count of top-10 results for the keyword
  - competition proxy: video count in results (more = harder)
  - opportunity_score: high views + low video count = good opportunity (0–100)
"""

import os
import urllib.parse

import requests
from googleapiclient.discovery import build
from crewai.tools import tool


def _yt():
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise EnvironmentError("YOUTUBE_API_KEY is not set.")
    return build("youtube", "v3", developerKey=api_key)


@tool("YouTube Keyword Score")
def keyword_score(keywords: list[str]) -> list[dict]:
    """Estimate keyword opportunity scores using real YouTube search data.

    For each keyword, searches YouTube and computes:
      - search_volume: average view count of top-10 results (proxy for demand)
      - competition: number of videos returned (proxy for how crowded the topic is)
      - opportunity_score: 0–100 composite (high views, lower competition = better)

    Args:
        keywords: Up to 10 keyword strings to score.

    Returns:
        List of dicts with: keyword, search_volume, competition, opportunity_score.
        Sorted by opportunity_score descending.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        return [
            {"keyword": kw, "search_volume": 0, "competition": 0,
             "opportunity_score": 0, "note": "YOUTUBE_API_KEY not set"}
            for kw in keywords
        ]

    youtube = _yt()
    results = []

    for kw in keywords[:10]:
        try:
            search_resp = youtube.search().list(
                q=kw,
                part="id",
                type="video",
                maxResults=10,
                fields="pageInfo,items/id/videoId",
            ).execute()

            video_ids = [item["id"]["videoId"] for item in search_resp.get("items", [])]
            total_videos = search_resp.get("pageInfo", {}).get("totalResults", 0)

            avg_views = 0
            if video_ids:
                stats_resp = youtube.videos().list(
                    id=",".join(video_ids),
                    part="statistics",
                    fields="items/statistics/viewCount",
                ).execute()
                view_counts = []
                for item in stats_resp.get("items", []):
                    vc = item.get("statistics", {}).get("viewCount")
                    if vc is not None:
                        view_counts.append(int(vc))
                if view_counts:
                    avg_views = sum(view_counts) // len(view_counts)

            # Opportunity score: normalise avg views (0–50) + low competition bonus (0–50)
            view_score = min(avg_views / 200_000 * 50, 50)   # cap at 50 pts at 200k avg views
            comp_score = max(50 - (total_videos / 200_000 * 50), 0)  # penalise crowded topics
            opportunity = round(view_score + comp_score)

            results.append({
                "keyword": kw,
                "search_volume": avg_views,
                "competition": total_videos,
                "opportunity_score": opportunity,
            })
        except Exception as exc:
            results.append({
                "keyword": kw,
                "search_volume": 0,
                "competition": 0,
                "opportunity_score": 0,
                "error": str(exc),
            })

    results.sort(key=lambda x: x["opportunity_score"], reverse=True)
    return results


@tool("YouTube Related Keywords")
def related_keywords(seed_keyword: str, limit: int = 20) -> list[str]:
    """Get related keyword suggestions using YouTube's autocomplete endpoint.

    This is the same data that powers YouTube's search-as-you-type suggestions —
    no extra API key needed beyond YOUTUBE_API_KEY.

    Args:
        seed_keyword: The base keyword to expand.
        limit: Max number of suggestions to return (default 20).

    Returns:
        List of related keyword strings.
    """
    try:
        encoded = urllib.parse.quote(seed_keyword)
        url = (
            f"https://suggestqueries.google.com/complete/search"
            f"?client=youtube&ds=yt&q={encoded}"
        )
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        # Response is JSONP: window.google.ac.h([query, [[suggestion, ...], ...]])
        text = resp.text
        # Strip JSONP wrapper
        import json, re
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            suggestions = [item[0] for item in data[1] if isinstance(item, list) and item]
            return suggestions[:limit]
    except Exception:
        pass

    # Fallback: basic variations
    return [
        f"{seed_keyword} 2026",
        f"best {seed_keyword}",
        f"{seed_keyword} for beginners",
        f"how to {seed_keyword}",
        f"{seed_keyword} tips",
    ]
