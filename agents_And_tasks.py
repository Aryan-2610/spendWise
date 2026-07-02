import os
import json
from dotenv import load_dotenv
from crewai import Agent, Task, LLM

load_dotenv()

if not os.environ.get("GEMINI_API_KEY"):
    print("Error: GEMINI_API_KEY not found in .env file!")
    exit()

# Initialize primary language model
gemini_engine = LLM(
    model="gemini/gemini-2.5-flash",
    api_key=os.environ.get("GEMINI_API_KEY")
)

# Comprehensive taxonomy mapped to common retail items
EXPENDITURE_TAXONOMY = {
    "Groceries & Pantry": [
        "carrot", "cucumber", "tomato", "oatmeal", "mozzarella", "cheese", "egg", "bean",
        "avocado", "apple", "pepper", "banana", "peanut butter", "bread", "pita", "milk",
        "curd", "paneer", "butter", "flour", "atta", "dal", "rice", "sugar", "salt",
        "oil", "spice", "grocery", "trader joe", "zepto", "blinkit", "bigbasket", "produce"
    ],
    "Café & Prepared Dining": [
        "frap", "coffee", "latte", "cappuccino", "espresso", "tea", "chai", "burger",
        "pizza", "noodle", "pasta", "biryani", "restaurant", "cafe", "bistro", "diner",
        "fast food", "mcdonalds", "kfc", "starbucks", "subway", "swiggy", "zomato", "bakery"
    ],
    "Logistics & Transit": [
        "fuel", "petrol", "diesel", "gas", "uber", "ola", "rapido", "taxi", "auto",
        "metro", "bus", "train", "flight", "parking", "toll", "service", "tyre", "repair"
    ],
    "Housing & Utilities": [
        "rent", "electricity", "power", "water", "gas", "cylinder", "wifi", "broadband",
        "internet", "recharge", "mobile", "phone", "maintenance", "utility"
    ],
    "Apparel & Personal Style": [
        "clothing", "shirt", "tshirt", "jeans", "pants", "dress", "shoes", "sneakers",
        "footwear", "watch", "bag", "wallet", "boutique", "zara", "h&m", "myntra"
    ],
    "Technology & Hardware": [
        "electronics", "gadget", "laptop", "phone", "tablet", "computer", "software",
        "subscription", "cloud", "cable", "charger", "headphone", "earphone", "monitor", "usb"
    ],
    "Health & Personal Care": [
        "pharmacy", "medicine", "tablet", "pill", "apollo", "medplus", "medical", "doctor",
        "hospital", "clinic", "gym", "fitness", "supplement", "protein", "shampoo", "soap", "salon"
    ],
    "Recreation & Media": [
        "movie", "pvr", "inox", "netflix", "prime", "hotstar", "spotify", "youtube",
        "concert", "show", "event", "ticket", "gaming", "steam"
    ],
    "Home & Living": [
        "furniture", "ikea", "chair", "table", "bed", "mattress", "cleaning",
        "detergent", "laundry", "hardware", "utensil", "kitchenware", "home"
    ],
    "Academics & Learning": [
        "tuition", "education", "school", "college", "book", "textbook", "notebook",
        "pen", "stationery", "course", "udemy", "coursera"
    ],
    "Taxes, Discounts & Adjustments": [
        "tax", "gst", "vat", "discount", "given", "coupon", "fee", "charge", "interest", "penalty"
    ]
}

AVAILABLE_BUCKETS = list(EXPENDITURE_TAXONOMY.keys())

def build_item_classification_agent():
    """Agent specialized in item-level retail classification."""
    return Agent(
        role="Line-Item Taxonomist",
        goal="Classify individual retail line items into accurate expenditure buckets.",
        backstory="You are a data engineer skilled at retail SKU mapping. You analyze item descriptions and merchant contexts to classify items with high precision. Return ONLY valid JSON.",
        llm=gemini_engine,
        verbose=True,
        allow_delegation=False
    )

