# Authentication System Documentation

## Overview
Complete authentication system integrated with Supabase for the AI Agent Logistics System. Includes email/password authentication, OAuth social login (Google, GitHub), password recovery, email verification, and protected routes.

## 🚀 Features

### ✅ Implemented Features
- **Email/Password Authentication**
  - User registration with email verification
  - Secure login with session management
  - Password strength validation
  - Remember me functionality

- **OAuth Social Login**
  - Google Sign-In
  - GitHub Sign-In
  - Automatic profile creation

- **Password Management**
  - Forgot password flow
  - Secure password reset via email
  - Password strength indicator
  - Password visibility toggle

- **User Profile Management**
  - Auto-create user profiles on signup
  - Store first name, last name, company name
  - Display user info in header
  - User avatar with initials

- **Security Features**
  - PKCE flow for OAuth
  - Auto-refresh tokens
  - Persistent sessions
  - Protected routes with redirect
  - Row Level Security (RLS) ready

- **UI/UX Features**
  - Responsive design (mobile, tablet, desktop)
  - Loading states and spinners
  - Error handling with alerts
  - Success confirmations
  - Gradient design system
  - Form validation

## 📁 File Structure

```
frontend/
├── .env                                    # Supabase credentials
├── src/
│   ├── lib/
│   │   └── supabase.js                    # Supabase client config
│   ├── services/
│   │   └── auth/
│   │       └── authService.js             # Auth API wrapper
│   ├── context/
│   │   └── AuthContext.jsx                # Global auth state
│   ├── components/
│   │   ├── ProtectedRoute.jsx             # Route guard
│   │   ├── auth/
│   │   │   ├── AuthLayout.jsx             # Auth page wrapper
│   │   │   ├── PasswordStrength.jsx       # Password indicator
│   │   │   └── SocialLogin.jsx            # OAuth buttons
│   │   └── layout/
│   │       └── Header.jsx                 # Updated with user menu
│   └── pages/
│       └── auth/
│           ├── Login.jsx                  # Login page
│           ├── Signup.jsx                 # Registration page
│           ├── ForgotPassword.jsx         # Password reset request
│           ├── ResetPassword.jsx          # Password update
│           ├── VerifyEmail.jsx            # Email verification
│           └── OAuthCallback.jsx          # OAuth redirect handler
```

## 🔧 Configuration

### 1. Supabase Setup

**Environment Variables (`.env`):**
```env
VITE_SUPABASE_URL=https://lslfjbnbcfhrlmloebax.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Supabase Dashboard Settings:**
1. **Authentication** → **Providers**
   - Enable Email provider
   - Enable Google OAuth (add Client ID & Secret)
   - Enable GitHub OAuth (add Client ID & Secret)

2. **Authentication** → **URL Configuration**
   - Site URL: `http://localhost:5173` (development)
   - Redirect URLs:
     - `http://localhost:5173/auth/callback`
     - `https://yourdomain.com/auth/callback` (production)

3. **Authentication** → **Email Templates**
   - Customize confirmation email
   - Customize password reset email
   - Set redirect URL: `{{ .SiteURL }}/auth/verify-email?token={{ .Token }}`

### 2. Database Schema

**Required Tables:**

```sql
-- Users table (auto-created by Supabase Auth)
-- auth.users

-- Profiles table (create this)
CREATE TABLE profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  first_name TEXT,
  last_name TEXT,
  company_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view own profile"
  ON profiles FOR SELECT
  USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
  ON profiles FOR INSERT
  WITH CHECK (auth.uid() = id);
```

**Trigger for auto-updating updated_at:**
```sql
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();
```

## 🎯 Usage

### Basic Authentication Flow

**1. Signup:**
```javascript
import { useAuth } from '@/context/AuthContext';

function SignupComponent() {
  const { signup } = useAuth();
  
  const handleSignup = async (e) => {
    e.preventDefault();
    await signup({
      email: 'user@example.com',
      password: 'SecurePass123!',
      firstName: 'John',
      lastName: 'Doe',
      companyName: 'Acme Corp'
    });
    // User will receive verification email
  };
}
```

