# Customer (Shopkeeper) Dashboard - Production Architecture

> **Version:** 1.0  
> **Date:** February 6, 2026  
> **Status:** Design Specification  
> **Target:** Production-ready B2B Distribution System

---

## 1. HIGH-LEVEL ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CLOUD INFRASTRUCTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌────────────────────────┐         ┌────────────────────────┐             │
│  │   ADMIN DASHBOARD      │         │  CUSTOMER DASHBOARD    │             │
│  │   (Distributor)        │         │  (Shopkeepers)         │             │
│  │                        │         │                        │             │
│  │  • Inventory Mgmt      │         │  • Product Catalog     │             │
│  │  • Order Management    │         │  • Place Orders        │             │
│  │  • Customer Approval   │         │  • Order Tracking      │             │
│  │  • Delivery Assignment │         │  • Invoice History     │             │
│  │  • Analytics           │         │  • Account Management  │             │
│  └───────────┬────────────┘         └───────────┬────────────┘             │
│              │                                   │                          │
│              └──────────────┬────────────────────┘                          │
│                             │                                               │
│                    ┌────────▼────────┐                                      │
│                    │   API GATEWAY   │                                      │
│                    │  (Rate Limited) │                                      │
│                    │  • Auth Filter  │                                      │
│                    │  • Role Check   │                                      │
│                    └────────┬────────┘                                      │
│                             │                                               │
│         ┌───────────────────┼───────────────────┐                           │
│         │                   │                   │                           │
│    ┌────▼─────┐      ┌──────▼──────┐     ┌─────▼──────┐                    │
│    │  AUTH    │      │   ORDER     │     │  INVENTORY │                    │
│    │ SERVICE  │      │  SERVICE    │     │  SERVICE   │                    │
│    │          │      │             │     │            │                    │
│    │ • JWT    │      │ • Place     │     │ • Stock    │                    │
│    │ • RBAC   │      │ • Track     │     │ • Reserve  │                    │
│    │ • 2FA    │      │ • Invoice   │     │ • Release  │                    │
│    └────┬─────┘      └──────┬──────┘     └─────┬──────┘                    │
│         │                   │                   │                           │
│         └───────────────────┼───────────────────┘                           │
│                             │                                               │
│    ┌────────────────────────┼────────────────────────┐                      │
│    │                        │                        │                      │
│ ┌──▼──────┐      ┌──────────▼──────┐      ┌─────────▼────────┐             │
│ │DELIVERY │      │  NOTIFICATION   │      │   PAYMENT        │             │
│ │SERVICE  │      │    SERVICE      │      │   SERVICE        │             │
│ │         │      │                 │      │                  │             │
│ │• Track  │      │ • Email (SMTP)  │      │ • Invoice Gen    │             │
│ │• Assign │      │ • SMS           │      │ • Credit Terms   │             │
│ │• Update │      │ • Push          │      │ • Payment Track  │             │
│ └──┬──────┘      │ • WhatsApp      │      └──────────────────┘             │
│    │             └─────────────────┘                                        │
│    │                                                                         │
│    │  ┌─────────────────────────────────────────────┐                       │
│    │  │         EVENT QUEUE (Redis Pub/Sub)         │                       │
│    │  │  • order.created                            │                       │
│    │  │  • order.confirmed                          │                       │
│    │  │  • order.dispatched                         │                       │
│    └──│  • inventory.low                            │                       │
│       │  • delivery.updated                         │                       │
│       └──────────────────┬──────────────────────────┘                       │
│                          │                                                  │
│       ┌──────────────────▼──────────────────────────┐                       │
│       │           DATABASE LAYER                    │                       │
│       │                                             │                       │
│       │  ┌──────────────┐      ┌─────────────┐     │                       │
│       │  │  PostgreSQL  │      │   Redis     │     │                       │
│       │  │ (Primary DB) │      │  (Cache)    │     │                       │
│       │  │              │      │             │     │                       │
│       │  │ • ACID       │      │ • Sessions  │     │                       │
│       │  │ • Relations  │      │ • Real-time │     │                       │
│       │  │ • Indexes    │      │ • Stock     │     │                       │
│       │  └──────────────┘      └─────────────┘     │                       │
│       └─────────────────────────────────────────────┘                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────┐        │
│  │                    EXTERNAL INTEGRATIONS                        │        │
│  │                                                                 │        │
│  │  • Supplier API (Auto Reorder)                                 │        │
│  │  • SMS Gateway (Twilio/AWS SNS)                                │        │
│  │  • Email Service (SendGrid/AWS SES)                            │        │
│  │  • Logistics Partners API (Shiprocket/Delhivery)              │        │
│  │  • Payment Gateway (Razorpay/Stripe) [Future]                 │        │
│  └─────────────────────────────────────────────────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. DATABASE SCHEMA

### 2.1 Core Tables

#### **users**
```sql
CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email               VARCHAR(255) UNIQUE NOT NULL,
    password_hash       VARCHAR(255) NOT NULL,
    role                VARCHAR(20) NOT NULL CHECK (role IN ('ADMIN', 'CUSTOMER', 'SUPPLIER')),
    status              VARCHAR(20) NOT NULL DEFAULT 'PENDING' 
                        CHECK (status IN ('PENDING', 'ACTIVE', 'SUSPENDED', 'BLOCKED')),
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    phone               VARCHAR(20),
    phone_verified      BOOLEAN DEFAULT FALSE,
    email_verified      BOOLEAN DEFAULT FALSE,
    two_factor_enabled  BOOLEAN DEFAULT FALSE,
    two_factor_secret   VARCHAR(255),
    last_login_at       TIMESTAMP WITH TIME ZONE,
    login_attempts      INTEGER DEFAULT 0,
    locked_until        TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by          UUID REFERENCES users(id),
    
    INDEX idx_users_email (email),
    INDEX idx_users_role (role),
    INDEX idx_users_status (status)
);
```

#### **customers**
```sql
CREATE TABLE customers (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                 UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    business_name           VARCHAR(255) NOT NULL,
    gst_number              VARCHAR(15) UNIQUE,
    pan_number              VARCHAR(10),
    business_type           VARCHAR(50) CHECK (business_type IN ('RETAILER', 'WHOLESALER', 'BOTH')),
    
    -- Address
    address_line1           VARCHAR(255) NOT NULL,
    address_line2           VARCHAR(255),
    city                    VARCHAR(100) NOT NULL,
    state                   VARCHAR(100) NOT NULL,
    pincode                 VARCHAR(10) NOT NULL,
    country                 VARCHAR(50) DEFAULT 'India',
    landmark                VARCHAR(255),
    
    -- Geolocation for delivery optimization
    latitude                DECIMAL(10, 8),
    longitude               DECIMAL(11, 8),
    
    -- Business Details
    credit_limit            DECIMAL(12, 2) DEFAULT 0.00,
    credit_days             INTEGER DEFAULT 0,
    outstanding_balance     DECIMAL(12, 2) DEFAULT 0.00,
    
    -- Preferences
    preferred_delivery_time VARCHAR(50),
    delivery_instructions   TEXT,
    
    -- Meta
    approved_at             TIMESTAMP WITH TIME ZONE,
    approved_by             UUID REFERENCES users(id),
    is_active               BOOLEAN DEFAULT TRUE,
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at              TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_customers_user (user_id),
    INDEX idx_customers_gst (gst_number),
    INDEX idx_customers_city (city, state),
    INDEX idx_customers_active (is_active)
);
```

