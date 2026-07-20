#!/usr/bin/env python3
"""
Enhanced Inventory Management Dashboard
With sidebar editing and supplier communication
"""

import streamlit as st
import pandas as pd
from inventory_manager import InventoryManager
from user_product_models import USER_PRODUCT_CATALOG
from database.models import SessionLocal, Supplier
import plotly.express as px
from datetime import datetime
import json

# Page configuration
st.set_page_config(
    page_title="Enhanced Inventory Management",
    page_icon="📦",
    layout="wide"
)

# Initialize session state
if 'selected_product_id' not in st.session_state:
    st.session_state.selected_product_id = None
if 'supplier_messages' not in st.session_state:
    st.session_state.supplier_messages = []

def get_supplier_info(supplier_id):
    """Get supplier information from database"""
    db = SessionLocal()
    try:
        supplier = db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
        if supplier:
            return {
                'supplier_id': supplier.supplier_id,
                'name': supplier.name,
                'email': supplier.contact_email,
                'phone': supplier.contact_phone,
                'lead_time': supplier.lead_time_days,
                'minimum_order': supplier.minimum_order
            }
    finally:
        db.close()
    return None

def send_supplier_message(supplier_id, message_type, product_info, quantity, notes=""):
    """Simulate sending message to supplier"""
    supplier = get_supplier_info(supplier_id)
    if not supplier:
        return False
    
    message = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'supplier': supplier,
        'message_type': message_type,
        'product_info': product_info,
        'quantity': quantity,
        'notes': notes,
        'status': 'Sent'
    }
    
    st.session_state.supplier_messages.append(message)
    return True

@st.cache_data
def load_inventory_data():
    with InventoryManager() as inv_mgr:
        return inv_mgr.get_inventory_report()

# Sidebar for Quick Inventory Editing
st.sidebar.title("🔧 Quick Inventory Editor")

# Product selector in sidebar
product_options = {f"{p.product_id} - {p.name[:30]}...": p.product_id for p in USER_PRODUCT_CATALOG}
selected_product_key = st.sidebar.selectbox(
    "Select Product to Edit", 
    options=list(product_options.keys()),
    key="sidebar_product_selector"
)
selected_product_id = product_options[selected_product_key]

# Get current product info
with InventoryManager() as inv_mgr:
    current_inv = inv_mgr.get_current_inventory(selected_product_id)
    current_stock = current_inv.current_stock if current_inv else 0
    reorder_point = current_inv.reorder_point if current_inv else 0
    supplier_id = current_inv.supplier_id if current_inv else "SUPPLIER_001"

# Get product details
selected_product = next((p for p in USER_PRODUCT_CATALOG if p.product_id == selected_product_id), None)

if selected_product:
    st.sidebar.markdown(f"### 📦 {selected_product.name[:25]}...")
    st.sidebar.markdown(f"**Product ID:** {selected_product_id}")
    st.sidebar.markdown(f"**Current Stock:** {current_stock}")
    st.sidebar.markdown(f"**Reorder Point:** {reorder_point}")
    
    # Stock status indicator
    if current_stock <= reorder_point:
        st.sidebar.error("🔴 LOW STOCK ALERT!")
    else:
        st.sidebar.success("🟢 Stock OK")
    
    # Quick edit section
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚡ Quick Edit")
    
    # Quick adjustment buttons
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("➕ Add 10", key="add_10"):
            with InventoryManager() as inv_mgr:
                result = inv_mgr.update_inventory(selected_product_id, 10, "Quick Add: +10 units")
                if result['success']:
                    st.sidebar.success("Added 10 units!")
                    st.rerun()
    
    with col2:
        if st.button("➖ Remove 5", key="remove_5"):
            with InventoryManager() as inv_mgr:
                result = inv_mgr.update_inventory(selected_product_id, -5, "Quick Remove: -5 units")
                if result['success']:
                    st.sidebar.success("Removed 5 units!")
                    st.rerun()
    
    # Custom adjustment
    st.sidebar.markdown("**Custom Adjustment:**")
    custom_change = st.sidebar.number_input("Quantity Change", value=0, key="custom_change")
    custom_reason = st.sidebar.text_input("Reason", value="Manual adjustment", key="custom_reason")
    
    if st.sidebar.button("Apply Change", type="primary", key="apply_custom"):
        if custom_change != 0:
            with InventoryManager() as inv_mgr:
                result = inv_mgr.update_inventory(selected_product_id, custom_change, custom_reason)
                if result['success']:
                    st.sidebar.success(f"Updated: {result['old_stock']} → {result['new_stock']}")
                    st.rerun()
                else:
                    st.sidebar.error(f"Error: {result['error']}")
    
    # Set absolute quantity
    st.sidebar.markdown("**Set Exact Quantity:**")
    new_quantity = st.sidebar.number_input("New Total", value=current_stock, min_value=0, key="new_total")
    
    if st.sidebar.button("Set Quantity", key="set_quantity"):
        with InventoryManager() as inv_mgr:
            result = inv_mgr.set_absolute_quantity(selected_product_id, new_quantity, "Set absolute quantity")
            if result['success']:
                st.sidebar.success(f"Set to {new_quantity} units!")
                st.rerun()
            else:
                st.sidebar.error(f"Error: {result['error']}")

