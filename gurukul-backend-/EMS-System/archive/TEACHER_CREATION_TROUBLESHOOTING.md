# Teacher Creation Troubleshooting

## If you see "Failed to create teacher" error

Follow these steps to diagnose and fix:

---

## Step 1: Check Browser Console

1. Open browser Developer Tools (Press `F12`)
2. Go to **Console** tab
3. Try creating a teacher again
4. Look for any red error messages
5. Copy the full error message

**Common errors you might see:**
- `Network Error` - Backend is not running
- `401 Unauthorized` - Not logged in or token expired
- `403 Forbidden` - Not an admin user
- `400 Bad Request` - Validation error (check the detail message)
- `500 Internal Server Error` - Backend error

---

## Step 2: Check Backend Logs

1. Look at the terminal where you're running `uvicorn`
2. Check for error messages when you try to create a teacher
3. Look for stack traces or exception details

**Common backend errors:**
- `Admin account is not associated with a school` - Admin needs a school_id
- `Email already exists` - Email is already in use (active user)
- Database connection errors
- Validation errors

---

## Step 3: Verify Your Admin Account

Make sure you're logged in as a **School Admin** (ADMIN role) with a `school_id`:

1. Check your user role in the dashboard
2. Verify you have a school assigned
3. If not, contact Super Admin to assign you to a school

---

## Step 4: Check Required Fields

When creating a teacher, make sure:
- ✅ **Name** is filled (required)
- ✅ **Email** is filled and valid format (required)
- ✅ **Subject** is optional (can be empty)

**Email format must be valid:**
- Must contain `@` symbol
- Must have domain (e.g., `@gmail.com`)
- Example: `teacher@example.com`

---

## Step 5: Test API Directly

Test the API endpoint directly using curl or Postman:

```bash
curl -X POST "http://localhost:8000/admin/teachers" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "name": "Test Teacher",
    "email": "test@example.com",
    "subject": "Mathematics"
  }'
```

Replace `YOUR_JWT_TOKEN` with your actual JWT token.

**To get your JWT token:**
1. Open browser Developer Tools (F12)
2. Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
3. Click **Local Storage** → `http://localhost:5173`
4. Find `token` key and copy its value

---

## Step 6: Common Issues and Solutions

### Issue 1: "Admin account is not associated with a school"

**Solution:**
- You need to be assigned to a school
- Contact Super Admin to assign you to a school
- Or check if your `school_id` is NULL in the database

### Issue 2: "Email already exists"

**Solution:**
- The email is already used by an active user
- Try a different email
- Or delete the existing user first (if you have permission)

### Issue 3: "Network Error" or "Failed to fetch"

**Solution:**
- Backend is not running
- Start backend: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Check if backend is accessible: http://localhost:8000/docs

### Issue 4: "401 Unauthorized"

**Solution:**
- You're not logged in
- Token expired - log out and log in again
- Check if JWT token is valid

### Issue 5: "403 Forbidden"

**Solution:**
- You're not logged in as ADMIN
- Check your user role
- Only School Admins can create teachers

### Issue 6: Database Connection Error

**Solution:**
- Check database is running
- Verify `.env` file has correct database credentials
- Check database connection string

---

## Step 7: Check Form Data

Make sure the form is sending correct data:

1. Open browser Developer Tools (F12)
2. Go to **Network** tab
3. Try creating a teacher
4. Find the `POST /admin/teachers` request
5. Click on it
6. Check **Payload** or **Request** tab
7. Verify the data being sent:
   ```json
   {
     "name": "Teacher Name",
     "email": "teacher@example.com",
     "subject": "Mathematics"
   }
   ```

---

## Step 8: Verify Backend Endpoint

1. Open: http://localhost:8000/docs
2. Find `POST /admin/teachers` endpoint
3. Click "Try it out"
4. Fill in the form:
   - name: "Test Teacher"
   - email: "test@example.com"
   - subject: "Math"
5. Click "Execute"
6. Check the response

**If it works in Swagger but not in frontend:**
- Check CORS settings
- Check API base URL in frontend
- Check authentication headers

---

## Still Having Issues?

1. **Check all error messages** (browser console + backend logs)
2. **Share the exact error message** you're seeing
3. **Share backend logs** when you try to create a teacher
4. **Verify backend is running** and accessible
5. **Check your user role and school_id**

---

## Quick Checklist

- [ ] Backend is running (`uvicorn` command is active)
- [ ] Frontend is running (`npm run dev`)
- [ ] You're logged in as ADMIN
- [ ] Your admin account has a `school_id`
- [ ] Email format is valid
- [ ] Name field is filled
- [ ] No duplicate email (active users only)
- [ ] Browser console shows no errors
- [ ] Backend logs show no errors
