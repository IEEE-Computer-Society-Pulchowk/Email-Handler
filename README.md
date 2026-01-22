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
- `sheet_name`: Name of the sheet tab (ignored if `csv_file` is set)
- `subject`: Subject line (supports template variables like `{Name}`)
- `mode`: Either `"individual"` (one email per row) or `"bcc"` (one email to all)
- `required_columns`: Column names that must exist in the sheet
- `column_mapping`: Optional mapping to rename sheet/CSV columns for templates
- `template_vars`: Optional default values for template variables
- `csv_file`: Optional CSV filename in the job folder; when set, data is loaded from this CSV instead of Google Sheets

### template.html Format

Use `{ColumnName}` placeholders that will be replaced with values from the sheet:

```html
<!DOCTYPE html>
<html>
<body>
    <p>Dear {Name},</p>
    <p>Your interview is scheduled for {Time}.</p>
</body>
</html>
```

## Usage

### Dry Run (Preview Only)
```bash
python main.py jobs/your-job-name --dry-run
```

### Send Emails
```bash
python main.py jobs/your-job-name
```

## Examples

Three example jobs are included:

1. **jobs/test-job/** - Simple test email
2. **jobs/jan18-interview/** - Interview scheduling (individual mode)
3. **jobs/bcc-demo/** - Workshop wrap-up (BCC mode)

## Creating a New Job

1. Create a new folder in `jobs/`:
   ```bash
   mkdir jobs/my-new-job
   ```

2. Create `config.json`:
   ```bash
   cp jobs/test-job/config.json jobs/my-new-job/
   # Edit with your values
   ```

3. Create `template.html`:
   ```bash
   cp jobs/test-job/template.html jobs/my-new-job/
   # Customize your email template
   ```

4. Test it:
   ```bash
   python main.py jobs/my-new-job --dry-run
   ```

## Modes

### Individual Mode
Sends one personalized email to each recipient. Each row in the sheet becomes one email.

**Use for:** Interview schedules, certificates, personalized messages

### BCC Mode
Sends one email to all recipients via BCC. Only requires an "Email" column.

**Use for:** Announcements, newsletters, group updates

## Requirements

- Python 3.7+
- Google OAuth credentials (`credentials.json`)
- Required Python packages (see `requirements.txt`)

## Setup Credentials

### 1. Get OAuth Credentials from Google Cloud

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Gmail API
   - Google Sheets API
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
   - Application type: Desktop application
   - Download the JSON file
5. Rename or copy the downloaded file to `credentials.json` in this project root

### 2. Example credentials.json

See `credentials.example.json` for the expected structure:

```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["http://localhost"]
  }
}
```

Replace the placeholder values with your actual credentials from Google Cloud.

## Authentication

First run will open a browser for Google OAuth authentication. The token is saved to `token.json`.

If you get a token error, delete `token.json` and re-authenticate:
```bash
rm token.json
python main.py jobs/test-job --dry-run
```

## Migration from Old System

The system now exclusively uses the folder-based job configuration.
