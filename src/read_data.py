import os
import pandas as pd

# Define the path to the mock SharePoint directory
mock_folder = '/Users/arnavmenon/Code/extra/flexify/mock_sharepoint'

print(f"--- Reading Excel files from: {mock_folder} ---")

# Iterate through files in the directory
for filename in os.listdir(mock_folder):
    if filename.endswith('.xlsx'):
        file_path = os.path.join(mock_folder, filename)
        print(f"\nProcessing Excel file: {file_path}")
        try:
            # Read all sheets into a dictionary of DataFrames
            excel_data = pd.read_excel(file_path, sheet_name=None)

            # Process each sheet
            for sheet_name, df in excel_data.items():
                print(f"  - Sheet Name: '{sheet_name}'")
                print(f"    Columns: {list(df.columns)}")
                print(f"    Number of Rows: {len(df)}")

        except Exception as e:
            print(f"  * Error reading file {file_path}: {e}")

print("\n--- Reading Q&A Knowledge Base ---")

# Define potential Q&A filenames
qa_csv_filename = 'faq.csv'

qa_csv_path = os.path.join(mock_folder, qa_csv_filename)

qa_df = None
qa_source_file = None

# Try reading CSV first
if os.path.exists(qa_csv_path):
    print(f"Found Q&A file: {qa_csv_path}")
    try:
        qa_df = pd.read_csv(qa_csv_path)
        qa_source_file = qa_csv_path
    except Exception as e:
        print(f"  * Error reading CSV file {qa_csv_path}: {e}")
else:
    print(f"Could not find '{qa_csv_filename}' in {mock_folder}")

# Print info if Q&A data was loaded
if qa_df is not None:
    print(f"\nSuccessfully loaded Q&A data from: {qa_source_file}")
    print(f"  Columns: {list(qa_df.columns)}")
    print(f"  Number of Q&A pairs: {len(qa_df)}")

print("\n--- Script Finished ---")