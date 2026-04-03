"""
IdeaPlannerAgent — selects and structures the best video idea from trends.

Takes the TrendScout output and produces a structured video brief:
  - Title hook variants (A/B)
  - Target audience profile
  - Content angle (listicle / explainer / story / comparison)
  - Estimated watch time target
  - Monetization angle (ad CPM + affiliate opportunities)
"""

from crewai import Agent
from tools import search_tool


def build_idea_planner(llm) -> Agent:
    return Agent(
        role="Idea Planner",
        goal=(
            "Select the single best video idea from the trend report and produce "
            "a structured creative brief with hook variants, content angle, and "
            "monetization notes."
        ),
        backstory=(
            "You are a seasoned YouTube content strategist who has helped faceless "
            "channels grow from 0 to 100k subscribers. You understand what hooks "
            "stop the scroll, which angles retain viewers past 50%, and how to "
            "frame topics for maximum ad revenue. You always think like a viewer "
            "first and an algorithm second."
        ),
        tools=[search_tool.web_search],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