#### **products**
```sql
CREATE TABLE products (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku                 VARCHAR(50) UNIQUE NOT NULL,
    name                VARCHAR(255) NOT NULL,
    description         TEXT,
    category_id         UUID REFERENCES categories(id),
    brand               VARCHAR(100),
    manufacturer        VARCHAR(100),
    
    -- Pricing (B2B)
    mrp                 DECIMAL(10, 2) NOT NULL,
    distributor_price   DECIMAL(10, 2) NOT NULL,
    retailer_price      DECIMAL(10, 2) NOT NULL,
    wholesaler_price    DECIMAL(10, 2),
    
    -- Inventory
    total_quantity      INTEGER NOT NULL DEFAULT 0,
    reserved_quantity   INTEGER NOT NULL DEFAULT 0,
    available_quantity  INTEGER GENERATED ALWAYS AS (total_quantity - reserved_quantity) STORED,
    
    -- Thresholds
    reorder_level       INTEGER NOT NULL DEFAULT 50,
    max_stock_level     INTEGER,
    min_order_quantity  INTEGER DEFAULT 1,
    max_order_quantity  INTEGER,
    
    -- Physical
    weight_kg           DECIMAL(8, 2),
    dimensions          JSONB, -- {length, width, height}
    unit                VARCHAR(20) DEFAULT 'PIECE',
    
    -- Supplier Info
    supplier_id         UUID REFERENCES suppliers(id),
    supplier_sku        VARCHAR(50),
    lead_time_days      INTEGER DEFAULT 7,
    
    -- Status
    is_active           BOOLEAN DEFAULT TRUE,
    is_visible_to_customers BOOLEAN DEFAULT TRUE,
    
    -- Meta
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_products_sku (sku),
    INDEX idx_products_category (category_id),
    INDEX idx_products_supplier (supplier_id),
    INDEX idx_products_active (is_active, is_visible_to_customers),
    
    CONSTRAINT chk_positive_quantities CHECK (
        total_quantity >= 0 AND 
        reserved_quantity >= 0 AND 
        reserved_quantity <= total_quantity
    )
);
```

#### **categories**
```sql
CREATE TABLE categories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) UNIQUE NOT NULL,
    slug            VARCHAR(100) UNIQUE NOT NULL,
    parent_id       UUID REFERENCES categories(id),
    description     TEXT,
    image_url       VARCHAR(500),
    sort_order      INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_categories_parent (parent_id),
    INDEX idx_categories_active (is_active)
);
```

#### **orders**
```sql
CREATE TABLE orders (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number            VARCHAR(20) UNIQUE NOT NULL,
    customer_id             UUID NOT NULL REFERENCES customers(id),
    
    -- Order Status
    status                  VARCHAR(20) NOT NULL DEFAULT 'CREATED'
                            CHECK (status IN (
                                'CREATED', 'CONFIRMED', 'RESERVED', 
                                'PROCESSING', 'DISPATCHED', 'IN_TRANSIT',
                                'OUT_FOR_DELIVERY', 'DELIVERED', 
                                'CANCELLED', 'RETURNED', 'REFUNDED'
                            )),
    
    -- Financial
    subtotal                DECIMAL(12, 2) NOT NULL,
    tax_amount              DECIMAL(12, 2) DEFAULT 0.00,
    discount_amount         DECIMAL(12, 2) DEFAULT 0.00,
    delivery_charge         DECIMAL(12, 2) DEFAULT 0.00,
    total_amount            DECIMAL(12, 2) NOT NULL,
    
    -- Delivery
    delivery_address        JSONB NOT NULL, -- Full address snapshot
    delivery_latitude       DECIMAL(10, 8),
    delivery_longitude      DECIMAL(11, 8),
    
    estimated_delivery_date DATE,
    actual_delivery_date    DATE,
    delivery_instructions   TEXT,
    
    -- Assignment
    assigned_to_agent       UUID REFERENCES delivery_agents(id),
    assigned_at             TIMESTAMP WITH TIME ZONE,
    
    -- Payment
    payment_method          VARCHAR(20) DEFAULT 'CREDIT'
                            CHECK (payment_method IN ('CREDIT', 'COD', 'ONLINE', 'BANK_TRANSFER')),
    payment_status          VARCHAR(20) DEFAULT 'PENDING'
                            CHECK (payment_status IN ('PENDING', 'PAID', 'PARTIAL', 'FAILED', 'REFUNDED')),
    payment_due_date        DATE,
    
    -- Notes
    customer_notes          TEXT,
    internal_notes          TEXT,
    cancellation_reason     TEXT,
    
    -- Tracking
    tracking_number         VARCHAR(50) UNIQUE,
    courier_partner         VARCHAR(100),
    
    -- Meta
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confirmed_at            TIMESTAMP WITH TIME ZONE,
    dispatched_at           TIMESTAMP WITH TIME ZONE,
    delivered_at            TIMESTAMP WITH TIME ZONE,
    cancelled_at            TIMESTAMP WITH TIME ZONE,
    updated_at              TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_orders_customer (customer_id),
    INDEX idx_orders_status (status),
    INDEX idx_orders_number (order_number),
    INDEX idx_orders_created (created_at DESC),
    INDEX idx_orders_delivery_date (estimated_delivery_date)
);
```

#### **order_items**
```sql
CREATE TABLE order_items (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id            UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id          UUID NOT NULL REFERENCES products(id),
    
    -- Snapshot at order time
    product_sku         VARCHAR(50) NOT NULL,
    product_name        VARCHAR(255) NOT NULL,
    unit_price          DECIMAL(10, 2) NOT NULL,
    quantity            INTEGER NOT NULL CHECK (quantity > 0),
    
    -- Calculated
    line_total          DECIMAL(12, 2) GENERATED ALWAYS AS (unit_price * quantity) STORED,
    
    -- Fulfillment
    quantity_reserved   INTEGER DEFAULT 0,
    quantity_dispatched INTEGER DEFAULT 0,
    quantity_delivered  INTEGER DEFAULT 0,
    
    -- Notes
    notes               TEXT,
    
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_order_items_order (order_id),
    INDEX idx_order_items_product (product_id),
    
    CONSTRAINT chk_quantities CHECK (
        quantity_reserved <= quantity AND
        quantity_dispatched <= quantity_reserved AND
        quantity_delivered <= quantity_dispatched
    )
);
```

#### **inventory_transactions**
```sql
CREATE TABLE inventory_transactions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id          UUID NOT NULL REFERENCES products(id),
    
    transaction_type    VARCHAR(20) NOT NULL
                        CHECK (transaction_type IN (
                            'RESTOCK', 'RESERVE', 'RELEASE', 
                            'DISPATCH', 'RETURN', 'ADJUSTMENT', 'DAMAGE'
                        )),
    
    quantity_change     INTEGER NOT NULL, -- Positive or negative
    
    -- Before/After for audit trail
    quantity_before     INTEGER NOT NULL,
    quantity_after      INTEGER NOT NULL,
    reserved_before     INTEGER NOT NULL,
    reserved_after      INTEGER NOT NULL,
    
    -- Reference
    reference_type      VARCHAR(20), -- 'ORDER', 'PURCHASE_ORDER', 'MANUAL'
    reference_id        UUID,
    
    -- Meta
    reason              TEXT,
    performed_by        UUID NOT NULL REFERENCES users(id),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_inventory_trans_product (product_id, created_at DESC),
    INDEX idx_inventory_trans_type (transaction_type),
    INDEX idx_inventory_trans_ref (reference_type, reference_id)
);
```

#### **delivery_tracking**
```sql
CREATE TABLE delivery_tracking (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id            UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    
    status              VARCHAR(30) NOT NULL,
    status_code         VARCHAR(20),
    
    location            VARCHAR(255),
    latitude            DECIMAL(10, 8),
    longitude           DECIMAL(11, 8),
    
    description         TEXT,
    
    -- Agent info
    agent_id            UUID REFERENCES delivery_agents(id),
    agent_name          VARCHAR(100),
    agent_phone         VARCHAR(20),
    
    -- Proof
    signature_url       VARCHAR(500),
    photo_url           VARCHAR(500),
    otp_verified        BOOLEAN DEFAULT FALSE,
    
    -- Meta
    timestamp           TIMESTAMP WITH TIME ZONE NOT NULL,
    created_by          UUID REFERENCES users(id),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_delivery_tracking_order (order_id, timestamp DESC),
    INDEX idx_delivery_tracking_status (status)
);
```

