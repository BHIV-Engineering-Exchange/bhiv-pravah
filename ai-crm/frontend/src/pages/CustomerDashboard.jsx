import React, { useState, useEffect } from 'react';
import { ShoppingCart, Package, Search, Filter, Grid, List, Plus, Minus, Check } from 'lucide-react';
import Button from '../components/common/ui/Button';
import Card from '../components/common/ui/Card';
import { productAPI } from '../services/api/productAPI';
import { orderAPI } from '../services/api/orderAPI';

const CustomerDashboard = () => {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [category, setCategory] = useState('all');
  const [viewMode, setViewMode] = useState('grid');
  const [orderHistory, setOrderHistory] = useState([]);

  useEffect(() => {
    fetchProducts();
    fetchOrderHistory();
  }, []);

  const normalizeProduct = (p) => {
    return {
      id: p._id || p.id,
      name: p.name || 'Unnamed Product',
      description: p.description || '',
      category: p.category || '',
      price: Number(p.sellingPrice || p.price || 0),
      stock: Number(p.stockQuantity || p.stock || 0),
      image_url: p.image_url || p.imageUrl || '/api/placeholder/400/300',
    };
  };

  const normalizeOrder = (o) => {
    return {
      id: o._id || o.id,
      created_at: o.createdAt || o.created_at,
      total_amount: Number(o.totalAmount || o.total_amount || 0),
      status: String(o.status || 'PLACED').toUpperCase(),
    };
  };

  const getOrderStatusLabel = (status) => {
    if (status === 'PLACED') return 'PLACED';
    if (status === 'DISPATCHED') return 'DISPATCHED';
    if (status === 'DELIVERED') return 'DELIVERED';
    return status;
  };

  const getOrderStatusClass = (status) => {
    if (status === 'DELIVERED') return 'text-success';
    if (status === 'PLACED') return 'text-warning';
    if (status === 'DISPATCHED') return 'text-info';
    return 'text-muted-foreground';
  };

  const confirmReceived = async (orderId) => {
    try {
      const response = await orderAPI.confirmDelivery(orderId);
      if (response.data?.success) {
        alert('Thank you! Order marked as delivered.');
        fetchOrderHistory();
      }
    } catch (error) {
      console.error('Error confirming delivery:', error);
      alert('Failed to confirm delivery. Please try again.');
    }
  };

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const response = await productAPI.getProducts({
        limit: 1000,
        isActive: 'true',
        bustCache: true,
      });
      const rawProducts = response.data?.data?.products || [];
      setProducts(Array.isArray(rawProducts) ? rawProducts.map(normalizeProduct) : []);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchOrderHistory = async () => {
    try {
      const response = await orderAPI.getOrders({ page: 1, limit: 50 });
      const rawOrders = response.data?.data?.orders || [];
      setOrderHistory(Array.isArray(rawOrders) ? rawOrders.map(normalizeOrder) : []);
    } catch (error) {
      console.error('Error fetching order history:', error);
    }
  };

  const addToCart = (product) => {
    const existingItem = cart.find(item => item.id === product.id);
    if (existingItem) {
      setCart(cart.map(item => 
        item.id === product.id 
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ));
    } else {
      setCart([...cart, { ...product, quantity: 1 }]);
    }
  };

  const removeFromCart = (productId) => {
    const existingItem = cart.find(item => item.id === productId);
    if (existingItem.quantity > 1) {
      setCart(cart.map(item =>
        item.id === productId
          ? { ...item, quantity: item.quantity - 1 }
          : item
      ));
    } else {
      setCart(cart.filter(item => item.id !== productId));
    }
  };

  const placeOrder = async () => {
    if (cart.length === 0) return;

    try {
      const response = await orderAPI.createOrder({
        items: cart.map((item) => ({
          productId: item.id,
          quantity: item.quantity,
        })),
      });

      if (response.data?.success) {
        alert('Order placed successfully! You will receive a confirmation email.');
        setCart([]);
        fetchOrderHistory();
        fetchProducts(); // refresh stock after order
      }
    } catch (error) {
      console.error('Error placing order:', error);
      alert('Failed to place order. Please try again.');
    }
  };

  const filteredProducts = products.filter(product => {
    const matchesSearch = product.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         product.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = category === 'all' || product.category === category;
    return matchesSearch && matchesCategory;
  });

  const cartTotal = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const cartItemCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary via-secondary to-accent p-6 shadow-lg">
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">Customer Portal</h1>
              <p className="text-white/80">Browse our product catalog and place orders</p>
            </div>
            <div className="relative">
              <Button
                onClick={() => document.getElementById('cart-section').scrollIntoView({ behavior: 'smooth' })}
                className="bg-white/20 hover:bg-white/30 text-white"
              >
                <ShoppingCart className="w-5 h-5 mr-2" />
                Cart ({cartItemCount})
              </Button>
              {cartItemCount > 0 && (
                <span className="absolute -top-2 -right-2 bg-destructive text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold">
                  {cartItemCount}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Search and Filters */}
        <Card className="p-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-5 h-5" />
              <input
                type="text"
                placeholder="Search products..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
              />
            </div>
            <div className="flex gap-2">
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary"
              >
                <option value="all">All Categories</option>
                <option value="electronics">Electronics</option>
                <option value="furniture">Furniture</option>
                <option value="clothing">Clothing</option>
                <option value="food">Food & Beverage</option>
              </select>
              <div className="flex border rounded-lg overflow-hidden">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 ${viewMode === 'grid' ? 'bg-primary text-white' : 'bg-white'}`}
                >
                  <Grid className="w-5 h-5" />
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 ${viewMode === 'list' ? 'bg-primary text-white' : 'bg-white'}`}
                >
                  <List className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        </Card>

        {/* Products Grid/List */}
        <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-4'}>
          {loading ? (
            <div className="col-span-full text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
              <p className="mt-4 text-muted-foreground">Loading products...</p>
            </div>
          ) : filteredProducts.length === 0 ? (
            <div className="col-span-full text-center py-12">
              <Package className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No products found</p>
            </div>
          ) : (
            filteredProducts.map((product) => (
              <Card key={product.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                <div className={viewMode === 'grid' ? '' : 'flex'}>
                  <div className={viewMode === 'grid' ? 'h-48' : 'w-48 h-48'}>
                    <img
                      src={product.image_url}
                      alt={product.name}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <div className="p-6 flex-1">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold text-lg">{product.name}</h3>
                      <span className="text-primary font-bold text-xl">${product.price}</span>
                    </div>
                    <p className="text-sm text-muted-foreground mb-4">{product.description}</p>
                    <div className="flex items-center justify-between">
                      <div className="text-sm">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
                          product.stock > 50 ? 'bg-success/10 text-success' :
                          product.stock > 0 ? 'bg-warning/10 text-warning' :
                          'bg-destructive/10 text-destructive'
                        }`}>
                          {product.stock > 0 ? `${product.stock} in stock` : 'Out of stock'}
                        </span>
                      </div>
                      <Button
                        onClick={() => addToCart(product)}
                        disabled={product.stock === 0}
                        size="sm"
                      >
                        <Plus className="w-4 h-4 mr-1" />
                        Add to Cart
                      </Button>
                    </div>
                  </div>
                </div>
              </Card>
            ))
          )}
        </div>

        {/* Shopping Cart */}
        <div id="cart-section">
          <Card className="p-6">
            <h2 className="text-2xl font-bold mb-6 flex items-center">
              <ShoppingCart className="w-6 h-6 mr-2 text-primary" />
              Shopping Cart
            </h2>
            {cart.length === 0 ? (
              <div className="text-center py-12">
                <ShoppingCart className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">Your cart is empty</p>
              </div>
            ) : (
              <>
                <div className="space-y-4 mb-6">
                  {cart.map((item) => (
                    <div key={item.id} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4 flex-1">
                        <img
                          src={item.image_url}
                          alt={item.name}
                          className="w-20 h-20 object-cover rounded"
                        />
                        <div>
                          <h4 className="font-semibold">{item.name}</h4>
                          <p className="text-sm text-muted-foreground">${item.price} each</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                          <Button
                            onClick={() => removeFromCart(item.id)}
                            variant="outline"
                            size="sm"
                          >
                            <Minus className="w-4 h-4" />
                          </Button>
                          <span className="w-12 text-center font-semibold">{item.quantity}</span>
                          <Button
                            onClick={() => addToCart(item)}
                            variant="outline"
                            size="sm"
                          >
                            <Plus className="w-4 h-4" />
                          </Button>
                        </div>
                        <div className="w-24 text-right font-bold">
                          ${(item.price * item.quantity).toFixed(2)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="border-t pt-6">
                  <div className="flex justify-between items-center mb-6">
                    <span className="text-xl font-semibold">Total:</span>
                    <span className="text-3xl font-bold text-primary">${cartTotal.toFixed(2)}</span>
                  </div>
                  <Button
                    onClick={placeOrder}
                    className="w-full bg-gradient-to-r from-primary to-secondary hover:from-primary/90 hover:to-secondary/90"
                    size="lg"
                  >
                    <Check className="w-5 h-5 mr-2" />
                    Place Order
                  </Button>
                </div>
              </>
            )}
          </Card>
        </div>

        {/* Order History */}
        {orderHistory.length > 0 && (
          <Card className="p-6">
            <h2 className="text-2xl font-bold mb-6">Order History</h2>
            <div className="space-y-4">
              {orderHistory.map((order) => (
                <div key={order.id} className="p-4 border rounded-lg">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h4 className="font-semibold">Order #{order.id.slice(-8)}</h4>
                      <p className="text-sm text-muted-foreground">{new Date(order.created_at).toLocaleDateString()}</p>
                    </div>
                    <div className="text-right">
                      <span className="font-bold text-lg">${order.total_amount.toFixed(2)}</span>
                      <span className={`block text-sm ${
                        getOrderStatusClass(order.status)
                      }`}>
                        {getOrderStatusLabel(order.status)}
                      </span>
                    </div>
                  </div>

                  {order.status === 'DISPATCHED' && (
                    <div className="mt-3 flex justify-end">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => confirmReceived(order.id)}
                      >
                        Mark Received
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Card>
        )}
      </div>
    </div>
  );
};

export default CustomerDashboard;
