# Frontend Integration Guide - Dashboard Reference

## 🎯 Recommended Dashboard Reference: `unified_dashboard.py`

**Why Unified Dashboard?**
- ✅ Combines ALL functionality (CRM, Logistics, Inventory, Suppliers, Products, AI Agents)
- ✅ Most comprehensive feature set
- ✅ Single source of truth for all integrations
- ✅ Best structure for frontend mapping
- ✅ Already uses API endpoints that your frontend can consume

---

## 📋 Dashboard Structure Mapping

### Streamlit → React Component Mapping

| Streamlit Component | React Equivalent | Location |
|---------------------|------------------|----------|
| `st.sidebar.selectbox()` | `<Sidebar>` navigation | `frontend/src/components/layout/Sidebar.jsx` |
| `st.metric()` | `<MetricCard>` | `frontend/src/components/common/charts/MetricCard.jsx` |
| `st.plotly_chart()` | `<LineChart>`, `<BarChart>`, `<PieChart>` | `frontend/src/components/common/charts/` |
| `st.dataframe()` | `<Table>` | `frontend/src/components/common/ui/Table.jsx` |
| `st.button()` | `<Button>` | `frontend/src/components/common/ui/Button.jsx` |
| `st.selectbox()`, `st.text_input()` | Form components | `frontend/src/components/common/forms/` |
| `st.columns()` | CSS Grid/Flexbox | Tailwind CSS classes |

---

## 🔌 API Integration Points

### 1. Main API (`api_app.py` - Port 8000)

#### Dashboard Data Endpoints:
```javascript
// Get unified dashboard data
GET /dashboard/crm
GET /api/dashboard/kpis
GET /api/dashboard/alerts
GET /api/dashboard/charts
GET /api/dashboard/activity
GET /api/dashboard/system-status
```

#### Inventory Endpoints:
```javascript
GET /inventory
GET /inventory/{id}
PATCH /inventory/{id}/stock
POST /inventory/{id}/adjust
GET /inventory/low-stock
GET /inventory/alerts
```

#### Orders & Logistics:
```javascript
GET /orders
POST /orders
GET /orders/{id}
GET /shipments
POST /shipments
```

### 2. CRM API (`crm_api.py` - Port 8001)

#### CRM Endpoints:
```javascript
GET /accounts
POST /accounts
GET /accounts/{id}
GET /contacts
POST /contacts
GET /leads
POST /leads
GET /opportunities
POST /opportunities
GET /dashboard  // CRM dashboard data
POST /query/natural  // Natural language queries
```

---

## 🚀 Frontend Integration Steps

### Step 1: Update API Services

Create/Update API service files to match unified dashboard endpoints:

**File: `frontend/src/services/api/unifiedAPI.js`**
```javascript
import apiClient from './baseAPI';

export const unifiedAPI = {
  // Dashboard Overview
  getDashboardData: () => apiClient.get('/dashboard/crm'),
  getKPIs: () => apiClient.get('/api/dashboard/kpis'),
  getAlerts: () => apiClient.get('/api/dashboard/alerts'),
  getCharts: () => apiClient.get('/api/dashboard/charts'),
  getActivity: () => apiClient.get('/api/dashboard/activity'),
  getSystemStatus: () => apiClient.get('/api/dashboard/system-status'),
  
  // Orders & Logistics
  getOrders: (params) => apiClient.get('/orders', { params }),
  createOrder: (data) => apiClient.post('/orders', data),
  getShipments: (params) => apiClient.get('/shipments', { params }),
  
  // Inventory
  getInventory: (params) => apiClient.get('/inventory', { params }),
  getLowStock: (threshold) => apiClient.get('/inventory/low-stock', { 
    params: { threshold } 
  }),
  
  // Suppliers
  getSuppliers: () => apiClient.get('/suppliers'),
  createSupplier: (data) => apiClient.post('/suppliers', data),
  
  // Products
  getProducts: (params) => apiClient.get('/products', { params }),
  uploadProductImage: (productId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post(`/products/${productId}/image`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  
  // AI Agents
  getAgents: () => apiClient.get('/api/agents'),
  getAgentMetrics: (id) => apiClient.get(`/api/agents/${id}/metrics`),
  triggerAgent: (id, data) => apiClient.post(`/api/agents/${id}/trigger`, data),
};

export default unifiedAPI;
```

