 STARTING RECEIPT ANALYSIS PIPELINE")
  

    if not os.path.exists(OCR_INPUT_FILE):
        print(f"Error: Could not find '{OCR_INPUT_FILE}'. Please scan receipts first.")
        return