import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { History, Eye, ArrowRight, Calendar, User, FileText, RefreshCw, Filter, ArrowLeft } from 'lucide-react';
import LoadingState from '../components/LoadingState';

const TaskHistory = () => {
    const navigate = useNavigate();
    const [historyData, setHistoryData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('All');

    const getBackendUrl = () => {
        let backendUrl = process.env.REACT_APP_API_BASE
            || process.env.REACT_APP_BACKEND_URL
            || 'http://localhost:8000/api/v1';
        backendUrl = backendUrl.replace(/\/+$/, '');
        if (!backendUrl.endsWith('/api/v1')) {
            backendUrl = `${backendUrl}/api/v1`;
        }
        return backendUrl;
    };

    const fetchHistoryData = async () => {
        try {
            setLoading(true);
            const baseUrl = getBackendUrl();
            const token = localStorage.getItem('parikshak_token');
            const response = await fetch(`${baseUrl}/lifecycle/history`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                setHistoryData(data);
                setError(null);
            } else {
                setError(`Failed to load history: ${response.status}`);
            }
        } catch (err) {
            setError(`Network error: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHistoryData();
    }, []);

    // Static fallback items from the single-source-of-truth mockup
    const mockHistory = [
        { submission_id: 'sub-tgov002', task_title: 'Parikshak Completion, Integration and Handover Task', submitted_by: 'Ishan Shirode', submitted_at: '2026-07-07T11:42:00Z', score: 84, status: 'pass', evaluation_result: 'PASS', has_pdf: true },
        { submission_id: 'sub-tgov001', task_title: 'Implement Core SQLite Emitter and Event Store', submitted_by: 'Ishan Shirode', submitted_at: '2026-07-05T16:20:00Z', score: 82, status: 'pass', evaluation_result: 'PASS', has_pdf: false },
        { submission_id: 'sub-tgov000', task_title: 'Draft Niyantran Assignments Ledger Mutator', submitted_by: 'Ishan Shirode', submitted_at: '2026-07-03T14:15:00Z', score: 68, status: 'borderline', evaluation_result: 'NEED WORK', has_pdf: true },
        { submission_id: 'sub-tinit001', task_title: 'Genesis Gov-OS pipeline definition', submitted_by: 'Ishan Shirode', submitted_at: '2026-07-01T10:30:00Z', score: 90, status: 'pass', evaluation_result: 'PASS', has_pdf: false }
    ];

    const displayData = historyData.length > 0 ? historyData : mockHistory;

    const filteredData = displayData.filter(item => {
        const evalResult = (item.evaluation_result || 'FAIL').toUpperCase();
        const statusVal = item.status || 'fail';

        if (activeTab === 'All') return true;
        if (activeTab === 'Pass') return evalResult === 'PASS' && statusVal !== 'borderline';
        if (activeTab === 'Need Work') return evalResult === 'NEED WORK' || statusVal === 'borderline';
        if (activeTab === 'Fail') return evalResult === 'FAIL';
        return true;
    });

    const getStatusStyle = (item) => {
        const evalResult = (item.evaluation_result || 'FAIL').toUpperCase();
        const statusVal = item.status || 'fail';

        if (evalResult === 'PASS' && statusVal !== 'borderline') {
            return {
                label: 'PASS',
                bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
                scoreColor: 'text-emerald-400'
            };
        }
        if (evalResult === 'NEED WORK' || statusVal === 'borderline') {
            return {
                label: 'NEED WORK',
                bg: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
                scoreColor: 'text-amber-400'
            };
        }
        return {
            label: 'FAIL',
            bg: 'bg-rose-500/10 text-rose-400 border-rose-500/20',
            scoreColor: 'text-rose-400'
        };
    };

    if (loading && historyData.length === 0) return <LoadingState message="Synchronizing audit ledger..." />;

    return (
        <div className="max-w-4xl mx-auto space-y-8 fade-in">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#1a243a] pb-6">
                <div className="flex items-center gap-4">
                    <button 
                        onClick={() => navigate('/')} 
                        className="p-2.5 bg-[#0c1527] hover:bg-[#131f37] text-slate-400 hover:text-white rounded-xl border border-[#1a243a] transition-all"
                    >
                        <ArrowLeft size={18} />
                    </button>
                    <div>
                        <h1 className="text-3xl font-black text-white tracking-tight">Task History</h1>
                        <p className="text-slate-400 font-bold text-xs uppercase tracking-widest mt-1">Immutable Verification Ledger</p>
                    </div>
                </div>
                <button 
                    onClick={fetchHistoryData} 
                    className="p-2.5 bg-[#0c1527] hover:bg-[#131f37] text-slate-400 hover:text-white rounded-xl border border-[#1a243a] transition-all"
                >
                    <RefreshCw size={16} />
                </button>
            </div>

            {/* Filter Tabs */}
            <div className="flex border-b border-[#1a243a] gap-2 pb-px overflow-x-auto">
                {['All', 'Pass', 'Need Work', 'Fail'].map((tab) => (
                    <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`px-4 py-3 text-xs font-black uppercase tracking-wider transition-all duration-200 border-b-2 -mb-px shrink-0 ${
                            activeTab === tab
                                ? 'text-blue-400 border-blue-500 bg-blue-500/5'
                                : 'text-slate-400 hover:text-slate-200 border-transparent'
                        }`}
                    >
                        {tab}
                    </button>
                ))}
            </div>

            {/* Task list */}
            {filteredData.length === 0 ? (
                <div className="text-center py-12 bg-[#0c1527] border border-[#1a243a] rounded-2xl">
                    <History className="mx-auto text-slate-500 mb-2.5" size={32} />
                    <p className="text-xs font-bold text-slate-400">No matching submissions found in ledger</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {filteredData.map((task) => {
                        const style = getStatusStyle(task);
                        const dateFormatted = new Date(task.submitted_at).toLocaleDateString('en-US', {
                            day: 'numeric',
                            month: 'short',
                            year: 'numeric'
                        });
                        const timeFormatted = new Date(task.submitted_at).toLocaleTimeString('en-US', {
                            hour: 'numeric',
                            minute: '2-digit'
                        });

                        return (
                            <div 
                                key={task.submission_id}
                                onClick={() => navigate(`/review/${task.submission_id}`)}
                                className="bg-[#0c1527] border border-[#1a243a] p-4 rounded-xl flex items-center justify-between gap-6 hover:scale-[1.005] hover:border-slate-700 transition-all duration-200 cursor-pointer group"
                            >
                                <div className="space-y-1.5 min-w-0">
                                    <div className="flex items-center gap-2 flex-wrap">
                                        <span className="text-[10px] font-black text-slate-400 font-mono uppercase">
                                            {task.submission_id.slice(0, 12)}
                                        </span>
                                        {task.has_pdf && (
                                            <span className="flex items-center gap-1 bg-blue-500/10 text-blue-400 border border-blue-500/20 px-1.5 py-0.25 rounded text-[8px] font-black">
                                                <FileText size={8} /> PDF
                                            </span>
                                        )}
                                    </div>
                                    <h4 className="text-xs font-black text-white group-hover:text-blue-400 transition-colors truncate max-w-[320px] sm:max-w-md">
                                        {task.task_title}
                                    </h4>
                                    <div className="text-[9px] text-slate-500 font-semibold flex items-center gap-1.5">
                                        <span>By {task.submitted_by}</span>
                                        <span>•</span>
                                        <span>{dateFormatted} {timeFormatted}</span>
                                    </div>
                                </div>

                                <div className="text-right shrink-0 flex flex-col items-end gap-2">
                                    <span className={`text-[9px] font-black uppercase px-2.5 py-0.5 rounded border ${style.bg}`}>
                                        {style.label}
                                    </span>
                                    <div className={`text-[10px] font-black ${style.scoreColor}`}>
                                        Score: {task.score}/100
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

export default TaskHistory;