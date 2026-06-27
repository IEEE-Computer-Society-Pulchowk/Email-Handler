import base64
import mimetypes
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
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


def _build_attachment(path: str) -> MIMEBase:
    ctype, _ = mimetypes.guess_type(path)
    maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
    with open(path, "rb") as f:
        part = MIMEBase(maintype, subtype)
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment", filename=Path(path).name)
    return part


def build_raw_message(
    sender: str,
    recipient: str,
    subject: str,
    html_body: str,
    bcc: Optional[List[str]] = None,
    attachments: Optional[List[str]] = None,
) -> str:
    # mixed wraps body + files; alternative is enough for a body-only mail.
    msg = MIMEMultipart("mixed" if attachments else "alternative")
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = subject

    if bcc:
        msg["Bcc"] = ", ".join(bcc)

    msg.attach(MIMEText(html_body, "html"))
    for path in attachments or []:
        msg.attach(_build_attachment(path))
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
