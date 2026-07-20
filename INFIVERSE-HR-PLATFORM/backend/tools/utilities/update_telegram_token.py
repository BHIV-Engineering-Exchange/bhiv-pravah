#!/usr/bin/env python3
"""
Update Telegram Bot Token
"""

import os
import httpx

def test_telegram_token(token):
    """Test if telegram token works"""
    try:
        response = httpx.get(f"https://api.telegram.org/bot{token}/getMe", timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                bot_info = data["result"]
                print(f"[SUCCESS] Bot found: @{bot_info.get('username')} ({bot_info.get('first_name')})")
                return True
        print(f"[ERROR] Token invalid: {response.status_code}")
        return False
    except Exception as e:
        print(f"[ERROR] Test failed: {str(e)}")
        return False

def main():
    print("Telegram Bot Token Updater")
    print("=" * 30)
    
    current_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    print(f"Current token: {current_token[:10]}...{current_token[-10:] if len(current_token) > 20 else current_token}")
    
    print("\nTo get a new bot token:")
    print("1. Open Telegram and search for @BotFather")
    print("2. Send /newbot command")
    print("3. Follow instructions to create bot")
    print("4. Copy the token and paste below")
    
    new_token = input("\nEnter new bot token (or press Enter to skip): ").strip()
    
    if new_token:
        print(f"\nTesting token: {new_token[:10]}...{new_token[-10:]}")
        if test_telegram_token(new_token):
            print(f"\n[SUCCESS] Token is valid!")
            print(f"Update your .env file:")
            print(f"TELEGRAM_BOT_TOKEN={new_token}")
        else:
            print(f"\n[ERROR] Token is invalid. Please check and try again.")
    else:
        print("\nSkipped token update.")

if __name__ == "__main__":
    main()