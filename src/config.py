import json
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Dict

# Default sender identity — edit here to change the org's From address/name.
DEFAULT_SENDER_EMAIL = "pulchowkcompsbc@gmail.com"
DEFAULT_SENDER_NAME = "IEEE Computer Society Pulchowk Student Branch Chapter"

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
    has_sheets = ("spreadsheet_id" in config and "sheet_name" in config) or (
        "test_spreadsheet_id" in config and "test_sheet_name" in config
    )

    # Validate required fields
    required_fields = ["subject", "mode"]
    if not csv_file and not has_sheets:
        required_fields.extend(["spreadsheet_id", "sheet_name"])
    missing = [field for field in required_fields if field not in config]
    if missing:
        raise SystemExit(
            f"Missing required fields in config.json: {', '.join(missing)}"
        )

    # Validate mode
    try:
        Mode(config["mode"])
    except ValueError:
        valid_modes = [m.value for m in Mode]
        raise SystemExit(
            f"Invalid mode '{config['mode']}'. Must be one of: {', '.join(valid_modes)}"
        )

    # Set defaults
    config.setdefault("sender_email", DEFAULT_SENDER_EMAIL)
    config.setdefault("sender_name", DEFAULT_SENDER_NAME)
    config.setdefault("required_columns", ["Email"])
    config.setdefault("template_vars", {})
    config.setdefault("column_mapping", {})
    config.setdefault("attachments", [])  # static files attached to every email
    config.setdefault("attachment_columns", [])  # per-row file paths from these columns
    # Test fields default to production values if not specified
    if csv_file:
        config.setdefault("test_csv_file", csv_file)
    elif "spreadsheet_id" in config and "sheet_name" in config:
        config.setdefault("test_sheet_name", config["sheet_name"])
        config.setdefault("test_spreadsheet_id", config["spreadsheet_id"])
    config["template_file"] = str(template_file.absolute())
    config["job_folder"] = str(job_path)  # for resolving dynamic attachment paths

    # Resolve + validate static attachments (relative to the job folder).
    resolved = []
    for a in config["attachments"]:
        path = (job_path / a).resolve()
        if not path.exists():
            raise SystemExit(f"Attachment not found: {path}")
        resolved.append(str(path))
    config["attachments"] = resolved

    return config
