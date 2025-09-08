# Google Sheets Synchronization Script

This script synchronizes changes from the master Google Sheet (all projects) to the primary Lacuna Fund sheet (Lacuna projects only).

## Purpose

The master sheet contains all Fair Forward projects, while the primary sheet contains only projects marked as "Lacuna Dataset = Yes". When content is updated in the master sheet, this script detects and applies those changes to the corresponding projects in the primary sheet.

## Usage

### Basic Usage (Dry Run)
```bash
# Activate the environment
conda activate data_catalog

# Check for changes without applying them (safe)
python scripts/sync_from_master_sheet.py --dry-run
```

### Apply Changes
```bash
# Actually apply the detected changes
python scripts/sync_from_master_sheet.py --apply
```

### Custom Credentials
```bash
# Use different credentials file
python scripts/sync_from_master_sheet.py --credentials path/to/your/creds.json
```

## How It Works

### 1. Project Matching
Projects are matched between sheets using multiple fallback criteria:
1. **Dataset Speaking Titles** (primary)
2. **Use Case Speaking Title** (fallback)
3. **Point of Contact/Communities** (fallback)
4. **Dataset Link** (fallback)
5. **Model/Use-Case Links** (fallback)

Uses fuzzy matching with 80%+ similarity threshold to handle minor text variations.

### 2. Change Detection
- Compares content in all common columns between master and primary sheets
- Ignores columns with `ui_` prefix (never syncs these)
- Ignores `Project ID` column (protected)
- Detects actual content differences (not just whitespace)

### 3. Synchronization
- **Dry run by default** - shows what would change without applying
- Logs all detected changes with before/after values
- Only updates columns that exist in both sheets

## Protected Columns

These columns are **never** synchronized:
- `Project ID` 
- Any column containing `ui_` (like ui_x folder references)

## Output Example

```
2025-09-08 12:09:57,502 - INFO - Will check for changes in 21 columns
2025-09-08 12:09:57,489 - INFO - Matched projects: ui_15 -> ui_1 (Score: 100, Criterion: Dataset Speaking Titles)
2025-09-08 12:09:57,504 - INFO - Synchronization complete. 25 projects matched, 0 total changes detected
```

## Future Automation

This script can be automated using GitHub Actions:

```yaml
# .github/workflows/sync-sheets.yml
name: Sync Google Sheets
on:
  schedule:
    - cron: '0 9 * * *'  # Daily at 9 AM
  workflow_dispatch:  # Manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run sync
        env:
          GOOGLE_CREDENTIALS: ${{ secrets.GOOGLE_CREDENTIALS }}
        run: |
          echo "$GOOGLE_CREDENTIALS" > creds.json
          python scripts/sync_from_master_sheet.py --apply --credentials creds.json
```

## Error Handling

- **Connection Errors:** Checks Google Sheets API connectivity
- **Missing Columns:** Handles different column structures gracefully
- **No Matches:** Reports when projects can't be matched
- **Fuzzy Matching:** Uses similarity scores to avoid false positives

## Safety Features

- **Dry run default:** Never applies changes unless `--apply` is specified
- **Detailed logging:** Shows exactly what will change
- **Protected columns:** Critical columns are never modified
- **Backup recommendations:** Always backup sheets before major syncs
