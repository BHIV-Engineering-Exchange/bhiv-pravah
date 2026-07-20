import React from 'react';
import { Shield, Bell, RefreshCw } from 'lucide-react';

const ExecutiveHeader = ({ level, healthStatus = 'Healthy', onRefresh, loading = false, rightContent }) => {
  const getHealthStyles = (status) => {
    switch (status.toLowerCase()) {
      case 'critical':
      case 'degraded':
      case 'offline':
        return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
      case 'risk':
      case 'warning':
      case 'warming up':
        return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
      default:
        return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    }
  };

  const getHealthPulse = (status) => {
    switch (status.toLowerCase()) {
      case 'critical':
      case 'degraded':
      case 'offline':
        return 'bg-rose-500';
      case 'risk':
      case 'warning':
      case 'warming up':
        return 'bg-amber-500';
      default:
        return 'bg-emerald-500';
    }
  };

  return (
    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6 pb-6 border-b border-white/5">
      <div>
        <div className="flex items-center gap-2 text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1.5">
          <span>Gurukul Drishti</span>
          <span className="text-gray-700">/</span>
          <span>Command Center</span>
          <span className="text-gray-700">/</span>
          <span className="text-orange-500">{level}</span>
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
          {level} Intelligence Control
        </h1>
      </div>

      <div className="flex items-center gap-3 w-full md:w-auto justify-end">
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border ${getHealthStyles(healthStatus)} backdrop-blur-md text-xs font-bold uppercase tracking-wider`}>
          <span className={`h-2 w-2 rounded-full animate-ping ${getHealthPulse(healthStatus)}`} />
          <span>System {healthStatus}</span>
        </div>

        {onRefresh && (
          <button 
            onClick={onRefresh}
            disabled={loading}
            className="p-2.5 rounded-xl bg-white/5 border border-white/10 text-gray-400 hover:text-white transition-colors relative group"
            title="Force Synchronize Telemetry"
          >
            <RefreshCw size={16} className={loading ? "animate-spin text-orange-500" : ""} />
          </button>
        )}

        {rightContent}
      </div>
    </div>
  );
};

export default ExecutiveHeader;
