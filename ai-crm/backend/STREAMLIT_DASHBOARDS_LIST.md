# Streamlit Dashboards List

Complete list of all Streamlit dashboards in the AI CRM system:

## Main Dashboards (Recommended)

1. **unified_dashboard.py** (Port 8500)
   - **Description**: Unified dashboard combining all functionality
   - **Features**: CRM, Logistics, Supplier Management, Product Catalog, AI Agents
   - **Run**: `streamlit run unified_dashboard.py --server.port=8500`
   - **URL**: http://localhost:8500

2. **crm_dashboard.py** (Port 8501)
   - **Description**: Enhanced CRM Dashboard
   - **Features**: Account Management, Leads, Opportunities, Natural Language Queries
   - **Run**: `streamlit run crm_dashboard.py --server.port=8501`
   - **URL**: http://localhost:8501

3. **dashboard_app.py** (Port 8502)
   - **Description**: AI Agent Logistics Dashboard
   - **Features**: Logistics, Inventory, AI Agents, Real-time KPIs
   - **Run**: `streamlit run dashboard_app.py --server.port=8502`
   - **URL**: http://localhost:8502

4. **dashboard_with_supplier.py** (Port 8503)
   - **Description**: Enhanced Supplier Dashboard
   - **Features**: Supplier Management, Contact System, Inventory Editing
   - **Run**: `streamlit run dashboard_with_supplier.py --server.port=8503`
   - **URL**: http://localhost:8503

5. **product_catalog_dashboard.py** (Port 8504)
   - **Description**: Product Catalog Management
   - **Features**: Product Management, Image Upload, Catalog
   - **Run**: `streamlit run product_catalog_dashboard.py --server.port=8504`
   - **URL**: http://localhost:8504

6. **supplier_showcase.py** (Port 8505)
   - **Description**: Supplier Showcase Portal
   - **Features**: Professional Supplier Portal, Marketing, Product Presentation
   - **Run**: `streamlit run supplier_showcase.py --server.port=8505`
   - **URL**: http://localhost:8505

## Additional Dashboards

7. **supplier_management_dashboard.py**
   - **Description**: Supplier Management Dashboard
   - **Features**: Add, edit, and manage suppliers
   - **Run**: `streamlit run supplier_management_dashboard.py`
   - **Default Port**: 8501 (if port not specified)

8. **enhanced_inventory_dashboard.py**
   - **Description**: Enhanced Inventory Management
   - **Features**: Inventory management with sidebar editing and supplier communication
   - **Run**: `streamlit run enhanced_inventory_dashboard.py`
   - **Default Port**: 8501 (if port not specified)

9. **simple_dashboard.py**
   - **Description**: Simple Dashboard for BHIV Integrator Core
   - **Features**: BHIV Integrator monitoring (no pyarrow dependency)
   - **Run**: `streamlit run simple_dashboard.py`
   - **Default Port**: 8501 (if port not specified)

## Quick Launch Scripts

- **start_unified_dashboard.py**: Launches the unified dashboard (recommended)
- **start_all_dashboards.py**: Launches all main dashboards simultaneously

## Usage

### Run Single Dashboard:
```bash
cd backend
streamlit run <dashboard_name>.py --server.port=<port>
```

### Run Unified Dashboard (Recommended):
```bash
cd backend
python start_unified_dashboard.py
```

### Run All Dashboards:
```bash
cd backend
python start_all_dashboards.py
```

## Port Allocation

- Port 8500: Unified Dashboard
- Port 8501: CRM Dashboard
- Port 8502: Main/Logistics Dashboard
- Port 8503: Enhanced Supplier Dashboard
- Port 8504: Product Catalog Dashboard
- Port 8505: Supplier Showcase Portal

