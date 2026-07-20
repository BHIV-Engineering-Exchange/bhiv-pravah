# Infiverse BHL - Comprehensive Workforce Management System

## 🚀 Project Overview

Infiverse BHL is a comprehensive, full-stack workforce management system designed to streamline employee operations, task management, attendance tracking, salary management, and AI-powered optimization. The system provides real-time monitoring, automated workflows, and intelligent insights for modern workplace management.

## 🏗️ Architecture

### Technology Stack

**Frontend (Client)**
- **Framework**: React 19.1.0 with Vite 6.3.1
- **Routing**: React Router DOM 7.5.2
- **State Management**: Context API (Auth, Socket, Workspace, Dashboard)
- **UI Framework**: Tailwind CSS 4.1.4 with Shadcn/UI components
- **Animations**: Framer Motion 12.23.12
- **Real-time**: Socket.IO Client 4.8.1
- **HTTP Client**: Axios 1.9.0
- **Charts**: Recharts 2.15.4
- **Date Handling**: Date-fns 4.1.0
- **Notifications**: React Toastify 11.0.5

**Backend (Server)**
- **Runtime**: Node.js with Express 5.1.0
- **Database**: MongoDB with Mongoose 8.14.0
- **Authentication**: JWT (jsonwebtoken 9.0.2)
- **Real-time**: Socket.IO 4.8.1
- **File Processing**: Multer 1.4.5, ExcelJS 4.4.0, XLSX 0.18.5
- **AI Integration**: Google Generative AI 0.24.0, Gemini AI 2.2.1
- **Image Processing**: Sharp 0.33.5, Canvas 3.1.2
- **PDF Generation**: PDFKit 0.17.1, jsPDF 3.0.1
- **Email**: Nodemailer 7.0.0
- **Cloud Storage**: Cloudinary 2.6.0
- **Geolocation**: Geolib 3.3.4
- **OCR**: Tesseract.js 6.0.1
- **Screen Capture**: Screenshot-desktop 1.15.0

## 📁 Project Structure

```
Infiverse-BHL/
├── client/                          # Frontend React Application
│   ├── src/
│   │   ├── components/              # Reusable UI Components
│   │   │   ├── attendance/          # Attendance Management Components
│   │   │   │   ├── LiveAttendanceDashboard.jsx
│   │   │   │   └── RealTimeTracker.jsx
│   │   │   ├── dashboard/           # Dashboard Components
│   │   │   ├── departments/         # Department Management
│   │   │   ├── leave/               # Leave Management
│   │   │   ├── monitoring/          # Employee Monitoring
│   │   │   ├── salary/              # Salary Management
│   │   │   ├── tasks/               # Task Management
│   │   │   └── ui/                  # Base UI Components (Shadcn)
│   │   ├── context/                 # React Context Providers
│   │   │   ├── auth-context.jsx     # Authentication State
│   │   │   ├── socket-context.jsx   # Real-time Socket Connection
│   │   │   ├── workspace-context.jsx # Workspace State
│   │   │   └── DashboardContext.jsx # Dashboard State
│   │   ├── hooks/                   # Custom React Hooks
│   │   │   ├── use-attendance.js    # Attendance Operations
│   │   │   ├── use-salary.js        # Salary Operations
│   │   │   ├── use-tasks.js         # Task Operations
│   │   │   └── use-toast.js         # Toast Notifications
│   │   ├── pages/                   # Main Application Pages
│   │   │   ├── Dashboard.jsx        # Admin Dashboard
│   │   │   ├── UserDashboard.jsx    # Employee Dashboard
│   │   │   ├── AttendanceDashboard.jsx
│   │   │   ├── SalaryManagement.jsx
│   │   │   ├── EmployeeMonitoring.jsx
│   │   │   └── Tasks.jsx
│   │   ├── lib/                     # Utility Libraries
│   │   │   └── api.js               # API Client Configuration
│   │   └── layouts/                 # Layout Components
│   └── package.json
├── server/                          # Backend Node.js Application
│   ├── models/                      # MongoDB Data Models
│   │   ├── User.js                  # User Schema
│   │   ├── Task.js                  # Task Schema
│   │   ├── Attendance.js            # Attendance Schema
│   │   ├── Salary.js                # Salary Schema
│   │   ├── Leave.js                 # Leave Management
│   │   ├── Department.js            # Department Schema
│   │   └── Notification.js          # Notification Schema
│   ├── routes/                      # API Route Handlers
│   │   ├── auth.js                  # Authentication Routes
│   │   ├── attendance.js            # Attendance Management
│   │   ├── salary.js                # Salary Management
│   │   ├── tasks.js                 # Task Management
│   │   ├── users.js                 # User Management
│   │   ├── monitoring.js            # Employee Monitoring
│   │   └── ai.js                    # AI Integration
│   ├── services/                    # Business Logic Services
│   │   ├── attendanceService.js     # Attendance Processing
│   │   ├── salaryCalculator.js      # Salary Calculations
│   │   ├── screenCapture.js         # Screen Monitoring
│   │   ├── excelProcessor.js        # Excel File Processing
│   │   └── groqAIService.js         # AI Service Integration
│   ├── middleware/                  # Express Middleware
│   │   ├── auth.js                  # JWT Authentication
│   │   └── adminAuth.js             # Admin Authorization
│   ├── utils/                       # Utility Functions
│   │   ├── emailService.js          # Email Notifications
│   │   ├── cloudinary.js            # File Upload Service
│   │   └── pushNotificationService.js
│   └── index.js                     # Server Entry Point
└── README.md
```

