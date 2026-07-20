# Super Admin Guide

## Overview

The Super Admin is the highest authority in the School Management System. Only one Super Admin account exists, created during initial system setup. This guide covers setup, features, permissions, API endpoints, and troubleshooting.

## Table of Contents

1. [Super Admin Account](#super-admin-account)
2. [Initial Setup](#initial-setup)
3. [Super Admin Features](#super-admin-features)
4. [Permissions](#permissions)
5. [API Endpoints](#api-endpoints)
6. [Authentication & Login](#authentication--login)
7. [Security](#security)
8. [Troubleshooting](#troubleshooting)
9. [Quick Reference](#quick-reference)

---

## Super Admin Account

### Account Details

**Default Credentials** (set during setup):
- Email: `blackholeinfiverse48@gmail.com`
- Password: `superadmin123`
- Role: `SUPER_ADMIN`
- School ID: `NULL` (not assigned to any school)

### Important Security Rules

- ⚠️ **Only ONE Super Admin can exist**
- ⚠️ **Super Admin cannot be created via API** (only via setup endpoint/script)
- ⚠️ **Super Admin cannot be deleted**
- ⚠️ **Super Admin has access to ALL schools and users**
- ⚠️ **No signup form** - There is NO signup form or API endpoint for regular users to create a Super Admin account

---

## Initial Setup

### Method 1: Using the Setup Script (Recommended)

The setup script is the preferred method for creating the Super Admin account.

```bash
python scripts/setup_super_admin.py
```

**What the script does:**
1. Checks if a SUPER_ADMIN already exists in the database
2. If no SUPER_ADMIN exists, creates one with the predefined credentials
3. If SUPER_ADMIN already exists, displays a message and exits

**Output (First Run):**
```
Creating Super Admin account...
Super Admin created successfully!
  ID: 1
  Email: blackholeinfiverse48@gmail.com
  Role: SUPER_ADMIN
  School ID: None

IMPORTANT:
  - Keep these credentials secure
  - Change the password after first login if possible
  - Do not run this script again
```

**Output (Subsequent Runs):**
```
Super Admin already exists. Setup is not needed.
  The system already has a SUPER_ADMIN account.
```

### Method 2: Using the Setup API Endpoint

**⚠️ WARNING**: This endpoint should be protected or removed in production after initial setup.

**Endpoint**: `POST /super/setup`

**Request:**
- No body required
- No authentication required (for initial setup only)

**Response (First Run):**
```json
{
  "success": true,
  "message": "Super Admin created successfully.",
  "already_exists": false
}
```

**Response (Subsequent Runs):**
```json
{
  "success": false,
  "message": "Super Admin already exists. Setup is disabled.",
  "already_exists": true
}
```

**Important Notes:**
- This endpoint checks for existing SUPER_ADMIN before creation
- After first successful creation, this endpoint becomes a no-op
- Consider removing this endpoint in production or protecting it with additional security measures

---

## Super Admin Features

### 1. Dashboard Overview

**Path**: `/dashboard`

**Features**:
- System-wide statistics
- Total number of schools
- Total number of users
- Total number of admins
- Quick overview cards

### 2. School Management

#### View All Schools

**Path**: `/dashboard/schools`

**Features**:
- List all schools in the system
- Search schools by name
- View school details
- Edit school information
- Delete schools

#### Create School

**Path**: `/dashboard/create-school`

**Required Fields**:
- School Name
- School Email
- Address (optional)
- Phone (optional)

**Process**:
1. Fill in school information
2. Click "Create School"
3. School is created immediately
4. Redirected to schools list

#### Edit School

**Path**: `/dashboard/schools/:id/edit`

**Features**:
- Update school name
- Update school email
- Update address
- Update phone number
- Save changes

#### School Details

**Path**: `/dashboard/schools/:id`

**Features**:
- View complete school information
- View all admins assigned to school
- View all users in school
- Edit school button
- Delete school button

### 3. Admin Management

#### View All Admins

**Path**: `/dashboard/admins`

**Features**:
- List all school admins
- Search admins by name or email
- Filter by school
- View admin details
- Edit admin information
- Delete admins

#### Invite School Admin

**Path**: `/dashboard/create-admin`

**Process**:
1. Select school from dropdown
2. Enter admin name
3. Enter admin email
4. Click "Send Invitation"

**What Happens**:
- Admin account created with `NULL` password
- Password setup token generated
- Email sent to admin with setup link
- Admin receives email: "Set Your Password - School Management System"
- Admin clicks link and sets password
- Admin can then login

**Email Invitation Flow**:
```
Super Admin → Invite Admin → Email Sent → Admin Sets Password → Admin Can Login
```

#### Edit Admin

**Path**: `/dashboard/admins/:id/edit`

**Features**:
- Update admin name
- Update admin email
- Change assigned school
- Save changes

**Note**: Cannot change admin password (admin must use password reset)

### 4. User Management

#### View All Users

**Path**: `/dashboard/users`

**Features**:
- View all users across all schools
- Filter by role (SUPER_ADMIN, ADMIN, TEACHER, PARENT, STUDENT)
- Filter by school
- Search by name or email
- View user details

**User Roles**:
- **SUPER_ADMIN**: System administrator
- **ADMIN**: School administrator
- **TEACHER**: School teacher
- **PARENT**: Student's parent
- **STUDENT**: School student

---

## Permissions

### What Super Admin Can Do

✅ Create schools
✅ Edit any school
✅ Delete any school
✅ Invite school admins
✅ Edit any admin
✅ Delete any admin
✅ View all users
✅ View all schools
✅ Access all system features

### What Super Admin Cannot Do

❌ Create another Super Admin
❌ Delete own account
❌ Change own role
❌ Be assigned to a school

---

## API Endpoints

### Authentication

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/auth/login` | POST | No | Login and get JWT token |
| `/auth/login-json` | POST | No | Login with JSON body |

### Setup

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/super/setup` | POST | No | One-time Super Admin creation |

### Schools

| Endpoint | Method | Auth Required | Role Required | Description |
|----------|--------|---------------|---------------|-------------|
| `/schools/` | GET | Yes | SUPER_ADMIN | Get all schools |
| `/schools/` | POST | Yes | SUPER_ADMIN | Create school |
| `/schools/{id}` | GET | Yes | SUPER_ADMIN | Get school details |
| `/schools/{id}` | PUT | Yes | SUPER_ADMIN | Update school |
| `/schools/{id}` | DELETE | Yes | SUPER_ADMIN | Delete school |

### Admins

| Endpoint | Method | Auth Required | Role Required | Description |
|----------|--------|---------------|---------------|-------------|
| `/schools/admins` | GET | Yes | SUPER_ADMIN | Get all admins |
| `/super/invite-admin` | POST | Yes | SUPER_ADMIN | Invite admin (email-based) |
| `/schools/admins/{id}` | GET | Yes | SUPER_ADMIN | Get admin details |
| `/schools/admins/{id}` | PUT | Yes | SUPER_ADMIN | Update admin |
| `/schools/admins/{id}` | DELETE | Yes | SUPER_ADMIN | Delete admin |

### Dashboard

| Endpoint | Method | Auth Required | Role Required | Description |
|----------|--------|---------------|---------------|-------------|
| `/dashboard/stats` | GET | Yes | SUPER_ADMIN | Get system statistics |
| `/dashboard/users` | GET | Yes | SUPER_ADMIN | Get all users |

---

## Authentication & Login

### Login Endpoint

**Endpoint**: `POST /auth/login-json`

**Request Body:**
```json
{
  "email": "blackholeinfiverse48@gmail.com",
  "password": "superadmin123"
}
```

**Response (Success):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Response (Failure):**
```json
{
  "detail": "Incorrect email or password"
}
```

### JWT Token Contents

The JWT token contains the following claims:
- `sub`: User ID (string)
- `role`: User role (SUPER_ADMIN, ADMIN, TEACHER, PARENT, STUDENT)
- `school_id`: Associated school ID (null for SUPER_ADMIN)
- `exp`: Token expiration timestamp

### Using the Token

Include the token in the Authorization header for protected endpoints:

```
Authorization: Bearer <access_token>
```

**Example:**
```bash
curl -X GET "http://localhost:8000/schools/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Token Expiration

- Tokens expire after 30 minutes (default)
- Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` in `.env`
- Login again to get a new token

---

## Security

### Access Control Enforcement

#### Protected Endpoints

Endpoints that require SUPER_ADMIN role use the dependency `get_current_super_admin`:

```python
from app.dependencies import get_current_super_admin

@router.post("/schools/")
def create_school(
    current_user: User = Depends(get_current_super_admin)
):
    # Only SUPER_ADMIN can access this
    ...
```

#### Role Validation

The system prevents creating SUPER_ADMIN users through any API:
- Admin invitation endpoint (`POST /super/invite-admin`) creates users with `ADMIN` role only
- No user creation endpoint accepts `SUPER_ADMIN` as a role parameter
- The setup endpoint checks for existing SUPER_ADMIN before creation

### Security Best Practices

1. **Environment Variables**: Store sensitive configuration (SECRET_KEY, DATABASE_URL) in environment variables, not in code.

2. **Password Hashing**: All passwords are hashed using bcrypt with automatic salt generation.

3. **Token Expiration**: JWT tokens expire after 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).

4. **CORS Configuration**: Configure CORS properly for production to only allow requests from your frontend domain.

5. **Remove Setup Endpoint**: Consider removing or heavily securing the `/super/setup` endpoint after initial setup.

6. **Change Default Password**: After first login, implement a password change feature and change the default Super Admin password.

7. **Never Commit Credentials**: Never commit the `.env` file to version control. Use `.env.example` as a template.

---

## Troubleshooting

### Cannot Login

1. Verify email and password are correct
2. Check if account is active (`is_active = True`)
3. Check if password is set (not NULL)
4. Try resetting password (if feature available)
5. Check backend logs for errors

### Super Admin Already Exists Error

If you see "Super Admin already exists" but don't know the credentials:
1. Check the database directly: `SELECT * FROM users WHERE role = 'SUPER_ADMIN';`
2. Use database admin tools to reset the password hash if needed
3. Alternatively, delete the SUPER_ADMIN record and run the setup script again (use with caution)

### Cannot Create School

1. Verify you're logged in as Super Admin
2. Check if school email already exists
3. Check backend logs for errors
4. Verify JWT token is valid and not expired

### Admin Not Receiving Email

1. Check email configuration in `.env`
2. Verify admin email address is correct
3. Check spam/junk folder
4. Use resend script: `python scripts/resend_admin_invite.py <email>`
5. Check Brevo dashboard for delivery status
6. See `document/email_setup_guide_using_brevo.md` for detailed email troubleshooting

### Cannot Access Dashboard

1. Verify JWT token is valid
2. Check if token is expired (login again)
3. Verify role in token is `SUPER_ADMIN`
4. Check browser console for errors
5. Verify frontend is running on correct port

### Database Connection Issues

If the setup script fails with database connection errors:
1. Ensure PostgreSQL is running
2. Check `DATABASE_URL` in `.env` file
3. Verify database credentials
4. Ensure the database exists: `CREATE DATABASE school_management_db;`

### Token Authentication Issues

If login succeeds but protected endpoints return 401:
1. Check that the token is included in the Authorization header
2. Verify the token format: `Bearer <token>`
3. Check token expiration (tokens expire after 30 minutes)
4. Verify `SECRET_KEY` matches between token creation and validation

---

## Quick Reference

### Login

- **URL**: `http://localhost:3000/login`
- **Email**: `blackholeinfiverse48@gmail.com`
- **Password**: `superadmin123`

### Common Tasks

**Create School**:
1. Go to `/dashboard/create-school`
2. Fill form and submit

**Invite Admin**:
1. Go to `/dashboard/create-admin`
2. Select school
3. Enter name and email
4. Click "Send Invitation"

**View All Schools**:
- Go to `/dashboard/schools`

**View All Admins**:
- Go to `/dashboard/admins`

**View All Users**:
- Go to `/dashboard/users`

### Environment Configuration

Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/school_management_db

# JWT Configuration
SECRET_KEY=your-secret-key-here-change-in-production-use-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development
```

**Security Note**: Never commit the `.env` file to version control. Use `.env.example` as a template.

### Running the Application

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual configuration
   ```

3. **Create Super Admin:**
   ```bash
   python scripts/setup_super_admin.py
   ```

4. **Run the Server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access API Documentation:**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

---

## Support

For issues or questions regarding Super Admin:
1. Check this documentation
2. Review the application logs
3. Verify database connectivity and schema
4. Ensure all environment variables are set correctly
5. Check email configuration (see `document/email_setup_guide_using_brevo.md`)
