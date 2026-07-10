import os
import json
import time
import requests
import util
from pathlib import Path

# Configurable paths and API settings
RECEIPT_STORAGE_DIR = "receipts"
OUTPUT_DIRECTORY = "outputs"
PRIMARY_RAW_DATA_FILE = os.path.join(OUTPUT_DIRECTORY, "ocr_results.json")
LEGACY_BACKUP_FILE = os.path.join(OUTPUT_DIRECTORY, "expenses.json")

ASPRISE_ENDPOINT = "https://ocr2.asprise.com/api/v1/receipt"
DEFAULT_TEST_KEY = "TEST"

class ReceiptCaptureService:
    """Automated document processing engine utilizing receipt extraction endpoints."""
    
    def __init__(self, api_key: str = DEFAULT_TEST_KEY):
        self.api_key = api_key
        self.endpoint_url = ASPRISE_ENDPOINT
        os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
        self.scanned_records = self._load_existing_records()

    def _load_existing_records(self):
        if os.path.exists(PRIMARY_RAW_DATA_FILE):
            try:
                with open(PRIMARY_RAW_DATA_FILE, "r", encoding="utf-8") as file_ptr:
                    return json.load(file_ptr)
            except Exception as exc:
                print(f"[Warn] Could not parse existing records: {exc}. Starting fresh.")
                return []
        return []

    def _save_records(self):
        with open(PRIMARY_RAW_DATA_FILE, "w", encoding="utf-8") as file_ptr:
            json.dump(self.scanned_records, file_ptr, indent=2, ensure_ascii=False)
        with open(LEGACY_BACKUP_FILE, "w", encoding="utf-8") as file_ptr:
            json.dump(self.scanned_records, file_ptr, indent=2, ensure_ascii=False)

    def extract_document(self, image_filepath: str, max_retries: int = 4):
        """Sends document binary to OCR extraction service with retry logic for HTTP 429 rate limits."""
        for attempt in range(1, max_retries + 1):
            try:
                with open(image_filepath, "rb") as binary_stream:
                    payload = {
                        "api_key": self.api_key,
                        "recognizer": "auto",
                        "ref_no": f"tx_{int(time.time())}"
                    }
                    response = requests.post(
                        self.endpoint_url,
                        data=payload,
                        files={"file": binary_stream},
                        timeout=30
                    )
                if response.status_code == 429:
                    wait_time = attempt * 5
                    print(f"   ⏳ Rate limit hit (HTTP 429). Pausing for {wait_time}s before retry {attempt}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
                if response.status_code != 200:
                    print(f"[Error] Service returned HTTP {response.status_code} for {image_filepath}")
                    return None
                return response.json()
            except Exception as err:
                print(f"[Error] Request failure while processing {image_filepath}: {err}")
                time.sleep(2)
        print(f"   ❌ Exceeded maximum retries for {image_filepath} due to rate limiting.")
        return None

    def transform_receipt_payload(self, raw_json: dict, filename: str, sequence_id: int):
        """Transforms API response into a normalized line-item structure."""
        receipts_list = raw_json.get("receipts", [])
        if not receipts_list:
            return {
                "seq_no": sequence_id,
                "image_file": filename,
                "merchant": "Unidentified Store",
                "date": "unknown",
                "total": 0.0,
                "line_items": []
            }

        primary_doc = receipts_list[0]
        merchant_name = primary_doc.get("merchant_name") or "Unidentified Store"
        tx_date = primary_doc.get("date") or "unknown"
        doc_total = primary_doc.get("total")
        if doc_total is None:
            doc_total = primary_doc.get("subtotal", 0.0)

        raw_items = primary_doc.get("items", [])
        normalized_items = []

        for idx, item in enumerate(raw_items, start=1):
            desc = item.get("description") or f"Item #{idx}"
            amt = item.get("amount")
            if amt is None:
                amt = item.get("unitPrice", 0.0)
            qty = item.get("qty") or 1.0

            normalized_items.append({
                "item_id": idx,
                "description": str(desc).strip(),
                "quantity": float(qty) if isinstance(qty, (int, float)) else 1.0,
                "amount": float(amt) if isinstance(amt, (int, float)) else 0.0
            })

        # Fallback if line items couldn't be parsed individually
        if not normalized_items and doc_total and float(doc_total) > 0:
            normalized_items.append({
                "item_id": 1,
                "description": f"General Purchase at {merchant_name}",
                "quantity": 1.0,
                "amount": float(doc_total)
            })

        # Calculate exact sum from line items if overall total is missing or zero
        calculated_item_sum = sum(i["amount"] for i in normalized_items)
        final_total = float(doc_total) if (doc_total and float(doc_total) > 0) else calculated_item_sum

        return {
            "seq_no": sequence_id,
            "image_file": filename,
            "merchant": str(merchant_name).strip(),
            "date": str(tx_date).strip(),
            "total": round(final_total, 2),
            "line_items": normalized_items
        }

    def execute_batch_processing(self):
        """Scans all receipt images in target directory that haven't been previously processed."""
        if not os.path.exists(RECEIPT_STORAGE_DIR):
            print(f"[Notice] Input directory '{RECEIPT_STORAGE_DIR}' does not exist.")
            return

        processed_filenames = {
            rec.get("image_file") for rec in self.scanned_records if "image_file" in rec
        }

        all_image_paths = sorted([
            fname for fname in os.listdir(RECEIPT_STORAGE_DIR)
            if fname.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
        ])

        print(f"\n📁 Discovered {len(all_image_paths)} files in '{RECEIPT_STORAGE_DIR}'.")
        print(f"🔄 Previously indexed: {len(processed_filenames)} files.\n")

        added_records = 0
        for fname in all_image_paths:
            if fname in processed_filenames:
                continue

            seq_id = len(self.scanned_records) + 1
            print(f"[{seq_id}/{len(all_image_paths)}] Processing document: {fname} ...")
            full_path = os.path.join(RECEIPT_STORAGE_DIR, fname)

            api_result = self.extract_document(full_path)
            if not api_result:
                print(f"   ⚠️ Could not extract document data for {fname}.")
                continue

            structured_entry = self.transform_receipt_payload(api_result, fname, seq_id)
            self.scanned_records.append(structured_entry)
            processed_filenames.add(fname)
            added_records += 1

            items_count = len(structured_entry["line_items"])
            print(f"   ✅ Extracted: {structured_entry['merchant']} | Total: {util.symbol}{structured_entry['total']:.2f} | Items: {items_count}")

            self._save_records()
            # Polite pause to avoid triggering Asprise API rate limits on consecutive requests
            time.sleep(2.5)

        print(f"\n🎉 Batch capture completed! Added {added_records} new documents.")
        print(f"💾 Total records saved to '{PRIMARY_RAW_DATA_FILE}'.")

if __name__ == "__main__":
    service = ReceiptCaptureService()
    service.execute_batch_processing()