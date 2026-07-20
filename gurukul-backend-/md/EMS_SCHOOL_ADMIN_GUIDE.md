# School Admin Guide

## Overview

School Admins are administrators assigned to specific schools. They manage their school's teachers, students, and parents. School Admins are created and invited by the Super Admin.

## School Admin Account

### Account Creation

School Admins are created by Super Admin through the invitation system:

1. **Super Admin invites admin**:
   - Goes to `/dashboard/create-admin`
   - Selects school
   - Enters admin name and email
   - Clicks "Send Invitation"

2. **Admin receives email**:
   - Email subject: "Set Your Password - School Management System"
   - Contains password setup link
   - Link format: `http://localhost:3000/set-password?token=<token>`

3. **Admin sets password**:
   - Clicks email link
   - Enters new password (min 6 characters)
   - Confirms password
   - Password is set

4. **Admin can login**:
   - Goes to `/login`
   - Enters email and password
   - Accesses school admin dashboard

### Account Information

- **Role**: `ADMIN`
- **School ID**: Assigned during invitation
- **Password**: Set by admin via email link
- **Status**: Active by default

## School Admin Features

### 1. Dashboard Overview

**Path**: `/dashboard`

**Features**:
- School-specific statistics
- Overview of school data
- Quick access to key features

### 2. My School

**Path**: `/dashboard/school`

**Features**:
- View school information
- School name, email, address, phone
- Edit school details (if permitted)

### 3. Teachers Management

**Path**: `/dashboard/teachers`

**Features** (to be implemented):
- View all teachers in school
- Add new teachers
- Edit teacher information
- Remove teachers
- Assign teachers to classes

### 4. Students Management

**Path**: `/dashboard/students`

**Features** (to be implemented):
- View all students in school
- Add new students
- Edit student information
- Remove students
- Assign students to classes

### 5. Parents Management

**Path**: `/dashboard/parents`

**Features** (to be implemented):
- View all parents in school
- Add new parents
- Link parents to students
- Edit parent information
- Remove parents

## School Admin Permissions

### What School Admin Can Do

✅ View own school information
✅ Manage teachers in their school
✅ Manage students in their school
✅ Manage parents in their school
✅ Access school-specific features
✅ View school statistics

### What School Admin Cannot Do

❌ Create or delete schools
❌ Invite other admins
❌ Access other schools' data
❌ View Super Admin features
❌ Change school assignment
❌ Delete own account

## Login Process

### Step 1: Receive Invitation

1. Super Admin invites you via email
2. Check your email inbox (and spam folder)
3. Look for email: "Set Your Password - School Management System"

### Step 2: Set Password

1. Click the link in the email
2. You'll be taken to: `http://localhost:3000/set-password?token=<token>`
3. Enter your new password (min 6 characters)
4. Confirm your password
5. Click "Set Password"
6. You'll see a success message
7. You'll be redirected to login page

### Step 3: Login

1. Go to: `http://localhost:3000/login`
2. Enter your email address
3. Enter the password you just set
4. Click "Login"
5. You'll see the School Admin Dashboard

## Dashboard Navigation

### Menu Items

The School Admin dashboard shows:
- **Dashboard** - Overview and statistics
- **My School** - School information
- **Teachers** - Teacher management
- **Students** - Student management
- **Parents** - Parent management

### Header Information

- Dashboard title: "School Admin Dashboard"
- Subtitle: "Manage your school"
- Your email address
- Your role: "School Admin"

## Password Management

### Setting Password

- Done via email invitation link
- One-time setup process
- Password must be at least 6 characters

### Changing Password

- Feature to be implemented
- Will allow admins to change their password
- Will require current password verification

### Password Reset

- Feature to be implemented
- Will allow password reset via email
- Similar to initial password setup

## Troubleshooting

### Did Not Receive Invitation Email

1. **Check spam/junk folder**
   - Emails often go to spam initially
   - Mark as "Not Spam" if found

2. **Verify email address**
   - Confirm email address is correct
   - Check for typos

3. **Check Brevo dashboard**
   - Super Admin can check email delivery status
   - Look for "Delivered", "Bounced", or "Failed"

4. **Request resend**
   - Super Admin can resend invitation
   - Use: `python scripts/resend_admin_invite.py <your-email>`

### Cannot Set Password

1. **Check token validity**
   - Token expires after 30 minutes
   - Request new invitation if expired

2. **Verify link**
   - Make sure link is complete
   - Check for any truncation

3. **Password requirements**
   - Minimum 6 characters
   - Passwords must match

### Cannot Login

1. **Verify credentials**
   - Check email is correct
   - Check password is correct

2. **Check account status**
   - Account must be active
   - Password must be set

3. **Token expiration**
   - JWT tokens expire after 30 minutes
   - Login again to get new token

### Access Denied Errors

1. **Verify role**
   - You must be logged in as ADMIN
   - Check your role in dashboard header

2. **Check permissions**
   - School Admins have limited access
   - Cannot access Super Admin features

3. **School assignment**
   - Verify you're assigned to a school
   - Contact Super Admin if not assigned

## Best Practices

### Password Security

- Use strong passwords (min 8+ characters recommended)
- Don't share your password
- Change password regularly (when feature available)

### Account Management

- Keep your email address updated
- Notify Super Admin if you change email
- Report suspicious activity

### Data Management

- Regularly review school data
- Keep student/parent information updated
- Remove inactive accounts

## Quick Reference

### Login URL

```
http://localhost:3000/login
```

### Set Password URL

```
http://localhost:3000/set-password?token=<your-token>
```

### Dashboard URL

```
http://localhost:3000/dashboard
```

### Common Tasks

**View School Information**:
- Go to `/dashboard/school`

**Manage Teachers**:
- Go to `/dashboard/teachers`

**Manage Students**:
- Go to `/dashboard/students`

**Manage Parents**:
- Go to `/dashboard/parents`

## Future Features

The following features are planned:
- [ ] Teacher management (add, edit, remove)
- [ ] Student management (add, edit, remove)
- [ ] Parent management (add, edit, remove)
- [ ] Class management
- [ ] Attendance tracking
- [ ] Grade management
- [ ] Report generation
- [ ] Password change functionality
- [ ] Profile management

## Support

If you need help:
1. Contact your Super Admin
2. Check this documentation
3. Review troubleshooting section
4. Check system logs (if accessible)