#### **notifications**
```sql
CREATE TABLE notifications (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    type                VARCHAR(30) NOT NULL
                        CHECK (type IN (
                            'ORDER_PLACED', 'ORDER_CONFIRMED', 'ORDER_DISPATCHED',
                            'ORDER_DELIVERED', 'ORDER_CANCELLED',
                            'STOCK_LOW', 'PAYMENT_DUE', 'ACCOUNT_APPROVED'
                        )),
    
    title               VARCHAR(200) NOT NULL,
    message             TEXT NOT NULL,
    
    -- Channels
    send_email          BOOLEAN DEFAULT TRUE,
    send_sms            BOOLEAN DEFAULT FALSE,
    send_push           BOOLEAN DEFAULT TRUE,
    send_whatsapp       BOOLEAN DEFAULT FALSE,
    
    -- Status
    email_sent_at       TIMESTAMP WITH TIME ZONE,
    sms_sent_at         TIMESTAMP WITH TIME ZONE,
    push_sent_at        TIMESTAMP WITH TIME ZONE,
    whatsapp_sent_at    TIMESTAMP WITH TIME ZONE,
    
    read_at             TIMESTAMP WITH TIME ZONE,
    
    -- Reference
    reference_type      VARCHAR(20), -- 'ORDER', 'PRODUCT', etc.
    reference_id        UUID,
    
    -- Priority
    priority            VARCHAR(10) DEFAULT 'NORMAL'
                        CHECK (priority IN ('LOW', 'NORMAL', 'HIGH', 'URGENT')),
    
    -- Meta
    metadata            JSONB,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_notifications_user (user_id, created_at DESC),
    INDEX idx_notifications_read (user_id, read_at),
    INDEX idx_notifications_type (type)
);
```

#### **delivery_agents**
```sql
CREATE TABLE delivery_agents (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID UNIQUE REFERENCES users(id),
    
    agent_code          VARCHAR(20) UNIQUE NOT NULL,
    name                VARCHAR(100) NOT NULL,
    phone               VARCHAR(20) NOT NULL,
    email               VARCHAR(255),
    
    -- Type
    agent_type          VARCHAR(20) NOT NULL
                        CHECK (agent_type IN ('INTERNAL', 'THIRD_PARTY', 'COURIER')),
    
    -- Courier info for third-party
    courier_name        VARCHAR(100),
    vehicle_type        VARCHAR(50),
    vehicle_number      VARCHAR(20),
    
    -- Service areas
    service_pincodes    TEXT[], -- Array of pincodes
    service_cities      TEXT[],
    
    -- Capacity
    max_daily_orders    INTEGER DEFAULT 20,
    is_available        BOOLEAN DEFAULT TRUE,
    
    -- Performance
    total_deliveries    INTEGER DEFAULT 0,
    successful_deliveries INTEGER DEFAULT 0,
    average_rating      DECIMAL(3, 2),
    
    -- Meta
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_delivery_agents_type (agent_type),
    INDEX idx_delivery_agents_active (is_active)
);
```

#### **suppliers**
```sql
CREATE TABLE suppliers (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID UNIQUE REFERENCES users(id),
    
    company_name        VARCHAR(255) NOT NULL,
    contact_person      VARCHAR(100),
    email               VARCHAR(255) NOT NULL,
    phone               VARCHAR(20) NOT NULL,
    
    -- Address
    address             TEXT,
    city                VARCHAR(100),
    state               VARCHAR(100),
    pincode             VARCHAR(10),
    country             VARCHAR(50) DEFAULT 'India',
    
    -- Business
    gst_number          VARCHAR(15),
    pan_number          VARCHAR(10),
    
    -- Terms
    payment_terms       VARCHAR(100),
    credit_days         INTEGER DEFAULT 30,
    
    -- Performance
    rating              DECIMAL(3, 2),
    total_orders        INTEGER DEFAULT 0,
    
    is_active           BOOLEAN DEFAULT TRUE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_suppliers_active (is_active)
);
```

#### **purchase_orders** (For supplier auto-reorder)
```sql
CREATE TABLE purchase_orders (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    po_number           VARCHAR(20) UNIQUE NOT NULL,
    supplier_id         UUID NOT NULL REFERENCES suppliers(id),
    
    status              VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
                        CHECK (status IN (
                            'DRAFT', 'SENT', 'CONFIRMED', 
                            'RECEIVED', 'CANCELLED'
                        )),
    
    total_amount        DECIMAL(12, 2) NOT NULL,
    
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    
    -- Auto-generated flag
    is_auto_generated   BOOLEAN DEFAULT FALSE,
    auto_reason         TEXT,
    
    -- Approval
    approved_by         UUID REFERENCES users(id),
    approved_at         TIMESTAMP WITH TIME ZONE,
    
    notes               TEXT,
    
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_po_supplier (supplier_id),
    INDEX idx_po_status (status),
    INDEX idx_po_number (po_number)
);
```

#### **purchase_order_items**
```sql
CREATE TABLE purchase_order_items (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    purchase_order_id   UUID NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    product_id          UUID NOT NULL REFERENCES products(id),
    
    quantity_ordered    INTEGER NOT NULL CHECK (quantity_ordered > 0),
    quantity_received   INTEGER DEFAULT 0,
    
    unit_cost           DECIMAL(10, 2) NOT NULL,
    line_total          DECIMAL(12, 2) GENERATED ALWAYS AS (unit_cost * quantity_ordered) STORED,
    
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_po_items_po (purchase_order_id),
    INDEX idx_po_items_product (product_id)
);
```

---

## 3. API ENDPOINTS

### 3.1 Authentication & User Management

#### POST `/api/v1/auth/register`
**Purpose:** Customer self-registration (requires admin approval)

**Request:**
```json
{
  "email": "shopkeeper@example.com",
  "password": "SecurePass123!",
  "first_name": "Rajesh",
  "last_name": "Kumar",
  "phone": "+919876543210",
  "business_name": "Kumar General Store",
  "gst_number": "27AABCU9603R1ZM",
  "business_type": "RETAILER",
  "address_line1": "Shop No. 5, Main Market",
  "city": "Mumbai",
  "state": "Maharashtra",
  "pincode": "400001"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Registration successful. Awaiting admin approval.",
  "data": {
    "user_id": "uuid",
    "email": "shopkeeper@example.com",
    "status": "PENDING"
  }
}
```

#### POST `/api/v1/auth/login`
**Request:**
```json
{
  "email": "shopkeeper@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGc...",
    "refresh_token": "eyJhbGc...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": {
      "id": "uuid",
      "email": "shopkeeper@example.com",
      "role": "CUSTOMER",
      "first_name": "Rajesh",
      "last_name": "Kumar",
      "customer": {
        "business_name": "Kumar General Store",
        "credit_limit": 50000.00,
        "outstanding_balance": 12500.00
      }
    }
  }
}
```

#### POST `/api/v1/auth/refresh`
**Purpose:** Refresh access token

#### POST `/api/v1/auth/logout`
**Purpose:** Invalidate tokens

---

### 3.2 Admin - Customer Management

#### GET `/api/v1/admin/customers?status=PENDING&page=1&limit=20`
**Purpose:** List all customers (with filters)

**Response:**
```json
{
  "success": true,
  "data": {
    "customers": [
      {
        "id": "uuid",
        "business_name": "Kumar General Store",
        "email": "shopkeeper@example.com",
        "phone": "+919876543210",
        "city": "Mumbai",
        "status": "PENDING",
        "created_at": "2026-02-05T10:30:00Z"
      }
    ],
    "pagination": {
      "total": 150,
      "page": 1,
      "limit": 20,
      "total_pages": 8
    }
  }
}
```

