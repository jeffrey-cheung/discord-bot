import os.path
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def get_sheet_id(url):
    prefix = 'docs.google.com/spreadsheets/'
    index = url.find(prefix) + len(prefix)
    url = url[index:]
    if 'd/' in url:
        index = url.find('d/')
        url = url[index + len('d/'):]
    index = url.find('/')
    return url[:index]


def read_sheet(spreadsheet_id, page_name, major_dimension='ROWS'):
    retry_delay = 2  # Initial delay in seconds
    max_retries = 3  # Max retry attempts
    for attempt in range(max_retries):
        try:
            return get_service_sheets().get(spreadsheetId=spreadsheet_id, range=page_name,
                                            majorDimension=major_dimension).execute().get('values', [])
        except HttpError as error:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)  # Backoff
                retry_delay *= 2  # Double the delay for the next attempt
            else:
                raise


def update_sheet(spreadsheet_id, page_name, data):
    retry_delay = 2  # Initial delay in seconds
    max_retries = 3  # Max retry attempts
    for attempt in range(max_retries):
        try:
            return get_service_sheets().update(spreadsheetId=spreadsheet_id, range=page_name,
                                               valueInputOption='USER_ENTERED', body={"values": [[data]]}).execute()
        except HttpError as error:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)  # Backoff
                retry_delay *= 2  # Double the delay for the next attempt
            else:
                raise


def batch_update_sheet(spreadsheet_id, batch_update_data):
    retry_delay = 2  # Initial delay in seconds
    max_retries = 3  # Max retry attempts
    data = []
    for key, value in batch_update_data.items():
        data.append({'range': key, 'values': [[value]]})
    for attempt in range(max_retries):
        try:
            return get_service_sheets().batchUpdate(spreadsheetId=spreadsheet_id,
                                                    body={'valueInputOption': 'USER_ENTERED', 'data': [data]}).execute()
        except HttpError as error:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)  # Backoff
                retry_delay *= 2  # Double the delay for the next attempt
            else:
                raise


def get_creds():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds


def get_service_sheets():
    service = build('sheets', 'v4', credentials=get_creds()).spreadsheets().values()
    return service
