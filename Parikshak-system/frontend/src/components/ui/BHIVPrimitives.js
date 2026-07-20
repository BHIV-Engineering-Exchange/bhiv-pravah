import React from 'react';
import { 
    Award, Target, FileCode, Shield, RefreshCw, GitCommit, 
    AlertTriangle, Activity, UserPlus, User, CheckCircle, Clock 
} from 'lucide-react';

// 1. Review Card
export const ReviewCard = ({ score, readiness, verdict, title, candidate, time, traceId, onClick }) => {
    const isPassed = verdict === 'PASS' || verdict === 'READY';
    const statusColor = isPassed ? 'text-emerald-500' : (verdict === 'PARTIAL' || verdict === 'NEEDS WORK' ? 'text-amber-500' : 'text-rose-500');
    const bgGradient = isPassed ? 'from-emerald-500/10 to-teal-500/10' : 'from-rose-500/10 to-red-500/10';
    return (
        <div 
            onClick={onClick}
            className={`p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md shadow-lg transition-all duration-300 hover:scale-[1.01] ${onClick ? 'cursor-pointer hover:border-blue-500' : ''}`}
        >
            <div className="flex justify-between items-start mb-4">
                <div>
                    <span className="text-[10px] font-black uppercase text-slate-400 tracking-wider">Operational Review</span>
                    <h3 className="font-extrabold text-slate-900 dark:text-white truncate max-w-[200px] mt-1">{title}</h3>
                </div>
                <div className={`px-2.5 py-1 rounded text-xs font-bold bg-slate-100 dark:bg-slate-800 ${statusColor}`}>
                    {verdict}
                </div>
            </div>
            <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="p-3 bg-slate-50 dark:bg-slate-900/50 rounded-xl">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-none">Readiness</span>
                    <div className="text-xl font-black text-blue-600 dark:text-blue-400 mt-1">{readiness}%</div>
                </div>
                <div className="p-3 bg-slate-50 dark:bg-slate-900/50 rounded-xl">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-none">Score</span>
                    <div className="text-xl font-black text-slate-900 dark:text-white mt-1">{score}<span className="text-xs font-normal text-slate-400">/100</span></div>
                </div>
            </div>
            <div className="text-xs text-slate-500 space-y-1 font-mono">
                <div className="truncate">Candidate: {candidate}</div>
                <div>Trace: {traceId?.slice(0, 16)}...</div>
            </div>
        </div>
    );
};

// 2. Task Card
export const TaskCard = ({ taskId, title, purpose, expectedRuntime, difficulty, onClick }) => {
    return (
        <div 
            onClick={onClick}
            className={`p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md shadow-lg ${onClick ? 'cursor-pointer hover:border-blue-500' : ''}`}
        >
            <div className="flex justify-between items-center mb-3">
                <span className="text-xs font-bold font-mono text-indigo-600 dark:text-indigo-400">{taskId}</span>
                <span className="px-2.5 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">{difficulty}</span>
            </div>
            <h3 className="text-base font-extrabold text-slate-900 dark:text-white mb-2">{title}</h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 mb-4 line-clamp-3 leading-relaxed">{purpose}</p>
            <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <Clock size={12} />
                <span>Runtime: {expectedRuntime || '2 hours'}</span>
            </div>
        </div>
    );
};

// 3. Evidence Card
export const EvidenceCard = ({ label, status, details }) => {
    return (
        <div className="p-4 rounded-xl border border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-slate-900/30 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-500/10 rounded-lg text-blue-500">
                    <FileCode size={16} />
                </div>
                <div>
                    <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 truncate max-w-[150px]">{label}</h4>
                    <span className="text-[10px] text-slate-500">{details}</span>
                </div>
            </div>
            <span className="px-2 py-0.5 text-[9px] font-black uppercase rounded bg-emerald-500/10 text-emerald-500">
                {status || 'VERIFIED'}
            </span>
        </div>
    );
};

