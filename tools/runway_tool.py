"""
Runway Gen-4.5 tool — generates cinematic AI video clips from text prompts.

Used by AssetCreator for hero shots and key visual moments that stock
footage cannot cover (e.g. "futuristic trading floor at night", "DNA strand
glowing under microscope").

API docs: https://docs.runwayml.com/api-reference
Model: gen4_turbo (fastest, best quality for b-roll clips)

Clip specs:
  - Duration: 5s or 10s
  - Resolution: 1280×768 (landscape) or 768×1280 (portrait/Shorts)
"""

import os
import time
from pathlib import Path

import requests
from crewai.tools import tool


_BASE_URL = "https://api.runwayml.com/v1"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {os.environ['RUNWAY_API_KEY']}",
        "Content-Type": "application/json",
        "X-Runway-Version": "2024-11-06",
    }


@tool("Runway Generate Clip")
def generate_clip(
    prompt: str,
    output_path: str,
    duration: int = 10,
    aspect_ratio: str = "1280:768",
    model: str = "gen4_turbo",
    poll_interval: int = 15,
    timeout: int = 600,
) -> str:
    """Generate a cinematic video clip from a text prompt using Runway Gen-4.

    Args:
        prompt: Detailed visual description of the clip.
        output_path: Local path to save the rendered MP4.
        duration: Clip length in seconds (5 or 10).
        aspect_ratio: "1280:768" (landscape) or "768:1280" (portrait).
        model: Runway model name.
        poll_interval: Seconds between status checks.
        timeout: Max seconds to wait.

    Returns:
        Absolute path to the downloaded MP4 clip.
    """
    api_key = os.getenv("RUNWAY_API_KEY")
    if not api_key:
        raise EnvironmentError("RUNWAY_API_KEY is not set.")

    payload = {
        "model": model,
        "prompt_text": prompt,
        "duration": duration,
        "ratio": aspect_ratio,
    }

    resp = requests.post(
        f"{_BASE_URL}/image_to_video",
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    task_id = resp.json()["id"]

    # Poll for completion
    elapsed = 0
    while elapsed < timeout:
        time.sleep(poll_interval)
        elapsed += poll_interval
        status_resp = requests.get(
            f"{_BASE_URL}/tasks/{task_id}", headers=_headers(), timeout=10
        )
        status_resp.raise_for_status()
        data = status_resp.json()

        if data["status"] == "SUCCEEDED":
            download_url = data["output"][0]
            break
        elif data["status"] in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"Runway task {task_id} failed: {data.get('failure')}")
    else:
        raise TimeoutError(f"Runway task {task_id} did not complete within {timeout}s")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with requests.get(download_url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    return str(Path(output_path).resolve())