### Step 2: Create Unified Dashboard Page

**File: `frontend/src/pages/UnifiedDashboard.jsx`**

This should mirror the structure of `unified_dashboard.py`:

```javascript
import React, { useState, useEffect } from 'react';
import { unifiedAPI } from '../services/api/unifiedAPI';
import MetricCard from '../components/common/charts/MetricCard';
import LineChart from '../components/common/charts/LineChart';
import BarChart from '../components/common/charts/BarChart';
import Card from '../components/common/ui/Card';
import { LoadingSpinner } from '../components/common/ui/Spinner';

export const UnifiedDashboard = () => {
  const [currentPage, setCurrentPage] = useState('Overview');
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [kpis, setKpis] = useState(null);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [dashboard, kpiData, alertData] = await Promise.all([
        unifiedAPI.getDashboardData(),
        unifiedAPI.getKPIs(),
        unifiedAPI.getAlerts()
      ]);
      
      setDashboardData(dashboard);
      setKpis(kpiData);
      setAlerts(alertData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner text="Loading dashboard..." />;
  }

  return (
    <div className="space-y-6">
      {/* Navigation Sidebar */}
      <div className="flex gap-4">
        <aside className="w-64">
          <nav className="space-y-2">
            {['Overview', 'CRM', 'Logistics', 'Inventory', 'Suppliers', 
              'Products', 'AI Agents', 'Analytics'].map((page) => (
              <button
                key={page}
                onClick={() => setCurrentPage(page)}
                className={`w-full text-left px-4 py-2 rounded-lg ${
                  currentPage === page 
                    ? 'bg-primary text-white' 
                    : 'bg-muted hover:bg-muted/80'
                }`}
              >
                {page}
              </button>
            ))}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1">
          {currentPage === 'Overview' && <OverviewPage data={dashboardData} />}
          {currentPage === 'CRM' && <CRMPage />}
          {currentPage === 'Logistics' && <LogisticsPage />}
          {currentPage === 'Inventory' && <InventoryPage />}
          {currentPage === 'Suppliers' && <SuppliersPage />}
          {currentPage === 'Products' && <ProductsPage />}
          {currentPage === 'AI Agents' && <AIAgentsPage />}
          {currentPage === 'Analytics' && <AnalyticsPage />}
        </main>
      </div>
    </div>
  );
};

// Page Components
const OverviewPage = ({ data }) => {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard Overview</h1>
      
      {/* KPI Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard title="Total Orders" value={data?.total_orders || 0} />
        <MetricCard title="Active Accounts" value={data?.active_accounts || 0} />
        <MetricCard title="Products" value={data?.total_products || 0} />
        <MetricCard title="Suppliers" value={data?.total_suppliers || 0} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <LineChart title="Orders Trend" data={data?.orders_trend || []} />
        <BarChart title="Inventory Status" data={data?.inventory_status || []} />
      </div>
    </div>
  );
};

// Add other page components (CRMPage, LogisticsPage, etc.)
// These should match the sections in unified_dashboard.py

export default UnifiedDashboard;
```

### Step 3: Update Routing

**File: `frontend/src/App.jsx`**

Add the unified dashboard route:

```javascript
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import UnifiedDashboard from './pages/UnifiedDashboard';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<UnifiedDashboard />} />
        <Route path="/dashboard" element={<UnifiedDashboard />} />
        <Route path="/unified" element={<UnifiedDashboard />} />
        {/* ... other routes */}
      </Routes>
    </BrowserRouter>
  );
}
```

### Step 4: Map Unified Dashboard Sections

Based on `unified_dashboard.py`, create these page components:

1. **Overview Page** - Main dashboard with KPIs
2. **CRM Page** - Accounts, Leads, Opportunities
3. **Logistics Page** - Orders, Shipments, Tracking
4. **Inventory Page** - Stock levels, Alerts, Adjustments
5. **Suppliers Page** - Supplier management, Contacts
6. **Products Page** - Product catalog, Image upload
7. **AI Agents Page** - Agent monitoring, Controls
8. **Analytics Page** - Reports, Charts, Insights

