#!/usr/bin/env python3
"""
Supplier & Salesman Product Showcase Interface
Professional product presentation for suppliers and sales teams
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import Dict, List, Optional
from database.service import DatabaseService
from database.models import Product, SessionLocal
from user_product_models import USER_PRODUCT_CATALOG, get_user_product_by_id, ProductCategory

# Page configuration
st.set_page_config(
    page_title="Product Showcase - Supplier Portal",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = "All"
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "grid"
if 'selected_product_showcase' not in st.session_state:
    st.session_state.selected_product_showcase = None

# Custom CSS for professional showcase
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #2ca02c);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    .product-showcase-card {
        border: 1px solid #e0e0e0;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        background: linear-gradient(135deg, #ffffff, #f8f9fa);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    .product-showcase-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    .category-pill {
        background: linear-gradient(45deg, #ff6b6b, #ff8e8e);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-size: 0.9em;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
    }
    .price-tag {
        background: linear-gradient(45deg, #4ecdc4, #44a08d);
        color: white;
        padding: 10px 20px;
        border-radius: 25px;
        font-size: 1.2em;
        font-weight: bold;
        display: inline-block;
        margin: 10px 0;
    }
    .feature-badge {
        background: #e3f2fd;
        border: 1px solid #2196f3;
        color: #1976d2;
        padding: 6px 12px;
        border-radius: 20px;
        font-size: 0.85em;
        margin: 3px;
        display: inline-block;
        font-weight: 500;
    }
    .spec-table {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
    }
    .contact-card {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        text-align: center;
    }
    .action-button {
        background: linear-gradient(45deg, #ff6b6b, #ffa500);
        color: white;
        border: none;
        padding: 12px 25px;
        border-radius: 25px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .action-button:hover {
        transform: scale(1.05);
    }
    .gallery-image {
        border-radius: 10px;
        margin: 5px;
        cursor: pointer;
        transition: transform 0.3s ease;
    }
    .gallery-image:hover {
        transform: scale(1.1);
    }
    .stats-card {
        background: linear-gradient(135deg, #74b9ff, #0984e3);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin: 10px;
    }
</style>
""", unsafe_allow_html=True)

def get_product_images(product_id: str) -> Dict:
    """Get product images and marketing content"""
    try:
        db = SessionLocal()
        product = db.query(Product).filter(Product.product_id == product_id).first()
        db.close()
        
        if product:
            gallery_images = []
            key_features = []
            specifications = {}
            
            if product.gallery_images:
                try:
                    gallery_images = json.loads(product.gallery_images)
                except:
                    gallery_images = []
            
            if product.key_features:
                try:
                    key_features = json.loads(product.key_features)
                except:
                    key_features = []
            
            if product.specifications:
                try:
                    specifications = json.loads(product.specifications)
                except:
                    specifications = {}
            
            return {
                "primary_image_url": product.primary_image_url,
                "thumbnail_url": product.thumbnail_url,
                "gallery_images": gallery_images,
                "marketing_description": product.marketing_description,
                "key_features": key_features,
                "specifications": specifications
            }
    except Exception as e:
        st.error(f"Error getting product data: {e}")
    
    return {
        "primary_image_url": None,
        "thumbnail_url": None,
        "gallery_images": [],
        "marketing_description": None,
        "key_features": [],
        "specifications": {}
    }

def display_header():
    """Display professional header"""
    st.markdown("""
    <div class="main-header">
        <h1>🏪 Product Showcase Portal</h1>
        <p>Professional Product Catalog for Suppliers & Sales Teams</p>
    </div>
    """, unsafe_allow_html=True)

