"""
Runway Gen-4.5 tool — generates cinematic AI video clips from text prompts.

Uses the official runwayml Python SDK.
API docs: https://docs.dev.runwayml.com/api/
Env var:  RUNWAYML_API_SECRET  (set in .env)

Models:
  gen4.5        — recommended (balanced quality/cost)
  gen4_turbo    — budget option (requires image input)

Clip specs:
  - Duration: 5 or 10 seconds
  - Ratio: "1280:720" (landscape) or "720:1280" (portrait/Shorts)
"""

import os
from pathlib import Path

import requests
from crewai.tools import tool


@tool("Runway Generate Clip")
def generate_clip(
    prompt: str,
    output_path: str,
    duration: int = 5,
    ratio: str = "1280:720",
    model: str = "gen4.5",
) -> str:
    """Generate a cinematic video clip from a text prompt using Runway Gen-4.5.

    Args:
        prompt: Detailed visual description of the clip.
        output_path: Local path to save the rendered MP4.
        duration: Clip length in seconds (5 or 10).
        ratio: "1280:720" (landscape) or "720:1280" (portrait).
        model: Runway model — "gen4.5" (default) or "gen4_turbo".

    Returns:
        Absolute path to the downloaded MP4 clip.
    """
    api_key = os.getenv("RUNWAYML_API_SECRET") or os.getenv("RUNWAY_API_KEY")
    if not api_key:
        raise EnvironmentError("RUNWAYML_API_SECRET is not set.")

    try:
        from runwayml import RunwayML
    except ImportError:
        raise ImportError("Install the Runway SDK: pip install runwayml")

    client = RunwayML(api_key=api_key)

    task = client.text_to_video.create(
        model=model,
        prompt_text=prompt,
        ratio=ratio,
        duration=duration,
    ).wait_for_task_output()

    download_url = task.output[0]

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with requests.get(download_url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    return str(Path(output_path).resolve())
