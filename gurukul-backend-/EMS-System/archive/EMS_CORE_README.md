# School Management System

A comprehensive multi-tenant School Management System built with FastAPI (Python) backend and React frontend. This system supports multiple schools, each with their own administrators, teachers, students, and parents, with complete data isolation and role-based access control.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Database Schema](#database-schema)
- [User Roles & Permissions](#user-roles--permissions)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Environment Variables](#environment-variables)
- [API Documentation](#api-documentation)
- [Frontend Structure](#frontend-structure)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This School Management System is designed to handle multiple schools (tenants) in a single application instance. Each school operates independently with its own:
- School Administrators
- Teachers
- Students
- Parents
- Classes, Subjects, and Timetables
- Lessons and Lectures
- Holidays and Events
- Announcements

The system ensures complete data isolation between schools using `school_id` filtering at the database and API level.

---

## ✨ Features

### Super Admin Features
- Create and manage multiple schools
- Create School Administrators via email invitation
- View all schools and their administrators
- View all users across all schools
- One-time Super Admin setup

### School Admin Features
- **Dashboard Overview**: View key metrics (teachers, students, parents, classes, lessons)
- **User Management**:
  - Create/manage Teachers, Students, and Parents
  - Bulk upload via Excel files
  - Automatic password generation
  - Email notifications with login credentials
- **Classes & Subjects Management**:
  - Create subjects and classes
  - Assign teachers to classes
  - Assign students to classes
- **Timetable Management**: Create weekly schedules per class
- **Lessons & Lectures**: View lessons created by teachers
- **Holidays & Events**: Manage school calendar
- **Announcements**: Create targeted announcements (Teachers/Students/Parents/Everyone)
- **Analytics & Reports**: 
  - Teacher workload visualization
  - Student distribution by grade/subject
  - Parent-student relationship mapping
  - Comprehensive charts and insights

### Security Features
- JWT-based authentication
- Role-based access control (RBAC)
- Multi-tenant data isolation
- Password hashing with bcrypt
- Email-based password setup for new users
- Soft delete (users marked as inactive, not deleted)

---

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.8+)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy 2.0
- **Authentication**: JWT (JSON Web Tokens)
- **Password Hashing**: bcrypt (via passlib)
- **Email Service**: FastAPI-Mail with Brevo (formerly Sendinblue) SMTP
- **File Processing**: openpyxl, pandas (for Excel uploads)
- **Validation**: Pydantic

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Routing**: React Router DOM
- **HTTP Client**: Axios
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **JWT Decoding**: jwt-decode

---

## 🏗 Architecture

### Multi-Tenancy Model
The system uses a **shared database, isolated data** approach:
- All schools share the same database
- Data isolation is enforced via `school_id` foreign keys
- All API endpoints filter data by `school_id` based on the logged-in user
- School Admins can only access data from their own school

### Authentication Flow
1. User logs in with email and password
2. Backend validates credentials and generates JWT token
3. JWT contains: `user_id`, `role`, `school_id`
4. Frontend stores token in localStorage
5. All subsequent API requests include token in Authorization header
6. Backend validates token and extracts user context

### Password Management
- **Super Admin**: Created via one-time setup script
- **School Admins**: Created by Super Admin, password set via email link
- **Teachers/Students/Parents**: 
  - Auto-generated strong passwords
  - Sent via email with login credentials
  - Can reset password via "Forgot Password" flow

---

## 🗄 Database Schema

### Core Tables

#### `schools`
Stores school information.
```sql
- id (PK)
- name
- address
- phone
- email
```

#### `users`
Stores all users (Super Admin, Admins, Teachers, Students, Parents).
```sql
- id (PK)
- name
- email (UNIQUE)
- password (hashed, nullable until set)
- role (ENUM: SUPER_ADMIN, ADMIN, TEACHER, PARENT, STUDENT)
- school_id (FK to schools, nullable for SUPER_ADMIN)
- is_active (boolean, for soft delete)
- subject (nullable, for teachers)
- grade (nullable, for students)
```

#### `password_tokens`
Stores tokens for password setup/reset.
```sql
- id (PK)
- user_id (FK to users)
- token (UNIQUE)
- expires_at
- is_used (boolean)
- created_at
```

### School Management Tables

#### `subjects`
Subjects taught in schools.
```sql
- id (PK)
- name
- code (optional)
- school_id (FK to schools)
- created_at
```

#### `classes`
Classes (e.g., "Grade 5A - Mathematics").
```sql
- id (PK)
- name (e.g., "Grade 5A")
- grade (e.g., "5")
- subject_id (FK to subjects)
- teacher_id (FK to users)
- school_id (FK to schools)
- academic_year (e.g., "2024-2025")
- created_at
```

#### `class_students`
Many-to-many relationship: Students enrolled in classes.
```sql
- id (PK)
- class_id (FK to classes)
- student_id (FK to users)
- enrolled_at
```

#### `student_parents`
Many-to-many relationship: Parents linked to students.
```sql
- id (PK)
- student_id (FK to users)
- parent_id (FK to users)
- relationship_type (e.g., "Father", "Mother", "Guardian")
- created_at
```

#### `lessons`
Lessons created by teachers for classes.
```sql
- id (PK)
- title
- description
- class_id (FK to classes)
- teacher_id (FK to users)
- school_id (FK to schools)
- lesson_date
- created_at
```

#### `lectures`
Individual lectures within a lesson.
```sql
- id (PK)
- lesson_id (FK to lessons)
- title
- content
- lecture_date
- start_time
- end_time
- created_at
```

#### `timetable_slots`
Weekly timetable schedule.
```sql
- id (PK)
- class_id (FK to classes)
- subject_id (FK to subjects)
- teacher_id (FK to users)
- school_id (FK to schools)
- day_of_week (0=Monday, 6=Sunday)
- start_time
- end_time
- room (optional)
- created_at
```

#### `holidays`
School holidays.
```sql
- id (PK)
- name
- start_date
- end_date
- school_id (FK to schools)
- description
- created_at
```

#### `events`
School events (exams, PTM, etc.).
```sql
- id (PK)
- title
- description
- event_date
- event_time
- event_type (e.g., "Exam", "PTM", "Annual Day")
- school_id (FK to schools)
- created_at
```

#### `announcements`
Announcements to teachers/students/parents.
```sql
- id (PK)
- title
- content
- target_audience (TEACHERS/STUDENTS/PARENTS/EVERYONE)
- school_id (FK to schools)
- published_at
- created_by (FK to users)
- created_at
```

### Database Relationships

```
School (1) ──< (N) User
School (1) ──< (N) Subject
School (1) ──< (N) Class
School (1) ──< (N) Lesson
School (1) ──< (N) TimetableSlot
School (1) ──< (N) Holiday
School (1) ──< (N) Event
School (1) ──< (N) Announcement

Subject (1) ──< (N) Class
User (1) ──< (N) Class (as teacher)
User (1) ──< (N) ClassStudent ──< (N) Class
User (1) ──< (N) StudentParent ──< (N) User (as parent)

Class (1) ──< (N) Lesson
Class (1) ──< (N) TimetableSlot
Lesson (1) ──< (N) Lecture
```

---

## 👥 User Roles & Permissions

### SUPER_ADMIN
- **Access**: All schools and users
- **Can Do**:
  - Create schools
  - Create School Administrators (via email invitation)
  - View all schools and admins
  - View all users across all schools
- **Cannot Do**:
  - Access school-specific data (classes, students, etc.)
  - Create teachers/students/parents directly

### ADMIN (School Admin)
- **Access**: Only their own school (`school_id` based)
- **Can Do**:
  - Manage teachers, students, parents
  - Create classes, subjects, timetables
  - View lessons, holidays, events
  - Create announcements
  - View analytics for their school
- **Cannot Do**:
  - Access other schools' data
  - Create other admins
  - Access Super Admin features

### TEACHER
- **Access**: Only their assigned classes and students
- **Can Do**:
  - View assigned classes
  - Create lessons and lectures
  - View students in their classes
- **Cannot Do**:
  - Create users
  - Access other teachers' classes
  - Manage school settings

### PARENT
- **Access**: Only their linked children's information
- **Can Do**:
  - View children's grades, attendance, schedule
  - View announcements targeted to parents
- **Cannot Do**:
  - Access other students' information
  - Create or modify data

### STUDENT
- **Access**: Only their own information
- **Can Do**:
  - View own grades, attendance, schedule
  - View announcements targeted to students
- **Cannot Do**:
  - Access other students' information
  - Create or modify data

---

## 📁 Project Structure

```
School_Mangment_System/
├── app/                          # Backend application
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Configuration settings
│   ├── database.py               # Database connection & Base
│   ├── auth.py                   # Authentication utilities
│   ├── dependencies.py           # FastAPI dependencies (auth, roles)
│   ├── email_service.py          # Email sending service
│   ├── models.py                 # SQLAlchemy ORM models
│   ├── schemas.py                # Pydantic schemas (request/response)
│   ├── routers/                  # API route handlers
│   │   ├── auth.py              # Authentication endpoints
│   │   ├── super_admin.py       # Super Admin endpoints
│   │   ├── schools.py           # School management endpoints
│   │   ├── dashboard.py         # Dashboard endpoints
│   │   └── admin/               # School Admin endpoints
│   │       └── dashboard.py     # All School Admin features
│   └── utils/                   # Utility functions
│       ├── password_generator.py    # Generate unique passwords
│       ├── excel_upload.py          # Excel bulk upload processing
│       └── excel_upload_combined.py # Combined student/parent upload
│
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── main.jsx             # React entry point
│   │   ├── App.jsx               # Main app component
│   │   ├── components/           # React components
│   │   │   ├── Layout.jsx        # Main layout with sidebar
│   │   │   ├── Login.jsx         # Login page
│   │   │   ├── SetPassword.jsx   # Password setup page
│   │   │   ├── Dashboard.jsx     # Dashboard router
│   │   │   ├── DashboardOverview.jsx  # Super Admin dashboard
│   │   │   ├── SchoolList.jsx    # List schools
│   │   │   ├── CreateSchool.jsx  # Create school form
│   │   │   ├── AdminList.jsx     # List admins
│   │   │   ├── CreateAdmin.jsx   # Create admin form
│   │   │   └── admin/            # School Admin components
│   │   │       ├── SchoolAdminDashboard.jsx
│   │   │       ├── TeachersManagement.jsx
│   │   │       ├── StudentsManagement.jsx
│   │   │       ├── ParentsManagement.jsx
│   │   │       ├── ClassesManagement.jsx
│   │   │       ├── TimetableManagement.jsx
│   │   │       ├── HolidaysEvents.jsx
│   │   │       ├── Announcements.jsx
│   │   │       ├── LessonsView.jsx
│   │   │       └── Analytics.jsx
│   │   ├── context/
│   │   │   └── AuthContext.jsx   # Authentication context
│   │   └── services/
│   │       └── api.js            # API service functions
│   ├── package.json
│   └── vite.config.js
│
├── scripts/                      # Utility scripts
│   ├── setup_super_admin.py      # One-time Super Admin creation
│   ├── migrate_database.py       # Database migration
│   ├── migrate_school_admin_models.py  # Create new tables
│   ├── add_subject_to_users.py   # Add subject column migration
│   ├── add_grade_to_users.py     # Add grade column migration
│   ├── test_email.py             # Test email configuration
│   ├── check_user_login.py       # Check user login status
│   └── resend_admin_invite.py    # Resend admin invitation
│
├── document/                     # Documentation
│   ├── SUPER_ADMIN_GUIDE.md
│   ├── SCHOOL_ADMIN_GUIDE.md
│   ├── email_setup_guide_using_brevo.md
│   └── ...
│
├── requirements.txt              # Python dependencies
├── env.example                   # Environment variables template
└── README.md                     # This file
```

---

## 🚀 Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Node.js 16+ and npm
- PostgreSQL 12+
- Git

### Step 1: Clone the Repository
```bash
git clone https://github.com/yashikart/School-Mangment-System.git
cd School_Mangment_System
```

### Step 2: Backend Setup

1. **Create a virtual environment** (recommended):
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

2. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up PostgreSQL database**:
```bash
# Create database
createdb school_management_db

# Or using psql:
psql -U postgres
CREATE DATABASE school_management_db;
\q
```

4. **Configure environment variables**:
```bash
# Copy the example file
cp env.example .env

# Edit .env with your settings
# See Environment Variables section below
```

5. **Run database migrations**:
```bash
# Create all tables
python scripts/migrate_database.py

# Create School Admin tables
python scripts/migrate_school_admin_models.py

# Add subject column to users (if needed)
python scripts/add_subject_to_users.py

# Add grade column to users (if needed)
python scripts/add_grade_to_users.py
```

6. **Create Super Admin** (one-time setup):
```bash
python scripts/setup_super_admin.py
```
Follow the prompts to create the Super Admin account.

7. **Start the backend server**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Step 3: Frontend Setup

1. **Navigate to frontend directory**:
```bash
cd frontend
```

2. **Install dependencies**:
```bash
npm install
```

3. **Start the development server**:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000` (or the port shown in terminal)

### Step 4: Verify Setup

1. Open `http://localhost:3000` in your browser
2. Login with Super Admin credentials
3. Create a school
4. Create a School Admin for that school
5. Check email for password setup link
6. Login as School Admin and explore the dashboard

---

## 🔐 Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/school_management_db

# JWT Configuration
SECRET_KEY=your-secret-key-here-change-in-production-use-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development

# Email Configuration (SMTP) - Brevo
MAIL_USERNAME=your-brevo-email@example.com
MAIL_PASSWORD=your-brevo-smtp-key
MAIL_FROM=noreply@yourdomain.com
MAIL_PORT=587
MAIL_SERVER=smtp-relay.brevo.com
MAIL_FROM_NAME=School Management System
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
USE_CREDENTIALS=true
VALIDATE_CERTS=true

# Frontend URL (for password setup links)
FRONTEND_URL=http://localhost:3000

# Password token expiration (minutes)
PASSWORD_TOKEN_EXPIRE_MINUTES=30
```

### Getting Brevo SMTP Credentials
1. Sign up at [Brevo](https://www.brevo.com/)
2. Go to Settings → SMTP & API → SMTP
3. Generate an SMTP key
4. Use your Brevo account email as `MAIL_USERNAME`
5. Use the SMTP key as `MAIL_PASSWORD`

See `document/email_setup_guide_using_brevo.md` for detailed email setup instructions.

---

## 📡 API Documentation

### Base URL
```
http://localhost:8000
```

### Authentication
Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

### Main API Endpoints

#### Authentication
- `POST /auth/login` - Login and get JWT token
- `POST /auth/set-password` - Set password via token (for new users)
- `POST /auth/forgot-password` - Request password reset
- `POST /auth/reset-password` - Reset password with token
- `POST /auth/change-password` - Change password (authenticated users)

#### Super Admin
- `POST /super/setup` - Create Super Admin (one-time)
- `GET /super/schools` - List all schools
- `POST /super/schools` - Create school
- `GET /super/admins` - List all admins
- `POST /super/invite-admin` - Invite School Admin via email
- `GET /super/users` - View all users

#### School Admin
- `GET /admin/dashboard/stats` - Get dashboard statistics
- `GET /admin/teachers` - List teachers
- `POST /admin/teachers` - Create teacher
- `PUT /admin/teachers/{id}` - Update teacher
- `DELETE /admin/teachers/{id}` - Delete teacher (soft delete)
- `POST /admin/teachers/upload-excel` - Bulk upload teachers
- Similar endpoints for `/admin/students` and `/admin/parents`
- `GET /admin/classes` - List classes
- `POST /admin/classes` - Create class
- `POST /admin/classes/{class_id}/students/{student_id}` - Assign student to class
- `GET /admin/analytics` - Get analytics data
- And many more...

### Interactive API Documentation
FastAPI provides automatic interactive documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🎨 Frontend Structure

### Routing
The frontend uses React Router for navigation:
- `/login` - Login page
- `/set-password` - Password setup page (with token query param)
- `/dashboard` - Main dashboard (role-based)

### Component Organization
- **Layout.jsx**: Main layout with sidebar navigation (role-based menu)
- **AuthContext.jsx**: Global authentication state management
- **api.js**: Centralized API service functions
- **Components**: Organized by feature (Super Admin, School Admin, etc.)

### State Management
- React Context API for authentication state
- Local component state for forms and UI
- No external state management library (Redux, etc.)

---

## 🔄 How It Works

### 1. Initial Setup Flow
```
1. Run setup_super_admin.py → Creates Super Admin in database
2. Super Admin logs in → Gets JWT token
3. Super Admin creates school → School record created
4. Super Admin invites School Admin → Admin user created (password=NULL)
5. Email sent with password setup link
6. School Admin clicks link → Sets password
7. School Admin logs in → Gets JWT token with school_id
```

### 2. User Creation Flow (School Admin)
```
1. School Admin creates teacher/student/parent
2. System generates unique password
3. User record created (password hashed)
4. Email sent with login credentials
5. User can login immediately
```

### 3. Excel Bulk Upload Flow
```
1. School Admin uploads Excel file
2. Backend validates data (emails, duplicates, etc.)
3. For each valid row:
   - Generate unique password
   - Create user record
   - Send email with credentials
4. Return summary (success count, failed rows with reasons)
```

### 4. Data Isolation (Multi-Tenancy)
```
1. User logs in → JWT contains school_id
2. All API requests include JWT in header
3. Backend extracts school_id from JWT
4. All database queries filter by school_id
5. School Admin can only see/modify their school's data
```

### 5. Class-Student Assignment
```
1. School Admin creates class → Class record created
2. School Admin assigns teacher → Class.teacher_id set
3. School Admin assigns students → ClassStudent records created
4. Analytics count students per class/teacher
5. Students appear in teacher's class list
```

---

## 🐛 Troubleshooting

### Backend Issues

**Database Connection Error**
- Check PostgreSQL is running
- Verify `DATABASE_URL` in `.env`
- Ensure database exists

**Import Errors**
- Activate virtual environment
- Reinstall dependencies: `pip install -r requirements.txt`

**JWT Token Errors**
- Check `SECRET_KEY` in `.env`
- Ensure token hasn't expired
- Clear browser localStorage and login again

### Frontend Issues

**CORS Errors**
- Ensure backend CORS settings include frontend URL
- Check `app/main.py` CORS configuration

**API Connection Failed**
- Verify backend is running on port 8000
- Check `api.js` base URL configuration
- Check browser console for errors

**Login Not Working**
- Verify user exists and is active
- Check password is set (not NULL)
- Run `python scripts/check_user_login.py <email>` to diagnose

### Email Issues

**Emails Not Sending**
- Verify Brevo SMTP credentials in `.env`
- Test email configuration: `python scripts/test_email.py`
- Check Brevo dashboard for sent emails
- See `document/email_setup_guide_using_brevo.md` for detailed troubleshooting

**Password Setup Link Not Working**
- Check `FRONTEND_URL` in `.env` matches frontend port
- Verify token hasn't expired
- Check token in database: `password_tokens` table

### Database Issues

**Missing Tables**
- Run migration scripts:
  ```bash
  python scripts/migrate_database.py
  python scripts/migrate_school_admin_models.py
  ```

**Column Errors**
- Run column migration scripts:
  ```bash
  python scripts/add_subject_to_users.py
  python scripts/add_grade_to_users.py
  ```

### Analytics Showing Zeros

**Students Not Counted**
- Ensure students are assigned to classes
- Go to Classes Management → Assign students to classes
- Analytics only count enrolled students

**Deleted Users Still Showing**
- System uses soft delete (`is_active=False`)
- Analytics filter by `is_active=True`
- Refresh page to see updated counts

---

## 🔗 PRANA Telemetry Integration

### EMS Backend Responsibilities (Identity Stability Only)

The EMS backend's responsibility with respect to PRANA telemetry is **limited to providing stable identifiers**. EMS backend does NOT interpret, score, store, or influence PRANA telemetry.

#### What EMS Backend Provides

1. **User Identity Stability**
   - `user_id` (from `users.id`) must be stable and consistent
   - JWT token contains `user_id` that persists across sessions
   - User ID is extracted from JWT and made available to frontend via `window.EMSUserContext`

2. **Session Identity** (if implemented)
   - `session_id` should exist early in the user session
   - Should persist across page refreshes
   - Should be available to frontend for PRANA packet construction

3. **Lesson Context Updates**
   - `lesson_id` must update correctly when user navigates to a different lesson
   - Lesson ID is backend-issued (auto-increment Integer from `lessons` table)
   - Frontend receives `lesson_id` from API responses and URL parameters
   - Frontend is responsible for setting `window.EMSTaskContext` with current `lesson_id`

#### What EMS Backend Does NOT Do

The EMS backend does **NOT**:
- ❌ Interpret PRANA telemetry packets
- ❌ Score or evaluate PRANA data
- ❌ Store PRANA packets (this is handled by the Bucket endpoint at `/bucket/prana/ingest`)
- ❌ Influence UX based on PRANA data
- ❌ Make decisions based on telemetry signals

**PRANA consumes identifiers only.** The EMS backend's role is purely to provide stable, reliable identifiers that PRANA can use to tag telemetry packets.

### Integration Points

- **User ID**: Available via JWT token (`sub` claim) → `window.EMSUserContext.id`
- **Lesson ID**: Available via lesson API responses → Frontend sets `window.EMSTaskContext.currentTaskId`
- **Session ID**: (To be implemented) Should be generated early and persist across refreshes

### Bucket Endpoint

The EMS backend provides a **separate, append-only ledger endpoint** at `/bucket/prana/ingest` that:
- Validates PRANA-E packet structure
- Stores packets immutably in `prana_packets` table
- Does NOT interpret or score the data
- Acts as a pure ingestion endpoint

See `app/routers/bucket.py` for implementation details.

---

## 📚 Additional Documentation

- **Super Admin Guide**: `document/SUPER_ADMIN_GUIDE.md`
- **School Admin Guide**: `document/SCHOOL_ADMIN_GUIDE.md`
- **Email Setup Guide**: `document/email_setup_guide_using_brevo.md`
- **Login Troubleshooting**: `document/LOGIN_TROUBLESHOOTING.md`

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License.

---

## 👤 Author

**Yashika Tirkey**
- GitHub: [@yashikart](https://github.com/yashikart)
- Repository: [School-Mangment-System](https://github.com/yashikart/School-Mangment-System)

---

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- React team for the powerful frontend library
- PostgreSQL for robust database support
- Brevo for email service
- All open-source contributors

---

## 📞 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Last Updated**: 2024