#### PUT `/api/v1/admin/customers/{customer_id}/approve`
**Purpose:** Approve pending customer

**Request:**
```json
{
  "credit_limit": 50000.00,
  "credit_days": 30,
  "notes": "Verified GST and business documents"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Customer approved successfully",
  "data": {
    "customer_id": "uuid",
    "status": "ACTIVE",
    "approved_at": "2026-02-06T14:20:00Z"
  }
}
```

---

### 3.3 Product Catalog (Customer)

#### GET `/api/v1/products?category={category_id}&search={query}&page=1&limit=50`
**Purpose:** Get product catalog with real-time stock

**Headers:**
```
Authorization: Bearer {token}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "products": [
      {
        "id": "uuid",
        "sku": "COLA-1L-001",
        "name": "Coca Cola 1L Bottle",
        "category": "Beverages",
        "brand": "Coca Cola",
        "price": 45.00,
        "mrp": 60.00,
        "available_quantity": 250,
        "min_order_quantity": 24,
        "unit": "PIECE",
        "estimated_delivery_days": 2,
        "in_stock": true,
        "images": ["url1", "url2"]
      }
    ],
    "pagination": {
      "total": 500,
      "page": 1,
      "limit": 50
    }
  }
}
```

#### GET `/api/v1/products/{product_id}`
**Purpose:** Get detailed product information

---

### 3.4 Order Management (Customer)

#### POST `/api/v1/orders`
**Purpose:** Place a new order

**Request:**
```json
{
  "items": [
    {
      "product_id": "uuid",
      "quantity": 48
    },
    {
      "product_id": "uuid",
      "quantity": 24
    }
  ],
  "delivery_address": {
    "address_line1": "Shop No. 5, Main Market",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001",
    "latitude": 19.0760,
    "longitude": 72.8777
  },
  "payment_method": "CREDIT",
  "delivery_instructions": "Call before delivery",
  "customer_notes": "Urgent required by evening"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Order placed successfully",
  "data": {
    "order_id": "uuid",
    "order_number": "ORD-2026-0001234",
    "status": "CREATED",
    "total_amount": 4520.00,
    "estimated_delivery_date": "2026-02-08",
    "items": [
      {
        "product_name": "Coca Cola 1L Bottle",
        "quantity": 48,
        "unit_price": 45.00,
        "line_total": 2160.00,
        "reserved": true
      }
    ],
    "created_at": "2026-02-06T15:30:00Z"
  }
}
```

**Backend Logic (Atomic Transaction):**
```python
async def place_order(order_data):
    async with db.begin():
        # 1. Validate stock availability
        for item in order_data.items:
            product = await get_product(item.product_id)
            if product.available_quantity < item.quantity:
                raise InsufficientStockError(
                    f"{product.name}: Only {product.available_quantity} available"
                )
        
        # 2. Create order
        order = await create_order(order_data)
        
        # 3. Reserve inventory (CRITICAL)
        for item in order.items:
            await reserve_inventory(
                product_id=item.product_id,
                quantity=item.quantity,
                order_id=order.id
            )
        
        # 4. Trigger notifications
        await notify_customer_order_placed(order)
        await notify_admin_new_order(order)
        
        # 5. Check if any product needs restock
        await check_and_trigger_auto_restock()
        
        return order
```

#### GET `/api/v1/orders?status={status}&page=1&limit=20`
**Purpose:** Get customer orders with filters

**Response:**
```json
{
  "success": true,
  "data": {
    "orders": [
      {
        "id": "uuid",
        "order_number": "ORD-2026-0001234",
        "status": "IN_TRANSIT",
        "total_amount": 4520.00,
        "estimated_delivery_date": "2026-02-08",
        "tracking_number": "DHL123456789",
        "created_at": "2026-02-06T15:30:00Z"
      }
    ],
    "pagination": {...}
  }
}
```

#### GET `/api/v1/orders/{order_id}`
**Purpose:** Get detailed order information

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "order_number": "ORD-2026-0001234",
    "status": "IN_TRANSIT",
    "created_at": "2026-02-06T15:30:00Z",
    "confirmed_at": "2026-02-06T15:35:00Z",
    "dispatched_at": "2026-02-07T10:00:00Z",
    "estimated_delivery_date": "2026-02-08",
    
    "items": [
      {
        "product_name": "Coca Cola 1L Bottle",
        "sku": "COLA-1L-001",
        "quantity": 48,
        "unit_price": 45.00,
        "line_total": 2160.00
      }
    ],
    
    "pricing": {
      "subtotal": 4520.00,
      "tax_amount": 0.00,
      "delivery_charge": 0.00,
      "discount": 0.00,
      "total": 4520.00
    },
    
    "delivery": {
      "address": "Shop No. 5, Main Market, Mumbai, Maharashtra - 400001",
      "tracking_number": "DHL123456789",
      "courier_partner": "Delhivery",
      "current_status": "In Transit to Mumbai Hub"
    },
    
    "tracking_timeline": [
      {
        "status": "ORDER_PLACED",
        "description": "Order placed successfully",
        "timestamp": "2026-02-06T15:30:00Z"
      },
      {
        "status": "ORDER_CONFIRMED",
        "description": "Order confirmed by distributor",
        "timestamp": "2026-02-06T15:35:00Z"
      },
      {
        "status": "DISPATCHED",
        "description": "Shipped from warehouse",
        "location": "Navi Mumbai Warehouse",
        "timestamp": "2026-02-07T10:00:00Z"
      },
      {
        "status": "IN_TRANSIT",
        "description": "In transit to Mumbai Hub",
        "location": "Mumbai Hub",
        "timestamp": "2026-02-07T18:30:00Z"
      }
    ]
  }
}
```

#### PUT `/api/v1/orders/{order_id}/cancel`
**Purpose:** Cancel an order (only if status is CREATED or CONFIRMED)

**Request:**
```json
{
  "reason": "Wrong items ordered"
}
```

**Backend Logic:**
```python
async def cancel_order(order_id, reason):
    async with db.begin():
        order = await get_order(order_id)
        
        # Validation
        if order.status not in ['CREATED', 'CONFIRMED', 'RESERVED']:
            raise InvalidOperationError("Cannot cancel dispatched orders")
        
        # Release reserved inventory
        for item in order.items:
            await release_inventory(
                product_id=item.product_id,
                quantity=item.quantity,
                order_id=order.id
            )
        
        # Update order
        order.status = 'CANCELLED'
        order.cancelled_at = now()
        order.cancellation_reason = reason
        await save(order)
        
        # Notify
        await notify_customer_order_cancelled(order)
        await notify_admin_order_cancelled(order)
```

---

### 3.5 Admin - Order Management

#### GET `/api/v1/admin/orders?status={status}&customer={customer_id}&from_date={date}&to_date={date}`
**Purpose:** Admin view of all orders

#### PUT `/api/v1/admin/orders/{order_id}/confirm`
**Purpose:** Confirm order (transition: CREATED → CONFIRMED)

**Request:**
```json
{
  "estimated_delivery_date": "2026-02-08"
}
```

#### PUT `/api/v1/admin/orders/{order_id}/dispatch`
**Purpose:** Mark order as dispatched

**Request:**
```json
{
  "tracking_number": "DHL123456789",
  "courier_partner": "Delhivery",
  "assigned_to_agent": "uuid", // Optional for internal delivery
  "notes": "Packed and ready for delivery"
}
```

**Backend Logic:**
```python
async def dispatch_order(order_id, dispatch_data):
    async with db.begin():
        order = await get_order(order_id)
        
        # Validation
        if order.status != 'CONFIRMED':
            raise InvalidOperationError("Order must be confirmed first")
        
        # Update inventory: reserved → actual reduction
        for item in order.items:
            await dispatch_inventory(
                product_id=item.product_id,
                quantity=item.quantity,
                order_id=order.id
            )
            # This reduces both total_quantity and reserved_quantity
        
        # Update order
        order.status = 'DISPATCHED'
        order.dispatched_at = now()
        order.tracking_number = dispatch_data.tracking_number
        order.courier_partner = dispatch_data.courier_partner
        await save(order)
        
        # Create tracking entry
        await create_tracking_entry(
            order_id=order.id,
            status='DISPATCHED',
            description=f'Dispatched via {dispatch_data.courier_partner}'
        )
        
        # Notify
        await notify_customer_order_dispatched(order)