**2. Login:**
```javascript
import { useAuth } from '@/context/AuthContext';

function LoginComponent() {
  const { login } = useAuth();
  
  const handleLogin = async (e) => {
    e.preventDefault();
    await login('user@example.com', 'SecurePass123!');
    // Redirects to dashboard
  };
}
```

**3. OAuth Login:**
```javascript
import { useAuth } from '@/context/AuthContext';

function OAuthComponent() {
  const { loginWithOAuth } = useAuth();
  
  const handleGoogleLogin = async () => {
    await loginWithOAuth('google');
    // Redirects to Google, then back to /auth/callback
  };
}
```

**4. Password Reset:**
```javascript
import { useAuth } from '@/context/AuthContext';

function ForgotPasswordComponent() {
  const { resetPassword } = useAuth();
  
  const handleReset = async (e) => {
    e.preventDefault();
    await resetPassword('user@example.com');
    // User receives reset email
  };
}
```

**5. Protected Routes:**
```javascript
import ProtectedRoute from '@/components/ProtectedRoute';

function App() {
  return (
    <Routes>
      <Route path="/auth/login" element={<Login />} />
      <Route path="/" element={
        <ProtectedRoute>
          <Dashboard />
        </ProtectedRoute>
      } />
    </Routes>
  );
}
```

### Accessing Auth State

```javascript
import { useAuth } from '@/context/AuthContext';

function UserProfile() {
  const { user, profile, isAuthenticated, loading, logout } = useAuth();
  
  if (loading) return <div>Loading...</div>;
  if (!isAuthenticated) return <div>Please log in</div>;
  
  return (
    <div>
      <h1>Welcome, {profile.first_name}!</h1>
      <p>Email: {user.email}</p>
      <button onClick={logout}>Sign Out</button>
    </div>
  );
}
```

## 🔐 Security Best Practices

### Implemented
✅ PKCE flow for OAuth
✅ Auto-refresh tokens
✅ Secure session storage
✅ Password strength validation
✅ Email verification required
✅ Protected route guards
✅ Error message sanitization

### Recommended Additional Steps
1. **Enable RLS on all tables**
   ```sql
   ALTER TABLE your_table ENABLE ROW LEVEL SECURITY;
   ```

2. **Add rate limiting** (Supabase Enterprise)
   - Limit signup attempts
   - Limit password reset requests

3. **Configure SMTP** (for production emails)
   - Use custom SMTP server
   - Customize email templates
   - Add company branding

4. **Add MFA** (Multi-Factor Authentication)
   ```javascript
   const { data } = await supabase.auth.mfa.enroll({
     factorType: 'totp'
   });
   ```

5. **Monitor auth events**
   ```javascript
   supabase.auth.onAuthStateChange((event, session) => {
     console.log('Auth event:', event);
     // Track login, logout, token refresh
   });
   ```

## 🧪 Testing

### Manual Testing Checklist

**Signup Flow:**
- [ ] Register with email/password
- [ ] Receive verification email
- [ ] Click verification link
- [ ] Redirected to login
- [ ] Profile created in database

**Login Flow:**
- [ ] Login with verified email
- [ ] See user info in header
- [ ] Session persists on refresh
- [ ] Remember me works

**OAuth Flow:**
- [ ] Click Google login
- [ ] Authorize with Google
- [ ] Redirected to dashboard
- [ ] Profile auto-created

**Password Reset:**
- [ ] Request password reset
- [ ] Receive reset email
- [ ] Click reset link
- [ ] Enter new password
- [ ] Login with new password

**Protected Routes:**
- [ ] Unauthenticated → redirects to login
- [ ] After login → can access dashboard
- [ ] After logout → redirected to login

**UI/UX:**
- [ ] Mobile responsive
- [ ] Error messages display
- [ ] Loading states work
- [ ] Success messages show
- [ ] Form validation works

## 🐛 Troubleshooting

### Common Issues

**1. "Invalid login credentials"**
- Check if email is verified
- Verify password is correct
- Check Supabase dashboard for user status

**2. Email verification not working**
- Check Supabase email settings
- Verify redirect URL is correct
- Check spam folder
- Enable email confirmations in Supabase

**3. OAuth not working**
- Verify OAuth credentials in Supabase
- Check redirect URLs match
- Ensure provider is enabled
- Check browser popup blockers

