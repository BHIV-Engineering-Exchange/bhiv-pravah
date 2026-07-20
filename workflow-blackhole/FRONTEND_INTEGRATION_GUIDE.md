# Frontend Integration Guide - Hourly Salary System

## Quick Start for Frontend Developers

This guide helps you integrate the hourly-based salary management system into the frontend.

## API Base URL
```
/api/hourly-salary
```

## Authentication
All requests require the `x-auth-token` header with a valid JWT token.

```javascript
const headers = {
  'x-auth-token': localStorage.getItem('token'),
  'Content-Type': 'application/json'
};
```

## Common Use Cases

### 1. Employee Dashboard - Show My Current Salary

```javascript
// Get current month salary for logged-in user
const fetchMySalary = async () => {
  try {
    const response = await fetch('/api/hourly-salary/my-salary/current', {
      headers: { 'x-auth-token': token }
    });
    const data = await response.json();
    
    if (data.success) {
      // Display data
      console.log('Total Hours:', data.data.hours.totalHours);
      console.log('Office Hours:', data.data.hours.officeHours);
      console.log('Remote Hours:', data.data.hours.remoteHours);
      console.log('Net Salary:', data.data.salary.netSalary);
    }
  } catch (error) {
    console.error('Error:', error);
  }
};
```

**UI Component Example:**
```jsx
function MySalaryCard({ salaryData }) {
  return (
    <Card>
      <CardHeader>
        <h2>My Salary - {salaryData.period.monthName} {salaryData.period.year}</h2>
      </CardHeader>
      <CardContent>
        <div className="stats-grid">
          <StatItem 
            label="Total Hours" 
            value={salaryData.hours.totalHours}
            icon={<Clock />}
          />
          <StatItem 
            label="Office Hours" 
            value={salaryData.hours.officeHours}
            icon={<Building />}
          />
          <StatItem 
            label="Remote Hours" 
            value={salaryData.hours.remoteHours}
            icon={<Home />}
          />
          <StatItem 
            label="Net Salary" 
            value={`$${salaryData.salary.netSalary}`}
            icon={<DollarSign />}
            highlight
          />
        </div>
        
        <div className="breakdown">
          <h3>Breakdown</h3>
          <div>Regular Pay: ${salaryData.salary.regularPay}</div>
          <div>Overtime Pay: ${salaryData.salary.overtimePay}</div>
          <div>Allowances: +${salaryData.salary.allowances}</div>
          <div>Deductions: -${salaryData.salary.deductions}</div>
        </div>
      </CardContent>
    </Card>
  );
}
```

### 2. Manager View - Team Activity Log

```javascript
// Get activity log for current month
const fetchActivityLog = async (year, month) => {
  try {
    const response = await fetch(
      `/api/hourly-salary/activity-log?year=${year}&month=${month}`,
      { headers: { 'x-auth-token': token } }
    );
    const data = await response.json();
    
    if (data.success) {
      return data.data.activityLog;
    }
  } catch (error) {
    console.error('Error:', error);
  }
};
```

**UI Component Example:**
```jsx
function ActivityLogTable({ activityLog }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Employee</TableHead>
          <TableHead>Date</TableHead>
          <TableHead>Hours</TableHead>
          <TableHead>Location</TableHead>
          <TableHead>Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {activityLog.map((log, index) => (
          <TableRow key={index}>
            <TableCell>{log.userName}</TableCell>
            <TableCell>{formatDate(log.date)}</TableCell>
            <TableCell>{log.totalHoursWorked}h</TableCell>
            <TableCell>
              <Badge variant={log.workLocationType === 'Office' ? 'default' : 'secondary'}>
                {log.workLocationType}
              </Badge>
            </TableCell>
            <TableCell>
              <Badge variant={log.isPresent ? 'success' : 'destructive'}>
                {log.status}
              </Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```

### 3. Admin Dashboard - Workforce Overview

