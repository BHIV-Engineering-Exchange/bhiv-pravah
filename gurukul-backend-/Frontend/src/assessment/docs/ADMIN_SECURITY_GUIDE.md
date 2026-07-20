# Admin Security Guide

## Current Setup: Environment Variables

Your admin credentials are now stored securely in environment variables instead of being hardcoded. This provides several benefits:

### ✅ Current Benefits
- **No hardcoded credentials** in your source code
- **Easy to change** without code deployment
- **Environment-specific** credentials (dev vs production)
- **Not committed to git** (`.env.local` is gitignored)

### 🔧 How to Change Credentials

Edit your `.env.local` file:
```env
# Change these values to your desired credentials
VITE_ADMIN_USERNAME=your_new_username
VITE_ADMIN_PASSWORD=your_new_secure_password
```

Then restart your development server: `npm run dev`

## Future Security Options

### Option 1: Keep Environment Variables (Current)
**Best for:** Simple setups, single admin user, development

**Pros:**
- Simple to implement and maintain
- Easy to change credentials
- No database complexity

**Cons:**
- Single admin user only
- Credentials visible to anyone with server access
- No password hashing

### Option 2: Upgrade to Supabase Database Storage
**Best for:** Production use, multiple admins, enhanced security

**Benefits:**
- Multiple admin users
- Password hashing
- User management features
- Audit trails
- Role-based permissions

**Implementation:** Would require creating an `admin_users` table in Supabase with proper authentication flow.

### Option 3: Integrate with Supabase Auth
**Best for:** Full-featured authentication system

**Benefits:**
- Built-in user management
- Password reset functionality
- Email verification
- Social login options
- Enterprise-grade security

## Security Best Practices

### For Current Setup:
1. **Change default credentials** immediately
2. **Use strong passwords** (12+ characters, mixed case, numbers, symbols)
3. **Keep `.env.local` secure** and never commit it to git
4. **Use different credentials** for development vs production

### General Recommendations:
1. **Regular password rotation** (every 3-6 months)
2. **Monitor admin access** through application logs
3. **Use HTTPS** in production
4. **Implement session timeouts**
5. **Consider two-factor authentication** for production

## Migration Path

If you want to upgrade to database-stored credentials later:

1. **Phase 1** (Current): Environment variables ✅
2. **Phase 2**: Move to Supabase table with hashed passwords
3. **Phase 3**: Full Supabase Auth integration

Each phase can be implemented independently without breaking existing functionality.

## Quick Security Checklist

- [ ] Changed default admin credentials in `.env.local`
- [ ] Verified `.env.local` is not committed to git
- [ ] Using strong, unique passwords
- [ ] Planning for production credential management
- [ ] Considering future authentication needs

---

**Need help upgrading to database storage?** Let me know and I can implement Option 2 or 3 for enhanced security.