// 4. Trace Card
export const TraceCard = ({ traceId, actor, role, timestamp }) => {
    return (
        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50 flex flex-col justify-between gap-3">
            <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider">Ecosystem Trace</span>
                <span className="px-2 py-0.5 text-[9px] font-bold bg-blue-500/10 text-blue-500 rounded">ACTIVE</span>
            </div>
            <div className="font-mono text-xs text-slate-900 dark:text-slate-200 truncate">{traceId}</div>
            <div className="flex justify-between items-center text-[10px] text-slate-500">
                <div>Actor: {actor} ({role})</div>
                <div>{new Date(timestamp).toLocaleTimeString()}</div>
            </div>
        </div>
    );
};

// 5. Replay Card
export const ReplayCard = ({ isDeterministic, matchPercent, details }) => {
    return (
        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800 shadow flex items-center gap-3">
            <div className={`p-2.5 rounded-lg ${isDeterministic ? 'bg-green-500/10 text-green-500' : 'bg-rose-500/10 text-rose-500'}`}>
                <RefreshCw size={16} className={isDeterministic ? '' : 'animate-spin'} />
            </div>
            <div className="flex-1 min-w-0">
                <div className="flex justify-between items-center">
                    <span className="text-xs font-bold">Replay Integrity</span>
                    <span className={`text-xs font-black ${isDeterministic ? 'text-green-500' : 'text-rose-500'}`}>{matchPercent}%</span>
                </div>
                <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate mt-0.5">{details}</p>
            </div>
        </div>
    );
};

