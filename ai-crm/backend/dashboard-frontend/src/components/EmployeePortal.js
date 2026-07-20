import React, { useState, useEffect } from 'react';
import {
  Container, Grid, Card, CardContent, Typography, Box,
  Button, TextField, Dialog, DialogTitle, DialogContent,
  DialogActions, Alert, Chip, Paper, Divider, List,
  ListItem, ListItemText, useMediaQuery, useTheme, CircularProgress
} from '@mui/material';
import {
  Person, Assessment, RateReview, Timeline,
  Send, CheckCircle, Pending
} from '@mui/icons-material';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { employeeAPI } from '../services/api';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const EmployeePortal = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [employeeId, setEmployeeId] = useState(localStorage.getItem('employeeId') || '');
  const [metrics, setMetrics] = useState(null);
  const [attendance, setAttendance] = useState([]);
  const [reviewDialog, setReviewDialog] = useState(false);
  const [reviewData, setReviewData] = useState({ type: '', comments: '' });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (employeeId) {
      loadEmployeeData();
    }
  }, [employeeId]);

  const loadEmployeeData = async () => {
    setLoading(true);
    try {
      const [metricsRes, attendanceRes] = await Promise.all([
        employeeAPI.getPersonalMetrics(employeeId),
        employeeAPI.getAttendanceHistory(employeeId)
      ]);

      setMetrics(metricsRes.data);
      setAttendance(attendanceRes.data);
    } catch (error) {
      console.error('Error loading employee data:', error);
      setMessage('Error loading employee data');
    } finally {
      setLoading(false);
    }
  };

  const handleEmployeeIdChange = (e) => {
    const id = e.target.value;
    setEmployeeId(id);
    localStorage.setItem('employeeId', id);
  };

  const handleReviewSubmit = async () => {
    try {
      await employeeAPI.requestReview(employeeId, reviewData);
      setMessage('Review request submitted successfully');
      setReviewDialog(false);
      setReviewData({ type: '', comments: '' });
    } catch (error) {
      console.error('Error submitting review request:', error);
      setMessage('Error submitting review request');
    }
  };

  if (!employeeId) {
    return (
      <Container maxWidth="sm" sx={{ mt: 4 }}>
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <Person sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
            <Typography variant="h5" gutterBottom>
              Employee Portal
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Enter your Employee ID to access your personal dashboard
            </Typography>
            <TextField
              fullWidth
              label="Employee ID"
              value={employeeId}
              onChange={handleEmployeeIdChange}
              sx={{ mb: 2 }}
            />
            <Button
              variant="contained"
              size="large"
              onClick={loadEmployeeData}
              disabled={!employeeId}
            >
              Access Portal
            </Button>
          </CardContent>
        </Card>
      </Container>
    );
  }

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 2, mb: 4 }}>
      {message && (
        <Alert severity={message.includes('Error') ? 'error' : 'success'} sx={{ mb: 2 }}>
          {message}
        </Alert>
      )}

      <Box display="flex" justifyContent="space-between" alignItems="center" sx={{ mb: 3 }}>
        <Typography variant="h4">
          👤 Employee Portal - {employeeId}
        </Typography>
        <Button
          variant="outlined"
          onClick={() => setEmployeeId('')}
          size={isMobile ? 'small' : 'medium'}
        >
          Switch Employee
        </Button>
      </Box>

      {/* Personal Metrics */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Assessment color="primary" sx={{ mr: 1 }} />
                <Typography variant="h6">Performance Score</Typography>
              </Box>
              <Typography variant="h3" color="primary">
                {metrics?.performance_score || 0}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Based on last 30 days
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Timeline color="secondary" sx={{ mr: 1 }} />
                <Typography variant="h6">Tasks Completed</Typography>
              </Box>
              <Typography variant="h3" color="secondary">
                {metrics?.tasks_completed || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                This month
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <RateReview sx={{ mr: 1, color: '#ff9800' }} />
                <Typography variant="h6">Pending Reviews</Typography>
              </Box>
              <Typography variant="h3" sx={{ color: '#ff9800' }}>
                {metrics?.pending_reviews || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Awaiting approval
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Performance Chart */}
      {metrics?.performance_history && (
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            📈 Performance Trend (Last 30 Days)
          </Typography>
          <Box sx={{ height: 300 }}>
            <Line
              data={{
                labels: metrics.performance_history.map(item => item.date),
                datasets: [{
                  label: 'Performance Score',
                  data: metrics.performance_history.map(item => item.score),
                  borderColor: '#1f77b4',
                  backgroundColor: 'rgba(31, 119, 180, 0.1)',
                  tension: 0.4,
                }]
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                  y: {
                    beginAtZero: true,
                    max: 100,
                  }
                }
              }}
            />
          </Box>
        </Paper>
      )}

      {/* Review Request Section */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📝 Request Performance Review
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Submit a request for performance review or feedback
              </Typography>
              <Button
                variant="contained"
                startIcon={<RateReview />}
                onClick={() => setReviewDialog(true)}
                fullWidth
              >
                Request Review
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📊 Recent Achievements
              </Typography>
              <List dense>
                {metrics?.achievements?.slice(0, 3).map((achievement, index) => (
                  <ListItem key={index}>
                    <CheckCircle color="success" sx={{ mr: 1 }} />
                    <ListItemText
                      primary={achievement.title}
                      secondary={achievement.date}
                    />
                  </ListItem>
                )) || (
                  <ListItem>
                    <ListItemText primary="No recent achievements" />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Attendance History */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          🕒 Recent Attendance
        </Typography>
        <Divider sx={{ mb: 2 }} />
        {attendance.length > 0 ? (
          attendance.slice(0, 10).map((record, index) => (
            <Box key={index} sx={{ mb: 2, pb: 2, borderBottom: index < attendance.length - 1 ? 1 : 0, borderColor: 'divider' }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                <Typography variant="subtitle2">
                  {new Date(record.date).toLocaleDateString()}
                </Typography>
                <Chip
                  label={record.status}
                  color={record.status === 'present' ? 'success' : 'warning'}
                  size="small"
                />
              </Box>
              <Typography variant="body2" color="text.secondary">
                Check-in: {record.check_in || 'N/A'} • Check-out: {record.check_out || 'N/A'}
              </Typography>
            </Box>
          ))
        ) : (
          <Typography variant="body2" color="text.secondary">
            No attendance records found
          </Typography>
        )}
      </Paper>

      {/* Review Request Dialog */}
      <Dialog open={reviewDialog} onClose={() => setReviewDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Request Performance Review</DialogTitle>
        <DialogContent>
          <TextField
            select
            fullWidth
            label="Review Type"
            value={reviewData.type}
            onChange={(e) => setReviewData({ ...reviewData, type: e.target.value })}
            sx={{ mb: 2, mt: 1 }}
            SelectProps={{ native: true }}
          >
            <option value="">Select type</option>
            <option value="mid_year">Mid-Year Review</option>
            <option value="annual">Annual Review</option>
            <option value="feedback">General Feedback</option>
            <option value="promotion">Promotion Review</option>
          </TextField>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Comments (Optional)"
            value={reviewData.comments}
            onChange={(e) => setReviewData({ ...reviewData, comments: e.target.value })}
            placeholder="Any specific areas you'd like to discuss..."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReviewDialog(false)}>Cancel</Button>
          <Button
            onClick={handleReviewSubmit}
            variant="contained"
            startIcon={<Send />}
            disabled={!reviewData.type}
          >
            Submit Request
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default EmployeePortal;