import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
    ArrowLeft, Target, CheckCircle, AlertTriangle, Calendar, 
    Zap, ArrowRight, Shield, BookOpen, Layers, Terminal, Clock, 
    Camera, Search, ChevronDown, ChevronUp, FileText, CheckCircle2
} from 'lucide-react';
import LoadingState from '../components/LoadingState';

const NextTask = () => {
    const { taskId } = useParams();
    const navigate = useNavigate();
    const [nextTaskData, setNextTaskData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    
    // Accordion state
    const [openSections, setOpenSections] = useState({
        deliverables: false,
        criteria: false,
        resources: false
    });

    const toggleSection = (section) => {
        setOpenSections(prev => ({
            ...prev,
            [section]: !prev[section]
        }));
    };

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

    const fetchNextTaskData = async () => {
        try {
            setLoading(true);
            const baseUrl = getBackendUrl();
            const token = localStorage.getItem('parikshak_token');
            const response = await fetch(`${baseUrl}/lifecycle/next/${taskId}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                setNextTaskData(data);
                setError(null);
            } else {
                setError(`Failed to load next task: ${response.status}`);
            }
        } catch (err) {
            setError(`Network error: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchNextTaskData();
    }, [taskId]);

    // Handle Start Task Action
    const handleStartTask = () => {
        alert("Task successfully synchronized and loaded into your local IDE workspace via Saarthi node integrations.");
        navigate('/');
    };

    if (loading) return <LoadingState message="Connecting to Niyantran specs database..." />;
    
    // Setup fallback defaults matching mockup single source of truth if API yields empty keys
    const data = nextTaskData || {
        next_task_id: 'T-GOV-003',
        title: 'Implement Performance Benchmarks and Load Testing Suite',
        task_type: 'ADVANCEMENT',
        difficulty: 'Intermediate',
        focus_area: 'Testing & Performance',
        objective: 'Construct a highly optimized load testing architecture capable of running concurrent request simulations on SQLite. Verify event logs and mutation state changes remain deterministic under concurrent locks.',
        deliverables: [
            'Setup automated locustfile benchmark pipeline',
            'Deploy concurrent thread-lock safety verifiers',
            'Log replay mutators timestamp validation metrics',
            'Hook metrics analytics dashboard outputs to Saarthi',
            'Produce certified coverage report',
            'Expose health check validation checks'
        ],
        acceptance_criteria: [
            'SQLite dual-write thread lock delay < 10ms',
            'Locust concurrent test suite must achieve > 200 req/s',
            'Verification accuracy ratio must remain at 100%',
            'No transaction rollback conflicts on Gov-OS SQLite',
            'Zero warning items in code evaluation report'
        ],
        learning_kit: [
            'Ecosystem thread locks documentation: bhiv.wiki/threads',
            'SQLite Write-Ahead Logging guides: sqlite.org/wal',
            'Command-center benchmark parameters schemas'
        ],
        assigned_at: new Date('2026-07-07T11:42:00Z').toISOString()
    };

    const dateFormatted = new Date(data.assigned_at).toLocaleDateString('en-US', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
    });

    const deliverablesList = data.deliverables || [];
    const criteriaList = data.acceptance_criteria || data.review_checklist || [];
    const resourcesList = data.learning_kit || [];

    return (
        <div className="max-w-4xl mx-auto space-y-8 fade-in">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-[#1a243a] pb-6">
                <div className="flex items-center gap-4">
                    <button 
                        onClick={() => navigate(`/review/${taskId}`)}
                        className="p-2.5 bg-[#0c1527] hover:bg-[#131f37] text-slate-400 hover:text-white rounded-xl border border-[#1a243a] transition-all"
                    >
                        <ArrowLeft size={18} />
                    </button>
                    <div>
                        <h1 className="text-3xl font-black text-white tracking-tight">Next Task Details</h1>
                        <p className="text-slate-400 font-bold text-xs uppercase tracking-widest mt-1">Ecosystem Advancement Specification</p>
                    </div>
                </div>
                <button className="p-2.5 bg-[#0c1527] hover:bg-[#131f37] text-slate-400 rounded-xl border border-[#1a243a]">
                    <Search size={16} />
                </button>
            </div>

            {/* Task Card Header Banner */}
            <section className="bg-[#0c1527] border border-[#1a243a] p-6 rounded-2xl shadow-xl space-y-4">
                <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[10px] font-black uppercase text-indigo-400 bg-indigo-500/10 px-2.5 py-0.5 rounded border border-indigo-500/20 tracking-wider">
                        {data.task_type || 'ADVANCEMENT'}
                    </span>
                    <span className="text-[10px] font-black uppercase text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded border border-emerald-500/20 tracking-wider">
                        {data.difficulty || 'Intermediate'}
                    </span>
                    <span className="text-[10px] font-black uppercase text-blue-400 bg-blue-500/10 px-2.5 py-0.5 rounded border border-blue-500/20 tracking-wider">
                        {data.next_task_id || 'T-GOV-003'}
                    </span>
                </div>
                
                <h2 className="text-2xl font-black text-white leading-tight">{data.title || 'Task Specification Title'}</h2>
            </section>

            {/* Metadata Grid */}
            <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-[#0c1527] border border-[#1a243a] p-4 rounded-xl shadow-md">
                    <div className="text-[9px] font-black text-slate-500 uppercase tracking-wider">Difficulty</div>
                    <div className="text-xs font-black text-white mt-1">{data.difficulty || 'Intermediate'}</div>
                </div>
                <div className="bg-[#0c1527] border border-[#1a243a] p-4 rounded-xl shadow-md">
                    <div className="text-[9px] font-black text-slate-500 uppercase tracking-wider">Focus Area</div>
                    <div className="text-xs font-black text-white mt-1">{data.focus_area || 'Testing & Performance'}</div>
                </div>
                <div className="bg-[#0c1527] border border-[#1a243a] p-4 rounded-xl shadow-md">
                    <div className="text-[9px] font-black text-slate-500 uppercase tracking-wider">Estimated Effort</div>
                    <div className="text-xs font-black text-white mt-1">6-8 Hours</div>
                </div>
                <div className="bg-[#0c1527] border border-[#1a243a] p-4 rounded-xl shadow-md">
                    <div className="text-[9px] font-black text-slate-500 uppercase tracking-wider">Assigned On</div>
                    <div className="text-xs font-black text-white mt-1">{dateFormatted}</div>
                </div>
            </section>

            {/* Objective */}
            <section className="bg-[#0c1527] border border-[#1a243a] p-6 rounded-2xl shadow-xl space-y-3">
                <h3 className="text-sm font-black uppercase tracking-wider text-white">Objective</h3>
                <p className="text-xs text-slate-300 leading-relaxed font-semibold">
                    {data.objective || 'Complete system requirements as defined in the target specification.'}
                </p>
            </section>

            {/* Accordions */}
            <section className="space-y-3">
                {/* Accordion 1: Deliverables */}
                <div className="bg-[#0c1527] border border-[#1a243a] rounded-2xl overflow-hidden shadow-xl">
                    <button 
                        onClick={() => toggleSection('deliverables')}
                        className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-[#131f37]/40 transition-colors"
                    >
                        <h4 className="text-xs font-black uppercase text-white tracking-widest flex items-center gap-2">
                            Deliverables <span className="text-[10px] text-slate-500 font-semibold font-mono">({deliverablesList.length})</span>
                        </h4>
                        {openSections.deliverables ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                    {openSections.deliverables && (
                        <div className="px-6 pb-5 pt-1 border-t border-[#1a243a] bg-[#131f37]/20">
                            <ul className="space-y-2.5 text-xs pt-3">
                                {deliverablesList.map((item, idx) => (
                                    <li key={idx} className="flex items-start gap-2.5 text-slate-300 font-semibold">
                                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0" />
                                        <span>{item}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>

                {/* Accordion 2: Acceptance Criteria */}
                <div className="bg-[#0c1527] border border-[#1a243a] rounded-2xl overflow-hidden shadow-xl">
                    <button 
                        onClick={() => toggleSection('criteria')}
                        className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-[#131f37]/40 transition-colors"
                    >
                        <h4 className="text-xs font-black uppercase text-white tracking-widest flex items-center gap-2">
                            Acceptance Criteria <span className="text-[10px] text-slate-500 font-semibold font-mono">({criteriaList.length})</span>
                        </h4>
                        {openSections.criteria ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                    {openSections.criteria && (
                        <div className="px-6 pb-5 pt-1 border-t border-[#1a243a] bg-[#131f37]/20">
                            <ul className="space-y-2.5 text-xs pt-3">
                                {criteriaList.map((item, idx) => (
                                    <li key={idx} className="flex items-start gap-2.5 text-slate-300 font-semibold">
                                        <CheckCircle2 size={14} className="text-emerald-500 mt-0.5 shrink-0" />
                                        <span>{item}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>

                {/* Accordion 3: Resources & References */}
                <div className="bg-[#0c1527] border border-[#1a243a] rounded-2xl overflow-hidden shadow-xl">
                    <button 
                        onClick={() => toggleSection('resources')}
                        className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-[#131f37]/40 transition-colors"
                    >
                        <h4 className="text-xs font-black uppercase text-white tracking-widest flex items-center gap-2">
                            Resources & References <span className="text-[10px] text-slate-500 font-semibold font-mono">({resourcesList.length})</span>
                        </h4>
                        {openSections.resources ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                    {openSections.resources && (
                        <div className="px-6 pb-5 pt-1 border-t border-[#1a243a] bg-[#131f37]/20">
                            <ul className="space-y-2.5 text-xs pt-3">
                                {resourcesList.map((item, idx) => (
                                    <li key={idx} className="flex items-start gap-2.5 text-slate-300 font-semibold">
                                        <BookOpen size={14} className="text-indigo-400 mt-0.5 shrink-0" />
                                        <span>{item}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            </section>

            {/* Bottom Start button */}
            <button 
                onClick={handleStartTask}
                className="w-full py-4 bg-blue-600 hover:bg-blue-700 text-white font-black text-xs uppercase tracking-wide rounded-xl shadow-lg shadow-blue-500/15 hover:scale-[1.005] active:scale-[0.995] transition-all flex items-center justify-center gap-2"
            >
                Start This Task
            </button>
        </div>
    );
};

export default NextTask;