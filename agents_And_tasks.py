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
    model="gemini/gemini-2.5-flash",
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

def get_analyze_task(agent, all_receipts):
    """Task for the Analyst to crunch the numbers."""
    
    # Just pass the amounts so the LLM can do the math itself using the categories from the previous task
    receipt_text = ""
    for receipt in all_receipts:
        receipt_text += f"- File: {receipt['image_file']}, Amount: ₹{receipt['total']}\n"

    prompt = f"""
    You will receive a JSON object of categorized receipts from the previous Categorizer task.
    Match them with these receipt amounts:
    {receipt_text}
    
    Calculate the exact total spent overall, and the total spent per category.
    
    Return ONLY a JSON dictionary in the following format (no extra text):
    {{
      "total_spent": 100.50,
      "by_category": {{"Groceries": 50.00, "Other": 50.50}},
      "insights": ["Insight 1", "Insight 2"]
    }}
    """
    
    return Task(
        description=prompt,
        agent=agent,
        expected_output="A JSON object with spending insights."
    )

def get_advice_task(agent):
    """Task for the Advisor to give tips based on the analysis."""
    
    prompt = f"""
    You will receive a spending analysis JSON from the previous Financial Analyst task.
    Based on that analysis, give practical advice for a student trying to save money.
    
    Combine the analysis data you received with your new advice into a single JSON response.
    
    Return ONLY a JSON dictionary in the exact following format (no extra text, no markdown backticks):
    {{
      "analysis": {{
        "total_spent": 0,
        "by_category": {{}},
        "insights": []
      }},
      "advice": {{
        "budget_status": "Doing great / Needs work",
        "tips": ["Tip 1", "Tip 2"],
        "quick_win": "One thing they can do right now to save money",
        "positive_note": "A short encouraging sentence"
      }}
    }}
    """
    
    return Task(
        description=prompt,
        agent=agent,
        expected_output="A single JSON object combining analysis and friendly advice."
    )