## 🔧 Core Features

### 1. **User Management & Authentication**
- **Multi-role System**: Admin, Manager, User roles with different permissions
- **JWT Authentication**: Secure token-based authentication
- **User Profiles**: Comprehensive user profiles with avatars and department assignments
- **Department Management**: Hierarchical department structure

### 2. **Task Management System**
- **Task Creation & Assignment**: Create tasks with priorities, due dates, and dependencies
- **Task Dependencies**: Visual dependency tracking and management
- **Progress Tracking**: Real-time task progress monitoring
- **Task Submissions**: File upload and review system
- **Status Management**: Pending, In Progress, Completed status tracking

### 3. **Attendance Management**
- **Real-time Tracking**: Live attendance monitoring with geolocation
- **Biometric Integration**: Excel file upload for biometric device data
- **Start/End Day**: Manual check-in/check-out with location verification
- **Auto End Day**: Automatic day ending after maximum working hours
- **Attendance Analytics**: Comprehensive attendance reports and statistics
- **Discrepancy Detection**: Automatic detection of time and location mismatches

### 4. **Salary Management**
- **Automated Calculations**: Attendance-based salary calculations
- **Allowances & Deductions**: Configurable salary components
- **Salary History**: Track salary changes and adjustments
- **Performance Incentives**: KPI-based bonus calculations
- **Bank Integration**: Bank details management for payroll
- **Tax Management**: Tax calculations and exemptions

### 5. **Leave Management**
- **Leave Requests**: Digital leave application system
- **Approval Workflow**: Multi-level leave approval process
- **Leave Types**: Sick, vacation, personal, emergency leave categories
- **Leave Balance**: Automatic leave balance tracking
- **Calendar Integration**: Leave calendar visualization

### 6. **Employee Monitoring**
- **Screen Capture**: Intelligent screen monitoring with OCR analysis
- **Activity Tracking**: Keystroke and mouse activity monitoring
- **Website Monitoring**: Track visited websites and productivity
- **Time Tracking**: Detailed time tracking with break management
- **Productivity Scoring**: AI-powered productivity analysis

### 7. **AI-Powered Optimization**
- **Workflow Optimization**: AI suggestions for process improvement
- **Dependency Analysis**: Intelligent task dependency recommendations
- **Performance Insights**: AI-driven performance analytics
- **Predictive Analytics**: Forecast attendance and productivity trends
- **Automated Reporting**: AI-generated reports and insights

### 8. **Real-time Communication**
- **Socket.IO Integration**: Real-time updates across all modules
- **Push Notifications**: Browser push notifications for important events
- **Live Dashboard**: Real-time dashboard updates
- **Instant Alerts**: Immediate notifications for critical events

### 9. **Reporting & Analytics**
- **Comprehensive Dashboards**: Role-based dashboard views
- **Advanced Analytics**: Detailed reports with charts and graphs
- **Export Functionality**: PDF and Excel export capabilities
- **Custom Reports**: Configurable report generation
- **Data Visualization**: Interactive charts and graphs

### 10. **Mobile Responsiveness**
- **Responsive Design**: Mobile-first responsive design
- **Touch Optimization**: Touch-friendly interface
- **Offline Capability**: Limited offline functionality
- **Progressive Web App**: PWA features for mobile installation

## 🗄️ Database Schema

### User Model
```javascript
{
  name: String,
  email: String (unique),
  password: String (hashed),
  role: ['Admin', 'Manager', 'User'],
  department: ObjectId (ref: Department),
  avatar: String,
  createdAt: Date,
  updatedAt: Date
}
```