```javascript
// Get admin dashboard for current month
const fetchAdminDashboard = async () => {
  try {
    const response = await fetch('/api/hourly-salary/admin/dashboard/current', {
      headers: { 'x-auth-token': token }
    });
    const data = await response.json();
    
    if (data.success) {
      return data.data;
    }
  } catch (error) {
    console.error('Error:', error);
  }
};
```

**UI Component Example:**
```jsx
function AdminDashboard({ dashboardData }) {
  const { overallStats, employees } = dashboardData;
  
  return (
    <div className="admin-dashboard">
      {/* Overall Statistics */}
      <div className="stats-overview">
        <StatCard
          title="Total Employees"
          value={overallStats.totalEmployees}
          icon={<Users />}
        />
        <StatCard
          title="Total Hours"
          value={overallStats.totalHoursWorked}
          icon={<Clock />}
        />
        <StatCard
          title="Office Hours"
          value={overallStats.totalOfficeHours}
          icon={<Building />}
          percentage={
            (overallStats.totalOfficeHours / overallStats.totalHoursWorked * 100).toFixed(1)
          }
        />
        <StatCard
          title="Remote Hours"
          value={overallStats.totalRemoteHours}
          icon={<Home />}
          percentage={
            (overallStats.totalRemoteHours / overallStats.totalHoursWorked * 100).toFixed(1)
          }
        />
        <StatCard
          title="Total Payroll"
          value={`$${overallStats.totalNetSalary.toLocaleString()}`}
          icon={<DollarSign />}
          highlight
        />
      </div>
      
      {/* Employee List */}
      <Card>
        <CardHeader>
          <h2>Employee Details</h2>
        </CardHeader>
        <CardContent>
          <EmployeeTable employees={employees} />
        </CardContent>
      </Card>
      
      {/* Charts */}
      <div className="charts-grid">
        <WorkLocationChart data={overallStats} />
        <SalaryDistributionChart employees={employees} />
      </div>
    </div>
  );
}
```

### 4. Employee Details View

```javascript
// Get specific employee's salary for a month
const fetchEmployeeSalary = async (userId, year, month) => {
  try {
    const response = await fetch(
      `/api/hourly-salary/employee/${userId}/calculate/${year}/${month}`,
      { headers: { 'x-auth-token': token } }
    );
    const data = await response.json();
    
    if (data.success) {
      return data.data;
    }
  } catch (error) {
    console.error('Error:', error);
  }
};

// Get hours breakdown (office vs remote)
const fetchHoursBreakdown = async (userId, year, month) => {
  try {
    const response = await fetch(
      `/api/hourly-salary/employee/${userId}/hours-breakdown/${year}/${month}`,
      { headers: { 'x-auth-token': token } }
    );
    const data = await response.json();
    
    if (data.success) {
      return data.data;
    }
  } catch (error) {
    console.error('Error:', error);
  }
};
```

**UI Component Example:**
```jsx
function EmployeeDetailView({ employeeId }) {
  const [salaryData, setSalaryData] = useState(null);
  const [hoursBreakdown, setHoursBreakdown] = useState(null);
  
  useEffect(() => {
    const loadData = async () => {
      const now = new Date();
      const year = now.getFullYear();
      const month = now.getMonth() + 1;
      
      const [salary, breakdown] = await Promise.all([
        fetchEmployeeSalary(employeeId, year, month),
        fetchHoursBreakdown(employeeId, year, month)
      ]);
      
      setSalaryData(salary);
      setHoursBreakdown(breakdown);
    };
    
    loadData();
  }, [employeeId]);
  
  if (!salaryData) return <Loading />;
  
  return (
    <div className="employee-detail">
      <EmployeeHeader employee={salaryData.employee} />
      
      <div className="content-grid">
        {/* Summary Cards */}
        <SalaryCard data={salaryData} />
        <AttendanceCard data={salaryData.attendance} />
        <HoursCard data={salaryData.hours} />
        
        {/* Charts */}
        <WorkLocationPieChart breakdown={hoursBreakdown.summary} />
        <DailyHoursChart breakdown={hoursBreakdown.dailyBreakdown} />
        
        {/* Detailed Table */}
        <AttendanceDetailsTable details={salaryData.attendanceDetails} />
      </div>
    </div>
  );
}
```

