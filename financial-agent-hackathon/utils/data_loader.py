import pandas as pd
import os
from typing import Optional

def load_transactions(file_path: str) -> Optional[pd.DataFrame]:
    """
    Loads transaction data from an Excel (.xlsx, .xls) or CSV (.csv) file
    and performs basic validation.
    """
    try:
        # --- NEW: Check the file extension ---
        _, file_extension = os.path.splitext(file_path)

        if file_extension.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif file_extension.lower() == '.csv':
            df = pd.read_csv(file_path)
        else:
            print(f"Error: Unsupported file type '{file_extension}'. Please use an Excel or CSV file.")
            return None

        # Critical check to ensure user_id column exists
        if 'user_id' not in df.columns:
            print("Error: The dataset must contain a 'user_id' column.")
            return None
            
        print(f"Data loaded successfully from {file_path}. Found {len(df)} total transactions.")
        return df
        
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
        return None
    except Exception as e:
        print(f"An error occurred while reading the data file: {e}")
        return None