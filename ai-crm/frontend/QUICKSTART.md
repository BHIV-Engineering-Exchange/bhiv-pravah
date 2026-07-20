# 🚀 Quick Start Guide - Authentication System

## Prerequisites
- Node.js 16+ installed
- Supabase account (free tier works)
- Git (for version control)

## Step-by-Step Setup

### 1️⃣ Supabase Database Setup (5 minutes)

1. **Go to Supabase Dashboard**
   - Visit: https://supabase.com/dashboard
   - Select your project: `lslfjbnbcfhrlmloebax`

2. **Run SQL Setup**
   - Click **SQL Editor** in left sidebar
   - Click **New Query**
   - Copy contents from `supabase_setup.sql`
   - Paste and click **Run**
   - ✅ You should see "Success. No rows returned"

3. **Verify Tables**
   - Click **Table Editor** in left sidebar
   - You should see `profiles` table
   - Check the columns: id, email, first_name, last_name, company_name, avatar_url, created_at, updated_at

### 2️⃣ Configure Authentication Providers (5 minutes)

1. **Enable Email Provider**
   - Go to **Authentication** → **Providers**
   - Find **Email** provider
   - Toggle **Enable Email provider** to ON
   - Toggle **Confirm email** to ON (recommended)
   - Click **Save**

2. **Configure Site URL**
   - Go to **Authentication** → **URL Configuration**
   - Set **Site URL**: `http://localhost:5173`
   - Click **Save**

3. **Add Redirect URLs**
   - Still in **URL Configuration**
   - Under **Redirect URLs**, add:
     - `http://localhost:5173/auth/callback`
     - `http://localhost:5173/auth/verify-email`
   - Click **Save**

### 3️⃣ Setup OAuth Providers (Optional - 10 minutes)

#### Google OAuth Setup

1. **Create Google OAuth App**
   - Go to: https://console.cloud.google.com/
   - Create new project or select existing
   - Navigate to **APIs & Services** → **Credentials**
   - Click **Create Credentials** → **OAuth client ID**
   - Application type: **Web application**
   - Name: "AI Logistics System"
   - Authorized redirect URIs:
     - `https://lslfjbnbcfhrlmloebax.supabase.co/auth/v1/callback`
   - Click **Create**
   - Copy **Client ID** and **Client Secret**

2. **Configure in Supabase**
   - Go to Supabase **Authentication** → **Providers**
   - Find **Google** provider
   - Toggle **Enable Google provider** to ON
   - Paste **Client ID** and **Client Secret**
   - Click **Save**

#### GitHub OAuth Setup

1. **Create GitHub OAuth App**
   - Go to: https://github.com/settings/developers
   - Click **New OAuth App**
   - Application name: "AI Logistics System"
   - Homepage URL: `http://localhost:5173`
   - Authorization callback URL:
     - `https://lslfjbnbcfhrlmloebax.supabase.co/auth/v1/callback`
   - Click **Register application**
   - Copy **Client ID**
   - Click **Generate a new client secret**
   - Copy **Client Secret**

2. **Configure in Supabase**
   - Go to Supabase **Authentication** → **Providers**
   - Find **GitHub** provider
   - Toggle **Enable GitHub provider** to ON
   - Paste **Client ID** and **Client Secret**
   - Click **Save**

### 4️⃣ Start the Application (2 minutes)

1. **Navigate to frontend directory**
   ```powershell
   cd frontend
   ```

2. **Install dependencies** (if not already done)
   ```powershell
   npm install
   ```