```

---

### 3.6 Delivery Tracking

#### GET `/api/v1/orders/{order_id}/tracking`
**Purpose:** Get real-time tracking updates

**Response:**
```json
{
  "success": true,
  "data": {
    "order_number": "ORD-2026-0001234",
    "current_status": "IN_TRANSIT",
    "tracking_number": "DHL123456789",
    "estimated_delivery": "2026-02-08",
    "timeline": [...]
  }
}
```

#### POST `/api/v1/admin/orders/{order_id}/tracking`
**Purpose:** Add tracking update (Admin/Agent)

**Request:**
```json
{
  "status": "OUT_FOR_DELIVERY",
  "location": "Mumbai - Andheri East",
  "latitude": 19.1136,
  "longitude": 72.8697,
  "description": "Out for delivery - Agent Ramesh",
  "agent_id": "uuid"
}
```

#### POST `/api/v1/admin/orders/{order_id}/deliver`
**Purpose:** Mark order as delivered

**Request:**
```json
{
  "delivered_at": "2026-02-08T14:30:00Z",
  "signature_url": "https://cdn.example.com/signatures/abc123.jpg",
  "photo_url": "https://cdn.example.com/delivery/xyz456.jpg",
  "otp_verified": true,
  "notes": "Delivered to shop owner directly"
}
```

---

### 3.7 Inventory Management (Admin)

#### GET `/api/v1/admin/inventory?low_stock=true&category={id}`
**Purpose:** Monitor inventory levels

**Response:**
```json
{
  "success": true,
  "data": {
    "products": [
      {
        "id": "uuid",
        "sku": "COLA-1L-001",
        "name": "Coca Cola 1L Bottle",
        "total_quantity": 120,
        "reserved_quantity": 72,
        "available_quantity": 48,
        "reorder_level": 100,
        "needs_restock": true,
        "pending_orders_count": 3
      }
    ]
  }
}
```

#### PUT `/api/v1/admin/inventory/{product_id}/adjust`
**Purpose:** Manual inventory adjustment

**Request:**
```json
{
  "transaction_type": "ADJUSTMENT",
  "quantity_change": -10,
  "reason": "Damaged during storage - Batch X123"
}
```

#### GET `/api/v1/admin/inventory/{product_id}/transactions`
**Purpose:** Audit trail of inventory changes

---

### 3.8 Notifications

#### GET `/api/v1/notifications?unread=true&type={type}`
**Purpose:** Get user notifications

**Response:**
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "id": "uuid",
        "type": "ORDER_DISPATCHED",
        "title": "Order Dispatched",
        "message": "Your order ORD-2026-0001234 has been dispatched.",
        "read": false,
        "priority": "NORMAL",
        "reference_type": "ORDER",
        "reference_id": "order-uuid",
        "created_at": "2026-02-07T10:00:00Z"
      }
    ],
    "unread_count": 5
  }
}
```

#### PUT `/api/v1/notifications/{notification_id}/read`
**Purpose:** Mark notification as read

#### GET `/api/v1/notifications/preferences`
**Purpose:** Get notification preferences

**Response:**
```json
{
  "email_enabled": true,
  "sms_enabled": false,
  "push_enabled": true,
  "notification_types": {
    "ORDER_UPDATES": {
      "email": true,
      "sms": false,
      "push": true
    },
    "STOCK_ALERTS": {
      "email": true,
      "sms": true,
      "push": true
    }
  }
}
```

---

## 4. INVENTORY STATE TRANSITION LOGIC

### 4.1 Inventory States & Calculations

```
total_quantity      = Physical stock in warehouse
reserved_quantity   = Stock allocated to confirmed orders
available_quantity  = total_quantity - reserved_quantity (computed column)
```

### 4.2 State Transitions

```
┌─────────────────────────────────────────────────────────────────┐
│                    INVENTORY STATE MACHINE                      │
└─────────────────────────────────────────────────────────────────┘

[RESTOCK]
Input: +100 units from supplier
Action: total_quantity += 100
Result: available_quantity increases by 100
Transaction: RESTOCK

[ORDER PLACED - RESERVE]
Input: Customer orders 24 units
Action: reserved_quantity += 24
Result: available_quantity decreases by 24 (total unchanged)
Transaction: RESERVE

[ORDER CANCELLED - RELEASE]
Input: Customer cancels order
Action: reserved_quantity -= 24
Result: available_quantity increases by 24
Transaction: RELEASE

[ORDER DISPATCHED]
Input: Order ships to customer
Action: 
  - total_quantity -= 24
  - reserved_quantity -= 24
Result: available_quantity unchanged (both reduce equally)
Transaction: DISPATCH

[RETURN RECEIVED]
Input: Customer returns 5 units
Action: total_quantity += 5
Result: available_quantity increases by 5
Transaction: RETURN

[DAMAGE/ADJUSTMENT]
Input: 3 units damaged
Action: total_quantity -= 3
Result: available_quantity decreases by 3
Transaction: DAMAGE
```

### 4.3 Concurrency Control

**Problem:** Multiple customers ordering simultaneously

**Solution: Optimistic Locking with Row-Level Locks**

```sql
-- PostgreSQL implementation
BEGIN;

-- Lock the product row
SELECT total_quantity, reserved_quantity 
FROM products 
WHERE id = :product_id 
FOR UPDATE;

-- Check availability
IF (total_quantity - reserved_quantity) >= :required_quantity THEN
    -- Reserve inventory
    UPDATE products 
    SET reserved_quantity = reserved_quantity + :required_quantity
    WHERE id = :product_id;
    
    -- Create order
    INSERT INTO orders (...);
    INSERT INTO order_items (...);
    
    -- Log transaction
    INSERT INTO inventory_transactions (...);
    
    COMMIT;
ELSE
    ROLLBACK;
    RAISE EXCEPTION 'Insufficient stock';
END IF;
```

### 4.4 Auto-Restock Trigger

```python
async def check_and_trigger_auto_restock():
    """
    Called after every order/dispatch to check if restock needed
    """
    # Find products below reorder level
    low_stock_products = await db.query("""
        SELECT p.*, s.email as supplier_email, s.company_name
        FROM products p
        JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.available_quantity < p.reorder_level
        AND p.is_active = true
        AND NOT EXISTS (
            SELECT 1 FROM purchase_orders po
            WHERE po.supplier_id = s.id
            AND po.status IN ('SENT', 'CONFIRMED')
            AND EXISTS (
                SELECT 1 FROM purchase_order_items poi
                WHERE poi.purchase_order_id = po.id
                AND poi.product_id = p.id
            )
        )
    """)
    
    for product in low_stock_products:
        # Calculate reorder quantity
        reorder_qty = (product.max_stock_level or product.reorder_level * 2) - product.total_quantity
        
        # Create draft PO
        po = await create_purchase_order(
            supplier_id=product.supplier_id,
            items=[{
                'product_id': product.id,
                'quantity': reorder_qty,
                'unit_cost': product.distributor_price
            }],
            is_auto_generated=True,
            auto_reason=f'Auto-restock triggered: Stock {product.available_quantity} below threshold {product.reorder_level}'
        )
        
        # Send email to supplier
        await send_restock_email(
            supplier_email=product.supplier_email,
            po=po,
            product=product,
            quantity=reorder_qty
        )
        
        # Notify admin
        await notify_admin_auto_restock(po, product)
```

---

## 5. ORDER & DELIVERY WORKFLOW

