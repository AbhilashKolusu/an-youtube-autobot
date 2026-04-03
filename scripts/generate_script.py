#!/usr/bin/env python3
"""
generate_script.py - Call LLM for host script
"""

import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_script(topic):
    prompt = f"Write a 300-word script for a YouTube video introducing a music mix on the topic: {topic}. The host should be engaging and promote the mix."
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=500
    )
    return response.choices[0].text.strip()

def main():
    topic = "Lo-fi Study Mix"
    script = generate_script(topic)
    print(script)
    # Save to file or Google Sheet

if __name__ == '__main__':
    main()