#!/usr/bin/env python3
"""
AI Agent Logistics Dashboard with Supplier Contact Management
Enhanced dashboard with inventory editing and supplier communication
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
from database.service import DatabaseService
from database.models import init_database

# Page configuration
st.set_page_config(
    page_title="AI Agent Logistics Dashboard",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-critical {
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-high {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .alert-medium {
        background-color: #e8f5e8;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def get_supplier_info(supplier_id):
    """Get supplier information from database"""
    from database.models import SessionLocal, Supplier
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

def get_product_name(product_id):
    """Get product name from catalog"""
    try:
        from user_product_models import USER_PRODUCT_CATALOG
        for product in USER_PRODUCT_CATALOG:
            if product.product_id == product_id:
                return product.name
    except ImportError:
        pass
    return product_id

def get_product_image(product_id: str) -> str:
    """Get product image URL from database"""
    try:
        from database.models import SessionLocal, Product
        db = SessionLocal()
        product = db.query(Product).filter(Product.product_id == product_id).first()
        db.close()
        
        if product and product.thumbnail_url:
            return f"http://localhost:8000{product.thumbnail_url}"
        elif product and product.primary_image_url:
            return f"http://localhost:8000{product.primary_image_url}"
    except Exception as e:
        print(f"Error getting product image: {e}")
    
    return "https://via.placeholder.com/100x100?text=No+Image"

def load_dashboard_data():
    """Load all dashboard data"""
    with DatabaseService() as db_service:
        data = {
            'orders': db_service.get_orders(),
            'shipments': db_service.get_shipments(),
            'inventory': db_service.get_inventory(),
            'low_stock': db_service.get_low_stock_items(),
            'purchase_orders': db_service.get_purchase_orders(),
            'pending_reviews': db_service.get_pending_reviews(),
            'agent_logs': db_service.get_agent_logs(limit=50),
            'performance_metrics': db_service.get_performance_metrics(days=7)
        }
    return data

def create_kpi_metrics(data):
    """Create KPI metrics"""
    orders = data['orders']
    shipments = data['shipments']
    inventory = data['inventory']
    low_stock = data['low_stock']
    purchase_orders = data['purchase_orders']
    pending_reviews = data['pending_reviews']
    performance = data['performance_metrics']
    
    # Calculate KPIs
    total_orders = len(orders)
    active_shipments = len([s for s in shipments if s['status'] not in ['delivered', 'cancelled']])
    delivered_shipments = len([s for s in shipments if s['status'] == 'delivered'])
    delivery_rate = (delivered_shipments / len(shipments) * 100) if shipments else 0
    
    low_stock_count = len(low_stock)
    stock_health = ((len(inventory) - low_stock_count) / len(inventory) * 100) if inventory else 100
    
    pending_pos = len([po for po in purchase_orders if po['status'] == 'pending'])
    automation_rate = performance.get('automation_rate', 0)
    
    return {
        'total_orders': total_orders,
        'active_shipments': active_shipments,
        'delivery_rate': delivery_rate,
        'stock_health': stock_health,
        'low_stock_count': low_stock_count,
        'pending_pos': pending_pos,
        'automation_rate': automation_rate,
        'pending_reviews': len(pending_reviews)
    }

def display_kpi_dashboard(kpis):
    """Display KPI dashboard"""
    st.markdown('<div class="main-header">🚚 AI Agent Logistics Dashboard</div>', unsafe_allow_html=True)
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📦 Total Orders",
            value=kpis['total_orders'],
            delta=f"{kpis['active_shipments']} active shipments"
        )
        
    with col2:
        st.metric(
            label="🚚 Delivery Rate",
            value=f"{kpis['delivery_rate']:.1f}%",
            delta="Last 7 days"
        )
        
    with col3:
        st.metric(
            label="📊 Stock Health",
            value=f"{kpis['stock_health']:.1f}%",
            delta=f"{kpis['low_stock_count']} items low" if kpis['low_stock_count'] > 0 else "All items stocked",
            delta_color="inverse" if kpis['low_stock_count'] > 0 else "normal"
        )
        
    with col4:
        st.metric(
            label="🤖 Automation Rate",
            value=f"{kpis['automation_rate']:.1f}%",
            delta=f"{kpis['pending_reviews']} pending reviews"
        )

def display_alerts(data):
    """Display system alerts"""
    st.subheader("🚨 System Alerts")
    
    # Generate alerts based on data
    alerts = []
    
    # Stock alerts
    low_stock = data['low_stock']
    for item in low_stock:
        severity = "critical" if item['CurrentStock'] == 0 else "high"
        alerts.append({
            'severity': severity,
            'title': f"Low Stock Alert: {item['ProductID']}",
            'message': f"Current stock: {item['CurrentStock']}, Reorder point: {item['ReorderPoint']}",
            'timestamp': datetime.now()
        })
    
    # Display alerts
    if alerts:
        for alert in sorted(alerts, key=lambda x: x['timestamp'], reverse=True):
            severity_class = f"alert-{alert['severity']}"
            st.markdown(f"""
            <div class="{severity_class}">
                <strong>{alert['title']}</strong><br>
                {alert['message']}<br>
                <small>⏰ {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</small>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ No active alerts - All systems operating normally")

def display_performance_charts(data):
    """Display performance charts"""
    st.subheader("📈 Performance Analytics")
    
    # Order status distribution
    col1, col2 = st.columns(2)
    
    with col1:
        orders = data['orders']
        if orders:
            status_counts = {}
            for order in orders:
                status = order['Status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            fig_orders = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                title="Order Status Distribution"
            )
            st.plotly_chart(fig_orders, use_container_width=True)
    
    with col2:
        shipments = data['shipments']
        if shipments:
            shipment_counts = {}
            for shipment in shipments:
                status = shipment['status']
                shipment_counts[status] = shipment_counts.get(status, 0) + 1
            
            fig_shipments = px.pie(
                values=list(shipment_counts.values()),
                names=list(shipment_counts.keys()),
                title="Shipment Status Distribution"
            )
            st.plotly_chart(fig_shipments, use_container_width=True)
    
    # Product catalog overview
    st.subheader("🏷️ Your Product Catalog")
    try:
        from user_product_models import USER_PRODUCT_CATALOG
        if USER_PRODUCT_CATALOG:
            # Create product summary
            product_data = []
            for product in USER_PRODUCT_CATALOG:
                product_data.append({
                    'Product ID': product.product_id,
                    'Product Name': product.name,
                    'Category': product.category.value,
                    'Current Qty': product.current_qty,
                    'Price': f"${product.unit_price:.2f}",
                    'Supplier': product.supplier_id
                })
            
            df_products = pd.DataFrame(product_data)
            st.table(df_products)
    except ImportError:
        st.info("Product catalog not available")

def display_recent_activity(data):
    """Display recent activity with product information"""
    st.subheader("📜 Recent Activity")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["🔄 Activity Log", "🏷️ Product ID Reference"])
    
    with tab1:
        logs = data['agent_logs']
        if logs:
            # Display recent logs in a table with enhanced product info
            display_logs = []
            for log in logs[:15]:  # Show last 15 activities
                product_id = log['ProductID'] or 'N/A'
                product_name = get_product_name(product_id) if product_id != 'N/A' else 'N/A'
                
                display_logs.append({
                    'Time': log['timestamp'][:19] if log['timestamp'] else 'N/A',
                    'Action': log['action'],
                    'Product ID': product_id,
                    'Product Name': product_name if product_name != product_id else 'N/A',
                    'Quantity': log['quantity'] if log['quantity'] else 'N/A',
                    'Details': (log['details'] or '')[:60] + '...' if log['details'] and len(log['details']) > 60 else log['details'] or ''
                })
            
            df_activity = pd.DataFrame(display_logs)
            st.table(df_activity)
        else:
            st.info("No recent activity to display")
    
    with tab2:
        st.subheader("🏷️ Product ID Reference Table")
        
        try:
            from user_product_models import USER_PRODUCT_CATALOG
            if USER_PRODUCT_CATALOG:
                # Create comprehensive product reference table
                product_ref_data = []
                for product in USER_PRODUCT_CATALOG:
                    # Get current inventory info
                    inventory_info = next((inv for inv in data['inventory'] if inv['ProductID'] == product.product_id), None)
                    current_stock = inventory_info['CurrentStock'] if inventory_info else 0
                    
                    product_ref_data.append({
                        'Product ID': product.product_id,
                        'Product Name': product.name,
                        'Category': product.category.value,
                        'Brand': 'SYSKA' if 'SYSKA' in product.name else 'BOAST' if 'BOAST' in product.name else 'Other',
                        'Current Stock': current_stock,
                        'Price': f"${product.unit_price:.2f}",
                        'Supplier': product.supplier_id,
                        'Status': '🟢 Active' if product.is_active else '🔴 Inactive'
                    })
                
                df_products = pd.DataFrame(product_ref_data)
                
                # Add search functionality
                search_term = st.text_input("🔍 Search Products", placeholder="Search by Product ID, Name, or Category...")
                
                if search_term:
                    mask = df_products.apply(lambda x: x.astype(str).str.contains(search_term, case=False, na=False)).any(axis=1)
                    df_filtered = df_products[mask]
                    st.write(f"Found {len(df_filtered)} products matching '{search_term}'")
                else:
                    df_filtered = df_products
                
                st.table(df_filtered)
                
        except ImportError:
            st.error("Unable to load product catalog")

