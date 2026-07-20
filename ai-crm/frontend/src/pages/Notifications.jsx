import React, { useState, useEffect, useCallback } from 'react';
import { 
  Bell, AlertTriangle, CheckCircle, Info, XCircle,
  Settings, Filter, CheckCheck, RefreshCw
} from 'lucide-react';
import Card, { CardHeader, CardTitle, CardContent } from '../components/common/ui/Card';
import MetricCard from '../components/common/charts/MetricCard';
import Button from '../components/common/ui/Button';
import Badge from '../components/common/ui/Badge';
import Alert from '../components/common/ui/Alert';
import { LoadingSpinner } from '../components/common/ui/Spinner';
import { formatRelativeTime } from '@/utils/dateUtils';
import { dashboardAPI } from '../services/api/dashboardAPI';

export const Notifications = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [filter, setFilter] = useState('all'); // all, unread, read
  const [metrics, setMetrics] = useState({
    total: 0,
    unread: 0,
    today: 0,
    critical: 0,
  });

  // Fetch alerts from backend
  const fetchNotifications = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await dashboardAPI.getAlerts();
      const alerts = response.data?.alerts || response.data || [];

      // Transform alerts to notifications format
      const formattedNotifications = alerts.map((alert, index) => ({
        id: alert.id || index + 1,
        type: alert.severity === 'critical' ? 'error' :
              alert.severity === 'high' ? 'warning' :
              alert.severity === 'medium' ? 'info' : 'success',
        title: alert.title || alert.message || 'Alert',
        message: alert.message || alert.description || '',
        timestamp: alert.timestamp ? new Date(alert.timestamp) : new Date(),
        read: alert.read || false,
        severity: alert.severity || 'medium'
      }));

      setNotifications(formattedNotifications);

      // Calculate metrics
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const todayAlerts = formattedNotifications.filter(n => n.timestamp >= today);
      const unreadAlerts = formattedNotifications.filter(n => !n.read);
      const criticalAlerts = formattedNotifications.filter(n => n.severity === 'critical');

      setMetrics({
        total: formattedNotifications.length,
        unread: unreadAlerts.length,
        today: todayAlerts.length,
        critical: criticalAlerts.length,
      });

    } catch (err) {
      console.error('Error fetching notifications:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load notifications');
      // Fallback to empty array
      setNotifications([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchNotifications();
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchNotifications]);

  const getIcon = (type) => {
    const icons = {
      warning: AlertTriangle,
      success: CheckCircle,
      info: Info,
      error: XCircle,
    };
    return icons[type] || Info;
  };

  const getVariant = (type) => {
    const variants = {
      warning: 'warning',
      success: 'success',
      info: 'info',
      error: 'destructive',
    };
    return variants[type] || 'default';
  };

  const filteredNotifications = filter === 'all' 
    ? notifications 
    : filter === 'unread' 
    ? notifications.filter(n => !n.read)
    : notifications.filter(n => n.read);

  if (loading) {
    return <LoadingSpinner text="Loading notifications..." />;
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-heading font-bold tracking-tight">Alert Management</h1>
          <p className="text-muted-foreground mt-1">
            View and manage system notifications and alerts
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="outline" size="sm" onClick={fetchNotifications}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline">
            <Filter className="h-4 w-4 mr-2" />
            Filter
          </Button>
          <Button variant="outline">
            <CheckCheck className="h-4 w-4 mr-2" />
            Mark All Read
          </Button>
          <Button>
            <Settings className="h-4 w-4 mr-2" />
            Settings
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

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Notifications"
          value={metrics.total.toLocaleString()}
          icon={Bell}
          variant="primary"
        />
        <MetricCard
          title="Unread"
          value={metrics.unread.toLocaleString()}
          icon={Bell}
          variant="warning"
        />
        <MetricCard
          title="Today"
          value={metrics.today.toLocaleString()}
          icon={Bell}
          variant="accent"
        />
        <MetricCard
          title="Critical"
          value={metrics.critical.toLocaleString()}
          icon={AlertTriangle}
          variant="destructive"
        />
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-border">
        <button
          onClick={() => setFilter('all')}
          className={`px-4 py-2 font-medium transition-colors ${
            filter === 'all'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          All ({notifications.length})
        </button>
        <button
          onClick={() => setFilter('unread')}
          className={`px-4 py-2 font-medium transition-colors ${
            filter === 'unread'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Unread ({notifications.filter(n => !n.read).length})
        </button>
        <button
          onClick={() => setFilter('read')}
          className={`px-4 py-2 font-medium transition-colors ${
            filter === 'read'
              ? 'border-b-2 border-primary text-primary'
              : 'text-muted-foreground hover:text-foreground'
          }`}
        >
          Read ({notifications.filter(n => n.read).length})
        </button>
      </div>

      {/* Notifications List */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-3">
            {filteredNotifications.map((notification) => {
              const Icon = getIcon(notification.type);
              return (
                <div
                  key={notification.id}
                  className={`flex items-start gap-4 p-4 rounded-lg border transition-all ${
                    notification.read
                      ? 'bg-muted/30 border-border'
                      : 'bg-background border-primary/20'
                  }`}
                >
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    notification.type === 'warning' ? 'bg-warning/10' :
                    notification.type === 'success' ? 'bg-success/10' :
                    notification.type === 'error' ? 'bg-destructive/10' :
                    'bg-primary/10'
                  }`}>
                    <Icon className={`h-5 w-5 ${
                      notification.type === 'warning' ? 'text-warning' :
                      notification.type === 'success' ? 'text-success' :
                      notification.type === 'error' ? 'text-destructive' :
                      'text-primary'
                    }`} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="font-semibold">{notification.title}</h3>
                      {!notification.read && (
                        <Badge variant="primary" className="text-xs">New</Badge>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">{notification.message}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatRelativeTime(notification.timestamp)}
                    </p>
                  </div>
                </div>
              );
            })}
            {filteredNotifications.length === 0 && (
              <div className="text-center py-12">
                <Bell className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">No notifications found</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Notifications;
