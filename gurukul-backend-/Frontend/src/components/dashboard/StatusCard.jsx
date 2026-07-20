import React from 'react';
import { FaHeartbeat, FaCheckCircle, FaExclamationTriangle, FaServer, FaShieldAlt } from 'react-icons/fa';

/**
 * StatusCard Component
 * Flexible status panel that changes rendering based on the active role's status details.
 */
const StatusCard = ({ title, statusSummary, role = 'student' }) => {
    
    const renderContent = () => {
        const lowerRole = role.toLowerCase();
        const summary = statusSummary || {};
        
        if (lowerRole === 'student') {
            const { overall_status, active_goals = [], pacing_coefficient } = summary;
            return (
                <div className="space-y-3">
                    <div className="flex justify-between items-center bg-white/5 p-2.5 rounded-lg border border-white/5">
                        <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Compliance</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            overall_status === 'fully_compliant' ? 'bg-green-500/20 text-green-300' : 'bg-amber-500/20 text-amber-300'
                        }`}>
                            {overall_status?.replace('_', ' ').toUpperCase() || 'COMPLIANT'}
                        </span>
                    </div>
                    {pacing_coefficient && (
                        <div className="flex justify-between items-center bg-white/5 p-2.5 rounded-lg border border-white/5">
                            <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Pacing Coefficient</span>
                            <span className="text-[11px] font-mono text-cyan-400 font-bold">{pacing_coefficient}x</span>
                        </div>
                    )}
                    {active_goals && active_goals.length > 0 && (
                        <div className="bg-white/5 p-2.5 rounded-lg border border-white/5 space-y-1.5">
                            <span className="text-[9px] text-gray-500 font-bold uppercase tracking-wider">Active Goals</span>
                            <ul className="space-y-1">
                                {active_goals.map((goal, idx) => (
                                    <li key={idx} className="text-[10px] text-gray-300 flex items-center gap-1.5">
                                        <span className="w-1 h-1 rounded-full bg-orange-500"></span>
                                        <span className="truncate">{goal}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            );
        }

        if (lowerRole === 'teacher') {
            const { class_name, average_comprehension, warning_flags_count = 0 } = summary;
            return (
                <div className="space-y-3">
                    {class_name && (
                        <div className="flex justify-between items-center bg-white/5 p-2.5 rounded-lg border border-white/5">
                            <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Class Cohort</span>
                            <span className="text-[10px] text-white font-bold truncate max-w-[150px]">{class_name}</span>
                        </div>
                    )}
                    <div className="flex justify-between items-center bg-white/5 p-2.5 rounded-lg border border-white/5">
                        <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Avg Comprehension</span>
                        <span className="text-[11px] font-bold text-green-400">{average_comprehension}%</span>
                    </div>
                    <div className="flex justify-between items-center bg-white/5 p-2.5 rounded-lg border border-white/5">
                        <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Anomaly Warnings</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            warning_flags_count > 0 ? 'bg-red-500/20 text-red-300' : 'bg-green-500/20 text-green-300'
                        }`}>
                            {warning_flags_count} Active
                        </span>
                    </div>
                </div>
            );
        }

        // Admin, Institution Admin or Regional Admin
        const isRegional = lowerRole === 'regional-admin' || lowerRole === 'regional_admin';
        
        if (isRegional) {
            const { redundancy_level, system_survivability_rate, active_replay_workers } = summary;
            return (
                <div className="space-y-3">
                    <div className="flex justify-between items-center bg-white/5 p-2.5 rounded-lg border border-white/5">
                        <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Redundancy</span>
                        <span className="text-[10px] text-purple-300 font-bold">{redundancy_level || 'Triple Region'}</span>
                    </div>
                    <div className="flex justify-between items-center bg-white/5 p-2.5 rounded-lg border border-white/5">
                        <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Survivability Rate</span>
                        <span className="text-[11px] text-emerald-400 font-mono font-bold">{(system_survivability_rate * 100).toFixed(4)}%</span>
                    </div>
                    <div className="flex justify-between items-center bg-white/5 p-2.5 rounded-lg border border-white/5">
                        <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Active Workers</span>
                        <span className="text-[11px] text-cyan-400 font-bold">{active_replay_workers || 0}</span>
                    </div>
                </div>
            );
        } else {
            // Institution Admin
            const { infrastructure_state, sqlite_write_locks_triggered = 0, average_response_time_ms } = summary;
            return (
                <div className="space-y-3">
                    <div className="flex justify-between items-center bg-white/5 p-2.5 rounded-lg border border-white/5">
                        <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Infrastructure</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                            infrastructure_state === 'green' ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'
                        }`}>
                            {infrastructure_state?.toUpperCase() || 'OK'}
                        </span>
                    </div>
                    <div className="flex justify-between items-center bg-white/5 p-2.5 rounded-lg border border-white/5">
                        <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Write Locks Triggered</span>
                        <span className={`text-[10px] font-bold ${sqlite_write_locks_triggered > 0 ? 'text-red-400' : 'text-gray-300'}`}>
                            {sqlite_write_locks_triggered}
                        </span>
                    </div>
                    <div className="flex justify-between items-center bg-white/5 p-2.5 rounded-lg border border-white/5">
                        <span className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Avg Latency</span>
                        <span className="text-[11px] font-mono text-cyan-400 font-bold">{average_response_time_ms ? `${average_response_time_ms} ms` : '145 ms'}</span>
                    </div>
                </div>
            );
        }
    };

    const getHeaderIcon = () => {
        const lowerRole = role.toLowerCase();
        if (lowerRole === 'student') return FaCheckCircle;
        if (lowerRole === 'teacher') return FaExclamationTriangle;
        return FaServer;
    };

    const Icon = getHeaderIcon();

    return (
        <div className="glass-panel p-5 rounded-2xl border border-white/5 bg-black/40 h-full flex flex-col justify-between">
            <div>
                <h4 className="text-[10px] font-bold uppercase tracking-widest text-gray-500 mb-3 flex items-center gap-1.5">
                    <Icon className="text-orange-500" />
                    {title}
                </h4>
                {renderContent()}
            </div>
        </div>
    );
};

export default StatusCard;