### 5. Admin Actions - Update Hourly Rates

```javascript
// Update hourly rates for multiple employees
const updateHourlyRates = async (updates) => {
  try {
    const response = await fetch(
      '/api/hourly-salary/admin/hourly-rates/bulk-update',
      {
        method: 'POST',
        headers: {
          'x-auth-token': token,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ updates })
      }
    );
    const data = await response.json();
    
    if (data.success) {
      console.log('Updated:', data.results);
      return data.results;
    }
  } catch (error) {
    console.error('Error:', error);
  }
};

// Example usage
const handleBulkUpdate = async () => {
  const updates = [
    { userId: 'user1_id', hourlyRate: 30 },
    { userId: 'user2_id', hourlyRate: 35 },
    { userId: 'user3_id', hourlyRate: 40 }
  ];
  
  const results = await updateHourlyRates(updates);
  // Show success/error messages
};
```

### 6. Update Work Location Type

```javascript
// Change work location type for an attendance record
const updateWorkLocation = async (attendanceId, workLocationType) => {
  try {
    const response = await fetch(
      `/api/hourly-salary/attendance/${attendanceId}/location`,
      {
        method: 'PATCH',
        headers: {
          'x-auth-token': token,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ workLocationType })
      }
    );
    const data = await response.json();
    
    if (data.success) {
      console.log('Updated:', data.data);
      return data.data;
    }
  } catch (error) {
    console.error('Error:', error);
  }
};
```

## Data Structures

### Salary Data Response
```typescript
interface SalaryData {
  employee: {
    id: string;
    name: string;
    email: string;
    employeeId: string;
    hourlyRate: number;
  };
  period: {
    year: number;
    month: number;
    monthName: string;
    startDate: Date;
    endDate: Date;
  };
  attendance: {
    totalDays: number;
    presentDays: number;
    absentDays: number;
    attendanceRate: string;
    workLocationBreakdown: {
      officeDays: number;
      remoteDays: number;
      hybridDays: number;
    };
  };
  hours: {
    totalHours: number;
    regularHours: number;
    overtimeHours: number;
    officeHours: number;
    remoteHours: number;
    avgHoursPerDay: string;
    officePercentage: string;
    remotePercentage: string;
  };
  salary: {
    hourlyRate: number;
    regularPay: number;
    overtimePay: number;
    grossSalary: number;
    allowances: number;
    deductions: number;
    netSalary: number;
  };
  attendanceDetails: AttendanceDetail[];
}

interface AttendanceDetail {
  date: Date;
  status: string;
  isPresent: boolean;
  totalHoursWorked: number;
  regularHours: number;
  overtimeHours: number;
  officeHours: number;
  remoteHours: number;
  workLocationType: string;
  checkIn: Date;
  checkOut: Date;
  dailyEarning: number;
}
```

### Activity Log Response
```typescript
interface ActivityLogResponse {
  summary: {
    totalRecords: number;
    totalEmployees: number;
    totalHours: number;
    totalOfficeHours: number;
    totalRemoteHours: number;
    presentDays: number;
    absentDays: number;
  };
  activityLog: ActivityLogEntry[];
}

interface ActivityLogEntry {
  userId: string;
  userName: string;
  userEmail: string;
  employeeId: string;
  department: string;
  date: Date;
  status: string;
  isPresent: boolean;
  totalHoursWorked: number;
  regularHours: number;
  overtimeHours: number;
  officeHours: number;
  remoteHours: number;
  workLocationType: string;
  checkIn: Date;
  checkOut: Date;
}
```