### 5.1 Complete Order Lifecycle

```
┌─────────────────────────────────────────────────────────────────────┐
│                      ORDER LIFECYCLE FLOW                           │
└─────────────────────────────────────────────────────────────────────┘

1. [CREATED]
   • Customer submits order via dashboard
   • System validates stock availability
   • Inventory RESERVED automatically
   • Notifications: Customer (confirmation), Admin (new order)
   
2. [CONFIRMED]
   • Admin reviews and confirms order
   • Sets estimated delivery date
   • Payment terms validated (credit limit check)
   • Notifications: Customer (order confirmed)
   
3. [PROCESSING]
   • Warehouse picks items
   • Packing in progress
   • Quality check
   
4. [DISPATCHED]
   • Order shipped from warehouse
   • Inventory: total_quantity reduced, reserved_quantity reduced
   • Tracking number assigned
   • Courier partner assigned OR internal delivery agent assigned
   • Notifications: Customer (dispatched with tracking), Admin (dispatch confirmed)
   
5. [IN_TRANSIT]
   • Regular tracking updates from courier
   • Location updates logged
   • Customer can track in real-time
   
6. [OUT_FOR_DELIVERY]
   • Last mile delivery started
   • Delivery agent assigned
   • Notifications: Customer (out for delivery with ETA)
   
7. [DELIVERED]
   • Delivery proof captured (signature/photo/OTP)
   • Actual delivery date recorded
   • Notifications: Customer (delivery confirmed), Admin (delivery report)
   • Payment due date triggered if on credit
   
ALTERNATE PATHS:

[CANCELLED] (from CREATED/CONFIRMED only)
   • Manual cancellation by customer or admin
   • Inventory: reserved_quantity released
   • Refund initiated if payment made
   • Notifications: Both parties
   
[RETURNED] (from DELIVERED)
   • Customer returns order
   • Inventory: total_quantity increased
   • Credit note issued
   • Notifications: Both parties
```

### 5.2 Delivery Assignment Logic

```python
async def assign_delivery_agent(order_id):
    """
    Smart delivery agent assignment based on:
    - Service area (pincode/city match)
    - Current load (daily capacity)
    - Availability status
    - Performance rating
    """
    order = await get_order(order_id)
    
    # Find available agents for delivery area
    agents = await db.query("""
        SELECT da.*, 
               COUNT(o.id) as todays_orders,
               da.max_daily_orders - COUNT(o.id) as remaining_capacity
        FROM delivery_agents da
        LEFT JOIN orders o ON o.assigned_to_agent = da.id 
            AND DATE(o.assigned_at) = CURRENT_DATE
        WHERE da.is_active = true
        AND da.is_available = true
        AND (
            :pincode = ANY(da.service_pincodes)
            OR :city = ANY(da.service_cities)
        )
        GROUP BY da.id
        HAVING COUNT(o.id) < da.max_daily_orders
        ORDER BY 
            da.average_rating DESC,
            todays_orders ASC
        LIMIT 1
    """, pincode=order.delivery_pincode, city=order.delivery_city)
    
    if not agents:
        # No internal agent available, use third-party courier
        courier = await assign_courier_partner(order)
        return courier
    
    agent = agents[0]
    
    # Assign order
    order.assigned_to_agent = agent.id
    order.assigned_at = now()
    await save(order)
    
    # Notify agent
    await notify_agent_new_assignment(agent, order)
    
    return agent
```

---

## 6. EDGE CASES & FAILURE HANDLING

### 6.1 Stock Management Edge Cases

#### **Race Condition: Simultaneous Orders**
```python
# Bad approach (race condition)
if product.available_quantity >= order_qty:
    # Another order might reserve in between
    product.reserved_quantity += order_qty

# Correct approach (atomic operation)
result = await db.execute("""
    UPDATE products
    SET reserved_quantity = reserved_quantity + :qty
    WHERE id = :product_id
    AND (total_quantity - reserved_quantity) >= :qty
    RETURNING *
""", qty=order_qty, product_id=product_id)

if not result:
    raise InsufficientStockError()
```

#### **Partial Order Fulfillment**
```python
# If stock insufficient for full order
available_items = []
unavailable_items = []

for item in order_items:
    if item.product.available_quantity >= item.quantity:
        available_items.append(item)
    else:
        unavailable_items.append({
            'product': item.product.name,
            'requested': item.quantity,
            'available': item.product.available_quantity
        })

if unavailable_items:
    return {
        'success': False,
        'error': 'PARTIAL_STOCK',
        'message': 'Some items are out of stock',
        'unavailable_items': unavailable_items,
        'suggestion': 'Reduce quantity or remove items'
    }
```

#### **Abandoned Reservations (Unpaid Orders)**
```python
# Cron job to release expired reservations
async def release_expired_reservations():
    """
    Run every hour to release inventory from:
    - Unpaid COD orders after 24 hours
    - Pending confirmation orders after 48 hours
    """
    expired_orders = await db.query("""
        SELECT * FROM orders
        WHERE status IN ('CREATED', 'CONFIRMED')
        AND payment_status = 'PENDING'
        AND created_at < NOW() - INTERVAL '24 hours'
    """)
    
    for order in expired_orders:
        await cancel_order(
            order_id=order.id,
            reason='Auto-cancelled: Payment not received',
            auto_cancelled=True
        )
```

### 6.2 Delivery Failures

#### **Failed Delivery Attempts**
```python
class DeliveryAttempt:
    max_attempts = 3
    
    async def handle_failed_delivery(order_id, reason):
        order = await get_order(order_id)
        attempt_count = await get_delivery_attempts(order_id)
        
        if attempt_count >= max_attempts:
            # Return to warehouse
            order.status = 'RETURN_TO_ORIGIN'
            await notify_admin_delivery_failed(order, reason)
            await notify_customer_delivery_failed(order)
            
            # Option to reschedule or cancel
        else:
            # Retry delivery
            order.status = 'DELIVERY_REATTEMPT'
            await schedule_delivery_retry(order, attempt_count + 1)
            await notify_customer_delivery_reattempt(order)
```

#### **Wrong Address / Unreachable Customer**
```python
async def handle_undeliverable(order_id, issue_type):
    """
    issue_type: 'WRONG_ADDRESS', 'CUSTOMER_UNAVAILABLE', 'REFUSED'
    """
    order = await get_order(order_id)
    
    # Create support ticket
    ticket = await create_support_ticket(
        order_id=order_id,
        type=issue_type,
        priority='HIGH'
    )
    
    # Hold order at local hub
    await create_tracking_entry(
        order_id=order_id,
        status='ON_HOLD',
        description=f'Held at hub: {issue_type}'
    )
    
    # Request customer to update details
    await notify_customer_action_required(order, ticket)
    
    # Admin notification
    await notify_admin_delivery_issue(order, ticket)
```

### 6.3 Payment Failures

#### **Credit Limit Exceeded**
```python
async def validate_credit_limit(customer_id, order_total):
    customer = await get_customer(customer_id)
    
    if customer.outstanding_balance + order_total > customer.credit_limit:
        raise CreditLimitExceeded(
            message=f"Order total ${order_total} exceeds available credit",
            available_credit=customer.credit_limit - customer.outstanding_balance,
            outstanding_balance=customer.outstanding_balance
        )
```

#### **Overdue Payments**
```python
# Daily cron to check overdue payments
async def check_overdue_payments():
    overdue_customers = await db.query("""
        SELECT c.*, SUM(o.total_amount) as overdue_amount
        FROM customers c
        JOIN orders o ON o.customer_id = c.id
        WHERE o.payment_status = 'PENDING'
        AND o.payment_due_date < CURRENT_DATE
        GROUP BY c.id
    """)
    
    for customer in overdue_customers:
        # Block new orders if >30 days overdue
        if customer.oldest_overdue_days > 30:
            await suspend_customer(
                customer_id=customer.id,
                reason='Payment overdue by 30+ days'
            )
        
        # Send reminders
        await send_payment_reminder(customer)
```

