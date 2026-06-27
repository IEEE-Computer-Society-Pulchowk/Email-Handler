import argparse
from pathlib import Path

import pandas as pd

from .auth import get_services
from .config import Mode, load_job_config
from .data import fetch_sheet_dataframe
from .mailer import (
    apply_column_mapping,
    build_raw_message,
    confirm_action,
    load_html_template,
    preview_recipients,
    render_template,
    send_raw_message,
)


def ensure_columns(df, required):
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise SystemExit(f"Missing columns in sheet: {', '.join(missing)}")


def send_bcc(gmail_service, job, df, sender_email, sender_name):
    recipients = df["Email"].dropna().unique().tolist()
    if not recipients:
        print("No BCC recipients found.")
        return

    html_template = load_html_template(job["template_file"])
    html_body = render_template(html_template, job.get("template_vars", {}))
    subject = render_template(job["subject"], job.get("template_vars", {}))

    sender_header = f"{sender_name} <{sender_email}>"
    raw = build_raw_message(
        sender_header, sender_email, subject, html_body, bcc=recipients
    )
    send_raw_message(gmail_service, raw)
    print(f"Sent one BCC email to {len(recipients)} recipients.")


def send_individual(gmail_service, job, df, sender_email, sender_name):
    html_template = load_html_template(job["template_file"])
    column_mapping = job.get("column_mapping", {})
    sender_header = f"{sender_name} <{sender_email}>"

    for _, row in df.iterrows():
        mapped_data = apply_column_mapping(row.to_dict(), column_mapping)
        context = {**job.get("template_vars", {}), **mapped_data}
        subject = render_template(job["subject"], context)
        html_body = render_template(html_template, context)

        raw = build_raw_message(sender_header, row["Email"], subject, html_body)
        send_raw_message(gmail_service, raw)
        print(f"Sent to {row.get('Name', '(no name)')} ({row['Email']})")

    print(f"Total emails sent: {len(df)}")


MODE_HANDLERS = {
    Mode.BCC: send_bcc,
    Mode.INDIVIDUAL: send_individual,
}


def run_job(job_folder: str, dry_run: bool = False, use_test: bool = False):
    """Run a mail job from a job folder containing config.json and template.html.

    Args:
        job_folder: Path to the job folder
        dry_run: If True, preview only without sending
        use_test: If True, use test data source
    """
    job = load_job_config(job_folder)
    gmail_service, sheets_service = get_services()

    has_csv = "csv_file" in job
    has_prod_sheets = "spreadsheet_id" in job and "sheet_name" in job
    has_test_sheets = "test_spreadsheet_id" in job and "test_sheet_name" in job

    # ── Decide source ───────────────────────────────────────────
    # --test with test sheets → auto use sheets
    # --test with test CSV only (no test sheets) → auto use CSV
    # Normal run with both CSV and prod sheets → ask
    # Otherwise pick whatever is configured

    if use_test and has_test_sheets:
        use_sheets = True
        use_csv = False
    elif use_test and has_csv:
        use_sheets = False
        use_csv = True
    elif has_csv and has_prod_sheets:
        print("Warning: both CSV and Google Sheets are configured in config.json.")
        choice = input("Use (c)sv or (s)heets? [C/s]: ").strip().lower()
        use_sheets = choice == "s"
        use_csv = not use_sheets
    elif has_csv:
        use_sheets = False
        use_csv = True
    elif has_prod_sheets:
        use_sheets = True
        use_csv = False
    else:
        # Only test sheets configured without --test
        print("Test-only sheets config. Use --test to read from the test sheet.")
        print("Or add spreadsheet_id and sheet_name for production use.")
        return

    if use_csv:
        csv_file = (
            job["csv_file"]
            if not use_test
            else job.get("test_csv_file", job["csv_file"])
        )
        csv_path = Path(job_folder) / csv_file
        if not csv_path.exists():
            raise SystemExit(f"CSV file not found: {csv_path}")
        df = pd.read_csv(csv_path)
    else:
        sheet_name = job["sheet_name"] if not use_test else job["test_sheet_name"]
        spreadsheet_id = (
            job["spreadsheet_id"] if not use_test else job["test_spreadsheet_id"]
        )

        df = fetch_sheet_dataframe(
            sheets_service,
            spreadsheet_id,
            sheet_name,
            job.get("range_name"),
        )

    if df.empty:
        print("No data found in the selected sheet.")
        return

    ensure_columns(df, job.get("required_columns", ["Email"]))

    sender_email = job["sender_email"]
    sender_name = job["sender_name"]

    print(f"Job folder: {job_folder}")
    print(f"From: {sender_name} <{sender_email}>")
    print(f"Subject: {job['subject']}")
    print(f"Template: {job['template_file']}")
    print(f"Mode: {job['mode']}")
    preview_recipients(df, job["mode"])

    if dry_run:
        print("Dry-run only: no emails will be sent.")
        return

    if not confirm_action("Send these emails?"):
        print("Aborted by user.")
        return

    # Convert mode string to Mode enum
    mode = Mode(job["mode"])
    handler = MODE_HANDLERS.get(mode)
    if not handler:
        supported = ", ".join(m.value for m in MODE_HANDLERS)
        raise SystemExit(
            f"Unsupported mode '{job['mode']}'. Expected one of: {supported}"
        )

    handler(gmail_service, job, df, sender_email, sender_name)


def main():
    parser = argparse.ArgumentParser(
        description="Send emails from Google Sheets data using a job folder configuration.",
        epilog="Example: python main.py jobs/test-job --dry-run",
    )
    parser.add_argument(
        "job_folder",
        help="Path to the job folder containing config.json and template.html",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without sending emails."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Use test_sheet_name and test_spreadsheet_id instead of production values.",
    )
    args = parser.parse_args()

    run_job(args.job_folder, dry_run=args.dry_run, use_test=args.test)


if __name__ == "__main__":
    main()
