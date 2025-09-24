import pandas as pd
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def create_budget_baseline_with_pandas(df: pd.DataFrame) -> dict:
    """
    Analyzes historical data to create a baseline of average monthly spending.
    """
    print("Executing Pandas Budget Baseline...")
    
    # --- Data Preparation ---
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['month'] = df['timestamp'].dt.to_period('M')
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    
    debit_df = df[df['direction'].str.strip().str.lower() == 'debit'].copy()

    if debit_df.empty:
        return {"summary": "No spending data available to create a budget baseline."}
    
    # --- Categorization Mapping (Needs vs. Wants) ---
    def map_category(cat):
        cat = str(cat).lower()
        if any(c in cat for c in ['groceries', 'utilities', 'rent', 'transport', 'bills', 'emi', 'health']):
            return 'Needs'
        elif any(c in cat for c in ['shopping', 'food', 'travel', 'entertainment', 'recharge', 'lifestyle', 'subscription']):
            return 'Wants'
        else:
            return 'Other'
            
    debit_df['budget_category'] = debit_df['category'].apply(map_category)
    
    # --- Analysis ---
    monthly_spend = debit_df.groupby(['month', 'budget_category'])['amount'].sum().unstack(fill_value=0)
    avg_monthly_spend = monthly_spend.mean()
    total_avg_spend = avg_monthly_spend.sum()

    baseline = {
        "avg_monthly_spend_needs": f"{avg_monthly_spend.get('Needs', 0):,.2f}",
        "avg_monthly_spend_wants": f"{avg_monthly_spend.get('Wants', 0):,.2f}",
        "total_avg_monthly_spend": f"{total_avg_spend:,.2f}"
    }
    return baseline

def generate_budget_plan_with_llm(baseline: dict, profile: str) -> str:
    """
    Uses an LLM to generate a personalized budget proposal and financial tip.
    """
    if "summary" in baseline:
        return baseline["summary"]

    print("Executing LLM Budget Plan...")
    prompt = f"""
    You are a friendly financial advisor AI. Create a simple, personalized monthly budget for a user based on their past spending and profile.

    **User Profile Summary:**
    {profile}

    **User's Average Monthly Spending:**
    - Average on NEEDS (essentials): ₹{baseline['avg_monthly_spend_needs']}
    - Average on WANTS (discretionary): ₹{baseline['avg_monthly_spend_wants']}
    - Total Average Monthly Spend: ₹{baseline['total_avg_monthly_spend']}

    **Your Task:**
    Create a "Proposed Monthly Budget" section.
    1.  **Budget Proposal:** Suggest a simple budget based on the 50/30/20 rule (50% Needs, 30% Wants, 20% Savings), but **adjust it realistically** based on the user's actual spending. Present this as a clear table with categories (Needs, Wants, Savings), proposed percentages, and the corresponding Rupee amounts.
    2.  **Personalized Tip:** Provide **one actionable and encouraging financial tip** based on their profile and spending.

    Keep the tone helpful and non-judgmental. Start the response with a heading "### Proposed Monthly Budget".
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
        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred with the OpenAI API during budget planning: {e}"