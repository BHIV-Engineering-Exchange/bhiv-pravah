import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Menu,
  Search,
  Bell,
  ChevronDown,
  User,
  Settings,
  LogOut,
  HelpCircle,
  Shield,
  Calculator,
  Eye,
} from 'lucide-react';
import { useAuthStore } from '../../store/authStore';
import { ThemeDropdown } from '../common/ThemeToggle';
import clsx from 'clsx';

const roleConfig = {
  admin: { label: 'Admin', color: 'bg-destructive/10 text-destructive', icon: Shield },
  accountant: { label: 'Accountant', color: 'bg-primary/10 text-primary', icon: Calculator },
  viewer: { label: 'Viewer', color: 'bg-muted text-muted-foreground', icon: Eye },
  user: { label: 'User', color: 'bg-muted text-muted-foreground', icon: User },
};

const Navbar = ({ onToggleSidebar, onMobileMenuClick }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  const displayName = user?.name || user?.email?.split('@')[0] || 'User';
  const displayRole = user?.role || user?.roles?.[0] || 'user';
  const displayInitial = displayName.charAt(0).toUpperCase();

  const handleLogout = () => {
    logout();
  };

  const notifications = [
    { id: 1, title: 'Invoice #INV-001 paid', time: '2 hours ago', unread: true },
    { id: 2, title: 'New expense pending approval', time: '5 hours ago', unread: true },
    { id: 3, title: 'GST filing reminder', time: '1 day ago', unread: false },
  ];

  return (
    <header className="sticky top-0 z-30 h-18 backdrop-blur-2xl border-b transition-all duration-300 bg-background/75 border-border/40">
      <div className="flex items-center justify-between h-full px-4">
        {/* Left side */}
        <div className="flex items-center gap-4">
          <button
            onClick={onMobileMenuClick}
            className="lg:hidden p-2.5 hover:bg-muted rounded-xl transition-all duration-300"
          >
            <Menu className="w-5 h-5 text-muted-foreground" />
          </button>
          <button
            onClick={onToggleSidebar}
            className="hidden lg:block p-2.5 hover:bg-muted rounded-xl transition-all duration-300"
          >
            <Menu className="w-5 h-5 text-muted-foreground" />
          </button>

          <div className="hidden md:flex items-center">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search invoices, expenses..."
                className="w-80 pl-10 pr-4 py-2.5 bg-muted text-foreground placeholder:text-muted-foreground border-0 rounded-xl text-sm transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-primary focus:bg-background"
              />
            </div>
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-2">
          <ThemeDropdown />

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="relative p-2.5 hover:bg-muted rounded-xl transition-all duration-300"
            >
              <Bell className="w-5 h-5 text-muted-foreground" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-destructive rounded-full animate-pulse"></span>
            </button>

            {showNotifications && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowNotifications(false)}
                />
                <div className="absolute right-0 mt-2 w-80 bg-card rounded-xl shadow-xl border border-border/50 z-20 animate-fade-in">
                  <div className="px-4 py-3 border-b border-border/50">
                    <h3 className="font-semibold text-foreground font-display">Notifications</h3>
                  </div>
                  <div className="max-h-96 overflow-y-auto">
                    {notifications.map((notification) => (
                      <div
                        key={notification.id}
                        className={clsx(
                          'px-4 py-3 hover:bg-muted cursor-pointer border-b border-border/30 last:border-0 transition-colors duration-200',
                          notification.unread && 'bg-primary/5'
                        )}
                      >
                        <p className="text-sm text-foreground">{notification.title}</p>
                        <p className="text-xs text-muted-foreground mt-1">{notification.time}</p>
                      </div>
                    ))}
                  </div>
                  <div className="px-4 py-3 border-t border-border/50">
                    <button className="text-sm text-primary hover:text-primary/80 font-medium transition-colors duration-200">
                      View all notifications
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>

          <button className="p-2.5 hover:bg-muted rounded-xl transition-all duration-300">
            <HelpCircle className="w-5 h-5 text-muted-foreground" />
          </button>

          {/* User menu */}
          <div className="relative ml-2">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 p-1.5 hover:bg-muted rounded-xl transition-all duration-300"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-primary to-primary/80 rounded-full flex items-center justify-center shadow-lg shadow-primary/20">
                <span className="text-sm font-medium text-primary-foreground">
                  {displayInitial}
                </span>
              </div>
              <div className="hidden md:block text-left max-w-[200px]">
                <p className="text-sm font-medium text-foreground truncate">{displayName}</p>
                {user?.email && (
                  <p className="text-xs text-muted-foreground truncate" title={user.email}>{user.email}</p>
                )}
                <span className={clsx(
                  'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
                  roleConfig[displayRole]?.color || 'bg-muted text-muted-foreground'
                )}>
                  {(() => {
                    const RoleIcon = roleConfig[displayRole]?.icon;
                    return RoleIcon ? <RoleIcon className="w-3 h-3" /> : null;
                  })()}
                  {roleConfig[displayRole]?.label || displayRole}
                </span>
              </div>
              <ChevronDown className="w-4 h-4 text-muted-foreground hidden md:block" />
            </button>

            {showUserMenu && (
              <>
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowUserMenu(false)}
                />
                <div className="absolute right-0 mt-2 w-56 bg-card rounded-xl shadow-xl border border-border/50 z-20 animate-fade-in">
                  <div className="px-4 py-3 border-b border-border/50">
                    <p className="text-sm font-medium text-foreground">{displayName}</p>
                    <p className="text-xs text-muted-foreground mb-1">{user?.email}</p>
                    <span className={clsx(
                      'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
                      roleConfig[displayRole]?.color || 'bg-muted text-muted-foreground'
                    )}>
                      {(() => {
                        const RoleIcon = roleConfig[displayRole]?.icon;
                        return RoleIcon ? <RoleIcon className="w-3 h-3" /> : null;
                      })()}
                      {roleConfig[displayRole]?.label || displayRole}
                    </span>
                  </div>
                  <div className="py-2">
                    <button
                      onClick={() => {
                        setShowUserMenu(false);
                        navigate('/settings/company');
                      }}
                      className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-foreground hover:bg-muted rounded-lg mx-1 transition-colors duration-200"
                    >
                      <Settings className="w-4 h-4" />
                      Settings
                    </button>
                  </div>
                  <div className="border-t border-border/50 py-2">
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-destructive hover:bg-destructive/10 rounded-lg mx-1 transition-colors duration-200"
                    >
                      <LogOut className="w-4 h-4" />
                      Logout
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
