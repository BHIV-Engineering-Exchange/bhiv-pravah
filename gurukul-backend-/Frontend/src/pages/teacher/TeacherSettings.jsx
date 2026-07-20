import React, { useState, useEffect } from 'react';
import { FaUser, FaGlobe, FaBell, FaChalkboardTeacher, FaUpload, FaComments, FaShieldAlt, FaTrash, FaSave } from 'react-icons/fa';
import { useAuth } from '../../contexts/AuthContext';
import { useModal } from '../../contexts/ModalContext';
import { apiGet, apiPut, apiDelete, handleApiError } from '../../utils/apiClient';
import { setLanguage, getCurrentLanguage } from '../../utils/languageSupport';
import API_BASE_URL from '../../config';

const TeacherSettings = () => {
    const { user, logout } = useAuth();
    const { confirm, alert } = useModal();
    const [activeTab, setActiveTab] = useState('profile');
    const [loading, setLoading] = useState(false);

    // Profile state
    const [fullName, setFullName] = useState(user?.full_name || '');
    const [email] = useState(user?.email || '');
    const [bio, setBio] = useState('');

    // Preferences state
    const [language, setLanguageState] = useState(() => {
        const saved = getCurrentLanguage();
        const langMap = { 'en': 'English', 'ar': 'Arabic' };
        return langMap[saved] || 'English';
    });
    const [notifications, setNotifications] = useState({
        newAssignments: true,
        studentSubmissions: true,
        messages: true,
        announcements: true
    });

    // Class Defaults
    const [classDefaults, setClassDefaults] = useState({
        defaultSubject: '',
        autoGrade: false,
        allowLateSubmissions: true,
        maxFileSize: 10 // MB
    });

    // Content Settings
    const [contentSettings, setContentSettings] = useState({
        allowedFileTypes: ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'mp4', 'mov'],
        requireApproval: false,
        maxUploadSize: 50 // MB
    });

    // Communication Settings
    const [communicationSettings, setCommunicationSettings] = useState({
        emailNotifications: true,
        inAppNotifications: true,
        parentNotifications: true
    });

    useEffect(() => {
        if (user?.full_name) {
            setFullName(user.full_name);
        }
        fetchSettings();
    }, [user]);

    const fetchSettings = async () => {
        try {
            setLoading(true);
            // TODO: Replace with actual endpoint
            const data = await apiGet('/api/v1/ems/teacher/settings').catch(() => null);
            if (data) {
                if (data.bio) setBio(data.bio);
                if (data.notifications) setNotifications(data.notifications);
                if (data.classDefaults) setClassDefaults(data.classDefaults);
                if (data.contentSettings) setContentSettings(data.contentSettings);
                if (data.communicationSettings) setCommunicationSettings(data.communicationSettings);
            }
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'fetch settings' });
            if (!errorInfo.message.includes('404')) {
                await alert(errorInfo.message, errorInfo.title);
            }
        } finally {
            setLoading(false);
        }
    };

    const handleSaveProfile = async () => {
        try {
            setLoading(true);
            await apiPut('/api/v1/auth/update-profile', {
                full_name: fullName,
            });
            await alert('Profile updated successfully!', 'Success');
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'update profile' });
            await alert(errorInfo.message, errorInfo.title);
        } finally {
            setLoading(false);
        }
    };

    const handleSaveSettings = async (settingsType, settingsData) => {
        try {
            setLoading(true);
            // TODO: Replace with actual endpoint
            await apiPut('/api/v1/ems/teacher/settings', {
                [settingsType]: settingsData
            });
            await alert('Settings saved successfully!', 'Success');
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'save settings' });
            await alert(errorInfo.message, errorInfo.title);
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteAccount = async () => {
        const result = await confirm(
            'Are you sure you want to delete your account? This action cannot be undone and will permanently delete all your data.',
            'Delete Account'
        );
        if (!result) return;

        try {
            setLoading(true);
            await apiDelete('/api/v1/auth/delete-account');
            await alert('Account deleted successfully. Redirecting to sign in...', 'Account Deleted');
            logout();
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'delete account' });
            await alert(errorInfo.message, errorInfo.title);
        } finally {
            setLoading(false);
        }
    };

    const handleLanguageChange = (newLanguage) => {
        const langCode = newLanguage === 'English' ? 'en' : 'ar';
        setLanguageState(newLanguage);
        setLanguage(langCode);
        localStorage.setItem('user_language', langCode);
    };

    const tabs = [
        { id: 'profile', label: 'Profile', icon: FaUser },
        { id: 'preferences', label: 'Preferences', icon: FaGlobe },
        { id: 'classes', label: 'Class Defaults', icon: FaChalkboardTeacher },
        { id: 'content', label: 'Content', icon: FaUpload },
        { id: 'communication', label: 'Communication', icon: FaComments },
        { id: 'security', label: 'Security', icon: FaShieldAlt },
    ];

    return (
        <div className="space-y-6">
            <div>
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <FaUser className="text-orange-400" />
                    Settings
                </h3>
                <p className="text-gray-400 text-sm mt-1">Manage your account settings and preferences</p>
            </div>

            {/* Tabs */}
            <div className="flex flex-wrap gap-2 border-b border-white/10">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                            activeTab === tab.id
                                ? 'border-orange-500 text-orange-400'
                                : 'border-transparent text-gray-400 hover:text-white'
                        }`}
                    >
                        <tab.icon />
                        <span>{tab.label}</span>
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            <div className="glass-panel p-6 rounded-2xl border border-white/10">
                {activeTab === 'profile' && (
                    <div className="space-y-4">
                        <h4 className="text-lg font-semibold text-white mb-4">Profile Information</h4>
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Full Name
                            </label>
                            <input
                                type="text"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-orange-500"
                                placeholder="Enter your full name"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Email
                            </label>
                            <input
                                type="email"
                                value={email}
                                disabled
                                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-gray-500 cursor-not-allowed"
                            />
                            <p className="text-xs text-gray-500 mt-1">Email cannot be changed</p>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Bio
                            </label>
                            <textarea
                                value={bio}
                                onChange={(e) => setBio(e.target.value)}
                                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-orange-500"
                                rows="3"
                                placeholder="Tell us about yourself..."
                            />
                        </div>
                        <button
                            onClick={handleSaveProfile}
                            disabled={loading}
                            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-600 to-amber-600 text-white font-semibold rounded-lg hover:from-orange-700 hover:to-amber-700 transition-all disabled:opacity-50"
                        >
                            <FaSave />
                            Save Profile
                        </button>
                    </div>
                )}

                {activeTab === 'preferences' && (
                    <div className="space-y-6">
                        <h4 className="text-lg font-semibold text-white mb-4">Preferences</h4>
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Language
                            </label>
                            <select
                                value={language}
                                onChange={(e) => handleLanguageChange(e.target.value)}
                                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-orange-500"
                            >
                                <option value="English">English</option>
                                <option value="Arabic">Arabic</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-4">
                                Notifications
                            </label>
                            <div className="space-y-3">
                                {Object.entries(notifications).map(([key, value]) => (
                                    <div key={key} className="flex items-center justify-between">
                                        <span className="text-gray-300 capitalize">
                                            {key.replace(/([A-Z])/g, ' $1').trim()}
                                        </span>
                                        <button
                                            onClick={() => setNotifications({ ...notifications, [key]: !value })}
                                            className={`w-12 h-6 rounded-full transition-colors ${
                                                value ? 'bg-orange-500' : 'bg-gray-600'
                                            }`}
                                        >
                                            <span className={`block w-5 h-5 rounded-full bg-white transform transition-transform ${
                                                value ? 'translate-x-6' : 'translate-x-1'
                                            }`} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                        <button
                            onClick={() => handleSaveSettings('notifications', notifications)}
                            disabled={loading}
                            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-600 to-amber-600 text-white font-semibold rounded-lg hover:from-orange-700 hover:to-amber-700 transition-all disabled:opacity-50"
                        >
                            <FaSave />
                            Save Preferences
                        </button>
                    </div>
                )}

                {activeTab === 'classes' && (
                    <div className="space-y-6">
                        <h4 className="text-lg font-semibold text-white mb-4">Class Defaults</h4>
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Default Subject
                            </label>
                            <select
                                value={classDefaults.defaultSubject}
                                onChange={(e) => setClassDefaults({ ...classDefaults, defaultSubject: e.target.value })}
                                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-orange-500"
                            >
                                <option value="">None</option>
                                <option value="Mathematics">Mathematics</option>
                                <option value="Physics">Physics</option>
                                <option value="Chemistry">Chemistry</option>
                                <option value="Biology">Biology</option>
                                <option value="Computer Science">Computer Science</option>
                                <option value="History">History</option>
                                <option value="Geography">Geography</option>
                                <option value="Literature">Literature</option>
                                <option value="Economics">Economics</option>
                            </select>
                        </div>
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <span className="text-gray-300">Auto-grade assignments</span>
                                <button
                                    onClick={() => setClassDefaults({ ...classDefaults, autoGrade: !classDefaults.autoGrade })}
                                    className={`w-12 h-6 rounded-full transition-colors ${
                                        classDefaults.autoGrade ? 'bg-orange-500' : 'bg-gray-600'
                                    }`}
                                >
                                    <span className={`block w-5 h-5 rounded-full bg-white transform transition-transform ${
                                        classDefaults.autoGrade ? 'translate-x-6' : 'translate-x-1'
                                    }`} />
                                </button>
                            </div>
                            <div className="flex items-center justify-between">
                                <span className="text-gray-300">Allow late submissions</span>
                                <button
                                    onClick={() => setClassDefaults({ ...classDefaults, allowLateSubmissions: !classDefaults.allowLateSubmissions })}
                                    className={`w-12 h-6 rounded-full transition-colors ${
                                        classDefaults.allowLateSubmissions ? 'bg-orange-500' : 'bg-gray-600'
                                    }`}
                                >
                                    <span className={`block w-5 h-5 rounded-full bg-white transform transition-transform ${
                                        classDefaults.allowLateSubmissions ? 'translate-x-6' : 'translate-x-1'
                                    }`} />
                                </button>
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Max File Size (MB)
                            </label>
                            <input
                                type="number"
                                value={classDefaults.maxFileSize}
                                onChange={(e) => setClassDefaults({ ...classDefaults, maxFileSize: parseInt(e.target.value) })}
                                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-orange-500"
                                min="1"
                                max="100"
                            />
                        </div>
                        <button
                            onClick={() => handleSaveSettings('classDefaults', classDefaults)}
                            disabled={loading}
                            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-600 to-amber-600 text-white font-semibold rounded-lg hover:from-orange-700 hover:to-amber-700 transition-all disabled:opacity-50"
                        >
                            <FaSave />
                            Save Class Defaults
                        </button>
                    </div>
                )}

                {activeTab === 'content' && (
                    <div className="space-y-6">
                        <h4 className="text-lg font-semibold text-white mb-4">Content Settings</h4>
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Allowed File Types
                            </label>
                            <div className="flex flex-wrap gap-2">
                                {['pdf', 'doc', 'docx', 'ppt', 'pptx', 'mp4', 'mov', 'jpg', 'png'].map((type) => (
                                    <label key={type} className="flex items-center gap-2 px-3 py-2 bg-white/5 rounded-lg cursor-pointer hover:bg-white/10">
                                        <input
                                            type="checkbox"
                                            checked={contentSettings.allowedFileTypes.includes(type)}
                                            onChange={(e) => {
                                                if (e.target.checked) {
                                                    setContentSettings({
                                                        ...contentSettings,
                                                        allowedFileTypes: [...contentSettings.allowedFileTypes, type]
                                                    });
                                                } else {
                                                    setContentSettings({
                                                        ...contentSettings,
                                                        allowedFileTypes: contentSettings.allowedFileTypes.filter(t => t !== type)
                                                    });
                                                }
                                            }}
                                            className="rounded"
                                        />
                                        <span className="text-gray-300 text-sm uppercase">{type}</span>
                                    </label>
                                ))}
                            </div>
                        </div>
                        <div className="flex items-center justify-between">
                            <span className="text-gray-300">Require approval for student content</span>
                            <button
                                onClick={() => setContentSettings({ ...contentSettings, requireApproval: !contentSettings.requireApproval })}
                                className={`w-12 h-6 rounded-full transition-colors ${
                                    contentSettings.requireApproval ? 'bg-orange-500' : 'bg-gray-600'
                                }`}
                            >
                                <span className={`block w-5 h-5 rounded-full bg-white transform transition-transform ${
                                    contentSettings.requireApproval ? 'translate-x-6' : 'translate-x-1'
                                }`} />
                            </button>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Max Upload Size (MB)
                            </label>
                            <input
                                type="number"
                                value={contentSettings.maxUploadSize}
                                onChange={(e) => setContentSettings({ ...contentSettings, maxUploadSize: parseInt(e.target.value) })}
                                className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-orange-500"
                                min="1"
                                max="500"
                            />
                        </div>
                        <button
                            onClick={() => handleSaveSettings('contentSettings', contentSettings)}
                            disabled={loading}
                            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-600 to-amber-600 text-white font-semibold rounded-lg hover:from-orange-700 hover:to-amber-700 transition-all disabled:opacity-50"
                        >
                            <FaSave />
                            Save Content Settings
                        </button>
                    </div>
                )}

                {activeTab === 'communication' && (
                    <div className="space-y-6">
                        <h4 className="text-lg font-semibold text-white mb-4">Communication Settings</h4>
                        <div className="space-y-3">
                            {Object.entries(communicationSettings).map(([key, value]) => (
                                <div key={key} className="flex items-center justify-between">
                                    <span className="text-gray-300 capitalize">
                                        {key.replace(/([A-Z])/g, ' $1').trim()}
                                    </span>
                                    <button
                                        onClick={() => setCommunicationSettings({ ...communicationSettings, [key]: !value })}
                                        className={`w-12 h-6 rounded-full transition-colors ${
                                            value ? 'bg-orange-500' : 'bg-gray-600'
                                        }`}
                                    >
                                        <span className={`block w-5 h-5 rounded-full bg-white transform transition-transform ${
                                            value ? 'translate-x-6' : 'translate-x-1'
                                        }`} />
                                    </button>
                                </div>
                            ))}
                        </div>
                        <button
                            onClick={() => handleSaveSettings('communicationSettings', communicationSettings)}
                            disabled={loading}
                            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-600 to-amber-600 text-white font-semibold rounded-lg hover:from-orange-700 hover:to-amber-700 transition-all disabled:opacity-50"
                        >
                            <FaSave />
                            Save Communication Settings
                        </button>
                    </div>
                )}

                {activeTab === 'security' && (
                    <div className="space-y-6">
                        <h4 className="text-lg font-semibold text-white mb-4">Account Security</h4>
                        <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                            <h5 className="text-red-400 font-semibold mb-2 flex items-center gap-2">
                                <FaTrash />
                                Delete Account
                            </h5>
                            <p className="text-gray-400 text-sm mb-4">
                                Permanently delete your account and all associated data. This action cannot be undone.
                            </p>
                            <button
                                onClick={handleDeleteAccount}
                                disabled={loading}
                                className="px-4 py-2 bg-red-600 text-white font-semibold rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
                            >
                                Delete My Account
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default TeacherSettings;

