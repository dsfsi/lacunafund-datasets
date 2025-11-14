#!/usr/bin/env python3
"""
Add Climate Datasets Integration Script

This script integrates the extracted climate datasets from climate-datasets.json
into the Excel data catalog following the established pattern from health datasets.
"""

import json
import pandas as pd
from pathlib import Path
import sys

def load_climate_datasets():
    """Load the extracted climate datasets from climate-datasets.json"""
    climate_json_path = Path(__file__).parent.parent / "climate-datasets.json"
    
    if not climate_json_path.exists():
        raise FileNotFoundError(f"Climate datasets JSON not found at {climate_json_path}")
    
    with open(climate_json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_excel_rows(climate_datasets):
    """Convert climate datasets to Excel format matching existing structure"""
    excel_rows = []
    
    # Starting from ui_50 based on current data going up to ui_49
    starting_ui_number = 50
    
    for idx, dataset in enumerate(climate_datasets):
        ui_id = f"ui_{starting_ui_number + idx}"
        
        # Map climate dataset fields to Excel columns
        excel_row = {
            "Project ID": ui_id,
            "Dataset Speaking Titles": dataset["title"],
            "Use Case Speaking Title": None,  # Not provided in climate data
            "Description - What can be done with this? What is this about?": dataset["description"],
            "Dataset Link": dataset["dataset_link"],
            "Model/Use-Case Links": None,
            "Domain/SDG": "SDG 13 (Climate Action)",  # All climate datasets
            "Data Type": "Climate Data",  # Appropriate for climate datasets
            "Point of Contact/Communities": dataset["contact"],
            "Country Team": dataset["country"],
            "Data - Key Characteristics": "",  # To be filled if needed
            "Model/Use-Case - Key Characteristics": "",
            "Deep Dive - How can you concretely work with this and build on this?": "",
            "License": "",  # To be filled if available
            "Organizations Involved": f"Powered by: {', '.join([org['organization'] for org in dataset['authors']])}\nCatalyzed by: Lacuna-Fund / Meridian (Climate-call) & FAIR Forward - AI for All\nFinanced by: BMZ",
            "Authors": ', '.join([f"{', '.join(author['names'])} ({author['organization']})" for author in dataset["authors"]]),
            "Maturity / Readiness for replication or scaling [INTERNAL]": "Dataset",
            "Technical Domain": "Climate Science",
            "Expressive visualization / picture related to dataset / possible use / story-tellling": dataset["image"],
            "Additional Resources (Paper, Publications, etc)": None,
            "GIZ Funded (Yes/No)": "Yes",
            "Info on fair sharing as as Digital Public Good": None,
            "Comments": f"Added via climate dataset integration - extracted from climate.html"
        }
        
        excel_rows.append(excel_row)
    
    return excel_rows

def add_to_excel_catalog(excel_rows):
    """Add climate datasets to the Excel data catalog"""
    # Check if Excel file exists
    excel_path = Path(__file__).parent.parent / "docs" / "data_catalog.xlsx"
    
    if not excel_path.exists():
        print(f"Excel file not found at {excel_path}")
        print("Creating new Excel file with climate datasets...")
        df = pd.DataFrame(excel_rows)
    else:
        # Load existing Excel file
        print(f"Loading existing Excel file from {excel_path}")
        try:
            df_existing = pd.read_excel(excel_path)
            df_new = pd.DataFrame(excel_rows)
            df = pd.concat([df_existing, df_new], ignore_index=True)
            print(f"Added {len(excel_rows)} climate datasets to existing {len(df_existing)} datasets")
        except Exception as e:
            print(f"Error loading Excel file: {e}")
            print("Creating new Excel file with climate datasets...")
            df = pd.DataFrame(excel_rows)
    
    # Save updated Excel file
    try:
        df.to_excel(excel_path, index=False)
        print(f"Successfully saved updated Excel file to {excel_path}")
        return True
    except Exception as e:
        print(f"Error saving Excel file: {e}")
        return False

def main():
    """Main integration function"""
    print("Starting climate datasets integration...")
    
    try:
        # Load climate datasets
        climate_datasets = load_climate_datasets()
        print(f"Loaded {len(climate_datasets)} climate datasets")
        
        # Convert to Excel format
        excel_rows = create_excel_rows(climate_datasets)
        print(f"Created {len(excel_rows)} Excel rows")
        
        # Add to Excel catalog
        success = add_to_excel_catalog(excel_rows)
        
        if success:
            print("\n✓ Climate datasets successfully integrated!")
            print("Next steps:")
            print("1. Review the Excel file: docs/data_catalog.xlsx")
            print("2. Run generate_catalog.py to rebuild the site")
            print("3. Commit and push changes")
        else:
            print("\n✗ Integration failed!")
            return 1
            
    except Exception as e:
        print(f"Error during integration: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())