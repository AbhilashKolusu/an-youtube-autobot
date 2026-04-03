"""
SEOOptimizerAgent — finalises title, description, tags, and chapters.

Uses vidIQ keyword data + LLM to:
  1. Pick the highest-volume, lowest-competition title variant
  2. Write a 250-word SEO description with primary keyword in first 2 lines
  3. Generate 15 tags (mix of head + long-tail)
  4. Format chapter timestamps from script sections
  5. Add pinned comment template for engagement boost

Output: enriched metadata JSON saved to episode build folder.
"""

from crewai import Agent
from tools import vidiq_tool, youtube_tool


def build_seo_optimizer(llm) -> Agent:
    return Agent(
        role="SEO Optimizer",
        goal=(
            "Maximise discoverability for '{title}' by producing a keyword-optimised "
            "title, description, tag set, and chapter list using real YouTube search "
            "volume data from vidIQ."
        ),
        backstory=(
            "You are a YouTube SEO specialist who has ranked hundreds of videos on "
            "page 1. You treat vidIQ keyword scores as ground truth and always "
            "balance search volume against competition. You know that the first "
            "150 characters of a description are the only ones Google indexes, and "
            "you front-load the primary keyword accordingly."
        ),
        tools=[
            vidiq_tool.keyword_score,
            youtube_tool.search_trending,
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
