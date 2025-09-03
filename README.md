# Data Catalog

Welcome to the Lacuna Fund's data and use-case catalog. Below is a list of datasets and use-cases that have been collected throughout the Lacuna Fund.

You can access the live website here: [Data Catalog!](https://www.dsfsi.co.za/lacunafund-datasets/)

> **Note:** This data catalog is currently a prototype and is not yet fully developed. It is intended to showcase the concept and functionality, but may undergo significant changes in the future.

## How to Contribute Data

If you are a Lacuna Fund grantee and want to add/change your dataset, please see the instructions below:

1.  **Access the Source:** The data for this catalog lives in this [Google Sheet](https://docs.google.com/spreadsheets/d/18sgZgPGZuZjeBTHrmbr1Ra7mx8vSToUqnx8vCjhIp0c/edit?gid=2002859408#gid=2002859408).
2.  **Add Your Project:** Add a new row to the sheet and fill in the details for your project. Please follow the format of existing entries and use the second row as a guide for the expected content in each column.
3.  **Update the Website:** Once you've added your information to the Google Sheet, the website needs to be rebuilt to include it. Please contact one of the repository maintainers or follow the "Update via GitHub Actions" steps below (if you have write access) to trigger an update.

## How to Update the Website

The content of this catalog is primarily sourced from the Google Sheet mentioned above. Changes made there need to be reflected on the website.

There are two main ways to update the website:

1.  **Local Update (for Developers):**
    *   Ensure you have the prerequisites installed (see Development section).
    *   Run the main build script locally: `python scripts/build_from_google_sheets.py`
    *   This single script fetches the latest data, applies necessary processing (like fuzzy column matching), saves the intermediate `docs/data_catalog.xlsx`, creates/updates project markdown files in `docs/public/projects/`, generates the final `docs/index.html`, and saves a daily backup CSV to `data_sources/google_sheets_backup/`.
    *   Optionally, run `python scripts/download_placeholder_images.py` if new projects need placeholder images (requires Pexels API key setup).
    *   Commit and push all changed files (including `index.html`, `.xlsx`, backups, and any new/modified files in `docs/public/projects/`) to the `main` branch.

2.  **Update via GitHub Actions (for Non-Developers with Repo Access):**
    *   This method allows updating the website directly from GitHub without running code locally.
    *   Go to the repository's **Actions** tab on GitHub.
    *   In the left sidebar, click on the "**Manually Update Website from Google Sheets**" workflow.
    *   Above the list of workflow runs, click the "**Run workflow**" dropdown button.
    *   Ensure the "Branch: `main`" is selected.
    *   Click the green "**Run workflow**" button.
    *   The workflow will perform the same steps as running `scripts/build_from_google_sheets.py` locally, fetching the latest data, rebuilding the website, and automatically committing the changes to the `main` branch. The live website will be updated shortly after the workflow completes successfully. (Note: This action does not currently run the placeholder image download script).


### Placeholder Images

To download placeholder images for projects lacking them:
```bash
python scripts/download_placeholder_images.py
```
This requires a Pexels API key. Set it up via:
- A `.env` file in the root directory: `PEXELS_API_KEY=your_api_key_here`
- Command-line argument: `--api-key YOUR_API_KEY`

(Note: The `scripts/download_placeholder_images.py` script uses `requirements.txt` for its dependencies.)

### Configuration

#### Google Sheets API Credentials

1. Create a Google Cloud service account.
2. Download its JSON key file.
3. Save it as `data_sources/google_sheets_api/service_account_JN.json` (or match the path used in scripts/workflows).
4. Ensure this file is listed in `.gitignore` and **never commit it**.

#### Pexels API Key

Needed for `scripts/download_placeholder_images.py`. Set via `.env` file or `--api-key` argument.


### Project Structure

```
├── data_sources/
│   ├── google_sheets_api/            # Google Sheets API credentials
│   │   └── service_account_JN.json   # Service account file (ignored by git)
│   └── google_sheets_backup/         # Daily and monthly raw CSV backups
├── scripts/                          # Build and utility scripts
│   ├── build_from_google_sheets.py   # Main build script
│   ├── generate_catalog.py           # HTML catalog generator
│   ├── download_placeholder_images.py # Image download utility
│   ├── backup_google_sheet.py        # Backup utility
│   └── placeholder_images_README.md  # Image documentation
├── docs/                             # Generated website files
│   ├── data_catalog.xlsx             # Processed data from Google Sheets
│   ├── index.html                    # Main website (GitHub Pages)
│   ├── enhanced_side_panel.js         # Side panel functionality
│   ├── enhanced_side_panel.css        # Side panel styles
│   └── public/projects/              # Project-specific files
├── .github/workflows/                # GitHub Actions
│   ├── update_from_google_sheets.yml # Manual website update
│   ├── monthly_backup.yml            # Monthly backup automation
│   └── analytics_update.yml          # Daily analytics collection
└── requirements.txt                  # Python dependencies
```

### GitHub Actions

- `.github/workflows/update_from_google_sheets.yml`: **Manually triggered** workflow to run `scripts/build_from_google_sheets.py` and commit results to `main`.
- `.github/workflows/monthly_backup.yml`: **Automatically triggered** workflow (1st of month) to run `scripts/backup_google_sheet.py` and commit the monthly raw CSV backup.

### Contributing (Code)

If you would like to contribute *code changes* to this project, please follow these steps:

1. Fork the repository
2. Create a new branch for your feature (`git checkout -b feature/YourFeature`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add some feature'`)
5. Push to the branch (`git push origin feature/YourFeature`)
6. Create a new Pull Request

Please ensure that your code follows the existing style and includes appropriate documentation.

## License

This project is licensed under the terms of the LICENSE file included in the repository.