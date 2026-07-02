import os
import re
import json
from crewai import Crew, Process
from agents_And_tasks import (
    build_item_classification_agent, build_financial_auditor_agent, build_student_coach_agent,
    create_item_mapping_task, create_audit_task, create_coaching_task,
    EXPENDITURE_TAXONOMY, AVAILABLE_BUCKETS
)

RAW_OCR_INPUT = "outputs/ocr_results.json"
ITEMIZED_OUTPUT_DATA = "outputs/categorized_receipts.json"
FINAL_AUDIT_REPORT = "outputs/crew_analysis.json"

def clean_json_payload(raw_text):
    """Safely extracts JSON payload from LLM responses."""
    if not raw_text:
        return {}
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

def rule_based_item_taxonomy(description_text):
    """Deterministic keyword matching fallback for retail item descriptions."""
    text_lower = str(description_text).lower()
    for category_name, keywords in EXPENDITURE_TAXONOMY.items():
        for kw in keywords:
            if kw in text_lower:
                return category_name
    return "Groceries & Pantry"

def execute_analytics_pipeline():
    print("=" * 72)
    print(" 🚀 EXECUTION ENGINE: ITEM-WISE CATEGORIZATION & DETERMINISTIC AUDIT")
    print("=" * 72)

    if not os.path.exists(RAW_OCR_INPUT):
        print(f"❌ Critical Error: Input source '{RAW_OCR_INPUT}' missing. Execute scan service first.")
        return

    with open(RAW_OCR_INPUT, "r", encoding="utf-8") as file_ptr:
        raw_documents = json.load(file_ptr)

    if not raw_documents:
        print("❌ No receipt records discovered inside input payload.")
        return

    print(f"\n📁 Loaded {len(raw_documents)} receipt documents.")

    # 1. Flatten into unique line items for item-wise categorization
    flattened_items = []
    for doc in raw_documents:
        merch = doc.get("merchant", "General Store")
        seq = doc.get("seq_no", 1)
        for item in doc.get("line_items", []):
            item_id = item.get("item_id", 1)
            u_key = f"r{seq}_i{item_id}"
            flattened_items.append({
                "unique_key": u_key,
                "seq_no": seq,
                "merchant": merch,
                "description": item.get("description", ""),
                "amount": float(item.get("amount", 0.0)),
                "quantity": float(item.get("quantity", 1.0))
            })

    print(f"🔍 Discovered {len(flattened_items)} total line items across all receipts.")

    # Check if existing item categorization cache exists
    item_category_map = {}
    if os.path.exists(ITEMIZED_OUTPUT_DATA):
        try:
            with open(ITEMIZED_OUTPUT_DATA, "r", encoding="utf-8") as file_ptr:
                cached_docs = json.load(file_ptr)
                for c_doc in cached_docs:
                    seq = c_doc.get("seq_no", 1)
                    for c_item in c_doc.get("line_items", []):
                        uk = f"r{seq}_i{c_item.get('item_id', 1)}"
                        if "category" in c_item:
                            item_category_map[uk] = c_item["category"]
        except Exception as exc:
            print(f"[Warn] Could not read existing item cache: {exc}")

    unclassified_items = [
        it for it in flattened_items if it["unique_key"] not in item_category_map
    ]

    if unclassified_items:
        print(f"⚙️ Running AI Taxonomist on {len(unclassified_items)} unclassified line items...")
        taxonomist = build_item_classification_agent()
        batch_size = 20
        for b_idx in range(0, len(unclassified_items), batch_size):
            batch = unclassified_items[b_idx:b_idx + batch_size]
            print(f"   -> Processing item batch {b_idx // batch_size + 1} ({len(batch)} items)...")
            task = create_item_mapping_task(taxonomist, batch)
            crew = Crew(agents=[taxonomist], tasks=[task], process=Process.sequential, verbose=False)
            res = crew.kickoff()
            parsed_res = clean_json_payload(res)

            for item_obj in batch:
                uk = item_obj["unique_key"]
                desc = item_obj["description"]
                if uk in parsed_res and isinstance(parsed_res[uk], dict):
                    assigned_cat = parsed_res[uk].get("category")
                else:
                    assigned_cat = rule_based_item_taxonomy(desc)

                if assigned_cat not in AVAILABLE_BUCKETS:
                    assigned_cat = rule_based_item_taxonomy(desc)

                item_category_map[uk] = assigned_cat

    # Reconstruct itemized receipt dataset
    enriched_documents = []
    for doc in raw_documents:
        seq = doc.get("seq_no", 1)
        new_line_items = []
        for item in doc.get("line_items", []):
            item_id = item.get("item_id", 1)
            uk = f"r{seq}_i{item_id}"
            cat = item_category_map.get(uk, rule_based_item_taxonomy(item.get("description", "")))
            new_item = dict(item)
            new_item["category"] = cat
            new_line_items.append(new_item)

        new_doc = dict(doc)
        new_doc["line_items"] = new_line_items
        enriched_documents.append(new_doc)

    os.makedirs("outputs", exist_ok=True)
    with open(ITEMIZED_OUTPUT_DATA, "w", encoding="utf-8") as file_ptr:
        json.dump(enriched_documents, file_ptr, indent=2, ensure_ascii=False)

    print(f"✅ Item-wise categorization complete! Saved to '{ITEMIZED_OUTPUT_DATA}'.")

    # 2. Deterministic Python Accounting Computation
    print("\n🧮 Executing 100% Deterministic Python Accounting Aggregation...")
    overall_total = 0.0
    category_totals = {}
    item_counts = {}

    for doc in enriched_documents:
        for item in doc.get("line_items", []):
            cost = float(item.get("amount", 0.0))
            cat = item.get("category", "Groceries & Pantry")

            overall_total += cost
            category_totals[cat] = category_totals.get(cat, 0.0) + cost
            item_counts[cat] = item_counts.get(cat, 0) + 1

    overall_total = round(overall_total, 2)
    for cat in category_totals:
        category_totals[cat] = round(category_totals[cat], 2)

    python_accounting_summary = {
        "overall_total": overall_total,
        "category_totals": category_totals,
        "item_counts": item_counts
    }

    print(f"   -> Verified Total Expenditure: ₹{overall_total:,.2f}")
    print(f"   -> Active Expenditure Buckets: {len(category_totals)}")

    # 3. AI Financial Audit & Advisory Phase
    print("\n💡 Synthesizing Financial Audit & Student Coaching Report...")
    auditor = build_financial_auditor_agent()
    coach = build_student_coach_agent()

    audit_task = create_audit_task(auditor, python_accounting_summary)
    crew_auditor = Crew(agents=[auditor], tasks=[audit_task], process=Process.sequential, verbose=False)
    audit_res = crew_auditor.kickoff()
    parsed_audit = clean_json_payload(audit_res)
    observations = parsed_audit.get("audit_insights", [
        f"Analyzed {len(flattened_items)} distinct line items across {len(enriched_documents)} receipts.",
        f"Highest line-item concentration is observed within top spending buckets."
    ])

    coaching_task = create_coaching_task(coach, python_accounting_summary, observations)
    crew_coach = Crew(agents=[coach], tasks=[coaching_task], process=Process.sequential, verbose=False)
    coach_res = crew_coach.kickoff()
    final_payload = clean_json_payload(coach_res)

    if "analysis" not in final_payload or not isinstance(final_payload["analysis"], dict):
        final_payload["analysis"] = {}

    final_payload["analysis"]["total_spent"] = python_accounting_summary["overall_total"]
    final_payload["analysis"]["by_category"] = python_accounting_summary["category_totals"]
    final_payload["analysis"]["category_counts"] = python_accounting_summary["item_counts"]
    final_payload["analysis"]["insights"] = observations

    if "advice" not in final_payload or not isinstance(final_payload["advice"], dict):
        final_payload["advice"] = {
            "budget_status": "Optimized Student Spending",
            "tips": ["Monitor recurring item costs and buy non-perishables in bulk."],
            "quick_win": "Audit line items with unit costs exceeding ₹5.00.",
            "positive_note": "Itemized tracking gives you complete control over your budget!"
        }

    with open(FINAL_AUDIT_REPORT, "w", encoding="utf-8") as file_ptr:
        json.dump(final_payload, file_ptr, indent=2, ensure_ascii=False)

    print(f"\n🏆 Workflow execution completed! Report persisted to '{FINAL_AUDIT_REPORT}'.")
    print("Execute `python analysis.py` to launch interactive dashboard.")

if __name__ == "__main__":
    execute_analytics_pipeline()