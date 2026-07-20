#!/usr/bin/env python3
"""
Complete Guide: How to Add New Businesses to the Database
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.crm_service import CRMService
from database.models import init_database

def method_1_add_via_api():
    """Method 1: Add business via API calls (Recommended for applications)"""
    print("🌐 Method 1: Adding Business via API")
    print("=" * 50)
    
    import requests
    
    # Example API calls to add a new business
    api_base = "http://localhost:8001"  # CRM API endpoint
    
    # 1. Create Account (Company)
    account_data = {
        "name": "New Electronics Store",
        "account_type": "customer",
        "industry": "Electronics Retail",
        "website": "https://newelectronics.com",
        "phone": "+1-555-0123",
        "email": "info@newelectronics.com",
        "billing_address": "123 Business St, City, State 12345",
        "city": "Business City",
        "state": "California",
        "country": "USA",
        "postal_code": "12345",
        "annual_revenue": 2000000.0,
        "employee_count": 25,
        "territory": "West Coast",
        "account_manager_id": "USER_001",
        "status": "active",
        "lifecycle_stage": "prospect",
        "notes": "New electronics retailer interested in bulk purchasing"
    }
    
    print("📋 Account Data to Send:")
    for key, value in account_data.items():
        print(f"   {key}: {value}")
    
    print("\n🔗 API Call Example:")
    print(f"POST {api_base}/accounts")
    print("Content-Type: application/json")
    print(f"Body: {account_data}")
    
    # Note: Actual API call would be:
    # response = requests.post(f"{api_base}/accounts", json=account_data)
    # account = response.json()
    
    print("\n✅ Expected Response:")
    print("   - Account ID: ACC_12345678")
    print("   - Status: Created successfully")
    print("   - Ready for contacts and opportunities")

def method_2_add_via_crm_service():
    """Method 2: Add business directly via CRM Service (Recommended for scripts)"""
    print("\n🔧 Method 2: Adding Business via CRM Service")
    print("=" * 50)
    
    try:
        with CRMService() as crm:
            # 1. Create Account
            account_data = {
                'name': 'Tech Startup Inc',
                'account_type': 'customer',
                'industry': 'Technology',
                'website': 'https://techstartup.com',
                'phone': '+1-555-0456',
                'email': 'contact@techstartup.com',
                'billing_address': '456 Innovation Ave, Tech City, CA 90210',
                'city': 'Tech City',
                'state': 'California',
                'country': 'USA',
                'postal_code': '90210',
                'annual_revenue': 500000.0,
                'employee_count': 10,
                'territory': 'West Coast',
                'account_manager_id': 'USER_001',
                'status': 'active',
                'lifecycle_stage': 'prospect',
                'created_by': 'admin',
                'notes': 'Fast-growing tech startup, high potential'
            }
            
            account = crm.create_account(account_data)
            print(f"✅ Account Created: {account['name']} (ID: {account['account_id']})")
            
            # 2. Add Primary Contact
            contact_data = {
                'account_id': account['account_id'],
                'first_name': 'John',
                'last_name': 'Doe',
                'title': 'CEO',
                'department': 'Executive',
                'email': 'john.doe@techstartup.com',
                'phone': '+1-555-0456',
                'mobile': '+1-555-0457',
                'contact_role': 'decision_maker',
                'is_primary': True,
                'status': 'active',
                'created_by': 'admin',
                'notes': 'Primary decision maker, very responsive'
            }
            
            contact = crm.create_contact(contact_data)
            print(f"✅ Contact Created: {contact['full_name']} (ID: {contact['contact_id']})")
            
            # 3. Create Initial Opportunity
            opportunity_data = {
                'account_id': account['account_id'],
                'primary_contact_id': contact['contact_id'],
                'name': 'Tech Startup Initial Purchase',
                'description': 'Initial bulk purchase of electronic components',
                'opportunity_type': 'new_business',
                'stage': 'prospecting',
                'probability': 25.0,
                'amount': 50000.0,
                'currency': 'USD',
                'expected_revenue': 50000.0,
                'close_date': datetime.now() + timedelta(days=60),
                'owner_id': 'USER_001',
                'requirements': 'Power banks, earbuds, chargers for retail',
                'products_interested': '["USR001", "USR002", "USR003"]',
                'created_by': 'admin',
                'notes': 'High potential first-time customer'
            }
            
            opportunity = crm.create_opportunity(opportunity_data)
            print(f"✅ Opportunity Created: {opportunity['name']} (ID: {opportunity['opportunity_id']})")
            
            # 4. Add Follow-up Task
            task_data = {
                'title': 'Follow up with Tech Startup CEO',
                'description': 'Schedule product demonstration and discuss pricing',
                'task_type': 'follow_up',
                'priority': 'high',
                'status': 'pending',
                'due_date': datetime.now() + timedelta(days=3),
                'assigned_to': 'USER_001',
                'account_id': account['account_id'],
                'opportunity_id': opportunity['opportunity_id'],
                'created_by': 'admin'
            }
            
            task = crm.create_task(task_data)
            print(f"✅ Task Created: {task['title']} (ID: {task['task_id']})")
            
            return account['account_id']
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def method_3_add_from_lead():
    """Method 3: Add business by converting a lead"""
    print("\n🎯 Method 3: Adding Business from Lead Conversion")
    print("=" * 50)
    
    try:
        with CRMService() as crm:
            # 1. Create Lead first
            lead_data = {
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'company': 'Mobile Accessories Plus',
                'title': 'Owner',
                'email': 'sarah@mobileplus.com',
                'phone': '+1-555-0789',
                'lead_source': 'website',
                'lead_status': 'new',
                'lead_stage': 'inquiry',
                'budget': 75000.0,
                'timeline': 'Q2 2024',
                'authority': 'decision_maker',
                'need': 'Looking for reliable supplier of mobile accessories',
                'assigned_to': 'USER_001',
                'territory': 'West Coast',
                'created_by': 'admin',
                'notes': 'Owns 3 mobile accessory stores, expanding to 5'
            }
            
            lead = crm.create_lead(lead_data)
            print(f"✅ Lead Created: {lead['full_name']} from {lead['company']} (ID: {lead['lead_id']})")
            
            # 2. Convert Lead to Account + Opportunity
            opportunity_data = {
                'name': 'Mobile Accessories Plus Partnership',
                'description': 'Supply mobile accessories to 5 retail locations',
                'opportunity_type': 'new_business',
                'stage': 'qualification',
                'probability': 50.0,
                'amount': 75000.0,
                'currency': 'USD',
                'expected_revenue': 75000.0,
                'close_date': datetime.now() + timedelta(days=45),
                'owner_id': 'USER_001',
                'requirements': 'Mobile accessories for 5 retail stores',
                'products_interested': '["USR004", "USR005", "USR006"]',
                'created_by': 'admin'
            }
            
            conversion_result = crm.convert_lead_to_opportunity(lead['lead_id'], opportunity_data)
            
            print(f"✅ Lead Converted Successfully:")
            print(f"   - Account: {conversion_result['account']['name']}")
            print(f"   - Contact: {conversion_result['contact']['full_name']}")
            print(f"   - Opportunity: {conversion_result['opportunity']['name']}")
            print(f"   - Lead Status: {conversion_result['lead']['lead_status']}")
            
            return conversion_result['account']['account_id']
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def method_4_bulk_import():
    """Method 4: Bulk import multiple businesses"""
    print("\n�� Method 4: Bulk Import Multiple Businesses")
    print("=" * 50)
    
    # Sample business data for bulk import
    businesses = [
        {
            'name': 'Electronics Warehouse',
            'account_type': 'distributor',
            'industry': 'Electronics Distribution',
            'phone': '+1-555-1001',
            'email': 'orders@electrowarehouse.com',
            'city': 'Los Angeles',
            'state': 'California',
            'annual_revenue': 10000000.0,
            'employee_count': 50,
            'territory': 'West Coast'
        },
        {
            'name': 'Gadget Galaxy',
            'account_type': 'customer',
            'industry': 'Electronics Retail',
            'phone': '+1-555-1002',
            'email': 'info@gadgetgalaxy.com',
            'city': 'San Francisco',
            'state': 'California',
            'annual_revenue': 3000000.0,
            'employee_count': 15,
            'territory': 'West Coast'
        },
        {
            'name': 'Tech Solutions Corp',
            'account_type': 'customer',
            'industry': 'Technology Services',
            'phone': '+1-555-1003',
            'email': 'contact@techsolutions.com',
            'city': 'Seattle',
            'state': 'Washington',
            'annual_revenue': 5000000.0,
            'employee_count': 30,
            'territory': 'Northwest'
        }
    ]
    
    try:
        with CRMService() as crm:
            created_accounts = []
            
            for business_data in businesses:
                # Add default values
                business_data.update({
                    'status': 'active',
                    'lifecycle_stage': 'prospect',
                    'created_by': 'bulk_import',
                    'country': 'USA'
                })
                
                account = crm.create_account(business_data)
                created_accounts.append(account)
                print(f"✅ Created: {account['name']} (ID: {account['account_id']})")
            
            print(f"\n🎉 Successfully imported {len(created_accounts)} businesses!")
            return created_accounts
            
    except Exception as e:
        print(f"❌ Bulk import error: {e}")
        return []

def method_5_dashboard_interface():
    """Method 5: Add business through dashboard interface"""
    print("\n🖥�� Method 5: Adding Business via Dashboard Interface")
    print("=" * 50)
    
    print("📋 Steps to add business via CRM Dashboard:")
    print("1. Open CRM Dashboard: http://localhost:8501")
    print("2. Navigate to 'Accounts' page")
    print("3. Click 'Add New Account' button")
    print("4. Fill in the form with business details:")
    print("   - Company Name")
    print("   - Account Type (customer/distributor/dealer)")
    print("   - Industry")
    print("   - Contact Information")
    print("   - Address Details")
    print("   - Financial Information")
    print("5. Click 'Save Account'")
    print("6. Add contacts and opportunities as needed")
    
    print("\n📝 Form Fields Available:")
    fields = [
        "Company Name*", "Account Type*", "Industry", "Website",
        "Phone", "Email", "Billing Address", "Shipping Address",
        "City", "State", "Country", "Postal Code",
        "Annual Revenue", "Employee Count", "Territory",
        "Account Manager", "Status", "Lifecycle Stage", "Notes"
    ]
    
    for field in fields:
        print(f"   - {field}")
    
    print("\n* = Required fields")

def method_6_csv_import():
    """Method 6: Import businesses from CSV file"""
    print("\n📄 Method 6: Import from CSV File")
    print("=" * 50)
    
    # Create sample CSV content
    csv_content = """name,account_type,industry,phone,email,city,state,annual_revenue,employee_count,territory