# Supplier Communication Section
st.sidebar.markdown("---")
st.sidebar.markdown("### 📞 Supplier Communication")

supplier_info = get_supplier_info(supplier_id)
if supplier_info:
    st.sidebar.markdown(f"**Supplier:** {supplier_info['name']}")
    st.sidebar.markdown(f"**Email:** {supplier_info['email']}")
    st.sidebar.markdown(f"**Phone:** {supplier_info['phone']}")
    st.sidebar.markdown(f"**Lead Time:** {supplier_info['lead_time']} days")
    st.sidebar.markdown(f"**Min Order:** {supplier_info['minimum_order']} units")
    
    # Quick reorder button
    if current_stock <= reorder_point:
        st.sidebar.error("⚠️ Reorder Required!")
        reorder_qty = st.sidebar.number_input("Reorder Quantity", value=50, min_value=supplier_info['minimum_order'])
        
        if st.sidebar.button("📧 Send Reorder Request", type="primary"):
            success = send_supplier_message(
                supplier_id, 
                "Reorder Request",
                {
                    'product_id': selected_product_id,
                    'product_name': selected_product.name,
                    'current_stock': current_stock,
                    'reorder_point': reorder_point
                },
                reorder_qty,
                f"Urgent reorder required. Current stock: {current_stock}, Reorder point: {reorder_point}"
            )
            if success:
                st.sidebar.success("Reorder request sent!")
                st.rerun()
    
    # Custom message
    st.sidebar.markdown("**Send Custom Message:**")
    message_type = st.sidebar.selectbox("Message Type", ["Stock Inquiry", "Quality Issue", "Delivery Update", "General"])
    message_notes = st.sidebar.text_area("Message", placeholder="Enter your message to supplier...")
    
    if st.sidebar.button("📤 Send Message"):
        if message_notes:
            success = send_supplier_message(
                supplier_id,
                message_type,
                {
                    'product_id': selected_product_id,
                    'product_name': selected_product.name
                },
                0,
                message_notes
            )
            if success:
                st.sidebar.success("Message sent!")
                st.rerun()

# Main Dashboard
st.title("📦 Enhanced Inventory Management Dashboard")

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Inventory Overview", "📞 Supplier Messages", "📈 Analytics", "🔄 Bulk Operations"])

