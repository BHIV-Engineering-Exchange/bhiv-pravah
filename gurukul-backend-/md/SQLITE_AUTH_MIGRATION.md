# SQLite-Only Authentication Migration Guide

## ✅ Migration Complete!

Your application has been successfully migrated from Supabase authentication to SQLite-only authentication.

## What Changed

### Backend Changes

1. **New Authentication Endpoints** (`backend/app/routers/auth.py`):
   - `POST /api/v1/auth/register` - Register new users
   - `POST /api/v1/auth/login` - Login and get JWT token
   - `GET /api/v1/auth/me` - Get current user info (unchanged)

2. **Password Hashing**:
   - Uses `bcrypt` via `passlib` for secure password hashing
   - Passwords are hashed before storing in SQLite database

3. **JWT Token Generation**:
   - Tokens are generated using `python-jose` with HS256 algorithm
   - Tokens expire after 7 days (configurable in `config.py`)
   - Secret key stored in `JWT_SECRET_KEY` (change in production!)

4. **Updated `get_current_user`**:
   - Now verifies JWT tokens signed by our own backend
   - No longer depends on Supabase tokens

### Frontend Changes

1. **AuthContext** (`Frontend/src/contexts/AuthContext.jsx`):
   - Removed Supabase dependency
   - Now uses backend API endpoints for login/register
   - Stores JWT token in `localStorage` as `auth_token`
   - Automatically checks auth status on app load

2. **SignIn/SignUp Pages**:
   - Updated to use new backend API endpoints
   - Auto-redirects to appropriate dashboard after login/signup

3. **API Client** (`Frontend/src/utils/apiClient.js`):
   - Now reads token from `localStorage` instead of Supabase session
   - Automatically includes token in Authorization header

4. **Removed Supabase**:
   - `supabaseClient.js` is no longer needed (can be deleted)
   - All Supabase imports removed from frontend

## Configuration

### Backend Environment Variables

Add to your `.env` file:

```env
# JWT Secret Key (CHANGE THIS IN PRODUCTION!)
JWT_SECRET_KEY=your-secret-key-change-in-production

# JWT Token Expiration (optional, defaults to 7 days)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

**⚠️ IMPORTANT**: Generate a strong random secret key for production:
```python
import secrets
print(secrets.token_urlsafe(32))
```

### Frontend

No new environment variables needed. The frontend automatically uses the backend API URL from `config.js`.

## Database Schema

The User model already supports `hashed_password`:
- Existing users may have `hashed_password = NULL` (from Supabase era)
- New users will have hashed passwords stored
- The registration endpoint requires a password

## Migration Steps for Existing Users

If you have existing users in your database from Supabase:

1. **Option 1**: Ask users to reset their password (recommended)
   - They'll need to use "Forgot Password" (if implemented) or contact admin

2. **Option 2**: Manually set passwords for users
   ```python
   from passlib.context import CryptContext
   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
   hashed = pwd_context.hash("temporary_password")
   # Update user in database
   ```

## Testing

1. **Test Registration**:
   ```bash
   curl -X POST http://localhost:3000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test123","full_name":"Test User","role":"STUDENT"}'
   ```

2. **Test Login**:
   ```bash
   curl -X POST http://localhost:3000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test123"}'
   ```

3. **Test Protected Endpoint**:
   ```bash
   curl -X GET http://localhost:3000/api/v1/auth/me \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
   ```

## Security Notes

✅ **Implemented**:
- Password hashing with bcrypt
- JWT token signing and verification
- Token expiration
- Secure password storage

⚠️ **Recommended for Production**:
- Use HTTPS only
- Set a strong `JWT_SECRET_KEY`
- Implement rate limiting on login/register endpoints
- Add password strength requirements
- Implement password reset functionality
- Add email verification (optional)
- Consider refresh tokens for longer sessions

## Removing Supabase Package (Optional)

Once you've confirmed everything works, you can remove Supabase from frontend:

```bash
cd Frontend
npm uninstall @supabase/supabase-js
```

You can also delete:
- `Frontend/src/supabaseClient.js`
- `Frontend/test-supabase-connection.js` (if exists)

## Rollback Plan

If you need to rollback:
1. Restore previous `AuthContext.jsx` from git
2. Restore previous `auth.py` from git
3. Restore Supabase environment variables
4. Reinstall `@supabase/supabase-js` package

## Next Steps

1. ✅ Test registration and login flows
2. ✅ Verify protected endpoints work with new tokens
3. ✅ Update any documentation
4. ⚠️ Set strong `JWT_SECRET_KEY` in production
5. 🔄 Consider implementing password reset functionality
6. 🔄 Consider adding email verification

## Support

If you encounter issues:
1. Check backend logs for authentication errors
2. Verify JWT_SECRET_KEY is set correctly
3. Ensure database has `hashed_password` column
4. Check browser console for frontend errors
5. Verify API_BASE_URL is correct in frontend config

