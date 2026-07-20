# Biometric Attendance & Salary Management System

## 🎯 Overview

A comprehensive system for managing employee attendance through biometric data processing and automated salary calculations. This system handles:

- **Live Attendance Tracking** - Real-time login/logout for office and WFH employees
- **Biometric Data Upload** - Process unstructured punch data from CSV/Excel files
- **Date-Range Salary Calculation** - Calculate salaries based on worked hours, overtime, and attendance
- **Interactive Dashboard** - View KPIs, detailed logs, and employee summaries
- **Export Functionality** - Export salary reports and attendance logs to Excel

---

## 🚀 Features

### 1. Live Attendance Tracking
- Record real-time punch-in/punch-out for all employees
- Support for both Office and Work-From-Home (WFH) employees
- Store comprehensive data: Employee ID, Name, Department, Date, Punch In/Out, Total Hours, Work Type

### 2. Biometric Data Upload & Processing
- Upload CSV or Excel files containing raw biometric punch data
- Automatic parsing with intelligent field mapping
- Employee matching via multiple identifiers (Employee ID, Biometric ID, Email)
- Handles unstructured data with multiple punches per day
- Groups punches and derives first/last as In/Out
- Flags incomplete records (missing punch-out)
- Calculates daily worked hours automatically
- Marks absent days where no punches exist

### 3. Date-Range Salary Calculation
- Select custom date ranges for salary calculations
- Per-employee calculations including:
  - Total worked hours
  - Present/Absent/Half-day counts
  - Overtime hours (hours beyond standard shift)
  - Regular pay and overtime pay
  - Allowances and deductions
- Support for multiple salary types:
  - **Monthly** - Pro-rated based on working days
  - **Hourly** - Direct hourly rate calculation
  - **Daily** - Daily rate with overtime calculations

### 4. Comprehensive Dashboard
**KPI Cards:**
- Total Employees
- Present Today / Absent Today
- Average Hours Today
- Estimated Payroll for Period

**Filters:**
- Department
- Employee
- Work Type (Office/WFH)
- Status (Present/Absent/Late/Leave)
- Custom Date Range

**Views:**
- Upload & Process Biometric Data
- Salary Calculation Summary
- Detailed Daily Logs
- Employee-wise Aggregated Data

### 5. Export Functionality
- Export salary reports to Excel
- Export detailed attendance logs to Excel
- Formatted with proper column widths
- Includes all calculations and summaries

---

## 📁 File Structure

### Backend (Server)

```
server/
├── models/
│   ├── BiometricPunch.js          # Individual punch records
│   ├── EmployeeMaster.js          # Employee salary configuration
│   ├── DailyAttendance.js         # Daily attendance records (existing, enhanced)
│   └── BiometricUpload.js         # Upload tracking (existing)
│
├── services/
│   ├── biometricProcessor.js      # Parse & process biometric files
│   └── attendanceSalaryService.js # Salary calculations & aggregations
│
├── routes/
│   └── biometricAttendance.js     # All API endpoints
│
└── index.js                        # Route registration
```

### Frontend (Client)

```
client/
└── src/
    └── pages/
        └── BiometricAttendanceDashboard.jsx  # Main dashboard component
```

---

## 🔧 Installation & Setup

### 1. Install Required Packages

```bash
cd server
npm install xlsx csv-parser moment multer
```

### 2. Database Models
All models are automatically created. No manual database setup required.

### 3. Server Configuration
The route is already added to `server/index.js`:

```javascript
app.use('/api/biometric-attendance', biometricAttendanceRoutes);
```

### 4. Frontend Configuration
The route is already added to `client/src/App.jsx`:

```javascript
<Route path="/biometric-attendance-dashboard" element={
  <ProtectedRoute>
    <BiometricAttendanceDashboard />
  </ProtectedRoute>
} />
```

### 5. Start the Application

**Backend:**
```bash
cd server
npm start
```

**Frontend:**
```bash
cd client
npm start
```

---

## 📊 API Endpoints

### Base URL: `/api/biometric-attendance`

#### 1. Upload Biometric Data
```http
POST /upload
Content-Type: multipart/form-data

Body: { file: <CSV or Excel file> }
```

