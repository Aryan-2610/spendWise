import os
import json
from dotenv import load_dotenv
from crewai import Agent, Task, LLM

load_dotenv()

if not os.environ.get("GEMINI_API_KEY"):
    print("Error: GEMINI_API_KEY not found in .env file!")
    exit()

#setup gemini
gemini_model = LLM(
    model="gemini/gemini-1.5-flash",
    api_key=os.environ.get("GEMINI_API_KEY")
)

#category list (9+others)
VALID_CATEGORIES = [
    "Groceries", "Food & Drinks", "Snacks", "Household Supplies",
    "Toiletries & Personal Care", "Electronics", "Medical & Pharmacy",
    "Clothing & Apparel", "Other"
]

#ai agents

def get_categorizer_agent():
    """This AI looks at receipts and sorts them into categories."""
    return Agent(
        role="Categorizer",
        ##objective
        goal="Sort expenses into correct categories.",
        ##kind of system prompt
        backstory="You are an organized assistant who sorts receipts. You must output ONLY a valid JSON object. No other text, no markdown backticks, no explanations.",
        llm=gemini_model,
        ##display o/p or reasoning
        verbose=True,
        ##as delegation is false cant pass of its task to someone else ,do and give
        allow_delegation=False 
    )

def get_analyst_agent():
    """This AI looks at the numbers and finds spending trends."""
    return Agent(
        role="Financial Analyst",
        goal="Find patterns in spending data.",
        backstory="You are a numbers expert who finds spending trends. You must output ONLY a valid JSON object. No other text, no markdown backticks, no explanations.",
        llm=gemini_model,
        verbose=True,
        allow_delegation=False
    )

def get_advisor_agent():
    """This AI gives helpful tips based on the analysis."""
    return Agent(
        role="Budget Advisor",
        goal="Give helpful, easy-to-follow budgeting tips for students.",
        backstory="You are a friendly financial coach for college students. You must output ONLY a valid JSON object. No other text, no markdown backticks, no explanations.",
        llm=gemini_model,
        verbose=True,
        allow_delegation=False
    )

#defining various tasks

##needs the agent which does task , input as arg
def get_categorize_task(agent, new_receipts):
    """Task for the Categorizer to sort new receipts."""
    
    # Create a simple text list of the receipts for the AI to read
    receipt_text = ""
    for receipt in new_receipts:## loop on all
        receipt_text += f"- File: {receipt['image_file']}, Store: {receipt['merchant']}, Amount: ₹{receipt['total']}\n"
    
    prompt = f"""
    Look at these receipts:
    {receipt_text} ## basically contain data of all reciepts
    
    Pick ONE category for each receipt from this list: {', '.join(VALID_CATEGORIES)}
    
    Return ONLY a JSON dictionary in the following format (no extra text):
    {{
      "receipt_name.jpg": {{
        "category": "Groceries",
        "reason": "Because they bought food."
      }}
    }}
    """
    
    return Task(
        description=prompt,
        agent=agent,
        expected_output="A JSON object with the categorized receipts."
    )

def get_analyze_task(agent, all_receipts, categorizations):
    """Task for the Analyst to crunch the numbers."""
    
    total_spent = 0
    category_totals = {}
    
    # Calculate the total spent per category and total (manually do maths in function)
    for receipt in all_receipts:
        image_name = receipt['image_file']
        
        # Look up the category we assigned earlier (default to 'Other' if not found)
        assigned_category = categorizations.get(image_name, {}).get('category', 'Other')
        
        # Get the amount spent (default to 0 if it's missing)
        amount = receipt.get('total', 0) 
        if amount is None: amount = 0
            
        # Add the amount to our running totals
        total_spent += amount
        
        if assigned_category in category_totals:
            category_totals[assigned_category] += amount
        else:
            category_totals[assigned_category] = amount

    prompt = f"""
    Analyze this spending data:
    Total Spent: ₹{total_spent}
    Breakdown: {json.dumps(category_totals)}
    
    Return ONLY a JSON dictionary in the following format (no extra text):
    {{
      "total_spent": {total_spent},
      "by_category": {json.dumps(category_totals)},
      "insights": ["Insight 1", "Insight 2"]
    }}
    """
    
    return Task(
        description=prompt,
        agent=agent,
        expected_output="A JSON object with spending insights."
    )

def get_advice_task(agent, analysis_data):
    """Task for the Advisor to give tips based on the analysis."""
    
    prompt = f"""
    Based on this spending analysis:
    {json.dumps(analysis_data)}
    
    Give practical advice for a student trying to save money.
    
    Return ONLY a JSON dictionary in the following format (no extra text):
    {{
      "budget_status": "Doing great / Needs work",
      "tips": ["Tip 1", "Tip 2"],
      "quick_win": "One thing they can do right now to save money",
      "positive_note": "A short encouraging sentence"
    }}
    """
    
    return Task(
        description=prompt,
        agent=agent,
        expected_output="A JSON object with friendly advice."
    )