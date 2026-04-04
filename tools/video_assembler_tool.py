"""
Video assembler tool — builds a full YouTube video locally using:
  1. Pexels API       — free stock footage clips per b-roll prompt
  2. FFmpeg           — merges clips, overlays narration audio, adds captions
  3. No paid video API needed

Pipeline per section:
  search Pexels for b_roll_prompt → download best clip → trim to narration duration
  → concat all clips → overlay narration MP3 → burn SRT captions → output final.mp4

Pexels free tier: 200 requests/hour, 20,000/month — plenty for daily videos.
Get API key at: pexels.com/api/
"""

import os
import subprocess
import tempfile
import textwrap
from pathlib import Path

import requests
from crewai.tools import tool


_PEXELS_BASE = "https://api.pexels.com/videos"


def _pexels_headers() -> dict:
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        raise EnvironmentError("PEXELS_API_KEY is not set.")
    return {"Authorization": api_key}


def _search_pexels_clip(query: str, min_duration: int = 5) -> str | None:
    """Search Pexels for a video clip matching the query. Returns download URL or None."""
    try:
        resp = requests.get(
            f"{_PEXELS_BASE}/search",
            headers=_pexels_headers(),
            params={"query": query, "per_page": 5, "orientation": "landscape"},
            timeout=10,
        )
        resp.raise_for_status()
        videos = resp.json().get("videos", [])
        for video in videos:
            # Pick an HD file (720p or 1080p)
            for file in sorted(video.get("video_files", []), key=lambda f: f.get("height", 0), reverse=True):
                if file.get("height", 0) >= 720 and file.get("file_type") == "video/mp4":
                    return file["link"]
    except Exception:
        pass
    return None


def _download_file(url: str, dest: str) -> bool:
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    f.write(chunk)
        return True
    except Exception:
        return False


def _ffprobe_duration(path: str) -> float:
    """Get duration of a media file in seconds."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", path],
            capture_output=True, text=True, timeout=30,
        )
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def _build_srt(sections: list[dict], audio_path: str) -> str:
    """Generate a simple SRT caption file from script sections."""
    duration = _ffprobe_duration(audio_path)
    if not sections or duration == 0:
        return ""

    lines = []
    per_section = duration / len(sections)
    for i, section in enumerate(sections):
        start = i * per_section
        end = start + per_section
        text = section.get("heading", f"Section {i+1}")
        # Wrap long headings
        wrapped = "\n".join(textwrap.wrap(text, width=50))

        def fmt(sec: float) -> str:
            h = int(sec // 3600)
            m = int((sec % 3600) // 60)
            s = int(sec % 60)
            ms = int((sec % 1) * 1000)
            return f"{h:02}:{m:02}:{s:02},{ms:03}"

        lines.append(f"{i+1}\n{fmt(start)} --> {fmt(end)}\n{wrapped}\n")

    return "\n".join(lines)


@tool("Assemble YouTube Video")
def assemble_video(
    script_json: dict,
    narration_path: str,
    output_path: str,
    resolution: str = "1920x1080",
) -> str:
    """Build a complete YouTube video from a script and narration audio.

    Steps:
      1. For each script section, search Pexels for a matching stock clip
      2. Download and trim each clip to fit the section's time allocation
      3. Concatenate all clips
      4. Overlay the narration MP3 audio track
      5. Burn in section-heading captions (SRT)
      6. Output a single MP4 to output_path

    Args:
        script_json: Script object with 'sections' list (each has 'heading', 'b_roll_prompt').
        narration_path: Path to the ElevenLabs narration MP3.
        output_path: Where to write the final merged MP4.
        resolution: Output resolution (default 1920x1080).

    Returns:
        Absolute path to the assembled MP4.
    """
    sections = script_json.get("sections", [])
    if not sections:
        raise ValueError("script_json must have at least one section.")

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    audio_duration = _ffprobe_duration(narration_path)
    if audio_duration == 0:
        raise RuntimeError(f"Could not read duration of narration: {narration_path}")

    per_section_dur = audio_duration / len(sections)
    width, height = resolution.split("x")

    with tempfile.TemporaryDirectory() as tmpdir:
        clip_paths = []

        for i, section in enumerate(sections):
            query = section.get("b_roll_prompt") or section.get("heading", "nature landscape")
            clip_url = _search_pexels_clip(query)

            raw_clip = os.path.join(tmpdir, f"raw_{i}.mp4")
            trimmed_clip = os.path.join(tmpdir, f"clip_{i}.mp4")

            if clip_url and _download_file(clip_url, raw_clip):
                # Trim/loop to exact duration, scale to target resolution
                subprocess.run([
                    "ffmpeg", "-y",
                    "-stream_loop", "-1",          # loop if clip is shorter than needed
                    "-i", raw_clip,
                    "-t", str(per_section_dur),
                    "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                           f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1",
                    "-r", "30",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                    "-an",
                    trimmed_clip,
                ], check=True, capture_output=True, timeout=120)
            else:
                # Fallback: black frame clip
                subprocess.run([
                    "ffmpeg", "-y",
                    "-f", "lavfi", "-i", f"color=c=black:s={width}x{height}:r=30",
                    "-t", str(per_section_dur),
                    "-c:v", "libx264", "-preset", "fast",
                    "-an",
                    trimmed_clip,
                ], check=True, capture_output=True, timeout=60)

            clip_paths.append(trimmed_clip)

        # Write concat list
        concat_list = os.path.join(tmpdir, "concat.txt")
        with open(concat_list, "w") as f:
            for p in clip_paths:
                f.write(f"file '{p}'\n")

        # Concatenate all clips into silent base video
        base_video = os.path.join(tmpdir, "base.mp4")
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0", "-i", concat_list,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            base_video,
        ], check=True, capture_output=True, timeout=300)

        # Build SRT captions
        srt_content = _build_srt(sections, narration_path)
        srt_path = os.path.join(tmpdir, "captions.srt")
        with open(srt_path, "w") as f:
            f.write(srt_content)

        # Merge: base video + narration audio + burn captions
        subprocess.run([
            "ffmpeg", "-y",
            "-i", base_video,
            "-i", narration_path,
            "-vf", f"subtitles={srt_path}:force_style='FontSize=22,PrimaryColour=&HFFFFFF,OutlineColour=&H000000,Outline=2,Bold=1'",
            "-c:v", "libx264", "-preset", "fast", "-crf", "21",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            output_path,
        ], check=True, capture_output=True, timeout=600)

    return str(Path(output_path).resolve())
