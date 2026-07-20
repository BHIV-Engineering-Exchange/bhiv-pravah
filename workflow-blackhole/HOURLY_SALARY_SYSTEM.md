# Hourly-Based Salary Management System

## Overview
This system calculates employee salaries based on actual worked hours from daily attendance records. It tracks both office and remote working hours, providing comprehensive insights for payroll management.

## Key Features

### 1. **Hourly-Based Salary Calculation**
- Salaries calculated based on actual hours worked
- Supports both regular hours and overtime (1.5x rate)
- Integrates with daily attendance records (biometric + start/end day)
- Monthly salary calculations with detailed breakdowns

### 2. **Office vs Remote Hours Tracking**
- Automatically detects work location (Office, Home, Remote, Hybrid)
- Separate tracking for office hours and remote hours
- Biometric data indicates office presence
- Admin can view total office vs remote hours for each employee

### 3. **Activity Log System**
- Real-time tracking of all employees' worked hours
- Daily breakdown showing:
  - Total hours worked
  - Office hours
  - Remote hours
  - Regular vs overtime hours
  - Check-in and check-out times

### 4. **Admin Dashboard**
- Comprehensive view of all employees
- Monthly summary with:
  - Total hours worked by all employees
  - Office vs remote hours distribution
  - Salary calculations for entire workforce
  - Average attendance rates
  - Total payroll costs

## API Endpoints

### Employee Salary Endpoints

#### Calculate Monthly Salary
```
GET /api/hourly-salary/employee/:userId/calculate/:year/:month
```
**Response:**
```json
{
  "success": true,
  "data": {
    "employee": {
      "id": "user_id",
      "name": "John Doe",
      "hourlyRate": 25
    },
    "period": {
      "year": 2025,
      "month": 12,
      "monthName": "December"
    },
    "attendance": {
      "totalDays": 31,
      "presentDays": 22,
      "absentDays": 9,
      "attendanceRate": "70.97"
    },
    "hours": {
      "totalHours": 176,
      "regularHours": 168,
      "overtimeHours": 8,
      "officeHours": 120,
      "remoteHours": 56,
      "avgHoursPerDay": "8.00",
      "officePercentage": "68.18",
      "remotePercentage": "31.82"
    },
    "salary": {
      "hourlyRate": 25,
      "regularPay": 4200,
      "overtimePay": 300,
      "grossSalary": 4500,
      "allowances": 500,
      "deductions": 200,
      "netSalary": 4800
    },
    "attendanceDetails": [...]
  }
}
```

#### Get Hours Breakdown
```
GET /api/hourly-salary/employee/:userId/hours-breakdown/:year/:month
```
Returns detailed daily breakdown of office vs remote hours.

#### Get Current Month Salary
```
GET /api/hourly-salary/my-salary/current
```
Quick access to logged-in user's current month salary.

### Activity Log Endpoints

#### Get Activity Log
```
GET /api/hourly-salary/activity-log?year=2025&month=12
```
or
```
GET /api/hourly-salary/activity-log?startDate=2025-12-01&endDate=2025-12-31
```

**Response:**
```json
{
  "success": true,
  "data": {
    "summary": {
      "totalRecords": 450,
      "totalEmployees": 20,
      "totalHours": 3600,
      "totalOfficeHours": 2400,
      "totalRemoteHours": 1200,
      "presentDays": 400,
      "absentDays": 50
    },
    "activityLog": [
      {
        "userId": "user_id",
        "userName": "John Doe",
        "employeeId": "EMP001",
        "date": "2025-12-09",
        "totalHoursWorked": 8.5,
        "officeHours": 8.5,
        "remoteHours": 0,
        "overtimeHours": 0.5,
        "workLocationType": "Office",
        "checkIn": "2025-12-09T09:00:00Z",
        "checkOut": "2025-12-09T17:30:00Z"
      }
    ]
  }
}
```

#### Get Current Month Activity Log
```
GET /api/hourly-salary/activity-log/current
```

### Admin Dashboard Endpoints

#### Get Admin Dashboard
```
GET /api/hourly-salary/admin/dashboard/:year/:month
```

**Response:**
```json
{
  "success": true,
  "data": {
    "period": {
      "year": 2025,
      "month": 12,
      "monthName": "December"
    },
    "overallStats": {
      "totalEmployees": 20,
      "totalHoursWorked": 3600,
      "totalOfficeHours": 2400,
      "totalRemoteHours": 1200,
      "totalOvertimeHours": 100,
      "totalGrossSalary": 90000,
      "totalNetSalary": 85000,
      "avgAttendanceRate": "85.50",
      "avgHoursPerEmployee": "180.00"
    },
    "employees": [
      {
        "userId": "user_id",
        "name": "John Doe",
        "hourlyRate": 25,
        "hours": {
          "totalHours": 180,
          "officeHours": 120,
          "remoteHours": 60,
          "overtimeHours": 10
        },
        "salary": {
          "grossSalary": 4625,
          "netSalary": 4400
        }
      }
    ]
  }
}
```

#### Get Current Month Dashboard
```
GET /api/hourly-salary/admin/dashboard/current
```

### Management Endpoints

