import os
import re
import json
import util
from crewai import Crew, Process
from agents_And_tasks import (
    categorizer_agent, analyst_agent, advisor_agent,
    create_categorization_task, create_analysis_task, create_advisory_task,
    CATEGORIES
)

OCR_INPUT_FILE = "outputs/ocr_results.json"
CATEGORIZED_FILE = "outputs/categorized_receipts.json"
FINAL_REPORT_FILE = "outputs/crew_analysis.json"

def clean_json_response(raw_text):
    """Clean up and parse JSON from LLM output."""
    if not raw_text:
        return {}
    if hasattr(raw_text, "raw"):
        raw_text = raw_text.raw
    elif hasattr(raw_text, "output"):
        raw_text = raw_text.output
    cleaned = str(raw_text).strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}") + 1
    if start_idx != -1 and end_idx > start_idx:
        try:
            return json.loads(cleaned[start_idx:end_idx])
        except Exception:
            return {}
    return {}

def run_pipeline():
   
    print(" STARTING RECEIPT ANALYSIS PIPELINE")

    if not os.path.exists(OCR_INPUT_FILE):
        print(f"Error: Could not find '{OCR_INPUT_FILE}'. Please scan receipts first.")
        return

    with open(OCR_INPUT_FILE, "r", encoding="utf-8") as f:
        receipts = json.load(f)

    if not receipts:
        print(" No receipt data found.")
        return

    print(f"\n Loaded {len(receipts)} receipts.")

    # 1. Collect all receipt items
    all_items = []
    for doc in receipts:
        store = doc.get("merchant", "General Store")
        seq = doc.get("seq_no", 1)
        for item in doc.get("line_items", []):
            item_id = item.get("item_id", 1)
            all_items.append({
                "unique_key": f"r{seq}_i{item_id}",
                "seq_no": seq,
                "merchant": store,
                "description": item.get("description", ""),
                "amount": float(item.get("amount", 0.0)),
                "quantity": float(item.get("quantity", 1.0))
            })

    print(f"Found {len(all_items)} line items across receipts.")

    # Load previously saved categories if available
    category_map = {}
    if os.path.exists(CATEGORIZED_FILE):
        try:
            with open(CATEGORIZED_FILE, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                for doc in cached_data:
                    seq = doc.get("seq_no", 1)
                    for item in doc.get("line_items", []):
                        key = f"r{seq}_i{item.get('item_id', 1)}"
                        if "category" in item:
                            category_map[key] = item["category"]
        except Exception:
            pass

    unclassified = [item for item in all_items if item["unique_key"] not in category_map]

    if unclassified:
        print(f" Categorizing {len(unclassified)} items with AI agent")
        categorizer = categorizer_agent()
        batch_size = 20
        for i in range(0, len(unclassified), batch_size):
            batch = unclassified[i:i + batch_size]
            print(f"   -> Processing batch {i // batch_size + 1} ({len(batch)} items)...")
            task = create_categorization_task(categorizer, batch)
            crew = Crew(agents=[categorizer], tasks=[task], process=Process.sequential, verbose=False)
            res = crew.kickoff()
            parsed = clean_json_response(res)

            for item in batch:
                key = item["unique_key"]
                val = parsed.get(key)
                category = None
                if isinstance(val, dict):
                    category = val.get("category")
                elif isinstance(val, str):
                    category = val

                if category:
                    category = category.strip()
                    if category not in CATEGORIES:
                        # Case-insensitive or partial match against valid categories
                        for valid_cat in CATEGORIES:
                            if valid_cat.lower() in category.lower() or category.lower() in valid_cat.lower():
                                category = valid_cat
                                break
                        else:
                            category = "Other"
                else:
                    category = "Other"

                category_map[key] = category

    # Update receipts with categories
    updated_receipts = []
    for doc in receipts:
        seq = doc.get("seq_no", 1)
        new_line_items = []
        for item in doc.get("line_items", []):
            key = f"r{seq}_i{item.get('item_id', 1)}"
            cat = category_map.get(key, "Other")
            new_item = dict(item)
            new_item["category"] = cat
            new_line_items.append(new_item)

        new_doc = dict(doc)
        new_doc["line_items"] = new_line_items
        updated_receipts.append(new_doc)

    os.makedirs("outputs", exist_ok=True)
    with open(CATEGORIZED_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_receipts, f, indent=2, ensure_ascii=False)

    print(f" Items categorized and saved to '{CATEGORIZED_FILE}'.")

    # 2. Calculate totals using simple Python math
    print("\n Calculating totals...")
    total_spent = 0.0
    category_totals = {}
    item_counts = {}

    for doc in updated_receipts:
        for item in doc.get("line_items", []):
            cost = float(item.get("amount", 0.0))
            cat = item.get("category", "Groceries")

            total_spent += cost
            category_totals[cat] = category_totals.get(cat, 0.0) + cost
            item_counts[cat] = item_counts.get(cat, 0) + 1

    total_spent = round(total_spent, 2)
    for cat in category_totals:
        category_totals[cat] = round(category_totals[cat], 2)

    summary = {
        "overall_total": total_spent,
        "category_totals": category_totals,
        "item_counts": item_counts
    }

    print(f"   -> Total Spent: {util.symbol}{total_spent:,.2f}")

    # 3. Analyze patterns and generate advice
    print("\nGenerating insights and student budgeting advice...")
    analyst = analyst_agent()
    advisor = advisor_agent()

    analysis_task = create_analysis_task(analyst, summary)
    crew_analyst = Crew(agents=[analyst], tasks=[analysis_task], process=Process.sequential, verbose=False)
    analyst_res = crew_analyst.kickoff()
    parsed_analysis = clean_json_response(analyst_res)
    insights = parsed_analysis.get("insights", [
        f"Analyzed {len(all_items)} items across {len(updated_receipts)} receipts.",
        f"Spending is concentrated in your top categories."
    ])

    advisory_task = create_advisory_task(advisor, summary, insights)
    crew_advisor = Crew(agents=[advisor], tasks=[advisory_task], process=Process.sequential, verbose=False)
    advisor_res = crew_advisor.kickoff()
    final_report = clean_json_response(advisor_res)

    if "analysis" not in final_report or not isinstance(final_report["analysis"], dict):
        final_report["analysis"] = {}

    final_report["analysis"]["total_spent"] = summary["overall_total"]
    final_report["analysis"]["by_category"] = summary["category_totals"]
    final_report["analysis"]["category_counts"] = summary["item_counts"]
    final_report["analysis"]["insights"] = insights

    if "advice" not in final_report or not isinstance(final_report["advice"], dict):
        final_report["advice"] = {
            "budget_status": "Healthy Spending",
            "tips": ["Keep track of small daily expenses to save more."],
            "quick_win": "Review your highest spending category this week.",
            "positive_note": "Great job tracking your budget!"
        }

    with open(FINAL_REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)

    print(f"\n Done! Full report saved to '{FINAL_REPORT_FILE}'.")
    print("Run `python analysis.py` to view your spending dashboard.")

if __name__ == "__main__":
    run_pipeline()