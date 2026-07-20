import React from 'react';

/**
 * KPICard Component
 * Displays a single high-level key performance indicator (KPI).
 * Supports loading skeletons and premium glassmorphic styling.
 */
const KPICard = ({ title, value, subText, color = 'text-orange-400', loading = false, icon: Icon }) => {
    if (loading) {
        return (
            <div className="glass-panel p-5 rounded-2xl border border-white/5 bg-black/40 animate-pulse min-h-[120px] flex flex-col justify-between">
                <div className="h-3 w-1/2 bg-white/10 rounded mb-2"></div>
                <div className="h-8 w-2/3 bg-white/10 rounded mb-2"></div>
                <div className="h-3 w-1/3 bg-white/10 rounded"></div>
            </div>
        );
    }

    return (
        <div className="glass-panel p-5 rounded-2xl border border-white/5 bg-black/40 hover:border-orange-500/20 hover:scale-[1.02] transition-all duration-300 group relative overflow-hidden flex flex-col justify-between min-h-[120px]">
            <div>
                <div className="flex justify-between items-start mb-2">
                    <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">{title}</span>
                    {Icon && (
                        <span className={`p-1.5 rounded-lg bg-white/5 ${color.replace('text-', 'text-opacity-80 text-')}`}>
                            <Icon className="text-sm" />
                        </span>
                    )}
                </div>
                <div className="text-3xl font-bold text-white mb-1 tabular-nums tracking-tight">{value}</div>
            </div>
            {subText && (
                <div className={`text-xs ${color} font-medium mt-1 flex items-center gap-1`}>
                    {subText}
                </div>
            )}
            <div className="absolute -bottom-8 -right-8 w-20 h-20 bg-orange-500/5 rounded-full blur-2xl group-hover:bg-orange-500/10 transition-all duration-300"></div>
        </div>
    );
};

export default KPICard;
