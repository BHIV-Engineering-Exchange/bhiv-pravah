# 📧 Email Verification Setup Guide

## Issue: "Email not confirmed"

This happens when email confirmation is required but not properly configured in Supabase.

## 🔧 Option 1: Disable Email Confirmation (Development Only)

For development/testing, you can disable email confirmation:

### Steps:

1. **Go to Supabase Dashboard**
   - Visit: https://supabase.com/dashboard
   - Select your project: `lslfjbnbcfhrlmloebax`

2. **Disable Email Confirmation**
   - Click **Authentication** in left sidebar
   - Click **Providers** tab
   - Find **Email** provider
   - **Uncheck** "Confirm email"
   - Click **Save**

3. **Test Signup**
   - Sign up with a new email
   - ✅ You should be logged in immediately
   - ✅ No email verification required

**⚠️ Important:** Re-enable this for production!

---

## 🎯 Option 2: Configure Email Verification (Production Ready)

For production, you should keep email verification enabled and configure it properly:

### Steps:

### 1. Configure Redirect URLs

1. **Go to Authentication → URL Configuration**
   - **Site URL**: `http://localhost:3001` (for dev)
   - Click **Save**

2. **Add Redirect URLs**
   Under "Redirect URLs", add:
   ```
   http://localhost:3001/auth/verify-email
   http://localhost:3001/auth/callback
   http://localhost:3001/*
   ```
   Click **Save**

### 2. Customize Email Template (Optional but Recommended)

1. **Go to Authentication → Email Templates**

2. **Click "Confirm signup" template**

3. **Update the template** to include better messaging:
   ```html
   <h2>Welcome to AI Agent Logistics System!</h2>
   <p>Please click the link below to verify your email address:</p>
   <p><a href="{{ .ConfirmationURL }}">Verify Email Address</a></p>
   <p>Or copy and paste this URL into your browser:</p>
   <p>{{ .ConfirmationURL }}</p>
   <p>This link expires in 24 hours.</p>
   ```

4. Click **Save**

### 3. Test Email Verification Flow

1. **Sign up with a valid email address**
   - Go to: http://localhost:3001/auth/signup
   - Fill in the form with a real email address
   - Click "Create Account"

2. **Check your email inbox**
   - Look for email from Supabase (check spam folder!)
   - Subject: "Confirm Your Signup"

3. **Click the verification link**
   - Should redirect to: `http://localhost:3001/auth/verify-email#access_token=...`
   - You'll see "Email Verified!" message
   - Auto-redirects to dashboard

4. **Verify in Supabase Dashboard**
   - Go to **Authentication** → **Users**
   - Find your user
   - ✅ "Email Confirmed At" should have a timestamp
   - ✅ Green checkmark next to email

---

## 🐛 Troubleshooting

### Problem: Not receiving verification email

**Solution 1: Check Supabase Email Logs**
1. Go to **Authentication** → **Logs**
2. Look for email delivery events
3. Check for errors

**Solution 2: Use Supabase Development Inbox (Free Tier)**
1. During development, Supabase captures emails in the dashboard
2. Go to **Authentication** → **Users**
3. Click on your user
4. Look for "Confirmation sent to" message
5. Copy the confirmation link from there

**Solution 3: Check Spam Folder**
- Supabase emails often land in spam
- Add `noreply@mail.app.supabase.io` to contacts

**Solution 4: Use a Different Email Provider**
- Try Gmail, Outlook, or Yahoo
- Some email providers block automated emails

### Problem: "Invalid verification link"

**Possible Causes:**
1. Link expired (24 hour limit)
2. Link already used
3. Redirect URL not configured in Supabase

**Solutions:**
1. Request a new verification email
2. Check redirect URLs in Supabase settings
3. Sign up again with a different email

### Problem: Verification link redirects to wrong URL

**Solution:**
1. Check `emailRedirectTo` in `authService.js`:
   ```javascript
   emailRedirectTo: `${window.location.origin}/auth/verify-email`
   ```
2. Ensure it matches your app's route
3. Restart dev server after changes

### Problem: Email verified but still can't login

**Solution 1: Check user status in Supabase**
1. Go to **Authentication** → **Users**
2. Check if user is "Active" or "Blocked"
3. Check "Email Confirmed At" timestamp

**Solution 2: Clear browser cache and try again**
1. Clear localStorage: `localStorage.clear()`
2. Clear cookies for localhost
3. Try logging in again

**Solution 3: Manually confirm email (Development only)**
1. Go to Supabase **SQL Editor**
2. Run this query:
   ```sql
   UPDATE auth.users 
   SET email_confirmed_at = NOW() 
   WHERE email = 'your-email@example.com';
   ```
3. Try logging in again

---

## 🔒 Security Best Practices

### For Production:

1. **Always enable email verification**
   - Prevents fake signups
   - Verifies user owns the email

2. **Use custom SMTP server**
   - More reliable delivery
   - Better branding
   - Configure in: **Project Settings** → **Auth** → **SMTP Settings**

3. **Set up proper email templates**
   - Match your brand
   - Clear call-to-action
   - Include security warnings

4. **Configure rate limiting**
   - Prevent spam signups
   - Limit verification email requests

5. **Monitor failed verifications**
   - Check logs regularly
   - Investigate suspicious patterns

---

## 📋 Quick Reference

### Current Configuration:

- **Verification Route**: `/auth/verify-email`
- **OAuth Callback Route**: `/auth/callback`
- **Redirect URL in Code**: `${window.location.origin}/auth/verify-email`

### Required Supabase Settings:

- **Site URL**: Your app's base URL (e.g., `http://localhost:3001`)
- **Redirect URLs**: Must include `/auth/verify-email` and `/auth/callback`
- **Email Provider**: Enabled
- **Confirm Email**: Enabled (for production) or Disabled (for quick testing)

### Files Involved:

- `src/services/auth/authService.js` - Sets `emailRedirectTo`
- `src/pages/auth/VerifyEmail.jsx` - Handles verification
- `src/pages/auth/Signup.jsx` - Triggers email send
- `src/lib/supabase.js` - Supabase client config

---

## ✅ Testing Checklist

After configuration, test:

- [ ] Can sign up with new email
- [ ] Verification email received (check inbox and spam)
- [ ] Can click verification link
- [ ] Redirects to `/auth/verify-email`
- [ ] Shows "Email Verified!" message
- [ ] Auto-redirects to dashboard
- [ ] User appears in Supabase dashboard as "confirmed"
- [ ] Can login after verification
- [ ] Session persists on refresh

---

## 🚀 Production Deployment

Before deploying to production:

1. **Update Site URL** to production domain
2. **Update Redirect URLs** to production domain
3. **Enable email confirmation**
4. **Configure custom SMTP** (recommended)
5. **Customize email templates** with your branding
6. **Test the complete flow** on production
7. **Set up email monitoring** and alerts

---

## 📞 Still Having Issues?

### Quick Fixes:

1. **For Testing Only** - Disable email confirmation temporarily
2. **For Development** - Use the Supabase development inbox
3. **For Production** - Set up custom SMTP and proper DNS

### Debug Mode:

Add this to `VerifyEmail.jsx` to see what's happening:

```javascript
console.log('Hash params:', window.location.hash);
console.log('Search params:', window.location.search);
console.log('Full URL:', window.location.href);
```

This will help identify if the redirect is working correctly.

---

**Need more help?** Check the main `QUICKSTART.md` or `AUTH_SYSTEM_README.md` files.
