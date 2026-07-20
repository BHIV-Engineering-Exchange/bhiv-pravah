#!/usr/bin/env python3
"""
Supplier Management Dashboard
Add, edit, and manage suppliers through a web interface
"""

import streamlit as st
import pandas as pd
import requests
from database.service import DatabaseService
from database.models import SessionLocal, Supplier
from datetime import datetime
import json

# Page configuration
st.set_page_config(
    page_title="Supplier Management",
    page_icon="🏭",
    layout="wide"
)

st.title("🏭 Supplier Management Dashboard")

# Initialize session state
if 'suppliers_data' not in st.session_state:
    st.session_state.suppliers_data = []

def load_suppliers():
    """Load suppliers from database"""
    try:
        with DatabaseService() as db_service:
            suppliers = db_service.get_suppliers()
        return suppliers
    except Exception as e:
        st.error(f"Error loading suppliers: {e}")
        return []

def create_supplier(supplier_data):
    """Create new supplier in database"""
    try:
        db = SessionLocal()
        
        # Check if supplier_id already exists
        existing = db.query(Supplier).filter(Supplier.supplier_id == supplier_data['supplier_id']).first()
        if existing:
            db.close()
            return {"success": False, "error": "Supplier ID already exists"}
        
        # Create new supplier
        new_supplier = Supplier(
            supplier_id=supplier_data['supplier_id'],
            name=supplier_data['name'],
            contact_email=supplier_data.get('contact_email'),
            contact_phone=supplier_data.get('contact_phone'),
            api_endpoint=supplier_data.get('api_endpoint'),
            lead_time_days=supplier_data.get('lead_time_days', 7),
            minimum_order=supplier_data.get('minimum_order', 1),
            is_active=supplier_data.get('is_active', True)
        )
        
        db.add(new_supplier)
        db.commit()
        
        result = {
            'supplier_id': new_supplier.supplier_id,
            'name': new_supplier.name,
            'contact_email': new_supplier.contact_email,
            'contact_phone': new_supplier.contact_phone,
            'lead_time_days': new_supplier.lead_time_days,
            'minimum_order': new_supplier.minimum_order,
            'is_active': new_supplier.is_active
        }
        
        db.close()
        return {"success": True, "supplier": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_supplier(supplier_id, supplier_data):
    """Update existing supplier"""
    try:
        db = SessionLocal()
        
        supplier = db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
        if not supplier:
            db.close()
            return {"success": False, "error": "Supplier not found"}
        
        # Update fields
        supplier.name = supplier_data.get('name', supplier.name)
        supplier.contact_email = supplier_data.get('contact_email', supplier.contact_email)
        supplier.contact_phone = supplier_data.get('contact_phone', supplier.contact_phone)
        supplier.api_endpoint = supplier_data.get('api_endpoint', supplier.api_endpoint)
        supplier.lead_time_days = supplier_data.get('lead_time_days', supplier.lead_time_days)
        supplier.minimum_order = supplier_data.get('minimum_order', supplier.minimum_order)
        supplier.is_active = supplier_data.get('is_active', supplier.is_active)
        
        db.commit()
        
        result = {
            'supplier_id': supplier.supplier_id,
            'name': supplier.name,
            'contact_email': supplier.contact_email,
            'contact_phone': supplier.contact_phone,
            'lead_time_days': supplier.lead_time_days,
            'minimum_order': supplier.minimum_order,
            'is_active': supplier.is_active
        }
        
        db.close()
        return {"success": True, "supplier": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# Main dashboard
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Current Suppliers")
    
    # Load and display suppliers
    suppliers = load_suppliers()
    
    if suppliers:
        suppliers_df = pd.DataFrame(suppliers)
        
        # Display suppliers table
        st.table(suppliers_df)
        
        # Edit existing supplier
        st.subheader("✏️ Edit Supplier")
        selected_supplier_id = st.selectbox(
            "Select supplier to edit:",
            options=[s['supplier_id'] for s in suppliers],
            format_func=lambda x: f"{x} - {next((s['name'] for s in suppliers if s['supplier_id'] == x), '')}"
        )
        
        if selected_supplier_id:
            selected_supplier = next((s for s in suppliers if s['supplier_id'] == selected_supplier_id), None)
            
            if selected_supplier:
                with st.form("edit_supplier_form"):
                    edit_name = st.text_input("Name", value=selected_supplier['name'])
                    edit_email = st.text_input("Contact Email", value=selected_supplier['contact_email'] or "")
                    edit_phone = st.text_input("Contact Phone", value=selected_supplier['contact_phone'] or "")
                    edit_api = st.text_input("API Endpoint", value=selected_supplier.get('api_endpoint', '') or "")
                    edit_lead_time = st.number_input("Lead Time (days)", value=selected_supplier['lead_time_days'], min_value=1, max_value=365)
                    edit_min_order = st.number_input("Minimum Order", value=selected_supplier['minimum_order'], min_value=1)
                    edit_active = st.checkbox("Active", value=selected_supplier['is_active'])
                    
                    if st.form_submit_button("💾 Update Supplier"):
                        update_data = {
                            'name': edit_name,
                            'contact_email': edit_email,
                            'contact_phone': edit_phone,
                            'api_endpoint': edit_api,
                            'lead_time_days': edit_lead_time,
                            'minimum_order': edit_min_order,
                            'is_active': edit_active
                        }
                        
                        result = update_supplier(selected_supplier_id, update_data)
                        
                        if result['success']:
                            st.success(f"✅ Supplier {selected_supplier_id} updated successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error updating supplier: {result['error']}")
    
    else:
        st.info("No suppliers found. Add your first supplier using the form on the right.")

with col2:
    st.subheader("➕ Add New Supplier")
    
    with st.form("add_supplier_form"):
        supplier_id = st.text_input("Supplier ID*", placeholder="e.g., SUPPLIER_004")
        name = st.text_input("Company Name*", placeholder="e.g., ABC Components Ltd.")
        email = st.text_input("Contact Email", placeholder="orders@company.com")
        phone = st.text_input("Contact Phone", placeholder="+1-555-0123")
        api_endpoint = st.text_input("API Endpoint", placeholder="http://supplier.com/api")
        lead_time = st.number_input("Lead Time (days)", value=7, min_value=1, max_value=365)
        min_order = st.number_input("Minimum Order Quantity", value=1, min_value=1)
        is_active = st.checkbox("Active", value=True)
        
        if st.form_submit_button("➕ Add Supplier"):
            if supplier_id and name:
                new_supplier_data = {
                    'supplier_id': supplier_id.strip().upper(),
                    'name': name.strip(),
                    'contact_email': email.strip() if email else None,
                    'contact_phone': phone.strip() if phone else None,
                    'api_endpoint': api_endpoint.strip() if api_endpoint else None,
                    'lead_time_days': lead_time,
                    'minimum_order': min_order,
                    'is_active': is_active
                }
                
                result = create_supplier(new_supplier_data)
                
                if result['success']:
                    st.success(f"✅ Supplier {supplier_id} created successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Error creating supplier: {result['error']}")
            else:
                st.error("❌ Please fill in required fields (Supplier ID and Company Name)")

# Statistics section
st.markdown("---")
st.subheader("📊 Supplier Statistics")

if suppliers:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Suppliers", len(suppliers))
    
    with col2:
        active_count = len([s for s in suppliers if s['is_active']])
        st.metric("Active Suppliers", active_count)
    
    with col3:
        avg_lead_time = sum(s['lead_time_days'] for s in suppliers) / len(suppliers)
        st.metric("Avg Lead Time", f"{avg_lead_time:.1f} days")
    
    with col4:
        suppliers_with_email = len([s for s in suppliers if s['contact_email']])
        st.metric("With Email Contact", suppliers_with_email)

# Refresh button
if st.button("🔄 Refresh Data"):
    st.rerun()

# Export functionality
st.markdown("---")
st.subheader("📤 Export/Import")

col1, col2 = st.columns(2)

with col1:
    if st.button("📁 Export Suppliers to JSON"):
        suppliers_json = json.dumps(suppliers, indent=2, default=str)
        st.download_button(
            label="💾 Download suppliers.json",
            data=suppliers_json,
            file_name=f"suppliers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

with col2:
    uploaded_file = st.file_uploader("📂 Import Suppliers from JSON", type=['json'])
    if uploaded_file is not None:
        try:
            import_data = json.load(uploaded_file)
            st.json(import_data)
            st.info("Import functionality can be implemented based on your needs.")
        except Exception as e:
            st.error(f"Error reading file: {e}")