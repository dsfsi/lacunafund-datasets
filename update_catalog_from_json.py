#!/usr/bin/env python3
"""
Script to update the data catalog from the frontend/data.json file.
This script reads the JSON data and regenerates the HTML catalog.
"""

import json
import pandas as pd
import sys
import os

def update_catalog_from_json():
    """Read the frontend/data.json file and regenerate the catalog."""
    
    # Paths
    json_file = "frontend/data.json"
    excel_file = "docs/data_catalog.xlsx"
    
    print(f"Reading data from {json_file}...")
    
    # Read the JSON data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Successfully loaded {len(data)} records from JSON")
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return False
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Save as Excel (to match the existing workflow)
    try:
        df.to_excel(excel_file, index=False)
        print(f"Successfully saved data to {excel_file}")
    except Exception as e:
        print(f"Error saving Excel file: {e}")
        return False
    
    # Now run the generate_catalog.py script
    print("Generating HTML catalog...")
    try:
        os.system(f'python scripts/generate_catalog.py --input "{excel_file}" --output "docs/index.html"')
        print("Successfully generated HTML catalog")
        return True
    except Exception as e:
        print(f"Error generating catalog: {e}")
        return False

if __name__ == "__main__":
    success = update_catalog_from_json()
    if success:
        print("\n✅ Catalog update completed successfully!")
        print("📁 Updated files:")
        print("   - docs/data_catalog.xlsx")
        print("   - docs/index.html")
        print("   - frontend/data.json (source)")
        print("\n🌐 The agriculture datasets have been integrated into the site!")
    else:
        print("\n❌ Catalog update failed!")
        sys.exit(1)