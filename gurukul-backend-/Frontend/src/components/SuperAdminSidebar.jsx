
import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
    FaThLarge,
    FaUsers,
    FaChartLine,
    FaSignOutAlt,
    FaUserCircle,
    FaServer,
    FaUniversity,
    FaGlobe
} from 'react-icons/fa';
import { useSidebar } from '../contexts/SidebarContext';
import { useAuth } from '../contexts/AuthContext';

const SuperAdminSidebar = () => {
    const { isSidebarOpen, closeSidebar } = useSidebar();
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [activeHash, setActiveHash] = React.useState(() => window.location.hash.replace('#', '') || 'overview');

    const menuItems = [
        { icon: FaGlobe, label: "Platform Overview", path: "/superadmin#overview", hash: "overview" },
        { icon: FaUniversity, label: "School Management", path: "/superadmin#schools", hash: "schools" },
        { icon: FaUsers, label: "Global Users", path: "/superadmin#users", hash: "users" },
        { icon: FaServer, label: "Infrastructure Health", path: "/superadmin#health", hash: "health" },
    ];

    React.useEffect(() => {
        const handleHashChange = () => {
            setActiveHash(window.location.hash.replace('#', '') || 'overview');
        };
        window.addEventListener('hashchange', handleHashChange);
        handleHashChange();
        return () => window.removeEventListener('hashchange', handleHashChange);
    }, []);

    const handleLogout = async () => {
        try {
            await logout();
            closeSidebar();
            navigate('/signin');
        } catch (error) {
            console.error('Logout failed', error);
        }
    };

    return (
        <>
            <div
                className={`fixed inset-0 bg-black/60 z-30 lg:hidden backdrop-blur-sm transition-opacity duration-300 ${isSidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}
                onClick={closeSidebar}
            />

            <aside className={`
                w-64 flex flex-col gap-2 h-full lg:h-[calc(100vh-100px)] 
                fixed lg:sticky top-0 lg:top-24 left-0 z-40 
                transition-transform duration-300 ease-in-out
                bg-black/95 lg:bg-transparent backdrop-blur-xl lg:backdrop-blur-none 
                border-r lg:border-r-0 border-white/10 lg:border-transparent
                p-4 lg:p-0
                ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
            `}>
                <div className="lg:hidden mb-6 mt-2 flex items-center gap-3 px-2">
                    <span className="text-xl font-bold text-white font-heading">PLATFORM ADMIN</span>
                </div>

                <div className="glass-panel p-3 flex-grow flex flex-col justify-between border border-white/10 shadow-xl rounded-2xl bg-black/40 lg:bg-black/60">
                    <div className="flex flex-col gap-2">
                        <div className="px-4 py-2 mb-2">
                            <span className="text-[10px] font-bold text-orange-500 uppercase tracking-[0.2em]">Platform Control</span>
                        </div>
                        {menuItems.map((item, index) => {
                            const isActive = activeHash === item.hash;
                            return (
                                <NavLink
                                    key={index}
                                    to={item.path}
                                    onClick={() => {
                                        closeSidebar();
                                        window.location.hash = item.hash;
                                    }}
                                    className={`
                                        flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300 group
                                        ${isActive
                                            ? 'bg-gradient-to-r from-orange-600 to-amber-600 text-white shadow-lg border border-white/20 transform scale-105'
                                            : 'bg-white/5 text-gray-300 hover:text-white hover:bg-white/10 border border-transparent'}
                                    `}
                                >
                                    <item.icon className="text-lg opacity-80 group-hover:opacity-100" />
                                    <span className="text-sm font-medium tracking-wide">{item.label}</span>
                                </NavLink>
                            );
                        })}
                    </div>

                    <div className="pt-3 border-t border-white/10 mt-2">
                        {user && (
                            <div className="flex flex-col gap-2">
                                <div className="flex items-center gap-3 px-4 py-2">
                                    <FaUserCircle className="text-xl text-orange-400" />
                                    <div className="flex flex-col overflow-hidden">
                                        <span className="text-xs text-white font-bold truncate">{user.full_name || 'Super Admin'}</span>
                                        <span className="text-[10px] text-gray-500 truncate">{user.email}</span>
                                    </div>
                                </div>
                                <button
                                    onClick={handleLogout}
                                    className="w-full flex items-center gap-4 px-4 py-3 rounded-xl bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-all border border-red-500/20"
                                >
                                    <FaSignOutAlt className="text-lg" />
                                    <span className="text-sm font-bold">Log Out</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </aside>
        </>
    );
};

export default SuperAdminSidebar;
