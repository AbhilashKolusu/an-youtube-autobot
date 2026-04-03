"""
AnalyticsAgent — post-upload performance loop that feeds insights back to the crew.

Runs 24h and 7d after upload to:
  1. Pull views, watch time, CTR, AVD from YouTube Analytics API
  2. Compare against channel benchmarks
  3. Flag under/over-performers
  4. Generate insights memo for TrendScout (feeds next cycle's context)
  5. Write summary to logs/analytics/{episode_id}.json

The LangGraph pipeline calls this agent as a scheduled node so the crew
learns from every video automatically.
"""

from crewai import Agent
from tools import youtube_tool


def build_analytics_agent(llm) -> Agent:
    return Agent(
        role="Analytics Agent",
        goal=(
            "Retrieve 24h and 7d performance metrics for episode {episode_id}, "
            "compare against channel benchmarks, and produce a concise insights "
            "memo that the TrendScout can use to improve the next video brief."
        ),
        backstory=(
            "You are a YouTube data analyst obsessed with improving content "
            "performance. You go beyond vanity metrics — you track Click-Through "
            "Rate, Average View Duration, impressions, and audience retention curves. "
            "Your insights memos are actionable, not descriptive: every report ends "
            "with 3 specific changes for the next video."
        ),
        tools=[
            youtube_tool.get_video_analytics,
            youtube_tool.get_channel_benchmarks,
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
