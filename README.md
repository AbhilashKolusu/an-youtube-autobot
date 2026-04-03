# an-youtube-autobot

Fully autonomous YouTube video pipeline (2026 edition). Produces and publishes daily faceless videos across multiple high-RPM niches using a CrewAI multi-agent crew + LangGraph stateful orchestration.

## Architecture

```
n8n Cron (06:00 UTC)
        │
        ▼
   main.py / webhook
        │
        ▼
  LangGraph Pipeline  ←── MemorySaver (resumable state)
        │
  ┌─────┴──────────────────────────────────┐
  │                                        │
  ▼                                        ▼
TrendScoutAgent            (parallel at each node)
  │  YouTube Data API v3
  │  Perplexity search
  │  vidIQ keyword scores
  ▼
IdeaPlannerAgent
  │  Selects 1 idea → creative brief
  ▼
ScriptWriterAgent
  │  Full script + b-roll prompts
  ▼
ContentModAgent  ──(issues)──→ ScriptWriter (max 2 retries)
  │  (approved)
  ├──────────────────┐
  ▼                  ▼
AssetCreatorAgent  ThumbnailAgent
  │ ElevenLabs TTS    │ Flux/Grok Imagine × 5
  │ InVideo base vid  │ Vision CTR scoring
  │ Runway hero clips │ Pick winner
  └──────┬────────────┘
         ▼
   SEOOptimizerAgent
     │ vidIQ keyword data
     │ Final title/desc/tags/chapters
     ▼
  YouTubeUploaderAgent
     │ Upload private → schedule public (+2h)
     │ Set thumbnail
     ▼
  [next day] AnalyticsAgent
     │ 24h + 7d performance pull
     │ Insights memo → feeds next TrendScout
     ▼
   logs/analytics/{video_id}.json
```

**Stack:**

| Layer | Tool |
|-------|------|
| Orchestration | CrewAI (hierarchical crew) + LangGraph (state machine) |
| Manager LLM | Claude claude-opus-4-6 |
| Worker LLM | Claude Sonnet 4.6 |
| Trend research | YouTube Data API v3 + Perplexity sonar-pro |
| SEO | vidIQ API |
| Voiceover | ElevenLabs `eleven_multilingual_v2` |
| Base video | InVideo AI v3 |
| Cinematic clips | Runway Gen-4.5 |
| Uploader | YouTube Data API v3 (OAuth) |
| Analytics | YouTube Analytics API v2 |
| Scheduler | n8n cron (recommended) or built-in `schedule` |

---

## Niches

| Niche | CPM Target | Schedule |
|-------|-----------|----------|
| `personal-finance` | $18 | Mon / Wed / Fri |
| `ai-tools` | $14 | Tue / Thu / Sat |
| `health-longevity` | $15 | Mon / Thu |

---

## Quick Start

### 1. Install dependencies
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Fill in ANTHROPIC_API_KEY, YOUTUBE_API_KEY, ELEVENLABS_API_KEY, etc.
```

### 3. Set up YouTube OAuth (once per channel)
```bash
# Follow Google OAuth flow — saves token to niches/{niche}/configs/youtube_oauth.json
python scripts/youtube_upload.py --niche personal-finance --path /dev/null --episode_id test
```

### 4. Run pipeline
```bash
# Single niche, today's date
python main.py --niche personal-finance

# All niches
python main.py --all

# Daily scheduler (stays running, fires at 06:00 UTC)
python main.py --schedule

# Pull analytics for an uploaded video
python main.py --analytics --niche personal-finance --video-id dQw4w9WgXcQ --days-back 1
```

### 5. n8n trigger (recommended for production)
Configure an n8n **Cron** node → **HTTP Request** node → `POST http://your-host:8000/run?niche=personal-finance`

---

## Repository Structure

```
an-youtube-autobot/
├── agents/                     # CrewAI agent definitions (1 file per agent)
│   ├── trend_scout.py
│   ├── idea_planner.py
│   ├── script_writer.py
│   ├── content_mod.py
│   ├── asset_creator.py
│   ├── thumbnail_agent.py
│   ├── seo_optimizer.py
│   └── analytics_agent.py
│
├── tools/                      # API wrapper tools used by agents
│   ├── youtube_tool.py         # YouTube Data API v3 + Analytics API
│   ├── elevenlabs_tool.py      # TTS
│   ├── vidiq_tool.py           # Keyword research
│   ├── invideo_tool.py         # Script-to-video
│   ├── runway_tool.py          # Cinematic clip generation
│   └── search_tool.py          # Perplexity web search
│
├── workflows/
│   └── pipeline.py             # LangGraph state machine (full pipeline graph)
│
├── niches/
│   ├── personal-finance/
│   │   ├── configs/niche.json  # Voice, tone, tags, schedule config
│   │   ├── builds/             # Episode outputs (narration, video, thumbnail)
│   │   └── assets/             # Channel-specific assets
│   ├── ai-tools/
│   └── health-longevity/
│
├── scripts/                    # Utility scripts (kept for backward compat)
│   ├── youtube_upload.py       # Standalone uploader (OAuth setup helper)
│   └── weekly_report.py        # Manual analytics report
│
├── logs/
│   ├── pipeline.log            # Pipeline run logs
│   └── analytics/              # Per-video analytics memos
│
├── crew.py                     # CrewAI crew factory
├── main.py                     # CLI entry point
├── requirements.txt
└── .env.example
```

---

## Adding a New Niche

1. Create the directory structure:
   ```bash
   python scripts/create_niche.py my-new-niche
   ```
2. Add `niches/my-new-niche/configs/niche.json` (copy from an existing niche).
3. Add `"my-new-niche"` to the `NICHES` list in `main.py`.
4. Set up a separate YouTube OAuth token for the new channel.

---

## API Quota Notes

- **YouTube Data API**: 10,000 units/day. Each upload costs ~1,600 units. Running 3 niches = ~4,800 units/day — within limits.
- **ElevenLabs**: ~2,500 characters per minute of audio. An 8-min video ≈ 1,200 words ≈ 7,200 chars.
- **Runway Gen-4**: Billed per second of generated video. Budget ~30s of clips per video.
- **Perplexity**: ~5 searches per pipeline run. sonar-pro tier recommended.

---

## Security

- Store all secrets in `.env` (never commit).
- Use per-niche OAuth tokens (one Google account per channel).
- Rate limiting and quota retry logic is built into `tools/youtube_tool.py`.