def build_financial_auditor_agent():
    """Agent that synthesizes itemized spending patterns."""
    return Agent(
        role="Senior Financial Auditor",
        goal="Evaluate line-item expenditure distribution and extract behavioral insights.",
        backstory="You are an auditor who relies strictly on deterministic Python accounting summaries. You discover micro-spending trends and item preferences. Return ONLY valid JSON.",
        llm=gemini_engine,
        verbose=True,
        allow_delegation=False
    )

def build_student_coach_agent():
    """Agent that translates financial audits into student-focused advice."""
    return Agent(
        role="Student Financial Advisory Lead",
        goal="Provide practical, non-judgmental financial coaching tailored to college life.",
        backstory="You are a mentor specializing in student personal finance. You create actionable strategies for reducing recurring costs without sacrificing quality of life. Return ONLY valid JSON.",
        llm=gemini_engine,
        verbose=True,
        allow_delegation=False
    )

def create_item_mapping_task(agent, line_items_batch):
    """Generates task for item-wise classification."""
    items_str = ""
    for entry in line_items_batch:
        items_str += f"- ID: {entry['unique_key']} | Store: {entry['merchant']} | Item: '{entry['description']}' | Cost: ₹{entry['amount']}\n"

    hints_str = "\n".join(
        f"• {bucket}: {', '.join(kws)}" for bucket, kws in EXPENDITURE_TAXONOMY.items()
    )

    prompt = f"""
    Classify the following retail line items:
    {items_str}

    Assign ONE classification bucket to each item ID from this exact taxonomy:
    {', '.join(AVAILABLE_BUCKETS)}

    Taxonomy Keywords & Definitions:
    {hints_str}

    Return ONLY a JSON dictionary mapping each unique ID string to its category and rationale:
    {{
      "rec1_item1": {{
        "category": "Groceries & Pantry",
        "confidence": 0.98,
        "rationale": "Fresh produce item."
      }}
    }}
    """

    return Task(
        description=prompt,
        agent=agent,
        expected_output="JSON dictionary mapping unique item IDs to taxonomy classifications."
    )

def create_audit_task(agent, python_accounting_summary):
    """Generates task for qualitative audit of Python deterministic math."""
    prompt = f"""
    Review the deterministic accounting summary computed by Python verification scripts:
    Overall Verified Total: ₹{python_math_total(python_accounting_summary):.2f}
    
    Category Expenditure Breakdown:
    {json.dumps(python_accounting_summary['category_totals'], indent=2)}

    Item Count per Category:
    {json.dumps(python_accounting_summary['item_counts'], indent=2)}

    Generate 3 to 4 analytical observations focusing on specific item concentration, average item cost, and merchant habits.

    Return ONLY a JSON dictionary:
    {{
      "audit_insights": [
        "First observation regarding spending concentration.",
        "Second observation highlighting item transaction frequency.",
        "Third observation evaluating expenditure velocity."
      ]
    }}
    """

    return Task(
        description=prompt,
        agent=agent,
        expected_output="JSON object containing financial audit observations."
    )

def python_math_total(summary):
    return summary.get("overall_total", 0.0)

def create_coaching_task(agent, python_accounting_summary, audit_observations):
    """Generates task for student budgeting advisory."""
    prompt = f"""
    Review verified student accounting totals:
    Total Spent: ₹{python_accounting_summary['overall_total']:.2f}
    Category Distribution: {json.dumps(python_accounting_summary['category_totals'])}

    Audit Observations:
    {json.dumps(audit_observations)}

    Provide actionable personal finance recommendations for a university student.
    Return ONLY a JSON object:
    {{
      "analysis": {{
        "total_spent": {python_accounting_summary['overall_total']},
        "by_category": {json.dumps(python_accounting_summary['category_totals'])},
        "item_counts": {json.dumps(python_accounting_summary['item_counts'])},
        "insights": {json.dumps(audit_observations)}
      }},
      "advice": {{
        "budget_status": "Optimized / Stable / Needs Adjustment",
        "tips": [
          "First concrete cost-reduction recommendation.",
          "Second lifestyle optimization recommendation."
        ],
        "quick_win": "Immediate adjustment for today.",
        "positive_note": "Short word of encouragement."
      }}
    }}
    """

    return Task(
        description=prompt,
        agent=agent,
        expected_output="Complete financial health report combining Python math, audit, and advice."
    )