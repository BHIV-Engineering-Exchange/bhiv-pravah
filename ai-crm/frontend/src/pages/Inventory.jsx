import React, { useState, useEffect, useCallback } from 'react';
import { 
  ShoppingCart, AlertTriangle, TrendingUp, TrendingDown, 
  Plus, Search, Filter, RefreshCw, Package
} from 'lucide-react';
import Card, { CardHeader, CardTitle, CardContent } from '../components/common/ui/Card';
import MetricCard from '../components/common/charts/MetricCard';
import Button from '../components/common/ui/Button';
import Input from '../components/common/forms/Input';
import Badge from '../components/common/ui/Badge';
import { Alert } from '../components/common/ui/Alert';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../components/common/ui/Table';
import { LoadingSpinner } from '../components/common/ui/Spinner';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { productAPI } from '../services/api/productAPI';

export const Inventory = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [inventory, setInventory] = useState([]);
  const [lowStockItems, setLowStockItems] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [metrics, setMetrics] = useState({
    totalItems: 0,
    inStock: 0,
    lowStock: 0,
    outOfStock: 0,
    totalValue: 0,
  });

  // Fetch inventory data
  const fetchInventoryData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch inventory
      const inventoryResponse = await productAPI.getProducts({ limit: 1000, bustCache: true });
      const inventoryData = inventoryResponse.data?.data?.products || [];

      // Transform inventory data
      const formattedInventory = inventoryData.map(item => {
        const currentStock = item.stockQuantity || 0;
        const reorderPoint = item.minThreshold || 0;
        const unitCost = item.costPrice || 0;
        const totalValue = currentStock * unitCost;
        
        let status = 'in_stock';
        if (currentStock === 0) {
          status = 'out_of_stock';
        } else if (currentStock <= reorderPoint) {
          status = 'low_stock';
        }

        return {
          id: item._id,
          productName: item.name || 'Unknown',
          productId: item.sku || item._id,
          currentStock,
          reorderPoint,
          unitCost,
          totalValue,
          status,
          lastRestocked: item.updatedAt ? new Date(item.updatedAt) : new Date()
        };
      });

      setInventory(formattedInventory);
      setLowStockItems(formattedInventory.filter(item => item.status === 'low_stock' || item.status === 'out_of_stock'));

      // Calculate metrics
      const totalItems = formattedInventory.length;
      const inStock = formattedInventory.filter(item => item.status === 'in_stock').length;
      const lowStock = formattedInventory.filter(item => item.status === 'low_stock').length;
      const outOfStock = formattedInventory.filter(item => item.status === 'out_of_stock').length;
      const totalValue = formattedInventory.reduce((sum, item) => sum + item.totalValue, 0);

      setMetrics({
        totalItems,
        inStock,
        lowStock,
        outOfStock,
        totalValue: Math.round(totalValue),
      });

    } catch (err) {
      console.error('Error fetching inventory:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load inventory');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchInventoryData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchInventoryData();
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchInventoryData]);

  const getStatusVariant = (status) => {
    const variants = {
      in_stock: 'success',
      low_stock: 'warning',
      out_of_stock: 'destructive',
    };
    return variants[status] || 'default';
  };

  const filteredInventory = inventory.filter(item => 
    item.productName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.productId.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const stockChartData = [
    { name: 'In Stock', value: metrics.inStock, color: '#22c55e' },
    { name: 'Low Stock', value: metrics.lowStock, color: '#f59e0b' },
    { name: 'Out of Stock', value: metrics.outOfStock, color: '#ef4444' },
  ].filter(item => item.value > 0);

  if (loading) {
    return <LoadingSpinner text="Loading inventory..." />;
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-heading font-bold tracking-tight">Inventory Management</h1>
          <p className="text-muted-foreground mt-1">
            Monitor stock levels and manage inventory
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={fetchInventoryData}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Adjust Stock
          </Button>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive" onClose={() => setError(null)}>
          <AlertTriangle className="h-4 w-4 mr-2" />
          {error}
        </Alert>
      )}

      {/* Low Stock Alerts */}
      {lowStockItems.length > 0 && (
        <Alert variant="warning" className="border-l-4 border-warning">
          <AlertTriangle className="h-5 w-5" />
          <div>
            <h4 className="font-semibold">Low Stock Alert</h4>
            <p className="text-sm">
              {lowStockItems.length} {lowStockItems.length === 1 ? 'item' : 'items'} {lowStockItems.some(i => i.status === 'out_of_stock') ? 'are out of stock or' : ''} need restocking
            </p>
          </div>
        </Alert>
      )}

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        <MetricCard
          title="Total Items"
          value={metrics.totalItems.toLocaleString()}
          icon={ShoppingCart}
          variant="primary"
        />
        <MetricCard
          title="In Stock"
          value={metrics.inStock.toLocaleString()}
          icon={Package}
          variant="success"
        />
        <MetricCard
          title="Low Stock"
          value={metrics.lowStock.toLocaleString()}
          icon={AlertTriangle}
          variant="warning"
        />
        <MetricCard
          title="Out of Stock"
          value={metrics.outOfStock.toLocaleString()}
          icon={Package}
          variant="destructive"
        />
        <MetricCard
          title="Total Value"
          value={metrics.totalValue.toLocaleString()}
          icon={TrendingUp}
          variant="accent"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Stock Status Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stockChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Low Stock Items</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {lowStockItems.slice(0, 5).map((item) => (
                <div key={item.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                  <div>
                    <div className="font-medium">{item.productName}</div>
                    <div className="text-sm text-muted-foreground">
                      Current: {item.currentStock} | Reorder: {item.reorderPoint}
                    </div>
                  </div>
                  <Badge variant={getStatusVariant(item.status)}>
                    {item.status.replace('_', ' ')}
                  </Badge>
                </div>
              ))}
              {lowStockItems.length === 0 && (
                <p className="text-center text-muted-foreground py-8">No low stock items</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Inventory Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Inventory Items</CardTitle>
            <div className="flex items-center gap-3">
              <Input
                placeholder="Search inventory..."
                icon={Search}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-64"
              />
              <Button variant="outline">
                <Filter className="h-4 w-4 mr-2" />
                Filter
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Product</TableHead>
                <TableHead>Product ID</TableHead>
                <TableHead>Current Stock</TableHead>
                <TableHead>Reorder Point</TableHead>
                <TableHead>Unit Cost</TableHead>
                <TableHead>Total Value</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Last Restocked</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredInventory.map((item) => (
                <TableRow key={item.id}>
                  <TableCell className="font-medium">{item.productName}</TableCell>
                  <TableCell className="text-muted-foreground">{item.productId}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {item.currentStock}
                      {item.currentStock < item.reorderPoint && (
                        <TrendingDown className="h-4 w-4 text-warning" />
                      )}
                    </div>
                  </TableCell>
                  <TableCell>{item.reorderPoint}</TableCell>
                  <TableCell>{item.unitCost.toFixed(2)}</TableCell>
                  <TableCell className="font-semibold">{item.totalValue.toLocaleString()}</TableCell>
                  <TableCell>
                    <Badge variant={getStatusVariant(item.status)}>
                      {item.status.replace('_', ' ')}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {new Date(item.lastRestocked).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <Button variant="ghost" size="sm">
                      Adjust
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default Inventory;
