# An-YouTube-Autobot

A presenter-driven YouTube channel that auto-publishes content for multiple niches. Each niche has its own automated workflow from script generation to final promotion and analytics reporting.

## Features

- Multi-niche support (e.g., music mixes, tech reviews)
- Automated topic ideation from Google Trends
- Script generation with LLM
- Video recording with teleprompter
- Automated video editing with DaVinci Resolve or FFmpeg
- Content-specific generation (music, thumbnails, etc.)
- YouTube upload and scheduling
- Social media promotion
- Analytics reporting
- Daily automated posting

## Setup

1. Create a new niche: `python3 scripts/create_niche.py <niche_name>`
2. Configure environment: Copy `.env.example` to `.env` and customize for each niche
3. Set up APIs and credentials in `niches/<niche>/configs/`
4. Install dependencies: `pip install -r requirements.txt`
5. Run daily scheduler: `python3 scripts/daily_scheduler.py`

See [docs/SOP.md](docs/SOP.md) for detailed setup instructions.

## Repository Structure

```
youtube-automation/
│
├─ .github/                     # GitHub Actions (optional CI)
│   └─ workflows/
│       └─ process.yml
│
├─ niches/                      # Niche-specific content
│   ├─ music-mix/               # Music mix niche
│   │   ├─ configs/             # Niche-specific configs
│   │   ├─ scripts/             # Niche-specific scripts (if any)
│   │   ├─ assets/              # Templates, backgrounds
│   │   ├─ recordings/          # Raw footage
│   │   ├─ builds/              # Build outputs
│   │   └─ docs/                # Niche docs
│   └─ tech-reviews/            # Another niche example
│
├─ scripts/                     # Common scripts
│   ├─ create_niche.py          # Create new niche
│   ├─ daily_scheduler.py       # Daily automation runner
│   ├─ topics.py                # Trend analysis
│   ├─ generate_script.py       # Script generation
│   ├─ watch.py                 # Folder monitoring
│   ├─ music_prompt.py          # Music generation (niche-specific)
│   ├─ resolve_edit.py          # Video editing
│   ├─ ffmpeg_edit.sh           # FFmpeg fallback
│   ├─ thumbnail.py             # Thumbnail creation
│   ├─ youtube_upload.py        # YouTube upload
│   ├─ social_blast.py          # Social promotion
│   └─ weekly_report.py         # Analytics
│
├─ template/                    # Template for new niches
│
├─ docs/
│   ├─ README.md
│   └─ SOP.md                   # Standard operating procedures
│
└─ .env.example                 # Sample env variables
```

## Creating a New Niche

1. Run `python3 scripts/create_niche.py my-new-niche`
2. Customize the niche-specific scripts in `niches/my-new-niche/scripts/`
3. Update `scripts/daily_scheduler.py` to include the new niche
4. Configure APIs and settings

## Daily Automation

The `daily_scheduler.py` runs at 9 AM daily, executing the full pipeline for each niche:
- Topic research
- Script generation
- (Manual recording step)
- Automated editing and upload

For fully automated channels, integrate AI video generation tools.