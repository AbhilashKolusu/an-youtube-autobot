# Standard Operating Procedures (SOP)

## Overview

This document outlines the step-by-step procedures for operating the An-YouTube-Autobot system.

## 1. Topic Ideation & Script Generation

- Run `python scripts/topics.py` to pull top-search queries from Google Trends and AnswerThePublic.
- Results are written to a Google Sheet (YouTube Topics).
- Zapier watches the sheet and calls an LLM to generate a 300-word host script.
- Script is saved back to the sheet and exported as `teleprompter.html`.

## 2. Recording (Human Presenter)

- Presenter opens `teleprompter.html` on a tablet/phone.
- Records webcam + mic via OBS, saving to `recordings/host/{episode_id}/host.mp4`.
- Drops the raw file into the watch folder.

## 3. Automated Pipeline

- `watch.py` detects new file and triggers the pipeline.
- Music mix generation via `music_prompt.py`.
- Video editing with `resolve_edit.py` or `ffmpeg_edit.sh`.
- Thumbnail generation with `thumbnail.py`.
- Final assembly and upload via `youtube_upload.py`.

## 4. Social Promotion

- Zapier/Make triggers posts to Discord, Twitter, Instagram, TikTok.

## 5. Analytics & Reporting

- `weekly_report.py` runs every Monday to generate reports.

## Setup Checklist

- Create Google Cloud project and enable APIs.
- Set up OAuth for YouTube and Google Sheets.
- Install dependencies: `pip install -r requirements.txt`
- Install DaVinci Resolve and enable Scripting API.
- Sign up for Music AI service and get API key.
- Create Canva app and get API token.
- Build Zapier/Make workflows.

## Maintenance

- Version control with Git tags per episode.
- Monitor with HealthCheck.io.
- Ensure content safety and audio licensing.