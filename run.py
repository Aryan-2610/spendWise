import json
import os
from crewai import Crew, Process
from agents_and_tasks import (
    get_categorizer_agent, get_analyst_agent, get_advisor_agent,
    get_categorize_task, get_analyze_task, get_advice_task
)

# Hardcoded categories as requested
CATEGORIES = [
    "Groceries", "Food & Drinks", "Snacks", "Household Supplies",
    "Toiletries & Personal Care", "Electronics", "Medical & Pharmacy",
    "Clothing & Apparel", "Other"
]

def run_collaborative_workflow():
    # Load your receipt data
    with open("outputs/expenses.json", "r") as f:
        all_receipts = json.load(f)

    # Initialize Agents
    categorizer = get_categorizer_agent()
    analyst = get_analyst_agent()
    advisor = get_advisor_agent()

    # Define Tasks
    task_cat = get_categorize_task(categorizer, all_receipts)
    task_ana = get_analyze_task(analyst, all_receipts, {})
    task_adv = get_advice_task(advisor, {})

    # Collaborative Crew
    expense_crew = Crew(
        agents=[categorizer, analyst, advisor],
        tasks=[task_cat, task_ana, task_adv],
        process=Process.sequential, 
        verbose=True
    )

    result = expense_crew.kickoff()
    print(f"✅ Workflow complete: {result}")

if __name__ == "__main__":
    run_collaborative_workflow()