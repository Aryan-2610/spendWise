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

#exhaustive category list with keyword hints so merchant names match confidently
CATEGORY_HINTS = {
    "Groceries & Quick Commerce": [
        "zepto", "swiggy instamart", "blinkit", "bigbasket", "supermarket", "grocery",
        "dairy", "vegetable", "fruit", "produce", "rice", "atta", "flour", "dal",
        "spice", "snack", "biscuit", "chips", "tea", "coffee", "cereal", "beverage"
    ],
    "Dining Out": [
        "restaurant", "cafe", "bistro", "diner", "fast food", "burger", "pizza",
        "mcdonalds", "kfc", "domino", "starbucks", "subway", "swiggy", "zomato",
        "bar", "pub", "dessert", "ice cream", "bakery", "dine"
    ],
    "Transportation": [
        "fuel", "petrol", "diesel", "uber", "ola", "rapido", "taxi", "auto",
        "transit", "metro", "bus", "train", "flight", "airline", "airways",
        "parking", "toll", "mechanic", "tyre", "tire"
    ],
    "Housing & Utilities": [
        "rent", "electricity", "power", "water", "gas", "lpg", "cylinder",
        "internet", "broadband", "wifi", "airtel", "jio", "vodafone", "recharge",
        "mobile", "phone", "maintenance", "utility", "bill"
    ],
    "Shopping & Apparel": [
        "clothing", "clothes", "shirt", "jeans", "dress", "shoes", "sneakers",
        "footwear", "accessories", "watch", "bag", "wallet", "boutique",
        "zara", "h&m", "myntra", "apparel", "fashion"
    ],
    "Electronics & Tech": [
        "electronics", "gadget", "laptop", "mobile device", "tablet", "computer",
        "software", "subscription", "cloud", "aws", "apple", "google storage",
        "cable", "charger", "headphone", "earphone", "monitor", "tech"
    ],
    "Health & Wellness": [
        "pharmacy", "medicine", "apollo", "medplus", "medical", "consultation",
        "doctor", "hospital", "clinic", "lab test", "gym", "fitness", "supplement",
        "personal care", "shampoo", "soap", "skincare", "salon", "spa"
    ],
    "Entertainment": [
        "movie", "cinema", "pvr", "inox", "netflix", "prime video", "hotstar",
        "spotify", "youtube", "concert", "event", "ticket", "gaming", "steam"
    ],
    "Home & Lifestyle": [
        "furniture", "ikea", "chair", "table", "mattress", "cleaning",
        "detergent", "decor", "laundry", "dry clean", "hardware", "kitchenware", "home"
    ],
    "Education": [
        "tuition", "education", "school", "college", "university", "book",
        "textbook", "notebook", "pen", "stationery", "course", "udemy", "coursera"
    ],
    "Financial & Fees": [
        "bank", "charge", "fee", "interest", "gst", "tax", "vat", "tip",
        "service charge", "penalty", "insurance", "premium", "emi", "loan"
    ]
}

VALID_CATEGORIES = list(CATEGORY_HINTS.keys())

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

    # Give the AI keyword hints per category so it has something concrete to match merchant names against
    hints_text = ""
    for category, keywords in CATEGORY_HINTS.items():
        hints_text += f"- {category}: {', '.join(keywords)}\n"
    
    prompt = f"""
    Look at these receipts:
    {receipt_text} ## basically contain data of all reciepts
    
    Pick ONE category for each receipt from this list: {', '.join(VALID_CATEGORIES)}

    Here are keyword hints for each category, based on the kind of store or item they usually match:
    {hints_text}

    This list is exhaustive, so always pick the closest matching category even if the merchant name isn't an exact keyword match. Do not invent categories outside this list.
    
    Return ONLY a JSON dictionary in the following format (no extra text):
    {{
      "receipt_name.jpg": {{
        "category": "Groceries & Quick Commerce",
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
      "by_category": {{"Groceries & Quick Commerce": 50.00, "Dining Out": 50.50}},
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