**Expected CSV/Excel Columns:**
- `employee_id` / `emp_id` / `id`
- `biometric_id` / `card_no` / `badge_id`
- `punch_time` / `time` / `timestamp`
- `device_id` (optional)
- `location` (optional)

**Response:**
```json
{
  "success": true,
  "uploadId": "...",
  "processedRecords": 150,
  "successfulMatches": 145,
  "discrepancies": 5
}
```

#### 2. Derive Daily Attendance
```http
POST /derive-attendance
Content-Type: application/json

{
  "startDate": "2025-12-01",
  "endDate": "2025-12-06"
}
```

Groups all punches by employee and date, calculates worked hours, and creates daily attendance records.

#### 3. Calculate Salary
```http
POST /salary-calculation
Content-Type: application/json

{
  "startDate": "2025-12-01",
  "endDate": "2025-12-31",
  "userId": "optional",
  "departmentId": "optional",
  "workType": "Office|WFH|optional"
}
```

**Response:**
```json
{
  "success": true,
  "dateRange": { "start": "...", "end": "..." },
  "grandTotal": {
    "totalEmployees": 50,
    "totalPresentDays": 1250,
    "totalHours": 9800,
    "totalPayable": 250000
  },
  "employees": [...]
}
```

#### 4. Get Dashboard KPIs
```http
GET /dashboard-kpis?departmentId=...&workType=...
```

Returns today's statistics.

#### 5. Get Detailed Logs
```http
GET /detailed-logs?startDate=...&endDate=...&departmentId=...
```

Returns individual daily attendance records.

#### 6. Get Employee Aggregates
```http
GET /employee-aggregates?startDate=...&endDate=...
```

Returns summarized data per employee.

#### 7. Create/Update Employee Master
```http
POST /employee-master
Content-Type: application/json

{
  "userId": "...",
  "employeeId": "EMP001",
  "biometricId": "BIO123",
  "salaryType": "Monthly|Hourly|Daily",
  "monthlySalary": 5000,
  "hourlyRate": 25,
  "dailyRate": 200,
  "standardShiftHours": 8,
  "overtimeEnabled": true,
  "overtimeRate": 1.5,
  "allowances": { ... },
  "deductions": { ... }
}
```

#### 8. Export Salary Report
```http
GET /export-salary?startDate=...&endDate=...
```

Downloads Excel file with salary calculations.

#### 9. Export Attendance Logs
```http
GET /export-detailed-logs?startDate=...&endDate=...
```

Downloads Excel file with detailed attendance logs.

---

## 💡 Usage Guide

### Step 1: Set Up Employee Master Records

Before using the system, configure employee salary information:

```javascript
// Example API call to create employee master
const employeeData = {
  userId: "user_id_from_database",
  employeeId: "EMP001",
  biometricId: "BIO123",
  salaryType: "Monthly",
  monthlySalary: 6000,
  standardShiftHours: 8,
  overtimeEnabled: true,
  overtimeRate: 1.5,
  allowances: {
    housing: 500,
    transport: 200,
    medical: 100
  },
  deductions: {
    tax: 300,
    insurance: 100
  }
};
```

### Step 2: Upload Biometric Data

1. Go to **Upload Data** tab
2. Click **Select File** and choose your CSV/Excel file
3. Click **Upload & Process**
4. System will parse the file and match employees automatically
5. Review upload history to see results

**Sample CSV Format:**
```csv
employee_id,biometric_id,punch_time,device_id,location
EMP001,BIO123,2025-12-06 09:00:00,DEVICE1,Main Office
EMP001,BIO123,2025-12-06 18:30:00,DEVICE1,Main Office
EMP002,BIO456,2025-12-06 09:15:00,DEVICE2,Branch Office
```

### Step 3: Derive Attendance

After uploading punch data:

1. Select date range
2. Click **Derive Attendance from Punches**
3. System groups punches by employee/date
4. Calculates first punch as In, last as Out
5. Computes worked hours
6. Marks absent days

### Step 4: View Salary Calculations

1. Go to **Salary Calculation** tab
2. Select date range (e.g., start and end of month)
3. Apply filters (department, work type)
4. View grand total and per-employee breakdown
5. Export to Excel for payroll processing

### Step 5: Review Detailed Logs

1. Go to **Detailed Logs** tab
2. Filter by date, department, status
3. See punch-in/out times, hours worked, status
4. Export logs for reporting

