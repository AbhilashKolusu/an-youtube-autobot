#!/usr/bin/env python3
"""
topics.py - Pull trends & write to Google Sheet
"""

import os
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle
from datetime import datetime

# Scopes for Google Sheets and Trends
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/trends.readonly']

def log_api_usage(niche, action, cost):
    """Logs API usage to the central tracking file."""
    log_file = "logs/api_usage.csv"
    os.makedirs("logs", exist_ok=True)
    file_exists = os.path.isfile(log_file)
    niche_name = niche or os.getenv('NICHE', 'system')
    with open(log_file, "a") as f:
        if not file_exists:
            f.write("timestamp,niche,action,cost_units\n")
            file_exists = True
        f.write(f"{datetime.now().isoformat()},{niche_name},{action},{cost}\n")

def get_credentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('configs/client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def main():
    creds = get_credentials()
    # Build services
    sheets_service = build('sheets', 'v4', credentials=creds)
    trends_service = build('trends', 'v1', credentials=creds)

    # Example: Get trending queries
    # This is a placeholder; actual implementation needed
    print("Pulling trends...")

    # Write to Google Sheet
    spreadsheet_id = 'your_sheet_id_here'
    range_name = 'Topics!A1'
    values = [['Topic', 'Searches'], ['Lo-fi Mix', '1000']]
    body = {'values': values}
    
    log_api_usage(None, "sheets.values.update", 1)
    
    result = sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id, range=range_name,
        valueInputOption='RAW', body=body).execute()
    print(f"Updated {result.get('updatedCells')} cells.")

if __name__ == '__main__':
    main()