import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

import pandas as pd

from .config import SafeDict


def load_html_template(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def render_template(template_text: str, context: Dict) -> str:
    return template_text.format_map(SafeDict(**context))


def apply_column_mapping(row_data: Dict, column_mapping: Dict) -> Dict:
    """Rename row keys per column_mapping (e.g. {"Name": "name"}); unmapped keys pass through.

    Blank CSV cells arrive as NaN — coerce to "" so they render gracefully instead of "nan".
    """
    return {
        column_mapping.get(k, k): ("" if pd.isna(v) else v)
        for k, v in row_data.items()
    }


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
    return (
        gmail_service.users()
        .messages()
        .send(userId="me", body={"raw": raw_message})
        .execute()
    )


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
