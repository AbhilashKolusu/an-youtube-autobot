"""
ThumbnailAgent — generates and scores 5 thumbnail variants, picks the winner.

Pipeline:
  1. Build 5 visually distinct prompts based on the video title and hook
  2. Generate each variant as a 1280×720 image via Flux (Replicate)
  3. Vision-score each thumbnail for CTR signals using the LLM
  4. Select the highest-scoring variant
  5. Save winner to niches/{niche}/builds/{episode_id}/thumbnail.jpg

CTR scoring criteria (via vision LLM):
  - Bold, readable text overlay concept (score 0–10)
  - Emotional face or striking visual (score 0–10)
  - Colour contrast vs YouTube dark/light backgrounds (score 0–10)
  - Curiosity gap alignment with title (score 0–10)
"""

from crewai import Agent
from tools import flux_tool, search_tool


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
            "compete in a 10-second scroll. For each variant you write a detailed "
            "Flux image prompt that specifies: subject, lighting, colour palette, "
            "camera angle, and mood. After generating all 5, you score them "
            "analytically and pick the winner."
        ),
        tools=[
            flux_tool.generate_thumbnail,
            search_tool.web_search,
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
