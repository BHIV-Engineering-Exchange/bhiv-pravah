# Email Setup Guide Using Brevo

## Overview

The School Management System uses **Brevo** (formerly Sendinblue) for sending password setup emails to new admins. This comprehensive guide covers Brevo setup, email configuration, password setup flow, testing, and troubleshooting.

## Table of Contents

1. [Brevo Setup](#brevo-setup)
2. [Email Configuration](#email-configuration)
3. [Email Flow](#email-flow)
4. [Testing](#testing)
5. [Troubleshooting](#troubleshooting)
6. [Security](#security)

---

## Brevo Setup

### What is Brevo?

Brevo (formerly Sendinblue) is an email service provider that offers:
- **Free tier**: 300 emails/day
- Reliable SMTP service
- Email tracking and analytics
- Easy setup and configuration
- Good delivery rates

### Step 1: Create Brevo Account

1. Go to: https://www.brevo.com/
2. Sign up for a free account
3. Verify your email address
4. Complete account setup

### Step 2: Get SMTP Credentials

1. Login to Brevo dashboard: https://app.brevo.com/
2. Navigate to: **Settings** → **SMTP & API** → **SMTP** tab
3. You'll see your SMTP credentials:
   - **SMTP Server**: `smtp-relay.brevo.com` (recommended) or `smtp.brevo.com`
   - **Port**: `587` (TLS) or `465` (SSL)
   - **Login**: Your Brevo account email (the email you used to register)
   - **SMTP Key**: Copy your SMTP key (starts with `xsmtpsib-`)

**Important**: 
- Use the **SMTP Key**, not the API key
- The **Login** must be your Brevo account email, not a Gmail or other email

---

## Email Configuration

### Step 1: Update `.env` File

Open your `.env` file in the root directory and add/update these settings:

```env
# Email Configuration (Brevo SMTP)
MAIL_USERNAME=your-brevo-account-email@example.com
MAIL_PASSWORD=xsmtpsib-your-complete-smtp-key-here
MAIL_FROM=noreply@schoolmanagement.com
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

### Configuration Details

| Variable | Description | Example |
|----------|-------------|---------|
| `MAIL_USERNAME` | Your Brevo account email | `your-email@example.com` |
| `MAIL_PASSWORD` | Your Brevo SMTP key | `xsmtpsib-159e19761fa4be...` |
| `MAIL_FROM` | Sender email address | `noreply@schoolmanagement.com` |
| `MAIL_PORT` | SMTP port | `587` (TLS) or `465` (SSL) |
| `MAIL_SERVER` | Brevo SMTP server | `smtp-relay.brevo.com` |
| `MAIL_STARTTLS` | Enable STARTTLS | `true` (for port 587) |
| `MAIL_SSL_TLS` | Enable SSL/TLS | `false` (for port 587) |
| `FRONTEND_URL` | Frontend URL for links | `http://localhost:3000` |
| `PASSWORD_TOKEN_EXPIRE_MINUTES` | Token expiration | `30` |

### Step 2: Restart Server

After updating `.env`, **restart your FastAPI server**:

```bash
# Stop server (Ctrl+C)
# Then restart:
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Brevo SMTP Server Options

#### Option 1: smtp-relay.brevo.com (Recommended)
- **Port**: 587 (TLS)
- **Encryption**: STARTTLS
- **Best for**: Production use
- **Settings**:
  ```env
  MAIL_SERVER=smtp-relay.brevo.com
  MAIL_PORT=587
  MAIL_STARTTLS=true
  MAIL_SSL_TLS=false
  ```

#### Option 2: smtp.brevo.com
- **Port**: 587 (TLS) or 465 (SSL)
- **Encryption**: STARTTLS or SSL
- **Settings for TLS**:
  ```env
  MAIL_SERVER=smtp.brevo.com
  MAIL_PORT=587
  MAIL_STARTTLS=true
  MAIL_SSL_TLS=false
  ```
- **Settings for SSL**:
  ```env
  MAIL_SERVER=smtp.brevo.com
  MAIL_PORT=465
  MAIL_STARTTLS=false
  MAIL_SSL_TLS=true
  ```

---

## Email Flow

### Complete Password Setup Flow

```
┌─────────────────────────────────────────────────────────────┐
│           EMAIL-BASED PASSWORD SETUP FLOW                  │
└─────────────────────────────────────────────────────────────┘

1. SUPER_ADMIN INVITES ADMIN
   ┌──────────────────────────────────────┐
   │ POST /super/invite-admin              │
   │ {                                      │
   │   "name": "John Doe",                  │
   │   "email": "john@school.com",          │
   │   "school_id": 1                      │
   │ }                                      │
   └───────────────┬──────────────────────┘
                   │
                   ▼
   ┌──────────────────────────────────────┐
   │ Backend creates User:                 │
   │ - password: NULL (not set!)           │
   │ - role: ADMIN                         │
   │ - is_active: TRUE                     │
   └───────────────┬──────────────────────┘
                   │
                   ▼
   ┌──────────────────────────────────────┐
   │ Generate secure token (32 chars)     │
   │ Save to password_tokens table        │
   │ - expires_at: now + 30 minutes        │
   │ - is_used: FALSE                      │
   └───────────────┬──────────────────────┘
                   │
                   ▼
   ┌──────────────────────────────────────┐
   │ Send Email via Brevo SMTP            │
   │ To: john@school.com                   │
   │ Subject: Set Your Password            │
   │ Link: {FRONTEND_URL}/set-password    │
   │         ?token=abc123xyz...           │
   └───────────────┬──────────────────────┘
                   │
                   ▼
   ┌──────────────────────────────────────┐
   │ Response: Success                     │
   └──────────────────────────────────────┘

2. ADMIN RECEIVES EMAIL
   ┌──────────────────────────────────────┐
   │ Email arrives at john@school.com     │
   │ Admin clicks link                     │
   └───────────────┬──────────────────────┘
                   │
                   ▼
   ┌──────────────────────────────────────┐
   │ POST /auth/set-password               │
   │ {                                      │
   │   "token": "abc123xyz...",            │
   │   "password": "mypassword123"         │
   │ }                                      │
   └───────────────┬──────────────────────┘
                   │
                   ▼
   ┌──────────────────────────────────────┐
   │ Backend validates token              │
   │ - Token exists?                       │
   │ - Token not expired?                  │
   │ - Token not used?                     │
   └───────────────┬──────────────────────┘
                   │
                   ▼
   ┌──────────────────────────────────────┐
   │ Hash password with bcrypt            │
   │ Save to users.password                │
   │ Mark token as used                    │
   └───────────────┬──────────────────────┘
                   │
                   ▼
   ┌──────────────────────────────────────┐
   │ Response: Success                     │
   └──────────────────────────────────────┘

3. ADMIN CAN NOW LOGIN
   ┌──────────────────────────────────────┐
   │ POST /auth/login-json                 │
   │ {                                      │
   │   "email": "john@school.com",         │
   │   "password": "mypassword123"         │
   │ }                                      │
   └───────────────┬──────────────────────┘
                   │
                   ▼
   ┌──────────────────────────────────────┐
   │ Backend authenticates                │
   │ Returns JWT token                     │
   └──────────────────────────────────────┘
```

### Key Components

#### 1. Invite Admin Endpoint (`POST /super/invite-admin`)

**Location**: `app/routers/super_admin.py`

**What it does**:
- Creates ADMIN user with `password = NULL`
- Generates secure token (32 characters)
- Saves token to `password_tokens` table
- Sends email with password setup link
- Returns success response

**Security**:
- Only SUPER_ADMIN can access
- Token is cryptographically secure
- Token expires after 30 minutes

#### 2. Email Service (`app/email_service.py`)

**Functions**:
- `generate_password_token(db, user_id)` - Creates secure token
- `send_password_setup_email(db, user, password_token)` - Sends email
- `validate_password_token(db, token)` - Validates token
- `mark_token_as_used(db, password_token)` - Marks token as used

#### 3. Set Password Endpoint (`POST /auth/set-password`)

**Location**: `app/routers/auth.py`

**What it does**:
- Validates the token
- Validates password (min 6 characters)
- Hashes password with bcrypt
- Saves password to user
- Marks token as used

#### 4. Login Endpoint (`POST /auth/login-json`)

**Location**: `app/routers/auth.py`

**What it does**:
- Authenticates user with email and password
- Checks: user exists, is_active, password exists, password matches
- Returns JWT token if successful

### Email Template

**Subject**: "Set Your Password - School Management System"

**Body**:
```
Hello {user.name},

You have been invited to join the School Management System as an Administrator.

Please set your password by clicking on the following link:
{setup_link}

This link will expire in {PASSWORD_TOKEN_EXPIRE_MINUTES} minutes.

If you did not request this invitation, please ignore this email.

Best regards,
School Management System
```

**Setup Link Format**:
```
{FRONTEND_URL}/set-password?token={token}
```

---

## Testing

### Method 1: Test Email Configuration Script

**Location**: `scripts/test_email.py` or `tests/email/test_email_config.py`

**Usage**:
```bash
python scripts/test_email.py
```

**What it does**:
- Checks email configuration
- Validates SMTP connection
- Sends test email to `MAIL_USERNAME`
- Shows success or error messages

**Expected Output** (Success):
```
[OK] Email sent successfully!
Please check your inbox: your-email@example.com
Also check spam/junk folder!
```

### Method 2: Test Admin Invitation

**Steps**:
1. Login as Super Admin
2. Go to `/dashboard/create-admin`
3. Enter test admin details
4. Click "Send Invitation"
5. Check email inbox

**What to check**:
- ✅ Email received
- ✅ Subject is correct
- ✅ Link works
- ✅ Token is valid

### Method 3: Resend Admin Invitation

**Location**: `scripts/resend_admin_invite.py`

**Usage**:
```bash
python scripts/resend_admin_invite.py admin@example.com
```

**What it does**:
- Finds admin user
- Generates new token
- Sends invitation email
- Shows setup link

### Method 4: Check Email Status

**Location**: `scripts/check_email_status.py`

**Usage**:
```bash
python scripts/check_email_status.py
```

**What it shows**:
- Email configuration
- Recent password tokens
- Users without passwords
- Active tokens with setup links

### Method 5: Check Brevo Dashboard

1. Login to Brevo: https://app.brevo.com/
2. Go to: **Statistics** → **Email Logs**
3. Check sent emails:
   - **Recipient**: Email address
   - **Status**: Delivered, Bounced, or Failed
   - **Subject**: "Set Your Password - School Management System"

---

## Troubleshooting

### Issue 1: Authentication Failed

**Error**: `SMTPAuthenticationError: (535, '5.7.8 Authentication failed')`

**Causes**:
- Wrong `MAIL_USERNAME` (not Brevo account email)
- Wrong `MAIL_PASSWORD` (not SMTP key)
- Incomplete SMTP key

**Solution**:
1. Verify credentials in Brevo dashboard
2. Copy exact values to `.env`
3. No quotes or spaces in `.env`
4. Restart backend server

### Issue 2: Email Not Received

**Possible Causes**:
1. **Email in spam folder** (most common)
   - Check spam/junk folder
   - Mark as "Not Spam"

2. **Wrong recipient email**
   - Verify email address is correct
   - Check for typos

3. **Email bounced**
   - Check Brevo dashboard
   - Verify email address is valid

4. **Email delayed**
   - Wait 2-5 minutes
   - Check again

**Solution**:
1. Check spam folder first
2. Verify email address
3. Check Brevo dashboard for status
4. Wait a few minutes
5. Request resend if needed

### Issue 3: Token Expired

**Error**: "Token expired or invalid"

**Cause**: Token expires after 30 minutes (default)

**Solution**:
1. Request new invitation
2. Use resend script: `python scripts/resend_admin_invite.py <email>`
3. Set password immediately after receiving email

### Issue 4: Wrong Port in Link

**Problem**: Link uses wrong port (5173 vs 3000)

**Solution**:
1. Update `FRONTEND_URL` in `.env`:
   ```env
   FRONTEND_URL=http://localhost:3000
   ```
2. Restart backend server
3. New invitations will use correct port

### Issue 5: Connection Refused/Timeout

**Error**: Connection refused or timeout

**Solution**:
1. Check firewall allows SMTP connections (port 587)
2. Verify `MAIL_SERVER` and `MAIL_PORT` are correct
3. Try using `smtp-relay.brevo.com` instead of `smtp.brevo.com`

### Issue 6: Daily Email Limit Exceeded

**Error**: Email sending fails due to limit

**Solution**:
1. Brevo free tier allows 300 emails/day
2. Wait 24 hours or upgrade to paid plan
3. Check email sending status in Brevo dashboard

---

## Security

### Security Features

1. **SUPER_ADMIN Never Knows Passwords**
   - Passwords are NULL when admin is created
   - Only admin sets password via email link

2. **Secure Token Generation**
   - Cryptographically secure random tokens
   - 32 characters, URL-safe
   - Unique per invitation

3. **Time-Limited Tokens**
   - Tokens expire after 30 minutes (configurable)
   - Prevents long-term token abuse

4. **Single-Use Tokens**
   - Tokens marked as `is_used = TRUE` after use
   - Cannot be reused

5. **Password Hashing**
   - All passwords hashed with bcrypt
   - Never stored in plain text

6. **Active Status Check**
   - Users must be `is_active = TRUE` to login
   - Allows deactivation without deletion

### Security Best Practices

1. **Never commit credentials**: Add `.env` to `.gitignore`
2. **Use SMTP Keys**: Never use main account password
3. **Rotate Keys**: Regularly rotate SMTP keys
4. **Monitor Usage**: Check Brevo dashboard for unusual activity
5. **Use HTTPS**: Always use encrypted connections (STARTTLS/SSL)
6. **Verify Sender Domain**: Add SPF/DKIM records for production

---

## Brevo Dashboard Features

1. **Email Statistics**: Track sent emails, delivery rates
2. **Email Logs**: See detailed logs of sent emails
3. **SMTP Settings**: Manage SMTP keys
4. **Sender Verification**: Verify sender domains
5. **Email Templates**: Create email templates (optional)

---

## Production Considerations

1. **Use Environment Variables**: Don't commit `.env` to git
2. **Verify Sender Domain**: Add SPF/DKIM records for better deliverability
3. **Monitor Quotas**: Brevo free tier has 300 emails/day limit
4. **Upgrade Plan**: Consider paid plan for higher limits (9,000 emails/month)
5. **Email Templates**: Use HTML email templates for better appearance
6. **Rate Limiting**: Implement rate limiting for email sending
7. **Error Handling**: Implement retry logic for failed emails
8. **Update FRONTEND_URL**: Use production URL in `.env`

---

## Quick Reference

### Brevo Dashboard
- URL: https://app.brevo.com/
- SMTP Settings: Settings → SMTP & API → SMTP

### Test Commands
```bash
# Test email configuration
python scripts/test_email.py

# Resend invitation
python scripts/resend_admin_invite.py <email>

# Check email status
python scripts/check_email_status.py
```

### Configuration File
- Location: `.env` (root directory)
- Required: `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_SERVER`, `FRONTEND_URL`

### Brevo Free Tier Limits
- **300 emails/day** (free tier)
- **Unlimited contacts**
- **Email tracking available**

---

## Support

For email issues:
1. Check this guide
2. Review troubleshooting section
3. Check Brevo dashboard
4. Test with `test_email.py` script
5. Check backend logs
6. Verify `.env` configuration
