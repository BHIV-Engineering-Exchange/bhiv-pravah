#!/usr/bin/env python3
"""
Smart Logistics Chatbot with Live Data Integration
Connects to live database for real-time order and inventory queries
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

class SmartChatbot:
    """Smart chatbot with live data integration"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.conversation_history = []
    
    def get_live_data(self):
        """Get live data from database"""
        try:
            from database.service import DatabaseService
            with DatabaseService() as db_service:
                return {
                    'orders': db_service.get_orders()[:20],  # Last 20 orders
                    'inventory': db_service.get_inventory()[:30],  # All inventory
                    'shipments': db_service.get_shipments()[:15],  # Last 15 shipments
                    'low_stock': db_service.get_low_stock_items()
                }
        except Exception as e:
            print(f"Error getting live data: {e}")
            return {
                'orders': [],
                'inventory': [],
                'shipments': [],
                'low_stock': []
            }
    
    def create_system_prompt(self, live_data):
        """Create system prompt with live data"""
        return f"""
You are a helpful AI logistics assistant for an inventory management system.

CURRENT LIVE DATA (Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):

ORDERS ({len(live_data['orders'])} recent orders):
{json.dumps(live_data['orders'][:10], indent=2)}

INVENTORY ({len(live_data['inventory'])} products):
{json.dumps(live_data['inventory'][:15], indent=2)}

SHIPMENTS ({len(live_data['shipments'])} recent shipments):
{json.dumps(live_data['shipments'][:10], indent=2)}

LOW STOCK ALERTS ({len(live_data['low_stock'])} items):
{json.dumps(live_data['low_stock'], indent=2)}

CAPABILITIES:
- Check order status by Order ID
- Check product inventory levels
- Check shipment tracking status
- Provide stock alerts and reorder recommendations
- Answer general logistics questions

INSTRUCTIONS:
- Search the live data to answer user questions
- If order/product not found, politely say so
- Provide specific, helpful information
- Be concise but informative
- Use emojis for better user experience
"""
    
    def ask_gpt(self, user_message):
        """Send message to OpenAI with live data context"""
        try:
            # Get fresh live data for each query
            live_data = self.get_live_data()
            system_prompt = self.create_system_prompt(live_data)
            
            # Build conversation with system prompt
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history (last 5 exchanges)
            messages.extend(self.conversation_history[-10:])
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.3,
                max_tokens=500
            )
            
            bot_response = response.choices[0].message.content
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            
            return bot_response
            
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
    
    def quick_query(self, query):
        """Quick query without conversation history"""
        try:
            live_data = self.get_live_data()
            system_prompt = self.create_system_prompt(live_data)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error: {str(e)}"

def run_smart_chat():
    """Run the interactive smart chat loop"""
    print("🤖 Smart Logistics Chatbot is running! Type 'exit' to quit.")
    print("💡 Try asking: 'What orders are pending?', 'Check inventory for USR001', 'Any low stock alerts?'")
    print("-" * 60)
    
    chatbot = SmartChatbot()
    
    while True:
        user_input = input("\n🧑 You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("👋 Goodbye! Thanks for using the logistics chatbot.")
            break
        
        if user_input.strip():
            print("🤖 Bot: ", end="")
            answer = chatbot.ask_gpt(user_input)
            print(answer)
        else:
            print("Please enter a question or type 'exit' to quit.")

# API endpoint for chatbot
def get_chatbot_response(query):
    """API endpoint for getting chatbot responses"""
    chatbot = SmartChatbot()
    return chatbot.quick_query(query)

if __name__ == "__main__":
    run_smart_chat()
    run.api()
    