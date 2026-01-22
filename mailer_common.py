import base64
import json
import os
from collections import defaultdict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Shared OAuth scopes for Gmail send and Sheets read access.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


class Mode(str, Enum):
    BCC = "bcc"
    INDIVIDUAL = "individual"


class SafeDict(defaultdict):
    """Default missing keys to empty strings for template formatting."""

    def __missing__(self, key):
        return ""


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
                print(f"Token expired or revoked. Deleting {token_path} and re-authenticating...")
                os.remove(token_path)
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
                creds = flow.run_local_server(port=0)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    gmail_service = build("gmail", "v1", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)
    return gmail_service, sheets_service


def load_html_template(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def fetch_sheet_dataframe(
    sheets_service,
    spreadsheet_id: str,
    sheet_name: str,
    range_name: Optional[str] = None,
) -> pd.DataFrame:
    effective_range = range_name or f"{sheet_name}!A:Z"
    sheet = sheets_service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id, range=effective_range).execute()
    values = result.get("values", [])

    if not values:
        return pd.DataFrame()

    return pd.DataFrame(values[1:], columns=values[0])


def render_template(template_text: str, context: Dict) -> str:
    return template_text.format_map(SafeDict(**context))


def build_raw_message(
    sender: str,
    recipient: str,
    subject: str,
    html_body: str,
    bcc: Optional[List[str]] = None,
) -> str:
    msg = MIMEMultipart("alternative")
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject

    if bcc:
        msg["Bcc"] = ", ".join(bcc)

    msg.attach(MIMEText(html_body, "html"))
    return base64.urlsafe_b64encode(msg.as_bytes()).decode()


def send_raw_message(gmail_service, raw_message: str):
    return gmail_service.users().messages().send(userId="me", body={"raw": raw_message}).execute()


def preview_recipients(df: pd.DataFrame, mode: str) -> None:
    total = len(df)
    print(f"Total recipients: {total}")

    preview_columns = [col for col in ["Name", "Email"] if col in df.columns]
    if preview_columns:
        print(df[preview_columns])
    else:
        print(df.head())

    if mode == "bcc" and "Email" in df.columns:
        print(f"BCC list size: {df['Email'].notna().sum()}")


def confirm_action(prompt: str = "Send emails?") -> bool:
    answer = input(f"{prompt} [y/N]: ").strip().lower()
    return answer in ("y", "yes")


def load_job_config(job_folder: str) -> Dict:
    """Load job configuration from a folder containing config.json and template.html.
    
    Args:
        job_folder: Path to the job folder
        
    Returns:
        Dict containing:
        - spreadsheet_id: Google Sheet ID
        - sheet_name: Sheet tab name
        - subject: Subject line (may contain template variables)
        - mode: "individual" or "bcc"
        - required_columns: List of required column names
        - template_vars: Optional dict of default template variables
        - template_file: Absolute path to template.html
        
    Raises:
        SystemExit: If config.json or template.html is missing or invalid
    """
    job_path = Path(job_folder)
    
    if not job_path.exists():
        raise SystemExit(f"Job folder not found: {job_folder}")
    
    if not job_path.is_dir():
        raise SystemExit(f"Not a directory: {job_folder}")
    
    config_file = job_path / "config.json"
    template_file = job_path / "template.html"
    
    if not config_file.exists():
        raise SystemExit(f"config.json not found in: {job_folder}")
    
    if not template_file.exists():
        raise SystemExit(f"template.html not found in: {job_folder}")
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise SystemExit(f"Invalid JSON in {config_file}: {e}")
    
    csv_file = config.get("csv_file")

    # Validate required fields
    required_fields = ["subject", "mode"]
    if not csv_file:
        required_fields.extend(["spreadsheet_id", "sheet_name"])
    missing = [field for field in required_fields if field not in config]
    if missing:
        raise SystemExit(f"Missing required fields in config.json: {', '.join(missing)}")
    
    # Validate mode
    try:
        Mode(config["mode"])
    except ValueError:
        valid_modes = [m.value for m in Mode]
        raise SystemExit(f"Invalid mode '{config['mode']}'. Must be one of: {', '.join(valid_modes)}")
    
    # Set defaults
    config.setdefault("sender_email", "pulchowkcompsbc@gmail.com")
    config.setdefault("sender_name", "IEEE Computer Society Pulchowk Student Branch Chapter")
    config.setdefault("required_columns", ["Email"])
    config.setdefault("template_vars", {})
    config.setdefault("column_mapping", {})
    config["template_file"] = str(template_file.absolute())
    
    return config