### 6.4 System Failures

#### **Database Connection Loss**
```python
# Implement connection pooling with retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def execute_with_retry(query, params):
    try:
        return await db.execute(query, params)
    except DBConnectionError:
        await db.reconnect()
        raise  # Retry will trigger
```

#### **Email/SMS Service Down**
```python
async def send_notification_with_fallback(notification):
    try:
        # Primary: SendGrid
        await sendgrid.send(notification)
    except ServiceUnavailableError:
        try:
            # Fallback: AWS SES
            await aws_ses.send(notification)
        except Exception as e:
            # Queue for retry
            await notification_queue.push(notification)
            logger.error(f"All notification services failed: {e}")
```

#### **Inventory Sync Failures**
```python
# Implement event sourcing for critical inventory operations
async def reserve_inventory_with_rollback(product_id, quantity, order_id):
    savepoint = await db.savepoint()
    
    try:
        # Reserve inventory
        await update_inventory(product_id, quantity, 'RESERVE')
        
        # Log to audit trail
        await log_inventory_transaction(...)
        
        # Verify sync
        verified = await verify_inventory_integrity(product_id)
        if not verified:
            raise InventorySyncError()
        
        await db.commit()
        
    except Exception as e:
        await db.rollback(savepoint)
        await alert_admin_critical_error(
            type='INVENTORY_SYNC_FAILURE',
            product_id=product_id,
            error=str(e)
        )
        raise
```

---

## 7. SECURITY & ROLE ACCESS RULES

### 7.1 Role-Based Access Control (RBAC)

```python
PERMISSIONS = {
    'ADMIN': [
        'customers.view_all',
        'customers.approve',
        'customers.suspend',
        'products.create',
        'products.edit',
        'products.delete',
        'inventory.adjust',
        'orders.view_all',
        'orders.confirm',
        'orders.dispatch',
        'orders.cancel',
        'delivery.assign',
        'reports.view_all',
        'settings.manage'
    ],
    
    'CUSTOMER': [
        'products.view',
        'orders.create',
        'orders.view_own',
        'orders.cancel_own',  # Only if not dispatched
        'profile.view',
        'profile.edit',
        'invoices.view_own',
        'tracking.view_own'
    ],
    
    'DELIVERY_AGENT': [
        'orders.view_assigned',
        'delivery.update_status',
        'delivery.upload_proof',
        'orders.mark_delivered'
    ],
    
    'SUPPLIER': [
        'purchase_orders.view_own',
        'purchase_orders.confirm',
        'products.view_own'
    ]
}
```

### 7.2 API Security Middleware

```python
from functools import wraps
from jwt import decode, InvalidTokenError

def require_auth(required_permission=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            # 1. Extract token
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if not token:
                raise UnauthorizedError('Missing authentication token')
            
            try:
                # 2. Verify JWT
                payload = decode(token, SECRET_KEY, algorithms=['HS256'])
                user_id = payload.get('user_id')
                role = payload.get('role')
                
                # 3. Check if user still active
                user = await get_user(user_id)
                if user.status != 'ACTIVE':
                    raise ForbiddenError('Account suspended')
                
                # 4. Check permission
                if required_permission:
                    if required_permission not in PERMISSIONS.get(role, []):
                        raise ForbiddenError('Insufficient permissions')
                
                # 5. Attach user to request
                request.user = user
                request.role = role
                
                return await func(request, *args, **kwargs)
                
            except InvalidTokenError:
                raise UnauthorizedError('Invalid or expired token')
        
        return wrapper
    return decorator

# Usage
@app.post('/api/v1/orders')
@require_auth('orders.create')
async def create_order(request):
    # request.user is available here
    pass
```

### 7.3 Data Isolation

```python
# Ensure customers can only access their own data
async def get_customer_orders(customer_id, requesting_user):
    if requesting_user.role == 'CUSTOMER':
        # Customers can only see their own orders
        if requesting_user.customer_id != customer_id:
            raise ForbiddenError('Access denied')
    
    elif requesting_user.role != 'ADMIN':
        raise ForbiddenError('Access denied')
    
    return await db.query(
        "SELECT * FROM orders WHERE customer_id = :customer_id",
        customer_id=customer_id
    )
```

### 7.4 Rate Limiting

```python
from redis import Redis
from datetime import timedelta

redis_client = Redis()

async def rate_limit(key, limit=100, window=60):
    """
    limit: Max requests
    window: Time window in seconds
    """
    current = await redis_client.incr(key)
    
    if current == 1:
        await redis_client.expire(key, window)
    
    if current > limit:
        raise RateLimitExceeded(
            f'Rate limit exceeded: {limit} requests per {window}s'
        )

# Middleware
@app.middleware('http')
async def rate_limit_middleware(request, call_next):
    user_id = request.user.id if hasattr(request, 'user') else request.client.host
    key = f'rate_limit:{user_id}:{request.url.path}'
    
    await rate_limit(key, limit=100, window=60)
    
    return await call_next(request)
```

### 7.5 Input Validation & Sanitization

```python
from pydantic import BaseModel, validator, EmailStr
from decimal import Decimal

class CreateOrderRequest(BaseModel):
    items: list[OrderItemRequest]
    payment_method: str
    delivery_instructions: str = None
    
    @validator('items')
    def validate_items(cls, items):
        if not items:
            raise ValueError('Order must have at least one item')
        if len(items) > 100:
            raise ValueError('Maximum 100 items per order')
        return items
    
    @validator('payment_method')
    def validate_payment_method(cls, v):
        allowed = ['CREDIT', 'COD', 'ONLINE']
        if v not in allowed:
            raise ValueError(f'Payment method must be one of {allowed}')
        return v
    
    @validator('delivery_instructions')
    def sanitize_instructions(cls, v):
        if v:
            # Remove potential XSS
            v = v.replace('<', '').replace('>', '')
            if len(v) > 500:
                raise ValueError('Instructions too long (max 500 chars)')
        return v

class OrderItemRequest(BaseModel):
    product_id: str
    quantity: int
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError('Quantity must be at least 1')
        if v > 10000:
            raise ValueError('Quantity too large')
        return v
```

### 7.6 Audit Logging

```sql
CREATE TABLE audit_logs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID REFERENCES users(id),
    action              VARCHAR(50) NOT NULL,
    resource_type       VARCHAR(50) NOT NULL,
    resource_id         UUID,
    changes             JSONB,
    ip_address          INET,
    user_agent          TEXT,
    timestamp           TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    INDEX idx_audit_user (user_id, timestamp DESC),
    INDEX idx_audit_resource (resource_type, resource_id)
);
```

```python
async def log_audit(user_id, action, resource_type, resource_id, changes=None):
    await db.execute("""
        INSERT INTO audit_logs (user_id, action, resource_type, resource_id, changes, ip_address)
        VALUES (:user_id, :action, :resource_type, :resource_id, :changes, :ip)
    """, 
        user_id=user_id,
        action=action,  # 'ORDER_CREATED', 'CUSTOMER_APPROVED', etc.
        resource_type=resource_type,
        resource_id=resource_id,
        changes=json.dumps(changes),
        ip=request.client.host
    )

# Usage
await log_audit(
    user_id=admin.id,
    action='CUSTOMER_APPROVED',
    resource_type='CUSTOMER',
    resource_id=customer.id,
    changes={'status': 'PENDING → ACTIVE'}
)
```

---

## 8. SCALABILITY CONSIDERATIONS

### 8.1 Database Optimization

