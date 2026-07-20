# 🚀 Employee Monitoring System - DEMO & USAGE GUIDE

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Features](#features)
3. [Setup Instructions](#setup-instructions)
4. [API Endpoints](#api-endpoints)
5. [Frontend Integration](#frontend-integration)
6. [Dashboard Access](#dashboard-access)

## System Overview
The Employee Monitoring System (EMS) tracks real-time employee activity through browser events to measure actual work engagement vs. pretend work. The system operates with privacy-conscious tracking that focuses on behavioral patterns rather than content.

## Features

### Real-Time Activity Tracking
- **Mouse Movement Tracking** 🖱️
  - Captures mouse movements, clicks, and cursor patterns
  - Measures engagement through movement frequency
  - Detects periods of inactivity

- **Keystroke Analysis** ⌨️
  - Tracks typing activity and rhythm
  - Measures productivity through keystroke rate
  - Preserves privacy (no actual content captured)

- **Idle Time Detection** ⏳
  - Monitors periods of inactivity
  - Configurable thresholds (default: 2 minutes)
  - Generates alerts for extended idle periods

- **Window Focus Monitoring** 👁️
  - Tracks when browser/app is active/inactive
  - Detects tab switching and application changes
  - Identifies when employee is distracted

- **Content Interaction** 📄
  - Monitors scroll depth and patterns
  - Tracks content engagement
  - Measures time spent on different sections

### Advanced Features
- **Behavioral Analysis** - Identifies work patterns and anomalies
- **Productivity Scoring** - 0-100 scale measuring actual work
- **Risk Assessment** - Flags potential issues automatically
- **Real-Time Dashboard** - Live monitoring of employee status

## Setup Instructions

### Prerequisites
- Node.js (v14 or higher)
- MongoDB (running locally or remote)
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Server Setup
1. Navigate to server directory:
   ```bash
   cd server
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure environment variables in `.env`:
   ```env
   MONGODB_URI=mongodb://localhost:27017/employee-monitoring
   JWT_SECRET=your-jwt-secret-key
   # Add other required variables...
   ```

4. Start the server:
   ```bash
   npm run dev
   ```

### Client Setup
1. Navigate to client directory:
   ```bash
   cd client
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the client:
   ```bash
   npm run dev
   ```

## API Endpoints

### EMS Signal Collection Endpoints
```
POST   /api/ems-signals/signals/init     # Initialize tracking for employee
POST   /api/ems-signals/signals         # Send batch of activity signals  
POST   /api/ems-signals/signals/realtime # Send individual real-time signal
GET    /api/ems-signals/signals/:id     # Get current signal state
GET    /api/ems-signals/signals/:id/history # Get signal history
GET    /api/ems-signals/signals/:id/proof   # Get live capture proof
POST   /api/ems-signals/signals/:id/stop    # Stop tracking
DELETE /api/ems-signals/signals/:id         # Clear signals
```

### Signal Types
- `window_focus` - Browser window active state
- `keystroke_rate` - Typing activity measurement
- `mouse_movement` - Mouse engagement tracking
- `scroll_depth` - Content interaction
- `task_tab_active` - Work-related tab status
- `idle_time` - Inactivity detection
- `app_switch` - Application switching
- `browser_hidden` - Visibility status

## Frontend Integration

### Automatic Initialization
The EMS collector automatically starts when:
- Employee ID is found in `localStorage` or `sessionStorage`
- User navigates to monitored pages
- Authentication token is present

### Manual Initialization
```javascript
// Initialize with custom config
const collector = new EMSSignalCollector({
  employeeId: 'emp_12345',
  sessionId: 'session_abcde',
  apiEndpoint: '/api/ems-signals',
  batchInterval: 10000, // Send every 10 seconds
  debug: true
});

// Get live capture proof
window.getEMSProof = () => collector.getLiveCaptureProof();
```

### Browser Events Tracked
- `keydown` - Keystroke detection
- `mousemove` - Mouse movement tracking
- `click` - Mouse click events
- `scroll` - Scroll depth and direction
- `focus`/`blur` - Window focus changes
- `visibilitychange` - Browser visibility

## Dashboard Access

### Monitoring Dashboard
- URL: `/monitoring`
- Access: Admin users only
- Features:
  - Real-time employee status
  - Activity charts and trends
  - Screenshot gallery
  - Alert management
  - Productivity reports
  - AI insights

### Data Views
- **Dashboard**: Overall monitoring summary
- **Activity**: Detailed activity charts
- **Screenshots**: Captured screen images
- **Alerts**: Active monitoring alerts
- **AI Insights**: Automated behavior analysis
- **Production**: Productivity metrics
- **Reports**: Generated reports
- **Whitelist**: Approved websites
- **Bulk**: Mass monitoring controls

## Privacy & Compliance

### Data Protection
- No actual keystroke content stored
- Aggregated behavioral data only
- Encrypted data transmission
- Compliant with privacy regulations

### Opt-in Policy
- Explicit consent required
- Transparent tracking indicators
- Employee access to their own data
- Clear data retention policies

## Troubleshooting

### Common Issues
1. **Signals not being captured**
   - Verify employee ID is in localStorage
   - Check network connectivity
   - Confirm server endpoints are accessible

2. **Dashboard not showing data**
   - Ensure monitoring is started for the employee
   - Refresh the dashboard page
   - Check server logs for errors

3. **Performance concerns**
   - Adjust batch intervals as needed
   - Monitor server resource usage
   - Consider scaling for large teams

## Security Considerations

- Secure API endpoints with authentication
- Validate all incoming signal data
- Implement rate limiting
- Regular security audits
- Employee consent management
- Data encryption in transit and at rest

---

## 🎉 System Status: READY FOR PRODUCTION
The Employee Monitoring System is fully operational and ready to track mouse movements, keystrokes, idle time, and all other required activities in real-time!