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

# --- Main Multi-User Workflow Execution ---

def run_phase_1_for_multiple_users():
    """
    Main controller to load data and run the Phase 1 workflow for each user.
    """
    print("--- Initializing Phase 1: Multi-User Financial Profiling Engine ---")

    # 1. Build the reusable LangGraph workflow app
    workflow = StateGraph(FinancialAnalysisState)
    workflow.add_node("pandas_analysis", pandas_analysis_node)
    workflow.add_node("profile_llm", profile_llm_node)
    workflow.set_entry_point("pandas_analysis")
    workflow.add_edge("pandas_analysis", "profile_llm")
    workflow.add_edge("profile_llm", END)
    app = workflow.compile()

    # 2. Load the entire dataset once
    full_df = load_transactions("sample_data/upi_transactions.xlsx")
    if full_df is None:
        print("Halting process due to data loading failure.")
        return

    # 3. Identify all unique users
    unique_user_ids = full_df['user_id'].unique()
    print(f"Found {len(unique_user_ids)} unique users. Beginning analysis for each...")

    all_user_profiles = {}

    # 4. Loop through each user and run the graph
    for user_id in unique_user_ids:
        print(f"\n" + "="*50)
        print(f"Processing User ID: {user_id}")
        print("="*50)

        # Filter the DataFrame to get data for only the current user
        user_df = full_df[full_df['user_id'] == user_id].copy()

        if user_df.empty:
            all_user_profiles[user_id] = "No data available for this user."
            continue

        # Define the initial input for this user's graph run
        initial_input = {
            "user_id": user_id,
            "transactions_df": user_df
        }

        # Invoke the graph workflow for this single user
        final_state = app.invoke(initial_input)
        all_user_profiles[user_id] = final_state.get("profile_summary", "Error generating profile.")

    # 5. Display all the generated profiles
    print("\n" + "#"*60)
    print("      Phase 1 Processing Complete. Final User Profiles:")
    print("#"*60 + "\n")

    for user_id, profile in all_user_profiles.items():
        print(f"--- Financial Profile for User ID: {user_id} ---")
        print(profile)
        print("--- End of Profile ---\n")

if __name__ == "__main__":
    run_phase_1_for_multiple_users()