**4. "User already registered"**
- Check if user exists in Supabase
- Delete user from dashboard if needed
- Use different email address

**5. Session not persisting**
- Check localStorage is enabled
- Verify Supabase client config
- Check browser privacy settings

**6. Profile not loading**
- Check profiles table exists
- Verify RLS policies
- Check foreign key constraint
- Inspect network requests

## 📊 Monitoring

### Key Metrics to Track

1. **Authentication Success Rate**
   ```javascript
   // Track in analytics
   loginAttempts / successfulLogins
   ```

2. **Session Duration**
   ```javascript
   supabase.auth.onAuthStateChange((event, session) => {
     if (event === 'SIGNED_OUT') {
       const duration = Date.now() - loginTime;
       analytics.track('Session Duration', { duration });
     }
   });
   ```

3. **OAuth vs Email Signup**
   - Track which method users prefer
   - Optimize UX accordingly

4. **Password Reset Requests**
   - High rate may indicate UX issues
   - Consider social login

## 🚀 Deployment

### Production Checklist

**Environment Variables:**
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-production-key
```

**Supabase Settings:**
- [ ] Update Site URL to production domain
- [ ] Add production redirect URLs
- [ ] Configure custom SMTP (optional)
- [ ] Enable rate limiting
- [ ] Set up monitoring
- [ ] Configure custom email templates

**Frontend Deployment:**
- [ ] Build: `npm run build`
- [ ] Set environment variables
- [ ] Deploy to hosting (Vercel, Netlify, etc.)
- [ ] Test all auth flows on production

**Security:**
- [ ] Enable RLS on all tables
- [ ] Review API policies
- [ ] Set up backup procedures
- [ ] Configure monitoring/alerts
- [ ] Add CSP headers

## 📚 API Reference

### AuthContext Methods

```typescript
interface AuthContextType {
  // State
  user: User | null;
  session: Session | null;
  profile: Profile | null;
  loading: boolean;
  isAuthenticated: boolean;
  
  // Methods
  login(email: string, password: string): Promise<void>;
  signup(data: SignupData): Promise<void>;
  loginWithOAuth(provider: 'google' | 'github'): Promise<void>;
  logout(): Promise<void>;
  resetPassword(email: string): Promise<void>;
  updatePassword(newPassword: string): Promise<void>;
  updateProfile(data: Partial<Profile>): Promise<void>;
}
```

### Auth Service Methods

```typescript
// Sign up with email
signUp(email, password, userData): Promise<{ user, session }>

// Sign in with email
signIn(email, password): Promise<{ user, session }>

// OAuth sign in
signInWithOAuth(provider): Promise<{ url }>

// Sign out
signOut(): Promise<void>

// Password reset request
resetPassword(email): Promise<void>

// Update password
updatePassword(newPassword): Promise<void>

// Profile management
createUserProfile(userId, profileData): Promise<Profile>
getUserProfile(userId): Promise<Profile>
updateUserProfile(userId, updates): Promise<Profile>
```

## 🎨 Customization

### Styling
All auth pages use the design system from `tailwind.config.js`:
- `gradient-primary` - Main call-to-action buttons
- `gradient-secondary` - Feature highlights
- `gradient-accent` - Special elements

### Email Templates
Customize in Supabase Dashboard → Authentication → Email Templates:
- Confirmation email
- Password reset email
- Magic link email

### Branding
Update `AuthLayout.jsx`:
```javascript
// Change logo, title, tagline
<h1 className="text-3xl font-bold">Your Company</h1>
<p className="text-lg text-muted-foreground">Your tagline</p>
```

## 📞 Support

For issues or questions:
1. Check this documentation
2. Review Supabase docs: https://supabase.com/docs/guides/auth
3. Check browser console for errors
4. Inspect network requests
5. Review Supabase dashboard logs

## 🔄 Updates & Maintenance

### Regular Tasks
- [ ] Review Supabase logs weekly
- [ ] Monitor authentication metrics
- [ ] Update dependencies monthly
- [ ] Test auth flows after updates
- [ ] Backup database regularly

### Version History
- **v1.0.0** - Initial implementation with email/password, OAuth, password reset, email verification

---

**Built with ❤️ using React, Supabase, and Tailwind CSS**
