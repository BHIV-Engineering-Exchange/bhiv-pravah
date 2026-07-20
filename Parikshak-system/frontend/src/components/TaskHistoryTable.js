import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Calendar, ChevronRight, User, History, FileText } from 'lucide-react';
import StatusBadge from './StatusBadge';

const TaskHistoryTable = ({ tasks }) => {
    const navigate = useNavigate();

    if (!tasks || tasks.length === 0) {
        return (
            <div className="text-center py-20 card bg-slate-50/50 border-dashed border-2">
                <div className="mx-auto w-16 h-16 bg-slate-200 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4 text-slate-400">
                    <History size={32} />
                </div>
                <h3 className="text-lg font-bold">No Task History</h3>
                <p className="text-slate-500">Your submitted and reviewed tasks will appear here.</p>
            </div>
        );
    }

    return (
        <div className="card !p-0 overflow-hidden border-none shadow-2xl">
            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-slate-100/50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800">
                            <th className="px-6 py-4 text-xs font-black uppercase tracking-widest text-slate-500">Task Details</th>
                            <th className="px-6 py-4 text-xs font-black uppercase tracking-widest text-slate-500">Score</th>
                            <th className="px-6 py-4 text-xs font-black uppercase tracking-widest text-slate-500">Status</th>
                            <th className="px-6 py-4 text-xs font-black uppercase tracking-widest text-slate-500">PDF</th>
                            <th className="px-6 py-4 text-xs font-black uppercase tracking-widest text-slate-500">Date</th>
                            <th className="px-6 py-4 text-right"></th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                        {tasks.map((task) => (
                            <tr
                                key={task.submission_id}
                                onClick={() => navigate(`/review/${task.submission_id}`)}
                                className="group hover:bg-blue-500/5 cursor-pointer transition-colors duration-200"
                            >
                                <td className="px-6 py-5">
                                    <div className="flex flex-col">
                                        <span className="font-bold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                                            {task.task_title || 'Untitled Task'}
                                        </span>
                                        <span className="text-xs text-slate-500 flex items-center gap-1 mt-1 uppercase tracking-tighter">
                                            <User size={12} />
                                            By: {task.submitted_by || 'Unknown'}
                                        </span>
                                    </div>
                                </td>
                                <td className="px-6 py-5">
                                    <div className="flex items-center gap-2">
                                        <div className={`w-10 h-10 rounded-full ${task.score >= 80 ? 'bg-emerald-500/10 text-emerald-600' : 'bg-slate-100 dark:bg-slate-800'} flex items-center justify-center font-bold text-sm`}>
                                            {task.score || '—'}
                                        </div>
                                    </div>
                                </td>
                                <td className="px-6 py-5">
                                    <StatusBadge status={task.status} />
                                </td>
                                <td className="px-6 py-5">
                                    {task.has_pdf ? (
                                        <div className="flex items-center gap-1 text-[10px] font-black uppercase tracking-tighter text-blue-500 bg-blue-50 dark:bg-blue-900/30 px-2 py-0.5 rounded-full w-fit">
                                            <FileText size={10} />
                                            YES
                                        </div>
                                    ) : (
                                        <span className="text-[10px] font-black uppercase tracking-tighter text-slate-400">NO</span>
                                    )}
                                </td>
                                <td className="px-6 py-5">
                                    <div className="flex items-center gap-2 text-sm text-slate-500">
                                        <Calendar size={14} />
                                        {task.submitted_at ? new Date(task.submitted_at).toLocaleDateString() : 'N/A'}
                                    </div>
                                </td>
                                <td className="px-6 py-5 text-right">
                                    <ChevronRight size={20} className="inline text-slate-300 group-hover:text-blue-500 group-hover:translate-x-1 transition-all" />
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default TaskHistoryTable;
