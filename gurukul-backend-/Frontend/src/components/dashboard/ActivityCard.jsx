import React from 'react';
import { FaGraduationCap, FaHeart, FaUserCog, FaHistory } from 'react-icons/fa';

/**
 * ActivityCard Component
 * Displays system and learning events (quiz score, reflections, audit trails).
 */
const ActivityCard = ({ activity }) => {
    const { type, title, timestamp, details } = activity;

    const getActivityTheme = (t) => {
        switch (t) {
            case 'TEST_COMPLETED':
                return {
                    icon: FaGraduationCap,
                    color: 'text-blue-400 bg-blue-500/10 border-blue-500/15',
                    tag: 'Assessment'
                };
            case 'REFLECTION_SUBMITTED':
            case 'STUDENT_REFLECTION':
                return {
                    icon: FaHeart,
                    color: 'text-rose-400 bg-rose-500/10 border-rose-500/15',
                    tag: 'Reflection'
                };
            case 'AUDIT_LOG':
            default:
                return {
                    icon: FaUserCog,
                    color: 'text-gray-400 bg-white/5 border-white/10',
                    tag: 'Audit Log'
                };
        }
    };

    const theme = getActivityTheme(type);
    const Icon = theme.icon;

    return (
        <div className={`p-4 rounded-xl border ${theme.color} flex gap-3 transition-all hover:translate-x-0.5`}>
            <div className="p-2 rounded-lg bg-black/40 self-start">
                <Icon className="text-sm sm:text-base" />
            </div>
            <div className="flex-grow min-w-0">
                <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">{theme.tag}</span>
                    <span className="text-[9px] text-gray-500 font-mono">{new Date(timestamp).toLocaleString()}</span>
                </div>
                <h5 className="text-xs font-bold text-white mt-1 break-words">{title}</h5>

                {details && typeof details === 'object' && Object.keys(details).length > 0 && (
                    <div className="mt-2 text-[10px] text-gray-400 font-mono bg-black/40 rounded-lg p-2 border border-white/5 leading-relaxed overflow-x-auto">
                        {details.score !== undefined && (
                            <div>Score: <span className="text-white font-bold">{details.score}/{details.total}</span> ({details.percentage}%)</div>
                        )}
                        {details.mood_score !== undefined && (
                            <div>Mood Score: <span className="text-rose-300 font-bold">{details.mood_score}/10</span></div>
                        )}
                        {details.old_status !== undefined && (
                            <div>Status changed from <span className="text-red-300 font-bold">{details.old_status}</span></div>
                        )}
                        {details.assigned_to !== undefined && (
                            <div>Assigned to user: <span className="text-blue-300 font-bold font-mono">{details.assigned_to}</span></div>
                        )}
                        {details.type !== undefined && (
                            <div>Type: <span className="text-orange-300">{details.type}</span> | Priority: <span className="text-red-300">{details.priority}</span></div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ActivityCard;
