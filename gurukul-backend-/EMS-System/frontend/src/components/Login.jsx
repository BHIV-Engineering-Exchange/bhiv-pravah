import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useDemo } from '../context/DemoContext';
import { authAPI, schoolsAPI } from '../services/api';

const demoCredentials = [
  { role: 'Super Admin', email: 'blackholeinfiverse48@gmail.com', password: 'superadmin123', icon: '👑', color: '#A7F305' },
  { role: 'School Admin', email: 'admin@demo.com', password: 'demo123', icon: '🏫', color: '#06D6A0' },
  { role: 'Teacher', email: 'teacher@demo.com', password: 'demo123', icon: '👨‍🏫', color: '#6C63FF' },
  { role: 'Student', email: 'student@demo.com', password: 'demo123', icon: '🎓', color: '#FF6B9D' },
  { role: 'Parent', email: 'parent@demo.com', password: 'demo123', icon: '👨‍👩‍👧', color: '#FFD93D' },
];

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const { isDemoMode, toggleDemoMode } = useDemo();
  const navigate = useNavigate();

  // Registration states
  const [isRegistering, setIsRegistering] = useState(false);
  const [schools, setSchools] = useState([]);
  const [registerName, setRegisterName] = useState('');
  const [registerEmail, setRegisterEmail] = useState('');
  const [registerPassword, setRegisterPassword] = useState('');
  const [registerRole, setRegisterRole] = useState('STUDENT');
  const [registerSchoolId, setRegisterSchoolId] = useState('');
  const [registerSuccess, setRegisterSuccess] = useState('');

  // Fetch schools on switching to register mode
  useEffect(() => {
    if (isRegistering) {
      const fetchSchools = async () => {
        try {
          const schoolList = await schoolsAPI.getPublicList();
          setSchools(schoolList);
          if (schoolList.length > 0) {
            setRegisterSchoolId(schoolList[0].id.toString());
          }
        } catch (err) {
          console.error('Failed to load schools:', err);
        }
      };
      fetchSchools();
    }
  }, [isRegistering]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (email.toLowerCase().endsWith('@demo.com') && !isDemoMode) {
      setError('This is a demo account. Please enable "DEMO MODE" below the login button to use these credentials.');
      setLoading(false);
      return;
    }

    const result = await login(email, password);

    if (result.success) {
      navigate('/dashboard');
    } else {
      let errorMessage = result.message;

      // Helpful hint for race conditions during startup/deployment
      if (isDemoMode && email.toLowerCase().endsWith('@demo.com') && (errorMessage.includes('Incorrect') || errorMessage.includes('401'))) {
        errorMessage = "Demo login failed. If the system was just restarted, please wait 3-5 seconds for initialization and try again.";
      }

      setError(errorMessage);
    }

    setLoading(false);
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');
    setRegisterSuccess('');
    setLoading(true);

    try {
      const userData = {
        name: registerName,
        email: registerEmail,
        password: registerPassword,
        role: registerRole,
        school_id: registerRole === 'SUPER_ADMIN' ? null : (registerSchoolId ? parseInt(registerSchoolId) : null)
      };

      await authAPI.register(userData);
      
      setRegisterSuccess('Account created successfully! Auto-logging you in...');
      
      // Auto login
      setTimeout(async () => {
        const result = await login(registerEmail, registerPassword);
        if (result.success) {
          navigate('/dashboard');
        } else {
          setIsRegistering(false);
          setEmail(registerEmail);
          setPassword(registerPassword);
          setRegisterSuccess('');
          setLoading(false);
        }
      }, 1500);

    } catch (err) {
      const errMsg = err.response?.data?.detail || err.message || 'Registration failed. Please try again.';
      setError(errMsg);
      setLoading(false);
    }
  };

  const handleQuickLogin = async (cred) => {
    setEmail(cred.email);
    setPassword(cred.password);
    setError('');
    setLoading(true);
    
    const result = await login(cred.email, cred.password);
    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.message);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-dark-bg flex items-center justify-center px-4 relative overflow-hidden py-12">
      {/* Background gradient orbs */}
      <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-accent-green/5 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[400px] h-[400px] rounded-full bg-accent-blue/5 blur-[120px] pointer-events-none" />

      <div className="max-w-md w-full animate-fade-in relative z-10">
        {/* Card — Glassmorphism */}
        <div className="bg-[#1A1A2E]/80 backdrop-blur-xl border border-[#2A2A3E] rounded-3xl p-8 shadow-2xl">
          <div className="text-center mb-6">
            <h1 className="heading-serif text-4xl mb-2 tracking-tight">
              Gurukul
            </h1>
            <p className="text-gray-400 text-sm">School Management System</p>
          </div>

          {error && (
            <div className="error-box mb-6">
              <p>{error}</p>
            </div>
          )}

          {registerSuccess && (
            <div className="success-box mb-6">
              <p>{registerSuccess}</p>
            </div>
          )}

          {!isRegistering ? (
            /* LOGIN FORM */
            <>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="email" className="block text-[10px] font-semibold text-gray-400 mb-1.5 uppercase tracking-wider">
                    Email Address
                  </label>
                  <input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="input-dark"
                    placeholder="Enter your email"
                  />
                </div>

                <div>
                  <label htmlFor="password" className="block text-[10px] font-semibold text-gray-400 mb-1.5 uppercase tracking-wider">
                    Password
                  </label>
                  <input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="input-dark"
                    placeholder="Enter your password"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full btn-primary py-3 text-base mt-2"
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <span className="inline-block w-4 h-4 border-2 border-dark-bg/30 border-t-dark-bg rounded-full animate-spin" />
                      Logging in...
                    </span>
                  ) : 'Login'}
                </button>
              </form>

              {/* Toggle to Register */}
              <div className="mt-4 text-center">
                <button
                  onClick={() => {
                    setIsRegistering(true);
                    setError('');
                  }}
                  className="text-xs text-accent-green hover:underline font-medium bg-transparent border-none cursor-pointer"
                >
                  Don't have an account? Create one
                </button>
              </div>

              {/* Demo Mode Toggle */}
              <div className="mt-6 pt-5 border-t border-[#2A2A3E] flex items-center justify-center gap-3">
                <span className={`text-xs font-bold uppercase tracking-wider ${isDemoMode ? 'text-accent-green' : 'text-gray-500'}`}>Demo Mode</span>
                <button
                  onClick={toggleDemoMode}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-all duration-300 ${isDemoMode ? 'bg-accent-green' : 'bg-[#2A2A3E]'}`}
                >
                  <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-300 ${isDemoMode ? 'translate-x-6' : 'translate-x-1'}`} />
                </button>
              </div>

              {isDemoMode && (
                <div className="mt-6 pt-5 border-t border-[#2A2A3E] animate-fade-in">
                  <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest text-center mb-3">Quick Login (Demo Accounts)</p>
                  <div className="grid grid-cols-2 gap-2">
                    {demoCredentials.map((cred) => (
                      <button
                        key={cred.role}
                        onClick={() => handleQuickLogin(cred)}
                        disabled={loading}
                        className="flex items-center gap-2 p-2 border border-[#2A2A3E] rounded-xl hover:border-accent-green/50 hover:bg-accent-green/5 transition-all duration-300 text-left text-xs text-white cursor-pointer bg-transparent w-full"
                      >
                        <span className="text-sm">{cred.icon}</span>
                        <div className="truncate">
                          <div className="font-semibold" style={{ color: cred.color }}>{cred.role}</div>
                          <div className="text-[9px] text-gray-500 truncate">{cred.email}</div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            /* REGISTRATION FORM */
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label htmlFor="reg-name" className="block text-[10px] font-semibold text-gray-400 mb-1.5 uppercase tracking-wider">
                  Full Name
                </label>
                <input
                  id="reg-name"
                  type="text"
                  value={registerName}
                  onChange={(e) => setRegisterName(e.target.value)}
                  required
                  className="input-dark"
                  placeholder="Enter your name"
                />
              </div>

              <div>
                <label htmlFor="reg-email" className="block text-[10px] font-semibold text-gray-400 mb-1.5 uppercase tracking-wider">
                  Email Address
                </label>
                <input
                  id="reg-email"
                  type="email"
                  value={registerEmail}
                  onChange={(e) => setRegisterEmail(e.target.value)}
                  required
                  className="input-dark"
                  placeholder="Enter your email"
                />
              </div>

              <div>
                <label htmlFor="reg-password" className="block text-[10px] font-semibold text-gray-400 mb-1.5 uppercase tracking-wider">
                  Password
                </label>
                <input
                  id="reg-password"
                  type="password"
                  value={registerPassword}
                  onChange={(e) => setRegisterPassword(e.target.value)}
                  required
                  className="input-dark"
                  placeholder="Create a password"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="reg-role" className="block text-[10px] font-semibold text-gray-400 mb-1.5 uppercase tracking-wider">
                    Your Role
                  </label>
                  <select
                    id="reg-role"
                    value={registerRole}
                    onChange={(e) => setRegisterRole(e.target.value)}
                    className="input-dark bg-[#16162A] text-white cursor-pointer py-2.5"
                  >
                    <option value="SUPER_ADMIN">Super Admin</option>
                    <option value="ADMIN">School Admin</option>
                    <option value="TEACHER">Teacher</option>
                    <option value="STUDENT">Student</option>
                    <option value="PARENT">Parent</option>
                  </select>
                </div>

                {registerRole !== 'SUPER_ADMIN' && (
                  <div>
                    <label htmlFor="reg-school" className="block text-[10px] font-semibold text-gray-400 mb-1.5 uppercase tracking-wider">
                      Select School
                    </label>
                    <select
                      id="reg-school"
                      value={registerSchoolId}
                      onChange={(e) => setRegisterSchoolId(e.target.value)}
                      className="input-dark bg-[#16162A] text-white cursor-pointer py-2.5"
                    >
                      {schools.length > 0 ? (
                        schools.map(s => (
                          <option key={s.id} value={s.id}>{s.name}</option>
                        ))
                      ) : (
                        <option value="">Gurukul Demo Academy</option>
                      )}
                    </select>
                  </div>
                )}
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full btn-primary py-3 text-base mt-2 cursor-pointer"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="inline-block w-4 h-4 border-2 border-dark-bg/30 border-t-dark-bg rounded-full animate-spin" />
                    Registering...
                  </span>
                ) : 'Register & Log In'}
              </button>

              {/* Toggle to Login */}
              <div className="mt-4 text-center">
                <button
                  type="button"
                  onClick={() => {
                    setIsRegistering(false);
                    setError('');
                  }}
                  className="text-xs text-accent-green hover:underline font-medium bg-transparent border-none cursor-pointer"
                >
                  Already have an account? Log In
                </button>
              </div>
            </form>
          )}

          <div className="mt-5 text-center">
            <p className="text-gray-500 text-[10px]">All role dashboards are isolated and protected by role-based access.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
