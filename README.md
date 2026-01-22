# Email Mailer - Folder-Based Job Configuration

Send bulk emails from Google Sheets using job folders containing configuration and templates.

## Quick Start

```bash
python main.py jobs/test-individual --dry-run
```

## Job Folder Structure

Each job is a folder containing:

```
jobs/
  your-job-name/
   config.json       # Job configuration
   template.html     # Email HTML template
   data.csv          # Optional: local CSV data source
```

### config.json Format

```json
{
   "sender_email": "you@example.com",
   "sender_name": "Your Name",
   "spreadsheet_id": "YOUR_GOOGLE_SHEET_ID",
   "sheet_name": "SHEET_TAB_NAME",
   "subject": "Email Subject - {Name}",
   "mode": "individual",
   "required_columns": ["Name", "Email"],
   "column_mapping": {},
   "template_vars": {},
   "csv_file": "data.csv"
}
```

**Fields:**
- `sender_email`: From address
- `sender_name`: From display name
- `spreadsheet_id`: Google Sheet ID from the URL (ignored if `csv_file` is set)
# Email Mailer (Folder-Based)

Send personalized or BCC emails using Google Sheets or a local CSV, configured per job via folders.

## Project Layout

```
.
├── main.py
├── mailer_common.py
├── requirements.txt
├── credentials.example.json
├── credentials.json              # put your real OAuth client here
├── token.json                    # generated after first auth
└── jobs/
    ├── test-individual/
    │   ├── config.json
    │   └── template.html
    ├── test-bcc/
    │   ├── config.json
    │   └── template.html
    └── test-csv/
        ├── config.json
        ├── data.csv
        └── template.html
```

## Job Folder Reference

Each job folder must contain `config.json` and `template.html`. Optional: `data.csv` when using a local CSV source.

### config.json fields

```json
{
  "sender_email": "you@example.com",
  "sender_name": "Your Name",
  "subject": "Subject with {name}",
  "mode": "individual",              // or "bcc"
  "required_columns": ["Name", "Email"],
  "column_mapping": { "Name": "name" },
  "template_vars": { "organization": "Demo Org" },
  "spreadsheet_id": "<sheet id>",   // omit when using csv_file
  "sheet_name": "Sheet1",           // omit when using csv_file
  "test_sheet_name": "TestSheet1",  // optional; used with --test flag
  "test_spreadsheet_id": "<test id>",  // optional; used with --test flag
  "range_name": null,                // optional; defaults to Sheet!A:Z
  "csv_file": "data.csv"            // optional; load this CSV instead of Sheets
}
```

- `sender_email`, `sender_name`: From header.
- `subject`: Supports template variables.
- `mode`: `individual` (one per row) or `bcc` (single email to all addresses).
- `required_columns`: Columns that must exist in the data.
- `column_mapping`: Rename data columns for template use (e.g., `Name` → `name`).
- `template_vars`: Defaults merged into every email (useful for organization, event names, etc.).
- `spreadsheet_id`, `sheet_name`: Production sheet source (skip when using `csv_file`).
- `test_sheet_name`, `test_spreadsheet_id`: Test sheet source; used when `--test` flag is passed. Defaults to production values if omitted.
- `range_name`: Optional range (defaults to `Sheet!A:Z`).
- `csv_file`: Optional; load data from this CSV file instead of Sheets.

### template.html

Use `{placeholder}` values that match either:
- Mapped column names (after `column_mapping`), or
- Keys in `template_vars`.

Example snippet:
```html
<p>Dear {name},</p>
<p>Your session is at {time}.</p>
<p>{organization}</p>
```

## Running

From project root:

Dry run (preview only, no send):
```bash
python main.py jobs/test-individual --dry-run
```

Send emails:
```bash
python main.py jobs/test-individual
```

Use test sheet (if configured):
```bash
python main.py jobs/test-individual --test --dry-run
```

Use a CSV-based job:
```bash
python main.py jobs/test-csv --dry-run
```

**Flags:**
- `--dry-run`: Preview emails without sending.
- `--test`: Use `test_sheet_name` and `test_spreadsheet_id` instead of production values.

## Modes

- **individual**: one personalized email per row.
- **bcc**: one email sent to all recipients via BCC (requires at least `Email` column).

## Data Sources

- **Google Sheets**: Uses `spreadsheet_id`, `sheet_name` (and optional `range_name`).
- **CSV**: If `csv_file` is set, data loads from that file in the job folder.

## Credentials & Auth

1. Create OAuth client (Desktop) in Google Cloud; enable Gmail API and Google Sheets API.
2. Download the client JSON and save as `credentials.json` in project root (see [credentials.example.json](credentials.example.json)).
3. First run opens a browser for consent; `token.json` is generated and reused.
4. If token is expired/revoked, delete `token.json` and rerun.

## Examples

- Individual (Sheets): [jobs/test-individual/config.json](jobs/test-individual/config.json)
- BCC (Sheets): [jobs/test-bcc/config.json](jobs/test-bcc/config.json)
- Individual (CSV): [jobs/test-csv/config.json](jobs/test-csv/config.json)

## Environment

- Python 3.7+
- Install deps: `pip install -r requirements.txt`

## Safety Notes

- Always run with `--dry-run` before sending.
- Check sender details and subject in the preview output.
If you get a token error, delete `token.json` and re-authenticate:
