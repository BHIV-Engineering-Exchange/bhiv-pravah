import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
    FaThLarge,
    FaUsers,
    FaChartLine,
    FaFileAlt,
    FaCog,
    FaSignOutAlt,
    FaUserCircle,
    FaServer,
    FaDatabase,
    FaEye
} from 'react-icons/fa';
import { useSidebar } from '../contexts/SidebarContext';
import { useAuth } from '../contexts/AuthContext';
import { useDemo } from '../contexts/DemoContext';

const AdminSidebar = () => {
    const { isSidebarOpen, closeSidebar } = useSidebar();
    const { user, logout } = useAuth();
    const { isDemoMode } = useDemo();
    const navigate = useNavigate();
    const [activeHash, setActiveHash] = React.useState(() => window.location.hash.replace('#', '') || 'overview');

    const adminMenuItems = [
        ...(!isDemoMode ? [{ icon: FaServer, label: "System Overview", path: "/admin_dashboard#overview", hash: "overview" }] : []),
        ...(!isDemoMode ? [{ icon: FaUsers, label: "User Management", path: "/admin_dashboard#users", hash: "users" }] : []),
        ...(!isDemoMode ? [{ icon: FaDatabase, label: "MDU Registry", path: "/admin_dashboard#mdu_registry", hash: "mdu_registry" }] : []),
        { icon: FaEye, label: "Gurukul Drishti", path: "/admin_dashboard#drishti", hash: "drishti" },
        { icon: FaChartLine, label: "Reports & Analytics", path: "/admin_dashboard#reports", hash: "reports" },
    ];

    // Listen for hash changes
    React.useEffect(() => {
        const handleHashChange = () => {
            setActiveHash(window.location.hash.replace('#', '') || 'overview');
        };

        window.addEventListener('hashchange', handleHashChange);
        // Check initial hash
        handleHashChange();

        return () => window.removeEventListener('hashchange', handleHashChange);
    }, []);

    const handleLogout = async () => {
        try {
            await logout();
            closeSidebar();
            navigate('/signin');
        } catch (error) {
            console.error('Failed to log out', error);
        }
    };

    return (
        <>
            {/* Mobile Backdrop */}
            <div
                className={`fixed inset-0 bg-black/60 z-30 lg:hidden backdrop-blur-sm transition-opacity duration-300 ${isSidebarOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
                    }`}
                onClick={closeSidebar}
            />

            {/* Sidebar Container */}
            <aside className={`
                w-64 flex flex-col gap-2 h-full lg:h-[calc(100vh-100px)] 
                fixed lg:sticky top-0 lg:top-24 left-0 z-40 
                transition-transform duration-300 ease-in-out
                bg-black/95 lg:bg-transparent backdrop-blur-xl lg:backdrop-blur-none 
                border-r lg:border-r-0 border-white/10 lg:border-transparent
                p-4 lg:p-0
                ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
            `}>
                {/* Mobile Header */}
                <div className="lg:hidden mb-6 mt-2 flex items-center gap-3 px-2">
                    <span className="text-xl font-bold font-heading text-white">Admin Menu</span>
                </div>

                <div className="glass-panel p-3 flex-grow flex flex-col justify-between border border-white/10 shadow-xl rounded-2xl overflow-hidden bg-black/40 lg:bg-black/60">
                    {/* Main Menu */}
                    <div className="flex flex-col gap-2 overflow-y-auto no-scrollbar">
                        {adminMenuItems.map((item, index) => {
                            const isActive = activeHash === item.hash;

                            return (
                                <NavLink
                                    key={index}
                                    to={item.path}
                                    onClick={(e) => {
                                        closeSidebar();
                                        setActiveHash(item.hash);
                                        // Ensure hash is set
                                        window.location.hash = item.hash;
                                    }}
                                    className={`
                                        flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300 group
                                        ${isActive
                                            ? 'bg-gradient-to-r from-orange-600 to-amber-600 text-white shadow-lg border border-white/20 transform scale-105'
                                            : 'bg-white/5 text-gray-300 hover:text-white hover:pl-6 border border-transparent'}
                                    `}
                                >
                                    <item.icon className="text-lg opacity-80 group-hover:opacity-100" />
                                    <span className="text-sm font-medium tracking-wide">{item.label}</span>
                                </NavLink>
                            );
                        })}
                    </div>

                    {/* Footer Actions */}
                    <div className="pt-3 border-t border-white/10 mt-2 space-y-2">
                        {/* Settings */}
                        {!isDemoMode && (
                            <NavLink
                                to="/admin_dashboard#settings"
                                onClick={(e) => {
                                    closeSidebar();
                                    setActiveHash('settings');
                                    window.location.hash = 'settings';
                                }}
                                className={({ isActive }) => `
                                    flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300 group
                                    ${activeHash === 'settings'
                                        ? 'bg-gradient-to-r from-orange-600 to-amber-600 text-white shadow-lg border border-white/20 transform scale-105'
                                        : 'bg-white/5 text-gray-300 hover:text-white hover:pl-6 border border-transparent'}
                                `}
                            >
                                <FaCog className="text-lg opacity-80 group-hover:opacity-100" />
                                <span className="text-sm font-medium tracking-wide">Settings</span>
                            </NavLink>
                        )}

                        {/* Mobile User Section */}
                        {user && (
                            <div className="lg:hidden mt-4 pt-4 border-t border-white/10">
                                <div className="flex items-center gap-3 px-4 mb-3">
                                    <FaUserCircle className="text-xl text-orange-400" />
                                    <span className="text-sm text-gray-300 font-medium truncate">{user.email}</span>
                                </div>
                                <button
                                    onClick={handleLogout}
                                    className="w-full flex items-center gap-4 px-4 py-3 rounded-xl bg-red-500/10 text-red-400 hover:bg-red-500/20 hover:text-red-300 transition-all border border-red-500/20"
                                >
                                    <FaSignOutAlt className="text-lg" />
                                    <span className="text-sm font-bold tracking-wide">Log Out</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </aside>
        </>
    );
};

export default AdminSidebar;

