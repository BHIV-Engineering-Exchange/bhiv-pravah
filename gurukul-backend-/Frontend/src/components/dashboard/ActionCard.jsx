import React, { useState } from 'react';
import { FaPlay, FaCheck, FaBan, FaUserPlus, FaHistory, FaCheckCircle, FaTimes } from 'react-icons/fa';

/**
 * ActionCard Component
 * Displays a single DashboardAction item.
 * Supports status lifecycle transitions:
 * Created -> Assigned -> In Progress -> Completed -> Closed -> Cancelled
 */
const ActionCard = ({
    action,
    userRole = 'student',
    onStatusUpdate,
    onAssign,
    updating = false
}) => {
    const { id, title, description, status, owner_id, created_at } = action;
    const [assigneeId, setAssigneeId] = useState('');
    const [showAssignInput, setShowAssignInput] = useState(false);

    const getStatusStyle = (stat) => {
        switch (stat) {
            case 'Completed':
                return 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300';
            case 'In Progress':
                return 'bg-purple-500/10 border-purple-500/20 text-purple-300';
            case 'Assigned':
                return 'bg-blue-500/10 border-blue-500/20 text-blue-300';
            case 'Closed':
            case 'Cancelled':
                return 'bg-white/5 border-white/10 text-gray-500';
            case 'Created':
            default:
                return 'bg-white/5 border-white/10 text-gray-300';
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

    const canModify = !['Closed', 'Cancelled'].includes(status);

    return (
        <div className={`p-4 rounded-xl border flex flex-col justify-between gap-3 transition-all duration-300 ${getStatusStyle(status)}`}>
            <div>
                <div className="flex justify-between items-start gap-2 mb-1">
                    <span className="text-xs font-bold font-heading truncate">{title}</span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/5 font-mono font-bold">{status}</span>
                </div>
                {description && <p className="text-[10px] text-gray-400 leading-normal mt-1">{description}</p>}
                <div className="text-[9px] text-gray-500 mt-2 font-mono break-all">ID: {id}</div>
                {owner_id && (
                    <div className="text-[10px] text-gray-300 mt-1 flex items-center gap-1.5">
                        <span className="font-semibold text-gray-400">Owner:</span> 
                        <span className="truncate font-mono">{owner_id}</span>
                    </div>
                )}
                <div className="text-[9px] text-gray-500 mt-1 flex items-center gap-1">
                    <FaHistory className="text-[8px]" />
                    <span>Created: {new Date(created_at).toLocaleString()}</span>
                </div>
            </div>

            {/* Action Buttons */}
            {canModify && (
                <div className="border-t border-white/5 pt-2 mt-1 flex flex-wrap items-center justify-end gap-1.5">
                    {/* Inline Assign Toggle */}
                    {!isStudent && (
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

                    {/* Start action: transition to In Progress */}
                    {['Created', 'Assigned'].includes(status) && (
                        <button
                            onClick={() => onStatusUpdate && onStatusUpdate(id, 'In Progress')}
                            disabled={updating}
                            className="px-2 py-1 rounded bg-purple-600/20 border border-purple-500/30 hover:bg-purple-600/30 text-[9px] font-bold text-purple-300 hover:text-white flex items-center gap-1 transition-all"
                        >
                            <FaPlay className="text-[7px]" />
                            <span>Start</span>
                        </button>
                    )}

                    {/* Complete action: transition to Completed */}
                    {status === 'In Progress' && (
                        <button
                            onClick={() => onStatusUpdate && onStatusUpdate(id, 'Completed')}
                            disabled={updating}
                            className="px-2 py-1 rounded bg-emerald-600/20 border border-emerald-500/30 hover:bg-emerald-600/30 text-[9px] font-bold text-emerald-300 hover:text-white flex items-center gap-1 transition-all"
                        >
                            <FaCheck className="text-[8px]" />
                            <span>Complete</span>
                        </button>
                    )}

                    {/* Close action: transition to Closed */}
                    {!isStudent && status === 'Completed' && (
                        <button
                            onClick={() => onStatusUpdate && onStatusUpdate(id, 'Closed')}
                            disabled={updating}
                            className="px-2 py-1 rounded bg-white/10 border border-white/20 hover:bg-white/20 text-[9px] font-bold text-gray-300 hover:text-white flex items-center gap-1 transition-all"
                        >
                            <FaCheckCircle className="text-[8px]" />
                            <span>Close</span>
                        </button>
                    )}

                    {/* Cancel action */}
                    {status !== 'Completed' && (
                        <button
                            onClick={() => onStatusUpdate && onStatusUpdate(id, 'Cancelled')}
                            disabled={updating}
                            className="px-2 py-1 rounded bg-red-600/10 border border-red-500/20 hover:bg-red-600/20 text-[9px] font-bold text-red-400 hover:text-white flex items-center gap-1 transition-all"
                        >
                            <FaBan className="text-[8px]" />
                            <span>Cancel</span>
                        </button>
                    )}
                </div>
            )}
        </div>
    );
};

export default ActionCard;
