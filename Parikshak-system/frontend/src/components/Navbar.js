import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, PlusCircle, History, Zap, ShieldCheck, TrendingUp, Sparkles, Menu, X } from 'lucide-react';
import ThemeToggle from './ThemeToggle';

const Navbar = () => {
    const location = useLocation();
    const [isOpen, setIsOpen] = useState(false);

    const navLinks = [
        { name: 'Dashboard', path: '/', icon: <LayoutDashboard size={18} /> },
        { name: 'Submit Task', path: '/submit', icon: <PlusCircle size={18} /> },
        { name: 'Task History', path: '/history', icon: <History size={18} /> },
        { name: 'Review Queue', path: '/review-queue', icon: <ShieldCheck size={18} /> },
        { name: 'Journey Timeline', path: '/candidate-timeline', icon: <TrendingUp size={18} /> },
        { name: 'Design System', path: '/design-system', icon: <Sparkles size={18} /> },
    ];

    const isActive = (path) => location.pathname === path;

    return (
        <nav className="sticky top-0 z-50 glass-morphism border-b border-slate-200 dark:border-slate-800">
            <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                <Link to="/" className="flex items-center gap-2 group">
                    <div className="p-2 bg-blue-600 rounded-xl group-hover:rotate-12 transition-transform duration-300">
                        <Zap className="text-white" size={24} />
                    </div>
                    <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400 bg-clip-text text-transparent">
                        Parikshak
                    </span>
                </Link>

                {/* Desktop Navigation */}
                <div className="hidden lg:flex items-center gap-4">
                    {navLinks.map((link) => (
                        <Link
                            key={link.path}
                            to={link.path}
                            className={`flex items-center gap-1.5 px-3 py-2 rounded-lg font-bold text-xs transition-colors duration-200 ${isActive(link.path)
                                    ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30'
                                    : 'text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400'
                                }`}
                        >
                            {link.icon}
                            {link.name}
                        </Link>
                    ))}
                    <div className="h-6 w-px bg-slate-200 dark:bg-slate-800 mx-2" />
                    <ThemeToggle />
                </div>

                {/* Mobile / Tablet Menu Button */}
                <div className="lg:hidden flex items-center gap-4">
                    <ThemeToggle />
                    <button 
                        onClick={() => setIsOpen(!isOpen)} 
                        className="p-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-xl hover:bg-slate-200 transition-colors"
                    >
                        {isOpen ? <X size={20} /> : <Menu size={20} />}
                    </button>
                </div>
            </div>

            {/* Mobile Slide-out Drawer */}
            {isOpen && (
                <div className="lg:hidden fixed inset-y-0 right-0 z-40 w-64 bg-white dark:bg-slate-900 shadow-2xl p-6 flex flex-col gap-6 animate-in slide-in-from-right duration-200 border-l border-slate-200 dark:border-slate-800">
                    <div className="flex justify-between items-center pb-4 border-b border-slate-100 dark:border-slate-800">
                        <span className="font-extrabold text-sm text-slate-500">Navigation Menu</span>
                        <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-slate-600"><X size={20} /></button>
                    </div>
                    <div className="flex flex-col gap-2">
                        {navLinks.map((link) => (
                            <Link
                                key={link.path}
                                to={link.path}
                                onClick={() => setIsOpen(false)}
                                className={`flex items-center gap-3 px-4 py-3 rounded-xl font-bold text-sm transition-all ${isActive(link.path)
                                        ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30'
                                        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/50'
                                    }`}
                            >
                                {link.icon}
                                {link.name}
                            </Link>
                        ))}
                    </div>
                </div>
            )}
        </nav>
    );
};

export default Navbar;