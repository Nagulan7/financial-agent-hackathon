from typing import TypedDict, Optional, Any
import pandas as pd

class FinancialAnalysisState(TypedDict):
    """
    Represents the state of the analysis graph for a SINGLE user.
    """
    # Input data for the user
    user_id: Any
    transactions_df: pd.DataFrame
    
    # Results of Phase 1
    pandas_analysis: Optional[dict[str, Any]]
    profile_summary: Optional[str]
    
    # For error handling
    error_message: Optional[str]