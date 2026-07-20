# Login Troubleshooting Guide

## Common Login Issues and Solutions

### Issue: "Login failed. Please check your credentials."

This error can occur for several reasons. Follow these steps to diagnose and fix:

---

## Step 1: Check User Status

Run the diagnostic script to check your user account:

```bash
python scripts/check_user_login.py <your-email>
```

This will show:
- ✅ If user exists
- ✅ If user is active
- ✅ If password is set
- ⚠️ Specific issues preventing login

---

## Common Causes and Solutions

### 1. **User Not Found**
**Error:** "Incorrect email or password"

**Possible Reasons:**
- Email is misspelled
- User was never created
- Email has extra spaces

**Solution:**
- Double-check the email address
- Verify the user exists in the database
- Contact administrator to create the account

---

### 2. **Account is Inactive**
**Error:** "Account is inactive. Please contact administrator."

**Possible Reasons:**
- User was soft-deleted (`is_active = False`)
- Account was deactivated by admin

**Solution:**
- Contact your administrator to reactivate the account
- Or run this SQL to reactivate:
  ```sql
  UPDATE users SET is_active = TRUE WHERE email = 'your-email@example.com';
  ```

---

### 3. **Password Not Set (NULL)**
**Error:** "Password not set. Please check your email for password setup link."

**For School Admins (ADMIN role):**
- This is normal for newly created School Admins
- They receive an email invitation with a password setup link
- **Solution:** Check your email inbox (and spam folder) for the password setup link
- Use the link to set your password, then login

**For Other Users:**
- Contact administrator to set a password
- Or use the "Forgot Password" feature if available

---

### 4. **Wrong Password**
**Error:** "Incorrect email or password"

**Possible Reasons:**
- Password is incorrect
- Password has extra spaces
- Caps Lock is on
- Password was changed but you're using the old one

**Solution:**
- Double-check the password (case-sensitive)
- Try typing the password in a text editor first, then copy-paste
- Use "Forgot Password" to reset if available
- Contact administrator to reset password

---

### 5. **Super Admin Login Issues**

**If you're the Super Admin:**
- Super Admin password is set during initial setup
- Default credentials (if using setup script):
  - Email: `blackholeinfiverse48@gmail.com`
  - Password: `superadmin123`

**If login fails:**
1. Check if Super Admin exists:
   ```bash
   python scripts/check_user_login.py blackholeinfiverse48@gmail.com
   ```
2. If Super Admin doesn't exist, create it:
   ```bash
   python scripts/setup_super_admin.py
   ```

---

## Step 2: Verify Backend is Running

Make sure the FastAPI backend is running:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Check if backend is accessible:
- Open: http://localhost:8000/docs
- You should see the Swagger UI

---

## Step 3: Verify Frontend is Running

Make sure the React frontend is running:

```bash
cd frontend
npm run dev
```

Check if frontend is accessible:
- Open: http://localhost:5173
- You should see the login page

---

## Step 4: Check Network Connection

**Frontend-Backend Connection:**
- Frontend should connect to: `http://localhost:8000`
- Check `frontend/src/services/api.js` - `API_BASE_URL` should be correct
- Check browser console for CORS errors

---

## Step 5: Check Browser Console

Open browser Developer Tools (F12) and check:
1. **Console Tab:** Look for JavaScript errors
2. **Network Tab:** Check if login request is being sent
   - Status should be `200` for success
   - Status `401` means authentication failed
   - Status `500` means server error

---

## Step 6: Test Login via API Directly

Test the login endpoint directly using curl or Postman:

```bash
curl -X POST "http://localhost:8000/auth/login-json" \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com", "password": "your-password"}'
```

**Expected Success Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

**Expected Error Response:**
```json
{
  "detail": "Incorrect email or password"
}
```

---

## Quick Fixes

### Reset Password for a User

**Option 1: Use Forgot Password (if implemented)**
- Click "Forgot Password" on login page
- Enter email
- Check email for reset link

**Option 2: Admin Reset (SQL)**
```sql
-- Generate new password hash (use Python script)
-- Then update:
UPDATE users 
SET password = '<hashed_password>' 
WHERE email = 'user@example.com';
```

**Option 3: Reactivate User**
```sql
UPDATE users 
SET is_active = TRUE 
WHERE email = 'user@example.com';
```

---

## Still Having Issues?

1. **Check Backend Logs:**
   - Look at the terminal where `uvicorn` is running
   - Check for error messages or stack traces

2. **Check Database:**
   - Verify user exists: `SELECT * FROM users WHERE email = 'your-email@example.com';`
   - Check `is_active` and `password` fields

3. **Clear Browser Cache:**
   - Clear localStorage: `localStorage.clear()` in browser console
   - Clear cookies and cache
   - Try incognito/private window

4. **Verify Environment Variables:**
   - Check `.env` file has correct database connection
   - Verify `SECRET_KEY` is set (needed for JWT)

---

## Contact Support

If none of the above solutions work:
1. Run the diagnostic script: `python scripts/check_user_login.py <email>`
2. Share the output
3. Share backend logs
4. Share browser console errors

---

## Prevention Tips

1. **Always set passwords immediately** after account creation
2. **Don't soft-delete users** unless necessary (use `is_active = False` carefully)
3. **Keep email addresses unique** and validated
4. **Use strong passwords** and store them securely
5. **Test login** after creating new users
