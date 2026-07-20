#!/usr/bin/env python3
"""Test phone number normalization logic"""

def normalize_phone(phone: str) -> str:
    """Test the phone normalization logic"""
    original_phone = phone
    phone = phone.replace(' ', '').replace('-', '')  # Remove spaces and dashes
    
    print(f"Input: '{original_phone}' -> Cleaned: '{phone}' (len={len(phone)})")
    
    # Handle different Indian number formats
    if phone.startswith('91') and len(phone) == 12:  # 919284967526
        phone = '+' + phone
        print(f"Applied rule 1: 91xxxxxxxxxx -> {phone}")
    elif phone.startswith('+91') and len(phone) == 13:  # +919284967526 (correct)
        print(f"Applied rule 2: Already correct -> {phone}")
    elif len(phone) == 10 and phone.isdigit():  # 9284967526 (any 10 digits)
        phone = '+91' + phone
        print(f"Applied rule 3: 10 digits -> {phone}")
    elif phone.startswith('+9') and len(phone) == 11:  # +9284967526 (missing 1)
        phone = '+91' + phone[2:]
        print(f"Applied rule 4: +9xxxxxxxxx -> {phone}")
    elif not phone.startswith('+') and len(phone) >= 10:
        phone = f"+91{phone}"  # Default to Indian format
        print(f"Applied rule 5: Default -> {phone}")
    else:
        print(f"No rule applied -> {phone}")
    
    return phone

# Test cases
test_cases = [
    "9284967526",      # 10 digits
    "+91 9284967526",  # With space
    "+919284967526",   # Correct format
    "+9284967526",     # Missing 1
    "919284967526",    # 12 digits with 91
]

print("Phone Number Normalization Test")
print("=" * 40)

for test_phone in test_cases:
    result = normalize_phone(test_phone)
    print(f"Final: '{test_phone}' -> '{result}'")
    print("-" * 40)