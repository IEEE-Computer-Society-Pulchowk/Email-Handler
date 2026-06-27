# Email Mailer — IEEE CS Pulchowk SBC

Send bulk personalized or BCC emails using data from Google Sheets or local CSV files, configured per job via folders.

## Quick Start

```bash
# One-time setup (works on Windows, macOS, Linux)
python setup.py

# Run an example (preview only)
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

python main.py jobs/examples/individual --dry-run
```

## Project Layout

```
.
├── main.py                       # thin entry point → src.main:main()
├── src/                          # package
│   ├── config.py                 # Mode, SafeDict, scopes, sender defaults, config loading
│   ├── auth.py                   # Google OAuth (get_services)
│   ├── data.py                   # Google Sheets → DataFrame
│   ├── mailer.py                 # templating + Gmail message build/send
│   └── main.py                   # CLI + job orchestration
├── test_mailer.py                # offline checks (no network/auth)
├── requirements.txt
├── setup.py                      # one-time setup (cross-platform)
├── credentials.example.json
├── credentials.json              # your OAuth client (see Credentials & Auth)
├── token.json                    # generated after first auth
└── jobs/
    ├── .gitignore                # ignores everything except examples/
    ├── examples/
    │   ├── individual/           # individual, CSV
    │   ├── bcc/                   # bcc, CSV
    │   ├── csv/                   # individual, CSV with test CSV
    │   ├── sheets/               # individual, Google Sheets
    │   ├── bcc-sheets/           # bcc, Google Sheets
    │   ├── mapping-csv/          # individual, CSV with column_mapping
    │   ├── personalized/        # individual, multi-column + template_vars
    │   ├── optional-fields/     # individual, optional blank column (SafeDict)
    │   └── attachments/         # individual, static + per-row attachments
    └── mail-jobs/                # private repo — clone with setup.sh
```

## Job Folder Structure

Each job is a folder with a `config.json` and `template.html`. Data comes from either a CSV file or Google Sheets.

### CSV-based job

```
jobs/your-job-name/
├── config.json       # job configuration
├── template.html     # email HTML template
└── data.csv          # recipient data
```

**config.json:**

```json
{
  "sender_email": "you@example.com",
  "sender_name": "Your Name",
  "subject": "Interview Schedule - {Name}",
  "mode": "individual",
  "required_columns": ["Name", "Email", "Time"],
  "template_vars": {
    "organization": "Your Organization"
  },
  "csv_file": "data.csv"
}
```

### Sheets-based job

```
jobs/your-job-name/
├── config.json       # job configuration
└── template.html     # email HTML template
```

**config.json:**

```json
{
  "sender_email": "you@example.com",
  "sender_name": "Your Name",
  "spreadsheet_id": "YOUR_SPREADSHEET_ID",
  "sheet_name": "Sheet1",
  "test_spreadsheet_id": "YOUR_TEST_SPREADSHEET_ID",
  "test_sheet_name": "TestSheet",
  "subject": "Interview Schedule - {name}",
  "mode": "individual",
  "required_columns": ["Name", "Email", "Time"],
  "column_mapping": {
    "Name": "name",
    "Time": "time"
  },
  "template_vars": {
    "organization": "IEEE Computer Society Pulchowk Student Branch Chapter"
  }
}
```

### All config fields

| Field | CSV | Sheets | Description |
|---|---|---|---|
| `sender_email` | required | required | From address |
| `sender_name` | required | required | From display name |
| `subject` | required | required | Subject line — supports `{placeholder}` variables |
| `mode` | required | required | `"individual"` (one per row) or `"bcc"` (single email to all) |
| `required_columns` | required | required | Columns that must exist in the data |
| `template_vars` | optional | optional | Extra variables available in the template |
| `column_mapping` | — | optional | Rename sheet columns for template use (`"Name"` → `"name"`) |
| `attachments` | optional | optional | List of static files attached to **every** email (paths relative to the job folder) |
| `attachment_columns` | optional | optional | List of column names whose cell holds a per-row file path (relative to the job folder); `individual` mode only, blank cells are skipped |
| `csv_file` | required | — | Path to the CSV file (relative to the job folder) |
| `test_csv_file` | optional | — | Test CSV file used when `--test` is passed (defaults to `csv_file`) |
| `spreadsheet_id` | — | required | Google Sheet ID from the sheet URL |
| `sheet_name` | — | required | Sheet tab name |
| `test_spreadsheet_id` | — | optional | Test sheet ID (used with `--test` flag) |
| `test_sheet_name` | — | optional | Test sheet tab name (used with `--test` flag) |

### template.html

Use `{placeholder}` values that match CSV/Sheet column names (after `column_mapping`, if any) or keys in `template_vars`:

```html
<p>Dear {name},</p>
<p>Your session is at {time}.</p>
<p>{organization}</p>
```

The IEEE CS Pulchowk header image is included in all example templates.

### Attachments

Two optional, combinable fields (use either, both, or several of each):

```json
{
  "attachments": ["flyer.pdf"],
  "attachment_columns": ["Certificate"]
}
```

- `attachments` — static files sent with every email (works in both modes).
- `attachment_columns` — for `individual` mode, each listed column holds a file
  path for that row; blank cells are skipped. Paths are relative to the job
  folder. Missing files are reported up front (caught by `--dry-run`).

See [jobs/examples/attachments](jobs/examples/attachments) for both at once.

### data.csv

For CSV-based jobs, a file with headers matching `required_columns`:

```csv
Name,Email,Time
Alice Sharma,alice@example.com,10:00 AM
Bob Gurung,bob@example.com,11:30 AM
```

## Running

