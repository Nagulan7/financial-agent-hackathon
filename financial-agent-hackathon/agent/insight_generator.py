def generate_final_report(profile: str, trends: str, budget: str) -> str:
    """
    The Insight Generator agent.
    It takes all the individual summaries and assembles them into a single,
    cohesive, and well-formatted final report.
    """
    print("Executing Insight Generator (Phase 4)...")
    
    report = f"""
# Personalized UPI Financial & Budgeting Report

## 1. Your Financial Profile
{profile}

---

## 2. Recent Spending Trends
{trends}

---

## 3. Your Personalized Budget Plan
{budget}

---
*This report was automatically generated based on your transaction data. This is not financial advice. Please review for accuracy.*
    """
    
    print("Final report compiled successfully.")
    return report.strip()