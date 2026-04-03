#!/usr/bin/env python3
"""
generate_script.py - Call LLM for host script
"""

import openai
import os
import json
import argparse
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_content(niche, topic):
    # 1. Generate the Script
    script_prompt = f"Write a 300-word YouTube script for the niche '{niche}' about '{topic}'. Make it engaging and high-energy."
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=script_prompt,
        max_tokens=500
    )
    script = response.choices[0].text.strip()

    # 2. Generate Metadata (Title, Description, Tags)
    metadata_prompt = f"""
    Based on this script: '{script}', generate:
    1. A catchy YouTube Title.
    2. A SEO-friendly Description (including social links).
    3. A comma-separated list of 10 relevant tags.
    Return as a JSON object with keys: title, description, tags.
    """
    meta_response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=metadata_prompt,
        max_tokens=300
    )
    
    try:
        metadata = json.loads(meta_response.choices[0].text.strip())
    except:
        metadata = {"title": topic, "description": "New upload!", "tags": "automation, youtube"}

    return script, metadata

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--niche", required=True)
    parser.add_argument("--topic", required=True)
    parser.add_argument("--episode_id", required=True)
    args = parser.parse_args()

    script, metadata = generate_content(args.niche, args.topic)
    
    # Save metadata for the uploader
    output_path = f"niches/{args.niche}/builds/{args.episode_id}/metadata.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metadata, f)
    
    print(f"Script and Metadata generated for {args.episode_id}")

if __name__ == '__main__':
    main()