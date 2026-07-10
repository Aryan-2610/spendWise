import os
import json
import util
from dotenv import load_dotenv
from crewai import Agent, Task, LLM

load_dotenv()

# Initialize llm
llm = LLM(
    model="gemini/gemini-2.5-flash",
    api_key=os.environ.get("GEMINI_API_KEY")
)

# Simple list of spending categories
CATEGORIES = [
    "Groceries",
    "Food & Drinks",
    "Snacks",
    "Transportation",
    "Housing & Utilities",
    "Clothing & Apparel",
    "Electronics & Tech",
    "Medical & Healthcare",
    "Entertainment",
    "Education",
    "Other"
]
# AGENTS 

def categorizer_agent():
  ##categroize the items in each reciept
    return Agent(
        role="Expense Categorization Expert",
        goal="Accurately categorize purchased items into appropriate spending categories",
        backstory="""You are an expert at analyzing shopping receipts and categorizing expenses.
        You understand context and always return valid structured JSON.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

def analyst_agent():
   ##identify spending pattern
    return Agent(
        role="Spending Pattern Analyst",
        goal="Identify spending trends and habits from expense data",
        backstory="""You are a smart financial analyst who finds patterns in spending data.
        You always return structured JSON with helpful insights.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

def advisor_agent():
    #give practical advice
    return Agent(
        role="Personal Finance Advisor",
        goal="Provide practical budgeting advice and actionable tips for college students",
        backstory="""You are a friendly personal finance mentor specializing in college student budgeting.
        You give practical, realistic tips to save money. Return valid JSON.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

def chatter_agent():
    #interactive financial chatter and coach based on audit and human feedback
    return Agent(
        role="Interactive Financial Coach & Chatter",
        goal="Engage in conversational budgeting dialogue based on user feedback and multi-agent audit data",
        backstory="""You are the front-facing conversational coach of the SpendWise AI Crew.
        You take the analytical breakdowns from the Spending Pattern Analyst and the tactical tips
        from the Personal Finance Advisor, tailoring them dynamically to live human feedback and advice. Keep responses short, practical, and formatted cleanly in bullet points.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

# TASKS
def create_categorization_task(agent, items):
    """Task to categorize a batch of receipt items."""
    items_list = "" ##empty string
    for item in items:
        ##append to the item list a new line in which unique key ,store,desc,amount is there as a string to send to llm
        items_list += f"- ID: {item['unique_key']} | Store: {item['merchant']} | Item: '{item['description']}' | Cost: {util.symbol}{item['amount']}\n"

    categories_str = ", ".join(CATEGORIES) ## all the categories join it

    prompt = f"""
    Classify each of the following receipt line items into appropriate spending categories based on description and store name.
    {items_list}

    Choose ONE category for each item ID from this exact list:
    {categories_str}

    IMPORTANT INSTRUCTIONS:
    1. Do NOT default everything to Groceries. Accurately distinguish restaurants/coffee (Food & Drinks), snacks (Snacks), clothes (Clothing & Apparel), rides/fuel (Transportation), gadgets (Electronics & Tech), etc.
    2. You MUST include every single item ID listed above in your output dictionary. Do not omit any ID.

    Return ONLY a valid JSON dictionary mapping each item ID to a dictionary with the category:
    {{
      "r1_i1": {{
        "category": "Groceries"
      }}
    }}
    """

    return Task(
        description=prompt,
        agent=agent,
        expected_output="JSON dictionary mapping item IDs to spending categories."
    )

def create_analysis_task(agent, summary):
    """Task to analyze spending trends."""
    prompt = f"""
    Review this spending summary:
    Total Spent: {util.symbol}{summary['overall_total']:.2f}
    
    Spending by Category:
    {json.dumps(summary['category_totals'], indent=2)}

    Number of Items by Category:
    {json.dumps(summary['item_counts'], indent=2)}

    Generate 3 to 4 helpful analytical observations about where the money goes and general spending habits.

    Return ONLY a JSON dictionary:
    {{
      "insights": [
        "First observation about spending concentration.",
        "Second observation about spending frequency.",
        "Third observation evaluating top expenses."
      ]
    }}
    """

    return Task(
        description=prompt,
        agent=agent,
        expected_output="JSON object containing financial insights."
    )

def create_advisory_task(agent, summary, insights):
    """Task to give budgeting advice to the student."""
    prompt = f"""
    Review the student's spending data:
    Total Spent: {util.symbol}{summary['overall_total']:.2f}
    Spending by Category: {json.dumps(summary['category_totals'])}

    Analysis Insights:
    {json.dumps(insights)}

    Provide friendly, actionable personal finance recommendations tailored for a college student.
    Return ONLY a JSON object:
    {{
      "analysis": {{
        "total_spent": {summary['overall_total']},
        "by_category": {json.dumps(summary['category_totals'])},
        "category_counts": {json.dumps(summary['item_counts'])},
        "insights": {json.dumps(insights)}
      }},
      "advice": {{
        "budget_status": "Healthy / Needs Adjustment",
        "tips": [
          "First practical tip to save money.",
          "Second helpful budgeting suggestion."
        ],
        "quick_win": "One easy action you can take right now.",
        "positive_note": "Encouraging closing message."
      }}
    }}
    """

    return Task(
        description=prompt,
        agent=agent,
        expected_output="Complete financial health report in JSON format."
    )

def create_chat_task(agent, user_prompt, chat_history, financial_context):
    """Task for the chatter agent to converse based on human feedback and audit advice."""
    history_str = ""
    for msg in chat_history[:-1]:
        role_name = "User" if msg["role"] == "user" else "SpendWise AI Coach"
        history_str += f"{role_name}: {msg['content']}\n\n"

    prompt = f"""
    Review the user's audited financial spending report, analysis insights from the Analyst agent, and tips from the Advisor agent:
    {financial_context}

    Ongoing Conversation & Human Feedback:
    {history_str}

    Latest User Input / Question:
    {user_prompt}

    As the SpendWise AI Interactive Chatter, synthesize the Analyst and Advisor agent data to answer the user's question.
    CRITICAL INSTRUCTIONS:
    1. STRICT DOMAIN BOUNDARY: Strictly answer questions related to personal finance, budgeting, household cost-cutting, expense auditing, and financial literacy. If unrelated, politely state you only advise on financial matters.
    2. SHORT & CONCISE: Provide 3-4 punchy bullet points maximum (1-2 sentences per point).
    3. PRACTICAL & TAILORED: Give specific, realistic advice based on the user's human feedback and exact audit numbers.
    4. NO EMOJIS: Keep formatting clean and professional.

    Return ONLY your direct text response to the user.
    """

    return Task(
        description=prompt,
        agent=agent,
        expected_output="Concise, actionable bullet-point advice tailored to human feedback and audit data."
    )