### Admin Dashboard Response
```typescript
interface AdminDashboardResponse {
  period: {
    year: number;
    month: number;
    monthName: string;
    startDate: Date;
    endDate: Date;
  };
  overallStats: {
    totalEmployees: number;
    totalHoursWorked: number;
    totalOfficeHours: number;
    totalRemoteHours: number;
    totalOvertimeHours: number;
    totalGrossSalary: number;
    totalNetSalary: number;
    avgAttendanceRate: string;
    avgHoursPerEmployee: string;
  };
  employees: EmployeeSummary[];
}

interface EmployeeSummary {
  userId: string;
  name: string;
  email: string;
  employeeId: string;
  department: string;
  hourlyRate: number;
  attendance: {
    totalDays: number;
    presentDays: number;
    absentDays: number;
    attendanceRate: string;
  };
  hours: {
    totalHours: number;
    regularHours: number;
    overtimeHours: number;
    officeHours: number;
    remoteHours: number;
    avgHoursPerDay: string;
  };
  salary: {
    regularPay: number;
    overtimePay: number;
    grossSalary: number;
    allowances: number;
    deductions: number;
    netSalary: number;
  };
}
```

## Utility Functions

```javascript
// Format currency
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount);
};

// Format hours
const formatHours = (hours) => {
  const h = Math.floor(hours);
  const m = Math.round((hours - h) * 60);
  return `${h}h ${m}m`;
};

// Calculate percentage
const calculatePercentage = (part, total) => {
  if (total === 0) return '0';
  return ((part / total) * 100).toFixed(1);
};

// Get work location color
const getWorkLocationColor = (type) => {
  const colors = {
    'Office': 'blue',
    'Home': 'green',
    'Remote': 'green',
    'Hybrid': 'purple'
  };
  return colors[type] || 'gray';
};

// Get work location icon
const getWorkLocationIcon = (type) => {
  const icons = {
    'Office': Building,
    'Home': Home,
    'Remote': Wifi,
    'Hybrid': Split
  };
  return icons[type] || MapPin;
};
```

## Error Handling

```javascript
const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error
    const message = error.response.data.message || 'An error occurred';
    toast.error(message);
  } else if (error.request) {
    // Request made but no response
    toast.error('No response from server. Please check your connection.');
  } else {
    // Something else happened
    toast.error('An unexpected error occurred');
  }
};

// Usage
try {
  const data = await fetchMySalary();
} catch (error) {
  handleApiError(error);
}
```

## Best Practices

1. **Cache Data**: Use React Query or SWR to cache API responses
2. **Loading States**: Always show loading indicators during API calls
3. **Error Boundaries**: Wrap components in error boundaries
4. **Responsive Design**: Ensure tables and charts work on mobile
5. **Accessibility**: Use proper ARIA labels and keyboard navigation
6. **Date Handling**: Use moment.js or date-fns for date formatting
7. **Permissions**: Check user role before showing admin features

## Chart Examples

### Work Location Pie Chart
```javascript
import { PieChart, Pie, Cell, ResponsiveContainer, Legend } from 'recharts';

function WorkLocationPieChart({ officeHours, remoteHours }) {
  const data = [
    { name: 'Office', value: officeHours, color: '#3b82f6' },
    { name: 'Remote', value: remoteHours, color: '#10b981' }
  ];
  
  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          label
        >
          {data.map((entry, index) => (
            <Cell key={index} fill={entry.color} />
          ))}
        </Pie>
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}
```

### Daily Hours Bar Chart
```javascript
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

function DailyHoursChart({ dailyBreakdown }) {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={dailyBreakdown}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="officeHours" fill="#3b82f6" name="Office Hours" />
        <Bar dataKey="remoteHours" fill="#10b981" name="Remote Hours" />
      </BarChart>
    </ResponsiveContainer>
  );
}
```

## Need Help?

- API Documentation: See `HOURLY_SALARY_SYSTEM.md`
- Implementation Details: See `IMPLEMENTATION_SUMMARY_HOURLY_SALARY.md`
- Test the API: Use `server/test-hourly-salary.js`
- Contact: Backend team for API issues
