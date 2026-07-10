# util.py - Simple currency configuration for SpendWise

CURRENCIES = {
    "INR": "Rs",   # Indian Rupee
    "USD": "$",    # US Dollar
    "GBP": "£",    # British Pound
    "EUR": "€",    # Euro
    "JPY": "¥"     # Japanese Yen
}

# User sets their choice of currency here (e.g., "INR", "USD", "GBP", "EUR", "JPY")
curr = "INR"

# Active currency symbol used across the project (analysis, terminal, dashboard)
symbol = CURRENCIES.get(curr, "Rs")