```bash
# CSV: preview
python main.py jobs/examples/individual --dry-run

# CSV: send
python main.py jobs/examples/individual

# CSV: BCC mode
python main.py jobs/examples/bcc --dry-run

# CSV: use test CSV
python main.py jobs/examples/csv --test --dry-run

# Sheets: preview (production sheet)
python main.py jobs/examples/sheets --dry-run

# Sheets: preview (test sheet)
python main.py jobs/examples/sheets --test --dry-run

# CSV: column_mapping (renames Name→name, Time→time for the template)
python main.py jobs/examples/mapping-csv --dry-run

# CSV: multi-column personalization (Time, Venue, Role + template_vars)
python main.py jobs/examples/personalized --dry-run

# CSV: optional blank column renders gracefully (SafeDict)
python main.py jobs/examples/optional-fields --dry-run

# CSV: static + per-row attachments
python main.py jobs/examples/attachments --dry-run

# Sheets: BCC mode (needs a real spreadsheet_id)
python main.py jobs/examples/bcc-sheets --test --dry-run
```

## Tests

Offline checks — no network, no auth, no emails sent. Validates templating,
column mapping, message building, and that every `jobs/examples/*` config loads:

```bash
python test_mailer.py
```

**Flags:**

- `--dry-run`: Preview without sending.
- `--test`: Use test data source instead of production — swaps to `test_csv_file` (CSV) or `test_spreadsheet_id` / `test_sheet_name` (Sheets).

## Modes

- **individual** — one personalized email per row of data.
- **bcc** — single email sent to all recipients via BCC (only `Email` column needed).

## Credentials & Auth

### Step-by-Step: Getting Your `credentials.json`

1. **Go to the Google Cloud Console**  
   Visit [console.cloud.google.com](https://console.cloud.google.com) and create a new project (or select an existing one).

2. **Enable the required APIs**  
   Go to **APIs & Services > Library** and enable both:
   - **Gmail API**
   - **Google Sheets API**

3. **Create an OAuth consent screen**  
   Go to **APIs & Services > OAuth consent screen**.  
   - Choose **External** user type, click **Create**.  
   - Fill in the **App name**, **User support email**, and **Developer contact information**.  
   - Click **Save and Continue** through the scopes and test users pages (you don't need to add any scopes here — they're requested at runtime).  
   - You can set the **Publishing status** to **Testing** for personal use.

4. **Create an OAuth client ID**  
   Go to **APIs & Services > Credentials**.  
   - Click **+ Create Credentials > OAuth client ID**.  
   - Choose **Desktop application** as the application type (not "Web application").  
   - Give it a name and click **Create**.  
   - A dialog appears with your client ID and client secret — click **Download JSON**.

5. **Place the downloaded file**  
   Rename it to `credentials.json` and place it in the project root, next to `main.py`.  
   Your file should look like [credentials.example.json](credentials.example.json) with the `"installed"` key:

   ```json
   {
     "installed": {
       "client_id": "...apps.googleusercontent.com",
       "client_secret": "...",
       "redirect_uris": ["http://localhost", "http://localhost:8080"]
     }
   }
   ```

6. **First run — authorize**  
   Run any command (e.g. `python main.py jobs/examples/individual --dry-run`).  
   A browser tab will open asking you to sign in and grant consent.  
   After approval, a `token.json` file is saved in the project root for future runs.

### Troubleshooting

- **`redirect_uri_mismatch` (Error 400)**:  
  Make sure `credentials.json` uses the **Desktop application** type (`"installed"` key, not `"web"`).  
  If you accidentally created a "Web application" OAuth client, delete it and create a Desktop one instead, or  
  add `http://localhost:8080` to the **Authorized redirect URIs** of your existing Web client.

- **Token expired or revoked**:  
  Delete `token.json` and rerun — the script will prompt for consent again.

- **Access blocked / app not verified**:  
  The app is in **Testing** mode, so only test users you add on the OAuth consent screen can sign in.  
  If you get this error, go to **OAuth consent screen** and add your email under **Test users**.

## Examples

| Example | Source | Link |
|---|---|---|
| Individual | CSV | [jobs/examples/individual](jobs/examples/individual) |
| BCC | CSV | [jobs/examples/bcc](jobs/examples/bcc) |
| Individual | CSV (alt, w/ test CSV) | [jobs/examples/csv](jobs/examples/csv) |
| Individual | Google Sheets | [jobs/examples/sheets](jobs/examples/sheets) |
| BCC | Google Sheets | [jobs/examples/bcc-sheets](jobs/examples/bcc-sheets) |
| Individual (column_mapping) | CSV | [jobs/examples/mapping-csv](jobs/examples/mapping-csv) |
| Individual (multi-column + vars) | CSV | [jobs/examples/personalized](jobs/examples/personalized) |
| Individual (optional blank field) | CSV | [jobs/examples/optional-fields](jobs/examples/optional-fields) |
| Individual (static + per-row attachments) | CSV | [jobs/examples/attachments](jobs/examples/attachments) |

CSV examples are ready to run after running `./setup.sh`. The Sheets example needs a real spreadsheet ID — copy the folder and update `spreadsheet_id`.

## Environment

- Python 3.7+
- Install dependencies:

```bash
pip install -r requirements.txt
```

## Keeping jobs separate

Real campaign data lives in the **private** repo:

```
https://github.com/IEEE-Computer-Society-Pulchowk/mail-jobs
```

Clone it into `jobs/` (the folder is gitignored so nothing leaks):

```bash
python setup.py   # does this automatically, or manually:
git clone git@github.com:IEEE-Computer-Society-Pulchowk/mail-jobs.git jobs/mail-jobs
```

Then run:

```bash
python main.py jobs/mail-jobs/my-campaign --dry-run
```

## Safety Notes

- Always run with `--dry-run` before sending for real.
- Check sender details and subject in the preview output.
- Keep recipient data in the private `mail-jobs` repo, not here.
