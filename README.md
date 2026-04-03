# An-YouTube-Autobot

A presenter-driven YouTube channel that auto-publishes 2-3 minute "Music Mix" episodes. Each episode features a human host introducing a newly-composed, genre-blended instrumental mix (lo-fi, synth-wave, ambient, etc.). The workflow is fully automated from script generation to final promotion and analytics reporting.

## Features

- Automated topic ideation from Google Trends
- Script generation with LLM
- Video recording with teleprompter
- Automated video editing with DaVinci Resolve or FFmpeg
- Music mix generation using AI prompts
- Thumbnail generation
- YouTube upload and scheduling
- Social media promotion
- Analytics reporting

## Setup

See [docs/SOP.md](docs/SOP.md) for detailed setup instructions.

## Repository Structure

```
youtube-music-mix-automation/
│
├─ .github/                     # GitHub Actions (optional CI)
│   └─ workflows/
│       └─ process.yml
│
├─ configs/
│   ├─ youtube_oauth.json        # YouTube API credentials (keep secret)
│   ├─ google_sheets.json        # Service-account key
│   └─ zapier_webhook_urls.json # Social webhook endpoints
│
├─ scripts/
│   ├─ topics.py                 # Pull trends & write to Sheet
│   ├─ generate_script.py        # Call LLM for host script
│   ├─ watch.py                  # Watch folder → trigger pipeline
│   ├─ music_prompt.py           # Send Music-Mix prompt to LLM/MusicAI
│   ├─ resolve_edit.py           # DaVinci Resolve automation
│   ├─ ffmpeg_edit.sh            # FFmpeg fallback batch script
│   ├─ thumbnail.py               # Canva API thumbnail creator
│   ├─ youtube_upload.py         # YouTube Data API uploader
│   ├─ social_blast.py           # Zapier/Make trigger via webhook
│   └─ weekly_report.py          # Analytics → Slack/email
│
├─ assets/
│   ├─ templates/
│   │   ├─ intro.mov
│   │   ├─ outro.mov
│   │   └─ lower_third.fusion
│   └─ bg_lofi.png                # Base thumbnail background
│
├─ recordings/
│   └─ host/                       # Raw host footage (auto-watched)
│
├─ builds/
│   └─ {episode_id}/               # All intermediate files per episode
│
├─ docs/
│   ├─ README.md
│   └─ SOP.md                     # Standard operating procedures
│
└─ .env.example                   # Sample env variables (API keys, paths)
```

## License

[Add license here]