3. **Verify .env file exists**
   - Check that `frontend/.env` contains:
   ```env
   VITE_SUPABASE_URL=https://lslfjbnbcfhrlmloebax.supabase.co
   VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

4. **Start development server**
   ```powershell
   npm run dev
   ```

5. **Open browser**
   - Visit: http://localhost:5173
   - You should be redirected to: http://localhost:5173/auth/login

### 5️⃣ Test Authentication (10 minutes)

#### Test Email Signup

1. **Go to Signup Page**
   - Click "Create account" or visit `/auth/signup`

2. **Fill in the form**
   - First Name: Your name
   - Last Name: Your surname
   - Email: Your email
   - Password: Min 8 chars, with uppercase, lowercase, number, special char
   - Confirm Password: Same as password
   - Company Name: (optional)
   - Accept Terms: Check the box
   - Click **Create Account**

3. **Check Email**
   - Open your email inbox
   - Find email from Supabase
   - Click verification link
   - You'll be redirected to login page

4. **Login**
   - Enter email and password
   - Click **Sign In**
   - ✅ You should see the dashboard
   - ✅ Your name should appear in the header

#### Test OAuth Login (if configured)

1. **Go to Login Page**
   - Visit `/auth/login`

2. **Click "Continue with Google" or "Continue with GitHub"**
   - Authorize with your account
   - ✅ Should redirect to dashboard
   - ✅ Profile auto-created

#### Test Password Reset

1. **Go to Login Page**
   - Click "Forgot password?"

2. **Enter your email**
   - Click **Send Reset Link**
   - ✅ Check your email

3. **Click reset link in email**
   - Enter new password
   - Confirm new password
   - Click **Reset Password**
   - ✅ Redirected to login
   - ✅ Login with new password

#### Test Protected Routes

1. **Open browser in incognito/private mode**
   - Visit: http://localhost:5173
   - ✅ Should redirect to `/auth/login`

2. **Login**
   - ✅ Should redirect to dashboard

3. **Refresh page**
   - ✅ Should stay logged in (session persists)

4. **Click logout in header dropdown**
   - ✅ Should redirect to `/auth/login`

### 6️⃣ Verify Database

1. **Check Profiles Table**
   - Go to Supabase **Table Editor**
   - Click on **profiles** table
   - ✅ You should see your profile record
   - ✅ Fields should be populated

2. **Check Auth Users**
   - Go to **Authentication** → **Users**
   - ✅ You should see your user account
   - ✅ Email should be verified (green checkmark)

## ✅ Success Checklist

After completing setup, verify:

- [ ] Supabase database tables created
- [ ] Email provider enabled
- [ ] Site URL configured
- [ ] Redirect URLs added
- [ ] Frontend dependencies installed
- [ ] .env file configured
- [ ] Dev server running on port 5173
- [ ] Can access login page
- [ ] Can sign up new user
- [ ] Verification email received
- [ ] Can verify email
- [ ] Can login with email/password
- [ ] User info shows in header
- [ ] Can logout
- [ ] Protected routes redirect when not authenticated
- [ ] Session persists on page refresh
- [ ] Password reset works
- [ ] Profile created in database

## 🎯 Optional Enhancements

### Custom Email Templates

1. Go to **Authentication** → **Email Templates**
2. Customize:
   - **Confirm signup** - Welcome message
   - **Reset password** - Password reset instructions
   - **Magic Link** - Passwordless login

### Email SMTP (Production)

1. Go to **Project Settings** → **Auth**
2. Scroll to **SMTP Settings**
3. Configure your SMTP server (e.g., SendGrid, Mailgun)
4. Test email delivery

### Add More Profile Fields

```sql
-- Run in Supabase SQL Editor
ALTER TABLE profiles ADD COLUMN phone TEXT;
ALTER TABLE profiles ADD COLUMN role TEXT DEFAULT 'user';
ALTER TABLE profiles ADD COLUMN last_login TIMESTAMP WITH TIME ZONE;
```

Then update:
- `authService.js` - Add fields to createUserProfile
- `Signup.jsx` - Add form fields
- `AuthContext.jsx` - Update profile type

## 🐛 Troubleshooting

### "Failed to fetch" error
- Check if Supabase URL is correct in `.env`
- Verify internet connection
- Check Supabase project status

### Email not received
- Check spam folder
- Verify email provider is enabled
- Check Supabase logs: **Authentication** → **Logs**
- For development, check Supabase inbox (free tier)

### "User already registered"
- Delete user from Supabase dashboard
- Try different email
- Check profiles table for existing record

### OAuth not working
- Verify OAuth credentials are correct
- Check redirect URLs match exactly
- Enable popup blocker exceptions
- Check browser console for errors

### Session not persisting
- Clear browser localStorage
- Check .env file is loaded (restart dev server)
- Verify supabase client configuration

### Profile not showing
- Check RLS policies are created
- Verify trigger created profiles record
- Check browser network tab for API errors
- Manually insert profile if needed

## 📚 Next Steps

1. **Customize UI**
   - Update colors in `tailwind.config.js`
   - Change logo in `AuthLayout.jsx`
   - Modify email templates in Supabase

2. **Add Features**
   - Multi-factor authentication (MFA)
   - User roles and permissions
   - Profile photo upload
   - Email change flow
   - Account deletion

3. **Production Deployment**
   - Read `AUTH_SYSTEM_README.md` deployment section
   - Configure production environment variables
   - Set up custom domain
   - Enable rate limiting
   - Configure monitoring

4. **Security Hardening**
   - Review RLS policies
   - Enable MFA for admins
   - Set up audit logging
   - Configure CSP headers
   - Regular security audits

## 🎉 You're Done!

Your authentication system is now fully functional!

**Test the complete flow:**
1. Sign up → Verify email → Login → Dashboard
2. Logout → Password reset → Login with new password
3. OAuth login → Auto-create profile → Dashboard

**Need help?** Check `AUTH_SYSTEM_README.md` for detailed documentation.

---

**Happy coding! 🚀**
