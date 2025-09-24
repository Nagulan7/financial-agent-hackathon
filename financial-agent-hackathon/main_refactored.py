from langgraph.graph import StateGraph, END
from utils.state_manager import FinancialAnalysisState
from utils.data_loader import load_transactions
from agent.profile_builder import analyze_transactions_with_pandas, generate_profile_from_analysis

# --- Define Graph Nodes for a SINGLE USER analysis ---

def pandas_analysis_node(state: FinancialAnalysisState) -> FinancialAnalysisState:
    """Node 1: Performs quantitative analysis for the user."""
    print(f"--- User {state['user_id']} | Node: Pandas Analysis ---")
    analysis_results = analyze_transactions_with_pandas(state['transactions_df'])
    return {"pandas_analysis": analysis_results}

def profile_llm_node(state: FinancialAnalysisState) -> FinancialAnalysisState:
    """Node 2: Generates qualitative insights for the user."""
    print(f"--- User {state['user_id']} | Node: LLM Profile ---")
    profile = generate_profile_from_analysis(state['pandas_analysis'])
    return {"profile_summary": profile}

# --- Reusable Analysis Functions ---

def build_workflow():
    """Build and return the reusable LangGraph workflow app."""
    workflow = StateGraph(FinancialAnalysisState)
    workflow.add_node("pandas_analysis", pandas_analysis_node)
    workflow.add_node("profile_llm", profile_llm_node)
    workflow.set_entry_point("pandas_analysis")
    workflow.add_edge("pandas_analysis", "profile_llm")
    workflow.add_edge("profile_llm", END)
    return workflow.compile()

def analyze_single_user(app, user_id, user_df):
    """Analyze a single user and return the results."""
    if user_df.empty:
        return {"profile_summary": "No data available for this user.", "pandas_analysis": {}}
    
    initial_input = {
        "user_id": user_id,
        "transactions_df": user_df
    }
    
    return app.invoke(initial_input)

def analyze_all_users_data(full_df):
    """
    Analyze all users in the dataset and return structured results.
    Returns a dictionary with user_id as key and analysis results as value.
    """
    if full_df is None or full_df.empty:
        print("No data to analyze.")
        return {}
    
    # Build the workflow once
    app = build_workflow()
    
    # Get unique users
    unique_user_ids = full_df['user_id'].unique()
    print(f"Found {len(unique_user_ids)} unique users. Beginning analysis for each...")
    
    results = {}
    
    # Analyze each user
    for user_id in unique_user_ids:
        print(f"\n" + "="*50)
        print(f"Processing User ID: {user_id}")
        print("="*50)
        
        # Filter data for current user
        user_df = full_df[full_df['user_id'] == user_id].copy()
        
        # Analyze the user
        final_state = analyze_single_user(app, user_id, user_df)
        
        # Store results
        results[user_id] = {
            'profile_summary': final_state.get("profile_summary", "Error generating profile."),
            'pandas_analysis': final_state.get("pandas_analysis", {}),
            'transactions_df': user_df
        }
    
    return results

# --- Main Multi-User Workflow Execution ---

def run_phase_1_for_multiple_users():
    """
    Main controller to load data and run the Phase 1 workflow for each user.
    This function prints results to console (CLI mode).
    """
    print("--- Initializing Phase 1: Multi-User Financial Profiling Engine ---")

    # Load the entire dataset once
    full_df = load_transactions("sample_data/upi_transactions.xlsx")
    if full_df is None:
        print("Halting process due to data loading failure.")
        return

    # Analyze all users
    results = analyze_all_users_data(full_df)
    
    if not results:
        print("No results to display.")
        return

    # Display all the generated profiles
    print("\n" + "#"*60)
    print("      Phase 1 Processing Complete. Final User Profiles:")
    print("#"*60 + "\n")

    for user_id, user_data in results.items():
        print(f"--- Financial Profile for User ID: {user_id} ---")
        print(user_data['profile_summary'])
        print("--- End of Profile ---\n")

def load_and_analyze_for_streamlit(file_path=None, df=None):
    """
    Load and analyze data specifically for Streamlit usage.
    Returns the full dataset and analysis results.
    """
    if df is not None:
        full_df = df
    else:
        full_df = load_transactions(file_path)
    
    if full_df is None or full_df.empty:
        return None, {}
    
    results = analyze_all_users_data(full_df)
    return full_df, results

# --- Entry Point ---

if __name__ == "__main__":
    # CLI mode - run the original functionality
    run_phase_1_for_multiple_users()