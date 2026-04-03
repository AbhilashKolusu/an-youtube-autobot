#!/usr/bin/env python3
"""
ai_news_generator.py - Generate AI news content for the niche
"""

import requests
import openai
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

def fetch_ai_news():
    # Example: Fetch from a news API or scrape
    # For demo, use a placeholder
    news_sources = [
        "https://techcrunch.com/tag/artificial-intelligence/",
        "https://www.theverge.com/ai-artificial-intelligence",
        # Add more sources
    ]
    # In real implementation, scrape or use APIs like NewsAPI
    return ["AI breakthrough in quantum computing", "New GPT model released", "AI ethics debate heats up"]

def generate_script_from_news(news_items):
    prompt = f"Write a 300-word script for a YouTube video discussing recent AI news: {', '.join(news_items)}. Make it engaging for viewers interested in AI."
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=500
    )
    return response.choices[0].text.strip()

def main():
    news = fetch_ai_news()
    script = generate_script_from_news(news)
    print(script)
    # Save to file or Google Sheet

if __name__ == '__main__':
    main()