---

## 📊 Data Flow Example

### Unified Dashboard Data Flow:

```
Backend (unified_dashboard.py)
  ↓
  load_dashboard_data()
  ↓
  DatabaseService / API calls
  ↓
  Returns: { orders, shipments, inventory, suppliers, products, ... }
  ↓
Frontend (UnifiedDashboard.jsx)
  ↓
  unifiedAPI.getDashboardData()
  ↓
  React State Management
  ↓
  Component Rendering (MetricCard, Charts, Tables)
```

---

## 🔧 Configuration

### API Base URL

**File: `frontend/src/utils/constants.js`**

```javascript
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const CRM_API_BASE_URL = import.meta.env.VITE_CRM_API_BASE_URL || 'http://localhost:8001';
```

### Environment Variables

Create `.env` file in frontend directory:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_CRM_API_BASE_URL=http://localhost:8001
```

---

## 🎨 UI/UX Recommendations

Based on unified_dashboard.py styling:

1. **Color Scheme**: Use gradient backgrounds similar to Streamlit CSS
2. **Cards**: Use border-left accent colors for status indicators
3. **Metrics**: Large, bold numbers with trend indicators
4. **Charts**: Use Plotly.js or Recharts (React equivalent of Plotly)
5. **Navigation**: Sidebar navigation matching Streamlit sidebar
6. **Responsive**: Mobile-first design with Tailwind CSS

---

## 📝 Key Features to Implement

From `unified_dashboard.py`, prioritize these features:

### High Priority:
- ✅ Dashboard Overview with KPIs
- ✅ CRM Management (Accounts, Leads, Opportunities)
- ✅ Inventory Management with Alerts
- ✅ Order & Shipment Tracking
- ✅ Supplier Management
- ✅ Product Catalog with Image Upload

### Medium Priority:
- ⚠️ AI Agent Controls & Monitoring
- ⚠️ Natural Language Queries
- ⚠️ Analytics & Reports
- ⚠️ Real-time Updates

### Low Priority:
- 📌 Advanced Filtering
- 📌 Export Functionality
- 📌 Custom Dashboards

---

## 🚀 Quick Start Commands

```bash
# 1. Start Backend APIs
cd backend
python api_app.py  # Port 8000
python crm_api.py   # Port 8001

# 2. Start Frontend
cd frontend
npm install
npm run dev

# 3. Access Unified Dashboard
# Frontend: http://localhost:5173 (or your Vite port)
# Backend API: http://localhost:8000
# CRM API: http://localhost:8001
```

---

## 📚 Reference Files

- **Backend Dashboard**: `backend/unified_dashboard.py`
- **Main API**: `backend/api_app.py`
- **CRM API**: `backend/crm_api.py`
- **Frontend Dashboard**: `frontend/src/pages/Dashboard.jsx`
- **API Services**: `frontend/src/services/api/`

---

## ✅ Integration Checklist

- [ ] Create `unifiedAPI.js` service
- [ ] Create `UnifiedDashboard.jsx` page
- [ ] Map all dashboard sections from unified_dashboard.py
- [ ] Implement API calls for each section
- [ ] Add error handling and loading states
- [ ] Test API connectivity
- [ ] Add authentication/authorization
- [ ] Implement real-time updates (if needed)
- [ ] Add responsive design
- [ ] Test on mobile devices

---

## 🎯 Next Steps

1. **Start with Overview Page** - Get basic KPIs working
2. **Add CRM Section** - Use existing `CRM.jsx` as reference
3. **Add Inventory Section** - Use existing `Inventory.jsx` as reference
4. **Integrate AI Agents** - Use existing `Agents.jsx` as reference
5. **Add remaining sections** - Suppliers, Products, Analytics
6. **Polish UI/UX** - Match Streamlit dashboard styling
7. **Add Real-time Updates** - WebSocket or polling
8. **Testing** - Unit tests, integration tests

---

**Recommended Approach**: Start with the Overview page, then gradually add each section from `unified_dashboard.py` one at a time, testing API integration as you go.