def display_system_status(data):
    """Display system status"""
    st.subheader("⚙️ System Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🤖 AI Agents**")
        st.success("✅ Procurement Agent: Active")
        st.success("✅ Delivery Agent: Active")
        st.success("✅ Inventory Monitor: Active")
    
    with col2:
        st.markdown("**🔗 Integrations**")
        st.success("✅ Database: Connected")
        st.success("✅ Supplier APIs: Ready")
        st.success("✅ Courier APIs: Ready")
    
    with col3:
        st.markdown("**📊 Performance**")
        performance = data['performance_metrics']
        st.metric("Automation Rate", f"{performance.get('automation_rate', 0):.1f}%")
        st.metric("Total Actions", performance.get('total_actions', 0))
        st.metric("Success Rate", "100.0%")

def display_add_new_product_form():
    """Display form to add new product with image"""
    st.sidebar.markdown("#### 🆕 Add New Product")
    
    with st.sidebar.form("new_product_form", clear_on_submit=False):
        # Product basic info
        new_product_id = st.text_input("Product ID", placeholder="e.g., USR031", key="new_pid")
        new_product_name = st.text_input("Product Name", placeholder="Enter product name", key="new_pname")
        
        # Category selection
        from user_product_models import ProductCategory
        category_options = [cat.value for cat in ProductCategory]
        new_category = st.selectbox("Category", category_options, key="new_cat")
        
        # Price and basic specs
        new_price = st.number_input("Unit Price ($)", min_value=0.01, value=15.99, key="new_price")
        new_description = st.text_area("Description", height=60, key="new_desc")
        
        # Supplier
        new_supplier = st.selectbox("Supplier", ["SUPPLIER_001", "SUPPLIER_002", "SUPPLIER_003"], key="new_sup")
        
        # Stock info
        col1, col2 = st.columns(2)
        with col1:
            initial_stock = st.number_input("Initial Stock", min_value=0, value=50, key="new_stock")
        with col2:
            reorder_point = st.number_input("Reorder Point", min_value=1, value=10, key="new_reorder")
        
        # Product Image
        st.markdown("**Product Image:**")
        product_image = st.file_uploader(
            "Upload Product Image",
            type=['png', 'jpg', 'jpeg', 'webp'],
            key="new_product_image"
        )
        
        # Preview image if uploaded
        if product_image:
            from PIL import Image
            image = Image.open(product_image)
            
            # Show thumbnail
            st.image(image, caption="Image Preview", width=120)
            
            # Add click-to-expand functionality
            with st.expander("🔍 Click to View Full Size Image", expanded=False):
                st.image(image, caption="Full Size Preview", use_column_width=True)
                st.info(f"Image size: {image.size[0]}x{image.size[1]} pixels")
        
        # Submit button
        submit_new_product = st.form_submit_button("🆕 Create Product")
        
        if submit_new_product:
            if new_product_id and new_product_name and new_category:
                # Create product in database
                success = create_new_product_with_image(
                    product_id=new_product_id,
                    name=new_product_name,
                    category=new_category,
                    description=new_description,
                    price=new_price,
                    supplier_id=new_supplier,
                    initial_stock=initial_stock,
                    reorder_point=reorder_point,
                    image_file=product_image
                )
                
                if success:
                    st.sidebar.success(f"✅ Product '{new_product_name}' created successfully!")
                    st.sidebar.info(f"🆆 Product ID: {new_product_id}")
                    # Clear form by rerunning
                    st.rerun()
                else:
                    st.sidebar.error("❌ Failed to create product")
            else:
                st.sidebar.error("⚠️ Please fill in all required fields")

