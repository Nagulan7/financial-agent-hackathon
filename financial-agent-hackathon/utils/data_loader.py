import pandas as pd
from typing import Optional

def load_transactions(file_path: str) -> Optional[pd.DataFrame]:
    """
    Loads the main transaction data file and performs basic validation.
    """
    try:
        df = pd.read_excel(file_path)
        
        # CRITICAL CHECK: Ensure user_id column exists
        if 'user_id' not in df.columns:
            print("Error: The dataset must contain a 'user_id' column.")
            return None
            
        print(f"Data loaded successfully from {file_path}. Found {len(df)} total transactions.")
        return df
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
        return None
    except Exception as e:
        print(f"An error occurred while reading the Excel file: {e}")
        return None