### Step 6: View Employee Summary

1. Go to **Employee Summary** tab
2. See aggregated data: present days, hours, earnings
3. Compare employee performance
4. Export for management review

---

## 🔍 Data Processing Logic

### Biometric Punch Processing

1. **File Upload**: CSV/Excel files are uploaded and stored
2. **Parsing**: System identifies columns using flexible matching
3. **Employee Matching**: 
   - First tries Employee Master (by employeeId or biometricId)
   - Falls back to User table (by email or name)
4. **Punch Creation**: Individual punch records are created
5. **Grouping**: Punches grouped by (employee, date)
6. **Attendance Derivation**:
   - Sort punches by time
   - First punch = Punch In
   - Last punch = Punch Out (if > 30 minutes apart)
   - Calculate hours = (Punch Out - Punch In)

### Salary Calculation Logic

1. **Get Date Range**: Determine working days in range (exclude weekends)
2. **Fetch Attendance**: Get all attendance records for range
3. **Per Employee**:
   - Count present/absent/half-day/leave days
   - Sum total hours, regular hours, overtime hours
   - Calculate pay based on salary type:
     - **Monthly**: (monthlySalary / standardDays) × presentDays
     - **Hourly**: hourlyRate × regularHours + (hourlyRate × overtimeRate × overtimeHours)
     - **Daily**: dailyRate × presentDays + overtime
4. **Add Allowances**: Housing, transport, medical, etc.
5. **Subtract Deductions**: Tax, insurance, loans, etc.
6. **Total Payable** = Regular Pay + OT Pay + Allowances + Bonuses - Deductions

### Status Determination

- **Present**: Worked > 4 hours
- **Half Day**: Worked 0-4 hours
- **Late**: Punch in after 9:00 AM
- **Absent**: No punch in record
- **On Leave**: Leave record exists

### Overtime Calculation

- Standard shift = 8 hours (configurable per employee)
- Overtime = max(0, totalHours - standardShift)
- OT Pay = overtimeHours × hourlyRate × overtimeMultiplier (default 1.5x)

---

## 📋 Database Schema

### BiometricPunch
```javascript
{
  employeeId: String,
  biometricId: String,
  user: ObjectId (ref User),
  punchTime: Date,
  date: Date (date only, no time),
  punchType: 'In' | 'Out' | 'Unknown',
  deviceId: String,
  location: String,
  uploadBatch: ObjectId (ref BiometricUpload),
  isProcessed: Boolean,
  processedIntoAttendance: ObjectId (ref DailyAttendance),
  rawData: Mixed (original CSV row)
}
```

### EmployeeMaster
```javascript
{
  user: ObjectId (ref User),
  employeeId: String (unique),
  biometricId: String,
  name: String,
  department: ObjectId (ref Department),
  salaryType: 'Monthly' | 'Hourly' | 'Daily',
  monthlySalary: Number,
  hourlyRate: Number,
  dailyRate: Number,
  standardShiftHours: Number (default 8),
  standardWorkingDays: Number (default 26),
  halfDayThreshold: Number (default 4),
  overtimeEnabled: Boolean,
  overtimeRate: Number (default 1.5),
  allowances: {
    housing, transport, medical, food, other
  },
  deductions: {
    tax, insurance, providentFund, loan, other
  },
  isActive: Boolean
}
```

### DailyAttendance (Enhanced)
```javascript
{
  user: ObjectId (ref User),
  date: Date,
  biometricTimeIn: Date,
  biometricTimeOut: Date,
  biometricDeviceId: String,
  biometricLocation: String,
  totalHoursWorked: Number,
  regularHours: Number,
  overtimeHours: Number,
  status: 'Present' | 'Absent' | 'Half Day' | 'Late' | 'On Leave',
  isPresent: Boolean,
  isVerified: Boolean,
  verificationMethod: 'Biometric' | 'StartDay' | 'Both' | 'Manual',
  hasDiscrepancy: Boolean,
  discrepancyType: String,
  workLocationType: 'Office' | 'WFH',
  dailyWage: Number,
  earnedAmount: Number
}
```

---

## 🎨 Dashboard Features

### KPI Cards
- **Total Employees**: All active employees
- **Present Today**: Employees who punched in today
- **Average Hours Today**: Mean working hours for today
- **Estimated Payroll**: Total payable for selected period

