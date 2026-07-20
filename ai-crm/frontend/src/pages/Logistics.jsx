import React, { useState, useEffect } from 'react';
import { 
  Package, Truck, BarChart3, Bot, 
  Download, Search, Maximize2, RefreshCw,
  Building2, Truck as TruckIcon, LayoutDashboard,
  TrendingUp, Activity, AlertCircle
} from 'lucide-react';
import Card, { CardHeader, CardTitle, CardContent } from '../components/common/ui/Card';
import Button from '../components/common/ui/Button';
import Input from '../components/common/forms/Input';
import Badge from '../components/common/ui/Badge';
import Alert from '../components/common/ui/Alert';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../components/common/ui/Table';
import { LoadingSpinner } from '../components/common/ui/Spinner';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import MetricCard from '../components/common/charts/MetricCard';
import { orderAPI } from '../services/api/orderAPI';
import { productAPI } from '../services/api/productAPI';
import { restockAPI } from '../services/api/restockAPI';
import { formatDate } from '@/utils/dateUtils';

export const Logistics = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Orders data
  const [orders, setOrders] = useState([]);

  // Shipments data
  const [shipments, setShipments] = useState([]);

  // Inventory data for chart
  const [inventoryData, setInventoryData] = useState([]);

  // Low stock products (stockQuantity < minThreshold)
  const [lowStockProducts, setLowStockProducts] = useState([]);

  // Agent activity data
  const [agentActivity, setAgentActivity] = useState([]);

  // Fetch all data
  useEffect(() => {
    fetchAllData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchAllData();
    }, 30000);

    return () => clearInterval(interval);
  }, [activeTab]);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch orders
      try {
        const ordersResponse = await orderAPI.getOrders({ limit: 100 });
        setOrders(ordersResponse.data?.data?.orders || []);
      } catch (err) {
        console.warn('Failed to fetch orders:', err);
      }

      // Fetch inventory
      try {
        const inventoryResponse = await productAPI.getProducts({ limit: 1000, bustCache: true });
        const products = inventoryResponse.data?.data?.products || [];

        const lowStock = products
          .filter(p => (p.stockQuantity ?? 0) < (p.minThreshold ?? 0))
          .sort((a, b) => (a.stockQuantity ?? 0) - (b.stockQuantity ?? 0));
        setLowStockProducts(lowStock);

        setInventoryData(products.slice(0, 15).map(p => ({
          ProductID: p.sku,
          CurrentStock: p.stockQuantity || 0
        })));
      } catch (err) {
        console.warn('Failed to fetch inventory:', err);
      }

      // Fetch recent procurement/restock activity (Agents tab)
      if (activeTab === 'agents') {
        try {
          const restockResponse = await restockAPI.getRestockRequests({ limit: 10 });
          setAgentActivity(restockResponse.data?.data?.requests || []);
        } catch (err) {
          console.warn('Failed to fetch restock activity:', err);
        }
      }

      // Legacy sections not backed by MongoDB-only backend
      setShipments([]);

      // Calculate metrics from fetched data
      const processingOrdersCount = orders.filter(o => o.Status === 'Processing' || o.status === 'Processing').length;
      const inTransitCount = shipments.filter(s => s.status === 'out_for_delivery' || s.status === 'picked_up').length;
      const totalInventoryCount = inventoryData.reduce((sum, item) => sum + (item.CurrentStock || 0), 0);

      // KPIs are computed from fetched data, no need to set state

    } catch (err) {
      console.error('Error fetching logistics data:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const getStatusVariant = (status) => {
    const variants = {
      PLACED: 'warning',
      DISPATCHED: 'info',
      DELIVERED: 'success',
    };
    return variants[status] || 'default';
  };

  const getRestockStatusVariant = (status) => {
    const variants = {
      PENDING: 'warning',
      EMAIL_SENT: 'info',
      RESTOCKED: 'success'
    };
    return variants[status] || 'default';
  };

  const handleDispatchOrder = async (orderId) => {
    try {
      await orderAPI.dispatchOrder(orderId);
      fetchAllData();
    } catch (err) {
      console.error('Failed to dispatch order:', err);
      setError(err.response?.data?.message || err.message || 'Failed to dispatch order');
    }
  };

  const handleRunProcurementAgent = async () => {
    setLoading(true);
    try {
      setError(null);
      setSuccess(null);

      const response = await restockAPI.runProcurementAgent();
      const summary = response?.data?.data;

      if (summary) {
        const parts = [
          `Low stock: ${summary.lowStockProducts ?? 0}`,
          `Emailed: ${summary.emailed ?? 0}`,
          `Missing supplier email: ${summary.skippedMissingSupplierEmail ?? 0}`,
          `Already emailed: ${summary.skippedAlreadyEmailed ?? 0}`,
          `Failures: ${summary.failures ?? 0}`
        ];
        setSuccess(`Procurement run completed. ${parts.join(' | ')}`);

        if ((summary.failures ?? 0) > 0) {
          const firstError = summary.results?.find(r => r.status === 'failed')?.error;
          setError(firstError ? `Some emails failed: ${firstError}` : 'Some emails failed. Check SMTP configuration.');
        }
      } else {
        setSuccess('Procurement run completed.');
      }

      await fetchAllData();
    } catch (error) {
      console.error('Error running procurement agent:', error);
      setError(error.response?.data?.message || error.message || 'Failed to run procurement agent');
    } finally {
      setLoading(false);
    }
  };

  const handleRunDeliveryAgent = async () => {
    setError('Delivery agent is not available in the MongoDB backend');
  };

  const handleRefreshActivity = async () => {
    setLoading(true);
    try {
      const restockResponse = await restockAPI.getRestockRequests({ limit: 10 });
      setAgentActivity(restockResponse.data?.data?.requests || []);
    } catch (error) {
      console.error('Error refreshing activity:', error);
    } finally {
      setLoading(false);
    }
  };

  // Overview metrics (computed from real data)
  const overviewMetrics = {
    totalOrders: orders.length,
    totalShipments: 0,
    processingOrders: orders.filter(o => o.status === 'PLACED').length,
    inTransitShipments: orders.filter(o => o.status === 'DISPATCHED').length,
    totalInventory: inventoryData.reduce((sum, item) => sum + (item.CurrentStock || item.current_stock || 0), 0),
    agentActions: agentActivity.length,
  };

  // Orders trend data (last 7 days from real data)
  const ordersTrendData = (() => {
    const last7Days = [];
    const today = new Date();
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const dateStr = date.toISOString().split('T')[0];
      const dayOrders = orders.filter(o => {
        const orderDate = o.OrderDate || o.order_date;
        return orderDate && orderDate.startsWith(dateStr);
      });
      const dayShipments = shipments.filter(s => {
        const shipDate = s.created_at || s.timestamp || s.shipment_date;
        return shipDate && shipDate.startsWith(dateStr);
      });
      last7Days.push({
        date: `${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`,
        orders: dayOrders.length,
        shipments: dayShipments.length
      });
    }
    return last7Days;
  })();

  // Order status distribution
  const orderStatusData = [
    { name: 'Processing', value: orders.filter(o => (o.Status === 'Processing' || o.status === 'Processing')).length },
    { name: 'Shipped', value: orders.filter(o => (o.Status === 'Shipped' || o.status === 'Shipped')).length },
    { name: 'Cancelled', value: orders.filter(o => (o.Status === 'Cancelled' || o.status === 'Cancelled')).length },
  ].filter(item => item.value > 0);

  // Shipment status distribution
  const shipmentStatusData = [
    { name: 'Out for Delivery', value: shipments.filter(s => s.status === 'out_for_delivery').length },
    { name: 'Picked Up', value: shipments.filter(s => s.status === 'picked_up').length },
    { name: 'Created', value: shipments.filter(s => s.status === 'created').length },
    { name: 'Delivered', value: shipments.filter(s => s.status === 'delivered').length },
  ].filter(item => item.value > 0);

  // Inventory trend data (use current inventory data)
  const inventoryTrendData = (() => {
    if (inventoryData.length === 0) return [];
    const topProducts = inventoryData.slice(0, 5);
    const data = [];
    const today = new Date();
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      const dateStr = `${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
      const entry = { date: dateStr };
      topProducts.forEach((product) => {
        const productId = product.ProductID || product.product_id || 'PROD';
        const currentStock = product.CurrentStock || product.current_stock || 0;
        // Use current stock with slight variation for trend visualization
        entry[productId] = Math.max(0, currentStock + Math.floor(Math.random() * 5) - 2);
      });
      data.push(entry);
    }
    return data;
  })();

  const COLORS = [
    'hsl(var(--primary))',
    'hsl(var(--secondary))',
    'hsl(var(--accent))',
    'hsl(var(--info))',
    'hsl(var(--success))',
    'hsl(var(--warning))',
  ];

  const formatDateTime = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString('en-US', { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit', 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Success/Error Alerts */}
      {success && (
        <Alert variant="success" onClose={() => setSuccess(null)}>
          <AlertCircle className="h-4 w-4 mr-2" />
          {success}
        </Alert>
      )}
      {error && (
        <Alert variant="destructive" onClose={() => setError(null)}>
          <AlertCircle className="h-4 w-4 mr-2" />
          {error}
        </Alert>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center gap-6 border-b border-border pb-2">
        <button
          onClick={() => setActiveTab('overview')}
          className={`flex items-center gap-2 px-4 py-2 font-medium transition-colors ${
            activeTab === 'overview'
              ? 'text-primary border-b-2 border-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <LayoutDashboard className="h-4 w-4" />
          Overview
        </button>
        <button
          onClick={() => setActiveTab('orders')}
          className={`flex items-center gap-2 px-4 py-2 font-medium transition-colors ${
            activeTab === 'orders'
              ? 'text-primary border-b-2 border-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Package className="h-4 w-4" />
          Orders
        </button>
        <button
          onClick={() => setActiveTab('shipments')}
          className={`flex items-center gap-2 px-4 py-2 font-medium transition-colors ${
            activeTab === 'shipments'
              ? 'text-primary border-b-2 border-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Truck className="h-4 w-4" />
          Shipments
        </button>
        <button
          onClick={() => setActiveTab('inventory')}
          className={`flex items-center gap-2 px-4 py-2 font-medium transition-colors ${
            activeTab === 'inventory'
              ? 'text-primary border-b-2 border-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <BarChart3 className="h-4 w-4" />
          Inventory
        </button>
        <button
          onClick={() => setActiveTab('agents')}
          className={`flex items-center gap-2 px-4 py-2 font-medium transition-colors ${
            activeTab === 'agents'
              ? 'text-primary border-b-2 border-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          <Bot className="h-4 w-4" />
          Agents
        </button>
      </div>

      {/* Overview Section */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
        <div>
            <h1 className="text-3xl font-heading font-bold tracking-tight">Logistics & Inventory Overview</h1>
          <p className="text-muted-foreground mt-1">
              Comprehensive view of orders, shipments, inventory, and agent activity
          </p>
      </div>

          {/* Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <MetricCard
          title="Total Orders"
              value={overviewMetrics.totalOrders}
          icon={Package}
          variant="primary"
              trend="up"
              trendValue="+12.5%"
            />
            <MetricCard
              title="Total Shipments"
              value={overviewMetrics.totalShipments}
              icon={Truck}
              variant="info"
              trend="up"
              trendValue="+8.2%"
            />
            <MetricCard
              title="Processing Orders"
              value={overviewMetrics.processingOrders}
              icon={Activity}
              variant="warning"
        />
        <MetricCard
          title="In Transit"
              value={overviewMetrics.inTransitShipments}
          icon={Truck}
          variant="info"
        />
        <MetricCard
              title="Total Inventory"
              value={overviewMetrics.totalInventory}
              icon={BarChart3}
          variant="success"
              trend="up"
              trendValue="+5.3%"
        />
        <MetricCard
              title="Agent Actions"
              value={overviewMetrics.agentActions}
              icon={Bot}
              variant="accent"
        />
      </div>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                Low Stock Products
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>product</TableHead>
                      <TableHead>sku</TableHead>
                      <TableHead>stock</TableHead>
                      <TableHead>threshold</TableHead>
                      <TableHead>supplier email</TableHead>
                      <TableHead>status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {lowStockProducts.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center text-muted-foreground py-6">
                          No low stock products
                        </TableCell>
                      </TableRow>
                    ) : (
                      lowStockProducts.slice(0, 10).map((p) => (
                        <TableRow key={p._id || p.sku}>
                          <TableCell className="font-medium">{p.name}</TableCell>
                          <TableCell className="font-mono text-xs">{p.sku}</TableCell>
                          <TableCell className="font-mono text-xs">{p.stockQuantity ?? 0}</TableCell>
                          <TableCell className="font-mono text-xs">{p.minThreshold ?? 0}</TableCell>
                          <TableCell className="max-w-xs truncate">{p.supplier?.email || '-'}</TableCell>
                          <TableCell>
                            <Badge variant="warning">LOW</Badge>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          {/* Charts Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Orders Trend Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Orders & Shipments Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={ordersTrendData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fill: 'hsl(var(--muted-foreground))' }}
                      className="text-xs"
                    />
                    <YAxis 
                      tick={{ fill: 'hsl(var(--muted-foreground))' }}
                      className="text-xs"
                    />
                    <Tooltip 
                      contentStyle={{
                        backgroundColor: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '0.5rem',
                      }}
                    />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="orders" 
                      stroke="hsl(var(--primary))" 
                      strokeWidth={2}
                      name="Orders"
                      dot={{ fill: 'hsl(var(--primary))' }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="shipments" 
                      stroke="hsl(var(--info))" 
                      strokeWidth={2}
                      name="Shipments"
                      dot={{ fill: 'hsl(var(--info))' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Order Status Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Order Status Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={orderStatusData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {orderStatusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip 
                      contentStyle={{
                        backgroundColor: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '0.5rem',
                      }}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Shipment Status Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Shipment Status Breakdown</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={shipmentStatusData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis 
                      dataKey="name" 
                      tick={{ fill: 'hsl(var(--muted-foreground))' }}
                      className="text-xs"
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis 
                      tick={{ fill: 'hsl(var(--muted-foreground))' }}
                      className="text-xs"
                    />
                    <Tooltip 
                      contentStyle={{
                        backgroundColor: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '0.5rem',
                      }}
                    />
                    <Bar 
                      dataKey="value" 
                      fill="hsl(var(--primary))"
                      radius={[8, 8, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Inventory Trend Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Inventory Levels Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={inventoryTrendData}>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fill: 'hsl(var(--muted-foreground))' }}
                      className="text-xs"
                    />
                    <YAxis 
                      tick={{ fill: 'hsl(var(--muted-foreground))' }}
                      className="text-xs"
                    />
                    <Tooltip 
                      contentStyle={{
                        backgroundColor: 'hsl(var(--card))',
                        border: '1px solid hsl(var(--border))',
                        borderRadius: '0.5rem',
                      }}
                    />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="USR001" 
                      stroke="hsl(var(--primary))" 
                      strokeWidth={2}
                      dot={{ fill: 'hsl(var(--primary))' }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="USR002" 
                      stroke="hsl(var(--secondary))" 
                      strokeWidth={2}
                      dot={{ fill: 'hsl(var(--secondary))' }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="USR003" 
                      stroke="hsl(var(--accent))" 
                      strokeWidth={2}
                      dot={{ fill: 'hsl(var(--accent))' }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="USR004" 
                      stroke="hsl(var(--info))" 
                      strokeWidth={2}
                      dot={{ fill: 'hsl(var(--info))' }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="USR005" 
                      stroke="hsl(var(--success))" 
                      strokeWidth={2}
                      dot={{ fill: 'hsl(var(--success))' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Current Stock Levels Bar Chart */}
      <Card>
        <CardHeader>
              <CardTitle>Current Stock Levels by Product</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={inventoryData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis 
                    dataKey="ProductID" 
                    tick={{ fill: 'hsl(var(--muted-foreground))' }}
                    className="text-xs"
                  />
                  <YAxis 
                    label={{ value: 'CurrentStock', angle: -90, position: 'insideLeft' }}
                    tick={{ fill: 'hsl(var(--muted-foreground))' }}
                    className="text-xs"
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '0.5rem',
                    }}
                  />
                  <Bar 
                    dataKey="CurrentStock" 
                    fill="hsl(var(--primary))"
                    radius={[8, 8, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Orders Section */}
      {activeTab === 'orders' && (
        <div className="space-y-4">
          <h1 className="text-3xl font-heading font-bold tracking-tight">Order Management</h1>
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Order</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Items</TableHead>
                    <TableHead>Total</TableHead>
                    <TableHead>Placed At</TableHead>
                    <TableHead className="text-right">Action</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {orders.map((order) => (
                    <TableRow key={order._id}>
                      <TableCell className="font-medium">{order.orderNumber}</TableCell>
                      <TableCell>
                        <Badge variant={getStatusVariant(order.status)}>
                          {order.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">{order.customerId?.name || 'Customer'}</span>
                          <span className="text-xs text-muted-foreground">{order.customerId?.email || ''}</span>
                        </div>
                      </TableCell>
                      <TableCell className="max-w-xs truncate">
                        {(order.items || []).map((it) => `${it.sku}×${it.quantity}`).join(', ')}
                      </TableCell>
                      <TableCell>₹{Number(order.totalAmount || 0).toFixed(2)}</TableCell>
                      <TableCell>{formatDateTime(order.tracking?.placedAt || order.createdAt)}</TableCell>
                      <TableCell className="text-right">
                        {order.status === 'PLACED' ? (
                          <Button size="sm" onClick={() => handleDispatchOrder(order._id)}>
                            Dispatch
                          </Button>
                        ) : (
                          <span className="text-sm text-muted-foreground">-</span>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Shipments Section */}
      {activeTab === 'shipments' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-heading font-bold tracking-tight">Shipment Tracking</h1>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm">
                <Download className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="sm">
                <Search className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="sm">
                <Maximize2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
          <Card>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                      <TableHead>shipment_id</TableHead>
                      <TableHead>order_id</TableHead>
                      <TableHead>courier_id</TableHead>
                      <TableHead>tracking_number</TableHead>
                      <TableHead>status</TableHead>
                      <TableHead>origin_address</TableHead>
                      <TableHead>destination</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
                    {shipments.map((shipment) => (
                      <TableRow key={shipment.shipment_id}>
                        <TableCell className="font-medium">{shipment.shipment_id}</TableCell>
                        <TableCell>{shipment.order_id}</TableCell>
                        <TableCell>{shipment.courier_id}</TableCell>
                        <TableCell>{shipment.tracking_number}</TableCell>
                  <TableCell>
                          <Badge variant={getStatusVariant(shipment.status)}>
                            {shipment.status}
                    </Badge>
                  </TableCell>
                        <TableCell>{shipment.origin_address}</TableCell>
                        <TableCell className="max-w-xs truncate">{shipment.destination}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Inventory Section */}
      {activeTab === 'inventory' && (
        <div className="space-y-4">
          <h1 className="text-3xl font-heading font-bold tracking-tight">Inventory Status</h1>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                Low Stock Products
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>product</TableHead>
                      <TableHead>sku</TableHead>
                      <TableHead>stock</TableHead>
                      <TableHead>threshold</TableHead>
                      <TableHead>supplier email</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {lowStockProducts.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center text-muted-foreground py-6">
                          No low stock products
                        </TableCell>
                      </TableRow>
                    ) : (
                      lowStockProducts.slice(0, 10).map((p) => (
                        <TableRow key={p._id || p.sku}>
                          <TableCell className="font-medium">{p.name}</TableCell>
                          <TableCell className="font-mono text-xs">{p.sku}</TableCell>
                          <TableCell className="font-mono text-xs">{p.stockQuantity ?? 0}</TableCell>
                          <TableCell className="font-mono text-xs">{p.minThreshold ?? 0}</TableCell>
                          <TableCell className="max-w-xs truncate">{p.supplier?.email || '-'}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Current Stock Levels</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={inventoryData}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis 
                    dataKey="ProductID" 
                    tick={{ fill: 'hsl(var(--muted-foreground))' }}
                    className="text-xs"
                  />
                  <YAxis 
                    label={{ value: 'CurrentStock', angle: -90, position: 'insideLeft' }}
                    tick={{ fill: 'hsl(var(--muted-foreground))' }}
                    className="text-xs"
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'hsl(var(--card))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '0.5rem',
                    }}
                  />
                  <Bar 
                    dataKey="CurrentStock" 
                    fill="hsl(var(--primary))"
                    radius={[8, 8, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Agents Section */}
      {activeTab === 'agents' && (
        <div className="space-y-4">
          <h1 className="text-3xl font-heading font-bold tracking-tight">SETU Controls</h1>
          
          <div className="flex items-center gap-4">
            <Button onClick={handleRunProcurementAgent} disabled={loading}>
              <Building2 className="h-4 w-4 mr-2" />
              Run Procurement Agent
            </Button>
            <Button onClick={handleRunDeliveryAgent} disabled={loading} variant="outline">
              <TruckIcon className="h-4 w-4 mr-2" />
              Run Delivery Agent
            </Button>
          </div>

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Recent Agent Activity</CardTitle>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={handleRefreshActivity}
                      disabled={loading}
                      className={loading ? 'animate-spin' : ''}
                      aria-label="Refresh activity"
                    >
                  <RefreshCw className="h-4 w-4" />
                    </Button>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>created</TableHead>
                      <TableHead>product</TableHead>
                      <TableHead>sku</TableHead>
                      <TableHead>requested</TableHead>
                      <TableHead>supplier</TableHead>
                      <TableHead>status</TableHead>
                      <TableHead>email sent</TableHead>
                      <TableHead>notes</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {agentActivity.map((activity, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-mono text-xs">
                          {formatDateTime(activity.createdAt)}
                        </TableCell>
                        <TableCell>{activity.productName || activity.productId?.name || '-'}</TableCell>
                        <TableCell>{activity.sku || activity.productId?.sku || '-'}</TableCell>
                        <TableCell>{activity.requestedQuantity ?? '-'}</TableCell>
                        <TableCell className="max-w-xs truncate">{activity.supplierEmail || '-'}</TableCell>
                        <TableCell>
                          <Badge variant={getRestockStatusVariant(activity.status)}>
                            {activity.status || '-'}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-xs">
                          {activity.emailSentAt ? formatDateTime(activity.emailSentAt) : '-'}
                        </TableCell>
                        <TableCell className="max-w-xs truncate">{activity.notes || '-'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
              </div>
        </CardContent>
      </Card>
        </div>
      )}
    </div>
  );
};

export default Logistics;
