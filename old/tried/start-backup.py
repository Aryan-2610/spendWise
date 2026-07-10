import json
import os
from crewai import Crew, Process

# Import our  functions from the agents file
from agents_and_tasks import (
    get_categorizer_agent, get_analyst_agent, get_advisor_agent,
    get_categorize_task, get_analyze_task, get_advice_task
)

RAW_EXPENSES_FILE = "outputs/expenses.json"
FINAL_REPORT_FILE = "outputs/crew_analysis.json"

##clean ai output json and use python dict
def extract_json_from_ai(ai_text):
    """AI sometimes wraps JSON in markdown blocks like ```json ... ```. This cleans it up."""
    text = str(ai_text).strip()
    
    # Remove markdown code blocks if they exist
    if text.startswith("```json"):
        text = text.replace("```json", "", 1)
    if text.startswith("```"):
        text = text.replace("```", "", 1)
    if text.endswith("```"):
        text = text[:-3]
        
    try:
        # Convert the cleaned string into a Python dictionary
        return json.loads(text.strip())
    except Exception as e:
        print("Failed to understand AI's JSON output.")
        return None

def run_expense_analysis():
    print("Loading data...")
    
    # Load all scanned receipts
    with open(RAW_EXPENSES_FILE, "r") as file:
        all_receipts = json.load(file)

    # Load previously analyzed data if it exists
    saved_categories = {}
    if os.path.exists(FINAL_REPORT_FILE):
        with open(FINAL_REPORT_FILE, "r") as file:
            old_data = json.load(file)
            saved_categories = old_data.get("categorization", {})

    # Figure out which receipts are new
    new_receipts = []
    for receipt in all_receipts:
        if receipt['image_file'] not in saved_categories:
            new_receipts.append(receipt)

    if len(new_receipts) == 0:
        print("No new receipts to analyze. Everything is up to date!")
        return

    print(f"Found {len(new_receipts)} new receipts.using Agents\n")
    
    #  Create our Agents
    categorizer = get_categorizer_agent()
    analyst = get_analyst_agent()
    advisor = get_advisor_agent()

    # 2. Run Categorization Task
    print("STEP 1: Categorizing new receipts...")
    cat_task = get_categorize_task(categorizer, new_receipts)
    crew1 = Crew(agents=[categorizer], tasks=[cat_task], process=Process.sequential, verbose=False)
    
    new_categories_raw = crew1.kickoff()
    new_categories = extract_json_from_ai(new_categories_raw) or {}
    
    # Combine old and new categories
    all_categories = {**saved_categories, **new_categories}

    # 3. Run Analysis Task
    print("STEP 2: Finding spending trends...")
    analysis_task = get_analyze_task(analyst, all_receipts, all_categories)
    crew2 = Crew(agents=[analyst], tasks=[analysis_task], process=Process.sequential, verbose=False)
    
    analysis_raw = crew2.kickoff()
    analysis_data = extract_json_from_ai(analysis_raw)
    
    # Fallback if AI fails
    if not analysis_data:
        analysis_data = {"total_spent": 0, "by_category": {}, "insights": ["Could not generate insights."]}

    # 4. Run Advice Task
    print("STEP 3: Getting budget advice...")
    advice_task = get_advice_task(advisor, analysis_data)
    crew3 = Crew(agents=[advisor], tasks=[advice_task], process=Process.sequential, verbose=False)
    
    advice_raw = crew3.kickoff()
    advice_data = extract_json_from_ai(advice_raw)
    
    # Fallback if AI fails
    if not advice_data:
         advice_data = {"tips": ["Track daily"], "quick_win": "Review expenses"}

    # 5. Save everything to a single file
    final_output = {
        "categorization": all_categories,
        "analysis": analysis_data,
        "advice": advice_data
    }

    with open(FINAL_REPORT_FILE, "w") as file:
        json.dump(final_output, file, indent=2)

    print("\n✅ AI Analysis Complete! Data saved to", FINAL_REPORT_FILE)

if __name__ == "__main__":
    run_expense_analysis()