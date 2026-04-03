"""
ThumbnailAgent — generates and scores 5 thumbnail variants, picks the winner.

Pipeline:
  1. Generate 5 thumbnail image variants via Flux / Grok Imagine
  2. Vision-score each thumbnail (CTR signals: face, text contrast, emotion)
  3. Select the highest-scoring variant
  4. Save to niches/{niche}/builds/{episode_id}/thumbnail.jpg

CTR scoring criteria (via vision LLM):
  - Bold, readable text overlay (score 0–10)
  - Emotional face or striking visual (score 0–10)
  - Colour contrast vs YouTube dark/light backgrounds (score 0–10)
  - Curiosity gap alignment with title (score 0–10)
"""

from crewai import Agent
from tools import search_tool


def build_thumbnail_agent(llm) -> Agent:
    return Agent(
        role="Thumbnail Designer",
        goal=(
            "Generate 5 thumbnail variants for '{title}', score each for predicted "
            "CTR using vision analysis, and return the best-performing thumbnail "
            "saved to the episode build folder."
        ),
        backstory=(
            "You are a data-driven thumbnail designer who has A/B tested thousands "
            "of YouTube thumbnails. You understand the psychology of click-through: "
            "the rule of thirds, emotional triggers, text hierarchy, and colour "
            "contrast. You treat every thumbnail as a mini billboard that must "
            "compete in a 10-second scroll."
        ),
        tools=[search_tool.web_search],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