with tab1:
    st.subheader("📊 Current Inventory Status")
    
    # Load and display inventory
    df = load_inventory_data()
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_products = len(df)
        st.metric("Total Products", total_products)
    
    with col2:
        total_stock = df['Current Stock'].sum()
        st.metric("Total Stock", total_stock)
    
    with col3:
        low_stock_count = len(df[df['Needs Reorder'] == True])
        st.metric("Low Stock Items", low_stock_count, delta_color="inverse")
    
    with col4:
        avg_stock = df['Current Stock'].mean()
        st.metric("Average Stock", f"{avg_stock:.1f}")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        stock_filter = st.selectbox("Stock Status", ["All", "Low Stock", "Good Stock"])
    
    with col2:
        supplier_filter = st.selectbox("Supplier", ["All"] + [s.supplier_id for s in [get_supplier_info(sid) for sid in ["SUPPLIER_001", "SUPPLIER_002", "SUPPLIER_003"]] if s])
    
    with col3:
        sort_by = st.selectbox("Sort By", ["Product ID", "Product Name", "Current Stock", "Stock Status"])
    
    # Apply filters
    filtered_df = df.copy()
    
    if stock_filter == "Low Stock":
        filtered_df = filtered_df[filtered_df['Needs Reorder'] == True]
    elif stock_filter == "Good Stock":
        filtered_df = filtered_df[filtered_df['Needs Reorder'] == False]
    
    # Sort data
    if sort_by == "Current Stock":
        filtered_df = filtered_df.sort_values("Current Stock", ascending=False)
    elif sort_by == "Product Name":
        filtered_df = filtered_df.sort_values("Product Name")
    
    # Enhanced inventory table
    st.table(filtered_df)
    
    # Quick actions for selected products
    st.markdown("### ⚡ Quick Actions")
    selected_rows = st.multiselect(
        "Select products for bulk actions:",
        options=filtered_df['Product ID'].tolist(),
        format_func=lambda x: f"{x} - {filtered_df[filtered_df['Product ID']==x]['Product Name'].iloc[0][:30]}..."
    )
    
    if selected_rows:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📈 Increase All by 10"):
                with InventoryManager() as inv_mgr:
                    updates = [{'product_id': pid, 'quantity_change': 10, 'reason': 'Bulk increase +10'} for pid in selected_rows]
                    result = inv_mgr.bulk_update_inventory(updates)
                    st.success(f"Updated {result['successful']} products")
                    st.rerun()
        
        with col2:
            if st.button("📉 Decrease All by 5"):
                with InventoryManager() as inv_mgr:
                    updates = [{'product_id': pid, 'quantity_change': -5, 'reason': 'Bulk decrease -5'} for pid in selected_rows]
                    result = inv_mgr.bulk_update_inventory(updates)
                    st.success(f"Updated {result['successful']} products")
                    st.rerun()
        
        with col3:
            if st.button("📧 Send Reorder Requests"):
                messages_sent = 0
                for pid in selected_rows:
                    product = next((p for p in USER_PRODUCT_CATALOG if p.product_id == pid), None)
                    if product:
                        with InventoryManager() as inv_mgr:
                            inv = inv_mgr.get_current_inventory(pid)
                            if inv and inv.current_stock <= inv.reorder_point:
                                success = send_supplier_message(
                                    inv.supplier_id,
                                    "Bulk Reorder Request",
                                    {'product_id': pid, 'product_name': product.name},
                                    50,
                                    f"Bulk reorder request for {product.name}"
                                )
                                if success:
                                    messages_sent += 1
                
                st.success(f"Sent {messages_sent} reorder requests")
                st.rerun()

with tab2:
    st.subheader("📞 Supplier Communication Center")
    
    # Display supplier messages
    if st.session_state.supplier_messages:
        st.markdown("### 📨 Recent Messages")
        
        for i, msg in enumerate(reversed(st.session_state.supplier_messages[-10:])):  # Show last 10 messages
            with st.expander(f"{msg['message_type']} to {msg['supplier']['name']} - {msg['timestamp']}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Product:** {msg['product_info']['product_name']}")
                    st.markdown(f"**Product ID:** {msg['product_info']['product_id']}")
                    if msg['quantity'] > 0:
                        st.markdown(f"**Quantity:** {msg['quantity']}")
                    st.markdown(f"**Message:** {msg['notes']}")
                
                with col2:
                    st.markdown(f"**Supplier:** {msg['supplier']['name']}")
                    st.markdown(f"**Email:** {msg['supplier']['email']}")
                    st.markdown(f"**Phone:** {msg['supplier']['phone']}")
                    st.markdown(f"**Status:** {msg['status']}")
    else:
        st.info("No messages sent yet. Use the sidebar to send messages to suppliers.")
    
    # Supplier directory
    st.markdown("### 📋 Supplier Directory")
    
    suppliers_data = []
    for supplier_id in ["SUPPLIER_001", "SUPPLIER_002", "SUPPLIER_003"]:
        supplier = get_supplier_info(supplier_id)
        if supplier:
            # Count products for this supplier
            with InventoryManager() as inv_mgr:
                all_inv = inv_mgr.get_current_inventory()
                supplier_products = [inv for inv in all_inv if inv.supplier_id == supplier_id]
                low_stock_products = [inv for inv in supplier_products if inv.needs_reorder]
            
            suppliers_data.append({
                'Supplier ID': supplier['supplier_id'],
                'Name': supplier['name'],
                'Email': supplier['email'],
                'Phone': supplier['phone'],
                'Lead Time': f"{supplier['lead_time']} days",
                'Min Order': supplier['minimum_order'],
                'Products': len(supplier_products),
                'Low Stock Items': len(low_stock_products)
            })
    
    suppliers_df = pd.DataFrame(suppliers_data)
    st.table(suppliers_df)