// 6. Timeline Card
export const TimelineCard = ({ currentStage }) => {
    const stages = ['Task', 'Review', 'Testing', 'Fixes', 'Approval', 'Assignment'];
    const currentIdx = stages.findIndex(s => s.toLowerCase() === currentStage?.toLowerCase());
    
    return (
        <div className="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm shadow-md">
            <h4 className="text-xs font-black uppercase text-slate-400 tracking-wider mb-4">Engineering Journey Progress</h4>
            <div className="flex items-center justify-between relative">
                {stages.map((stage, i) => {
                    const isPassed = i < currentIdx;
                    const isCurrent = i === currentIdx;
                    return (
                        <div key={stage} className="flex flex-col items-center z-10 flex-1 relative">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs transition-colors ${
                                isPassed 
                                    ? 'bg-emerald-500 text-white' 
                                    : (isCurrent ? 'bg-blue-600 text-white ring-4 ring-blue-500/20' : 'bg-slate-200 dark:bg-slate-700 text-slate-400')
                            }`}>
                                {isPassed ? '✓' : i + 1}
                            </div>
                            <span className={`text-[10px] mt-2 font-bold uppercase ${
                                isCurrent ? 'text-blue-500' : (isPassed ? 'text-emerald-500' : 'text-slate-400')
                            }`}>
                                {stage}
                            </span>
                        </div>
                    );
                })}
                <div className="absolute top-[16px] left-[5%] right-[5%] h-0.5 bg-slate-200 dark:bg-slate-800 -z-10" />
                <div 
                    className="absolute top-[16px] left-[5%] h-0.5 bg-emerald-500 -z-10 transition-all duration-500" 
                    style={{ width: `${(Math.max(0, currentIdx) / (stages.length - 1)) * 90}%` }}
                />
            </div>
        </div>
    );
};

// 7. Risk Card
export const RiskCard = ({ riskType, severity, description, mitigation }) => {
    const isCritical = severity.toLowerCase() === 'critical';
    const severityColor = isCritical 
        ? 'bg-rose-500/10 text-rose-500 border-rose-500/20' 
        : (severity.toLowerCase() === 'high' ? 'bg-orange-500/10 text-orange-500 border-orange-500/20' : 'bg-amber-500/10 text-amber-500 border-amber-500/20');
        
    return (
        <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800 shadow flex flex-col gap-2">
            <div className="flex justify-between items-center">
                <span className="text-xs font-bold text-slate-800 dark:text-slate-200">{riskType}</span>
                <span className={`px-2 py-0.5 text-[9px] font-black rounded border uppercase ${severityColor}`}>{severity}</span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-normal">{description}</p>
            {mitigation && (
                <div className="mt-1 text-[10px] text-slate-400 bg-slate-50 dark:bg-slate-900/50 p-2 rounded">
                    <span className="font-bold text-slate-600 dark:text-slate-300">Mitigation:</span> {mitigation}
                </div>
            )}
        </div>
    );
};

// 8. Metric Card
export const MetricCard = ({ title, value, status, trend }) => {
    return (
        <div className="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md shadow flex items-center justify-between">
            <div>
                <span className="text-xs font-bold uppercase text-slate-400 tracking-wider block mb-1">{title}</span>
                <span className="text-3xl font-black text-slate-900 dark:text-white leading-none">{value}</span>
            </div>
            {trend && (
                <span className={`px-2 py-1 text-xs font-bold rounded flex items-center gap-0.5 ${
                    status === 'up' ? 'bg-emerald-500/10 text-emerald-500' : 'bg-rose-500/10 text-rose-500'
                }`}>
                    {status === 'up' ? '↑' : '↓'} {trend}
                </span>
            )}
        </div>
    );
};

// 9. Assignment Card
export const AssignmentCard = ({ title, assignee, skillMatch, workload, eta, onAssign }) => {
    return (
        <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-800 shadow flex flex-col justify-between gap-4">
            <div>
                <h4 className="font-extrabold text-sm text-slate-800 dark:text-slate-200 truncate">{title}</h4>
                <div className="flex items-center gap-3 mt-3">
                    <div className="w-8 h-8 rounded-full bg-blue-600 text-white font-bold flex items-center justify-center text-xs">
                        {assignee[0]}
                    </div>
                    <div>
                        <div className="text-xs font-bold">{assignee}</div>
                        <div className="text-[10px] text-slate-500">Skills Alignment: {skillMatch}%</div>
                    </div>
                </div>
            </div>
            <div className="flex justify-between items-center text-[10px] text-slate-400 border-t border-slate-100 dark:border-slate-700/50 pt-3">
                <div>Load: {workload} active</div>
                <div>ETA: {eta}</div>
            </div>
            {onAssign && (
                <button 
                    onClick={onAssign}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 rounded-xl text-xs transition-all shadow shadow-blue-500/10"
                >
                    Assign Task
                </button>
            )}
        </div>
    );
};

// 10. Candidate Card
export const CandidateCard = ({ name, activeTasks, skills, completedCount, status }) => {
    return (
        <div className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm shadow flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-2xl bg-indigo-600 text-white font-black flex items-center justify-center text-sm shadow shadow-indigo-600/10">
                    {name[0]}
                </div>
                <div>
                    <h4 className="font-extrabold text-sm text-slate-800 dark:text-slate-200">{name}</h4>
                    <div className="flex flex-wrap gap-1 mt-1">
                        {skills.slice(0, 3).map(skill => (
                            <span key={skill} className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-500 uppercase">{skill}</span>
                        ))}
                    </div>
                </div>
            </div>
            <div className="text-right">
                <span className={`text-[9px] font-black uppercase rounded-lg px-2 py-0.5 inline-block ${
                    status === 'deliverer' ? 'bg-emerald-500/10 text-emerald-500' : (status === 'help' ? 'bg-rose-500/10 text-rose-500' : 'bg-slate-100 dark:bg-slate-800 text-slate-400')
                }`}>
                    {status === 'deliverer' ? 'delivering' : (status === 'help' ? 'needs help' : 'improving')}
                </span>
                <div className="text-[10px] text-slate-400 mt-1">Done: {completedCount} | Active: {activeTasks}</div>
            </div>
        </div>
    );
};
