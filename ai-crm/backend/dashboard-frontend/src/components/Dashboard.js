import React, { useState, useEffect } from 'react';
import {
  Container, Grid, Card, CardContent, Typography, Box,
  Alert, Chip, useMediaQuery, useTheme, CircularProgress,
  Paper, Divider
} from '@mui/material';
import {
  ShoppingCart, LocalShipping, Inventory, TrendingUp,
  Warning, CheckCircle, Error, Info
} from '@mui/icons-material';
import { Pie, Bar } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js';
import { dashboardAPI } from '../services/api';

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

const Dashboard = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [kpis, setKpis] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [charts, setCharts] = useState(null);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [kpisRes, alertsRes, chartsRes, activityRes] = await Promise.all([
        dashboardAPI.getKPIs(),
        dashboardAPI.getAlerts(),
        dashboardAPI.getCharts(),
        dashboardAPI.getRecentActivity()
      ]);

      setKpis(kpisRes.data);
      setAlerts(alertsRes.data);
      setCharts(chartsRes.data);
      setActivity(activityRes.data);
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getAlertIcon = (severity) => {
    switch (severity) {
      case 'critical': return <Error color="error" />;
      case 'high': return <Warning color="warning" />;
      case 'medium': return <Info color="info" />;
      default: return <CheckCircle color="success" />;
    }
  };

  const getAlertColor = (severity) => {
    switch (severity) {
      case 'critical': return 'error';
      case 'high': return 'warning';
      case 'medium': return 'info';
      default: return 'success';
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 2, mb: 4 }}>
      <Typography variant="h4" gutterBottom sx={{ mb: 3 }}>
        🚚 AI Agent Logistics Dashboard
      </Typography>

      {/* KPI Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#e3f2fd' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <ShoppingCart color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Total Orders</Typography>
              </Box>
              <Typography variant="h4" color="primary">
                {kpis?.total_orders || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {kpis?.active_shipments || 0} active shipments
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#f3e5f5' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <LocalShipping color="secondary" sx={{ mr: 1 }} />
                <Typography variant="h6">Delivery Rate</Typography>
              </Box>
              <Typography variant="h4" color="secondary">
                {kpis?.delivery_rate?.toFixed(1) || 0}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Last 7 days
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#e8f5e8' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <Inventory color="success" sx={{ mr: 1 }} />
                <Typography variant="h6">Stock Health</Typography>
              </Box>
              <Typography variant="h4" color="success">
                {kpis?.stock_health?.toFixed(1) || 0}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {kpis?.low_stock_count || 0} items low
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: '#fff3e0' }}>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <TrendingUp sx={{ mr: 1, color: '#ff9800' }} />
                <Typography variant="h6">Automation</Typography>
              </Box>
              <Typography variant="h4" sx={{ color: '#ff9800' }}>
                {kpis?.automation_rate?.toFixed(1) || 0}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {kpis?.pending_reviews || 0} pending reviews
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Alerts Section */}
      {alerts.length > 0 && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
            🚨 System Alerts
          </Typography>
          {alerts.map((alert, index) => (
            <Alert
              key={index}
              severity={getAlertColor(alert.severity)}
              icon={getAlertIcon(alert.severity)}
              sx={{ mb: 1 }}
            >
              <Typography variant="subtitle2">{alert.title}</Typography>
              <Typography variant="body2">{alert.message}</Typography>
              <Typography variant="caption" color="text.secondary">
                {new Date(alert.timestamp).toLocaleString()}
              </Typography>
            </Alert>
          ))}
        </Paper>
      )}

      {/* Charts Section */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Order Status Distribution
            </Typography>
            {charts?.orderStatus && (
              <Box sx={{ height: 300 }}>
                <Pie
                  data={{
                    labels: Object.keys(charts.orderStatus),
                    datasets: [{
                      data: Object.values(charts.orderStatus),
                      backgroundColor: ['#ff6384', '#36a2eb', '#cc65fe', '#ffce56'],
                    }]
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                  }}
                />
              </Box>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Inventory Levels
            </Typography>
            {charts?.inventory && (
              <Box sx={{ height: 300 }}>
                <Bar
                  data={{
                    labels: charts.inventory.labels,
                    datasets: [{
                      label: 'Current Stock',
                      data: charts.inventory.currentStock,
                      backgroundColor: '#4caf50',
                    }, {
                      label: 'Reorder Point',
                      data: charts.inventory.reorderPoint,
                      backgroundColor: '#ff9800',
                    }]
                  }}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                      x: {
                        ticks: {
                          maxRotation: 45,
                          minRotation: 45,
                        }
                      }
                    }
                  }}
                />
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          📜 Recent Activity
        </Typography>
        <Divider sx={{ mb: 2 }} />
        {activity.length > 0 ? (
          activity.slice(0, 10).map((item, index) => (
            <Box key={index} sx={{ mb: 2, pb: 2, borderBottom: index < activity.length - 1 ? 1 : 0, borderColor: 'divider' }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="subtitle2">{item.action}</Typography>
                <Chip label={item.product_id} size="small" variant="outlined" />
              </Box>
              <Typography variant="body2" color="text.secondary">
                {item.details} • {new Date(item.timestamp).toLocaleString()}
              </Typography>
            </Box>
          ))
        ) : (
          <Typography variant="body2" color="text.secondary">
            No recent activity to display
          </Typography>
        )}
      </Paper>
    </Container>
  );
};

export default Dashboard;