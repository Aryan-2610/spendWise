import json
import os
from crewai import Crew, Process

# Fixed import to match exact filename casing
from agents_And_tasks import (
    get_categorizer_agent, get_analyst_agent, get_advisor_agent,
    get_categorize_task, get_analyze_task, get_advice_task
)

def run_collaborative_workflow():
    # Load your receipt data
    if not os.path.exists("outputs/expenses.json"):
        print("No expenses found. Run scan-reciepts-hf.py first.")
        return
        
    with open("outputs/expenses.json", "r") as f:
        all_receipts = json.load(f)

    # Initialize Agents
    categorizer = get_categorizer_agent()
    analyst = get_analyst_agent()
    advisor = get_advisor_agent()

    # Define Tasks (CrewAI will automatically pass context between sequential tasks)
    task_cat = get_categorize_task(categorizer, all_receipts)
    task_ana = get_analyze_task(analyst, all_receipts)
    task_adv = get_advice_task(advisor)

    # Collaborative Crew
    expense_crew = Crew(
        agents=[categorizer, analyst, advisor],
        tasks=[task_cat, task_ana, task_adv],
        process=Process.sequential, 
        verbose=True
    )

    result = expense_crew.kickoff()
    
    # Clean markdown backticks if the LLM forced them
    final_output = str(result)
    if final_output.startswith("```json"):
        final_output = final_output[7:]
    elif final_output.startswith("```"):
        final_output = final_output[3:]
        
    if final_output.endswith("```"):
        final_output = final_output[:-3]
        
    final_output = final_output.strip()
    
    # Save the output for analysis.py
    os.makedirs("outputs", exist_ok=True)
    with open("outputs/crew_analysis.json", "w") as f:
        f.write(final_output)

    print(f"✅ Workflow complete! Report saved.")

if __name__ == "__main__":
    run_collaborative_workflow()