def display_filters():
    """Display filtering options"""
    st.markdown("### 🔍 Product Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        categories = ["All"] + [cat.value for cat in ProductCategory]
        selected_category = st.selectbox("Category", categories, key="category_filter")
        st.session_state.selected_category = selected_category
    
    with col2:
        suppliers = ["All", "SUPPLIER_001 (Syska)", "SUPPLIER_002 (Boast)", "SUPPLIER_003 (Premium)"]
        selected_supplier = st.selectbox("Supplier", suppliers, key="supplier_filter")
    
    with col3:
        price_ranges = ["All", "$0-$10", "$10-$25", "$25-$50", "$50+"]
        selected_price = st.selectbox("Price Range", price_ranges, key="price_filter")
    
    with col4:
        view_modes = ["Grid View", "List View", "Detailed View"]
        selected_view = st.selectbox("View Mode", view_modes, key="view_mode_selector")
        st.session_state.view_mode = selected_view.lower().replace(" ", "_")

def filter_products() -> List:
    """Filter products based on selections"""
    filtered_products = USER_PRODUCT_CATALOG
    
    # Category filter
    if st.session_state.selected_category != "All":
        filtered_products = [p for p in filtered_products if p.category.value == st.session_state.selected_category]
    
    # Additional filters would be applied here
    
    return filtered_products

def display_product_grid(products: List):
    """Display products in grid layout"""
    st.markdown("### 📦 Product Catalog")
    
    # Products per row based on view mode
    if st.session_state.view_mode == "grid_view":
        cols_per_row = 3
    elif st.session_state.view_mode == "list_view":
        cols_per_row = 1
    else:  # detailed_view
        cols_per_row = 2
    
    # Display products
    for i in range(0, len(products), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, col in enumerate(cols):
            if i + j < len(products):
                product = products[i + j]
                
                with col:
                    display_product_card(product)

def display_product_card(product):
    """Display individual product card"""
    images = get_product_images(product.product_id)
    
    st.markdown('<div class="product-showcase-card">', unsafe_allow_html=True)
    
    # Product image
    if images["primary_image_url"]:
        st.image(f"http://localhost:8002{images['primary_image_url']}", use_column_width=True)
    else:
        st.image("https://via.placeholder.com/300x200?text=Product+Image", use_column_width=True)
    
    # Product name and category
    st.markdown(f"### {product.name}")
    st.markdown(f'<div class="category-pill">{product.category.value}</div>', unsafe_allow_html=True)
    
    # Price
    st.markdown(f'<div class="price-tag">${product.unit_price:.2f}</div>', unsafe_allow_html=True)
    
    # Quick specs
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**ID:** `{product.product_id}`")
        st.markdown(f"**Weight:** {product.weight_kg}kg")
    with col2:
        st.markdown(f"**Dimensions:** {product.dimensions}")
        st.markdown(f"**Supplier:** {product.supplier_id}")
    
    # Key features (first 3)
    if images.get("key_features"):
        st.markdown("**Key Features:**")
        for feature in images["key_features"][:3]:
            st.markdown(f'<span class="feature-badge">{feature}</span>', unsafe_allow_html=True)
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 View Details", key=f"view_{product.product_id}"):
            st.session_state.selected_product_showcase = product.product_id
            st.rerun()
    
    with col2:
        if st.button("📞 Contact", key=f"contact_{product.product_id}"):
            display_contact_modal(product)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_product_details(product):
    """Display detailed product view"""
    images = get_product_images(product.product_id)
    
    # Back button
    if st.button("← Back to Catalog"):
        st.session_state.selected_product_showcase = None
        st.rerun()
    
    st.markdown(f"# {product.name}")
    st.markdown(f'<div class="category-pill">{product.category.value}</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        # Main product image
        if images["primary_image_url"]:
            st.image(f"http://localhost:8002{images['primary_image_url']}", use_column_width=True)
        else:
            st.image("https://via.placeholder.com/400x400?text=Product+Image", use_column_width=True)
        
        # Gallery images
        if images.get("gallery_images"):
            st.markdown("**Gallery**")
            gallery_cols = st.columns(min(len(images["gallery_images"]), 4))
            for i, img_url in enumerate(images["gallery_images"]):
                with gallery_cols[i % 4]:
                    st.image(f"http://localhost:8002{img_url}", width=80, key=f"gallery_{i}")
    
    with col2:
        # Price and basic info
        st.markdown(f'<div class="price-tag">${product.unit_price:.2f}</div>', unsafe_allow_html=True)
        
        # Basic specifications
        st.markdown("### 📋 Product Information")
        info_data = {
            "Product ID": product.product_id,
            "Category": product.category.value,
            "Weight": f"{product.weight_kg} kg",
            "Dimensions": product.dimensions,
            "Supplier": product.supplier_id,
            "Reorder Point": f"{product.reorder_point} units",
            "Max Stock": f"{product.max_stock} units"
        }
        
        for key, value in info_data.items():
            st.markdown(f"**{key}:** {value}")
        
        # Marketing description
        if images.get("marketing_description"):
            st.markdown("### 📝 Description")
            st.markdown(images["marketing_description"])
        
        # Key features
        if images.get("key_features"):
            st.markdown("### ⭐ Key Features")
            for feature in images["key_features"]:
                st.markdown(f'<span class="feature-badge">{feature}</span>', unsafe_allow_html=True)
    
    # Technical specifications
    if images.get("specifications"):
        st.markdown("### 🔧 Technical Specifications")
        st.markdown('<div class="spec-table">', unsafe_allow_html=True)
        
        specs = images["specifications"]
        spec_cols = st.columns(2)
        spec_items = list(specs.items())
        
        for i, (key, value) in enumerate(spec_items):
            with spec_cols[i % 2]:
                st.markdown(f"**{key}:** {value}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Action section
    st.markdown("### 📞 Take Action")
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)
    
    with action_col1:
        if st.button("📧 Request Quote", key=f"quote_{product.product_id}"):
            display_quote_request(product)
    
    with action_col2:
        if st.button("📦 Check Stock", key=f"stock_{product.product_id}"):
            st.info(f"Current Stock: {product.current_qty} units")
    
    with action_col3:
        if st.button("📄 Download Specs", key=f"download_{product.product_id}"):
            generate_spec_sheet(product)
    
    with action_col4:
        if st.button("🔗 Share Product", key=f"share_{product.product_id}"):
            st.success(f"Product link: /product/{product.product_id}")

def display_contact_modal(product):
    """Display contact information modal"""
    st.markdown(f"""
    <div class="contact-card">
        <h3>📞 Contact Information</h3>
        <p><strong>Product:</strong> {product.name}</p>
        <p><strong>Product ID:</strong> {product.product_id}</p>
        <p><strong>Supplier:</strong> {product.supplier_id}</p>
        <hr style="border-color: rgba(255,255,255,0.3);">
        <p><strong>📧 Email:</strong> sales@company.com</p>
        <p><strong>📱 Phone:</strong> +1 (555) 123-4567</p>
        <p><strong>💬 WhatsApp:</strong> +1 (555) 987-6543</p>
    </div>
    """, unsafe_allow_html=True)

def display_quote_request(product):
    """Display quote request form"""
    st.markdown("### 📋 Request Quote")
    
    with st.form(f"quote_form_{product.product_id}"):
        st.markdown(f"**Product:** {product.name}")
        st.markdown(f"**Product ID:** {product.product_id}")
        
        quantity = st.number_input("Quantity", min_value=1, value=10)
        urgency = st.selectbox("Urgency", ["Standard", "Urgent", "Emergency"])
        
        company_name = st.text_input("Company Name")
        contact_person = st.text_input("Contact Person")
        email = st.text_input("Email Address")
        phone = st.text_input("Phone Number")
        
        additional_notes = st.text_area("Additional Requirements")
        
        if st.form_submit_button("📤 Send Quote Request"):
            st.success("✅ Quote request sent successfully!")
            st.balloons()

def generate_spec_sheet(product):
    """Generate downloadable specification sheet"""
    images = get_product_images(product.product_id)
    
    # Create specification sheet data
    spec_data = {
        "Product Information": {
            "Name": product.name,
            "ID": product.product_id,
            "Category": product.category.value,
            "Price": f"${product.unit_price:.2f}",
            "Weight": f"{product.weight_kg} kg",
            "Dimensions": product.dimensions
        }
    }
    
    if images.get("specifications"):
        spec_data["Technical Specifications"] = images["specifications"]
    
    if images.get("key_features"):
        spec_data["Key Features"] = {f"Feature {i+1}": feature for i, feature in enumerate(images["key_features"])}
    
    # Convert to downloadable format (would be PDF in real implementation)
    st.success("📄 Specification sheet generated!")
    st.json(spec_data)

def display_statistics():
    """Display catalog statistics"""
    st.markdown("### 📊 Catalog Statistics")
    
    total_products = len(USER_PRODUCT_CATALOG)
    categories = {}
    suppliers = {}
    
    for product in USER_PRODUCT_CATALOG:
        cat = product.category.value
        sup = product.supplier_id
        
        categories[cat] = categories.get(cat, 0) + 1
        suppliers[sup] = suppliers.get(sup, 0) + 1
    
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    
    with stat_col1:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{total_products}</h3>
            <p>Total Products</p>
        </div>
        """, unsafe_allow_html=True)
    
    with stat_col2:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{len(categories)}</h3>
            <p>Categories</p>
        </div>
        """, unsafe_allow_html=True)
    
    with stat_col3:
        st.markdown(f"""
        <div class="stats-card">
            <h3>{len(suppliers)}</h3>
            <p>Suppliers</p>
        </div>
        """, unsafe_allow_html=True)
    
    with stat_col4:
        if total_products > 0:
            avg_price = sum(p.unit_price for p in USER_PRODUCT_CATALOG) / total_products
        else:
            avg_price = 0.0
        st.markdown(f"""
        <div class="stats-card">
            <h3>${avg_price:.2f}</h3>
            <p>Avg Price</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main showcase application"""
    # Header
    display_header()
    
    # Check if viewing specific product
    if st.session_state.selected_product_showcase:
        product = get_user_product_by_id(st.session_state.selected_product_showcase)
        if product:
            display_product_details(product)
        else:
            st.error("Product not found!")
            st.session_state.selected_product_showcase = None
            st.rerun()
    else:
        # Display main catalog
        display_statistics()
        
        st.markdown("---")
        
        display_filters()
        
        st.markdown("---")
        
        filtered_products = filter_products()
        
        if filtered_products:
            display_product_grid(filtered_products)
        else:
            st.warning("⚠️ No products found in catalog. Please check the USER_PRODUCT_CATALOG configuration.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
        <p>🏪 Professional Product Showcase | AI Logistics System</p>
        <p>📞 Contact: sales@company.com | 📱 Phone: +1 (555) 123-4567</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()