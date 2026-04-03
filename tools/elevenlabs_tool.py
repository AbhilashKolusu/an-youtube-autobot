"""
ElevenLabs TTS tool — converts script narration to MP3.

Recommended voices for faceless channels:
  - "Rachel"   : warm, authoritative (finance / health)
  - "Adam"     : deep, confident (tech / AI docs)
  - "Antoni"   : friendly, energetic (curiosity / mystery)

Model: eleven_multilingual_v2 (best prosody, supports 29 languages)
"""

import os
from pathlib import Path

from crewai.tools import tool
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings


_client: ElevenLabs | None = None


def _get_client() -> ElevenLabs:
    global _client
    if _client is None:
        _client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
    return _client


@tool("ElevenLabs Text-to-Speech")
def text_to_speech(
    text: str,
    output_path: str,
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Rachel
    model_id: str = "eleven_multilingual_v2",
    stability: float = 0.45,
    similarity_boost: float = 0.80,
    style: float = 0.20,
) -> str:
    """Convert narration text to an MP3 file using ElevenLabs.

    Args:
        text: The narration script (plain text, no SSML).
        output_path: Where to save the MP3 (e.g. builds/ep001/narration.mp3).
        voice_id: ElevenLabs voice ID.
        model_id: ElevenLabs model ID.
        stability: Voice stability (0–1). Lower = more expressive.
        similarity_boost: Voice similarity boost (0–1).
        style: Speaking style exaggeration (0–1).

    Returns:
        Absolute path to the saved MP3 file.
    """
    client = _get_client()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    audio_generator = client.generate(
        text=text,
        voice=voice_id,
        model=model_id,
        voice_settings=VoiceSettings(
            stability=stability,
            similarity_boost=similarity_boost,
            style=style,
            use_speaker_boost=True,
        ),
    )

    with open(output_path, "wb") as f:
        for chunk in audio_generator:
            f.write(chunk)

    return str(Path(output_path).resolve())


@tool("ElevenLabs List Voices")
def list_voices() -> list[dict]:
    """List all available ElevenLabs voices for the account.

    Returns a list of dicts with voice_id, name, and labels.
    """
    client = _get_client()
    response = client.voices.get_all()
    return [
        {"voice_id": v.voice_id, "name": v.name, "labels": v.labels}
        for v in response.voices
    ]
