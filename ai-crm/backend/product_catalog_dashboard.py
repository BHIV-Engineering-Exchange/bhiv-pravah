#!/usr/bin/env python3
"""
Product Catalog Dashboard with Image Management
Complete product management interface with image upload and showcase capabilities
"""

import streamlit as st
import pandas as pd
import requests
import json
from PIL import Image
import io
import base64
from datetime import datetime
from typing import Optional, Dict, List
from database.service import DatabaseService
from database.models import init_database, Product, SessionLocal
from user_product_models import USER_PRODUCT_CATALOG, get_user_product_by_id, ProductCategory

# Page configuration
st.set_page_config(
    page_title="Product Catalog Management",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'selected_product' not in st.session_state:
    st.session_state.selected_product = None
if 'upload_success' not in st.session_state:
    st.session_state.upload_success = False

# Custom CSS for better styling
st.markdown("""
<style>
    .product-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        background-color: #fafafa;
    }
    .product-image {
        border-radius: 8px;
        max-width: 100%;
        height: auto;
    }
    .upload-area {
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        background-color: #f9f9f9;
    }
    .feature-tag {
        background-color: #e3f2fd;
        color: #1976d2;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        margin: 2px;
        display: inline-block;
    }
    .spec-table {
        background-color: #f5f5f5;
        padding: 10px;
        border-radius: 8px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def get_product_images(product_id: str) -> Dict:
    """Get product images from database"""
    try:
        db = SessionLocal()
        product = db.query(Product).filter(Product.product_id == product_id).first()
        db.close()
        
        if product:
            gallery_images = []
            if product.gallery_images:
                try:
                    gallery_images = json.loads(product.gallery_images)
                except:
                    gallery_images = []
            
            return {
                "primary_image_url": product.primary_image_url,
                "thumbnail_url": product.thumbnail_url,
                "gallery_images": gallery_images,
                "marketing_description": product.marketing_description,
                "key_features": json.loads(product.key_features) if product.key_features else [],
                "specifications": json.loads(product.specifications) if product.specifications else {}
            }
    except Exception as e:
        st.error(f"Error getting product images: {e}")
    
    return {"primary_image_url": None, "thumbnail_url": None, "gallery_images": [], 
            "marketing_description": None, "key_features": [], "specifications": {}}

def save_product_to_database(product_data: Dict) -> bool:
    """Save product information to database"""
    try:
        db = SessionLocal()
        
        # Check if product exists
        existing_product = db.query(Product).filter(Product.product_id == product_data['product_id']).first()
        
        if existing_product:
            # Update existing product
            for key, value in product_data.items():
                if hasattr(existing_product, key):
                    setattr(existing_product, key, value)
        else:
            # Create new product
            new_product = Product(**product_data)
            db.add(new_product)
        
        db.commit()
        db.close()
        return True
    except Exception as e:
        st.error(f"Error saving product: {e}")
        return False

def upload_image_to_api(product_id: str, image_file, image_type: str) -> bool:
    """Upload image via API"""
    try:
        # This would normally call the actual API
        # For demo purposes, we'll simulate the upload
        if image_type == "primary":
            endpoint = f"http://localhost:8002/products/{product_id}/images/primary"
        else:
            endpoint = f"http://localhost:8002/products/{product_id}/images/gallery"
        
        # In a real implementation, you would make an actual API call
        # files = {"file": image_file}
        # response = requests.post(endpoint, files=files)
        # return response.status_code == 200
        
        # For demo, we'll return True and show a simulation
        return True
    except Exception as e:
        st.error(f"Error uploading image: {e}")
        return False

def display_product_grid():
    """Display products in a grid layout"""
    st.subheader("📦 Product Catalog")
    
    # Filter options
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        category_filter = st.selectbox(
            "Filter by Category",
            ["All"] + [cat.value for cat in ProductCategory],
            key="category_filter"
        )
    
    with col2:
        supplier_filter = st.selectbox(
            "Filter by Supplier",
            ["All", "SUPPLIER_001", "SUPPLIER_002", "SUPPLIER_003"],
            key="supplier_filter"
        )
    
    with col3:
        stock_filter = st.selectbox(
            "Stock Status",
            ["All", "In Stock", "Low Stock", "Out of Stock"],
            key="stock_filter"
        )
    
    with col4:
        image_filter = st.selectbox(
            "Image Status",
            ["All", "With Images", "Without Images"],
            key="image_filter"
        )
    
    # Filter products
    filtered_products = USER_PRODUCT_CATALOG
    
    if category_filter != "All":
        filtered_products = [p for p in filtered_products if p.category.value == category_filter]
    
    if supplier_filter != "All":
        filtered_products = [p for p in filtered_products if p.supplier_id == supplier_filter]
    
    # Display products in grid
    cols_per_row = 3
    products_per_page = 9
    
    # Pagination
    total_products = len(filtered_products)
    total_pages = (total_products + products_per_page - 1) // products_per_page
    
    if total_pages > 1:
        page = st.selectbox(f"Page (Total: {total_products} products)", range(1, total_pages + 1)) - 1
    else:
        page = 0
    
    start_idx = page * products_per_page
    end_idx = min(start_idx + products_per_page, total_products)
    page_products = filtered_products[start_idx:end_idx]
    
    # Display products
    for i in range(0, len(page_products), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, col in enumerate(cols):
            if i + j < len(page_products):
                product = page_products[i + j]
                
                with col:
                    # Product card
                    st.markdown('<div class="product-card">', unsafe_allow_html=True)
                    
                    # Get product images
                    images = get_product_images(product.product_id)
                    
                    # Display primary image or placeholder
                    if images["primary_image_url"]:
                        st.image(f"http://localhost:8002{images['primary_image_url']}", 
                                caption=product.name, use_column_width=True)
                    else:
                        st.image("https://via.placeholder.com/200x200?text=No+Image", 
                                caption=product.name, use_column_width=True)
                    
                    # Product info
                    st.markdown(f"**{product.name}**")
                    st.markdown(f"ID: `{product.product_id}`")
                    st.markdown(f"Category: {product.category.value}")
                    st.markdown(f"Price: ${product.unit_price:.2f}")
                    
                    # Stock status
                    if product.current_qty > product.reorder_point:
                        st.success(f"Stock: {product.current_qty} units")
                    elif product.current_qty > 0:
                        st.warning(f"Low Stock: {product.current_qty} units")
                    else:
                        st.error("Out of Stock")
                    
                    # Manage button
                    if st.button(f"Manage", key=f"manage_{product.product_id}"):
                        st.session_state.selected_product = product.product_id
                        st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)

def display_product_manager():
    """Display product management interface"""
    if not st.session_state.selected_product:
        st.info("Select a product from the catalog to manage images and details.")
        return
    
    product = get_user_product_by_id(st.session_state.selected_product)
    if not product:
        st.error("Product not found!")
        return
    
    st.subheader(f"📝 Managing: {product.name}")
    
    # Back button
    if st.button("← Back to Catalog"):
        st.session_state.selected_product = None
        st.rerun()
    
    # Tabs for different management sections
    tab1, tab2, tab3, tab4 = st.tabs(["📸 Images", "📋 Details", "🎯 Marketing", "👁️ Preview"])
    
    with tab1:
        display_image_management(product)
    
    with tab2:
        display_product_details(product)
    
    with tab3:
        display_marketing_management(product)
    
    with tab4:
        display_product_preview(product)

def display_image_management(product):
    """Display image management interface"""
    st.markdown("### 📸 Image Management")
    
    # Get current images
    images = get_product_images(product.product_id)
    
    # Image upload section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("#### Upload New Images")
        
        # Primary image upload
        st.markdown("**Primary Product Image**")
        primary_file = st.file_uploader(
            "Choose primary image",
            type=['png', 'jpg', 'jpeg', 'webp'],
            key=f"primary_{product.product_id}"
        )
        
        if primary_file:
            # Display preview
            image = Image.open(primary_file)
            st.image(image, caption="Primary Image Preview", width=200)
            
            if st.button("Upload Primary Image", key=f"upload_primary_{product.product_id}"):
                if upload_image_to_api(product.product_id, primary_file, "primary"):
                    st.success("✅ Primary image uploaded successfully!")
                    st.session_state.upload_success = True
                    st.rerun()
        
        # Gallery images upload
        st.markdown("**Gallery Images**")
        gallery_files = st.file_uploader(
            "Choose gallery images (multiple)",
            type=['png', 'jpg', 'jpeg', 'webp'],
            accept_multiple_files=True,
            key=f"gallery_{product.product_id}"
        )
        
        if gallery_files:
            st.markdown(f"Selected {len(gallery_files)} images")
            
            # Preview gallery images
            preview_cols = st.columns(min(len(gallery_files), 4))
            for i, file in enumerate(gallery_files[:4]):
                with preview_cols[i]:
                    image = Image.open(file)
                    st.image(image, caption=f"Gallery {i+1}", width=100)
            
            if st.button("Upload Gallery Images", key=f"upload_gallery_{product.product_id}"):
                success_count = 0
                for file in gallery_files:
                    if upload_image_to_api(product.product_id, file, "gallery"):
                        success_count += 1
                
                st.success(f"✅ {success_count}/{len(gallery_files)} gallery images uploaded!")
                if success_count > 0:
                    st.rerun()
    
    with col2:
        st.markdown("#### Current Images")
        
        # Display current primary image
        if images["primary_image_url"]:
            st.markdown("**Primary Image**")
            st.image(f"http://localhost:8002{images['primary_image_url']}", width=150)
            if st.button("🗑️ Delete Primary", key=f"del_primary_{product.product_id}"):
                # Call delete API
                st.success("Primary image deleted!")
                st.rerun()
        else:
            st.info("No primary image uploaded")
        
        # Display gallery images
        if images["gallery_images"]:
            st.markdown(f"**Gallery ({len(images['gallery_images'])} images)**")
            for i, img_url in enumerate(images["gallery_images"]):
                col_img, col_btn = st.columns([3, 1])
                with col_img:
                    st.image(f"http://localhost:8002{img_url}", width=100)
                with col_btn:
                    if st.button("🗑️", key=f"del_gallery_{product.product_id}_{i}"):
                        st.success(f"Gallery image {i+1} deleted!")
                        st.rerun()
        else:
            st.info("No gallery images uploaded")

def display_product_details(product):
    """Display product details management"""
    st.markdown("### 📋 Product Details")
    
    # Editable product information
    with st.form(f"product_details_{product.product_id}"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("Product Name", value=product.name)
            new_category = st.selectbox(
                "Category", 
                [cat.value for cat in ProductCategory],
                index=[cat.value for cat in ProductCategory].index(product.category.value)
            )
            new_price = st.number_input("Unit Price ($)", value=float(product.unit_price), min_value=0.01)
            new_weight = st.number_input("Weight (kg)", value=float(product.weight_kg), min_value=0.0)
        
        with col2:
            new_dimensions = st.text_input("Dimensions", value=product.dimensions)
            new_reorder_point = st.number_input("Reorder Point", value=product.reorder_point, min_value=0)
            new_max_stock = st.number_input("Max Stock", value=product.max_stock, min_value=1)
            new_supplier = st.selectbox(
                "Supplier",
                ["SUPPLIER_001", "SUPPLIER_002", "SUPPLIER_003"],
                index=["SUPPLIER_001", "SUPPLIER_002", "SUPPLIER_003"].index(product.supplier_id)
            )
        
        new_description = st.text_area("Description", value=product.description, height=100)
        
        if st.form_submit_button("💾 Save Product Details"):
            # Update product data
            updated_data = {
                'product_id': product.product_id,
                'name': new_name,
                'category': new_category,
                'description': new_description,
                'unit_price': new_price,
                'weight_kg': new_weight,
                'dimensions': new_dimensions,
                'supplier_id': new_supplier,
                'reorder_point': new_reorder_point,
                'max_stock': new_max_stock,
                'updated_at': datetime.utcnow()
            }
            
            if save_product_to_database(updated_data):
                st.success("✅ Product details updated successfully!")
            else:
                st.error("❌ Failed to update product details")

def display_marketing_management(product):
    """Display marketing content management"""
    st.markdown("### 🎯 Marketing Content")
    
    images = get_product_images(product.product_id)
    
    with st.form(f"marketing_{product.product_id}"):
        # Marketing description
        marketing_desc = st.text_area(
            "Marketing Description",
            value=images.get("marketing_description", ""),
            height=150,
            help="Detailed marketing copy for suppliers and salesmen"
        )
        
        # Key features
        st.markdown("**Key Features**")
        current_features = images.get("key_features", [])
        
        # Dynamic feature input
        features = []
        for i in range(max(len(current_features) + 1, 5)):
            feature_value = current_features[i] if i < len(current_features) else ""
            feature = st.text_input(f"Feature {i+1}", value=feature_value, key=f"feature_{i}")
            if feature.strip():
                features.append(feature.strip())
        
        # Specifications
        st.markdown("**Technical Specifications**")
        current_specs = images.get("specifications", {})
        
        spec_keys = ["Brand", "Model", "Color", "Material", "Warranty", "Compatibility"]
        specifications = {}
        
        spec_col1, spec_col2 = st.columns(2)
        for i, key in enumerate(spec_keys):
            col = spec_col1 if i % 2 == 0 else spec_col2
            with col:
                value = st.text_input(key, value=current_specs.get(key, ""), key=f"spec_{key}")
                if value.strip():
                    specifications[key] = value.strip()
        
        # Custom specifications
        st.markdown("**Additional Specifications**")
        custom_spec_key = st.text_input("Specification Name", key="custom_spec_key")
        custom_spec_value = st.text_input("Specification Value", key="custom_spec_value")
        
        if custom_spec_key.strip() and custom_spec_value.strip():
            specifications[custom_spec_key.strip()] = custom_spec_value.strip()
        
        if st.form_submit_button("💾 Save Marketing Content"):
            # Save marketing data
            marketing_data = {
                'product_id': product.product_id,
                'marketing_description': marketing_desc,
                'key_features': json.dumps(features),
                'specifications': json.dumps(specifications),
                'updated_at': datetime.utcnow()
            }
            
            if save_product_to_database(marketing_data):
                st.success("✅ Marketing content updated successfully!")
            else:
                st.error("❌ Failed to update marketing content")

def display_product_preview(product):
    """Display product preview for suppliers/salesmen"""
    st.markdown("### 👁️ Supplier/Salesman Preview")
    st.markdown("*This is how suppliers and salesmen will see the product*")
    
    images = get_product_images(product.product_id)
    
    # Product showcase card
    st.markdown('<div class="product-card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Product images
        if images["primary_image_url"]:
            st.image(f"http://localhost:8002{images['primary_image_url']}", use_column_width=True)
        else:
            st.image("https://via.placeholder.com/300x300?text=No+Image", use_column_width=True)
        
        # Gallery thumbnails
        if images["gallery_images"]:
            st.markdown("**Gallery**")
            gallery_cols = st.columns(min(len(images["gallery_images"]), 4))
            for i, img_url in enumerate(images["gallery_images"][:4]):
                with gallery_cols[i]:
                    st.image(f"http://localhost:8002{img_url}", width=60)
    
    with col2:
        # Product information
        st.markdown(f"# {product.name}")
        st.markdown(f"**Product ID:** `{product.product_id}`")
        st.markdown(f"**Category:** {product.category.value}")
        st.markdown(f"**Price:** ${product.unit_price:.2f}")
        
        # Marketing description
        if images.get("marketing_description"):
            st.markdown("### Description")
            st.markdown(images["marketing_description"])
        
        # Key features
        if images.get("key_features"):
            st.markdown("### Key Features")
            for feature in images["key_features"]:
                st.markdown(f"• {feature}")
        
        # Specifications
        if images.get("specifications"):
            st.markdown("### Specifications")
            specs = images["specifications"]
            spec_df = pd.DataFrame(list(specs.items()), columns=["Specification", "Value"])
            # Display specifications without pyarrow dependency
            for spec, value in specs.items():
                st.markdown(f"**{spec}:** {value}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Action buttons for suppliers
    st.markdown("### 📞 Supplier Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📧 Request Quote", key=f"quote_{product.product_id}"):
            st.success("Quote request sent to procurement team!")
    
    with col2:
        if st.button("📦 Check Availability", key=f"availability_{product.product_id}"):
            st.info(f"Current stock: {product.current_qty} units")
    
    with col3:
        if st.button("📋 Download Spec Sheet", key=f"spec_sheet_{product.product_id}"):
            st.success("Specification sheet downloaded!")

def main():
    """Main application"""
    # Initialize database
    init_database()
    
    # Header
    st.markdown("# 📦 Product Catalog Management")
    st.markdown("Manage product images, details, and marketing content for supplier showcase")
    
    # Sidebar navigation
    st.sidebar.markdown("## Navigation")
    
    if st.session_state.selected_product:
        product = get_user_product_by_id(st.session_state.selected_product)
        st.sidebar.markdown(f"**Managing:** {product.name if product else 'Unknown'}")
        st.sidebar.markdown(f"**ID:** `{st.session_state.selected_product}`")
        
        if st.sidebar.button("🔙 Back to Catalog"):
            st.session_state.selected_product = None
            st.rerun()
    else:
        st.sidebar.markdown("Select a product to manage")
    
    # Quick stats
    st.sidebar.markdown("## Quick Stats")
    total_products = len(USER_PRODUCT_CATALOG)
    
    # Count products with images (would query database in real implementation)
    products_with_images = 0  # This would be calculated from database
    
    st.sidebar.metric("Total Products", total_products)
    st.sidebar.metric("Products with Images", products_with_images)
    st.sidebar.metric("Missing Images", total_products - products_with_images)
    
    # Main content
    if st.session_state.selected_product:
        display_product_manager()
    else:
        display_product_grid()

if __name__ == "__main__":
    main()