"Retail Electronics Co","customer","Electronics Retail","+1-555-2001","info@retailelectronics.com","Portland","Oregon",2500000,20,"Northwest"
"Component Suppliers Inc","supplier","Electronics Manufacturing","+1-555-2002","sales@componentsuppliers.com","Phoenix","Arizona",8000000,75,"Southwest"
"Mobile World","customer","Mobile Accessories","+1-555-2003","orders@mobileworld.com","Denver","Colorado",1500000,12,"Central"
"""
    
    # Save sample CSV
    csv_file = "sample_businesses.csv"
    with open(csv_file, 'w') as f:
        f.write(csv_content)
    
    print(f"📄 Created sample CSV file: {csv_file}")
    print("\n📋 CSV Format:")
    print(csv_content)
    
    # Import from CSV
    try:
        import pandas as pd
        
        df = pd.read_csv(csv_file)
        print(f"📊 Found {len(df)} businesses in CSV")
        
        with CRMService() as crm:
            imported_accounts = []
            
            for _, row in df.iterrows():
                business_data = {
                    'name': row['name'],
                    'account_type': row['account_type'],
                    'industry': row['industry'],
                    'phone': row['phone'],
                    'email': row['email'],
                    'city': row['city'],
                    'state': row['state'],
                    'annual_revenue': float(row['annual_revenue']),
                    'employee_count': int(row['employee_count']),
                    'territory': row['territory'],
                    'status': 'active',
                    'lifecycle_stage': 'prospect',
                    'country': 'USA',
                    'created_by': 'csv_import'
                }
                
                account = crm.create_account(business_data)
                imported_accounts.append(account)
                print(f"✅ Imported: {account['name']}")
            
            print(f"\n🎉 Successfully imported {len(imported_accounts)} businesses from CSV!")
            
            # Clean up
            os.remove(csv_file)
            return imported_accounts
            
    except Exception as e:
        print(f"❌ CSV import error: {e}")
        return []

def view_all_businesses():
    """View all businesses in the database"""
    print("\n👀 Current Businesses in Database")
    print("=" * 50)
    
    try:
        with CRMService() as crm:
            accounts = crm.get_accounts()
            
            if not accounts:
                print("📭 No businesses found in database")
                return
            
            print(f"📊 Found {len(accounts)} businesses:")
            print()
            
            for account in accounts:
                print(f"🏢 {account['name']}")
                print(f"   ID: {account['account_id']}")
                print(f"   Type: {account['account_type']}")
                print(f"   Industry: {account.get('industry', 'N/A')}")
                print(f"   Phone: {account.get('phone', 'N/A')}")
                print(f"   Email: {account.get('email', 'N/A')}")
                print(f"   Territory: {account.get('territory', 'N/A')}")
                print(f"   Status: {account['status']}")
                print(f"   Created: {account.get('created_at', 'N/A')}")
                print()
                
    except Exception as e:
        print(f"❌ Error viewing businesses: {e}")

def main():
    """Main function to demonstrate all methods"""
    print("🏢 Complete Guide: How to Add New Businesses to Database")
    print("=" * 80)
    
    # Initialize database
    print("🔧 Initializing database...")
    init_database()
    
    # Show current businesses
    view_all_businesses()
    
    # Demonstrate each method
    print("\n" + "=" * 80)
    print("🚀 DEMONSTRATION OF ALL METHODS")
    print("=" * 80)
    
    # Method 1: API (show example only)
    method_1_add_via_api()
    
    # Method 2: CRM Service (actually create)
    account_id_2 = method_2_add_via_crm_service()
    
    # Method 3: Lead conversion (actually create)
    account_id_3 = method_3_add_from_lead()
    
    # Method 4: Bulk import (actually create)
    bulk_accounts = method_4_bulk_import()
    
    # Method 5: Dashboard interface (show instructions)
    method_5_dashboard_interface()
    
    # Method 6: CSV import (actually create)
    csv_accounts = method_6_csv_import()
    
    # Show final results
    print("\n" + "=" * 80)
    print("📊 FINAL RESULTS")
    print("=" * 80)
    
    view_all_businesses()
    
    print("\n🎉 All methods demonstrated successfully!")
    print("\n📋 Summary of Methods:")
    print("1. ✅ API Calls - Best for applications")
    print("2. ✅ CRM Service - Best for scripts")
    print("3. ✅ Lead Conversion - Best for sales process")
    print("4. ✅ Bulk Import - Best for multiple businesses")
    print("5. ✅ Dashboard Interface - Best for manual entry")
    print("6. ✅ CSV Import - Best for data migration")

if __name__ == "__main__":
    main()