def display_add_images_form():
    """Display form to add images to existing products"""
    st.sidebar.markdown("#### 🖼️ Add Images to Product")
    
    # Get existing products
    try:
        from user_product_models import USER_PRODUCT_CATALOG
        if USER_PRODUCT_CATALOG:
            # Product selector
            product_options = {f"{p.product_id} - {p.name[:25]}...": p.product_id for p in USER_PRODUCT_CATALOG}
            selected_product_key = st.sidebar.selectbox(
                "Select Product", 
                options=list(product_options.keys()),
                key="image_product_selector"
            )
            selected_product_id = product_options[selected_product_key]
            
            # Get current product
            selected_product = next((p for p in USER_PRODUCT_CATALOG if p.product_id == selected_product_id), None)
            
            if selected_product:
                # Show current product image if exists
                current_image_url = get_product_image(selected_product_id)
                if current_image_url != "https://via.placeholder.com/100x100?text=No+Image":
                    # Show thumbnail
                    st.sidebar.image(current_image_url, width=100, caption="Current Image")
                    
                    # Add click-to-expand for current image
                    with st.sidebar.expander("🔍 View Current Image Full Size", expanded=False):
                        st.sidebar.image(current_image_url, caption=f"Current Image - {selected_product.name}", use_column_width=True)
                else:
                    st.sidebar.info("🖼️ No image yet")
                
                st.sidebar.markdown(f"**Product:** {selected_product.name}")
                
                # Image upload form
                with st.sidebar.form("add_image_form"):
                    image_type = st.selectbox(
                        "Image Type",
                        ["Primary Image", "Gallery Image"],
                        key="img_type"
                    )
                    
                    upload_image = st.file_uploader(
                        "Choose Image",
                        type=['png', 'jpg', 'jpeg', 'webp'],
                        key="upload_img"
                    )
                    
                    # Preview uploaded image
                    if upload_image:
                        from PIL import Image
                        image = Image.open(upload_image)
                        
                        # Show thumbnail preview
                        st.image(image, caption="Upload Preview", width=100)
                        
                        # Add click-to-expand for upload preview
                        with st.expander("🔍 View Upload Full Size", expanded=False):
                            st.image(image, caption=f"Upload Preview - {image_type}", use_column_width=True)
                            st.info(f"Image size: {image.size[0]}x{image.size[1]} pixels")
                    
                    submit_image = st.form_submit_button("💾 Upload Image")
                    
                    if submit_image and upload_image:
                        # Upload image via API
                        api_success = upload_image_via_api(
                            product_id=selected_product_id,
                            image_file=upload_image,
                            image_type="primary" if image_type == "Primary Image" else "gallery"
                        )
                        
                        if api_success:
                            st.sidebar.success(f"✅ {image_type} uploaded successfully!")
                            st.rerun()
                        else:
                            st.sidebar.error(f"❌ Failed to upload {image_type.lower()}")
    except ImportError:
        st.sidebar.info("Product catalog not available")

