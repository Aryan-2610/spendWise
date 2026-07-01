import os
import json
import requests
from datetime import datetime
import time


#folder
IMAGES_FOLDER = "images"
DATABASE_FILE = "outputs/expenses.json"

# API details for Asprise OCR
API_KEY = "TEST"## for free trial
API_URL = "https://ocr2.asprise.com/api/v1/receipt"
def load_existing_expenses():
    """Loads the database file if it exists, otherwise returns an empty list."""
    ##already present jsons ko check
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, "r") as file:
            return json.load(file)
    return []

def scan_image_with_api(image_path):
    """Sends one image to the OCR API and returns the result."""
    try:
        with open(image_path, "rb") as image_file:
            ##send as binary over the net to endpoint as post req and get res
            response = requests.post(
                API_URL, 
                data={'api_key': API_KEY, 'recognizer': 'auto'},
                files={"file": image_file},
                timeout=15
            )
        
        # If the request was successful, return the JSON data
        if response.status_code == 200:##working
            return response.json()
        else:
            print(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Network error while scanning {image_path}: {e}")
        return None

def process_all_images():
    """Loops through the images folder and scans new receipts."""
    print("Starting receipt scanner...")
    
    expenses_list = load_existing_expenses() ##already json
    
    # Create folder if it doesn't exist
    if not os.path.exists(IMAGES_FOLDER):
        os.makedirs(IMAGES_FOLDER)
        
    all_images = os.listdir(IMAGES_FOLDER)##reciept images
    
    # Use a set for O(1) lightning fast lookups instead of O(N^2) loops
    scanned_files = {expense["image_file"] for expense in expenses_list}
    
    print(f"Found {len(all_images)} images in the folder.")
    
    for filename in all_images:
        # Check if we already scanned this image
        if filename in scanned_files:
            print(f"Skipping {filename} - already scanned.")
            continue
            
        print(f"Scanning new receipt: {filename}...")
        full_path = os.path.join(IMAGES_FOLDER, filename)
        
        # Send to API
        api_result = scan_image_with_api(full_path)
        
        # Check if the API successfully found a receipt
        if api_result and "receipts" in api_result and len(api_result["receipts"]) > 0:
            receipt_data = api_result["receipts"][0]
            
            # Format the data neatly
            clean_data = {
                "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "image_file": filename,
                "merchant": receipt_data.get("merchant_name", "Unknown Store"),
                "total": receipt_data.get("total", 0),
                "date": receipt_data.get("date", "Unknown Date")
            }
            
            expenses_list.append(clean_data)
            print(f"Success! Saved {clean_data['merchant']} - ₹{clean_data['total']}")
            
            # Save to file as backup on crashes
            os.makedirs(os.path.dirname(DATABASE_FILE), exist_ok=True)
            with open(DATABASE_FILE, "w") as file:
                json.dump(expenses_list, file, indent=2)
        else:
            print(f"Error: Could not read {filename}")
        time.sleep(3)
    print("\nDone scanning!")

if __name__ == "__main__":
    process_all_images()