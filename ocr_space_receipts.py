import os
import requests
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Exact exhaustive category list mapped to descriptive keywords
CATEGORIES = {
    "Groceries & Quick Commerce": [
        "zepto", "swiggy instamart", "blinkit", "bigbasket", "supermarket", "grocery",
        "dairy", "milk", "curd", "paneer", "cheese", "butter", "bread", "egg",
        "vegetable", "fruit", "produce", "apple", "banana", "onion", "potato",
        "tomato", "rice", "atta", "flour", "wheat", "dal", "lentil", "sugar", "salt",
        "oil", "masala", "spice", "snack", "biscuit", "chips", "tea", "coffee",
        "cereal", "oats", "beverage", "juice"
    ],
    "Dining Out": [
        "restaurant", "cafe", "bistro", "diner", "fast food", "burger", "pizza",
        "mcdonalds", "kfc", "domino", "starbucks", "subway", "swiggy", "zomato",
        "chai", "noodle", "pasta", "biryani", "thali", "bar", "pub", "dessert",
        "ice cream", "bakery", "cake", "meal", "dine"
    ],
    "Transportation": [
        "fuel", "petrol", "diesel", "cabs", "uber", "ola", "rapido", "taxi",
        "auto", "transit", "metro", "bus", "train", "flight", "airline",
        "airways", "parking", "toll", "repair", "service", "mechanic", "tyre", "tire"
    ],
    "Housing & Utilities": [
        "rent", "electricity", "power", "bescom", "water", "gas", "lpg", "cylinder",
        "internet", "broadband", "wifi", "airtel", "jio", "vodafone", "recharge",
        "mobile", "phone", "maintenance", "utility", "bill"
    ],
    "Shopping & Apparel": [
        "clothing", "clothes", "shirt", "tshirt", "jeans", "pants", "trousers",
        "dress", "skirt", "shoes", "sneakers", "footwear", "socks", "accessories",
        "watch", "bag", "purse", "wallet", "tailoring", "tailor", "boutique",
        "zara", "h&m", "myntra", "apparel", "fashion"
    ],
    "Electronics & Tech": [
        "electronics", "gadget", "laptop", "mobile device", "tablet", "computer",
        "software", "subscription", "cloud", "aws", "apple", "google storage",
        "cable", "charger", "adapter", "repair", "headphone", "earphone", "monitor",
        "mouse", "keyboard", "tech", "usb"
    ],
    "Health & Wellness": [
        "pharmacy", "medicine", "tablet", "syrup", "pill", "paracetamol", "apollo",
        "medplus", "medical", "consultation", "doctor", "hospital", "clinic",
        "lab test", "gym", "fitness", "workout", "supplement", "protein", "vitamin",
        "personal care", "shampoo", "soap", "toothpaste", "skincare", "salon", "spa"
    ],
    "Entertainment": [
        "movie", "cinema", "pvr", "inox", "netflix", "prime video", "hotstar",
        "spotify", "youtube", "ott", "concert", "show", "event", "ticket",
        "gaming", "steam", "playstation", "xbox", "fun"
    ],
    "Home & Lifestyle": [
        "furniture", "ikea", "chair", "table", "bed", "mattress", "cleaning",
        "detergent", "phenyl", "broom", "mop", "decor", "cushion", "curtain",
        "laundry", "dry clean", "hardware", "utensil", "kitchenware", "home"
    ],
    "Education": [
        "tuition", "education", "school", "college", "university", "book",
        "textbook", "notebook", "pen", "pencil", "stationery", "course",
        "udemy", "coursera", "class", "exam"
    ],
    "Financial & Fees": [
        "bank", "charge", "fee", "interest", "gst", "cgst", "sgst", "igst", "tax",
        "vat", "tip", "service charge", "late fee", "penalty", "insurance",
        "premium", "emi", "loan", "total", "subtotal", "cash", "card", "discount"
    ]
}


def extract_receipt_lines(image_path):
    """
    Sends a receipt image to the OCR.space API and extracts text line-by-line.
    Uses procedural try/except error handling and includes the isTable=True parameter.
    """
    # Step 1: Load the API key from environment variables
    api_key = os.environ.get("OCR_SPACE_API_KEY")
    if not api_key:
        print("Error: OCR_SPACE_API_KEY not found. Please set it in your .env file.")
        return []

    # Step 2: Ensure the image file actually exists locally
    if not os.path.exists(image_path):
        print(f"Error: Receipt image '{image_path}' does not exist.")
        return []

    url = "https://api.ocr.space/parse/image"

    # Step 3: Prepare the parameters required by OCR.space
    # isTable=True helps OCR.space parse tabular data like itemized receipt lines
    payload = {
        "apikey": api_key,
        "isTable": True,
        "OCREngine": 2  # Engine 2 is recommended for numbers and table reading
    }

    try:
        # Step 4: Open the image file in binary read mode and send POST request
        with open(image_path, "rb") as image_file:
            response = requests.post(
                url,
                data=payload,
                files={"file": image_file},
                timeout=30
            )

        # Step 5: Check if the network request was successful (HTTP 200)
        response.raise_for_status()
        data = response.json()

        # Step 6: Check for API-level processing errors returned by OCR.space
        if data.get("IsErroredOnProcessing", False):
            error_message = data.get("ErrorMessage", ["Unknown OCR processing error"])
            print(f"OCR.space API error: {error_message}")
            return []

        parsed_results = data.get("ParsedResults")
        if not parsed_results:
            print("Warning: No parsed text returned from OCR.space.")
            return []

        # Step 7: Extract the raw text and split it line by line
        raw_text = parsed_results[0].get("ParsedText", "")
        
        # Remove empty lines and extra whitespace around each line
        extracted_lines = []
        for line in raw_text.splitlines():
            cleaned_line = line.strip()
            if cleaned_line:
                extracted_lines.append(cleaned_line)

        return extracted_lines

    except requests.exceptions.RequestException as network_error:
        print(f"Network failure while communicating with OCR.space: {network_error}")
        return []
    except Exception as general_error:
        print(f"An unexpected error occurred during OCR extraction: {general_error}")
        return []


def categorize_item_line(line_text):
    """
    Categorizes a single item text line into one of our exhaustive categories
    using simple, procedural keyword matching.
    """
    text_lower = line_text.lower()

    # Loop through each category and check if any keyword exists in the line text
    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category

    # If no keyword matches, default to Groceries & Quick Commerce as general store
    # item descriptions (like food or household items without brand names) usually fit best here.
    return "Groceries & Quick Commerce"


def process_and_categorize_receipt(image_path):
    """
    Main helper function that runs the OCR extraction on a receipt image
    and categorizes each extracted line.
    """
    print(f"\nScanning receipt: {image_path} ...")
    lines = extract_receipt_lines(image_path)

    if not lines:
        print("No lines extracted or an error occurred.")
        return []

    itemized_receipt = []
    for line in lines:
        assigned_category = categorize_item_line(line)
        itemized_receipt.append({
            "line": line,
            "category": assigned_category
        })

    return itemized_receipt


if __name__ == "__main__":
    # Example usage: Test with the first receipt found in the receipts folder
    test_image_folder = "receipts"
    if os.path.exists(test_image_folder):
        available_images = [
            f for f in os.listdir(test_image_folder)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        if available_images:
            sample_image = os.path.join(test_image_folder, available_images[0])
            results = process_and_categorize_receipt(sample_image)
            
            print("\n--- Categorized Receipt Lines ---")
            for item in results:
                print(f"[{item['category']}] -> {item['line']}")
        else:
            print(f"No image files found inside '{test_image_folder}'.")
    else:
        print("Receipts directory not found.")
