#!/usr/bin/env python3
"""
User Product Models from Excel File
Based on MODEL AND QTY copy.xlsx
"""

import pandas as pd
from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import os

class ProductCategory(Enum):
    POWER_BANK = "Power Bank"
    EARBUDS = "Earbuds"
    WATCH = "Smart Watch"
    NECKBAND = "Neckband"
    BLUETOOTH_SPEAKER = "Bluetooth Speaker"
    CABLE = "Cable"
    CHARGER = "Charger"
    HEADPHONES = "Headphones"

@dataclass
class UserProductModel:
    """User product model definition"""
    product_id: str
    name: str
    category: ProductCategory
    description: str
    unit_price: float
    weight_kg: float
    dimensions: str
    supplier_id: str
    reorder_point: int
    max_stock: int
    current_qty: int
    is_active: bool = True
    
    # Image fields
    primary_image_url: Optional[str] = None
    gallery_images: Optional[List[str]] = None
    thumbnail_url: Optional[str] = None
    
    # Marketing fields for suppliers/salesmen
    marketing_description: Optional[str] = None
    key_features: Optional[List[str]] = None
    specifications: Optional[Dict[str, str]] = None

# Data encryption utilities
from cryptography.fernet import Fernet
import os

# Initialize encryption (use environment variable or generate key)
ENCRYPTION_KEY = os.getenv("PRODUCT_ENCRYPTION_KEY", Fernet.generate_key())
cipher = Fernet(ENCRYPTION_KEY)

def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data using Fernet"""
    if not data:
        return ""
    return cipher.encrypt(data.encode()).decode()

def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data using Fernet"""
    if not encrypted_data:
        return ""
    try:
        return cipher.decrypt(encrypted_data.encode()).decode()
    except Exception:
        # Return original if decryption fails (for backward compatibility)
        return encrypted_data

