import pandas as pd
import json

# Read existing Excel file
excel_file = 'docs/data_catalog.xlsx'
df = pd.read_excel(excel_file)

print(f"Current Excel file has {len(df)} rows")

# Read health datasets from JSON
with open('health-datasets.json', 'r') as f:
    health_data = json.load(f)

print(f"Health datasets file has {len(health_data)} entries")

# Convert health datasets to DataFrame with correct format
health_rows = []
for item in health_data:
    # Map from the health dataset format to Excel format
    row = {
        'Project ID': f"ui_{item['Project ID']}",  # Convert to ui_X format
        'Dataset Speaking Titles': item.get('Project Title', ''),
        'Use Case Speaking Title': item.get('Use Cases', ''),
        'Description - What can be done with this? What is this about?': item.get('Project Description', ''),
        'Dataset Link': item.get('Project Link', ''),
        'Model/Use-Case Links': '',  # Not available in health data
        'Domain/SDG': item.get('Project Domain', ''),
        'Data Type': item.get('Data Type', ''),
        'Point of Contact/Communities': item.get('Contact', ''),
        'Country Team': item.get('Country', ''),
        'Data - Key Characteristics': item.get('Dataset Size', ''),
        'Model/Use-Case - Key Characteristics': item.get('Technical Details', ''),
        'Deep Dive - How can you concretely work with this and build on this?': item.get('Application Area', ''),
        'License': item.get('License', ''),
        'Organizations Involved': item.get('Author Affiliation', ''),
        'Authors': item.get('Project Author', ''),
        'Maturity / Readiness for replication or scaling [INTERNAL]': 'Dataset',  # Default value
        'Technical Domain': item.get('Model Type', ''),
        'Expressive visualization / picture related to dataset / possible use / story-tellling': None,
        'Additional Resources (Paper, Publications, etc)': None,
        'GIZ Funded (Yes/No)': 'Yes',  # Default for health datasets
        'Info on fair sharing as as Digital Public Good ': item.get('License', ''),
        'Comments': None
    }
    health_rows.append(row)

# Create DataFrame for health datasets
health_df = pd.DataFrame(health_rows)

# Combine the existing data with health data
combined_df = pd.concat([health_df, df], ignore_index=True)

print(f"Combined DataFrame has {len(combined_df)} rows")

# Sort by Project ID to maintain order (health first: ui_44-49, then agriculture: ui_1-43)
combined_df['sort_key'] = combined_df['Project ID'].str.extract(r'ui_(\d+)')[0].astype(int)
combined_df = combined_df.sort_values('sort_key').drop('sort_key', axis=1)

# Save back to Excel
combined_df.to_excel(excel_file, index=False)

print(f"Successfully updated {excel_file} with health datasets")
print(f"New Project IDs: {list(combined_df['Project ID'][:10])}")