with tab3:
    st.subheader("📈 Inventory Analytics")
    
    df = load_inventory_data()
    
    # Stock distribution chart
    col1, col2 = st.columns(2)
    
    with col1:
        # Stock levels by category
        category_data = []
        for product in USER_PRODUCT_CATALOG:
            with InventoryManager() as inv_mgr:
                inv = inv_mgr.get_current_inventory(product.product_id)
                if inv:
                    category_data.append({
                        'Category': product.category.value,
                        'Stock': inv.current_stock
                    })
        
        if category_data:
            category_df = pd.DataFrame(category_data)
            category_summary = category_df.groupby('Category')['Stock'].sum().reset_index()
            
            fig_category = px.pie(
                category_summary,
                values='Stock',
                names='Category',
                title="Stock Distribution by Category"
            )
            st.plotly_chart(fig_category, use_container_width=True)
    
    with col2:
        # Stock status distribution
        stock_status = df['Stock Status'].value_counts()
        fig_status = px.pie(
            values=stock_status.values,
            names=stock_status.index,
            title="Stock Status Distribution"
        )
        st.plotly_chart(fig_status, use_container_width=True)
    
    # Top/Bottom performers
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔝 Highest Stock Levels")
        top_stock = df.nlargest(5, 'Current Stock')[['Product ID', 'Product Name', 'Current Stock']]
        st.table(top_stock)
    
    with col2:
        st.markdown("### ⚠️ Lowest Stock Levels")
        low_stock = df.nsmallest(5, 'Current Stock')[['Product ID', 'Product Name', 'Current Stock']]
        st.table(low_stock)

with tab4:
    st.subheader("🔄 Bulk Operations")
    
    # Bulk update from CSV/Excel
    st.markdown("### 📁 Upload Inventory Updates")
    
    uploaded_file = st.file_uploader("Choose CSV or Excel file", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
            
            st.write("Preview of uploaded data:")
            st.table(df_upload.head())
            
            if 'Product ID' in df_upload.columns and 'New Quantity' in df_upload.columns:
                if st.button("Apply Bulk Updates from File"):
                    updates = []
                    for _, row in df_upload.iterrows():
                        product_id = row['Product ID']
                        new_qty = row['New Quantity']
                        
                        with InventoryManager() as inv_mgr:
                            current_inv = inv_mgr.get_current_inventory(product_id)
                            if current_inv:
                                quantity_change = new_qty - current_inv.current_stock
                                if quantity_change != 0:
                                    updates.append({
                                        'product_id': product_id,
                                        'quantity_change': quantity_change,
                                        'reason': 'Bulk file update'
                                    })
                    
                    if updates:
                        with InventoryManager() as inv_mgr:
                            result = inv_mgr.bulk_update_inventory(updates)
                            st.success(f"Updated {result['successful']} products from file")
                            st.rerun()
            else:
                st.error("File must contain 'Product ID' and 'New Quantity' columns")
        
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    # Template download
    st.markdown("### 📥 Download Template")
    
    template_data = []
    for product in USER_PRODUCT_CATALOG[:10]:  # First 10 products as template
        with InventoryManager() as inv_mgr:
            inv = inv_mgr.get_current_inventory(product.product_id)
            template_data.append({
                'Product ID': product.product_id,
                'Product Name': product.name,
                'Current Quantity': inv.current_stock if inv else 0,
                'New Quantity': inv.current_stock if inv else 0  # User will modify this
            })
    
    template_df = pd.DataFrame(template_data)
    csv = template_df.to_csv(index=False)
    
    st.download_button(
        label="📥 Download CSV Template",
        data=csv,
        file_name="inventory_update_template.csv",
        mime="text/csv"
    )

# Refresh data button
if st.button("🔄 Refresh All Data"):
    st.cache_data.clear()
    st.rerun()

# Footer with instructions
st.markdown("---")
st.markdown("""
### 💡 How to Use This Dashboard

1. **Sidebar Quick Editor**: Select any product and make instant adjustments
2. **Supplier Communication**: Send reorder requests and messages directly to suppliers
3. **Bulk Operations**: Update multiple products at once or upload from files
4. **Analytics**: Monitor stock levels and identify trends

**Tips:**
- Use the sidebar for quick edits of individual products
- Low stock items are automatically flagged for reordering
- All changes are logged and tracked in the system
- Supplier messages are simulated but show the workflow
""")

if __name__ == "__main__":
    pass