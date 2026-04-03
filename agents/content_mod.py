"""
ContentModAgent — fact-checks the script and enforces YouTube policy compliance.

Checks:
  1. Factual accuracy (flags unverified claims for citation or removal)
  2. YouTube Community Guidelines (no YMYL violations, hate speech, etc.)
  3. Copyright / music licensing flags
  4. Advertiser-friendly language (no profanity, no controversial framing)
  5. Medical / financial disclaimer requirements (YMYL niches)

Returns:
  {"approved": true/false, "issues": [...], "revised_script": "..."}
"""

from crewai import Agent
from tools import search_tool


def build_content_mod(llm) -> Agent:
    return Agent(
        role="Content Moderator",
        goal=(
            "Review the script for factual errors, YouTube policy violations, and "
            "advertiser-friendliness. Return an approved, cleaned script or a "
            "detailed list of issues that must be fixed before production."
        ),
        backstory=(
            "You are a former YouTube Trust & Safety policy expert and a fact-checker "
            "with a background in journalism. You know every nuance of YouTube's "
            "advertiser-friendly content guidelines and YMYL content policies. "
            "You protect the channel from demonetisation, strikes, and misinformation "
            "flags while keeping the content engaging and not over-sanitised."
        ),
        tools=[search_tool.web_search],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