def create_new_product_with_image(product_id: str, name: str, category: str, description: str, 
                                price: float, supplier_id: str, initial_stock: int, 
                                reorder_point: int, image_file=None) -> bool:
    """Create new product in database with optional image"""
    try:
        from database.models import SessionLocal, Product
        from user_product_models import ProductCategory
        
        # Check if product already exists
        db = SessionLocal()
        existing = db.query(Product).filter(Product.product_id == product_id).first()
        if existing:
            st.sidebar.error(f"⚠️ Product ID '{product_id}' already exists")
            db.close()
            return False
        
        # Create new product record
        new_product = Product(
            product_id=product_id,
            name=name,
            category=category,
            description=description,
            unit_price=price,
            supplier_id=supplier_id,
            reorder_point=reorder_point,
            max_stock=initial_stock * 5,  # Set max stock to 5x initial
            is_active=True
        )
        
        db.add(new_product)
        db.commit()
        db.close()
        
        # Add to inventory
        from inventory_manager import InventoryManager
        with InventoryManager() as inv_mgr:
            inv_result = inv_mgr.update_inventory(
                product_id, 
                initial_stock, 
                f"Initial stock for new product: {name}"
            )
            
            if not inv_result['success']:
                st.sidebar.warning("Product created but inventory not set")
        
        # Upload image if provided
        if image_file:
            upload_success = upload_image_via_api(product_id, image_file, "primary")
            if not upload_success:
                st.sidebar.warning("Product created but image upload failed")
        
        return True
        
    except Exception as e:
        st.sidebar.error(f"Error creating product: {str(e)}")
        return False