### Attendance Model
```javascript
{
  user: ObjectId (ref: User),
  date: Date,
  biometricTimeIn: Date,
  biometricTimeOut: Date,
  startDayTime: Date,
  endDayTime: Date,
  startDayLocation: {
    latitude: Number,
    longitude: Number,
    address: String,
    accuracy: Number
  },
  hoursWorked: Number,
  overtimeHours: Number,
  isPresent: Boolean,
  isVerified: Boolean,
  hasDiscrepancy: Boolean,
  productivityScore: Number,
  approvalStatus: ['Pending', 'Approved', 'Rejected'],
  employeeNotes: String,
  managerNotes: String
}
```

### Salary Model
```javascript
{
  user: ObjectId (ref: User),
  baseSalary: Number,
  currency: String,
  salaryType: ['Monthly', 'Annual', 'Hourly'],
  adjustments: [{
    type: String,
    amount: Number,
    reason: String,
    date: Date
  }],
  allowances: {
    housing: Number,
    transport: Number,
    medical: Number
  },
  deductions: {
    tax: Number,
    insurance: Number,
    providentFund: Number
  },
  bankDetails: {
    accountNumber: String,
    bankName: String,
    ifscCode: String
  }
}
```

### Task Model
```javascript
{
  title: String,
  description: String,
  status: ['Pending', 'In Progress', 'Completed'],
  priority: ['Low', 'Medium', 'High'],
  department: ObjectId (ref: Department),
  assignee: ObjectId (ref: User),
  dueDate: Date,
  dependencies: [ObjectId (ref: Task)],
  progress: Number (0-100),
  notes: String,
  links: [String]
}
```

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Get current user

### Attendance
- `GET /api/attendance/live` - Get live attendance data
- `POST /api/attendance/start-day/:userId` - Start work day
- `POST /api/attendance/end-day/:userId` - End work day
- `POST /api/attendance/upload` - Upload biometric data
- `GET /api/attendance/analytics` - Get attendance analytics
- `GET /api/attendance/user/:userId` - Get user attendance records

### Salary
- `GET /api/salary/user/:userId` - Get user salary details
- `POST /api/salary/calculate` - Calculate monthly salary
- `PUT /api/salary/:id` - Update salary information
- `GET /api/salary/analytics` - Get salary analytics

### Tasks
- `GET /api/tasks` - Get all tasks
- `POST /api/tasks` - Create new task
- `PUT /api/tasks/:id` - Update task
- `DELETE /api/tasks/:id` - Delete task
- `GET /api/tasks/:id` - Get task details

### Users
- `GET /api/users` - Get all users
- `POST /api/users` - Create new user
- `PUT /api/users/:id` - Update user
- `DELETE /api/users/:id` - Delete user

### Monitoring
- `POST /api/monitoring/screen-capture` - Capture screen
- `GET /api/monitoring/activity/:userId` - Get user activity
- `POST /api/monitoring/website-visit` - Log website visit

## 🚀 Installation & Setup

### Prerequisites
- Node.js (v18 or higher)
- MongoDB (v5 or higher)
- npm or yarn package manager

### Environment Variables

Create `.env` files in both client and server directories:

**Server (.env)**
```env
# Database
MONGODB_URI=mongodb://localhost:27017/infiverse-bhl

# JWT
JWT_SECRET=your_jwt_secret_key

# Office Location
OFFICE_LAT=19.1663
OFFICE_LNG=72.8526
OFFICE_RADIUS=100
OFFICE_ADDRESS=Your Office Address

# Working Hours
MAX_WORKING_HOURS=8
AUTO_END_DAY_ENABLED=true

# AI Services
GOOGLE_AI_API_KEY=your_google_ai_key
GROQ_API_KEY=your_groq_api_key

# Email Service
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Push Notifications
VAPID_PUBLIC_KEY=your_vapid_public_key
VAPID_PRIVATE_KEY=your_vapid_private_key
```

**Client (.env)**
```env
VITE_API_URL=http://localhost:5000/api
VITE_SOCKET_URL=http://localhost:5000
REACT_APP_OPENCAGE_API_KEY=your_opencage_api_key
```

### Installation Steps

1. **Clone the repository**
```bash
git clone https://github.com/your-repo/infiverse-bhl.git
cd infiverse-bhl
```

2. **Install server dependencies**
```bash
cd server
npm install
```

3. **Install client dependencies**
```bash
cd ../client
npm install
```

4. **Set up MongoDB**
```bash
# Start MongoDB service
mongod

# Create database (optional - will be created automatically)
mongo
use infiverse-bhl
```