# Load products from Excel file
def load_products_from_excel():
    """Load products from the Excel file"""
    file_path = 'data/MODEL AND QTY copy.xlsx'

    if not os.path.exists(file_path):
        print(f"Warning: Excel file not found: {file_path}")
        return []

    try:
        df = pd.read_excel(file_path)
        df_clean = df[['MODEL', 'QTY']].dropna()

        products = []
        for i, row in df_clean.iterrows():
            if row['MODEL'] == 'TOTAL':  # Skip the total row
                continue

            model_name = row['MODEL']
            qty = int(row['QTY'])

            # Generate product ID from model name
            product_id = f"USR{i+1:03d}"

            # Determine category based on model name
            category = ProductCategory.POWER_BANK  # Default
            if 'POWER BANK' in model_name.upper() or 'POWERBANK' in model_name.upper() or 'PB' in model_name.upper():
                category = ProductCategory.POWER_BANK
            elif 'EARBUDS' in model_name.upper() or 'EB' in model_name.upper():
                category = ProductCategory.EARBUDS
            elif 'WATCH' in model_name.upper():
                category = ProductCategory.WATCH
            elif 'NECKBAND' in model_name.upper() or 'NB' in model_name.upper():
                category = ProductCategory.NECKBAND
            elif 'SPEAKER' in model_name.upper() or 'BT' in model_name.upper():
                category = ProductCategory.BLUETOOTH_SPEAKER
            elif 'CABLE' in model_name.upper() or 'HF' in model_name.upper():
                category = ProductCategory.CABLE
            elif 'CHARGER' in model_name.upper() or 'WA' in model_name.upper() or 'PD' in model_name.upper() or 'QC' in model_name.upper():
                category = ProductCategory.CHARGER
            elif 'HE' in model_name.upper():
                category = ProductCategory.HEADPHONES

            # Determine supplier based on brand
            supplier_id = "SUPPLIER_001"  # Default
            if 'SYSKA' in model_name.upper():
                supplier_id = "SUPPLIER_001"  # Syska supplier
            elif 'BOAST' in model_name.upper():
                supplier_id = "SUPPLIER_002"  # Boast supplier

            # Set pricing based on category
            price_map = {
                ProductCategory.POWER_BANK: 25.99,
                ProductCategory.EARBUDS: 15.99,
                ProductCategory.WATCH: 45.99,
                ProductCategory.NECKBAND: 19.99,
                ProductCategory.BLUETOOTH_SPEAKER: 35.99,
                ProductCategory.CABLE: 8.99,
                ProductCategory.CHARGER: 12.99,
                ProductCategory.HEADPHONES: 29.99
            }

            # Set dimensions and weight based on category
            dimensions_map = {
                ProductCategory.POWER_BANK: "15 x 7 x 2 cm",
                ProductCategory.EARBUDS: "8 x 6 x 3 cm",
                ProductCategory.WATCH: "4 x 4 x 1 cm",
                ProductCategory.NECKBAND: "20 x 15 x 3 cm",
                ProductCategory.BLUETOOTH_SPEAKER: "18 x 8 x 8 cm",
                ProductCategory.CABLE: "15 x 10 x 2 cm",
                ProductCategory.CHARGER: "8 x 6 x 4 cm",
                ProductCategory.HEADPHONES: "20 x 18 x 8 cm"
            }

            weight_map = {
                ProductCategory.POWER_BANK: 0.4,
                ProductCategory.EARBUDS: 0.1,
                ProductCategory.WATCH: 0.2,
                ProductCategory.NECKBAND: 0.15,
                ProductCategory.BLUETOOTH_SPEAKER: 0.6,
                ProductCategory.CABLE: 0.1,
                ProductCategory.CHARGER: 0.2,
                ProductCategory.HEADPHONES: 0.3
            }

            # Generate random quantity instead of using the Excel quantity
            import random
            random_qty = random.randint(5, 50)  # Random quantity between 5 and 50

            # Encrypt sensitive supplier information
            encrypted_supplier_id = encrypt_sensitive_data(supplier_id)

            product = UserProductModel(
                product_id=product_id,
                name=model_name,
                category=category,
                description=f"{category.value} - {model_name}",
                unit_price=price_map.get(category, 20.99),
                weight_kg=weight_map.get(category, 0.3),
                dimensions=dimensions_map.get(category, "15 x 10 x 5 cm"),
                supplier_id=encrypted_supplier_id,  # Store encrypted
                reorder_point=max(5, random_qty // 3),  # Reorder when 1/3 of current qty
                max_stock=random_qty * 5,  # Max stock is 5x current qty
                current_qty=random_qty,
                is_active=True
            )

            products.append(product)

        return products

    except Exception as e:
        print(f"[ERROR] Error loading products from Excel: {e}")
        print("[INFO] Will use fallback sample products instead")
        return []

# Create fallback sample data if Excel file is not available
def create_fallback_products():
    """Create sample products when Excel file is not available"""
    return [
        UserProductModel(
            product_id="USR001",
            name="SYSKA Power Bank 10000mAh",
            category=ProductCategory.POWER_BANK,
            description="High capacity power bank with fast charging",
            unit_price=25.99,
            weight_kg=0.4,
            dimensions="15 x 7 x 2 cm",
            supplier_id="SUPPLIER_001",
            reorder_point=10,
            max_stock=100,
            current_qty=25
        ),
        UserProductModel(
            product_id="USR002",
            name="BOAST Wireless Earbuds",
            category=ProductCategory.EARBUDS,
            description="Premium wireless earbuds with noise cancellation",
            unit_price=15.99,
            weight_kg=0.1,
            dimensions="8 x 6 x 3 cm",
            supplier_id="SUPPLIER_002",
            reorder_point=15,
            max_stock=150,
            current_qty=45
        ),
        UserProductModel(
            product_id="USR003",
            name="Smart Watch Pro",
            category=ProductCategory.WATCH,
            description="Advanced smartwatch with health monitoring",
            unit_price=45.99,
            weight_kg=0.2,
            dimensions="4 x 4 x 1 cm",
            supplier_id="SUPPLIER_001",
            reorder_point=8,
            max_stock=80,
            current_qty=20
        ),
        UserProductModel(
            product_id="USR004",
            name="SYSKA Bluetooth Speaker",
            category=ProductCategory.BLUETOOTH_SPEAKER,
            description="Portable Bluetooth speaker with premium sound",
            unit_price=35.99,
            weight_kg=0.6,
            dimensions="18 x 8 x 8 cm",
            supplier_id="SUPPLIER_001",
            reorder_point=12,
            max_stock=120,
            current_qty=30
        ),
        UserProductModel(
            product_id="USR005",
            name="USB-C Fast Charger",
            category=ProductCategory.CHARGER,
            description="Quick charge USB-C adapter with PD support",
            unit_price=12.99,
            weight_kg=0.2,
            dimensions="8 x 6 x 4 cm",
            supplier_id="SUPPLIER_002",
            reorder_point=20,
            max_stock=200,
            current_qty=75
        )
    ]

# Load the product catalog
USER_PRODUCT_CATALOG = load_products_from_excel()
if not USER_PRODUCT_CATALOG:
    print("[INFO] Excel file not found, using fallback sample products")
    USER_PRODUCT_CATALOG = create_fallback_products()

# Helper functions
def get_user_product_by_id(product_id: str) -> Optional[UserProductModel]:
    """Get product by ID"""
    for product in USER_PRODUCT_CATALOG:
        if product.product_id == product_id:
            return product
    return None

def get_user_products_by_category(category: ProductCategory) -> List[UserProductModel]:
    """Get all products in a category"""
    return [p for p in USER_PRODUCT_CATALOG if p.category == category]

def get_user_products_by_supplier(supplier_id: str) -> List[UserProductModel]:
    """Get all products from a supplier"""
    # Decrypt supplier IDs for comparison
    return [p for p in USER_PRODUCT_CATALOG if decrypt_sensitive_data(p.supplier_id) == supplier_id]

def get_all_user_product_ids() -> List[str]:
    """Get all product IDs"""
    return [p.product_id for p in USER_PRODUCT_CATALOG]

def get_user_product_catalog_dict() -> Dict[str, UserProductModel]:
    """Get product catalog as dictionary"""
    return {p.product_id: p for p in USER_PRODUCT_CATALOG}

def get_low_stock_user_products() -> List[UserProductModel]:
    """Get products that need reordering based on current inventory"""
    return [p for p in USER_PRODUCT_CATALOG if p.current_qty <= p.reorder_point]

def get_user_product_quantities() -> Dict[str, int]:
    """Get current quantities for all products"""
    return {p.product_id: p.current_qty for p in USER_PRODUCT_CATALOG}

def get_user_products_by_brand(brand: str) -> List[UserProductModel]:
    """Get products by brand name"""
    return [p for p in USER_PRODUCT_CATALOG if brand.upper() in p.name.upper()]

# Generate sample orders and returns based on user products
def generate_sample_orders():
    """Generate sample orders using user products"""
    if not USER_PRODUCT_CATALOG:
        return []
    
    import random
    from datetime import datetime, timedelta
    
    orders = []
    order_statuses = ['Shipped', 'Delivered', 'Processing', 'In Transit', 'Cancelled']
    
    # Generate 15 sample orders
    for i in range(15):
        product = random.choice(USER_PRODUCT_CATALOG)
        order = {
            'order_id': 201 + i,
            'status': random.choice(order_statuses),
            'customer_id': f'CUST{i+1:03d}',
            'product_id': product.product_id,
            'quantity': random.randint(1, 3),
            'order_date': datetime.now() - timedelta(days=random.randint(0, 30))
        }
        orders.append(order)
    
    return orders

def generate_sample_returns():
    """Generate sample returns using user products"""
    if not USER_PRODUCT_CATALOG:
        return []
    
    import random
    from datetime import datetime, timedelta
    
    returns = []
    return_reasons = [
        'Defective - Not working properly',
        'Wrong product ordered',
        'Damaged during shipping',
        'Quality issues',
        'Customer changed mind',
        'Incompatible with device',
        'Battery issues',
        'Color not as expected',
        'Size issues',
        'Bulk return from retailer'
    ]
    
    # Generate returns for about 60% of products
    selected_products = random.sample(USER_PRODUCT_CATALOG, int(len(USER_PRODUCT_CATALOG) * 0.6))
    
    for product in selected_products:
        return_qty = random.randint(1, max(1, product.current_qty // 2))
        return_item = {
            'product_id': product.product_id,
            'return_quantity': return_qty,
            'reason': random.choice(return_reasons),
            'return_date': datetime.now() - timedelta(days=random.randint(1, 15))
        }
        returns.append(return_item)
    
    return returns

def generate_sample_shipments():
    """Generate sample shipments using user products"""
    orders = generate_sample_orders()
    if not orders:
        return []
    
    import random
    from datetime import datetime, timedelta
    
    shipments = []
    courier_ids = ['COURIER_001', 'COURIER_002', 'COURIER_003']
    shipment_statuses = ['created', 'picked_up', 'in_transit', 'out_for_delivery', 'delivered']
    
    # Generate shipments for shipped/delivered orders
    shipped_orders = [o for o in orders if o['status'] in ['Shipped', 'Delivered', 'In Transit']]
    
    for i, order in enumerate(shipped_orders[:10]):  # Limit to 10 shipments
        shipment = {
            'shipment_id': f'SHIP_{i+1:03d}',
            'order_id': order['order_id'],
            'courier_id': random.choice(courier_ids),
            'tracking_number': f'TRK{random.randint(100000000, 999999999)}',
            'status': random.choice(shipment_statuses),
            'origin_address': 'Electronics Warehouse, Tech District',
            'destination_address': f'Customer Address {i+1}',
            'estimated_delivery': datetime.now() + timedelta(days=random.randint(1, 5))
        }
        shipments.append(shipment)
    
    return shipments

if __name__ == "__main__":
    print("User Product Catalog Summary")
    print("=" * 60)
    
    if USER_PRODUCT_CATALOG:
        # Print catalog summary by category
        categories = {}
        total_qty = 0
        
        for product in USER_PRODUCT_CATALOG:
            if product.category not in categories:
                categories[product.category] = []
            categories[product.category].append(product)
            total_qty += product.current_qty
        
        for category, products in categories.items():
            category_qty = sum(p.current_qty for p in products)
            print(f"\n[CATEGORY] {category.value}: {len(products)} products, {category_qty} total qty")
            for product in products:
                print(f"   • {product.product_id}: {product.name} (Qty: {product.current_qty})")
        
        print(f"\n[STATS] Total Products: {len(USER_PRODUCT_CATALOG)}")
        print(f"[STATS] Total Categories: {len(categories)}")
        print(f"[STATS] Total Quantity: {total_qty}")
        
        # Show low stock products
        low_stock = get_low_stock_user_products()
        if low_stock:
            print(f"\n[WARNING] Low Stock Products ({len(low_stock)}):")
            for product in low_stock:
                print(f"   • {product.product_id}: {product.name} (Current: {product.current_qty}, Reorder: {product.reorder_point})")
        
        # Show brand distribution
        syska_products = get_user_products_by_brand('SYSKA')
        boast_products = get_user_products_by_brand('BOAST')
        print(f"\n[BRANDS] Brand Distribution:")
        print(f"   • SYSKA: {len(syska_products)} products")
        print(f"   • BOAST: {len(boast_products)} products")
        
    else:
        print("[ERROR] No products loaded from Excel file")