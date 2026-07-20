# 🗑️ Attendance Data Management System

A unified tool for managing and deleting attendance-related data from MongoDB. This system provides admin-only access to clear attendance data with proper safety measures and confirmation steps.

## 🚨 CRITICAL WARNING

**This system can permanently delete attendance data from your MongoDB database!**

- ⚠️ **Only use this in development or with proper backups**
- 🔒 **Admin role required for all operations**
- 📝 **Multiple confirmation steps are enforced**
- 🔄 **Actions cannot be undone**

## 📋 Features

### 🔍 Data Statistics
- View comprehensive statistics of all attendance-related data
- See record counts for each collection
- Check date ranges of existing data
- Real-time data overview before deletion

### 🗑️ Complete Data Deletion
- Delete ALL attendance-related data from MongoDB
- Covers 8 different collections:
  - Basic Attendance records
  - Daily Attendance records  
  - Salary Attendance data
  - Work Sessions
  - Employee Activity logs
  - Screen Captures
  - Monitoring Alerts
  - Attendance-related Feedback

### 📅 Date Range Deletion
- Delete data within specific date ranges
- Precise control over what gets deleted
- Selective cleanup options

### 🔒 Security Features
- Admin-only access control
- Multiple confirmation steps
- Confirmation codes required
- Real-time validation
- Detailed logging of operations

## 🛠️ Technical Implementation

### Backend API Endpoints

#### `GET /api/attendance-data/stats`
- **Purpose**: Get statistics of attendance data
- **Access**: Admin only
- **Response**: Record counts and date ranges

```javascript
{
  "success": true,
  "totalRecords": 15847,
  "breakdown": {
    "attendance": 5420,
    "dailyAttendance": 3210,
    "workSessions": 2890,
    "employeeActivity": 3456,
    "screenCaptures": 567,
    "monitoringAlerts": 234,
    "salaryAttendance": 45,
    "attendanceFeedback": 25
  },
  "dateRange": {
    "oldest": "2024-01-01T00:00:00.000Z",
    "newest": "2024-08-29T23:59:59.000Z"
  }
}
```

#### `DELETE /api/attendance-data/clear-all`
- **Purpose**: Delete all attendance-related data
- **Access**: Admin only
- **Required**: Confirmation code: `DELETE_ALL_ATTENDANCE_DATA`

```javascript
// Request Body
{
  "confirmationCode": "DELETE_ALL_ATTENDANCE_DATA"
}

// Response
{
  "success": true,
  "totalRecordsDeleted": 15847,
  "breakdown": {
    "attendance": 5420,
    "dailyAttendance": 3210,
    // ... other collections
  }
}
```

#### `DELETE /api/attendance-data/clear-by-date`
- **Purpose**: Delete data within date range
- **Access**: Admin only
- **Required**: Confirmation code: `DELETE_ATTENDANCE_DATA_BY_DATE`

```javascript
// Request Body
{
  "startDate": "2024-01-01",
  "endDate": "2024-01-31",
  "confirmationCode": "DELETE_ATTENDANCE_DATA_BY_DATE"
}
```

### Frontend Components

#### `AttendanceDataManagement.jsx`
- React component with modern UI
- Real-time data statistics
- Interactive confirmation dialogs
- Progress tracking
- Toast notifications

#### Navigation Integration
- Added to admin sidebar navigation
- Protected route implementation
- Role-based access control

## 🚀 Setup Instructions

### 1. Backend Setup

1. **Route Registration** (Already done)
   ```javascript
   // server/server.js
   app.use('/api/attendance-data', attendanceDataManagementRoutes);
   ```

2. **Model Dependencies** (Already configured)
   - All attendance-related models are imported
   - Proper error handling implemented

### 2. Frontend Setup

1. **Component Integration** (Already done)
   ```javascript
   // App.jsx
   import AttendanceDataManagement from "./components/admin/AttendanceDataManagement";
   
   // Route added
   <Route path="/attendance-data-management" element={<AttendanceDataManagement />} />
   ```

2. **API Integration** (Already configured)
   ```javascript
   // api.js
   const attendanceDataManagement = {
     getStats: () => fetchAPI('/attendance-data/stats'),
     clearAll: (code) => fetchAPI('/attendance-data/clear-all', { method: 'DELETE', body: JSON.stringify({ confirmationCode: code }) }),
     clearByDateRange: (start, end, code) => fetchAPI('/attendance-data/clear-by-date', { method: 'DELETE', body: JSON.stringify({ startDate: start, endDate: end, confirmationCode: code }) })
   };
   ```

