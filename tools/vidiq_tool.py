"""
vidIQ API tool — keyword research and SEO scoring.

API docs: https://developers.vidiq.com
Provides: keyword volume, competition score, overall opportunity score.

Note: vidIQ API access requires a Business plan or above.
Fallback: if VIDIQ_API_KEY is not set, returns placeholder scores so the
pipeline can still run in dev/test mode.
"""

import os

import requests
from crewai.tools import tool


_BASE_URL = "https://api.vidiq.com/v1"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {os.environ['VIDIQ_API_KEY']}",
        "Content-Type": "application/json",
    }


@tool("vidIQ Keyword Score")
def keyword_score(keywords: list[str]) -> list[dict]:
    """Fetch keyword opportunity scores from vidIQ for a list of keywords.

    Args:
        keywords: Up to 10 keyword strings to score.

    Returns:
        List of dicts with: keyword, search_volume, competition, opportunity_score.
    """
    api_key = os.getenv("VIDIQ_API_KEY")

    if not api_key:
        # Dev fallback — return mock data so agents can run without credentials
        return [
            {"keyword": kw, "search_volume": 0, "competition": 0, "opportunity_score": 0, "note": "VIDIQ_API_KEY not set"}
            for kw in keywords
        ]

    results = []
    for kw in keywords[:10]:
        resp = requests.get(
            f"{_BASE_URL}/keywords/score",
            headers=_headers(),
            params={"keyword": kw},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        results.append(
            {
                "keyword": kw,
                "search_volume": data.get("search_volume", 0),
                "competition": data.get("competition_score", 0),
                "opportunity_score": data.get("overall_score", 0),
            }
        )
    return results


@tool("vidIQ Related Keywords")
def related_keywords(seed_keyword: str, limit: int = 20) -> list[str]:
    """Get related keyword suggestions from vidIQ for a seed keyword.

    Args:
        seed_keyword: The base keyword to expand.
        limit: Max number of related keywords to return (default 20).

    Returns:
        List of related keyword strings sorted by opportunity score.
    """
    api_key = os.getenv("VIDIQ_API_KEY")

    if not api_key:
        return [f"{seed_keyword} tips", f"best {seed_keyword}", f"{seed_keyword} 2026"]

    resp = requests.get(
        f"{_BASE_URL}/keywords/related",
        headers=_headers(),
        params={"keyword": seed_keyword, "limit": limit},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return [item["keyword"] for item in data.get("keywords", [])]
