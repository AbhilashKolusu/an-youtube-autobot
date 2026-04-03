"""
InVideo AI tool — script-to-video generation.

InVideo AI API converts a structured script into a fully assembled video
with stock footage, transitions, and auto-captions.

API docs: https://ai.invideo.io/api-docs (v3)

Workflow:
  1. POST /videos — submit script, returns job_id
  2. GET  /videos/{job_id} — poll for status
  3. On COMPLETED — download the rendered MP4
"""

import os
import time
from pathlib import Path

import requests
from crewai.tools import tool


_BASE_URL = "https://api.invideo.io/v3"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {os.environ['INVIDEO_API_KEY']}",
        "Content-Type": "application/json",
    }


@tool("InVideo Script-to-Video")
def script_to_video(
    script_json: dict,
    output_path: str,
    aspect_ratio: str = "16:9",
    resolution: str = "1080p",
    voice_url: str | None = None,
    poll_interval: int = 30,
    timeout: int = 1800,
) -> str:
    """Submit a structured script to InVideo AI and download the rendered video.

    Args:
        script_json: The script object with sections and b_roll_prompt fields.
        output_path: Local path to save the rendered MP4.
        aspect_ratio: "16:9" (landscape) or "9:16" (Shorts).
        resolution: "1080p" or "4K".
        voice_url: Optional URL to a pre-rendered ElevenLabs MP3 to use as narration.
        poll_interval: Seconds between status checks.
        timeout: Max seconds to wait before raising a timeout error.

    Returns:
        Absolute path to the downloaded MP4.
    """
    api_key = os.getenv("INVIDEO_API_KEY")
    if not api_key:
        raise EnvironmentError("INVIDEO_API_KEY is not set.")

    payload = {
        "script": script_json,
        "settings": {
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "auto_captions": True,
            "music": "auto",
        },
    }
    if voice_url:
        payload["settings"]["voiceover_url"] = voice_url

    # Submit job
    resp = requests.post(f"{_BASE_URL}/videos", headers=_headers(), json=payload, timeout=30)
    resp.raise_for_status()
    job_id = resp.json()["job_id"]

    # Poll for completion
    elapsed = 0
    while elapsed < timeout:
        time.sleep(poll_interval)
        elapsed += poll_interval
        status_resp = requests.get(
            f"{_BASE_URL}/videos/{job_id}", headers=_headers(), timeout=10
        )
        status_resp.raise_for_status()
        data = status_resp.json()

        if data["status"] == "COMPLETED":
            download_url = data["download_url"]
            break
        elif data["status"] == "FAILED":
            raise RuntimeError(f"InVideo job {job_id} failed: {data.get('error')}")
    else:
        raise TimeoutError(f"InVideo job {job_id} did not complete within {timeout}s")

    # Download rendered video
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with requests.get(download_url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    return str(Path(output_path).resolve())