### 3. Navigation Setup

Admin sidebar now includes:
```javascript
{ title: "🗑️ Data Management", href: "/attendance-data-management", icon: Database }
```

## 📱 Usage Guide

### Accessing the Tool

1. **Login as Admin**
   - Only users with `role: "Admin"` can access
   - Non-admin users see access denied page

2. **Navigate to Data Management**
   - Go to sidebar → "🗑️ Data Management"
   - Or directly visit `/attendance-data-management`

### Using the Interface

1. **View Statistics**
   - Automatically loads current data stats
   - Shows breakdown by collection
   - Displays date ranges

2. **Delete All Data**
   - Click "Delete All Attendance Data"
   - Enter confirmation code: `DELETE_ALL_ATTENDANCE_DATA`
   - Confirm deletion

3. **Delete by Date Range**
   - Select start and end dates
   - Click "Delete by Date Range"
   - Enter confirmation code: `DELETE_ATTENDANCE_DATA_BY_DATE`
   - Confirm deletion

## 🛡️ Security Measures

### Authentication & Authorization
- JWT token validation
- Admin role verification
- Route-level protection

### Confirmation System
- Multi-step confirmation process
- Unique confirmation codes required
- Real-time validation

### Logging & Monitoring
- Complete operation logging
- User tracking for deletions
- Socket.IO real-time notifications

### Error Handling
- Comprehensive error catching
- Graceful failure handling
- Detailed error messages

## 🔧 Collections Affected

### Primary Collections
1. **`attendances`** - Basic attendance records
2. **`dailyattendances`** - Enhanced daily attendance
3. **`salaryattendances`** - Salary calculation data
4. **`work_sessions`** - Work session tracking
5. **`employee_activities`** - Activity monitoring
6. **`screen_captures`** - Screenshot data
7. **`monitoring_alerts`** - System alerts
8. **`feedbacks`** - Attendance-related feedback

### Data Relationships
- Properly handles referenced data
- Maintains referential integrity where needed
- Cleans up orphaned records

## 📊 Monitoring & Reporting

### Operation Logging
```javascript
console.log(`🚨 CRITICAL: Admin ${req.user.email} is attempting to delete ALL attendance data`);
console.log(`✅ Deleted ${deletedCount} attendance records`);
console.log(`🎯 COMPLETED: Successfully deleted ${totalRecords} total records`);
```

### Real-time Updates
```javascript
// Socket.IO event for real-time notifications
req.io.emit('attendance-data:cleared', {
  adminUser: req.user.email,
  totalDeleted: totalRecordsDeleted,
  timestamp: new Date(),
  breakdown: deletionResults
});
```

## 🚨 Emergency Procedures

### If Accidental Deletion Occurs
1. **Stop the application immediately**
2. **Restore from latest backup**
3. **Check application logs for deletion details**
4. **Verify data integrity after restoration**

### Prevention Measures
1. **Always backup before using this tool**
2. **Test in development environment first**
3. **Verify confirmation codes carefully**
4. **Understand the scope of deletion**

## 📞 Support & Troubleshooting

### Common Issues

**Q: Can't access the data management page**
- A: Ensure you're logged in as an Admin user

**Q: Confirmation code not working**
- A: Copy the exact code from the interface (case-sensitive)

**Q: API returns 403 error**
- A: Check your authentication token and admin role

**Q: Some data not deleted**
- A: Check server logs for specific error messages

### Debug Mode
Enable detailed logging:
```javascript
// In server console
console.log('Debug mode enabled for attendance data deletion');
```

## 🔗 Quick Access Links

### Development Environment
- **Direct URL**: `http://localhost:5173/attendance-data-management`
- **API Base**: `http://localhost:5000/api/attendance-data`

### Static Access Page
- **HTML Page**: `attendance-data-management.html` (created for direct access)

## ⚖️ Legal & Compliance

### Data Protection
- Ensure compliance with GDPR/local data protection laws
- Document all deletion activities
- Maintain audit trails

### Backup Requirements
- Always maintain current backups
- Test backup restoration procedures
- Document retention policies

---

## 🎯 Quick Start Checklist

- [ ] Verify admin access
- [ ] Check current data statistics
- [ ] Ensure proper backups exist
- [ ] Understand confirmation codes
- [ ] Test in development first
- [ ] Document the operation
- [ ] Execute with caution

**Remember: This tool provides powerful data deletion capabilities. Use responsibly and always with proper backups!** 🛡️
