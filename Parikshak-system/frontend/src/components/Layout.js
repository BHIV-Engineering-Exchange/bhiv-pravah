import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { 
    LayoutDashboard, PlusCircle, History, ShieldCheck, TrendingUp, 
    BarChart3, Zap, Sparkles, Settings, User, Server, Clock, 
    Menu, X, Shield, Activity, HelpCircle, FileText
} from 'lucide-react';
import ThemeToggle from './ThemeToggle';
import { checkBackendHealth } from '../api';

const Layout = ({ children }) => {
    const location = useLocation();
    const navigate = useNavigate();
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [isBackendHealthy, setIsBackendHealthy] = useState(true);

    useEffect(() => {
        const verifyHealth = async () => {
            const healthy = await checkBackendHealth();
            setIsBackendHealthy(healthy);
        };
        verifyHealth();
        const interval = setInterval(verifyHealth, 15000);
        return () => clearInterval(interval);
    }, []);

    const menuItems = [
        { name: 'Dashboard', path: '/', icon: <LayoutDashboard size={18} /> },
        { name: 'Submit Task', path: '/submit', icon: <PlusCircle size={18} /> },
        { name: 'Task History', path: '/history', icon: <History size={18} /> },
        { name: 'Review Queue', path: '/review-queue', icon: <ShieldCheck size={18} /> },
        { name: 'My Performance', path: '/candidate-timeline', icon: <TrendingUp size={18} /> },
        { name: 'Analytics', path: '/analytics', icon: <BarChart3 size={18} /> },
        { name: 'Niyantran Assignments', path: '/assign/general', icon: <Zap size={18} /> },
        { name: 'GC Shakti', path: '/shakti', icon: <Sparkles size={18} /> },
        { name: 'Settings', path: '/settings', icon: <Settings size={18} /> }
    ];

    const mobileBottomItems = [
        { name: 'Home', path: '/', icon: <LayoutDashboard size={20} /> },
        { name: 'Submit', path: '/submit', icon: <PlusCircle size={20} /> },
        { name: 'History', path: '/history', icon: <History size={20} /> },
        { name: 'Profile', path: '/profile', icon: <User size={20} /> }
    ];

    const isActive = (path) => {
        if (path === '/') return location.pathname === '/';
        return location.pathname.startsWith(path.split('/:')[0]);
    };

    const footerBadges = [
        { name: 'Deterministic Evaluation', color: 'text-blue-400 border-blue-500/20 bg-blue-500/5' },
        { name: 'Sri Satya Rule Engine', color: 'text-emerald-400 border-emerald-500/20 bg-emerald-500/5' },
        { name: 'Gov-OS Verified', color: 'text-purple-400 border-purple-500/20 bg-purple-500/5' },
        { name: 'Replay & Lineage', color: 'text-amber-400 border-amber-500/20 bg-amber-500/5' },
        { name: 'Ecosystem Integrated', color: 'text-sky-400 border-sky-500/20 bg-sky-500/5' },
        { name: 'Immutable & Auditable', color: 'text-rose-400 border-rose-500/20 bg-rose-500/5' },
        { name: 'Human-in-Loop Support', color: 'text-pink-400 border-pink-500/20 bg-pink-500/5' }
    ];

    return (
        <div className="min-h-screen flex flex-col md:flex-row bg-[#080d19] dark:bg-[#080d19] text-[#e2e8f0] font-sans antialiased">
            
            {/* Desktop & Tablet left sidebar */}
            <aside className="hidden md:flex flex-col justify-between w-64 lg:w-72 shrink-0 border-r border-[#1a243a] bg-[#0c1527] p-6 h-screen sticky top-0">
                <div className="space-y-8 overflow-y-auto pr-1">
                    {/* Header Logo */}
                    <Link to="/" className="flex items-center gap-2.5 group">
                        <div className="p-2 bg-blue-600 rounded-xl group-hover:rotate-12 transition-all duration-300 shadow-md shadow-blue-600/20">
                            <Shield className="text-white" size={22} />
                        </div>
                        <div className="flex flex-col">
                            <span className="text-lg font-black tracking-tight text-white leading-none">Parikshak</span>
                            <span className="text-[10px] text-slate-400 font-bold tracking-widest uppercase mt-1">BHIV Review Engine</span>
                        </div>
                    </Link>

                    {/* Navigation Items */}
                    <nav className="flex flex-col gap-1">
                        {menuItems.map((item) => (
                            <Link
                                key={item.path}
                                to={item.path === '/assign/general' ? '/assign/general' : item.path}
                                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-bold text-xs transition-all duration-200 ${
                                    isActive(item.path)
                                        ? 'text-blue-400 bg-blue-500/10 border border-blue-500/25 shadow-sm'
                                        : 'text-slate-400 hover:text-slate-200 hover:bg-[#131f37]'
                                }`}
                            >
                                <span className={isActive(item.path) ? 'text-blue-400 animate-pulse' : 'text-slate-500'}>
                                    {item.icon}
                                </span>
                                <span>{item.name}</span>
                            </Link>
                        ))}
                    </nav>
                </div>

                {/* Bottom System Status */}
                <div className="border-t border-[#1a243a] pt-4 mt-4 space-y-3">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <span className={`w-2 h-2 rounded-full ${isBackendHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500 animate-ping'}`} />
                            <span className="text-[10px] font-black tracking-tight text-slate-400 uppercase">System Status</span>
                        </div>
                        <span className="text-[9px] font-extrabold text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 uppercase">
                            {isBackendHealthy ? 'Operational' : 'Degraded'}
                        </span>
                    </div>
                    <div className="flex justify-between items-center text-[10px] text-slate-500 font-semibold">
                        <span>Version: v1.0.0</span>
                        <span>Uptime: 99.98%</span>
                    </div>
                </div>
            </aside>

            {/* Mobile Header */}
            <header className="md:hidden flex items-center justify-between px-5 h-16 bg-[#0c1527] border-b border-[#1a243a] sticky top-0 z-40">
                <Link to="/" className="flex items-center gap-2">
                    <div className="p-1.5 bg-blue-600 rounded-lg text-white">
                        <Shield size={18} />
                    </div>
                    <div className="flex flex-col">
                        <span className="text-sm font-black tracking-tight text-white leading-none">Parikshak</span>
                        <span className="text-[8px] text-slate-400 font-bold tracking-widest uppercase">BHIV Task Engine</span>
                    </div>
                </Link>

                <div className="flex items-center gap-2">
                    <ThemeToggle />
                    <button 
                        onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)} 
                        className="p-2 bg-[#131f37] text-slate-300 rounded-lg"
                    >
                        {isMobileMenuOpen ? <X size={18} /> : <Menu size={18} />}
                    </button>
                </div>
            </header>

            {/* Mobile Menu Side Drawer */}
            {isMobileMenuOpen && (
                <div className="md:hidden fixed inset-y-0 right-0 z-50 w-64 bg-[#0c1527] shadow-2xl p-6 flex flex-col justify-between border-l border-[#1a243a] animate-in slide-in-from-right duration-200">
                    <div className="space-y-6">
                        <div className="flex justify-between items-center pb-3 border-b border-[#1a243a]">
                            <span className="font-black text-xs text-slate-400 uppercase tracking-widest">Navigation Menu</span>
                            <button onClick={() => setIsMobileMenuOpen(false)} className="text-slate-400 hover:text-slate-200">
                                <X size={18} />
                            </button>
                        </div>
                        <nav className="flex flex-col gap-1.5">
                            {menuItems.map((item) => (
                                <Link
                                    key={item.path}
                                    to={item.path === '/assign/general' ? '/assign/general' : item.path}
                                    onClick={() => setIsMobileMenuOpen(false)}
                                    className={`flex items-center gap-3 px-3.5 py-3 rounded-xl font-bold text-xs transition-all ${
                                        isActive(item.path)
                                            ? 'text-blue-400 bg-blue-500/10 border border-blue-500/25'
                                            : 'text-slate-400 hover:bg-[#131f37]'
                                    }`}
                                >
                                    {item.icon}
                                    <span>{item.name}</span>
                                </Link>
                            ))}
                        </nav>
                    </div>
                    <div className="border-t border-[#1a243a] pt-4 text-[10px] text-slate-500 font-semibold space-y-1">
                        <div>System Status: All Systems Operational</div>
                        <div>Version: v1.0.0</div>
                    </div>
                </div>
            )}

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col min-w-0">
                <main className="flex-1 overflow-y-auto px-4 md:px-8 py-6 md:py-8 pb-20 md:pb-24">
                    {children}
                    
                    {/* Bottom Command-Center badges */}
                    <div className="mt-12 pt-8 border-t border-[#1a243a] flex flex-wrap gap-2.5 justify-center">
                        {footerBadges.map((badge, idx) => (
                            <span 
                                key={idx} 
                                className={`text-[10px] font-black uppercase px-3 py-1 rounded-full border tracking-wide transition-all duration-300 hover:scale-[1.03] ${badge.color}`}
                            >
                                {badge.name}
                            </span>
                        ))}
                    </div>
                </main>
            </div>

            {/* Mobile Bottom Tab Bar */}
            <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-[#0c1527] border-t border-[#1a243a] flex justify-around items-center px-4 z-40">
                {mobileBottomItems.map((item) => (
                    <Link
                        key={item.path}
                        to={item.path}
                        className={`flex flex-col items-center justify-center gap-1 transition-colors duration-200 ${
                            isActive(item.path)
                                ? 'text-blue-400'
                                : 'text-slate-400'
                        }`}
                    >
                        {item.icon}
                        <span className="text-[9px] font-extrabold uppercase tracking-tight">{item.name}</span>
                    </Link>
                ))}
            </nav>

        </div>
    );
};

export default Layout;
