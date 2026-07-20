import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import { FaUser, FaGlobe, FaShieldAlt, FaSignOutAlt, FaTrash } from 'react-icons/fa';
import { useAuth } from '../contexts/AuthContext';
import { useModal } from '../contexts/ModalContext';
import { setLanguage, getCurrentLanguage } from '../utils/languageSupport';
import API_BASE_URL from '../config';


const Settings = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const { confirm, prompt, alert } = useModal();
    const [activeSection, setActiveSection] = useState('profile');

    // Profile state - load from user object (from database) first, then localStorage as fallback
    const [fullName, setFullName] = useState(() => {
        // Priority: user.full_name from database > localStorage > email prefix
        return user?.full_name || localStorage.getItem('user_fullName') || (user?.email ? user.email.split('@')[0] : '');
    });
    const [email] = useState(() => {
        const saved = localStorage.getItem('user_email');
        return saved || (user?.email || 'vasco@gurukul.app');
    });
    const [bio, setBio] = useState(() => {
        const saved = localStorage.getItem('user_bio');
        return saved || 'Navigating the seas of knowledge.';
    });

    // Preferences state with localStorage persistence
    const [language, setLanguageState] = useState(() => {
        const saved = getCurrentLanguage();
        // Map language codes to display names
        const langMap = { 'en': 'English', 'ar': 'Arabic' };
        return langMap[saved] || 'English';
    });
    const [reduceMotion, setReduceMotion] = useState(() => {
        const saved = localStorage.getItem('user_reduceMotion');
        return saved === 'true';
    });


    // Load full name from user object when available
    useEffect(() => {
        if (user?.full_name) {
            setFullName(user.full_name);
            localStorage.setItem('user_fullName', user.full_name);
        }
    }, [user]);

    // Save profile changes to database (debounced)
    useEffect(() => {
        const timer = setTimeout(() => {
            if (fullName && fullName !== (user?.full_name || '')) {
                const token = localStorage.getItem('auth_token');
                if (token) {
                    fetch(`${API_BASE_URL}/api/v1/auth/update-profile`, {
                        method: 'PUT',
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            full_name: fullName,
                        }),
                    })
                    .then(response => {
                        if (response.ok) {
                            return response.json();
                        }
                        throw new Error('Failed to update profile');
                    })
                    .then(updatedUser => {
                        localStorage.setItem('user_fullName', updatedUser.full_name || '');
                    })
                    .catch(error => {
                        console.error('Error saving profile:', error);
                    });
                }
            }
        }, 1000); // Wait 1 second after user stops typing

        return () => clearTimeout(timer);
    }, [fullName, user]);


    useEffect(() => {
        localStorage.setItem('user_bio', bio);
    }, [bio]);

    // Persist preferences
    useEffect(() => {
        // Map display names to language codes
        const langCodeMap = { 'English': 'en', 'Arabic': 'ar' };
        const langCode = langCodeMap[language] || 'en';
        setLanguage(langCode);
    }, [language]);

    useEffect(() => {
        localStorage.setItem('user_reduceMotion', reduceMotion.toString());
        // Apply reduce motion to document
        if (reduceMotion) {
            document.documentElement.style.setProperty('--animation-duration', '0s');
        } else {
            document.documentElement.style.removeProperty('--animation-duration');
        }
    }, [reduceMotion]);


    // Load full name from user object when it changes (from database)
    useEffect(() => {
        if (user?.full_name) {
            setFullName(user.full_name);
            localStorage.setItem('user_fullName', user.full_name);
        }
    }, [user]);

    // Save profile changes to database (debounced - saves 1 second after user stops typing)
    useEffect(() => {
        const timer = setTimeout(() => {
            if (fullName && fullName !== (user?.full_name || '')) {
                const token = localStorage.getItem('auth_token');
                if (token) {
                    fetch(`${API_BASE_URL}/api/v1/auth/update-profile`, {
                        method: 'PUT',
                        headers: {
                            'Authorization': `Bearer ${token}`,
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            full_name: fullName,
                        }),
                    })
                    .then(response => {
                        if (response.ok) {
                            return response.json();
                        }
                        throw new Error('Failed to update profile');
                    })
                    .then(updatedUser => {
                        localStorage.setItem('user_fullName', updatedUser.full_name || '');
                    })
                    .catch(error => {
                        console.error('Error saving profile:', error);
                    });
                }
            }
        }, 1000); // Wait 1 second after user stops typing

        return () => clearTimeout(timer);
    }, [fullName, user]);

    const handleSignOut = async () => {
        const result = await confirm('Are you sure you want to sign out?', 'Sign Out');
        if (result) {
            try {
                await logout();
                navigate('/signin');
            } catch (error) {
                console.error('Failed to sign out:', error);
                alert('Failed to sign out. Please try again.', 'Error');
            }
        }
    };

    const handleDeleteAccount = async () => {
        const userInput = await prompt(
            'Are you absolutely sure you want to delete your account? This action is IRREVERSIBLE and will delete all your data from our servers. Type "DELETE" to confirm.',
            'Delete Account',
            'Type DELETE to confirm'
        );

        if (userInput === 'DELETE') {
            try {
                // Get auth token
                const token = localStorage.getItem('auth_token');
                if (!token) {
                    alert('You must be signed in to delete your account.', 'Error');
                    return;
                }

                // Call backend API to delete account
                const response = await fetch(`${API_BASE_URL}/api/v1/auth/delete-account`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json',
                    },
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Failed to delete account');
                }

                // Clear all localStorage data
                localStorage.clear();

                // Sign out the user
                await logout();

                await alert('Your account and all associated data have been permanently deleted from our servers.', 'Account Deleted');
                navigate('/signin');
            } catch (error) {
                console.error('Failed to delete account:', error);
                alert(`Failed to delete account: ${error.message}. Please try again or contact support.`, 'Error');
            }
        }
    };


    const renderContent = () => {
        switch (activeSection) {
            case 'profile':
                return (
                    <div className="space-y-6">
                        <h2 className="text-2xl font-bold text-white mb-6">Profile Settings</h2>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-2">
                                <label className="text-orange-200 text-xs font-bold uppercase tracking-wider">Full Name</label>
                                <input
                                    type="text"
                                    value={fullName}
                                    onChange={(e) => setFullName(e.target.value)}
                                    className="w-full bg-black/60 border border-white/10 rounded-xl p-3 text-white focus:border-orange-500 focus:outline-none transition-colors"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-orange-200 text-xs font-bold uppercase tracking-wider">Email Address</label>
                                <input
                                    type="email"
                                    value={email}
                                    readOnly
                                    disabled
                                    className="w-full bg-black/40 border border-white/5 rounded-xl p-3 text-gray-500 cursor-not-allowed"
                                />
                            </div>
                            <div className="col-span-1 md:col-span-2 space-y-2">
                                <label className="text-orange-200 text-xs font-bold uppercase tracking-wider">Bio</label>
                                <textarea
                                    rows="4"
                                    value={bio}
                                    onChange={(e) => setBio(e.target.value)}
                                    className="w-full bg-black/60 border border-white/10 rounded-xl p-3 text-white focus:border-orange-500 focus:outline-none transition-colors resize-none"
                                />
                            </div>
                        </div>
                    </div>
                );
            case 'preferences':
                return (
                    <div className="space-y-6">
                        <h2 className="text-2xl font-bold text-white mb-6">App Preferences</h2>

                        <div className="space-y-4">
                            <div className="bg-black/60 p-4 rounded-xl border border-white/10 flex justify-between items-center">
                                <div>
                                    <h3 className="text-white font-medium">Language</h3>
                                    <p className="text-gray-400 text-sm">Select your preferred language</p>
                                </div>
                                <select
                                    value={language}
                                    onChange={(e) => setLanguageState(e.target.value)}
                                    className="bg-white/5 border border-white/10 text-white rounded-lg p-2 outline-none focus:border-orange-500"
                                >
                                    <option value="English">English</option>
                                    <option value="Arabic">Arabic (العربية)</option>
                                </select>
                            </div>

                            <div className="bg-black/60 p-4 rounded-xl border border-white/10 flex justify-between items-center">
                                <div>
                                    <h3 className="text-white font-medium">Reduce Motion</h3>
                                    <p className="text-gray-400 text-sm">Minimize animations for better accessibility</p>
                                </div>
                                <div
                                    className={`w-12 h-6 rounded-full p-1 cursor-pointer transition-colors duration-300 ${reduceMotion ? 'bg-orange-500' : 'bg-gray-600'}`}
                                    onClick={() => setReduceMotion(!reduceMotion)}
                                >
                                    <div className={`w-4 h-4 bg-white rounded-full shadow-md transform transition-transform duration-300 ${reduceMotion ? 'translate-x-6' : 'translate-x-0'}`}></div>
                                </div>
                            </div>

                        </div>
                    </div>
                );
            case 'security':
                return (
                    <div className="space-y-6">
                        <h2 className="text-2xl font-bold text-white mb-6">Security & Account</h2>

                        <div className="space-y-4">
                            <button
                                onClick={handleSignOut}
                                className="w-full flex items-center justify-between p-4 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded-xl transition-all group cursor-pointer"
                            >
                                <span className="text-red-400 font-medium group-hover:text-red-300">Sign Out</span>
                                <FaSignOutAlt className="text-red-400 group-hover:text-red-300" />
                            </button>
                            <button
                                onClick={handleDeleteAccount}
                                className="w-full flex items-center justify-between p-4 bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 rounded-xl transition-all group cursor-pointer"
                            >
                                <div>
                                    <p className="text-left text-red-400 font-medium group-hover:text-red-300">Delete Account</p>
                                    <p className="text-left text-red-500/60 text-xs">This action is irreversible</p>
                                </div>
                                <FaTrash className="text-red-400 group-hover:text-red-300" />
                            </button>
                        </div>
                    </div>
                );
            default:
                return null;
        }
    };

    const navItems = [
        { id: 'profile', icon: FaUser, label: 'Profile' },
        { id: 'preferences', icon: FaGlobe, label: 'Preferences' },
        { id: 'security', icon: FaShieldAlt, label: 'Security' },
    ];

    return (
        <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6">
            <Sidebar />

            <main className="flex-grow flex flex-col lg:flex-row gap-4 sm:gap-6 animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                {/* Navigation Panel */}
                <div className="w-full lg:w-64 glass-panel no-hover p-4 sm:p-6 rounded-3xl border border-white/10 h-fit">
                    <h1 className="text-xl sm:text-2xl font-bold text-white mb-6 sm:mb-8 px-2">Settings</h1>
                    <div className="space-y-2">
                        {navItems.map((item) => (
                            <button
                                key={item.id}
                                onClick={() => setActiveSection(item.id)}
                                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all font-medium ${activeSection === item.id
                                    ? 'bg-orange-500 text-white shadow-lg shadow-orange-500/20'
                                    : 'text-gray-400 hover:bg-white/5 hover:text-white'
                                    }`}
                            >
                                <item.icon />
                                {item.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Content Panel */}
                <div className="flex-grow glass-panel no-hover p-4 sm:p-6 md:p-8 rounded-3xl border border-white/10 relative overflow-hidden h-auto lg:h-[calc(100vh-140px)] overflow-y-auto custom-scrollbar">
                    {/* Decorative Elements */}
                    <div className="absolute top-0 right-0 w-96 h-96 bg-orange-500/5 rounded-full blur-3xl pointer-events-none -translate-y-1/2 translate-x-1/2"></div>

                    <div className="relative z-10 max-w-2xl">
                        {renderContent()}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default Settings;
