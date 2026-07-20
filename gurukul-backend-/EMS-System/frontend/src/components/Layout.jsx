import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { useDemo } from '../context/DemoContext';

const Layout = ({ children }) => {
  const { user, logout, isSuperAdmin } = useAuth();
  const { isDemoMode, toggleDemoMode } = useDemo();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  // Handle responsive sidebar
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (!mobile) {
        setSidebarOpen(true); // Always show sidebar on desktop
      }
    };

    // Set initial state
    handleResize();

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Close sidebar when navigating on mobile
  useEffect(() => {
    if (isMobile) {
      setSidebarOpen(false);
    }
  }, [location.pathname, isMobile]);

  // Role-based menu items
  const getMenuItems = () => {
    const role = user?.role;

    if (role === 'SUPER_ADMIN') {
      return [
        { id: 'dashboard', label: 'Dashboard', icon: '📊', path: '/dashboard' },
        ...(!isDemoMode ? [
          { id: 'schools', label: 'Schools', icon: '🏫', path: '/dashboard/schools' },
          { id: 'create-school', label: 'Create School', icon: '➕', path: '/dashboard/create-school' },
          { id: 'admins', label: 'Admins', icon: '👥', path: '/dashboard/admins' },
          { id: 'create-admin', label: 'Create Admin', icon: '➕', path: '/dashboard/create-admin' },
          { id: 'users', label: 'All Users', icon: '👤', path: '/dashboard/users' },
        ] : []),
      ];
    } else if (role === 'ADMIN') {
      return [
        { id: 'dashboard', label: 'Dashboard', icon: '📊', path: '/dashboard' },
        { id: 'analytics', label: 'Analytics', icon: '📈', path: '/dashboard/analytics' },
        { id: 'teachers', label: 'Teachers', icon: '👨‍🏫', path: '/dashboard/teachers' },
        { id: 'students', label: 'Students', icon: '👨‍🎓', path: '/dashboard/students' },
        { id: 'parents', label: 'Parents', icon: '👨‍👩‍👧', path: '/dashboard/parents' },
        { id: 'classes', label: 'Classes', icon: '📚', path: '/dashboard/classes' },
        { id: 'timetable', label: 'Timetable', icon: '📅', path: '/dashboard/timetable' },
        { id: 'lessons', label: 'Lessons', icon: '📖', path: '/dashboard/lessons' },
        { id: 'parent-student-linking', label: 'Parent-Student Links', icon: '🔗', path: '/dashboard/parent-student-linking' },
        { id: 'holidays-events', label: 'Holidays & Events', icon: '🎉', path: '/dashboard/holidays-events' },
        { id: 'announcements', label: 'Announcements', icon: '📢', path: '/dashboard/announcements' },
        ...(!isDemoMode ? [{ id: 'reset-password', label: 'Reset Password', icon: '🔐', path: '/dashboard/reset-password' }] : []),
      ];
    } else if (role === 'TEACHER') {
      return [
        { id: 'dashboard', label: 'Dashboard', icon: '📊', path: '/dashboard' },
        { id: 'classes', label: 'My Classes', icon: '📚', path: '/dashboard/classes' },
        { id: 'students', label: 'Students', icon: '👨‍🎓', path: '/dashboard/students' },
        { id: 'lessons', label: 'Lessons', icon: '📖', path: '/dashboard/lessons' },
        { id: 'timetable', label: 'Timetable', icon: '📅', path: '/dashboard/timetable' },
        { id: 'announcements', label: 'Announcements', icon: '📢', path: '/dashboard/announcements' },
        { id: 'attendance', label: 'Attendance', icon: '✅', path: '/dashboard/attendance' },
        ...(!isDemoMode ? [{ id: 'reset-password', label: 'Reset Password', icon: '🔐', path: '/dashboard/reset-password' }] : []),
      ];
    } else if (role === 'PARENT') {
      return [
        { id: 'dashboard', label: 'Dashboard', icon: '📊', path: '/dashboard' },
        { id: 'children', label: 'My Children', icon: '👨‍👩‍👧', path: '/dashboard/children' },
        { id: 'attendance', label: 'Attendance', icon: '✅', path: '/dashboard/attendance' },
        { id: 'announcements', label: 'Announcements', icon: '📢', path: '/dashboard/announcements' },
        ...(!isDemoMode ? [{ id: 'reset-password', label: 'Reset Password', icon: '🔐', path: '/dashboard/reset-password' }] : []),
      ];
    } else if (role === 'STUDENT') {
      return [
        { id: 'dashboard', label: 'Dashboard', icon: '📊', path: '/dashboard' },
        { id: 'classes', label: 'My Classes', icon: '📚', path: '/dashboard/classes' },
        { id: 'teachers', label: 'My Teachers', icon: '👨‍🏫', path: '/dashboard/teachers' },
        { id: 'attendance', label: 'Attendance', icon: '✅', path: '/dashboard/attendance' },
        { id: 'schedule', label: 'Schedule', icon: '📅', path: '/dashboard/schedule' },
        { id: 'announcements', label: 'Announcements', icon: '📢', path: '/dashboard/announcements' },
        ...(!isDemoMode ? [{ id: 'reset-password', label: 'Reset Password', icon: '🔐', path: '/dashboard/reset-password' }] : []),
      ];
    }

    // Default menu for unknown roles
    return [
      { id: 'dashboard', label: 'Dashboard', icon: '📊', path: '/dashboard' },
    ];
  };

  const menuItems = getMenuItems();

  const handleNavigation = (path) => {
    navigate(path);
  };

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const getRoleDisplayName = (role) => {
    const roleNames = {
      'SUPER_ADMIN': 'Super Admin',
      'ADMIN': 'School Admin',
      'TEACHER': 'Teacher',
      'PARENT': 'Parent',
      'STUDENT': 'Student',
    };
    return roleNames[role] || role;
  };

  const getDashboardTitle = (role) => {
    const titles = {
      'SUPER_ADMIN': 'Super Admin Dashboard',
      'ADMIN': 'School Admin Dashboard',
      'TEACHER': 'Teacher Dashboard',
      'PARENT': 'Parent Dashboard',
      'STUDENT': 'Student Dashboard',
    };
    return titles[role] || 'Dashboard';
  };

  const getDashboardSubtitle = (role) => {
    const subtitles = {
      'SUPER_ADMIN': 'Manage schools, admins, and users',
      'ADMIN': 'Manage your school',
      'TEACHER': 'Manage your classes and students',
      'PARENT': 'View your children\'s information',
      'STUDENT': 'View your academic information',
    };
    return subtitles[role] || 'Welcome to your dashboard';
  };

  return (
    <div className="min-h-screen bg-dark-bg flex">
      {/* Mobile Overlay */}
      {isMobile && sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={`
          ${isMobile
            ? `fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300 ease-in-out ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}`
            : `${sidebarOpen ? 'w-64' : 'w-20'} fixed h-full transition-all duration-300`
          }
          bg-dark-surface border-r border-[#1E1E30] text-white flex flex-col
        `}
      >
        {/* Logo */}
        <div className="p-4 md:p-5 border-b border-[#1E1E30] flex-shrink-0">
          <div className="flex items-center justify-between">
            {(sidebarOpen || isMobile) && (
              <h1 className="heading-serif text-xl tracking-tight">
                <span className="text-accent-green">G</span>urukul
              </h1>
            )}
            {!isMobile && (
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 rounded-xl hover:bg-dark-card transition-colors text-gray-400 hover:text-accent-green"
              >
                {sidebarOpen ? '◀' : '▶'}
              </button>
            )}
            {isMobile && (
              <button
                onClick={() => setSidebarOpen(false)}
                className="p-2 rounded-xl hover:bg-dark-card transition-colors text-gray-400 text-xl"
              >
                ✕
              </button>
            )}
          </div>
        </div>

        {/* User Info */}
        <div className="p-3 md:p-4 border-b border-[#1E1E30] flex-shrink-0">
          {(sidebarOpen || isMobile) ? (
            <div>
              <p className="text-[10px] uppercase tracking-widest text-gray-500 font-semibold">Logged in as</p>
              <p className="text-sm font-semibold text-white mt-1">{getRoleDisplayName(user?.role)}</p>
              {user?.email && (
                <p className="text-xs text-gray-500 mt-1 truncate" title={user.email}>
                  {user.email}
                </p>
              )}
            </div>
          ) : (
            <div className="flex justify-center">
              <div className="w-9 h-9 bg-accent-green/15 border border-accent-green/30 rounded-xl flex items-center justify-center text-xs font-bold text-accent-green" title={user?.email || ''}>
                {user?.role?.charAt(0) || 'A'}
              </div>
            </div>
          )}
        </div>

        {/* Navigation Menu - Scrollable */}
        <nav className="flex-1 overflow-y-auto p-2 md:p-3 space-y-1">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                handleNavigation(item.path);
                if (isMobile) setSidebarOpen(false);
              }}
              className={`nav-item ${isActive(item.path) ? 'nav-item-active' : 'nav-item-inactive'}`}
            >
              <span className="text-lg">{item.icon}</span>
              {(sidebarOpen || isMobile) && <span className="font-medium">{item.label}</span>}
            </button>
          ))}
        </nav>

        {/* Logout Button - Fixed at bottom */}
        <div className="p-3 md:p-4 border-t border-[#1E1E30] flex-shrink-0">
          <button
            onClick={() => {
              logout();
              if (isMobile) setSidebarOpen(false);
            }}
            className="w-full flex items-center justify-center space-x-2 md:space-x-3 px-3 md:px-4 py-2.5 md:py-3 rounded-xl btn-danger text-sm md:text-base"
          >
            <span>🚪</span>
            {(sidebarOpen || isMobile) && <span className="font-medium">Logout</span>}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className={`flex-1 transition-all duration-300 ${isMobile ? 'ml-0' : (sidebarOpen ? 'ml-64' : 'ml-20')}`}>
        {/* Top Header */}
        <header className="bg-dark-surface/80 backdrop-blur-md border-b border-[#1E1E30] sticky top-0 z-30">
          <div className="px-4 md:px-6 py-3 md:py-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                {/* Mobile Menu Button */}
                {isMobile && (
                  <button
                    onClick={() => setSidebarOpen(true)}
                    className="p-2 rounded-xl hover:bg-dark-card transition-colors text-gray-400"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                  </button>
                )}
                <div>
                  <h2 className="heading-serif text-lg md:text-2xl">{getDashboardTitle(user?.role)}</h2>
                  <p className="text-xs md:text-sm text-gray-500 hidden sm:block">{getDashboardSubtitle(user?.role)}</p>
                </div>
              </div>
              <div className="flex items-center space-x-4 md:space-x-6">
                {/* Demo Mode Toggle */}
                <div className="flex items-center gap-2 bg-dark-card px-3 py-1.5 rounded-capsule border border-[#2A2A3E]">
                  <span className={`text-[10px] md:text-xs font-bold uppercase tracking-wider ${isDemoMode ? 'text-accent-green' : 'text-gray-500'}`}>Demo</span>
                  <button
                    onClick={toggleDemoMode}
                    className={`relative inline-flex h-5 w-9 items-center rounded-full transition-all duration-300 ${isDemoMode ? 'bg-accent-green' : 'bg-[#2A2A3E]'}`}
                  >
                    <span className={`inline-block h-3.5 w-3.5 transform rounded-full transition-transform duration-300 ${isDemoMode ? 'translate-x-4.5 bg-dark-bg' : 'translate-x-1 bg-gray-500'}`} />
                  </button>
                </div>

                <div className="text-right">
                  <p className="text-xs md:text-sm font-medium text-gray-300 truncate max-w-[120px] md:max-w-none">{user?.email || 'User'}</p>
                  <p className="text-xs text-gray-500 hidden sm:block">{getRoleDisplayName(user?.role)}</p>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-3 md:p-6">{children}</main>
      </div>
    </div>
  );
};

export default Layout;
