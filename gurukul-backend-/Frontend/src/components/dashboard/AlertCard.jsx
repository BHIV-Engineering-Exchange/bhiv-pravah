import React, { useState } from 'react';
import { FaExclamationTriangle, FaCheckCircle, FaUserPlus, FaHistory, FaCheck, FaTimes } from 'react-icons/fa';

/**
 * AlertCard Component
 * Displays a single DashboardAlert with visual markers for severity and priority.
 * Supports status transitions (OPEN -> RESOLVED -> CLOSED) and owner assignment.
 */
const AlertCard = ({
    alert,
    userRole = 'student',
    onStatusUpdate,
    onAssign,
    updating = false
}) => {
    const { id, type, priority, status, owner_id, created_at, created_by } = alert;
    const [assigneeId, setAssigneeId] = useState('');
    const [showAssignInput, setShowAssignInput] = useState(false);

    const getPriorityStyle = (prio) => {
        switch (prio?.toUpperCase()) {
            case 'CRITICAL':
                return 'bg-red-600/20 border-red-500/40 text-red-200 animate-pulse';
            case 'HIGH':
                return 'bg-red-500/10 border-red-500/25 text-red-300';
            case 'MEDIUM':
                return 'bg-amber-500/10 border-amber-500/25 text-amber-300';
            case 'LOW':
            default:
                return 'bg-blue-500/10 border-blue-500/25 text-blue-300';
        }
    };

    const handleAssignSubmit = (e) => {
        e.preventDefault();
        if (assigneeId.trim() && onAssign) {
            onAssign(id, assigneeId.trim());
            setShowAssignInput(false);
            setAssigneeId('');
        }
    };

    const isStudent = userRole.toLowerCase() === 'student';
    const isTeacher = userRole.toLowerCase() === 'teacher';
    const isAdmin = ['admin', 'institution_admin', 'regional_admin'].includes(userRole.toLowerCase());

    return (
        <div className={`p-4 rounded-xl border flex flex-col justify-between gap-3 transition-all duration-300 ${getPriorityStyle(priority)}`}>
            <div className="flex gap-3 items-start">
                <FaExclamationTriangle className="text-base sm:text-lg shrink-0 mt-0.5" />
                <div className="flex-grow min-w-0">
                    <div className="flex items-center justify-between gap-2">
                        <span className="text-xs font-bold uppercase tracking-wider">{type} Alert</span>
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/5 uppercase font-bold tracking-widest">{priority}</span>
                    </div>
                    <div className="text-[10px] text-gray-400 mt-1 font-mono break-all">ID: {id}</div>
                    {owner_id && (
                        <div className="text-[10px] text-gray-300 mt-1 flex items-center gap-1.5">
                            <span className="font-semibold text-gray-400">Assigned:</span> 
                            <span className="truncate font-mono">{owner_id}</span>
                        </div>
                    )}
                    <div className="text-[9px] text-gray-500 mt-1 flex items-center gap-1">
                        <FaHistory className="text-[8px]" />
                        <span>Created: {new Date(created_at).toLocaleString()}</span>
                    </div>
                </div>
            </div>

            {/* Actions Footer */}
            <div className="border-t border-white/5 pt-2 mt-1 flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-1.5">
                    <span className="text-[9px] uppercase tracking-wider text-gray-400 font-bold">Status:</span>
                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                        status === 'CLOSED' 
                            ? 'bg-green-500/20 text-green-300 border border-green-500/20'
                            : status === 'RESOLVED'
                                ? 'bg-blue-500/20 text-blue-300 border border-blue-500/20'
                                : 'bg-red-500/20 text-red-300 border border-red-500/20'
                    }`}>
                        {status}
                    </span>
                </div>

                <div className="flex items-center gap-1.5 ml-auto">
                    {/* Assignment input toggle for admins/teachers */}
                    {!isStudent && status !== 'CLOSED' && (
                        <div className="relative">
                            {showAssignInput ? (
                                <form onSubmit={handleAssignSubmit} className="flex items-center gap-1 bg-black/60 rounded-lg p-0.5 border border-white/10 absolute right-0 bottom-full mb-1 z-10">
                                    <input 
                                        type="text"
                                        placeholder="User UUID"
                                        value={assigneeId}
                                        onChange={(e) => setAssigneeId(e.target.value)}
                                        className="bg-transparent text-[10px] px-2 py-1 outline-none text-white w-28 font-mono border-none"
                                        autoFocus
                                    />
                                    <button type="submit" className="p-1 text-green-400 hover:text-green-300" title="Confirm">
                                        <FaCheck className="text-[9px]" />
                                    </button>
                                    <button type="button" onClick={() => setShowAssignInput(false)} className="p-1 text-red-400 hover:text-red-300" title="Cancel">
                                        <FaTimes className="text-[9px]" />
                                    </button>
                                </form>
                            ) : null}
                            <button
                                onClick={() => setShowAssignInput(!showAssignInput)}
                                disabled={updating}
                                className="px-2 py-1 rounded bg-white/5 border border-white/10 hover:border-orange-500/30 text-[9px] font-bold text-gray-300 hover:text-white flex items-center gap-1 transition-all"
                            >
                                <FaUserPlus className="text-[8px]" />
                                <span>Assign</span>
                            </button>
                        </div>
                    )}

                    {/* Resolve button for owner (or teacher/admin on behalf) */}
                    {status === 'OPEN' && (
                        <button
                            onClick={() => onStatusUpdate && onStatusUpdate(id, 'RESOLVED')}
                            disabled={updating}
                            className="px-2.5 py-1 rounded bg-orange-600/20 border border-orange-500/30 hover:bg-orange-600/30 text-[9px] font-bold text-orange-300 hover:text-white flex items-center gap-1 transition-all"
                        >
                            <FaCheckCircle className="text-[8px]" />
                            <span>Resolve</span>
                        </button>
                    )}

                    {/* Close button for teachers and admins */}
                    {!isStudent && status === 'RESOLVED' && (
                        <button
                            onClick={() => onStatusUpdate && onStatusUpdate(id, 'CLOSED')}
                            disabled={updating}
                            className="px-2.5 py-1 rounded bg-green-600/20 border border-green-500/30 hover:bg-green-600/30 text-[9px] font-bold text-green-300 hover:text-white flex items-center gap-1 transition-all"
                        >
                            <FaCheckCircle className="text-[8px]" />
                            <span>Close Alert</span>
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AlertCard;
