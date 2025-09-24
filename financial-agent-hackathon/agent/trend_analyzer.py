import pandas as pd
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_trends_with_pandas(df: pd.DataFrame) -> dict:
    """
    Performs quantitative, time-series analysis on transaction data using pandas.
    """
    print("Executing Pandas Trend Analysis...")
    
    # --- Data Preparation ---
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['month'] = df['timestamp'].dt.to_period('M')
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    
    debit_df = df[df['direction'].str.strip().str.lower() == 'debit'].copy()
    
    # Identify the last two full months in the data
    months = sorted(debit_df['month'].unique())
    if len(months) < 2:
        return {"summary": "Not enough data for a month-on-month comparison."}
    
    last_month_period = months[-1]
    prev_month_period = months[-2]

    # --- Analysis ---
    last_month_data = debit_df[debit_df['month'] == last_month_period]
    prev_month_data = debit_df[debit_df['month'] == prev_month_period]

    # 1. MoM Total Spending
    last_month_total = last_month_data['amount'].sum()
    prev_month_total = prev_month_data['amount'].sum()
    total_spend_change_pct = ((last_month_total - prev_month_total) / prev_month_total) * 100 if prev_month_total > 0 else 0

    # 2. MoM Spending by Top Categories
    last_month_categories = last_month_data.groupby('category')['amount'].sum()
    prev_month_categories = prev_month_data.groupby('category')['amount'].sum()
    category_comparison = pd.DataFrame({'last_month': last_month_categories, 'prev_month': prev_month_categories}).fillna(0)
    category_comparison['change'] = category_comparison['last_month'] - category_comparison['prev_month']
    top_increases = category_comparison['change'].nlargest(3).to_string()
    
    # 3. Burst Detection (Anomaly)
    avg_spend = debit_df['amount'].mean()
    std_dev = debit_df['amount'].std()
    burst_threshold = avg_spend + 3 * std_dev
    burst_transactions = last_month_data[last_month_data['amount'] > burst_threshold]

    analysis = {
        "last_month_name": last_month_period.strftime('%B %Y'),
        "prev_month_name": prev_month_period.strftime('%B %Y'),
        "total_spend_change_pct": f"{total_spend_change_pct:.2f}%",
        "top_category_increases": top_increases,
        "burst_transactions_report": "No significant burst spending detected." if burst_transactions.empty else burst_transactions[['timestamp', 'merchant_name', 'amount']].to_string()
    }
    return analysis

def summarize_trends_with_llm(analysis: dict) -> str:
    """
    Uses an LLM to generate a qualitative summary of financial trends.
    """
    if "summary" in analysis:
        return analysis["summary"]

    print("Executing LLM Trend Summary...")
    prompt = f"""
    You are a financial analyst AI. Create a concise, human-readable summary of a user's spending trends based on pre-calculated data.

    Here is the trend analysis comparing {analysis['last_month_name']} with {analysis['prev_month_name']}:
    ---
    - Overall Spending Change: {analysis['total_spend_change_pct']}
    - Top 3 Spending Increases by Category (Amount Change in Rupees):
    {analysis['top_category_increases']}
    - Report on Unusually Large Transactions this month:
    {analysis['burst_transactions_report']}
    ---
    Based ONLY on this data, write a brief "Spending Trends" summary.
    - Start with the overall spending change.
    - Highlight the most significant category increase.
    - Mention any noteworthy large transactions.
    - Keep the tone helpful and informative.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a financial analyst AI who summarizes spending trends."},
                      {"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"An error occurred with the OpenAI API during trend summarization: {e}"