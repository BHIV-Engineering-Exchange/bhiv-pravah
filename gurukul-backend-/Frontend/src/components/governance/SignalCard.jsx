import React from 'react';
import { TrendingUp, TrendingDown, AlertCircle, Activity } from 'lucide-react';

const SignalCard = ({ title, value, unit, signal, trend, description, type = 'info' }) => {
  const getStatusColor = (s) => {
    switch (s?.toLowerCase()) {
      case 'critical': return 'text-red-500 shadow-red-500/20';
      case 'risk': return 'text-yellow-500 shadow-yellow-500/20';
      case 'healthy': return 'text-emerald-500 shadow-emerald-500/20';
      default: return 'text-blue-500 shadow-blue-500/20';
    }
  };

  const getPulseColor = (s) => {
    switch (s?.toLowerCase()) {
      case 'critical': return 'bg-red-500';
      case 'risk': return 'bg-yellow-500';
      case 'healthy': return 'bg-emerald-500';
      default: return 'bg-blue-500';
    }
  };

  return (
    <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur-xl transition-all hover:bg-white/10 group">
      {/* Background Glow */}
      <div className={`absolute -right-10 -top-10 h-32 w-32 rounded-full blur-[60px] opacity-20 ${getPulseColor(signal)}`} />
      
      <div className="flex justify-between items-start mb-4">
        <div>
          <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">{title}</p>
          <div className="flex items-baseline gap-1 mt-1">
            <h3 className="text-3xl font-bold text-white tracking-tight">{value}</h3>
            {unit && <span className="text-sm font-medium text-gray-500">{unit}</span>}
          </div>
        </div>
        
        <div className={`relative flex items-center justify-center h-10 w-10 rounded-xl bg-white/5 border border-white/10 ${getStatusColor(signal)}`}>
          {signal && (
            <span className="absolute -top-1 -right-1 flex h-3 w-3">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${getPulseColor(signal)}`}></span>
              <span className={`relative inline-flex rounded-full h-3 w-3 ${getPulseColor(signal)}`}></span>
            </span>
          )}
          <Activity size={20} />
        </div>
      </div>

      {description && (
        <p className="text-sm text-gray-400 mb-4 line-clamp-2">{description}</p>
      )}

      <div className="flex items-center justify-between pt-4 border-t border-white/5">
        <div className="flex items-center gap-1.5">
          {trend === 'up' ? (
            <TrendingUp size={14} className="text-emerald-500" />
          ) : (
            <TrendingDown size={14} className="text-red-500" />
          )}
          <span className={`text-xs font-medium ${trend === 'up' ? 'text-emerald-500' : 'text-red-500'}`}>
            {trend === 'up' ? '+12%' : '-4%'}
          </span>
          <span className="text-[10px] text-gray-500">vs last week</span>
        </div>
        
        <div className="flex items-center gap-1">
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${getStatusColor(signal)} border-current/20 bg-current/5`}>
            {signal?.toUpperCase() || 'NORMAL'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default SignalCard;
