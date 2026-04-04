"""
crew.py — CrewAI crew factory (crewai >= 1.0.0 API).

crewai 1.x uses its own LLM class instead of LangChain wrappers.
Claude claude-opus-4-6 = manager LLM, Claude Sonnet 4.6 = worker LLM.
"""

import os
from crewai import Crew, Process, LLM

import agents as ag


def _manager_llm() -> LLM:
    """Claude claude-opus-4-6 as manager. Falls back to GPT-4o."""
    if os.getenv("ANTHROPIC_API_KEY"):
        return LLM(
            model="anthropic/claude-opus-4-6",
            api_key=os.environ["ANTHROPIC_API_KEY"],
            max_tokens=8096,
        )
    if os.getenv("OPENAI_API_KEY"):
        return LLM(model="gpt-4o", api_key=os.environ["OPENAI_API_KEY"])
    raise EnvironmentError("Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")


def _worker_llm() -> LLM:
    """Claude Sonnet 4.6 for workers (faster + cheaper)."""
    if os.getenv("ANTHROPIC_API_KEY"):
        return LLM(
            model="anthropic/claude-sonnet-4-6",
            api_key=os.environ["ANTHROPIC_API_KEY"],
            max_tokens=8096,
        )
    if os.getenv("OPENAI_API_KEY"):
        return LLM(model="gpt-4o-mini", api_key=os.environ["OPENAI_API_KEY"])
    raise EnvironmentError("Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")


def build_crew(niche: str) -> Crew:
    """Build the YouTube automation crew for a given niche.

    Agent order (referenced by index in workflows/pipeline.py):
      0 TrendScout  1 IdeaPlanner  2 ScriptWriter  3 ContentMod
      4 AssetCreator  5 ThumbnailAgent  6 SEOOptimizer  7 AnalyticsAgent

    Args:
        niche: Niche slug matching a niches/{niche}/ directory.

    Returns:
        Configured CrewAI Crew instance.
    """
    manager = _manager_llm()
    worker = _worker_llm()

    crew_agents = [
        ag.build_trend_scout(worker),
        ag.build_idea_planner(worker),
        ag.build_script_writer(worker),
        ag.build_content_mod(worker),
        ag.build_asset_creator(worker),
        ag.build_thumbnail_agent(worker),
        ag.build_seo_optimizer(worker),
        ag.build_analytics_agent(worker),
    ]

    return Crew(
        agents=crew_agents,
        tasks=[],           # Tasks are constructed per-node in workflows/pipeline.py
        process=Process.hierarchical,
        manager_llm=manager,
        memory=True,
        verbose=True,
        full_output=True,
    )
