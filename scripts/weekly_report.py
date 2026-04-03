#!/usr/bin/env python3
"""
weekly_report.py - Analytics → Slack/email
"""

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import requests
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

def get_analytics():
    creds = Credentials.from_authorized_user_file('configs/youtube_oauth.json')
    youtube_analytics = build('youtubeAnalytics', 'v2', credentials=creds)

    # Placeholder query
    response = youtube_analytics.reports().query(
        ids='channel==MINE',
        startDate='2024-01-01',
        endDate='2024-01-07',
        metrics='views,estimatedMinutesWatched',
        dimensions='day'
    ).execute()
    return response

def send_report(report):
    # Slack
    slack_url = os.getenv('SLACK_WEBHOOK_URL')
    requests.post(slack_url, json={"text": report})

    # Email
    msg = MIMEText(report)
    msg['Subject'] = 'Weekly YouTube Report'
    msg['From'] = os.getenv('EMAIL_USER')
    msg['To'] = 'you@example.com'

    server = smtplib.SMTP(os.getenv('EMAIL_SMTP_SERVER'))
    server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASS'))
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()

def main():
    analytics = get_analytics()
    report = f"Weekly Report: {analytics}"
    send_report(report)

if __name__ == '__main__':
    main()