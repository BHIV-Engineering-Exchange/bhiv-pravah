import pyotp

# Use the hardcoded secret from auth.py
secret = "JBSWY3DPEHPK3PXP"
totp = pyotp.TOTP(secret)

# Generate current valid TOTP code
current_code = totp.now()
print(f"Current valid TOTP code: {current_code}")