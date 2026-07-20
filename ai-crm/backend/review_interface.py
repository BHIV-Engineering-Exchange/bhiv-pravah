#!/usr/bin/env python3
"""
Human Review Interface for AI Agent Decisions
Usage: python review_interface.py
"""

import json
from human_review import review_system

def display_pending_reviews():
    """Display all pending reviews in a user-friendly format"""
    pending = review_system.get_pending_reviews()
    
    if not pending:
        print("✅ No pending reviews!")
        return False
    
    print(f"\n📋 {len(pending)} Pending Review(s):")
    print("=" * 60)
    
    for i, review in enumerate(pending, 1):
        print(f"\n{i}. Review ID: {review['review_id']}")
        print(f"   Type: {review['action_type']}")
        print(f"   Confidence: {review['confidence']:.2f}")
        print(f"   Time: {review['timestamp']}")
        print(f"   Agent Decision: {review['agent_decision']}")
        
        # Display relevant data
        data = review['data']
        if review['action_type'] == 'restock':
            print(f"   Product: {data.get('product_id', 'N/A')}")
            print(f"   Quantity: {data.get('quantity', 'N/A')}")
        elif review['action_type'] == 'chatbot_response':
            print(f"   User Query: {data.get('query', 'N/A')}")
        
        print("-" * 40)
    
    return True

def review_decision(review_id: str):
    """Handle human review of a specific decision"""
    pending = review_system.get_pending_reviews()
    review = next((r for r in pending if r['review_id'] == review_id), None)
    
    if not review:
        print(f"❌ Review {review_id} not found")
        return
    
    print(f"\n🔍 Reviewing: {review_id}")
    print(f"Action Type: {review['action_type']}")
    print(f"Confidence: {review['confidence']:.2f}")
    print(f"Agent Decision: {review['agent_decision']}")
    
    # Show detailed context
    data = review['data']
    if review['action_type'] == 'restock':
        print(f"Product ID: {data.get('product_id')}")
        print(f"Requested Quantity: {data.get('quantity')}")
        print(f"Reason: Return quantity exceeded threshold")
    
    print("\nOptions:")
    print("1. Approve")
    print("2. Reject")
    print("3. Skip")
    
    choice = input("\nYour decision (1/2/3): ").strip()
    
    if choice == "1":
        notes = input("Approval notes (optional): ").strip()
        review_system.approve_decision(review_id, notes)
    elif choice == "2":
        notes = input("Rejection reason: ").strip()
        review_system.reject_decision(review_id, notes)
    elif choice == "3":
        print("Skipped")
    else:
        print("Invalid choice")

def main():
    """Main review interface loop"""
    print("🤖 AI Agent Human Review Interface")
    print("Type 'help' for commands, 'quit' to exit")
    
    while True:
        print("\n" + "="*50)
        command = input("Command: ").strip().lower()
        
        if command in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            break
        
        elif command in ['help', 'h']:
            print("\nAvailable commands:")
            print("  list, l     - Show pending reviews")
            print("  review <id> - Review specific decision")
            print("  auto        - Auto-review all pending")
            print("  stats       - Show review statistics")
            print("  help, h     - Show this help")
            print("  quit, q     - Exit")
        
        elif command in ['list', 'l']:
            display_pending_reviews()
        
        elif command.startswith('review '):
            review_id = command.split(' ', 1)[1]
            review_decision(review_id)
        
        elif command == 'auto':
            auto_review_all()
        
        elif command == 'stats':
            show_statistics()
        
        else:
            print("Unknown command. Type 'help' for available commands.")

def auto_review_all():
    """Auto-review all pending items (for demo purposes)"""
    pending = review_system.get_pending_reviews()
    
    if not pending:
        print("✅ No pending reviews!")
        return
    
    print(f"🔄 Auto-reviewing {len(pending)} items...")
    
    for review in pending:
        # Simple auto-approval logic for demo
        if review['confidence'] > 0.5:
            review_system.approve_decision(review['review_id'], "Auto-approved: sufficient confidence")
        else:
            review_system.reject_decision(review['review_id'], "Auto-rejected: low confidence")
    
    print("✅ Auto-review complete!")

def show_statistics():
    """Show review statistics"""
    try:
        import pandas as pd
        df = pd.read_csv("data/review_log.csv")
        
        print("\n📊 Review Statistics:")
        print(f"Total reviews: {len(df)}")
        print(f"Approved: {len(df[df['human_decision'] == 'approved'])}")
        print(f"Rejected: {len(df[df['human_decision'] == 'rejected'])}")
        print(f"Average confidence: {df['confidence'].mean():.2f}")
        
    except FileNotFoundError:
        print("📊 No review history found")

if __name__ == "__main__":
    main()
