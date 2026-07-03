import os
import json
from dotenv import load_dotenv
from crewai import Agent, Task, LLM

load_dotenv()

# Initialize primary language model
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

# Simple keyword lookup for quick category matching
SIMPLE_KEYWORDS = {
    "Groceries": ["carrot", "cucumber", "tomato", "oatmeal", "mozzarella", "cheese", "milk", "bread", "oil", "rice", "dal", "sugar", "salt", "grocery", "trader joe"],
    "Food & Drinks": ["coffee", "tea", "burger", "pizza", "noodle", "pasta", "biryani", "restaurant", "cafe", "fast food", "starbucks", "swiggy", "zomato"],
    "Transportation": ["fuel", "petrol", "uber", "ola", "taxi", "auto", "metro", "bus", "train", "flight", "parking"],
    "Housing & Utilities": ["rent", "electricity", "water", "gas", "wifi", "internet", "recharge", "mobile"],
    "Clothing & Apparel": ["shirt", "tshirt", "jeans", "dress", "shoes", "sneakers", "watch", "bag", "zara", "h&m"],
    "Electronics & Tech": ["laptop", "phone", "tablet", "computer", "software", "subscription", "charger", "earphone"],
    "Medical & Healthcare": ["pharmacy", "medicine", "pill", "hospital", "clinic", "gym", "soap", "shampoo"],
    "Entertainment": ["movie", "netflix", "prime", "spotify", "concert", "ticket", "gaming"],
    "Education": ["tuition", "school", "college", "book", "notebook", "pen", "course"]
}

def guess_category(description):
    """Simple helper to guess a category based on keywords."""
    text = str(description).lower()
    for category, keywords in SIMPLE_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return category
    return "Groceries"


# ==========================================
# AGENTS (Simple functions, no classes!)
# ==========================================

def categorizer_agent():
    """Agent that categorizes receipts and line items."""
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
    """Agent that finds spending patterns and insights."""
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
    """Agent that gives practical financial advice."""
    return Agent(
        role="Personal Finance Advisor",
        goal="Provide practical budgeting advice and actionable tips for college students",
        backstory="""You are a friendly personal finance mentor specializing in college student budgeting.
        You give practical, realistic tips to save money. Return valid JSON.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )


# ==========================================
# TASKS
# ==========================================

def create_categorization_task(agent, items):
    """Task to categorize a batch of receipt items."""
    items_list = ""
    for item in items:
        items_list += f"- ID: {item['unique_key']} | Store: {item['merchant']} | Item: '{item['description']}' | Cost: ₹{item['amount']}\n"

    categories_str = ", ".join(CATEGORIES)

    prompt = f"""
    Classify each of the following receipt line items into one category:
    {items_list}

    Choose ONE category for each item ID from this exact list:
    {categories_str}

    Return ONLY a valid JSON dictionary mapping each item ID to its assigned category:
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
    Total Spent: ₹{summary['overall_total']:.2f}
    
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
    Total Spent: ₹{summary['overall_total']:.2f}
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