#### Update Work Location Type
```
PATCH /api/hourly-salary/attendance/:attendanceId/location
```
**Body:**
```json
{
  "workLocationType": "Office" | "Home" | "Remote" | "Hybrid"
}
```

#### Bulk Update Hourly Rates
```
POST /api/hourly-salary/admin/hourly-rates/bulk-update
```
**Body:**
```json
{
  "updates": [
    { "userId": "user_id_1", "hourlyRate": 30 },
    { "userId": "user_id_2", "hourlyRate": 35 }
  ]
}
```

## Data Models

### DailyAttendance (Enhanced)
```javascript
{
  user: ObjectId,
  date: Date,
  
  // Time tracking
  biometricTimeIn: Date,
  biometricTimeOut: Date,
  startDayTime: Date,
  endDayTime: Date,
  
  // Hours calculation
  totalHoursWorked: Number,
  regularHours: Number,
  overtimeHours: Number,
  officeHours: Number,      // NEW
  remoteHours: Number,      // NEW
  
  // Work location
  workLocationType: String, // 'Office', 'Home', 'Remote', 'Hybrid'
  
  // Salary
  dailyWage: Number,
  earnedAmount: Number
}
```

### User Model (Salary Fields)
```javascript
{
  name: String,
  email: String,
  employeeId: String,
  hourlyRate: Number,  // Hourly rate in USD
  department: ObjectId
}
```

## Salary Calculation Logic

### Regular Hours
- First 8 hours per day = regular rate
- Formula: `regularHours * hourlyRate`

### Overtime Hours
- Hours beyond 8 per day = overtime rate (1.5x)
- Formula: `overtimeHours * hourlyRate * 1.5`

### Work Location Detection
1. **Office**: Biometric data present
2. **Home/Remote**: No biometric data, only start/end day
3. **Hybrid**: Both biometric and start/end day data
   - Office hours = biometric time range
   - Remote hours = total hours - office hours

### Monthly Salary
```
regularPay = regularHours * hourlyRate
overtimePay = overtimeHours * hourlyRate * 1.5
grossSalary = regularPay + overtimePay
netSalary = grossSalary + allowances - deductions
```

## Usage Examples

### For Employees
```javascript
// Check my current month salary
fetch('/api/hourly-salary/my-salary/current', {
  headers: { 'x-auth-token': token }
})
```

### For Managers
```javascript
// Check team member's salary for December 2025
fetch('/api/hourly-salary/employee/USER_ID/calculate/2025/12', {
  headers: { 'x-auth-token': token }
})

// View activity log
fetch('/api/hourly-salary/activity-log?year=2025&month=12', {
  headers: { 'x-auth-token': token }
})
```

### For Admins
```javascript
// View dashboard for all employees
fetch('/api/hourly-salary/admin/dashboard/2025/12', {
  headers: { 'x-auth-token': token }
})

// Update hourly rates
fetch('/api/hourly-salary/admin/hourly-rates/bulk-update', {
  method: 'POST',
  headers: { 
    'Content-Type': 'application/json',
    'x-auth-token': token 
  },
  body: JSON.stringify({
    updates: [
      { userId: 'user1', hourlyRate: 30 },
      { userId: 'user2', hourlyRate: 35 }
    ]
  })
})
```

## Integration with Existing Systems

### Biometric Upload
When biometric data is uploaded:
1. Creates/updates DailyAttendance records
2. Sets `biometricTimeIn` and `biometricTimeOut`
3. Automatically sets `workLocationType` to 'Office'
4. Calculates `officeHours` based on biometric data

### Start/End Day
When employee starts/ends day via app:
1. Updates DailyAttendance record
2. Sets `startDayTime` and `endDayTime`
3. If no biometric data, sets `workLocationType` to 'Home'/'Remote'
4. Calculates `remoteHours` based on start/end day data

### Hybrid Work
When both biometric and app data exist:
1. `workLocationType` = 'Hybrid'
2. `officeHours` = hours from biometric data
3. `remoteHours` = total hours - office hours

## Authentication & Authorization

All endpoints require authentication via `x-auth-token` header.

Admin-only endpoints:
- `/admin/dashboard/:year/:month`
- `/admin/hourly-rates/bulk-update`

## Error Handling

All endpoints return consistent error format:
```json
{
  "success": false,
  "message": "Error message",
  "error": "Detailed error description"
}
```

## Performance Considerations

- All date range queries use indexed fields
- Aggregation pipelines optimized for large datasets
- Results cached in SalaryAttendance collection for historical records
- Supports pagination for large result sets (can be added)

## Future Enhancements

1. **Export Features**
   - Export salary reports to Excel/PDF
   - Bulk payslip generation

2. **Advanced Analytics**
   - Productivity metrics based on hours
   - Department-wise comparisons
   - Trend analysis

3. **Approval Workflow**
   - Manager approval for overtime
   - Exception handling for discrepancies

4. **Notifications**
   - Alert employees about salary calculations
   - Notify admins of unusual patterns

## Testing

All endpoints can be tested using the provided routes. Recommended test flow:

1. Upload biometric data or create attendance records
2. Calculate employee salary
3. View activity log
4. Check admin dashboard
5. Update work location types as needed
6. Verify calculations

## Support

For issues or questions, contact the development team or refer to the API documentation.
