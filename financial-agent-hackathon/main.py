from langgraph.graph import StateGraph, END
from utils.state_manager import FinancialAnalysisState
from utils.data_loader import load_transactions
from agent.profile_builder import analyze_transactions_with_pandas, generate_profile_from_analysis
from agent.trend_analyzer import analyze_trends_with_pandas, summarize_trends_with_llm
from agent.budgeting_expert import create_budget_baseline_with_pandas, generate_budget_plan_with_llm
from agent.insight_generator import generate_final_report # Import the new function

# --- Define Graph Nodes ---

# Phase 1 Nodes
def pandas_analysis_node(state: FinancialAnalysisState) -> FinancialAnalysisState:
    print(f"--- User {state['user_id']} | Node: Pandas Profile Analysis ---")
    analysis_results = analyze_transactions_with_pandas(state['transactions_df'])
    return {"pandas_analysis": analysis_results}

def profile_llm_node(state: FinancialAnalysisState) -> FinancialAnalysisState:
    print(f"--- User {state['user_id']} | Node: LLM Profile Summary ---")
    profile = generate_profile_from_analysis(state['pandas_analysis'])
    return {"profile_summary": profile}

# Phase 2 Nodes
def trend_pandas_node(state: FinancialAnalysisState) -> FinancialAnalysisState:
    print(f"--- User {state['user_id']} | Node: Pandas Trend Analysis ---")
    analysis = analyze_trends_with_pandas(state['transactions_df'])
    return {"trend_analysis": analysis}

def trend_llm_node(state: FinancialAnalysisState) -> FinancialAnalysisState:
    print(f"--- User {state['user_id']} | Node: LLM Trend Summary ---")
    summary = summarize_trends_with_llm(state['trend_analysis'])
    return {"trend_summary": summary}

# Phase 3 Nodes
def budget_pandas_node(state: FinancialAnalysisState) -> FinancialAnalysisState:
    print(f"--- User {state['user_id']} | Node: Pandas Budget Baseline ---")
    baseline = create_budget_baseline_with_pandas(state['transactions_df'])
    return {"budget_baseline": baseline}

def budget_llm_node(state: FinancialAnalysisState) -> FinancialAnalysisState:
    print(f"--- User {state['user_id']} | Node: LLM Budget Plan ---")
    summary = generate_budget_plan_with_llm(state['budget_baseline'], state['profile_summary'])
    return {"budget_summary": summary}

# Phase 4 Node (NEW)
def insight_generator_node(state: FinancialAnalysisState) -> FinancialAnalysisState:
    print(f"--- User {state['user_id']} | Node: Insight Generator (Report Assembly) ---")
    report = generate_final_report(
        profile=state.get('profile_summary', 'N/A'),
        trends=state.get('trend_summary', 'N/A'),
        budget=state.get('budget_summary', 'N/A')
    )
    return {"final_report": report}

# --- Main Multi-User Workflow Execution ---

def run_full_analysis_for_multiple_users():
    print("--- Initializing Full (Phase 1-4) Multi-User Financial Analysis Engine ---")

    workflow = StateGraph(FinancialAnalysisState)

    # Add all nodes
    workflow.add_node("profile_pandas", pandas_analysis_node)
    workflow.add_node("profile_llm", profile_llm_node)
    workflow.add_node("trend_pandas", trend_pandas_node)
    workflow.add_node("trend_llm", trend_llm_node)
    workflow.add_node("budget_pandas", budget_pandas_node)
    workflow.add_node("budget_llm", budget_llm_node)
    workflow.add_node("generate_report", insight_generator_node) # Add the final node
    
    # Define the complete workflow graph
    workflow.set_entry_point("profile_pandas")
    workflow.add_edge("profile_pandas", "profile_llm")
    workflow.add_edge("profile_llm", "trend_pandas")
    workflow.add_edge("trend_pandas", "trend_llm")
    workflow.add_edge("trend_llm", "budget_pandas")
    workflow.add_edge("budget_pandas", "budget_llm")
    workflow.add_edge("budget_llm", "generate_report") # Final step is report generation
    workflow.add_edge("generate_report", END)
    
    app = workflow.compile()

    full_df = load_transactions("sample_data/upi_transactions.xlsx")
    if full_df is None: return

    unique_user_ids = full_df['user_id'].unique()
    print(f"Found {len(unique_user_ids)} unique users. Beginning full analysis...")
    all_user_reports = {}

    for user_id in unique_user_ids:
        print(f"\n" + "="*50)
        print(f"Processing User ID: {user_id}")
        print("="*50)

        user_df = full_df[full_df['user_id'] == user_id].copy()
        if user_df.empty:
            all_user_reports[user_id] = "No data available for this user."
            continue

        initial_input = {"user_id": user_id, "transactions_df": user_df}
        final_state = app.invoke(initial_input)
        
        all_user_reports[user_id] = final_state.get('final_report', 'Error generating report.')

    print("\n" + "#"*60)
    print("      Full Analysis Complete. Final User Reports:")
    print("#"*60 + "\n")

    for user_id, report in all_user_reports.items():
        print(f"--- Personalized Report for User ID: {user_id} ---")
        print(report)
        print("--- End of Report ---\n")

if __name__ == "__main__":
    run_full_analysis_for_multiple_users()