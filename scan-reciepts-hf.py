import os
import json
import pytesseract
from PIL import Image
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

if not os.environ.get("HF_TOKEN"):
    print("Error: HF_TOKEN not found in .env file!")
    exit()

RECEIPTS_FOLDER = "receipts"
OUTPUT_FILE = "outputs/expenses.json"

#setup hf llm
hf_client = InferenceClient(
    model="Qwen/Qwen2.5-7B-Instruct",
    provider="auto",
    token=os.environ.get("HF_TOKEN")
)

##run tesseract ocr on one receipt image
def extract_text_from_image(image_path):
    image = Image.open(image_path)
    raw_text = pytesseract.image_to_string(image)
    return raw_text

##send raw ocr text to hf llm and get back structured receipt details
def extract_details_with_llm(raw_text, image_file):
    prompt = f"""
    Here is raw OCR text extracted from a receipt image:
    {raw_text}

    Pull out the merchant name, the final total amount, and the date if present.

    Return ONLY a valid JSON object in the following format (no extra text, no markdown backticks):
    {{
      "merchant": "store name",
      "total": 0.00,
      "date": "YYYY-MM-DD or unknown"
    }}
    """

    response = hf_client.chat_completion(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )

    reply = response.choices[0].message.content.strip()
    print(f"--- LLM raw reply for {image_file} ---\n{reply}\n")

    #clean markdown backticks if the llm forced them
    if reply.startswith("```json"):
        reply = reply[7:]
    elif reply.startswith("```"):
        reply = reply[3:]

    if reply.endswith("```"):
        reply = reply[:-3]

    reply = reply.strip()

    try:
        details = json.loads(reply)
    except Exception as e:
        print(f"Failed to understand AI's JSON output for {image_file}: {e}")
        details = {"merchant": "Unknown", "total": 0.0, "date": "unknown"}

    details["image_file"] = image_file
    return details

def scan_all_receipts():
    if not os.path.exists(RECEIPTS_FOLDER):
        print(f"No '{RECEIPTS_FOLDER}' folder found. Add receipt images first.")
        return

    os.makedirs("outputs", exist_ok=True)

    #load already scanned receipts so we dont redo work
    all_receipts = []
    scanned_files = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            all_receipts = json.load(f)
            scanned_files = {receipt["image_file"] for receipt in all_receipts}

    image_files = [f for f in os.listdir(RECEIPTS_FOLDER) if f.lower().endswith((".jpg", ".jpeg", ".png"))]

    new_count = 0
    for image_file in image_files:
        if image_file in scanned_files:
            continue

        print(f"Scanning {image_file}...")
        image_path = os.path.join(RECEIPTS_FOLDER, image_file)

        raw_text = extract_text_from_image(image_path)
        print(f"--- OCR text for {image_file} ---\n{raw_text}\n")

        details = extract_details_with_llm(raw_text, image_file)

        all_receipts.append(details)
        new_count += 1

    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_receipts, f, indent=2)

    print(f"\n Scan complete! {new_count} new receipts added. Total: {len(all_receipts)}")

if __name__ == "__main__":
    scan_all_receipts()