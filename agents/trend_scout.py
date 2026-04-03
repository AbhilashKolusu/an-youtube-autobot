"""
TrendScoutAgent — discovers top trending topics for a given niche.

Data sources:
  - YouTube Data API v3 (trending videos, search volume)
  - Perplexity / web search (Reddit, X, Google Trends signals)
  - vidIQ API (keyword opportunity scores)
"""

from crewai import Agent
from tools import youtube_tool, search_tool, vidiq_tool


def build_trend_scout(llm) -> Agent:
    return Agent(
        role="Trend Scout",
        goal=(
            "Identify 5–7 high-opportunity video topics for {niche} that are "
            "trending RIGHT NOW and align with high-RPM, searchable keywords."
        ),
        backstory=(
            "You are a data-driven YouTube trend analyst with deep expertise in "
            "spotting viral topics before they peak. You cross-reference YouTube "
            "search trends, Reddit/X discussions, and vidIQ keyword scores to find "
            "ideas with strong CPM potential and manageable competition."
        ),
        tools=[
            youtube_tool.search_trending,
            search_tool.web_search,
            vidiq_tool.keyword_score,
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
