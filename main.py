import argparse

from mailer_common import (
    Mode,
    build_raw_message,
    confirm_action,
    fetch_sheet_dataframe,
    get_services,
    load_html_template,
    load_job_config,
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
    raw = build_raw_message(sender_header, sender_email, subject, html_body, bcc=recipients)
    send_raw_message(gmail_service, raw)
    print(f"Sent one BCC email to {len(recipients)} recipients.")


def send_individual(gmail_service, job, df, sender_email, sender_name):
    html_template = load_html_template(job["template_file"])
    column_mapping = job.get("column_mapping", {})
    sender_header = f"{sender_name} <{sender_email}>"

    for _, row in df.iterrows():
        row_data = row.to_dict()
        # Apply column mapping: rename columns for template
        mapped_data = {column_mapping.get(k, k): v for k, v in row_data.items()}
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


def run_job(job_folder: str, dry_run: bool = False):
    """Run a mail job from a job folder containing config.json and template.html.
    
    Args:
        job_folder: Path to the job folder
        dry_run: If True, preview only without sending
    """
    job = load_job_config(job_folder)
    gmail_service, sheets_service = get_services()
    df = fetch_sheet_dataframe(
        sheets_service,
        job["spreadsheet_id"],
        job["sheet_name"],
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
        raise SystemExit(f"Unsupported mode '{job['mode']}'. Expected one of: {supported}")

    handler(gmail_service, job, df, sender_email, sender_name)


def main():
    parser = argparse.ArgumentParser(
        description="Send emails from Google Sheets data using a job folder configuration.",
        epilog="Example: python main.py jobs/test-job --dry-run"
    )
    parser.add_argument(
        "job_folder",
        help="Path to the job folder containing config.json and template.html"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without sending emails."
    )
    args = parser.parse_args()

    run_job(args.job_folder, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
