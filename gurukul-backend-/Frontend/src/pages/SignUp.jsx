import React, { useState } from 'react';
import { FaArrowRight, FaUser } from 'react-icons/fa';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { setUserRole } from '../utils/roles';

const SignUp = () => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState('STUDENT');
    const [error, setError] = useState(null);
    const [message, setMessage] = useState('');
    const [loading, setLoading] = useState(false);
    const { signup } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError(null);
        setMessage('');
        setLoading(true);
        
        try {
            const { user } = await signup(email, password, role, name);
            setMessage('Account created successfully! Redirecting...');
            
            // Auto-redirect to role-appropriate dashboard after successful signup
            setTimeout(() => {
                const lowerRole = role.toLowerCase();
                setUserRole(lowerRole === 'institution_admin' || lowerRole === 'regional_admin' ? 'admin' : lowerRole);
                
                if (['teacher', 'institution_admin', 'regional_admin', 'admin'].includes(lowerRole)) {
                    navigate('/drishti');
                } else if (lowerRole === 'student') {
                    navigate('/dashboard');
                } else {
                    navigate('/dashboard');
                }
            }, 1500);
        } catch (err) {
            console.error('Signup error:', err);
            setError(err.message || 'Failed to create account. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex items-center justify-center min-h-[calc(100vh-100px)] px-3 sm:px-4 py-4">
            {/* Registration Card */}
            <div className="w-full max-w-md glass-panel p-5 sm:p-6 md:p-10 animate-fade-in-up border border-white/10 shadow-2xl relative overflow-hidden">

                {/* Subtle decorative glow */}
                <div className="absolute -top-10 -left-10 w-32 h-32 bg-accent/20 rounded-full blur-3xl"></div>
                <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-orange-900/40 rounded-full blur-3xl"></div>

                <div className="relative z-10">
                    <h2 className="text-3xl sm:text-4xl font-heading font-bold mb-2 text-center text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400">Join Gurukul</h2>
                    <p className="text-center text-gray-400 text-xs sm:text-sm mb-6 sm:mb-8 tracking-wide">Begin your path to wisdom and discovery.</p>

                    {error && <div className="bg-red-500/20 text-red-300 p-3 rounded mb-4 text-sm border border-red-500/30 text-center">{error}</div>}
                    {message && <div className="bg-green-500/20 text-green-300 p-3 rounded mb-4 text-sm border border-green-500/30 text-center">{message}</div>}

                    <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
                        <div className="space-y-1">
                            <label className="text-xs font-semibold uppercase tracking-wider text-gray-400 ml-1">Full Name</label>
                            <input
                                type="text"
                                placeholder="Eklavya"
                                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-accent/50 focus:bg-white/10 transition-all"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                required
                            />
                        </div>

                        <div className="space-y-1">
                            <label className="text-xs font-semibold uppercase tracking-wider text-gray-400 ml-1">Email Address</label>
                            <input
                                type="email"
                                placeholder="student@gurukul.com"
                                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-accent/50 focus:bg-white/10 transition-all"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>

                        <div className="space-y-1">
                            <label className="text-xs font-semibold uppercase tracking-wider text-gray-400 ml-1">Password</label>
                            <input
                                type="password"
                                placeholder="Create a strong password"
                                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-accent/50 focus:bg-white/10 transition-all"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>

                        <div className="space-y-1">
                            <label className="text-xs font-semibold uppercase tracking-wider text-gray-400 ml-1">Account Role</label>
                            <select
                                className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-accent/50 focus:bg-[#12130e] transition-all cursor-pointer"
                                value={role}
                                onChange={(e) => setRole(e.target.value)}
                                required
                            >
                                <option value="STUDENT" className="bg-[#12130e] text-white">Student</option>
                                <option value="TEACHER" className="bg-[#12130e] text-white">Teacher</option>
                                <option value="INSTITUTION_ADMIN" className="bg-[#12130e] text-white">Institution Admin</option>
                                <option value="REGIONAL_ADMIN" className="bg-[#12130e] text-white">Regional Admin</option>
                            </select>
                        </div>

                        <button 
                            type="submit" 
                            disabled={loading}
                            className="w-full mt-2 py-3 rounded-lg bg-gradient-to-r from-orange-600 to-amber-700 hover:from-orange-500 hover:to-amber-600 text-white font-bold tracking-wide shadow-lg transform transition-all hover:-translate-y-1 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
                        >
                            {loading ? 'Creating Account...' : 'Create Account'} 
                            {!loading && <FaArrowRight className="text-sm opacity-80" />}
                        </button>
                    </form>

                    <p className="mt-8 text-center text-xs text-gray-400">
                        Already a scholar? <Link to="/signin" className="text-accent hover:text-orange-300 font-semibold transition-colors">Sign In</Link>
                    </p>
                </div>
            </div>
        </div>
    );
};

export default SignUp;