### Filters
- **Date Range**: Start and End date pickers
- **Department**: Dropdown with all departments
- **Employee**: Dropdown with all employees
- **Work Type**: Office / WFH filter
- **Status**: Present / Absent / Late / Leave filter

### Tables

**Upload History:**
- File name, upload date, total records, matches, status

**Salary Details:**
- Employee, department, present/absent days, hours, regular/OT pay, total payable

**Detailed Logs:**
- Date, employee, punch in/out, hours, status, work type

**Employee Aggregates:**
- Employee, present/absent/leave days, hours, overtime, total earned

---

## 🔐 Security & Permissions

- All endpoints require authentication (`auth` middleware)
- Users can view their own data
- Admins and Managers can view all data
- File uploads are validated (CSV/Excel only, 50MB max)
- Uploaded files are stored securely in `server/uploads/biometric/`

---

## 🚨 Error Handling

The system handles various error scenarios:

1. **Missing Employee Mapping**: Unmatched employees are flagged in upload report
2. **Invalid Date Formats**: Multiple date format parsers try to interpret dates
3. **Missing Punch Out**: Records are created with flag, hours = 0
4. **Incomplete Data**: Validation errors are returned with details
5. **File Format Issues**: Clear error messages for unsupported formats

---

## 📈 Performance Optimization

- **Indexes**: Added on user, date, employeeId, biometricId for fast queries
- **Batch Processing**: Punches processed in bulk
- **Aggregation Pipelines**: Used for employee summaries
- **Pagination**: Upload history supports limit/skip
- **Caching**: KPIs can be cached on frontend

---

## 🔄 Workflow Example

### Monthly Payroll Process

1. **Day 1-31**: Employees punch in/out using biometric devices
2. **End of Month**: 
   - Export biometric data from device as CSV
   - Upload to system via dashboard
   - Click "Derive Attendance"
3. **Review**:
   - Check detailed logs for anomalies
   - Fix any discrepancies (missing punches)
4. **Calculate**:
   - Set date range to full month
   - Click calculate salary
   - Review employee summaries
5. **Export**:
   - Download salary report Excel
   - Send to payroll team
   - Download attendance logs for HR records

---

## 🛠 Troubleshooting

### Issue: Employees not matching
**Solution**: 
- Ensure Employee Master records exist
- Check employeeId matches between biometric data and system
- Add biometric IDs to Employee Master

### Issue: Hours calculation incorrect
**Solution**:
- Verify punch times are correct in uploaded data
- Check if multiple punch-in/out pairs exist (only first/last are used)
- Ensure standard shift hours configured correctly

### Issue: Salary calculations seem wrong
**Solution**:
- Verify Employee Master has correct salary type and amounts
- Check if working days calculation excludes weekends correctly
- Review allowances and deductions configuration

### Issue: File upload fails
**Solution**:
- Ensure file is CSV or Excel format
- Check file size (max 50MB)
- Verify required columns exist (employee_id, punch_time)

---

## 📞 Support

For issues or questions:
1. Check the logs in browser console
2. Review server logs for API errors
3. Verify database connections
4. Check authentication tokens

---

## 🎉 Success! System is Ready

You now have a complete biometric attendance and salary management system with:

✅ Live attendance tracking
✅ Biometric data processing
✅ Date-range salary calculations
✅ Interactive dashboard with KPIs
✅ Export functionality
✅ Comprehensive filtering options
✅ Support for Office and WFH employees
✅ Overtime calculations
✅ Multiple salary types

**Access the dashboard at:** `/biometric-attendance-dashboard`

---

## 📝 Quick Reference

### Start Date/End Date Format
```
YYYY-MM-DD (e.g., 2025-12-01)
```

### Salary Types
- **Monthly**: Fixed monthly salary, pro-rated by days
- **Hourly**: Direct hourly rate × hours worked
- **Daily**: Fixed daily rate × days present

### Work Types
- **Office**: Employee works from office
- **WFH**: Employee works from home

### Status Types
- **Present**: Worked full day (>4 hours)
- **Absent**: No attendance record
- **Half Day**: Worked 0-4 hours
- **Late**: Arrived after 9:00 AM
- **On Leave**: Approved leave

---

**Created:** December 2025
**Version:** 1.0.0
**Status:** Production Ready ✅
