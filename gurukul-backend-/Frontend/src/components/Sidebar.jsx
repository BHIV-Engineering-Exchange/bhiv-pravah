import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
    FaThLarge,
    FaBookOpen,
    FaFileAlt,
    FaComments,
    FaClipboardList,
    FaVideo,
    FaRobot,
    FaUserAstronaut,
    FaCog,
    FaSignOutAlt,
    FaUserCircle,
    FaFlipboard,
    FaCalendarAlt,
    FaBullhorn,
    FaCheckCircle,
    FaChalkboardTeacher,
    FaFolder
} from 'react-icons/fa';
import { useSidebar } from '../contexts/SidebarContext';
import { useAuth } from '../contexts/AuthContext';
import { useDemo } from '../contexts/DemoContext';
import { getCurrentRole, getDashboardPath } from '../utils/roles';

const Sidebar = () => {
    const { isSidebarOpen, closeSidebar } = useSidebar();
    const { user, logout } = useAuth();
    const { isDemoMode } = useDemo();
    const currentRole = getCurrentRole();
    const dashboardPath = getDashboardPath(currentRole);
    const navigate = useNavigate();

    const menuItems = [
        { icon: FaThLarge, label: "Dashboard", path: dashboardPath },
        { icon: FaBookOpen, label: "Subjects", path: "/subjects" },
        // { icon: FaFileAlt, label: "Summarizer", path: "/summarizer" }, // PDF summarizer commented out
        { icon: FaComments, label: "Chatbot", path: "/chatbot" },
        { icon: FaClipboardList, label: "Test", path: "/test" },
        { icon: FaFlipboard, label: "Flashcards", path: "/flashcards" },
        { icon: FaFolder, label: "My Content", path: "/my-content" },
        { icon: FaVideo, label: "Lectures", path: "/lectures" },
        { icon: FaRobot, label: "Agent Simulator", path: "/agent-simulator" },
        { icon: FaUserAstronaut, label: "Avatar", path: "/avatar" },
    ];

    // EMS-specific menu items for students
    const emsMenuItems = currentRole === 'student' ? [
        { icon: FaBookOpen, label: "My Classes", path: "/ems/classes" },
        { icon: FaCalendarAlt, label: "My Schedule", path: "/ems/schedule" },
        { icon: FaBullhorn, label: "Announcements", path: "/ems/announcements" },
        { icon: FaCheckCircle, label: "Attendance", path: "/ems/attendance" },
        { icon: FaChalkboardTeacher, label: "My Teachers", path: "/ems/teachers" },
    ] : [];



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
                    <span className="text-xl font-bold font-heading text-white">Menu</span>
                </div>

                <div className="glass-panel p-3 flex-grow flex flex-col justify-between border border-white/10 shadow-xl rounded-2xl overflow-hidden bg-black/40 lg:bg-black/60">

                    {/* Main Menu */}
                    <div className="flex flex-col gap-2 overflow-y-auto no-scrollbar">
                        {menuItems.map((item, index) => (
                            <NavLink
                                key={index}
                                to={item.path}
                                onClick={closeSidebar}
                                className={({ isActive }) => `
                    flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300 group
                    ${isActive
                                        ? 'bg-gradient-to-r from-orange-600 to-amber-600 text-white shadow-lg border border-white/20 transform scale-105'
                                        : 'bg-white/5 text-gray-300 hover:text-white hover:pl-6 border border-transparent'}
                  `}
                            >
                                <item.icon className="text-lg opacity-80 group-hover:opacity-100" />
                                <span className="text-sm font-medium tracking-wide">{item.label}</span>
                            </NavLink>
                        ))}

                        {/* EMS Menu Items Separator */}
                        {emsMenuItems.length > 0 && (
                            <>
                                <div className="h-px bg-white/10 my-2" />
                                <div className="px-4 py-2">
                                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">School</span>
                                </div>
                                {emsMenuItems.map((item, index) => (
                                    <NavLink
                                        key={`ems-${index}`}
                                        to={item.path}
                                        onClick={closeSidebar}
                                        className={({ isActive }) => `
                            flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300 group
                            ${isActive
                                                ? 'bg-gradient-to-r from-orange-600 to-amber-600 text-white shadow-lg border border-white/20 transform scale-105'
                                                : 'bg-white/5 text-gray-300 hover:text-white hover:pl-6 border border-transparent'}
                          `}
                                    >
                                        <item.icon className="text-lg opacity-80 group-hover:opacity-100" />
                                        <span className="text-sm font-medium tracking-wide">{item.label}</span>
                                    </NavLink>
                                ))}
                            </>
                        )}
                    </div>

                    {/* Footer Actions */}
                    <div className="pt-3 border-t border-white/10 mt-2 space-y-2">
                        {/* Settings */}
                        {!isDemoMode && (
                            <NavLink
                                to="/settings"
                                onClick={closeSidebar}
                                className={({ isActive }) => `
                      flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300 group
                      ${isActive
                                        ? 'bg-gradient-to-r from-gray-700 to-gray-600 text-white shadow-lg border border-white/20'
                                        : 'bg-white/5 text-gray-300 hover:text-white border border-transparent'}
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

export default Sidebar;
