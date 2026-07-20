import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { useAuth } from '../../context/AuthContext'
import { authStorage } from '../../utils/authStorage'

type AuthMode = 'login' | 'signup'
type UserRole = 'candidate' | 'recruiter' | 'client'

const roleConfig = {
  candidate: {
    title: 'Candidate',
    gradient: 'from-blue-500 to-cyan-500',
    redirectPath: '/candidate/dashboard',
  },
  recruiter: {
    title: 'Recruiter',
    gradient: 'from-emerald-500 to-teal-500',
    redirectPath: '/recruiter',
  },
  client: {
    title: 'Client',
    gradient: 'from-purple-500 to-pink-500',
    redirectPath: '/client',
  },
}

export default function AuthPage() {
  // ...existing code...
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  
  // Get initial mode from URL query parameter, default to 'login'
  const urlMode = searchParams.get('mode')
  const initialMode = (urlMode === 'signup' ? 'signup' : 'login') as AuthMode
  const [mode, setMode] = useState<AuthMode>(initialMode)
  const [isLoading, setIsLoading] = useState(false)
  
  // Role selection state (only for signup)
  const [selectedRole, setSelectedRole] = useState<UserRole>('candidate')
  
  // Sync mode with URL parameter when URL changes
  useEffect(() => {
    const currentUrlMode = searchParams.get('mode')
    if (currentUrlMode === 'signup' || currentUrlMode === 'login') {
      const newMode = currentUrlMode as AuthMode
      if (mode !== newMode) {
        setMode(newMode)
      }
    }
  }, [searchParams, mode])
  
  // Helper to change mode and update URL
  const handleModeChange = (newMode: AuthMode) => {
    setMode(newMode)
    setSearchParams({ mode: newMode }, { replace: true })
  }
  
  // State for form data
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    fullName: '',
    company: '',
    phone: '',
  })

  // State for validation errors
  const [errors, setErrors] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    fullName: '',
    company: '',
    phone: '',
  });

  // Validation functions
  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return emailRegex.test(email);
  };

  const validatePassword = (password: string): { isValid: boolean; message: string } => {
    if (password.length < 6) {
      return { isValid: false, message: 'Password must be at least 6 characters' };
    }
    if (!/(?=.*[a-z])(?=.*[A-Z])/.test(password)) {
      return { isValid: false, message: 'Password must contain at least one uppercase and one lowercase letter' };
    }
    if (!/(?=.*\d)/.test(password)) {
      return { isValid: false, message: 'Password must contain at least one number' };
    }
    if (!/(?=.*[@$!%*?&])/.test(password)) {
      return { isValid: false, message: 'Password must contain at least one special character (@$!%*?&)' };
    }
    return { isValid: true, message: '' };
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    if (name === 'role') {
      setSelectedRole(value as UserRole)
      // Clear company error when role changes
      if (name === 'role' && value !== 'client') {
        setErrors(prev => ({ ...prev, company: '' }));
      }
    } else {
      setFormData({ ...formData, [name]: value });
      
      // Clear specific error when user starts typing
      if (errors[name as keyof typeof errors]) {
        setErrors(prev => ({ ...prev, [name]: '' }));
      }
      
      // Real-time validation
      if (name === 'email') {
        if (value && !validateEmail(value)) {
          setErrors(prev => ({ ...prev, email: 'Please enter a valid email address' }));
        } else {
          setErrors(prev => ({ ...prev, email: '' }));
        }
      } else if (name === 'password') {
        if (value) {
          const passwordValidation = validatePassword(value);
          if (!passwordValidation.isValid) {
            setErrors(prev => ({ ...prev, password: passwordValidation.message }));
          } else {
            setErrors(prev => ({ ...prev, password: '' }));
          }
        } else {
          setErrors(prev => ({ ...prev, password: '' }));
        }
      } else if (name === 'confirmPassword') {
        if (value && value !== formData.password) {
          setErrors(prev => ({ ...prev, confirmPassword: 'Passwords do not match' }));
        } else {
          setErrors(prev => ({ ...prev, confirmPassword: '' }));
        }
      }
    }
  }

  const { signIn, signUp, userRole } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    // Clear previous errors
    setErrors({
      email: '',
      password: '',
      confirmPassword: '',
      fullName: '',
      company: '',
      phone: '',
    });

    // Perform comprehensive validation
    let hasErrors = false;
    const newErrors = { ...errors };

    // Validate email format
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
      hasErrors = true;
    } else if (!validateEmail(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
      hasErrors = true;
    }

    // Validate password
    if (!formData.password.trim()) {
      newErrors.password = 'Password is required';
      hasErrors = true;
    } else {
      const passwordValidation = validatePassword(formData.password);
      if (!passwordValidation.isValid) {
        newErrors.password = passwordValidation.message;
        hasErrors = true;
      }
    }

    if (mode === 'signup') {
      // Validate full name
      if (!formData.fullName.trim()) {
        newErrors.fullName = 'Full name is required';
        hasErrors = true;
      }

      // Validate company for client
      if (selectedRole === 'client' && !formData.company.trim()) {
        newErrors.company = 'Company name is required for clients';
        hasErrors = true;
      }

      // Validate confirm password
      if (!formData.confirmPassword.trim()) {
        newErrors.confirmPassword = 'Please confirm your password';
        hasErrors = true;
      } else if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
        hasErrors = true;
      }
    }

    // Set errors if any
    if (hasErrors) {
      setErrors(newErrors);
      toast.error('Please fix the validation errors before submitting');
      setIsLoading(false);
      return;
    }

    try {
      if (mode === 'signup') {
        // SIGNUP: Create account with the selected role
        const { error } = await signUp(formData.email, formData.password, {
          name: formData.fullName,
          role: selectedRole,
          company: formData.company || undefined,
          phone: formData.phone || undefined
        })
        
        if (error) {
          const errorMsg = error || '';
          
          // Handle duplicate email errors
          if (errorMsg.toLowerCase().includes('already registered') || 
              errorMsg.toLowerCase().includes('user already registered') ||
              errorMsg.toLowerCase().includes('already exists') ||
              errorMsg.toLowerCase().includes('email address is already') ||
              errorMsg.toLowerCase().includes('already been registered') ||
              errorMsg.toLowerCase().includes('duplicate') ||
              errorMsg.toLowerCase().includes('unique constraint')) {
            setErrors(prev => ({ ...prev, email: 'This email is already registered. Please use a different email or login instead.' }));
            toast.error('This email is already registered. Please use a different email or login instead.');
          } else if (errorMsg.toLowerCase().includes('network') || 
                     errorMsg.toLowerCase().includes('timeout') ||
                     errorMsg.toLowerCase().includes('server') ||
                     errorMsg.toLowerCase().includes('connection')) {
            toast.error('Network error. Please check your connection and try again.');
          } else {
            toast.error(errorMsg || 'Signup failed. Please try again.');
          }
          setIsLoading(false);
          return;
        }
        
        // Role is already stored by AuthContext - just verify
        const storedRole = authStorage.getItem('user_role') || selectedRole;
        
        console.log('✅ Signup successful! Role:', storedRole, 'Redirecting to:', roleConfig[storedRole as UserRole]?.redirectPath);
        toast.success(`Account created successfully as ${roleConfig[storedRole as UserRole]?.title || selectedRole}!`);
        setIsLoading(false);
        navigate(roleConfig[storedRole as UserRole]?.redirectPath || roleConfig[selectedRole].redirectPath);
      } else {
        // LOGIN: Authenticate and redirect based on user's role
        const { error } = await signIn(formData.email, formData.password);
        
        if (error) {
          const errorMsg = error || '';
          
          if (errorMsg.toLowerCase().includes('invalid credentials') || 
              errorMsg.toLowerCase().includes('incorrect') ||
              errorMsg.toLowerCase().includes('wrong') ||
              errorMsg.toLowerCase().includes('failed')) {
            setErrors(prev => ({ ...prev, email: 'Invalid email or password', password: 'Invalid email or password' }));
            toast.error('Invalid email or password. Please try again.');
          } else if (errorMsg.toLowerCase().includes('network') || 
                     errorMsg.toLowerCase().includes('timeout') ||
                     errorMsg.toLowerCase().includes('server') ||
                     errorMsg.toLowerCase().includes('connection')) {
            toast.error('Network error. Please check your connection and try again.');
          } else {
            toast.error(errorMsg || 'Login failed. Please check your credentials.');
          }
          setIsLoading(false);
          return;
        }
        
        // Get user's role from JWT token (stored by AuthContext during login)
        // AuthContext extracts role from token and stores it in localStorage
        const roleFromStorage = authStorage.getItem('user_role') as UserRole;
        const roleFromContext = userRole as UserRole;
        
        // Prioritize role from context (from JWT token), then localStorage
        // Only default to candidate if neither is available
        let finalRole: UserRole = (roleFromContext || roleFromStorage) as UserRole;
        
        // Ensure role is valid (must be one of the three roles)
        if (!finalRole || !['candidate', 'recruiter', 'client'].includes(finalRole)) {
          console.warn('⚠️ Invalid or missing role, defaulting to candidate. Role from context:', roleFromContext, 'Role from storage:', roleFromStorage);
          finalRole = 'candidate';
        }
        
        console.log('🚀 Login: User role from token:', finalRole, 'Redirecting to:', roleConfig[finalRole].redirectPath);
        toast.success(`Login successful as ${roleConfig[finalRole].title}!`);
        setIsLoading(false);
        navigate(roleConfig[finalRole].redirectPath);
      }
    } catch (err: any) {
      console.error('Authentication error:', err);
      
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        toast.error('Network error. Please check your connection and try again.');
      } else {
        toast.error(err.message || 'An unexpected error occurred. Please try again.');
      }
      setIsLoading(false);
    }
  }

  // Fixed blue color scheme for auth page
  const fixedGradient = 'from-blue-500 to-cyan-500'

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center px-4 py-8">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className={`absolute top-20 right-20 w-[500px] h-[500px] bg-gradient-to-br ${fixedGradient} rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob`} />
        <div className="absolute bottom-20 left-20 w-[400px] h-[400px] bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000" />
        <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-br ${fixedGradient} rounded-full mix-blend-multiply filter blur-3xl opacity-5`} />
      </div>

      {/* Centered Content */}
      <div className={`relative z-10 w-full ${mode === 'signup' ? 'max-w-2xl' : 'max-w-md'}`}>
        {/* Logo & Branding */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-3 mb-6 group">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-400 via-purple-500 to-pink-500 p-0.5 group-hover:scale-110 transition-transform shadow-lg shadow-purple-500/20">
              <div className="w-full h-full rounded-2xl bg-slate-900 flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
            <span className="text-2xl font-bold block">
              <span className={`bg-gradient-to-r ${fixedGradient} bg-clip-text text-transparent`}>
                Sampada
              </span>
              <span className="text-gray-400 text-sm font-normal block mt-0.5">HR Recruitment System</span>
            </span>
          </div>

          {/* Heading */}
          <h1 className="text-3xl font-bold text-white mb-2">
            {mode === 'login' ? (
              <>Welcome <span className={`bg-gradient-to-r ${fixedGradient} bg-clip-text text-transparent`}>Back!</span></>
            ) : (
              <>Create <span className={`bg-gradient-to-r ${fixedGradient} bg-clip-text text-transparent`}>Account</span></>
            )}
          </h1>
          <p className="text-gray-400">
            {mode === 'login'
              ? 'Sign in to continue to your dashboard'
              : 'Join the AI-powered recruitment platform'}
          </p>
        </div>

        {/* Form Card */}
        <div className={`bg-slate-800/60 backdrop-blur-xl border border-slate-700/50 rounded-3xl p-8 shadow-2xl`}>
           {/* Mode Toggle */}
           <div className="flex bg-slate-900/60 rounded-2xl p-1.5 mb-6">
             <button
               type="button"
               onClick={() => handleModeChange('login')}
               className={`flex-1 py-3 px-4 rounded-xl font-semibold text-sm transition-all ${
                 mode === 'login'
                   ? `bg-gradient-to-r ${fixedGradient} text-white shadow-lg`
                   : 'text-gray-400 hover:text-white'
               }`}
             >
               Sign In
             </button>
             <button
               type="button"
               onClick={() => handleModeChange('signup')}
               className={`flex-1 py-3 px-4 rounded-xl font-semibold text-sm transition-all ${
                 mode === 'signup'
                   ? `bg-gradient-to-r ${fixedGradient} text-white shadow-lg`
                   : 'text-gray-400 hover:text-white'
               }`}
             >
               Sign Up
             </button>
           </div>

          <form onSubmit={handleSubmit}>
            {/* ========== SIGNUP FORM ========== */}
            {mode === 'signup' && (
              <div className="space-y-4 mb-4">
                {/* Role Selection - Only in Signup */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Select Role <span className="text-red-400">*</span>
                  </label>
                  <select
                    name="role"
                    value={selectedRole}
                    onChange={handleInputChange}
                    className={`w-full px-4 py-3 bg-slate-900/60 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-transparent focus:ring-2 focus:ring-blue-500 transition-all`}
                    required
                  >
                    <option value="candidate">Candidate</option>
                    <option value="recruiter">Recruiter (HR)</option>
                    <option value="client">Client</option>
                  </select>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Full Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Full Name <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="text"
                      name="fullName"
                      value={formData.fullName}
                      onChange={handleInputChange}
                      placeholder="John Doe"
                      className={`w-full px-4 py-3 bg-slate-900/60 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-transparent focus:ring-2 focus:ring-blue-500 transition-all ${
                        errors.fullName ? 'border-red-500' : 'border-slate-700'
                      }`}
                      required
                    />
                    {errors.fullName && (
                      <p className="mt-1 text-sm text-red-400">{errors.fullName}</p>
                    )}
                  </div>

                  {/* Email */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Email Address <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleInputChange}
                      placeholder="john@example.com"
                      className={`w-full px-4 py-3 bg-slate-900/60 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-transparent focus:ring-2 focus:ring-blue-500 transition-all ${
                        errors.email ? 'border-red-500' : 'border-slate-700'
                      }`}
                      required
                    />
                    {errors.email && (
                      <p className="mt-1 text-sm text-red-400">{errors.email}</p>
                    )}
                  </div>

                  {/* Phone */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Phone Number <span className="text-gray-500 text-xs">(Optional)</span>
                    </label>
                    <input
                      type="tel"
                      name="phone"
                      value={formData.phone}
                      onChange={handleInputChange}
                      placeholder="+1 (555) 123-4567"
                      className={`w-full px-4 py-3 bg-slate-900/60 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-transparent focus:ring-2 focus:ring-blue-500 transition-all ${
                        errors.phone ? 'border-red-500' : 'border-slate-700'
                      }`}
                    />
                    {errors.phone && (
                      <p className="mt-1 text-sm text-red-400">{errors.phone}</p>
                    )}
                  </div>

                  {/* Company - Only for recruiter/client */}
                  {(selectedRole === 'recruiter' || selectedRole === 'client') && (
                    <div>
                      <label className="block text-sm font-medium text-gray-300 mb-2">
                        Company Name {selectedRole === 'client' && <span className="text-red-400">*</span>}
                      </label>
                      <input
                        type="text"
                        name="company"
                        value={formData.company}
                        onChange={handleInputChange}
                        placeholder={selectedRole === 'client' ? "Enter your company name" : "Acme Inc."}
                        className={`w-full px-4 py-3 bg-slate-900/60 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-transparent focus:ring-2 focus:ring-blue-500 transition-all ${
                          errors.company ? 'border-red-500' : 'border-slate-700'
                        }`}
                        required={selectedRole === 'client'}
                      />
                      {errors.company && (
                        <p className="mt-1 text-sm text-red-400">{errors.company}</p>
                      )}
                      {selectedRole === 'client' && (
                        <p className="mt-1 text-xs text-gray-400">
                          Required for proper identification in job postings
                        </p>
                      )}
                    </div>
                  )}

                  {/* Password */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Password <span className="text-red-400">*</span>
                    </label>
                    <div className="relative">
                      <input
                        type={showPassword ? 'text' : 'password'}
                        name="password"
                        value={formData.password}
                        onChange={handleInputChange}
                        placeholder="••••••••"
                        className={`w-full px-4 py-3 pr-10 bg-slate-900/60 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-transparent focus:ring-2 focus:ring-blue-500 transition-all ${
                          errors.password ? 'border-red-500' : 'border-slate-700'
                        }`}
                        required
                      />
                      <button
                        type="button"
                        tabIndex={-1}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-200 focus:outline-none"
                        onClick={() => setShowPassword((prev) => !prev)}
                        aria-label={showPassword ? 'Hide password' : 'Show password'}
                      >
                        {showPassword ? (
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-5.523 0-10-4.477-10-10 0-1.657.402-3.22 1.125-4.575M15 12a3 3 0 11-6 0 3 3 0 016 0zm6.875-4.575A9.956 9.956 0 0122 9c0 5.523-4.477 10-10 10a9.956 9.956 0 01-4.575-1.125" /></svg>
                        ) : (
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0zm2.828-2.828A9.956 9.956 0 0122 12c0 5.523-4.477 10-10 10S2 17.523 2 12c0-2.21.896-4.21 2.343-5.657M9.88 9.88a3 3 0 104.24 4.24" /></svg>
                        )}
                      </button>
                    </div>
                    {errors.password && (
                      <p className="mt-1 text-sm text-red-400">{errors.password}</p>
                    )}
                  </div>

                  {/* Confirm Password */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Confirm Password <span className="text-red-400">*</span>
                    </label>
                    <div className="relative">
                      <input
                        type={showConfirmPassword ? 'text' : 'password'}
                        name="confirmPassword"
                        value={formData.confirmPassword}
                        onChange={handleInputChange}
                        placeholder="••••••••"
                        className={`w-full px-4 py-3 pr-10 bg-slate-900/60 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-transparent focus:ring-2 focus:ring-blue-500 transition-all ${
                          errors.confirmPassword ? 'border-red-500' : 'border-slate-700'
                        }`}
                        required
                      />
                      <button
                        type="button"
                        tabIndex={-1}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-200 focus:outline-none"
                        onClick={() => setShowConfirmPassword((prev) => !prev)}
                        aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
                      >
                        {showConfirmPassword ? (
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-5.523 0-10-4.477-10-10 0-1.657.402-3.22 1.125-4.575M15 12a3 3 0 11-6 0 3 3 0 016 0zm6.875-4.575A9.956 9.956 0 0122 9c0 5.523-4.477 10-10 10a9.956 9.956 0 01-4.575-1.125" /></svg>
                        ) : (
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0zm2.828-2.828A9.956 9.956 0 0122 12c0 5.523-4.477 10-10 10S2 17.523 2 12c0-2.21.896-4.21 2.343-5.657M9.88 9.88a3 3 0 104.24 4.24" /></svg>
                        )}
                      </button>
                    </div>
                    {errors.confirmPassword && (
                      <p className="mt-1 text-sm text-red-400">{errors.confirmPassword}</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* ========== LOGIN FORM ========== */}
            {mode === 'login' && (
              <div className="space-y-4">
                {/* Email */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    placeholder="john@example.com"
                    className={`w-full px-4 py-3 bg-slate-900/60 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-transparent focus:ring-2 focus:ring-blue-500 transition-all ${
                      errors.email ? 'border-red-500' : 'border-slate-700'
                    }`}
                    required
                  />
                  {errors.email && (
                    <p className="mt-1 text-sm text-red-400">{errors.email}</p>
                  )}
                </div>

                {/* Password */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? 'text' : 'password'}
                      name="password"
                      value={formData.password}
                      onChange={handleInputChange}
                      placeholder="••••••••"
                      className={`w-full px-4 py-3 pr-10 bg-slate-900/60 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-transparent focus:ring-2 focus:ring-blue-500 transition-all ${
                        errors.password ? 'border-red-500' : 'border-slate-700'
                      }`}
                      required
                    />
                    <button
                      type="button"
                      tabIndex={-1}
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-200 focus:outline-none"
                      onClick={() => setShowPassword((prev) => !prev)}
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                    >
                      {showPassword ? (
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-5.523 0-10-4.477-10-10 0-1.657.402-3.22 1.125-4.575M15 12a3 3 0 11-6 0 3 3 0 016 0zm6.875-4.575A9.956 9.956 0 0122 9c0 5.523-4.477 10-10 10a9.956 9.956 0 01-4.575-1.125" /></svg>
                      ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0zm2.828-2.828A9.956 9.956 0 0122 12c0 5.523-4.477 10-10 10S2 17.523 2 12c0-2.21.896-4.21 2.343-5.657M9.88 9.88a3 3 0 104.24 4.24" /></svg>
                      )}
                    </button>
                  </div>
                  {errors.password && (
                    <p className="mt-1 text-sm text-red-400">{errors.password}</p>
                  )}
                </div>

                {/* Forgot Password */}
                <div className="flex justify-end">
                  <button
                    type="button"
                    className="text-sm font-medium bg-gradient-to-r from-blue-500 to-cyan-500 bg-clip-text text-transparent hover:opacity-80 transition-opacity"
                  >
                    Forgot password?
                  </button>
                </div>
              </div>
            )}

            {/* Terms Checkbox - Signup only */}
            {mode === 'signup' && (
              <div className="flex items-start gap-3 mb-4">
                <input
                  type="checkbox"
                  id="terms"
                  className="w-4 h-4 mt-1 rounded border-slate-600 bg-slate-900/60 text-blue-500 focus:ring-offset-0"
                  required
                />
                <label htmlFor="terms" className="text-sm text-gray-400">
                  I agree to the{' '}
                  <button type="button" className="bg-gradient-to-r from-blue-500 to-cyan-500 bg-clip-text text-transparent font-medium">
                    Terms
                  </button>{' '}
                  and{' '}
                  <button type="button" className="bg-gradient-to-r from-blue-500 to-cyan-500 bg-clip-text text-transparent font-medium">
                    Privacy Policy
                  </button>
                </label>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className={`w-full py-3.5 px-6 bg-gradient-to-r ${fixedGradient} text-white font-bold rounded-xl hover:opacity-90 hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-6`}
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Processing...
                </>
              ) : (
                <>
                  {mode === 'login' ? 'Sign In' : 'Create Account'}
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </>
              )}
            </button>

            {/* Divider */}
            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-700" />
              </div>
              <div className="relative flex justify-center">
                <span className="px-4 bg-slate-800/60 text-gray-500 text-sm">Or continue with</span>
              </div>
            </div>

            {/* Social Login */}
            <div className="flex justify-center">
              <button
                type="button"
                className="flex items-center justify-center gap-2 py-3 px-8 bg-slate-900/60 border border-slate-700 rounded-xl text-white hover:bg-slate-700/60 hover:border-slate-600 transition-all group"
              >
                <svg className="w-5 h-5 group-hover:scale-110 transition-transform" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
                </svg>
                <span className="font-medium text-sm">Continue with Google</span>
              </button>
            </div>
          </form>

           {/* Switch Mode */}
           <p className="text-center text-gray-400 text-sm mt-6">
             {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
             <button
               type="button"
               onClick={() => handleModeChange(mode === 'login' ? 'signup' : 'login')}
               className="font-semibold bg-gradient-to-r from-blue-500 to-cyan-500 bg-clip-text text-transparent hover:opacity-80 transition-opacity"
             >
               {mode === 'login' ? 'Sign up' : 'Sign in'}
             </button>
           </p>
        </div>
      </div>
    </div>
  )
}
