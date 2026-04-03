"""
ScriptWriterAgent — produces the full video script + voiceover text.

Output format (JSON):
  {
    "title": "...",
    "hook": "First 30 seconds narration",
    "sections": [{"heading": "...", "narration": "...", "b_roll_prompt": "..."}],
    "cta": "...",
    "total_word_count": 900,
    "estimated_duration_mins": 7
  }

The b_roll_prompt fields feed directly into AssetCreator.
"""

from crewai import Agent
from tools import search_tool


def build_script_writer(llm) -> Agent:
    return Agent(
        role="Script Writer",
        goal=(
            "Write a compelling, well-structured {estimated_duration_mins}-minute "
            "YouTube script for '{title}' that hooks in the first 30 seconds, "
            "retains viewers with value-dense sections, and ends with a clear CTA. "
            "Include b-roll visual prompts for each section."
        ),
        backstory=(
            "You are an elite YouTube scriptwriter who specialises in faceless, "
            "narration-driven channels. Your scripts are tight, punchy, and optimised "
            "for watch-time. You write in a direct, conversational tone that sounds "
            "natural when spoken by an AI voice. You always include timestamped "
            "section markers and visual cue prompts so asset generation is seamless."
        ),
        tools=[search_tool.web_search],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
