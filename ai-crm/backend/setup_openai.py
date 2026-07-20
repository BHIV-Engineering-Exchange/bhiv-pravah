#!/usr/bin/env python3
"""
Setup script for OpenAI integration in CRM system
"""

import os
import sys

def setup_openai():
    """Setup OpenAI integration"""
    print("🤖 OpenAI Integration Setup")
    print("=" * 50)
    
    # Check if already configured
    current_key = os.getenv('OPENAI_API_KEY')
    if current_key:
        masked_key = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else "****"
        print(f"✅ OpenAI API Key already configured: {masked_key}")
        
        choice = input("\nDo you want to update it? (y/N): ").lower().strip()
        if choice != 'y':
            print("Keeping existing configuration.")
            return
    
    print("\n📝 To get your OpenAI API key:")
    print("1. Go to https://platform.openai.com/api-keys")
    print("2. Create a new API key")
    print("3. Copy the key (starts with 'sk-')")
    
    api_key = input("\n🔑 Enter your OpenAI API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided. Exiting.")
        return False
    
    if not api_key.startswith('sk-'):
        print("⚠️  Warning: API key should start with 'sk-'")
        choice = input("Continue anyway? (y/N): ").lower().strip()
        if choice != 'y':
            return False
    
    # For this session
    os.environ['OPENAI_API_KEY'] = api_key
    
    # Create/update .env file
    env_file = '.env'
    env_lines = []
    
    # Read existing .env file
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            env_lines = f.readlines()
    
    # Remove existing OPENAI_API_KEY line
    env_lines = [line for line in env_lines if not line.startswith('OPENAI_API_KEY')]
    
    # Add new OPENAI_API_KEY
    env_lines.append(f'OPENAI_API_KEY={api_key}\n')
    
    # Write back to .env file
    with open(env_file, 'w') as f:
        f.writelines(env_lines)
    
    print(f"✅ OpenAI API key saved to {env_file}")
    
    # Test the API key
    print("\n🧪 Testing OpenAI connection...")
    try:
        import openai
        
        # Set the API key
        openai.api_key = api_key
        
        # Simple test
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'Hello from CRM system!'"}
            ],
            max_tokens=20
        )
        
        test_response = response.choices[0].message.content.strip()
        print(f"✅ OpenAI API test successful!")
        print(f"🤖 Test response: {test_response}")
        
        return True
        
    except ImportError:
        print("❌ OpenAI package not installed.")
        print("💡 Install with: pip install openai")
        return False
        
    except Exception as e:
        print(f"❌ OpenAI API test failed: {str(e)}")
        print("💡 Please check your API key and try again.")
        return False

def show_usage_instructions():
    """Show instructions for using OpenAI integration"""
    print("\n" + "=" * 50)
    print("🎯 How to use OpenAI in CRM Dashboard:")
    print("=" * 50)
    print("""
1. 📊 Go to CRM Dashboard: http://localhost:8501
2. 🧠 Navigate to "Natural Language Query" page
3. 💬 Ask questions like:
   • "Show me all opportunities closing this month"
   • "What are the pending tasks for TechCorp?"
   • "List all leads from trade shows not yet converted"
   • "Account summary for TechCorp Industries"
   • "Pipeline analysis"
   
4. 🤖 The AI will understand your question and provide relevant data!
""")
    
    print("🔄 Restart your CRM system to ensure the API key is loaded:")
    print("   • Stop current system (Ctrl+C)")
    print("   • Run: python3 start_crm_system.py")

if __name__ == "__main__":
    print("Starting OpenAI setup...")
    
    success = setup_openai()
    
    if success:
        show_usage_instructions()
        print("\n🎉 OpenAI integration setup complete!")
    else:
        print("\n❌ OpenAI setup failed. Please try again.")
    
    sys.exit(0 if success else 1)