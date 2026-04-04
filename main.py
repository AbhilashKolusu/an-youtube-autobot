"""
main.py — Entry point for the an-youtube-autobot pipeline.

Run modes:
  1. Single run (manual / n8n webhook trigger):
       python main.py --niche personal-finance

  2. Daily scheduler (standalone, no n8n):
       python main.py --schedule

  3. Analytics-only (post-upload feedback loop):
       python main.py --analytics --niche personal-finance --video-id abc123

  4. All niches in sequence:
       python main.py --all

  5. Dry run — full pipeline, NO YouTube upload (review before publishing):
       python main.py --niche personal-finance --dry-run

  6. Approve a dry-run episode and upload it:
       python main.py --approve --niche personal-finance --episode-id personal-finance_20260403

The pipeline runs as a LangGraph stateful graph with CrewAI agents at each node.
State is checkpointed so individual failed nodes can be retried without
re-running the full pipeline.
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timezone

import schedule
import time
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/pipeline.log", mode="a"),
    ],
)
log = logging.getLogger("main")

# Supported niches — add more as channels are created
NICHES = [
    "personal-finance",
    "ai-tools",
    "health-longevity",
]


def run_pipeline(niche: str, date: str | None = None, dry_run: bool = False) -> dict:
    """Run the full video pipeline for a single niche.

    Args:
        niche: Niche slug (must have a niches/{niche}/ directory).
        date: Override date string (YYYY-MM-DD). Defaults to today UTC.
        dry_run: If True, skip the YouTube upload step. Output stays in builds/.

    Returns:
        Final pipeline state dict.
    """
    from crew import build_crew
    from workflows.pipeline import build_pipeline, PipelineState

    run_date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    episode_id = f"{niche}_{run_date.replace('-', '')}"

    mode = "DRY RUN (no upload)" if dry_run else "LIVE"
    log.info(f"Starting pipeline [{mode}] | niche={niche} | date={run_date} | episode={episode_id}")

    crew = build_crew(niche=niche)
    pipeline = build_pipeline(crew=crew)

    initial_state: PipelineState = {
        "niche": niche,
        "date": run_date,
        "episode_id": episode_id,
        "trends": [],
        "brief": {},
        "script": {},
        "mod_approved": False,
        "mod_issues": [],
        "mod_revision_count": 0,
        "narration_path": "",
        "video_path": "",
        "thumbnail_path": "",
        "metadata": {},
        "video_id": "",
        "analytics": {},
    }

    config = {"configurable": {"thread_id": episode_id, "dry_run": dry_run}}
    final_state = pipeline.invoke(initial_state, config=config)

    build_dir = f"niches/{niche}/builds/{episode_id}"
    if dry_run:
        log.info(
            f"DRY RUN complete | niche={niche} | episode={episode_id}\n"
            f"  Review files in: {build_dir}/\n"
            f"  Script:       {build_dir}/metadata.json\n"
            f"  Video:        {build_dir}/final.mp4\n"
            f"  Thumbnail:    {build_dir}/thumbnail.jpg\n"
            f"  To upload:    python main.py --approve --niche {niche} --episode-id {episode_id}"
        )
    else:
        log.info(
            f"Pipeline complete | niche={niche} | videoId={final_state.get('video_id', 'N/A')}"
        )
    return final_state


def _approve_and_upload(niche: str, episode_id: str):
    """Upload a dry-run episode after human review."""
    import json
    from tools.youtube_tool import upload_video
    from datetime import timedelta

    build_dir = f"niches/{niche}/builds/{episode_id}"
    meta_path = f"{build_dir}/metadata.json"
    video_path = f"{build_dir}/final.mp4"
    thumb_path = f"{build_dir}/thumbnail.jpg"

    if not os.path.exists(meta_path):
        log.error(f"metadata.json not found at {meta_path}. Run the pipeline first.")
        return
    if not os.path.exists(video_path):
        log.error(f"final.mp4 not found at {video_path}. Run the pipeline first.")
        return

    with open(meta_path) as f:
        meta = json.load(f)

    log.info(f"Uploading approved episode: {episode_id}")
    log.info(f"  Title: {meta['title']}")

    schedule_at = (datetime.now(timezone.utc) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    result = upload_video(
        niche=niche,
        video_path=video_path,
        title=meta["title"],
        description=meta["description"],
        tags=meta["tags"],
        thumbnail_path=thumb_path if os.path.exists(thumb_path) else None,
        schedule_at=schedule_at,
    )
    log.info(f"Uploaded successfully | videoId={result['videoId']} | scheduled for +2h")


def run_analytics(niche: str, video_id: str, days_back: int = 1):
    """Pull analytics for an uploaded video and log insights.

    Called 24h and 7d after upload (via n8n delayed trigger or cron).
    """
    from crew import build_crew
    from crewai import Crew, Task
    import agents as ag

    log.info(f"Fetching analytics | niche={niche} | videoId={video_id} | days_back={days_back}")

    from crewai import LLM
    llm = LLM(model="anthropic/claude-sonnet-4-6", api_key=os.environ["ANTHROPIC_API_KEY"], max_tokens=8096)
    analytics_agent = ag.build_analytics_agent(llm)

    task = Task(
        description=(
            f"Fetch {days_back}-day analytics for videoId={video_id} in niche={niche}. "
            "Compare against channel benchmarks and write an insights memo with 3 specific "
            "improvements for the next video. Save to logs/analytics/{video_id}.json"
        ).format(video_id=video_id),
        expected_output="Insights memo saved as JSON.",
        agent=analytics_agent,
    )

    Crew(agents=[analytics_agent], tasks=[task]).kickoff(
        inputs={"niche": niche, "video_id": video_id, "days_back": days_back}
    )


def daily_job():
    """Run all niches sequentially. Scheduled by the built-in scheduler."""
    log.info("=== Daily pipeline run starting ===")
    for niche in NICHES:
        try:
            run_pipeline(niche)
        except Exception as e:
            log.error(f"Pipeline failed for niche={niche}: {e}", exc_info=True)
    log.info("=== Daily pipeline run complete ===")


def main():
    os.makedirs("logs", exist_ok=True)
    os.makedirs("logs/analytics", exist_ok=True)

    parser = argparse.ArgumentParser(description="an-youtube-autobot pipeline runner")
    parser.add_argument("--niche", type=str, help="Run pipeline for a specific niche")
    parser.add_argument("--all", action="store_true", help="Run all niches in sequence")
    parser.add_argument("--schedule", action="store_true", help="Start daily scheduler (6 AM UTC)")
    parser.add_argument("--analytics", action="store_true", help="Run analytics-only mode")
    parser.add_argument("--video-id", type=str, help="Video ID for analytics mode")
    parser.add_argument("--days-back", type=int, default=1, help="Days back for analytics")
    parser.add_argument("--date", type=str, help="Override date (YYYY-MM-DD) for testing")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run full pipeline but SKIP YouTube upload — saves to builds/ for review")
    parser.add_argument("--approve", action="store_true",
                        help="Upload a previously dry-run episode after your review")
    parser.add_argument("--episode-id", type=str, help="Episode ID for --approve mode")
    args = parser.parse_args()

    if args.approve:
        if not args.niche or not args.episode_id:
            parser.error("--approve requires --niche and --episode-id")
        _approve_and_upload(args.niche, args.episode_id)

    elif args.analytics:
        if not args.niche or not args.video_id:
            parser.error("--analytics requires --niche and --video-id")
        run_analytics(args.niche, args.video_id, args.days_back)

    elif args.schedule:
        log.info("Scheduler mode: pipeline will run daily at 06:00 UTC")
        schedule.every().day.at("06:00").do(daily_job)
        while True:
            schedule.run_pending()
            time.sleep(60)

    elif args.all:
        daily_job()

    elif args.niche:
        run_pipeline(args.niche, date=args.date, dry_run=args.dry_run)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
