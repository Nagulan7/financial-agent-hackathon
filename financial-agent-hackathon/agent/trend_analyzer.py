import pandas as pd
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_trends_with_pandas(df: pd.DataFrame) -> dict:
    """
    Performs quantitative, time-series analysis on transaction data using pandas.
    Compares the last two full months of data.
    """
    print("Executing Pandas Trend Analysis Node...")
    
    # --- Data Preparation ---
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['month'] = df['timestamp'].dt.to_period('M')
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0)
    
    debit_df = df[df['direction'] == 'debit'].copy()
    
    # Identify the last two full months in the data
    months = sorted(debit_df['month'].unique())
    if len(months) < 2:
        print("Not enough monthly data to perform trend analysis.")
        return {"trend_summary": "Not enough data for a month-on-month comparison."}
    
    last_month_period = months[-1]
    prev_month_period = months[-2]

    # --- Analysis ---
    last_month_data = debit_df[debit_df['month'] == last_month_period]
    prev_month_data = debit_df[debit_df['month'] == prev_month_period]

    # 1. Month-over-Month (MoM) Total Spending
    last_month_total = last_month_data['amount'].sum()
    prev_month_total = prev_month_data['amount'].sum()
    
    total_spend_change_pct = ((last_month_total - prev_month_total) / prev_month_total) * 100 if prev_month_total > 0 else 0

    # 2. MoM Spending by Top Categories
    last_month_categories = last_month_data.groupby('category')['amount'].sum()
    prev_month_categories = prev_month_data.groupby('category')['amount'].sum()
    
    category_comparison = pd.DataFrame({
        'last_month': last_month_categories,
        'prev_month': prev_month_categories
    }).fillna(0)
    
    category_comparison['change'] = category_comparison['last_month'] - category_comparison['prev_month']
    
    # Get top 3 increases and decreases
    top_increases = category_comparison['change'].nlargest(3).to_string()
    top_decreases = category_comparison['change'].nsmallest(3).to_string()

    # 3. Burst Detection (Anomaly)
    # An anomaly is a transaction significantly larger than the monthly average
    avg_spend = debit_df['amount'].mean()
    std_dev = debit_df['amount'].std()
    burst_threshold = avg_spend + 3 * std_dev # Anything 3 standard deviations above average
    
    burst_transactions = last_month_data[last_month_data['amount'] > burst_threshold]

    analysis = {
        "last_month_name": last_month_period.strftime('%B %Y'),
        "prev_month_name": prev_month_period.strftime('%B %Y'),
        "total_spend_change_pct": f"{total_spend_change_pct:.2f}%",
        "top_category_increases": top_increases,
        "top_category_decreases": top_decreases,
        "burst_transactions_report": "No significant burst spending detected." if burst_transactions.empty else burst_transactions[['timestamp', 'merchant_name', 'amount']].to_string()
    }

    print("Pandas Trend Analysis Complete.")
    return analysis

def summarize_trends_with_llm(analysis: dict) -> str:
    """
    Uses an LLM to generate a qualitative summary of financial trends.
    """
    if "trend_summary" in analysis: # Handle case with not enough data
        return analysis["trend_summary"]

    print("Executing Trend Summarizer Node (LLM)...")
    
    prompt = f"""
    You are a financial analyst AI. Your task is to create a concise, human-readable summary of a user's spending trends based on pre-calculated data. The user wants to know what has changed in their spending recently.

    Here is the trend analysis comparing {analysis['last_month_name']} with {analysis['prev_month_name']}:
    ---
    - Overall Spending Change: {analysis['total_spend_change_pct']}
    
    - Top 3 Spending Increases by Category (Amount Change):
    {analysis['top_category_increases']}

    - Top 3 Spending Decreases by Category (Amount Change):
    {analysis['top_category_decreases']}

    - Report on Unusually Large Transactions (Burst Spending) this month:
    {analysis['burst_transactions_report']}
    ---

    Based ONLY on this data, write a brief "Spending Trends" section for a financial report.
    - Start with the overall spending change.
    - Highlight the most significant category changes (both increases and decreases).
    - Mention any noteworthy large transactions.
    - Keep the tone helpful and informative. Do not give financial advice.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a financial analyst AI who summarizes spending trends."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=400
        )
        summary = response.choices[0].message.content
        print("LLM Trend Summary Complete.")
        return summary
    except Exception as e:
        return f"An error occurred with the OpenAI API during trend summarization: {e}"