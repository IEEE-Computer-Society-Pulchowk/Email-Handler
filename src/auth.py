import os

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import SCOPES


def get_services(
    token_path: str = "token.json",
    credentials_path: str = "credentials.json",
    scopes=SCOPES,
):
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                # Token is expired or revoked, delete it and re-authenticate
                print(
                    f"Token expired or revoked. Deleting {token_path} and re-authenticating..."
                )
                os.remove(token_path)
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, scopes
                )
                creds = flow.run_local_server(port=8080)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
            creds = flow.run_local_server(port=8080)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    gmail_service = build("gmail", "v1", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)
    return gmail_service, sheets_service
