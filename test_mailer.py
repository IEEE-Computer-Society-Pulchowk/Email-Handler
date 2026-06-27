"""Offline checks for the mailer — no network, no auth, no email sent.

Run: python test_mailer.py   (also works under pytest)
"""

import base64
from email import message_from_bytes
from pathlib import Path

import numpy as np

from src.config import Mode, load_job_config
from src.main import row_attachment_paths
from src.mailer import apply_column_mapping, build_raw_message, render_template

EXAMPLES = Path(__file__).parent / "jobs" / "examples"


def test_render_template_safedict():
    out = render_template("Hi {name}, at {time}.", {"name": "Alice"})
    assert out == "Hi Alice, at .", out  # missing {time} → ""


def test_apply_column_mapping():
    mapped = apply_column_mapping({"Name": "Alice", "Time": "10 AM"}, {"Name": "name", "Time": "time"})
    assert mapped == {"name": "Alice", "time": "10 AM"}, mapped
    # blank CSV cell (NaN) → "" so it renders gracefully, not "nan"
    assert apply_column_mapping({"Note": np.nan}, {}) == {"Note": ""}


def test_build_raw_message():
    raw = build_raw_message(
        "Org <org@x.com>", "to@x.com", "Subj", "<p>Hello</p>", bcc=["a@x.com", "b@x.com"]
    )
    msg = message_from_bytes(base64.urlsafe_b64decode(raw))
    assert msg["To"] == "to@x.com"
    assert msg["Subject"] == "Subj"
    assert msg["Bcc"] == "a@x.com, b@x.com"
    assert "<p>Hello</p>" in msg.get_payload()[0].get_payload()


def test_build_raw_message_with_attachments():
    flyer = str(EXAMPLES / "attachments" / "flyer.txt")
    raw = build_raw_message(
        "Org <org@x.com>", "to@x.com", "Subj", "<p>Hi</p>", attachments=[flyer]
    )
    msg = message_from_bytes(base64.urlsafe_b64decode(raw))
    assert msg.get_content_subtype() == "mixed", msg.get_content_type()
    names = [p.get_filename() for p in msg.get_payload() if p.get_filename()]
    assert names == ["flyer.txt"], names


def test_row_attachment_paths():
    job = {
        "attachments": ["/static/flyer.txt"],
        "attachment_columns": ["Certificate"],
        "job_folder": str(EXAMPLES / "attachments"),
    }
    # static + valid dynamic
    paths = row_attachment_paths(job, {"Email": "a@x.com", "Certificate": "certs/alice.txt"})
    assert paths[0] == "/static/flyer.txt"
    assert paths[1].endswith("certs/alice.txt")
    # blank dynamic cell → static only
    assert row_attachment_paths(job, {"Email": "c@x.com", "Certificate": np.nan}) == ["/static/flyer.txt"]
    # missing named file → SystemExit
    try:
        row_attachment_paths(job, {"Email": "x@x.com", "Certificate": "certs/nope.txt"})
        assert False, "expected SystemExit for missing attachment"
    except SystemExit:
        pass


def test_all_example_configs_valid():
    folders = sorted(p for p in EXAMPLES.iterdir() if p.is_dir())
    assert folders, "no example folders found"
    for folder in folders:
        cfg = load_job_config(str(folder))
        assert "subject" in cfg, folder
        Mode(cfg["mode"])  # raises if invalid
        assert cfg["sender_email"] and cfg["sender_name"], folder
        assert Path(cfg["template_file"]).exists(), folder


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("All checks passed.")
