#!/usr/bin/env python3
"""
Interactive Script to Add New Business to Database
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.crm_service import CRMService
from database.models import init_database

def get_user_input(prompt, default=None, required=True):
    """Get user input with optional default value"""
    if default:
        prompt += f" [{default}]"
    prompt += ": "
    
    value = input(prompt).strip()
    
    if not value and default:
        return default
    elif not value and required:
        print("❌ This field is required!")
        return get_user_input(prompt.replace(f" [{default}]", "").replace(": ", ""), default, required)
    
    return value if value else None

def get_numeric_input(prompt, default=None, required=False):
    """Get numeric input from user"""
    while True:
        try:
            value = get_user_input(prompt, default, required)
            if value is None:
                return None
            return float(value)
        except ValueError:
            print("❌ Please enter a valid number!")

def add_business_interactive():
    """Interactive function to add a new business"""
    print("🏢 Add New Business to Database")
    print("=" * 40)
    print("Fill in the business information (press Enter to skip optional fields)")
    print()
    
    # Required fields
    name = get_user_input("Company Name", required=True)
    
    # Account type selection
    print("\nAccount Types:")
    print("1. Customer")
    print("2. Distributor") 
    print("3. Dealer")
    print("4. Supplier")
    print("5. Partner")
    
    account_type_map = {
        '1': 'customer',
        '2': 'distributor', 
        '3': 'dealer',
        '4': 'supplier',
        '5': 'partner'
    }
    
    while True:
        choice = get_user_input("Select Account Type (1-5)", "1", True)
        if choice in account_type_map:
            account_type = account_type_map[choice]
            break
        print("❌ Please select 1-5")
    
    # Optional fields
    industry = get_user_input("Industry", required=False)
    website = get_user_input("Website", required=False)
    phone = get_user_input("Phone", required=False)
    email = get_user_input("Email", required=False)
    
    # Address information
    print("\n📍 Address Information:")
    billing_address = get_user_input("Billing Address", required=False)
    city = get_user_input("City", required=False)
    state = get_user_input("State", required=False)
    country = get_user_input("Country", "USA", required=False)
    postal_code = get_user_input("Postal Code", required=False)
    
    # Business details
    print("\n💼 Business Details:")
    annual_revenue = get_numeric_input("Annual Revenue ($)", required=False)
    employee_count = get_numeric_input("Employee Count", required=False)
    if employee_count:
        employee_count = int(employee_count)
    
    # Territory selection
    print("\nTerritories:")
    print("1. West Coast")
    print("2. East Coast")
    print("3. Midwest")
    print("4. Southwest")
    print("5. Northwest")
    print("6. Central")
    
    territory_map = {
        '1': 'West Coast',
        '2': 'East Coast',
        '3': 'Midwest',
        '4': 'Southwest',
        '5': 'Northwest',
        '6': 'Central'
    }
    
    territory_choice = get_user_input("Select Territory (1-6)", "1", required=False)
    territory = territory_map.get(territory_choice, 'West Coast')
    
    # Account manager
    print("\nAccount Managers:")
    print("1. USER_001 (Sales Rep 1)")
    print("2. USER_002 (Sales Rep 2)")
    
    manager_choice = get_user_input("Select Account Manager (1-2)", "1", required=False)
    account_manager_id = "USER_001" if manager_choice == "1" else "USER_002"
    
    # Notes
    notes = get_user_input("Notes/Comments", required=False)
    
    # Prepare data
    business_data = {
        'name': name,
        'account_type': account_type,
        'industry': industry,
        'website': website,
        'phone': phone,
        'email': email,
        'billing_address': billing_address,
        'city': city,
        'state': state,
        'country': country,
        'postal_code': postal_code,
        'annual_revenue': annual_revenue,
        'employee_count': employee_count,
        'territory': territory,
        'account_manager_id': account_manager_id,
        'status': 'active',
        'lifecycle_stage': 'prospect',
        'created_by': 'interactive_script',
        'notes': notes
    }
    
    # Remove None values
    business_data = {k: v for k, v in business_data.items() if v is not None}
    
    # Confirm before saving
    print("\n" + "=" * 40)
    print("📋 Business Information Summary:")
    print("=" * 40)
    
    for key, value in business_data.items():
        if key != 'created_by':  # Skip internal field
            display_key = key.replace('_', ' ').title()
            print(f"{display_key}: {value}")
    
    print("\n" + "=" * 40)
    confirm = get_user_input("Save this business? (y/n)", "y", True).lower()
    
    if confirm not in ['y', 'yes']:
        print("❌ Business not saved.")
        return None
    
    # Save to database
    try:
        with CRMService() as crm:
            account = crm.create_account(business_data)
            
            print("\n✅ Business saved successfully!")
            print(f"   Company: {account['name']}")
            print(f"   Account ID: {account['account_id']}")
            print(f"   Type: {account['account_type']}")
            print(f"   Territory: {account.get('territory', 'N/A')}")
            
            # Ask if they want to add a contact
            add_contact = get_user_input("\nAdd a primary contact for this business? (y/n)", "y", True).lower()
            
            if add_contact in ['y', 'yes']:
                contact_id = add_contact_interactive(account['account_id'], account['name'])
                if contact_id:
                    print(f"✅ Contact added successfully!")
            
            # Ask if they want to create an opportunity
            add_opportunity = get_user_input("\nCreate an initial opportunity? (y/n)", "n", True).lower()
            
            if add_opportunity in ['y', 'yes']:
                opportunity_id = add_opportunity_interactive(account['account_id'], account['name'])
                if opportunity_id:
                    print(f"✅ Opportunity created successfully!")
            
            return account['account_id']
            
    except Exception as e:
        print(f"❌ Error saving business: {e}")
        return None

def add_contact_interactive(account_id, company_name):
    """Add a contact for the business"""
    print(f"\n👤 Add Contact for {company_name}")
    print("=" * 40)
    
    first_name = get_user_input("First Name", required=True)
    last_name = get_user_input("Last Name", required=True)
    title = get_user_input("Job Title", required=False)
    department = get_user_input("Department", required=False)
    email = get_user_input("Email", required=False)
    phone = get_user_input("Phone", required=False)
    mobile = get_user_input("Mobile", required=False)
    
    # Contact role
    print("\nContact Roles:")
    print("1. Decision Maker")
    print("2. Influencer")
    print("3. Contact")
    print("4. Distributor")
    print("5. Dealer")
    
    role_map = {
        '1': 'decision_maker',
        '2': 'influencer',
        '3': 'contact',
        '4': 'distributor',
        '5': 'dealer'
    }
    
    role_choice = get_user_input("Select Contact Role (1-5)", "1", True)
    contact_role = role_map.get(role_choice, 'contact')
    
    is_primary = get_user_input("Is this the primary contact? (y/n)", "y", True).lower() in ['y', 'yes']
    
    contact_notes = get_user_input("Notes about this contact", required=False)
    
    contact_data = {
        'account_id': account_id,
        'first_name': first_name,
        'last_name': last_name,
        'title': title,
        'department': department,
        'email': email,
        'phone': phone,
        'mobile': mobile,
        'contact_role': contact_role,
        'is_primary': is_primary,
        'status': 'active',
        'created_by': 'interactive_script',
        'notes': contact_notes
    }
    
    # Remove None values
    contact_data = {k: v for k, v in contact_data.items() if v is not None}
    
    try:
        with CRMService() as crm:
            contact = crm.create_contact(contact_data)
            print(f"✅ Contact created: {contact['full_name']} ({contact['contact_role']})")
            return contact['contact_id']
    except Exception as e:
        print(f"❌ Error creating contact: {e}")
        return None

def add_opportunity_interactive(account_id, company_name):
    """Add an opportunity for the business"""
    print(f"\n💰 Add Opportunity for {company_name}")
    print("=" * 40)
    
    opp_name = get_user_input("Opportunity Name", f"{company_name} - Initial Purchase", True)
    description = get_user_input("Description", required=False)
    
    # Opportunity type
    print("\nOpportunity Types:")
    print("1. New Business")
    print("2. Existing Business")
    print("3. Renewal")
    
    type_map = {
        '1': 'new_business',
        '2': 'existing_business',
        '3': 'renewal'
    }
    
    type_choice = get_user_input("Select Type (1-3)", "1", True)
    opportunity_type = type_map.get(type_choice, 'new_business')
    
    # Stage
    print("\nSales Stages:")
    print("1. Prospecting")
    print("2. Qualification")
    print("3. Proposal")
    print("4. Negotiation")
    
    stage_map = {
        '1': 'prospecting',
        '2': 'qualification',
        '3': 'proposal',
        '4': 'negotiation'
    }
    
    stage_choice = get_user_input("Select Stage (1-4)", "1", True)
    stage = stage_map.get(stage_choice, 'prospecting')
    
    # Probability based on stage
    probability_map = {
        'prospecting': 25.0,
        'qualification': 50.0,
        'proposal': 75.0,
        'negotiation': 90.0
    }
    
    default_probability = probability_map.get(stage, 25.0)
    probability = get_numeric_input(f"Probability %", default_probability, False) or default_probability
    
    amount = get_numeric_input("Deal Amount ($)", required=False)
    
    # Close date
    days_to_close = get_numeric_input("Days to expected close", 60, False) or 60
    close_date = datetime.now() + timedelta(days=int(days_to_close))
    
    requirements = get_user_input("Customer Requirements", required=False)
    products_interested = get_user_input("Products of Interest", required=False)
    competitors = get_user_input("Known Competitors", required=False)
    risks = get_user_input("Risks/Concerns", required=False)
    opp_notes = get_user_input("Opportunity Notes", required=False)
    
    opportunity_data = {
        'account_id': account_id,
        'name': opp_name,
        'description': description,
        'opportunity_type': opportunity_type,
        'stage': stage,
        'probability': probability,
        'amount': amount,
        'currency': 'USD',
        'expected_revenue': amount,
        'close_date': close_date,
        'owner_id': 'USER_001',
        'requirements': requirements,
        'products_interested': products_interested,
        'competitors': competitors,
        'risks': risks,
        'created_by': 'interactive_script',
        'notes': opp_notes
    }
    
    # Remove None values
    opportunity_data = {k: v for k, v in opportunity_data.items() if v is not None}
    
    try:
        with CRMService() as crm:
            opportunity = crm.create_opportunity(opportunity_data)
            print(f"✅ Opportunity created: {opportunity['name']}")
            print(f"   Stage: {opportunity['stage']}")
            print(f"   Probability: {opportunity['probability']}%")
            if opportunity.get('amount'):
                print(f"   Amount: ${opportunity['amount']:,.2f}")
            return opportunity['opportunity_id']
    except Exception as e:
        print(f"❌ Error creating opportunity: {e}")
        return None

def main():
    """Main function"""
    print("🚀 Interactive Business Addition Tool")
    print("=" * 50)
    
    # Initialize database
    print("🔧 Initializing database...")
    init_database()
    
    while True:
        print("\n" + "=" * 50)
        print("🏢 Business Management Menu")
        print("=" * 50)
        print("1. Add New Business")
        print("2. View All Businesses")
        print("3. Exit")
        
        choice = get_user_input("Select option (1-3)", "1", True)
        
        if choice == "1":
            account_id = add_business_interactive()
            if account_id:
                print(f"\n🎉 Business added successfully! Account ID: {account_id}")
        
        elif choice == "2":
            print("\n👀 All Businesses in Database:")
            print("=" * 40)
            
            try:
                with CRMService() as crm:
                    accounts = crm.get_accounts()
                    
                    if not accounts:
                        print("📭 No businesses found")
                    else:
                        for i, account in enumerate(accounts, 1):
                            print(f"{i}. {account['name']}")
                            print(f"   ID: {account['account_id']}")
                            print(f"   Type: {account['account_type']}")
                            print(f"   Industry: {account.get('industry', 'N/A')}")
                            print(f"   Territory: {account.get('territory', 'N/A')}")
                            print()
            except Exception as e:
                print(f"❌ Error viewing businesses: {e}")
        
        elif choice == "3":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please select 1-3.")

if __name__ == "__main__":
    main()