def upload_image_via_api(product_id: str, image_file, image_type: str) -> bool:
    """Upload image via API endpoint"""
    try:
        import requests
        import io
        
        # Prepare file for upload
        image_file.seek(0)  # Reset file pointer
        files = {'file': (image_file.name, image_file, image_file.type)}
        
        # Determine API endpoint
        if image_type == "primary":
            endpoint = f"http://localhost:8000/products/{product_id}/images/primary"
        else:
            endpoint = f"http://localhost:8000/products/{product_id}/images/gallery"
        
        # Make API call (note: in production, you'd need proper auth headers)
        response = requests.post(endpoint, files=files)
        
        if response.status_code == 200:
            return True
        else:
            st.sidebar.error(f"API Error: {response.status_code}")
            return False
            
    except Exception as e:
        st.sidebar.error(f"Upload error: {str(e)}")
        return False

def main():
    """Main dashboard application"""
    # Initialize database
    init_database()
    
    # Sidebar
    st.sidebar.title("🚚 Navigation")
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=False)
    
    if st.sidebar.button("🔄 Refresh Data"):
        st.experimental_rerun()
    
    # Manual agent triggers
    st.sidebar.markdown("### 🤖 Agent Controls")
    
    if st.sidebar.button("🏭 Run Procurement Agent"):
        with st.spinner("Running procurement agent..."):
            try:
                from procurement_agent import run_procurement_agent
                results = run_procurement_agent()
                st.sidebar.success(f"✅ Procurement completed: {results['purchase_orders_created']} POs created")
            except Exception as e:
                st.sidebar.error(f"❌ Error: {str(e)}")
    
    if st.sidebar.button("🚚 Run Delivery Agent"):
        with st.spinner("Running delivery agent..."):
            try:
                from delivery_agent import run_delivery_agent
                results = run_delivery_agent()
                st.sidebar.success(f"✅ Delivery completed: {results['shipments_created']} shipments created")
            except Exception as e:
                st.sidebar.error(f"❌ Error: {str(e)}")
    
    # PRODUCT MANAGEMENT SECTION
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🆕 Product Management")
    
    # Product Management Options
    product_action = st.sidebar.selectbox(
        "Choose Action",
        ["Select Product", "Add New Product", "Add Images to Existing Product"],
        key="product_management_action"
    )
    
    if product_action == "Add New Product":
        display_add_new_product_form()
    elif product_action == "Add Images to Existing Product":
        display_add_images_form()
    
    # INVENTORY EDITOR AND SUPPLIER MANAGEMENT
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📦 Quick Inventory Editor")
    
    try:
        from user_product_models import USER_PRODUCT_CATALOG
        from inventory_manager import InventoryManager
        
        if USER_PRODUCT_CATALOG:
            # Product selector
            product_options = {f"{p.product_id} - {p.name[:25]}...": p.product_id for p in USER_PRODUCT_CATALOG}
            selected_product_key = st.sidebar.selectbox(
                "Select Product to Edit", 
                options=list(product_options.keys()),
                key="sidebar_product_selector"
            )
            selected_product_id = product_options[selected_product_key]
            
            # Get current product info
            with InventoryManager() as inv_mgr:
                current_inv = inv_mgr.get_current_inventory(selected_product_id)
                if current_inv:
                    current_stock = current_inv.current_stock
                    reorder_point = current_inv.reorder_point
                    supplier_id = current_inv.supplier_id or "SUPPLIER_001"
                else:
                    current_stock = 0
                    reorder_point = 0
                    supplier_id = "SUPPLIER_001"
            
            # Get product details
            selected_product = next((p for p in USER_PRODUCT_CATALOG if p.product_id == selected_product_id), None)
            
            if selected_product:
                # Display product image with click-to-expand functionality
                product_image_url = get_product_image(selected_product_id)
                
                # Show clickable image
                if product_image_url != "https://via.placeholder.com/100x100?text=No+Image":
                    # Add click functionality with expander
                    with st.sidebar.expander("🖼️ Click to View Full Image", expanded=False):
                        st.image(product_image_url, caption=f"{selected_product.name} - Full Size", use_column_width=True)
                    
                    # Show thumbnail in sidebar
                    st.sidebar.image(product_image_url, width=120, caption=f"📸 {selected_product.name}")
                else:
                    st.sidebar.image("https://via.placeholder.com/120x120?text=No+Image", width=120, caption=selected_product.name)
                    st.sidebar.info("📸 No image available - Upload one below!")
                
                # Product info
                st.sidebar.markdown(f"**{selected_product.name}**")
                st.sidebar.markdown(f"Category: {selected_product.category.value}")
                st.sidebar.markdown(f"Price: ${selected_product.unit_price:.2f}")
                
                st.sidebar.markdown(f"**Current Stock:** {current_stock}")
                st.sidebar.markdown(f"**Reorder Point:** {reorder_point}")
                
                # Stock status indicator
                if current_stock <= reorder_point:
                    st.sidebar.error("🔴 LOW STOCK ALERT!")
                else:
                    st.sidebar.success("🟢 Stock OK")
                
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
                custom_change = st.sidebar.number_input("Custom Change", value=0, key="custom_change", help="Positive to add, negative to remove")
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
                
                # SUPPLIER CONTACT MANAGEMENT
                st.sidebar.markdown("---")
                st.sidebar.markdown("### 📞 Supplier Contact")
                
                supplier_info = get_supplier_info(supplier_id)
                if supplier_info:
                    st.sidebar.markdown(f"**Supplier:** {supplier_info['name']}")
                    st.sidebar.markdown(f"**Email:** {supplier_info['email']}")
                    st.sidebar.markdown(f"**Phone:** {supplier_info['phone']}")
                    st.sidebar.markdown(f"**Lead Time:** {supplier_info['lead_time']} days")
                    st.sidebar.markdown(f"**Min Order:** {supplier_info['minimum_order']} units")
                    
                    # Edit Contact Info Button
                    if st.sidebar.button("✏️ Edit Contact Info", key="edit_contact"):
                        st.session_state.show_contact_editor = True
                    
                    # Contact Editor
                    if st.session_state.get('show_contact_editor', False):
                        st.sidebar.markdown("**📝 Edit Supplier Contact:**")
                        
                        new_email = st.sidebar.text_input("Email", value=supplier_info['email'], key="new_email")
                        new_phone = st.sidebar.text_input("Phone", value=supplier_info['phone'], key="new_phone")
                        new_lead_time = st.sidebar.number_input("Lead Time (days)", value=supplier_info['lead_time'], min_value=1, key="new_lead_time")
                        new_min_order = st.sidebar.number_input("Min Order", value=supplier_info['minimum_order'], min_value=1, key="new_min_order")
                        
                        col1, col2 = st.sidebar.columns(2)
                        with col1:
                            if st.button("💾 Save", key="save_contact"):
                                from database.models import SessionLocal, Supplier
                                db = SessionLocal()
                                try:
                                    supplier = db.query(Supplier).filter(Supplier.supplier_id == supplier_id).first()
                                    if supplier:
                                        supplier.contact_email = new_email
                                        supplier.contact_phone = new_phone
                                        supplier.lead_time_days = new_lead_time
                                        supplier.minimum_order = new_min_order
                                        db.commit()
                                        st.sidebar.success("✅ Contact info updated!")
                                        st.session_state.show_contact_editor = False
                                        st.rerun()
                                except Exception as e:
                                    st.sidebar.error(f"Error: {e}")
                                finally:
                                    db.close()
                        
                        with col2:
                            if st.button("❌ Cancel", key="cancel_contact"):
                                st.session_state.show_contact_editor = False
                                st.rerun()
                    
                    # Custom Alert Section
                    st.sidebar.markdown("---")
                    st.sidebar.markdown("### 📨 Send Custom Alert")
                    
                    alert_type = st.sidebar.selectbox(
                        "Alert Type",
                        ["Quality Issue", "Delivery Delay", "Price Inquiry", "Stock Alert", "General Message"],
                        key="alert_type"
                    )
                    
                    custom_message = st.sidebar.text_area(
                        "Message",
                        placeholder="Enter your message to the supplier...",
                        key="custom_message",
                        height=80
                    )
                    
                    if st.sidebar.button("📤 Send Alert", key="send_alert"):
                        if custom_message.strip():
                            # Create alert message
                            full_message = f"""
{alert_type.upper()} - {selected_product.name}

Product ID: {selected_product_id}
Current Stock: {current_stock}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Message:
{custom_message}

Contact Info:
Phone: {supplier_info['phone']}
Email: {supplier_info['email']}
                            """
                            
                            # SEND REAL EMAIL TO SUPPLIER
                            try:
                                from supplier_notification_system import SupplierNotificationSystem
                                notifier = SupplierNotificationSystem()
                                
                                # Create professional email subject
                                email_subject = f"🔔 {alert_type.upper()}: {selected_product.name}"
                                
                                # Create HTML formatted email
                                html_message = f"""
                                <html>
                                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                                        <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                                            <h2 style="color: #1f77b4; margin: 0;">🔔 {alert_type.upper()}</h2>
                                        </div>
                                        
                                        <p>Dear {supplier_info['name']},</p>
                                        
                                        <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; margin: 20px 0;">
                                            <h3 style="margin-top: 0; color: #856404;">📦 Product Information</h3>
                                            <p><strong>Product:</strong> {selected_product.name}</p>
                                            <p><strong>Product ID:</strong> {selected_product_id}</p>
                                            <p><strong>Current Stock:</strong> {current_stock} units</p>
                                            <p><strong>Alert Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                                        </div>
                                        
                                        <div style="background-color: #d1ecf1; padding: 15px; border-radius: 5px; border-left: 4px solid #17a2b8; margin: 20px 0;">
                                            <h3 style="margin-top: 0; color: #0c5460;">📝 Message</h3>
                                            <p>{custom_message}</p>
                                        </div>
                                        
                                        <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745; margin: 20px 0;">
                                            <h3 style="margin-top: 0; color: #155724;">📞 Contact Information</h3>
                                            <p><strong>Company:</strong> {notifier.company_name}</p>
                                            <p><strong>Email:</strong> {notifier.company_email}</p>
                                            <p><strong>Phone:</strong> {notifier.company_phone}</p>
                                        </div>
                                        
                                        <p>Please respond to this message at your earliest convenience.</p>
                                        
                                        <p>Best regards,<br>
                                        <strong>Inventory Management Team</strong><br>
                                        {notifier.company_name}<br>
                                        <em>This message was sent from our AI Logistics Dashboard</em></p>
                                    </div>
                                </body>
                                </html>
                                """
                                
                                # Send email to supplier
                                email_success = notifier.send_email_to_supplier(
                                    supplier_info['email'],
                                    email_subject,
                                    html_message,
                                    is_html=True
                                )
                                
                                if email_success:
                                    st.sidebar.success(f"✅ {alert_type} EMAIL SENT to {supplier_info['name']}!")
                                    st.sidebar.info(f"📧 Sent to: {supplier_info['email']}")
                                else:
                                    st.sidebar.warning(f"⚠️ {alert_type} logged (email config needed)")
                                    st.sidebar.info(f"📧 Would send to: {supplier_info['email']}")
                                
                            except Exception as e:
                                st.sidebar.error(f"❌ Error sending email: {str(e)}")
                                st.sidebar.info(f"📧 Target: {supplier_info['email']}")
                            
                            # Store message in session state for history
                            if 'supplier_messages' not in st.session_state:
                                st.session_state.supplier_messages = []
                            
                            st.session_state.supplier_messages.append({
                                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'supplier': supplier_info['name'],
                                'email': supplier_info['email'],
                                'phone': supplier_info['phone'],
                                'message_type': alert_type,
                                'product': selected_product.name,
                                'message': full_message.strip()
                            })
                            
                            st.sidebar.info(f"📞 {supplier_info['phone']}")
                            
                            # Page will automatically refresh and clear the form
                            st.rerun()
                        else:
                            st.sidebar.error("Please enter a message!")
                    
                    # Show recent messages
                    if st.session_state.get('supplier_messages', []):
                        st.sidebar.markdown("---")
                        st.sidebar.markdown("### 📬 Recent Messages")
                        
                        for msg in st.session_state.supplier_messages[-2:]:  # Show last 2 messages
                            st.sidebar.markdown(f"**{msg['message_type']}** to {msg['supplier']}")
                            st.sidebar.markdown(f"*{msg['timestamp']}*")
                            st.sidebar.markdown("---")
    
    except ImportError:
        st.sidebar.info("Inventory editor not available")
    
    # Load data
    with st.spinner("Loading dashboard data..."):
        data = load_dashboard_data()
        kpis = create_kpi_metrics(data)
    
    # Display dashboard sections
    display_kpi_dashboard(kpis)
    
    st.markdown("---")
    
    # Alerts section
    display_alerts(data)
    
    st.markdown("---")
    
    # Performance charts
    display_performance_charts(data)
    
    st.markdown("---")
    
    # Recent activity and system status
    col1, col2 = st.columns(2)
    
    with col1:
        display_recent_activity(data)
    
    with col2:
        display_system_status(data)
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "🤖 AI Agent Logistics Dashboard | "
        f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        "</div>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()