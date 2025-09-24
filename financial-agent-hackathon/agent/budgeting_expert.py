import pandas as pd
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def create_budget_baseline_with_pandas(df: pd.DataFrame) -> dict:
    """
    Analyzes historical data to create a baseline of average monthly spending.
    """
    print("Executing Pandas Budget Baseline Node...")
    
    # --- Data Preparation ---
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['month'] = df['timestamp'].dt.to_period('M')
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    
    debit_df = df[df['direction'] == 'debit'].copy()
    
    # --- Categorization Mapping ---
    # Map specific categories to broader budget categories (Needs vs. Wants)
    # This is a crucial step for high-level budgeting.
    def map_category(cat):
        cat = str(cat).lower()
        if any(c in cat for c in ['groceries', 'utilities', 'rent', 'transport', 'bills', 'emi']):
            return 'Needs'
        elif any(c in cat for c in ['shopping', 'food', 'travel', 'entertainment', 'recharge', 'lifestyle']):
            return 'Wants'
        else:
            return 'Other'
            
    debit_df['budget_category'] = debit_df['category'].apply(map_category)
    
    # --- Analysis ---
    # Calculate average monthly spend per budget category
    monthly_spend = debit_df.groupby(['month', 'budget_category'])['amount'].sum().unstack(fill_value=0)
    avg_monthly_spend = monthly_spend.mean()
    
    total_avg_spend = avg_monthly_spend.sum()

    baseline = {
        "avg_monthly_spend_needs": f"{avg_monthly_spend.get('Needs', 0):,.2f}",
        "avg_monthly_spend_wants": f"{avg_monthly_spend.get('Wants', 0):,.2f}",
        "avg_monthly_spend_other": f"{avg_monthly_spend.get('Other', 0):,.2f}",
        "total_avg_monthly_spend": f"{total_avg_spend:,.2f}"
    }

    print("Pandas Budget Baseline Complete.")
    return baseline

def generate_budget_plan_with_llm(baseline: dict, profile: str) -> str:
    """
    Uses an LLM to generate a personalized budget proposal and financial tip.
    """
    print("Executing Budget Planner Node (LLM)...")
    
    prompt = f"""
    You are a friendly and practical financial advisor AI. Your goal is to create a simple, personalized monthly budget for a user based on their past spending and inferred profile.

    Here is the user's financial profile summary from Phase 1:
    ---
    {profile}
    ---

    Here is a summary of their average monthly spending from Phase 3:
    ---
    - Average Monthly Spending on NEEDS (essentials like groceries, bills): ₹{baseline['avg_monthly_spend_needs']}
    - Average Monthly Spending on WANTS (discretionary like shopping, dining): ₹{baseline['avg_monthly_spend_wants']}
    - Average Monthly Spending on OTHER categories: ₹{baseline['avg_monthly_spend_other']}
    - TOTAL Average Monthly Spend: ₹{baseline['total_avg_monthly_spend']}
    ---

    Based on all this information, create a "Proposed Monthly Budget" section.
    1.  **Budget Proposal:** Suggest a simple budget based on the 50/30/20 rule (50% Needs, 30% Wants, 20% Savings), but **adjust it realistically** based on the user's actual spending. Present this as a clear, simple table with categories (Needs, Wants, Savings), proposed percentages, and the corresponding amounts in Rupees.
    2.  **Personalized Financial Tip:** Based on their profile and spending, provide **one actionable and encouraging tip**. For example, if they spend a lot on dining out, suggest a "no-spend weekend" or packing lunch.

    Keep the tone helpful and non-judgmental. Start the response with a heading "Proposed Monthly Budget".
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a friendly and practical financial advisor AI."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=500
        )
        summary = response.choices[0].message.content
        print("LLM Budget Plan Complete.")
        return summary
    except Exception as e:
        return f"An error occurred with the OpenAI API during budget planning: {e}"