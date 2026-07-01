import json
import os

##save report at
FINAL_REPORT_FILE = "outputs/crew_analysis.json"

def show_dashboard():
    # Make sure the file exists first
    if not os.path.exists(FINAL_REPORT_FILE):
        print("Report not found")
        return

    # Load the data
    with open(FINAL_REPORT_FILE, "r") as file:##open in read mode
        data = json.load(file)

    # Extract the parts we need (using .get() prevents errors if keys are missing)
    ##check analsysis,advice in crew_analsysi.json for already present
    analysis = data.get("analysis", {})
    advice = data.get("advice", {})

   
    print("  YOUR SMART SPENDING REPORT")
    

    # Total Spent
    total = analysis.get("total_spent", 0)
    print(f" total spent: ₹{total:.2f}")

    # Categories Breakdown
    print("\ncategory breakdown:")
    categories = analysis.get("by_category", {})
    
    # Sort categories so the highest spending is at the top
    sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)
    
    for category_name, amount in sorted_categories:
        # Calculate percentage (prevent dividing by zero)
        if total > 0:
            percentage = (amount / total) * 100
        else:
            percentage = 0
            
       #alignment
        print(f"   • {category_name:<25} ₹{amount:>8.2f}  ({percentage:.1f}%)")

    # Insights
    print(" AI INSIGHTS:")
    for insight in analysis.get("insights", []):
        print(f"   {insight}")

    # Advice
    print("\nCOACHING & ADVICE:")
    print(f"   Status: {advice.get('budget_status', 'Unknown')}")
    
    print("   Tips:")
    for tip in advice.get("tips", []):
        print(f"   - {tip}")

    print(f"\nQuick Action: {advice.get('quick_win', 'None')}")
    print(f"Note: {advice.get('positive_note', 'Keep it up!')}\n")

if __name__ == "__main__":
    show_dashboard()