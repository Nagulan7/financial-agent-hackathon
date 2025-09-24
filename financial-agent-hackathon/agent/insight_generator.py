def generate_final_report(profile_summary: str, trend_summary: str, budget_summary: str) -> str:
    """
    Combines the summaries from all three phases into a single, cohesive report.
    """
    print("Executing Final Report Generation Node...")
    
    final_report = f"""
# Your Personalized UPI Financial & Budgeting Report

## 1. Your Financial Profile
{profile_summary}

---

## 2. Recent Spending Trends
{trend_summary}

---

## 3. Your Personalized Budget Plan
{budget_summary}

---

*This report was automatically generated based on your transaction data. This is not financial advice. Please review for accuracy.*
    """
    print("Final report compiled.")
    return final_report.strip()