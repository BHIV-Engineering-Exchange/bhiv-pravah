import React from 'react';
import { ChevronRight, Shield, Bell, Map, Users, Settings as SettingsIcon, LayoutDashboard, Globe } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

const GovernanceLayout = ({ children, level, healthStatus = 'Healthy' }) => {
  const location = useLocation();

  const levels = [
    { name: 'Teacher', path: '/governance/teacher', icon: Users },
    { name: 'School Admin', path: '/governance/school', icon: LayoutDashboard },
    { name: 'District', path: '/governance/district', icon: Map },
    { name: 'Regional', path: '/governance/regional', icon: Globe },
    { name: 'State', path: '/governance/state', icon: SettingsIcon },
    { name: 'Minister', path: '/governance/minister', icon: Shield },
  ];

  const getHealthColor = (status) => {
    switch (status.toLowerCase()) {
      case 'critical': return 'text-red-500 bg-red-500/10 border-red-500/20';
      case 'risk': return 'text-yellow-500 bg-yellow-500/10 border-yellow-500/20';
      default: return 'text-emerald-500 bg-emerald-500/10 border-emerald-500/20';
    }
  };

  const getPulseAnimation = (status) => {
    switch (status.toLowerCase()) {
      case 'critical': return 'animate-pulse bg-red-500';
      case 'risk': return 'animate-pulse bg-yellow-500';
      default: return 'bg-emerald-500';
    }
  };

  return (
    <div className="w-full min-h-screen bg-[#050505] text-white p-4 sm:p-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-gray-500 uppercase tracking-[0.2em] mb-2">
            <span>Gurukul Intelligence</span>
            <ChevronRight size={12} />
            <span>Governance</span>
            <ChevronRight size={12} />
            <span className="text-accent">{level}</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight bg-gradient-to-r from-white to-white/50 bg-clip-text text-transparent">
            {level} Dashboard
          </h1>
        </div>

        <div className="flex items-center gap-4">
          <div className={`flex items-center gap-3 px-4 py-2 rounded-xl border ${getHealthColor(healthStatus)} backdrop-blur-md`}>
            <div className={`h-2.5 w-2.5 rounded-full ${getPulseAnimation(healthStatus)}`} />
            <span className="text-sm font-bold uppercase tracking-wider">System {healthStatus}</span>
          </div>
          
          <button className="p-2.5 rounded-xl bg-white/5 border border-white/10 text-gray-400 hover:text-white transition-colors relative group">
            <Bell size={20} />
            <span className="absolute top-2 right-2 h-2 w-2 bg-red-500 rounded-full border-2 border-[#050505] group-hover:scale-110 transition-transform" />
          </button>
        </div>
      </div>

      {/* Level Navigation */}
      <div className="flex flex-wrap gap-2 mb-10 p-1.5 rounded-2xl bg-white/5 border border-white/10 w-fit">
        {levels.map((lvl) => {
          const Icon = lvl.icon;
          const isActive = location.pathname === lvl.path;
          return (
            <Link
              key={lvl.name}
              to={lvl.path}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                isActive 
                ? 'bg-white/10 text-white shadow-lg' 
                : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
              }`}
            >
              <Icon size={16} />
              {lvl.name}
            </Link>
          );
        })}
      </div>

      {/* Main Content */}
      <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
        {children}
      </div>
    </div>
  );
};

export default GovernanceLayout;
