import json
import os
import util

FINAL_REPORT_FILE = "outputs/crew_analysis.json"
ITEMIZED_RECEIPTS_FILE = "outputs/categorized_receipts.json"

def show_dashboard():
    if not os.path.exists(FINAL_REPORT_FILE):
        print(f"Report not found at '{FINAL_REPORT_FILE}'. Please run `python run.py` first.")
        return

    with open(FINAL_REPORT_FILE, "r", encoding="utf-8") as file_ptr:
        payload = json.load(file_ptr)

    analysis = payload.get("analysis", {})
    advice = payload.get("advice", {})

    print("\n" + "=" * 68)
    print(" SMART SPENDING DASHBOARD — ITEM-WISE & VERIFIED AUDIT")
    print("=" * 68)

    curr_sym = util.symbol
    total_expenditure = float(analysis.get("total_spent", 0.0))
    print(f"\n💰 Total Verified Expenditure: {curr_sym}{total_expenditure:,.2f}")

    counts = analysis.get("category_counts", analysis.get("item_counts", {}))
    total_items = sum(counts.values()) if counts else 0
    if total_items > 0:
        print(f" Total Retail Line Items Audited & Classified: {total_items}")

    print("\nEXPENDITURE BREAKDOWN BY RETAIL ITEM CATEGORY:")
    categories = analysis.get("by_category", {})
    sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)

    for cat_name, amount in sorted_categories:
        pct = (amount / total_expenditure * 100) if total_expenditure > 0 else 0.0
        cnt = counts.get(cat_name, "")
        cnt_str = f"({cnt} line items)" if cnt else ""
        print(f"   • {cat_name:<30} {curr_sym}{amount:>10,.2f}  ({pct:>5.1f}%)  {cnt_str}")

    print("\n SENIOR AUDITOR SPENDING OBSERVATIONS:")
    for insight in analysis.get("insights", []):
        print(f"   🔹 {insight}")

    print("\n🎓 STUDENT FINANCIAL COACHING & ADVICE:")
    print(f"   ⚡ Health Status: {advice.get('budget_status', 'Stable')}")
    
    print("    Personalized Actionable Strategies:")
    for tip in advice.get("tips", []):
        print(f"      - {tip}")

    print(f"\n   Quick Win Action: {advice.get('quick_win', 'Audit top spending categories.')}")
    print(f"    Note: {advice.get('positive_note', 'Great job tracking your budget!')}\n")
    print("=" * 68 + "\n")

if __name__ == "__main__":
    show_dashboard()