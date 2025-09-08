#!/usr/bin/env python3
"""
Script to synchronize changes from the master Google Sheet to the primary Lacuna Fund sheet.

This script:
1. Fetches data from both the master sheet (all projects) and primary sheet (Lacuna projects only)
2. Identifies projects in master sheet marked as "Lacuna Dataset = Yes"
3. Matches them with projects in the primary sheet using multiple fallback criteria
4. Detects content differences and syncs changes to the primary sheet
5. Never overwrites ui_x related columns in the primary sheet

Usage:
    python scripts/sync_from_master_sheet.py [--dry-run] [--credentials path/to/creds.json]
"""

import argparse
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from thefuzz import process, fuzz
import logging
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SheetSyncer:
    def __init__(self, credentials_path):
        """Initialize the Google Sheets client."""
        self.credentials_path = credentials_path
        self.client = None
        self.spreadsheet = None
        self.primary_sheet = None
        self.master_sheet = None
        
        # Column mapping for fuzzy matching (same as build_from_google_sheets.py)
        self.CANONICAL_COLUMN_MAP = {
            "Project ID": ["Project ID", "Stable ID", "Unique Project ID"],
            "OnSite Name": ["OnSite Name", "Name in GIZ-internal database", "Project Title", "Title"],
            "Dataset Speaking Titles": ["Dataset Speaking Titles", "Dataset Title", "Expressive Title [for dataset]", "Catchy Title [for dataset]"],
            "Use Case Speaking Title": ["Use Case Speaking Title", "Use Case Title", "Expressive Title [for use case, application]", "Catchy Title [for use case, application]"],
            "Description - What can be done with this? What is this about?": [
                "Description - What can be done with this? What is this about?",
                "Description - What can be done", "Description", "About",
                "What this is about and how can I use this? ",
                "What this is about/Description"
            ],
            "Dataset Link": ["Dataset Link", "Dataset URL", "Access to the dataset [link]"],
            "Model/Use-Case Links": [
                "Model/Use-Case Links", "Use Case Link", "Model Link", "Model/Use Case URL",
                "Access to AI Model, Software, AI Application [link]"
            ],
            "Domain/SDG": ["Domain/SDG", "Domain", "SDG", "Sector /Sustainable Development Goal ", "Technical Domain"],
            "Use Case Pipeline Status": ["Use Case Pipeline Status", "Status", "Pipeline Status", "Use Case Pipeline Status / maturity [INTERNAL]"],
            "Data Type": ["Data Type", "Type", "Type of Data"],
            "Point of Contact/Communities": ["Point of Contact/Communities", "Contact", "POC", "Community", "Point of contact & community support "],
            "Country Team": ["Country Team", "Country", "Region", "Team", "Country / Region "],
            "Data - Key Characteristics": [
                "Data - Key Characteristics", "Data Characteristics", "Data Details",
                "Data: how to use it & key characteristics ",
                "Data characteristics: how to use it & key characteristics "
            ],
            "Model/Use-Case - Key Characteristics": [
                "Model/Use-Case - Key Characteristics", "Model Characteristics", "Model Details", "Use Case Characteristics",
                "How to use & key characteristics of the AI Model, Software, AI Application",
                "Model characteristics: How to use & key characteristics of the AI Model, Software, AI Application"
            ],
            "Deep Dive - How can you concretely work with this and build on this?": [
                "Deep Dive - How can you concretely work with this and build on this?",
                "Deep Dive - How can you concretely work", "Deep Dive", "How to Use",
                "Deep dive: How can you concretely work with this and built on this? How much will this cost and which resources are available to help me? ",
                "How to use it: How can you concretely work with this and built on this? How much will this cost and which resources are available to help me? "
            ],
            "License": ["License", "Usage Rights"],
            "Organizations Involved": [
                "Organizations involved - including logos, links and visual elements",
                "Organizations Involved", "Contributing Organizations", "Partners"
            ],
            "Authors": [
                "Authors of this information.", "Authors", "Information Authors", "Data Curators",
                "Editor of this information:"
            ],
            "Lacuna Dataset": [
                "Lacuna Dataset (Yes/No)", "Lacuna Dataset", "Lacuna Fund Dataset", "Is Lacuna Dataset"
            ]
        }

    def connect_to_sheets(self):
        """Establish connection to Google Sheets."""
        try:
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            credentials = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_path, scope)
            self.client = gspread.authorize(credentials)
            
            # Connect to the spreadsheet
            spreadsheet_id = "18sgZgPGZuZjeBTHrmbr1Ra7mx8vSToUqnx8vCjhIp0c"
            self.spreadsheet = self.client.open_by_key(spreadsheet_id)
            
            # Get both sheets
            self.primary_sheet = self.spreadsheet.get_worksheet_by_id(2002859408)  # Lacuna projects only
            self.master_sheet = self.spreadsheet.get_worksheet_by_id(756053104)   # All projects
            
            logger.info(f"Connected to primary sheet: {self.primary_sheet.title}")
            logger.info(f"Connected to master sheet: {self.master_sheet.title}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            raise

    def fetch_sheet_data(self, sheet):
        """Fetch and normalize data from a sheet."""
        try:
            all_values = sheet.get_all_values()
            if len(all_values) < 3:
                logger.error(f"Sheet {sheet.title} has insufficient data")
                return None, None
                
            headers = all_values[0]
            # Skip explanatory row (index 1) and get data from row 2 onwards
            data = all_values[2:]
            
            # Create DataFrame
            df = pd.DataFrame(data, columns=headers)
            
            # Apply column mapping using fuzzy matching
            mapped_df = self.apply_column_mapping(df)
            
            logger.info(f"Fetched {len(mapped_df)} rows from {sheet.title}")
            return mapped_df, headers
            
        except Exception as e:
            logger.error(f"Failed to fetch data from {sheet.title}: {e}")
            return None, None

    def apply_column_mapping(self, df):
        """Apply fuzzy column mapping to standardize column names."""
        header_mapping = {}
        processed_headers = set()
        similarity_threshold = 70
        
        # Find best matches for each canonical column
        for canonical_name, aliases in self.CANONICAL_COLUMN_MAP.items():
            best_match = None
            highest_score = -1
            
            for actual_header in df.columns:
                if actual_header in processed_headers:
                    continue
                    
                match_result = process.extractOne(actual_header, aliases, scorer=fuzz.token_sort_ratio)
                if match_result and match_result[1] > highest_score:
                    highest_score = match_result[1]
                    best_match = actual_header
            
            if best_match and highest_score >= similarity_threshold:
                header_mapping[best_match] = canonical_name
                processed_headers.add(best_match)
                logger.debug(f"Mapped: '{best_match}' -> '{canonical_name}' (Score: {highest_score})")
        
        # Rename columns and return
        df_mapped = df.rename(columns=header_mapping)
        return df_mapped

    def find_lacuna_projects(self, master_df):
        """Find projects in master sheet marked as Lacuna Dataset = Yes."""
        if 'Lacuna Dataset' not in master_df.columns:
            logger.error("'Lacuna Dataset' column not found in master sheet")
            return pd.DataFrame()
        
        # Filter for Lacuna projects (case-insensitive)
        lacuna_mask = master_df['Lacuna Dataset'].str.lower().str.strip() == 'yes'
        lacuna_projects = master_df[lacuna_mask].copy()
        
        logger.info(f"Found {len(lacuna_projects)} Lacuna projects in master sheet")
        return lacuna_projects

    def match_projects(self, lacuna_projects, primary_df):
        """Match projects between master and primary sheets using multiple criteria."""
        matches = []
        
        # Define matching criteria in order of preference
        matching_criteria = [
            'Dataset Speaking Titles',
            'Use Case Speaking Title', 
            'Point of Contact/Communities',
            'Dataset Link',
            'Model/Use-Case Links'
        ]
        
        for _, lacuna_row in lacuna_projects.iterrows():
            best_match = None
            best_score = 0
            match_criterion = None
            
            # Try each matching criterion
            for criterion in matching_criteria:
                if criterion not in lacuna_row.index or criterion not in primary_df.columns:
                    continue
                    
                lacuna_value = str(lacuna_row[criterion]).strip()
                if not lacuna_value or lacuna_value.lower() in ['nan', 'none', '']:
                    continue
                
                # Find best match in primary sheet for this criterion
                primary_values = primary_df[criterion].astype(str).str.strip()
                match_result = process.extractOne(lacuna_value, primary_values.tolist(), scorer=fuzz.token_sort_ratio)
                
                if match_result and match_result[1] > best_score and match_result[1] >= 80:
                    best_score = match_result[1]
                    # Find the index of this match
                    matching_indices = primary_df[primary_df[criterion].astype(str).str.strip() == match_result[0]].index
                    if len(matching_indices) > 0:
                        best_match = matching_indices[0]
                        match_criterion = criterion
            
            if best_match is not None:
                matches.append({
                    'lacuna_index': lacuna_row.name,
                    'primary_index': best_match,
                    'match_score': best_score,
                    'match_criterion': match_criterion,
                    'lacuna_project_id': lacuna_row.get('Project ID', 'Unknown'),
                    'primary_project_id': primary_df.loc[best_match].get('Project ID', 'Unknown')
                })
                logger.info(f"Matched projects: {lacuna_row.get('Project ID', 'Unknown')} -> {primary_df.loc[best_match].get('Project ID', 'Unknown')} "
                          f"(Score: {best_score}, Criterion: {match_criterion})")
            else:
                logger.warning(f"No match found for lacuna project: {lacuna_row.get('Project ID', 'Unknown')}")
        
        return matches

    def detect_changes(self, lacuna_projects, primary_df, matches):
        """Detect content differences between matched projects."""
        changes = []
        
        # Get common columns (excluding ui_x related ones)
        lacuna_columns = set(lacuna_projects.columns)
        primary_columns = set(primary_df.columns)
        common_columns = lacuna_columns.intersection(primary_columns)
        
        # Remove columns we should never sync
        protected_columns = {'Project ID'}  # Add other protected columns as needed
        ui_columns = {col for col in common_columns if 'ui_' in col.lower()}
        
        syncable_columns = common_columns - protected_columns - ui_columns
        
        logger.info(f"Will check for changes in {len(syncable_columns)} columns: {sorted(syncable_columns)}")
        
        for match in matches:
            lacuna_row = lacuna_projects.loc[match['lacuna_index']]
            primary_row = primary_df.loc[match['primary_index']]
            
            row_changes = []
            
            for col in syncable_columns:
                lacuna_value = str(lacuna_row[col]).strip()
                primary_value = str(primary_row[col]).strip()
                
                # Normalize empty values
                if lacuna_value.lower() in ['nan', 'none', '']:
                    lacuna_value = ''
                if primary_value.lower() in ['nan', 'none', '']:
                    primary_value = ''
                
                # Check if values are different
                if lacuna_value != primary_value:
                    row_changes.append({
                        'column': col,
                        'master_value': lacuna_value,
                        'primary_value': primary_value
                    })
            
            if row_changes:
                changes.append({
                    'match': match,
                    'changes': row_changes
                })
                logger.info(f"Found {len(row_changes)} changes for project {match['lacuna_project_id']}")
        
        return changes

    def apply_changes(self, changes, primary_df, primary_headers, dry_run=True):
        """Apply changes to the primary sheet."""
        if not changes:
            logger.info("No changes to apply")
            return
        
        logger.info(f"{'[DRY RUN] ' if dry_run else ''}Applying {len(changes)} project updates...")
        
        if not dry_run:
            # Get all values from primary sheet to work with
            all_values = self.primary_sheet.get_all_values()
            
        for change_set in changes:
            match = change_set['match']
            project_changes = change_set['changes']
            
            logger.info(f"{'[DRY RUN] ' if dry_run else ''}Updating project {match['lacuna_project_id']} -> {match['primary_project_id']}")
            
            for change in project_changes:
                col = change['column']
                new_value = change['master_value']
                old_value = change['primary_value']
                
                logger.info(f"  {'[DRY RUN] ' if dry_run else ''}Column '{col}': '{old_value}' -> '{new_value}'")
                
                if not dry_run:
                    try:
                        # Find the column index in the original headers
                        # We need to reverse-map from canonical name back to original header
                        original_col = None
                        for orig_header in primary_headers:
                            # Apply the same mapping logic to find the original column
                            for canonical_name, aliases in self.CANONICAL_COLUMN_MAP.items():
                                if canonical_name == col:
                                    match_result = process.extractOne(orig_header, aliases, scorer=fuzz.token_sort_ratio)
                                    if match_result and match_result[1] >= 70:
                                        original_col = orig_header
                                        break
                            if original_col:
                                break
                        
                        if original_col and original_col in primary_headers:
                            col_index = primary_headers.index(original_col) + 1  # Google Sheets is 1-indexed
                            row_index = match['primary_index'] + 3  # +3 because: 0-based index + 1 for 1-based + 2 for header rows
                            
                            # Update the cell in Google Sheets
                            self.primary_sheet.update_cell(row_index, col_index, new_value)
                            logger.info(f"    ✅ Updated cell ({row_index}, {col_index}) '{original_col}' with '{new_value}'")
                        else:
                            logger.warning(f"    ⚠️  Could not find original column for '{col}' in primary sheet headers")
                            
                    except Exception as e:
                        logger.error(f"    ❌ Failed to update column {col}: {e}")

    def run_sync(self, dry_run=True):
        """Run the complete synchronization process."""
        logger.info(f"Starting synchronization {'(DRY RUN)' if dry_run else ''}")
        
        # Connect to sheets
        self.connect_to_sheets()
        
        # Fetch data from both sheets
        logger.info("Fetching data from sheets...")
        primary_df, primary_headers = self.fetch_sheet_data(self.primary_sheet)
        master_df, master_headers = self.fetch_sheet_data(self.master_sheet)
        
        if primary_df is None or master_df is None:
            logger.error("Failed to fetch sheet data")
            return False
        
        # Find Lacuna projects in master sheet
        lacuna_projects = self.find_lacuna_projects(master_df)
        if lacuna_projects.empty:
            logger.warning("No Lacuna projects found in master sheet")
            return False
        
        # Match projects between sheets
        logger.info("Matching projects between sheets...")
        matches = self.match_projects(lacuna_projects, primary_df)
        if not matches:
            logger.warning("No project matches found")
            return False
        
        # Detect changes
        logger.info("Detecting content differences...")
        changes = self.detect_changes(lacuna_projects, primary_df, matches)
        
        # Apply changes
        self.apply_changes(changes, primary_df, primary_headers, dry_run=dry_run)
        
        # Summary
        total_changes = sum(len(change_set['changes']) for change_set in changes)
        logger.info(f"Synchronization complete. {len(matches)} projects matched, {total_changes} total changes detected")
        
        if total_changes > 0 and dry_run:
            logger.info("Run with --apply to actually apply these changes")
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Sync changes from master Google Sheet to Lacuna Fund sheet')
    parser.add_argument('--credentials', type=str, 
                       default="data_sources/google_sheets_api/service_account_JN.json",
                       help='Path to Google Sheets API credentials file')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Show changes without applying them (default)')
    parser.add_argument('--apply', action='store_true',
                       help='Actually apply the changes to the sheet')
    
    args = parser.parse_args()
    
    # If --apply is specified, turn off dry-run
    if args.apply:
        args.dry_run = False
    
    try:
        syncer = SheetSyncer(args.credentials)
        success = syncer.run_sync(dry_run=args.dry_run)
        
        if success:
            logger.info("Script completed successfully")
        else:
            logger.error("Script completed with errors")
            exit(1)
            
    except Exception as e:
        logger.error(f"Script failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()