5. **Start the development servers**

**Terminal 1 (Server):**
```bash
cd server
npm start
```

**Terminal 2 (Client):**
```bash
cd client
npm run dev
```

6. **Access the application**
- Frontend: http://localhost:5173
- Backend API: http://localhost:5000/api

## 🔐 User Roles & Permissions

### Admin
- Full system access
- User management (create, update, delete users)
- Department management
- System configuration
- All reports and analytics
- Employee monitoring access

### Manager
- Department-specific access
- Task assignment and management
- Team attendance monitoring
- Salary management for team members
- Leave approval authority
- Team performance reports

### User/Employee
- Personal dashboard access
- Task management (assigned tasks)
- Attendance tracking (start/end day)
- Leave request submission
- Personal reports and analytics
- Profile management

## 🔄 Real-time Features

The system uses Socket.IO for real-time communication:

### Real-time Events
- **attendance:day-started** - When employee starts day
- **attendance:day-ended** - When employee ends day
- **attendance:auto-day-ended** - Auto end day notification
- **task-created** - New task assignment
- **task-updated** - Task status changes
- **leave-requested** - New leave request
- **notification** - System notifications

### Live Updates
- Dashboard statistics
- Attendance status changes
- Task progress updates
- System notifications
- User activity status

## 🤖 AI Integration

### AI Services Used
1. **Google Generative AI** - Content generation and analysis
2. **Groq AI** - Fast inference for real-time analysis
3. **Custom ML Models** - Productivity scoring and pattern recognition

### AI Features
- **Productivity Analysis** - AI-powered productivity scoring
- **Workflow Optimization** - Intelligent process improvement suggestions
- **Predictive Analytics** - Forecast attendance and performance trends
- **Anomaly Detection** - Identify unusual patterns in employee behavior
- **Automated Reporting** - AI-generated insights and reports
- **OCR Analysis** - Screen content analysis for productivity tracking

## 📊 Monitoring & Analytics

### Employee Monitoring
- **Screen Capture** - Periodic screen captures with OCR analysis
- **Activity Tracking** - Keystroke and mouse activity monitoring
- **Website Monitoring** - Track visited websites and categorize productivity
- **Application Usage** - Monitor application usage patterns
- **Idle Time Detection** - Track inactive periods

### Analytics Dashboard
- **Attendance Trends** - Historical attendance patterns
- **Productivity Metrics** - Individual and team productivity scores
- **Task Performance** - Task completion rates and efficiency
- **Department Analytics** - Department-wise performance comparison
- **Custom Reports** - Configurable report generation

## 🔧 Configuration

### System Configuration
- **Working Hours** - Configurable standard working hours
- **Office Location** - GPS coordinates for location verification
- **Attendance Rules** - Flexible attendance policies
- **Leave Policies** - Customizable leave rules and balances
- **Salary Components** - Configurable allowances and deductions

### Monitoring Settings
- **Screen Capture Frequency** - Adjustable capture intervals
- **Website Categories** - Productivity classification of websites
- **Activity Thresholds** - Configurable activity detection levels
- **Privacy Settings** - Granular privacy controls

## 🚀 Deployment

### Production Deployment

1. **Build the client**
```bash
cd client
npm run build
```

2. **Configure production environment**
```bash
# Update environment variables for production
# Set up MongoDB Atlas or production database
# Configure domain and SSL certificates
```

3. **Deploy to cloud platform**
```bash
# Example for Heroku
heroku create infiverse-bhl
git push heroku main
```

### Docker Deployment
```dockerfile
# Dockerfile example
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5000
CMD ["npm", "start"]
```

## 🧪 Testing

### Running Tests
```bash
# Server tests
cd server
npm test

# Client tests
cd client
npm test
```

### Test Coverage
- Unit tests for core business logic
- Integration tests for API endpoints
- End-to-end tests for critical user flows
- Performance tests for monitoring features

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow ESLint configuration for code style
- Write comprehensive tests for new features
- Update documentation for API changes
- Follow semantic versioning for releases

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation wiki

## 🔄 Version History

### v1.0.0 (Current)
- Initial release with core features
- User management and authentication
- Task management system
- Attendance tracking
- Basic salary management
- Employee monitoring
- AI integration
- Real-time updates

### Planned Features (v1.1.0)
- Advanced reporting dashboard
- Mobile application
- Integration with external HR systems
- Enhanced AI capabilities
- Performance review system
- Training management module

---

**Built with ❤️ by the Infiverse BHL Development Team**