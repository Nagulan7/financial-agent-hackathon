from typing import TypedDict, Optional, Any
import pandas as pd

class FinancialAnalysisState(TypedDict):
    """
    Represents the state of the analysis graph for a SINGLE user.
    """
    # Input data
    user_id: Any
    transactions_df: pd.DataFrame
    
    # Phase 1: Profiling Results
    pandas_analysis: Optional[dict[str, Any]]
    profile_summary: Optional[str]
    
    # Phase 2: Trend Analysis Results
    trend_analysis: Optional[dict[str, Any]]
    trend_summary: Optional[str]
    
    # Phase 3: Budget Planning Results
    budget_baseline: Optional[dict[str, Any]]
    budget_summary: Optional[str]

    # Phase 4: Final Report (NEW)
    final_report: Optional[str]
    
    # Error handling
    error_message: Optional[str]