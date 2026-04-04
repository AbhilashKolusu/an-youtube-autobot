"""
AssetCreatorAgent — converts the approved script into a full video.

Pipeline:
  1. Script narration → ElevenLabs TTS (MP3)
  2. Section b-roll prompts → Pexels stock footage + FFmpeg assembly (base video)
  3. Hero / cinematic shots → Runway Gen-4.5 (key moments)
  4. Final merged MP4 with narration + captions → output

Output: niches/{niche}/builds/{episode_id}/final.mp4
"""

from crewai import Agent
from tools import elevenlabs_tool, video_assembler_tool, runway_tool


def build_asset_creator(llm) -> Agent:
    return Agent(
        role="Asset Creator",
        goal=(
            "Produce a complete, broadcast-ready MP4 video for episode {episode_id} "
            "using the approved script. Generate narration audio, assemble stock-footage "
            "visuals via Pexels, render cinematic hero clips with Runway, and output "
            "a single merged file."
        ),
        backstory=(
            "You are a multimodal AI production studio in a single agent. You "
            "orchestrate ElevenLabs for natural voiceover, the video assembler for "
            "rapid stock-footage assembly with FFmpeg, and Runway for cinematic AI-generated "
            "hero shots. You always verify audio-video sync and caption accuracy "
            "before signing off on a render."
        ),
        tools=[
            elevenlabs_tool.text_to_speech,
            video_assembler_tool.assemble_video,
            runway_tool.generate_clip,
        ],
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )
