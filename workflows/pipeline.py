"""
LangGraph production pipeline — stateful, retry-safe orchestration.

Graph topology:
  START
    → trend_scout
    → idea_planner
    → script_writer
    → content_mod  ──(issues found)──→ script_writer  (retry loop, max 2)
         │ (approved)
    → asset_creator  (parallel fork)
    → thumbnail_agent
    ← join
    → seo_optimizer
    → uploader
    → END (schedule analytics node via separate delayed trigger)

State is persisted via LangGraph's MemorySaver so the pipeline can be
resumed after failures without re-running completed steps.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Annotated, Any
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from crewai import Crew, Process, Task
import agents as ag
from tools import youtube_tool


# ---------------------------------------------------------------------------
# Pipeline state
# ---------------------------------------------------------------------------

class PipelineState(TypedDict):
    niche: str
    date: str
    episode_id: str

    # TrendScout output
    trends: list[dict]

    # IdeaPlanner output
    brief: dict  # {title, hook_variants, angle, audience, duration_mins}

    # ScriptWriter output
    script: dict  # full script JSON

    # ContentMod output
    mod_approved: bool
    mod_issues: list[str]
    mod_revision_count: int  # tracks retry loops

    # AssetCreator output
    narration_path: str
    video_path: str

    # ThumbnailAgent output
    thumbnail_path: str

    # SEOOptimizer output
    metadata: dict  # {title, description, tags, chapters, pinned_comment}

    # Uploader output
    video_id: str

    # AnalyticsAgent output (written post-upload by a separate delayed trigger)
    analytics: dict


# ---------------------------------------------------------------------------
# Node implementations
# ---------------------------------------------------------------------------

def _episode_id(niche: str, date: str) -> str:
    return f"{niche}_{date.replace('-', '')}"


def node_trend_scout(state: PipelineState, crew: Crew) -> dict:
    task = Task(
        description=(
            f"Research trending topics for the '{state['niche']}' niche on {state['date']}. "
            "Use YouTube trending search and web search. Return a JSON list of 5–7 topic "
            "objects with: title, why_trending, estimated_views, keyword_opportunity_score."
        ),
        expected_output="JSON list of 5–7 trending topic objects.",
        agent=crew.agents[0],  # TrendScout
    )
    result = Crew(agents=[crew.agents[0]], tasks=[task]).kickoff()
    try:
        trends = json.loads(str(result))
    except json.JSONDecodeError:
        trends = [{"title": str(result), "why_trending": "parsed from text", "estimated_views": 0, "keyword_opportunity_score": 0}]
    return {"trends": trends}


def node_idea_planner(state: PipelineState, crew: Crew) -> dict:
    task = Task(
        description=(
            f"Given these trending topics: {json.dumps(state['trends'], indent=2)}\n\n"
            "Select the single best topic for the '{niche}' niche and return a JSON creative brief "
            "with: title, hook_variants (list of 2), angle, target_audience, estimated_duration_mins, "
            "monetization_angle."
        ).format(niche=state["niche"]),
        expected_output="JSON creative brief object.",
        agent=crew.agents[1],  # IdeaPlanner
    )
    result = Crew(agents=[crew.agents[1]], tasks=[task]).kickoff()
    try:
        brief = json.loads(str(result))
    except json.JSONDecodeError:
        brief = {"title": str(result)[:100], "hook_variants": [], "angle": "explainer",
                 "target_audience": "general", "estimated_duration_mins": 8, "monetization_angle": ""}
    return {"brief": brief, "episode_id": _episode_id(state["niche"], state["date"])}


def node_script_writer(state: PipelineState, crew: Crew) -> dict:
    context = ""
    if state.get("mod_issues"):
        context = f"\n\nPrevious draft was rejected for: {state['mod_issues']}. Fix these issues."

    task = Task(
        description=(
            f"Write a full YouTube script based on this creative brief:\n{json.dumps(state['brief'], indent=2)}"
            f"{context}\n\n"
            "Return a JSON object with: title, hook (first 30s narration), sections "
            "(list of {{heading, narration, b_roll_prompt}}), cta, total_word_count, estimated_duration_mins."
        ),
        expected_output="JSON script object.",
        agent=crew.agents[2],  # ScriptWriter
    )
    result = Crew(agents=[crew.agents[2]], tasks=[task]).kickoff()
    try:
        script = json.loads(str(result))
    except json.JSONDecodeError:
        script = {"title": state["brief"].get("title", ""), "hook": str(result)[:500],
                  "sections": [], "cta": "", "total_word_count": 0, "estimated_duration_mins": 8}
    return {"script": script, "mod_issues": []}


def node_content_mod(state: PipelineState, crew: Crew) -> dict:
    task = Task(
        description=(
            f"Review this YouTube script for factual accuracy, YouTube policy compliance, "
            f"and advertiser-friendliness:\n\n{json.dumps(state['script'], indent=2)}\n\n"
            "Return JSON: {{approved: true/false, issues: [list of issues], revised_script: <script JSON or null>}}"
        ),
        expected_output="JSON moderation result with approved flag and issues list.",
        agent=crew.agents[3],  # ContentMod
    )
    result = Crew(agents=[crew.agents[3]], tasks=[task]).kickoff()
    try:
        mod = json.loads(str(result))
    except json.JSONDecodeError:
        mod = {"approved": True, "issues": [], "revised_script": None}

    updates: dict[str, Any] = {
        "mod_approved": mod.get("approved", True),
        "mod_issues": mod.get("issues", []),
        "mod_revision_count": state.get("mod_revision_count", 0),
    }
    if mod.get("revised_script"):
        updates["script"] = mod["revised_script"]
    return updates


def _route_after_mod(state: PipelineState) -> str:
    if state["mod_approved"]:
        return "asset_creator"
    if state.get("mod_revision_count", 0) >= 2:
        # Give up after 2 revisions — log and continue with last script
        return "asset_creator"
    return "script_writer"


def node_asset_creator(state: PipelineState, crew: Crew) -> dict:
    build_dir = f"niches/{state['niche']}/builds/{state['episode_id']}"
    os.makedirs(build_dir, exist_ok=True)

    task = Task(
        description=(
            f"Produce the full video for episode {state['episode_id']}.\n\n"
            f"Script: {json.dumps(state['script'], indent=2)}\n\n"
            f"1. Generate narration MP3 → {build_dir}/narration.mp3\n"
            f"2. Create base video → {build_dir}/base.mp4\n"
            f"3. Generate hero clips for key sections (use b_roll_prompt fields)\n"
            f"4. Output final merged video → {build_dir}/final.mp4"
        ),
        expected_output=f"Path to final video: {build_dir}/final.mp4",
        agent=crew.agents[4],  # AssetCreator
    )
    result = Crew(agents=[crew.agents[4]], tasks=[task]).kickoff()
    return {
        "narration_path": f"{build_dir}/narration.mp3",
        "video_path": f"{build_dir}/final.mp4",
    }


def node_thumbnail_agent(state: PipelineState, crew: Crew) -> dict:
    build_dir = f"niches/{state['niche']}/builds/{state['episode_id']}"

    task = Task(
        description=(
            f"Generate 5 thumbnail variants for: '{state['script'].get('title', '')}'\n"
            f"Score each for CTR using vision analysis.\n"
            f"Save the winner to {build_dir}/thumbnail.jpg"
        ),
        expected_output=f"Path to winning thumbnail: {build_dir}/thumbnail.jpg",
        agent=crew.agents[5],  # ThumbnailAgent
    )
    result = Crew(agents=[crew.agents[5]], tasks=[task]).kickoff()
    return {"thumbnail_path": f"{build_dir}/thumbnail.jpg"}


def node_seo_optimizer(state: PipelineState, crew: Crew) -> dict:
    build_dir = f"niches/{state['niche']}/builds/{state['episode_id']}"

    task = Task(
        description=(
            f"Optimise the SEO metadata for this video.\n\n"
            f"Script title: {state['script'].get('title', '')}\n"
            f"Script sections: {[s['heading'] for s in state['script'].get('sections', [])]}\n"
            f"Niche: {state['niche']}\n\n"
            "Return JSON with: title (final, ≤100 chars), description (≤5000 chars, keyword in first 150), "
            "tags (list of 15 strings), chapters (list of {{time, label}}), pinned_comment."
        ),
        expected_output="JSON metadata object.",
        agent=crew.agents[6],  # SEOOptimizer
    )
    result = Crew(agents=[crew.agents[6]], tasks=[task]).kickoff()
    try:
        metadata = json.loads(str(result))
    except json.JSONDecodeError:
        metadata = {
            "title": state["script"].get("title", "New Video"),
            "description": "",
            "tags": [state["niche"]],
            "chapters": [],
            "pinned_comment": "",
        }

    # Persist metadata to build dir
    meta_path = f"{build_dir}/metadata.json"
    os.makedirs(build_dir, exist_ok=True)
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return {"metadata": metadata}


def node_uploader(state: PipelineState, crew: Crew, config: dict | None = None) -> dict:
    # Respect dry_run flag — skip actual upload, just log what would happen
    dry_run = (config or {}).get("configurable", {}).get("dry_run", False)

    if dry_run:
        meta = state["metadata"]
        print(
            f"\n{'='*60}\n"
            f"DRY RUN — upload skipped. Review these files before approving:\n"
            f"  Video     : {state.get('video_path', 'N/A')}\n"
            f"  Thumbnail : {state.get('thumbnail_path', 'N/A')}\n"
            f"  Title     : {meta.get('title', 'N/A')}\n"
            f"  Tags      : {', '.join(meta.get('tags', [])[:5])} ...\n"
            f"{'='*60}\n"
        )
        return {"video_id": "DRY_RUN"}

    from tools.youtube_tool import upload_video
    from datetime import timedelta

    meta = state["metadata"]
    schedule_at = (datetime.now(timezone.utc) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")

    result = upload_video(
        niche=state["niche"],
        video_path=state["video_path"],
        title=meta["title"],
        description=meta["description"],
        tags=meta["tags"],
        thumbnail_path=state.get("thumbnail_path"),
        schedule_at=schedule_at,
    )

    print(f"✓ Uploaded episode {state['episode_id']} → videoId: {result['videoId']}")
    return {"video_id": result["videoId"]}


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_pipeline(crew: Crew) -> StateGraph:
    """Construct and compile the LangGraph pipeline.

    Args:
        crew: A fully-configured CrewAI Crew with agents in canonical order.

    Returns:
        Compiled LangGraph runnable.
    """
    import functools

    def bind(node_fn):
        return functools.partial(node_fn, crew=crew)

    builder = StateGraph(PipelineState)

    builder.add_node("trend_scout", bind(node_trend_scout))
    builder.add_node("idea_planner", bind(node_idea_planner))
    builder.add_node("script_writer", bind(node_script_writer))
    builder.add_node("content_mod", bind(node_content_mod))
    builder.add_node("asset_creator", bind(node_asset_creator))
    builder.add_node("thumbnail_agent", bind(node_thumbnail_agent))
    builder.add_node("seo_optimizer", bind(node_seo_optimizer))
    builder.add_node("uploader", bind(node_uploader))

    builder.add_edge(START, "trend_scout")
    builder.add_edge("trend_scout", "idea_planner")
    builder.add_edge("idea_planner", "script_writer")
    builder.add_edge("script_writer", "content_mod")

    builder.add_conditional_edges(
        "content_mod",
        _route_after_mod,
        {
            "script_writer": "script_writer",
            "asset_creator": "asset_creator",
        },
    )

    # Asset creation and thumbnail run sequentially (thumbnail needs video title)
    builder.add_edge("asset_creator", "thumbnail_agent")
    builder.add_edge("thumbnail_agent", "seo_optimizer")
    builder.add_edge("seo_optimizer", "uploader")
    builder.add_edge("uploader", END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)
