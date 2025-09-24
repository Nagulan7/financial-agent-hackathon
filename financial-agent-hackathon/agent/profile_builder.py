import pandas as pd
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_transactions_with_pandas(df: pd.DataFrame) -> dict:
    """
    Performs quantitative analysis (top categories/merchants) for a single user's DataFrame.
    """
    print("Executing Pandas Analysis for User...")
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    
    # **CRITICAL FIX**: This line is now robust. It handles "debit", "Debit", " DEBIT ", etc.
    debit_transactions = df[df['direction'].str.strip().str.lower() == 'debit'].copy()

    # If a user has no spending, we return a specific message.
    if debit_transactions.empty:
        return {"summary": "This user has no spending (debit) transactions to analyze."}

    # Calculate spending by category (for charts)
    category_spending = debit_transactions.groupby('category')['amount'].sum().to_dict()
    top_categories = debit_transactions.groupby('category')['amount'].sum().nlargest(5).to_string()
    top_merchants = debit_transactions['merchant_name'].value_counts().nlargest(5).to_string()
    total_debit = debit_transactions['amount'].sum()
    
    # Additional metrics for Streamlit
    total_transactions = len(debit_transactions)
    avg_transaction_amount = debit_transactions['amount'].mean()
    unique_merchants = debit_transactions['merchant_name'].nunique()
    
    analysis = {
        "top_spending_categories": top_categories,
        "top_merchants_by_frequency": top_merchants,
        "total_debit": f"{total_debit:,.2f}",
        "transaction_samples": df.sample(n=min(10, len(df)), random_state=42).to_string(),
        # Additional structured data for Streamlit
        "category_spending": category_spending,
        "total_spending": total_debit,
        "total_transactions": total_transactions,
        "average_transaction_amount": avg_transaction_amount,
        "unique_merchants": unique_merchants
    }
    return analysis

def generate_profile_from_analysis(analysis: dict) -> str:
    """
    Uses an LLM to generate the qualitative profile from a user's pre-analyzed data.
    """
    if "summary" in analysis:
        return analysis["summary"]

    print("Executing LLM Profile Generation for User...")
    prompt = f"""
    You are a financial analyst AI. Based on the following summary of a user's spending, create a concise financial profile.

    **Data Summary:**
    - Total Money Spent: ₹{analysis['total_debit']}
    - Top Spending Categories by Amount:
    {analysis['top_spending_categories']}
    - Top Merchants by Transaction Frequency:
    {analysis['top_merchants_by_frequency']}

    **Your Task:**
    Based ONLY on the data provided, write a brief summary covering:
    1.  **Spending Habits:** A one-paragraph summary of the user's main spending patterns.
    2.  **Potential Fixed Obligations:** Identify any merchants from the list that look like recurring bills or subscriptions (e.g., rent, utilities, streaming services).
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a financial analyst AI who creates concise user profiles."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred with the OpenAI API: {e}"