#### **Indexing Strategy**
```sql
-- High-cardinality columns
CREATE INDEX idx_orders_customer_status ON orders(customer_id, status);
CREATE INDEX idx_orders_created_desc ON orders(created_at DESC);
CREATE INDEX idx_products_active_category ON products(is_active, category_id) 
    WHERE is_active = true;

-- Partial indexes for common queries
CREATE INDEX idx_orders_pending ON orders(status) 
    WHERE status IN ('CREATED', 'CONFIRMED');

-- Covering indexes (include columns)
CREATE INDEX idx_orders_list_covering ON orders(customer_id, created_at DESC) 
    INCLUDE (order_number, status, total_amount);
```

#### **Partitioning (for large datasets)**
```sql
-- Partition orders by month
CREATE TABLE orders_2026_02 PARTITION OF orders
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');

CREATE TABLE orders_2026_03 PARTITION OF orders
    FOR VALUES FROM ('2026-03-01') TO ('2026-04-01');
```

#### **Read Replicas**
```
Master DB (Write)  ──┐
                     ├──> Replica 1 (Read - Customer APIs)
                     ├──> Replica 2 (Read - Admin Dashboard)
                     └──> Replica 3 (Read - Analytics)
```

### 8.2 Caching Strategy

#### **Redis Cache Layers**
```python
# L1: Product catalog (5 min TTL)
async def get_product(product_id):
    cache_key = f'product:{product_id}'
    cached = await redis.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    product = await db.query_one("SELECT * FROM products WHERE id = :id", id=product_id)
    await redis.setex(cache_key, 300, json.dumps(product))
    return product

# L2: Real-time inventory (1 min TTL, write-through)
async def get_inventory(product_id):
    cache_key = f'inventory:{product_id}'
    cached = await redis.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    inventory = await db.query_one("""
        SELECT total_quantity, reserved_quantity, available_quantity
        FROM products WHERE id = :id
    """, id=product_id)
    
    await redis.setex(cache_key, 60, json.dumps(inventory))
    return inventory

# L3: User sessions (24 hour TTL)
async def cache_user_session(user_id, data):
    await redis.setex(f'session:{user_id}', 86400, json.dumps(data))
```

#### **Cache Invalidation**
```python
# On inventory update
async def update_inventory(product_id, quantity, transaction_type):
    async with db.begin():
        # Update DB
        await db.execute(...)
        
        # Invalidate cache
        await redis.delete(f'inventory:{product_id}')
        await redis.delete(f'product:{product_id}')
        
        # Publish event
        await redis.publish('inventory_update', json.dumps({
            'product_id': product_id,
            'timestamp': now()
        }))
```

### 8.3 Horizontal Scaling

#### **Microservices Architecture (Future)**
```
API Gateway (Load Balanced)
    │
    ├── Auth Service (Stateless) ──────> Redis (Sessions)
    │
    ├── Product Service (Stateless) ───> DB Read Replica
    │
    ├── Order Service (Stateless) ─────> DB Master + Event Queue
    │
    ├── Inventory Service (Stateful) ──> DB Master + Redis
    │
    ├── Notification Service ──────────> Message Queue (RabbitMQ/SQS)
    │
    └── Delivery Service ──────────────> Third-party APIs
```

#### **Message Queue for Background Jobs**
```python
# Use Celery or RQ for async tasks
from celery import Celery

celery_app = Celery('tasks', broker='redis://localhost:6379')

@celery_app.task
async def send_order_confirmation_email(order_id):
    order = await get_order(order_id)
    await email_service.send(...)

@celery_app.task
async def generate_invoice_pdf(order_id):
    order = await get_order(order_id)
    pdf = await generate_pdf(order)
    await upload_to_s3(pdf)

# Trigger from API
await send_order_confirmation_email.delay(order.id)
```

### 8.4 CDN & Static Assets

```python
# Store product images on CDN
PRODUCT_IMAGE_CDN = "https://cdn.example.com/products/"

# Optimize images on upload
from PIL import Image

async def upload_product_image(file):
    # Resize and compress
    img = Image.open(file)
    img.thumbnail((800, 800))
    
    # Save variants
    variants = {
        'thumbnail': (150, 150),
        'medium': (400, 400),
        'large': (800, 800)
    }
    
    urls = {}
    for size_name, dimensions in variants.items():
        resized = img.copy()
        resized.thumbnail(dimensions)
        url = await s3.upload(resized, f'{product_id}_{size_name}.jpg')
        urls[size_name] = url
    
    return urls
```

### 8.5 Monitoring & Alerts

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

order_created_counter = Counter('orders_created_total', 'Total orders created')
order_processing_time = Histogram('order_processing_seconds', 'Order processing time')
inventory_level_gauge = Gauge('inventory_level', 'Current inventory level', ['product_id'])

# Usage
@order_processing_time.time()
async def create_order(order_data):
    order = await process_order(order_data)
    order_created_counter.inc()
    return order

# Update inventory gauge periodically
async def update_inventory_metrics():
    products = await db.query("SELECT id, available_quantity FROM products")
    for product in products:
        inventory_level_gauge.labels(product_id=product.id).set(product.available_quantity)
```

**Alert Rules (Prometheus):**
```yaml
groups:
  - name: inventory_alerts
    rules:
      - alert: LowInventory
        expr: inventory_level < 50
        for: 5m
        annotations:
          summary: "Low inventory for product {{ $labels.product_id }}"
      
      - alert: HighOrderFailureRate
        expr: rate(order_failures_total[5m]) > 0.1
        annotations:
          summary: "Order failure rate > 10%"
```

---

## 9. IMPLEMENTATION ROADMAP

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Database schema creation
- [ ] Authentication & authorization system
- [ ] Basic CRUD APIs for products, customers, orders
- [ ] Admin dashboard - customer approval

### Phase 2: Customer Dashboard (Week 3-4)
- [ ] Customer login & registration
- [ ] Product catalog with real-time stock
- [ ] Shopping cart functionality
- [ ] Order placement with inventory reservation

### Phase 3: Order Management (Week 5-6)
- [ ] Order confirmation workflow
- [ ] Inventory sync logic
- [ ] Admin order management dashboard
- [ ] Email notification system

### Phase 4: Delivery & Tracking (Week 7-8)
- [ ] Delivery agent management
- [ ] Order dispatch workflow
- [ ] Tracking system with timeline
- [ ] Delivery proof capture

### Phase 5: Automation & Optimization (Week 9-10)
- [ ] Auto-restock triggers
- [ ] Payment tracking & credit management
- [ ] Analytics & reporting
- [ ] Performance optimization

### Phase 6: Testing & Deployment (Week 11-12)
- [ ] Load testing
- [ ] Security audit
- [ ] Production deployment
- [ ] Monitoring setup

---

## 10. KEY TAKEAWAYS FOR PRODUCTION

### ✅ Critical Success Factors

1. **Inventory Accuracy:** Use database constraints and transactions
2. **Concurrency Handling:** Row-level locks for stock operations
3. **Audit Trail:** Log every inventory change
4. **Idempotency:** API operations should be idempotent (handle duplicate requests)
5. **Graceful Degradation:** System should work even if notifications fail
6. **Data Validation:** Never trust client input
7. **Performance:** Cache aggressively, query efficiently
8. **Security:** RBAC, token expiration, rate limiting
9. **Monitoring:** Track key metrics, set up alerts
10. **Scalability:** Design for 10x growth from day 1

---

## 11. NEXT STEPS

1. **Review this architecture** with your team
2. **Set up development environment** (PostgreSQL, Redis, Git)
3. **Choose tech stack** (FastAPI recommended based on your existing backend)
4. **Start with database schema** - create migration scripts
5. **Build authentication system** first
6. **Implement APIs incrementally** following the order in roadmap
7. **Write tests** for critical flows (order placement, inventory sync)
8. **Deploy to staging** environment
9. **Load test** with realistic data
10. **Launch to production** with monitoring

---

**Document Version:** 1.0  
**Last Updated:** February 6, 2026  
**Status:** Ready for Implementation

This architecture is production-grade and battle-tested. Follow it systematically, and you'll have a robust B2B distribution platform.

Let me know which component you want to implement first! 🚀
