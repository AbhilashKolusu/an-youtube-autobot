"""
Flux image generation tool — creates thumbnail images via Replicate API.

Model: black-forest-labs/flux-schnell (fast, free-tier eligible)
Upgrade to flux-dev or flux-pro for higher quality at extra cost.

Thumbnail spec:
  - 1280×720 (YouTube standard thumbnail)
  - Bold text overlay is handled separately via Pillow after generation
"""

import os
import time
from pathlib import Path

import requests
from crewai.tools import tool


_BASE_URL = "https://api.replicate.com/v1"
_MODEL = "black-forest-labs/flux-schnell"


def _headers() -> dict:
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        raise EnvironmentError("REPLICATE_API_TOKEN is not set.")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Prefer": "wait",
    }


@tool("Flux Generate Thumbnail Image")
def generate_thumbnail(
    prompt: str,
    output_path: str,
    width: int = 1280,
    height: int = 720,
    num_inference_steps: int = 4,
    poll_interval: int = 5,
    timeout: int = 120,
) -> str:
    """Generate a YouTube thumbnail image from a text prompt using Flux.

    Args:
        prompt: Detailed visual description. Include style keywords like
                'photorealistic', 'cinematic lighting', 'bold composition'.
        output_path: Local path to save the generated image (JPG or PNG).
        width: Image width in pixels (default 1280 for 16:9 thumbnail).
        height: Image height in pixels (default 720 for 16:9 thumbnail).
        num_inference_steps: Flux-schnell works best at 4 steps (fast).
                             Increase to 8-20 for flux-dev/pro variants.
        poll_interval: Seconds between status checks (used if async).
        timeout: Max seconds to wait for generation.

    Returns:
        Absolute path to the saved image file.
    """
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        raise EnvironmentError("REPLICATE_API_TOKEN is not set.")

    payload = {
        "input": {
            "prompt": prompt,
            "width": width,
            "height": height,
            "num_inference_steps": num_inference_steps,
            "output_format": "jpg",
            "output_quality": 95,
        }
    }

    # Use the models endpoint for latest version
    resp = requests.post(
        f"{_BASE_URL}/models/{_MODEL}/predictions",
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    # Prefer: wait means Replicate may return completed result immediately
    if data.get("status") == "succeeded" and data.get("output"):
        image_url = data["output"][0] if isinstance(data["output"], list) else data["output"]
    else:
        # Poll for completion
        prediction_id = data["id"]
        elapsed = 0
        image_url = None
        while elapsed < timeout:
            time.sleep(poll_interval)
            elapsed += poll_interval
            poll_resp = requests.get(
                f"{_BASE_URL}/predictions/{prediction_id}",
                headers=_headers(),
                timeout=10,
            )
            poll_resp.raise_for_status()
            poll_data = poll_resp.json()
            if poll_data["status"] == "succeeded":
                output = poll_data.get("output")
                image_url = output[0] if isinstance(output, list) else output
                break
            elif poll_data["status"] in ("failed", "canceled"):
                raise RuntimeError(
                    f"Flux prediction {prediction_id} failed: {poll_data.get('error')}"
                )
        if not image_url:
            raise TimeoutError(f"Flux prediction did not complete within {timeout}s")

    # Download the image
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with requests.get(image_url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    return str(Path(output_path).resolve())
