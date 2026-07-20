import React, { useState, useRef, useEffect } from 'react';
import {
  Container, Card, CardContent, Typography, Box,
  Button, Alert, Switch, FormControlLabel, Dialog,
  DialogTitle, DialogContent, DialogActions, Paper,
  Grid, Chip, List, ListItem, ListItemText, Divider,
  useMediaQuery, useTheme, CircularProgress
} from '@mui/material';
import {
  Camera, CheckCircle, AccessTime, PrivacyTip,
  Face, Warning
} from '@mui/icons-material';
import { attendanceAPI } from '../services/api';

const AttendanceSystem = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [employeeId, setEmployeeId] = useState(localStorage.getItem('employeeId') || '');
  const [privacyOptIn, setPrivacyOptIn] = useState(false);
  const [isCheckedIn, setIsCheckedIn] = useState(false);
  const [attendanceHistory, setAttendanceHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [cameraActive, setCameraActive] = useState(false);
  const [privacyDialog, setPrivacyDialog] = useState(false);

  useEffect(() => {
    if (employeeId) {
      loadAttendanceData();
    }
  }, [employeeId]);

  const loadAttendanceData = async () => {
    try {
      const response = await attendanceAPI.getAttendanceRecords(employeeId);
      setAttendanceHistory(response.data);
      // Check if already checked in today
      const today = new Date().toDateString();
      const todayRecord = response.data.find(record =>
        new Date(record.date).toDateString() === today && !record.check_out
      );
      setIsCheckedIn(!!todayRecord);
    } catch (error) {
      console.error('Error loading attendance data:', error);
    }
  };

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 }
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      setCameraActive(true);
    } catch (error) {
      console.error('Error accessing camera:', error);
      setMessage('Error accessing camera. Please check permissions.');
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    setCameraActive(false);
  };

  const captureImage = () => {
    if (!videoRef.current || !canvasRef.current) return null;

    const canvas = canvasRef.current;
    const video = videoRef.current;
    const context = canvas.getContext('2d');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0);

    return canvas.toDataURL('image/jpeg', 0.8);
  };

  const handleAttendance = async (action) => {
    if (!privacyOptIn) {
      setPrivacyDialog(true);
      return;
    }

    if (!employeeId) {
      setMessage('Please enter your Employee ID');
      return;
    }

    setLoading(true);
    try {
      const imageData = captureImage();
      const data = {
        employee_id: employeeId,
        action: action,
        image_data: imageData,
        timestamp: new Date().toISOString()
      };

      if (action === 'checkin') {
        await attendanceAPI.checkIn(data);
        setIsCheckedIn(true);
        setMessage('Successfully checked in!');
      } else {
        await attendanceAPI.checkOut(data);
        setIsCheckedIn(false);
        setMessage('Successfully checked out!');
      }

      // Refresh attendance history
      await loadAttendanceData();
    } catch (error) {
      console.error('Error processing attendance:', error);
      setMessage('Error processing attendance. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePrivacyUpdate = async () => {
    try {
      await attendanceAPI.updatePrivacySettings(employeeId, {
        facial_recognition_opt_in: privacyOptIn
      });
      setPrivacyDialog(false);
    } catch (error) {
      console.error('Error updating privacy settings:', error);
      setMessage('Error updating privacy settings');
    }
  };

  const handleEmployeeIdChange = (e) => {
    const id = e.target.value;
    setEmployeeId(id);
    localStorage.setItem('employeeId', id);
  };

  if (!employeeId) {
    return (
      <Container maxWidth="sm" sx={{ mt: 4 }}>
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <AccessTime sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
            <Typography variant="h5" gutterBottom>
              Attendance System
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
              Enter your Employee ID to access the attendance system
            </Typography>
            <input
              type="text"
              placeholder="Employee ID"
              value={employeeId}
              onChange={handleEmployeeIdChange}
              style={{
                width: '100%',
                padding: '12px',
                fontSize: '16px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                marginBottom: '16px'
              }}
            />
            <Button
              variant="contained"
              size="large"
              onClick={loadAttendanceData}
              disabled={!employeeId}
            >
              Access System
            </Button>
          </CardContent>
        </Card>
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
          🕒 Attendance System - {employeeId}
        </Typography>
        <Button
          variant="outlined"
          onClick={() => setEmployeeId('')}
          size={isMobile ? 'small' : 'medium'}
        >
          Switch Employee
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* Camera and Check-in/out Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <Face sx={{ mr: 1 }} />
                Facial Recognition Attendance
              </Typography>

              {/* Privacy Settings */}
              <Box sx={{ mb: 3 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={privacyOptIn}
                      onChange={(e) => setPrivacyOptIn(e.target.checked)}
                      color="primary"
                    />
                  }
                  label={
                    <Box>
                      <Typography variant="body2">Opt-in to Facial Recognition</Typography>
                      <Typography variant="caption" color="text.secondary">
                        Required for biometric attendance
                      </Typography>
                    </Box>
                  }
                />
                <Button
                  size="small"
                  startIcon={<PrivacyTip />}
                  onClick={() => setPrivacyDialog(true)}
                  sx={{ ml: 2 }}
                >
                  Privacy Policy
                </Button>
              </Box>

              {/* Camera Section */}
              <Box sx={{ mb: 3 }}>
                {!cameraActive ? (
                  <Button
                    variant="contained"
                    startIcon={<Camera />}
                    onClick={startCamera}
                    fullWidth
                    disabled={!privacyOptIn}
                  >
                    Start Camera
                  </Button>
                ) : (
                  <Box>
                    <video
                      ref={videoRef}
                      autoPlay
                      playsInline
                      style={{
                        width: '100%',
                        maxHeight: '300px',
                        border: '1px solid #ccc',
                        borderRadius: '4px'
                      }}
                    />
                    <Button
                      variant="outlined"
                      onClick={stopCamera}
                      sx={{ mt: 1 }}
                      fullWidth
                    >
                      Stop Camera
                    </Button>
                  </Box>
                )}
              </Box>

              {/* Check-in/out Buttons */}
              <Box display="flex" gap={2}>
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<CheckCircle />}
                  onClick={() => handleAttendance('checkin')}
                  disabled={!cameraActive || isCheckedIn || loading}
                  fullWidth
                >
                  {loading ? <CircularProgress size={20} /> : 'Check In'}
                </Button>
                <Button
                  variant="contained"
                  color="error"
                  startIcon={<CheckCircle />}
                  onClick={() => handleAttendance('checkout')}
                  disabled={!cameraActive || !isCheckedIn || loading}
                  fullWidth
                >
                  {loading ? <CircularProgress size={20} /> : 'Check Out'}
                </Button>
              </Box>

              <canvas ref={canvasRef} style={{ display: 'none' }} />
            </CardContent>
          </Card>
        </Grid>

        {/* Attendance History */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📊 Attendance History
              </Typography>
              <Divider sx={{ mb: 2 }} />

              {attendanceHistory.length > 0 ? (
                <List>
                  {attendanceHistory.slice(0, 10).map((record, index) => (
                    <ListItem key={index} divider={index < attendanceHistory.length - 1}>
                      <ListItemText
                        primary={
                          <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Typography variant="subtitle2">
                              {new Date(record.date).toLocaleDateString()}
                            </Typography>
                            <Chip
                              label={record.status}
                              color={record.status === 'present' ? 'success' : 'warning'}
                              size="small"
                            />
                          </Box>
                        }
                        secondary={
                          <Typography variant="body2" color="text.secondary">
                            Check-in: {record.check_in || 'N/A'} •
                            Check-out: {record.check_out || 'N/A'} •
                            Hours: {record.hours_worked || 'N/A'}
                          </Typography>
                        }
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
                  No attendance records found
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Privacy Policy Dialog */}
      <Dialog open={privacyDialog} onClose={() => setPrivacyDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ display: 'flex', alignItems: 'center' }}>
          <PrivacyTip sx={{ mr: 1 }} />
          Facial Recognition Privacy Policy
        </DialogTitle>
        <DialogContent>
          <Typography variant="h6" gutterBottom>
            Data Collection and Usage
          </Typography>
          <Typography variant="body2" paragraph>
            Facial recognition data is used solely for attendance tracking and verification purposes.
            Images are processed in real-time and not stored permanently on our servers.
          </Typography>

          <Typography variant="h6" gutterBottom>
            Privacy Rights
          </Typography>
          <Typography variant="body2" paragraph>
            You have the right to opt-out of facial recognition at any time. Your decision will not
            affect your employment status or access to other system features.
          </Typography>

          <Typography variant="h6" gutterBottom>
            Data Security
          </Typography>
          <Typography variant="body2" paragraph>
            All biometric data is encrypted and processed securely. Access is restricted to authorized
            personnel only, and data retention follows our privacy policy guidelines.
          </Typography>

          <Alert severity="warning" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>Important:</strong> Facial recognition requires camera access. Please ensure
              your device has proper lighting and clear visibility of your face.
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPrivacyDialog(false)}>Cancel</Button>
          <Button
            onClick={handlePrivacyUpdate}
            variant="contained"
            disabled={!privacyOptIn}
          >
            I Agree & Opt-in
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default AttendanceSystem;