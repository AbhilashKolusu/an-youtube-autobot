#!/usr/bin/env python3
"""
music_prompt.py - Send Music-Mix prompt to LLM/MusicAI
"""

import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

MUSIC_PROMPT = """
You are a professional music producer.
Task: Compose a 4-8-minute instrumental mix that blends lo-fi hip-hop, chillhop, synth-wave, ambient, and EDM.
[Full prompt from user query]
"""

def generate_music_prompt(title):
    prompt = MUSIC_PROMPT.replace("[Insert episode-specific title]", title)
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1000
    )
    return response.choices[0].text.strip()

def main():
    title = "Midnight Study Vibes – Lo-Fi × Chill-Synth Fusion"
    result = generate_music_prompt(title)
    print(result)
    # Save WAV or project files

if __name__ == '__main__':
    main()