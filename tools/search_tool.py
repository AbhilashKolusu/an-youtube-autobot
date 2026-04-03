"""
Web search tool — Perplexity API for real-time research.

Used by TrendScout, ScriptWriter, and ContentMod for:
  - Current events and trend signals (Reddit, X, news)
  - Fact-checking claims in scripts
  - Competitor video research

Fallback: if PERPLEXITY_API_KEY is not set, uses a basic DuckDuckGo scrape.
"""

import os

import requests
from crewai.tools import tool


@tool("Web Search")
def web_search(query: str, max_results: int = 5) -> list[dict]:
    """Search the web for current information using Perplexity API.

    Args:
        query: The search query string.
        max_results: Max number of results to return (default 5).

    Returns:
        List of dicts with: title, url, snippet, published_date.
    """
    api_key = os.getenv("PERPLEXITY_API_KEY")

    if api_key:
        return _perplexity_search(query, api_key, max_results)

    # Fallback: DuckDuckGo Instant Answer API (no key required, limited)
    return _ddg_search(query, max_results)


def _perplexity_search(query: str, api_key: str, max_results: int) -> list[dict]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": "Return search results as a JSON list of {title, url, snippet, published_date} objects.",
            },
            {"role": "user", "content": query},
        ],
        "max_tokens": 1024,
        "return_citations": True,
    }
    resp = requests.post(
        "https://api.perplexity.ai/chat/completions",
        headers=headers,
        json=payload,
        timeout=20,
    )
    resp.raise_for_status()
    content = resp.json()["choices"][0]["message"]["content"]

    # Perplexity returns citations separately
    citations = resp.json().get("citations", [])
    results = []
    for i, cite in enumerate(citations[:max_results]):
        results.append(
            {
                "title": cite.get("title", f"Result {i+1}"),
                "url": cite.get("url", ""),
                "snippet": cite.get("snippet", ""),
                "published_date": cite.get("date", ""),
            }
        )
    return results


def _ddg_search(query: str, max_results: int) -> list[dict]:
    resp = requests.get(
        "https://api.duckduckgo.com/",
        params={"q": query, "format": "json", "no_html": 1},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    for topic in data.get("RelatedTopics", [])[:max_results]:
        if "Text" in topic:
            results.append(
                {
                    "title": topic.get("Text", "")[:80],
                    "url": topic.get("FirstURL", ""),
                    "snippet": topic.get("Text", ""),
                    "published_date": "",
                }
            )
    return results
