# Location Map & Discrepancy Detection Implementation

## Overview
This implementation adds an interactive map to the live attendance section and automatically detects location discrepancies when employees start and end their day at significantly different locations.

## Features Implemented

### 1. Interactive Map in Live Attendance
- **Technology**: React Leaflet (OpenStreetMap)
- **Location**: `client/src/components/attendance/LiveAttendanceMap.jsx`
- **Features**:
  - Real-time interactive map showing employee locations
  - Office location marker with radius circle (2km)
  - Employee markers with status colors (green=present, yellow=late, red=absent)
  - Click markers to see employee details
  - Distance calculation from office
  - Visual indicators for employees within office radius

### 2. Location Detection at Start Day
- **Endpoint**: `POST /api/attendance/start-day/:userId`
- **Location**: `server/routes/attendance.js`
- **Features**:
  - Captures GPS coordinates (latitude, longitude)
  - Validates location (office radius check or WFH option)
  - Stores location with address and accuracy
  - Required for starting the day

### 3. Location Detection at End Day
- **Endpoint**: `POST /api/attendance/end-day/:userId`
- **Location**: `server/routes/attendance.js`
- **Features**:
  - Captures GPS coordinates when ending day
  - Calculates distance between start and end locations
  - Automatically creates discrepancy record if distance > threshold (default: 5km)
  - Creates admin alert for review

### 4. Location Discrepancy Model
- **File**: `server/models/LocationDiscrepancy.js`
- **Features**:
  - Tracks start and end locations
  - Calculates distance in meters and kilometers
  - Severity levels: low, medium, high, critical
  - Status tracking: pending, reviewed, resolved, dismissed
  - Automatic severity determination based on distance

### 5. Admin Alert System
- **Integration**: Uses existing `MonitoringAlert` model
- **Alert Type**: `location_discrepancy` (added to enum)
- **Features**:
  - Automatic alert creation when discrepancy detected
  - Real-time socket.io notification to admins
  - Severity-based alert levels
  - Includes location details and distance information

### 6. API Endpoints

#### Get Location Discrepancies
```
GET /api/attendance/location-discrepancies
Query Parameters:
  - status: pending|reviewed|resolved|dismissed
  - severity: low|medium|high|critical
  - startDate: YYYY-MM-DD
  - endDate: YYYY-MM-DD
  - limit: number (default: 50)
```

#### Update Discrepancy Status
```
PUT /api/attendance/location-discrepancies/:id
Body:
  - status: pending|reviewed|resolved|dismissed
  - resolutionNotes: string
```

### 7. Frontend Location Discrepancy Display
- **Component**: `LiveAttendanceMap.jsx`
- **Features**:
  - Alert button showing count of pending discrepancies
  - Expandable list of location discrepancies
  - Shows employee name, distance, severity
  - Displays start and end location addresses
  - Color-coded by severity (red=critical, orange=high, yellow=medium)

## Configuration

### Environment Variables
```env
# Location discrepancy threshold (in meters)
LOCATION_DISCREPANCY_THRESHOLD=5000  # Default: 5km

# Office location
OFFICE_LAT=19.1663
OFFICE_LNG=72.8526
OFFICE_RADIUS=2000  # 2km radius for office validation
```

### Severity Levels
- **Critical**: Distance ≥ 15km (3x threshold)
- **High**: Distance ≥ 10km (2x threshold)
- **Medium**: Distance ≥ 5km (1x threshold)
- **Low**: Distance < 5km (below threshold, but still tracked)

## How It Works

### Start Day Flow
1. Employee clicks "Start Day" button
2. Browser requests GPS location
3. Location is validated (office radius or WFH)
4. Start location is saved to attendance record
5. Employee can begin work

### End Day Flow
1. Employee clicks "End Day" button
2. Browser requests GPS location
3. End location is saved to attendance record
4. System calculates distance between start and end locations
5. If distance > threshold:
   - Creates `LocationDiscrepancy` record
   - Creates `MonitoringAlert` for admin
   - Emits socket.io event for real-time notification
6. Attendance record is updated with end time and hours worked

### Admin Review Flow
1. Admin sees alert notification in dashboard
2. Admin navigates to Live Attendance → Location Map tab
3. Admin clicks "Location Alerts" button
4. Admin reviews list of discrepancies
5. Admin can update status (reviewed/resolved) with notes

## Map Features

### Visual Elements
- **Red Marker**: Office location (centered)
- **Blue Circle**: Office radius (2km)
- **Green Markers**: Employees present and within office radius
- **Yellow Markers**: Late employees
- **Red Markers**: Absent employees
- **Green Dot**: Indicator for employees within office radius

### Interactive Features
- Click employee marker to see popup with details
- Click employee in list to highlight on map
- Hover over markers for quick info
- Zoom and pan to explore locations
- Office radius circle shows valid work area

## Data Flow

```
Start Day
  ↓
GPS Location Captured
  ↓
Saved to Attendance.startDayLocation
  ↓
End Day
  ↓
GPS Location Captured
  ↓
Saved to Attendance.endDayLocation
  ↓
Distance Calculated
  ↓
If Distance > Threshold:
  ├─ LocationDiscrepancy Created
  ├─ MonitoringAlert Created
  └─ Socket.io Event Emitted
  ↓
Admin Notified
  ↓
Admin Reviews in Dashboard
```

## Files Modified/Created

### Created Files
1. `server/models/LocationDiscrepancy.js` - New model for tracking discrepancies
2. `LOCATION_MAP_IMPLEMENTATION.md` - This documentation

### Modified Files
1. `server/routes/attendance.js`
   - Added location discrepancy detection in end-day endpoint
   - Added location discrepancy API endpoints
   
2. `server/models/MonitoringAlert.js`
   - Added `location_discrepancy` to alert_type enum

3. `client/src/components/attendance/LiveAttendanceMap.jsx`
   - Complete rewrite with interactive Leaflet map
   - Added location discrepancy alert display
   - Enhanced UI with real map visualization

### Dependencies Added
- `react-leaflet@4.2.1` - React wrapper for Leaflet maps
- `leaflet` - Interactive map library

## Testing

### Test Scenarios
1. **Normal Day**: Start and end at same location → No discrepancy
2. **Office to Home**: Start at office, end at home (>5km) → Discrepancy created
3. **Far Distance**: Start and end >15km apart → Critical severity alert
4. **Admin Review**: Admin can view and resolve discrepancies

### Manual Testing Steps
1. Start day at office location
2. End day at different location (>5km away)
3. Check admin dashboard for alert
4. Navigate to Live Attendance → Location Map
5. Click "Location Alerts" button
6. Verify discrepancy appears in list
7. Review and update status

## Future Enhancements

1. **Geofencing**: Automatic detection when employee leaves office area during work
2. **Route Tracking**: Show path between start and end locations
3. **Historical Analysis**: Track location patterns over time
4. **Mobile App**: Native GPS tracking for better accuracy
5. **Batch Processing**: Process multiple discrepancies at once
6. **Export Reports**: Generate CSV/PDF reports of location discrepancies
7. **Custom Thresholds**: Per-employee or per-department thresholds

## Notes

- Map uses OpenStreetMap tiles (free, no API key required)
- Location accuracy depends on device GPS quality
- WFH employees may have larger discrepancies (expected)
- Admin can configure threshold per organization needs
- All location data is stored securely and only accessible to admins

