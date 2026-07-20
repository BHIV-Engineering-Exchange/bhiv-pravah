import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
    Clock, Award, HelpCircle, AlertTriangle, ArrowRight, TrendingUp, 
    CheckCircle, ShieldAlert, Sparkles, UserCheck, User
} from 'lucide-react';
import LoadingState from '../components/LoadingState';

const TimelineCard = ({ currentStage }) => {
    const stages = ['Task', 'Review', 'Testing', 'Fixes', 'Approval', 'Assignment'];
    const currentIdx = stages.findIndex(s => s.toLowerCase() === currentStage?.toLowerCase());
    
    return (
        <div className="p-6 rounded-2xl border border-[#1a243a] bg-[#0c1527] shadow-xl">
            <h4 className="text-[10px] font-black uppercase text-slate-400 tracking-wider mb-5">Engineering Journey Progress</h4>
            <div className="flex items-center justify-between relative">
                {stages.map((stage, i) => {
                    const isPassed = i < currentIdx;
                    const isCurrent = i === currentIdx;
                    return (
                        <div key={stage} className="flex flex-col items-center z-10 flex-1 relative">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center font-black text-xs transition-colors ${
                                isPassed 
                                    ? 'bg-emerald-500 text-white' 
                                    : (isCurrent ? 'bg-blue-600 text-white ring-4 ring-blue-500/20 animate-pulse' : 'bg-[#131f37] text-slate-500 border border-[#1a243a]')
                            }`}>
                                {isPassed ? '✓' : i + 1}
                            </div>
                            <span className={`text-[9px] mt-2.5 font-black uppercase tracking-wider ${
                                isCurrent ? 'text-blue-400' : (isPassed ? 'text-emerald-400' : 'text-slate-500')
                            }`}>
                                {stage}
                            </span>
                        </div>
                    );
                })}
                <div className="absolute top-[16px] left-[5%] right-[5%] h-0.5 bg-[#131f37] -z-10" />
                <div 
                    className="absolute top-[16px] left-[5%] h-0.5 bg-emerald-500 -z-10 transition-all duration-500" 
                    style={{ width: `${(Math.max(0, currentIdx) / (stages.length - 1)) * 90}%` }}
                />
            </div>
        </div>
    );
};

const CandidateTimeline = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [history, setHistory] = useState([]);
    const [error, setError] = useState(null);
    const [selectedCandidate, setSelectedCandidate] = useState('');

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

    const getHeaders = () => {
        const token = localStorage.getItem('parikshak_token');
        return {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {})
        };
    };

    const fetchHistory = async () => {
        try {
            setLoading(true);
            const baseUrl = getBackendUrl();
            const response = await fetch(`${baseUrl}/lifecycle/history`, { headers: getHeaders() });
            if (!response.ok) throw new Error('Failed to load execution history');
            const data = await response.json();
            setHistory(data);
            
            if (data.length > 0) {
                const candidates = [...new Set(data.map(item => item.submitted_by))];
                setSelectedCandidate(candidates[0]);
            } else {
                // Populate default mockup candidate if history is empty
                setSelectedCandidate('Ishan Shirode');
            }
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, []);

    if (loading) return <LoadingState message="Aggregating candidate performance metrics..." />;

    if (error) return (
        <div className="max-w-4xl mx-auto card text-center py-12 bg-[#0c1527] border border-[#1a243a] rounded-2xl shadow-xl">
            <AlertTriangle className="mx-auto text-rose-500 mb-4" size={48} />
            <h3 className="text-xl font-black text-white">Failed to Load Performance Analytics</h3>
            <p className="text-slate-400 text-xs mt-1">{error}</p>
        </div>
    );

    // Group items by candidate
    const candidatesData = {};
    
    // Add default mock items to ensure rich display if empty
    const mockHistory = [
        { submission_id: 'sub-tgov002', task_id: 'T-GOV-002', task_title: 'Parikshak Completion, Integration and Handover Task', submitted_by: 'Ishan Shirode', submitted_at: '2026-07-07T11:42:00Z', score: 84, status: 'pass', evaluation_result: 'PASS' },
        { submission_id: 'sub-tgov001', task_id: 'T-GOV-001', task_title: 'Implement Core SQLite Emitter and Event Store', submitted_by: 'Ishan Shirode', submitted_at: '2026-07-05T16:20:00Z', score: 82, status: 'pass', evaluation_result: 'PASS' },
        { submission_id: 'sub-tgov000', task_id: 'T-GOV-000', task_title: 'Draft Niyantran Assignments Ledger Mutator', submitted_by: 'Ishan Shirode', submitted_at: '2026-07-03T14:15:00Z', score: 68, status: 'borderline', evaluation_result: 'NEED WORK' }
    ];

    const timelineItems = history.length > 0 ? history : mockHistory;

    timelineItems.forEach(item => {
        const name = item.submitted_by || 'Unknown';
        if (!candidatesData[name]) {
            candidatesData[name] = [];
        }
        candidatesData[name].push(item);
    });

    const candidateNames = Object.keys(candidatesData);

    const cognitiveSignals = {
        improving: [],
        stagnating: [],
        needsHelp: [],
        deliverer: []
    };

    candidateNames.forEach(name => {
        const items = [...candidatesData[name]].sort((a, b) => new Date(a.submitted_at) - new Date(b.submitted_at));
        const scores = items.map(item => item.score);
        const passCount = items.filter(item => item.evaluation_result === 'PASS' || item.status === 'pass').length;
        const totalCount = items.length;
        const passRate = totalCount > 0 ? (passCount / totalCount) * 100 : 0;
        const avgScore = scores.reduce((a, b) => a + b, 0) / (scores.length || 1);
        
        let growth = 0;
        if (scores.length >= 2) {
            const mid = Math.floor(scores.length / 2);
            const firstHalf = scores.slice(0, mid);
            const secondHalf = scores.slice(mid);
            const avg1 = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
            const avg2 = secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length;
            growth = avg2 - avg1;
        }

        const candidateStats = {
            name,
            total: totalCount,
            passRate: Math.round(passRate),
            avgScore: Math.round(avgScore),
            growth: Math.round(growth),
            lastSubmission: items[items.length - 1]
        };

        if (passRate >= 75 && avgScore >= 75) {
            cognitiveSignals.deliverer.push(candidateStats);
        } else if (growth >= 10) {
            cognitiveSignals.improving.push(candidateStats);
        } else if (passRate < 50 || (scores.length >= 2 && scores[scores.length - 1] < 50)) {
            cognitiveSignals.needsHelp.push(candidateStats);
        } else {
            cognitiveSignals.stagnating.push(candidateStats);
        }
    });

    const activeCandidateItems = selectedCandidate ? [...candidatesData[selectedCandidate]].sort((a, b) => new Date(b.submitted_at) - new Date(a.submitted_at)) : [];
    
    const getCurrentStage = (lastItem) => {
        if (!lastItem) return 'Task';
        if (lastItem.evaluation_result === 'PASS' || lastItem.status === 'pass') {
            return 'Assignment';
        } else if (lastItem.score > 60) {
            return 'Fixes';
        } else {
            return 'Testing';
        }
    };

    const currentStage = activeCandidateItems.length > 0 ? getCurrentStage(activeCandidateItems[0]) : 'Task';

    return (
        <div className="space-y-8 max-w-7xl mx-auto pb-12 fade-in">
            {/* Header */}
            <header className="border-b border-[#1a243a] pb-6">
                <h1 className="text-3xl font-black text-white tracking-tight">Candidate Journey Timeline</h1>
                <p className="text-slate-400 font-bold text-xs uppercase tracking-widest mt-1">Manager Oversight: Individual Growth & Performance Signals</p>
            </header>

            {/* Manager Cognitive Guidance */}
            <section className="space-y-4">
                <h2 className="text-sm font-black text-slate-400 uppercase tracking-widest flex items-center gap-2">
                    <Sparkles className="text-yellow-400 animate-pulse" size={16} />
                    Manager Cognitive Guidance
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    
                    {/* Consistently Delivers */}
                    <div className="bg-[#0c1527] border-t-4 border-t-emerald-500 border-x border-b border-[#1a243a] p-5 rounded-2xl shadow-xl space-y-4">
                        <div className="flex justify-between items-center text-emerald-400">
                            <span className="text-[10px] font-black uppercase tracking-wider">Consistently Delivers</span>
                            <UserCheck size={16} />
                        </div>
                        <div className="space-y-2">
                            {cognitiveSignals.deliverer.length === 0 ? (
                                <p className="text-[10px] text-slate-500 italic">No candidates classified yet.</p>
                            ) : (
                                cognitiveSignals.deliverer.map(c => (
                                    <div 
                                        key={c.name} 
                                        onClick={() => setSelectedCandidate(c.name)} 
                                        className="p-3 bg-[#131f37] hover:bg-[#1c2c4c] rounded-xl cursor-pointer flex justify-between items-center text-xs border border-[#1a243a] transition-all"
                                    >
                                        <span className="font-bold text-white">{c.name}</span>
                                        <span className="text-emerald-400 font-black">{c.passRate}% pass</span>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Steady Improvement */}
                    <div className="bg-[#0c1527] border-t-4 border-t-blue-500 border-x border-b border-[#1a243a] p-5 rounded-2xl shadow-xl space-y-4">
                        <div className="flex justify-between items-center text-blue-400">
                            <span className="text-[10px] font-black uppercase tracking-wider">Steady Improvement</span>
                            <TrendingUp size={16} />
                        </div>
                        <div className="space-y-2">
                            {cognitiveSignals.improving.length === 0 ? (
                                <p className="text-[10px] text-slate-500 italic">No candidates classified yet.</p>
                            ) : (
                                cognitiveSignals.improving.map(c => (
                                    <div 
                                        key={c.name} 
                                        onClick={() => setSelectedCandidate(c.name)} 
                                        className="p-3 bg-[#131f37] hover:bg-[#1c2c4c] rounded-xl cursor-pointer flex justify-between items-center text-xs border border-[#1a243a] transition-all"
                                    >
                                        <span className="font-bold text-white">{c.name}</span>
                                        <span className="text-blue-400 font-black">+{c.growth} score</span>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Needs Supervision */}
                    <div className="bg-[#0c1527] border-t-4 border-t-rose-500 border-x border-b border-[#1a243a] p-5 rounded-2xl shadow-xl space-y-4">
                        <div className="flex justify-between items-center text-rose-400">
                            <span className="text-[10px] font-black uppercase tracking-wider">Needs Supervision</span>
                            <ShieldAlert size={16} />
                        </div>
                        <div className="space-y-2">
                            {cognitiveSignals.needsHelp.length === 0 ? (
                                <p className="text-[10px] text-slate-500 italic">All clear.</p>
                            ) : (
                                cognitiveSignals.needsHelp.map(c => (
                                    <div 
                                        key={c.name} 
                                        onClick={() => setSelectedCandidate(c.name)} 
                                        className="p-3 bg-[#131f37]/50 hover:bg-[#1c2c4c] rounded-xl cursor-pointer flex justify-between items-center text-xs border border-rose-500/20 transition-all"
                                    >
                                        <span className="font-bold text-white">{c.name}</span>
                                        <span className="text-rose-400 font-black">At Risk</span>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Plateau / Flatline */}
                    <div className="bg-[#0c1527] border-t-4 border-t-amber-500 border-x border-b border-[#1a243a] p-5 rounded-2xl shadow-xl space-y-4">
                        <div className="flex justify-between items-center text-amber-400">
                            <span className="text-[10px] font-black uppercase tracking-wider">Plateau / Flatline</span>
                            <HelpCircle size={16} />
                        </div>
                        <div className="space-y-2">
                            {cognitiveSignals.stagnating.length === 0 ? (
                                <p className="text-[10px] text-slate-500 italic">No candidates classified yet.</p>
                            ) : (
                                cognitiveSignals.stagnating.map(c => (
                                    <div 
                                        key={c.name} 
                                        onClick={() => setSelectedCandidate(c.name)} 
                                        className="p-3 bg-[#131f37] hover:bg-[#1c2c4c] rounded-xl cursor-pointer flex justify-between items-center text-xs border border-[#1a243a] transition-all"
                                    >
                                        <span className="font-bold text-white">{c.name}</span>
                                        <span className="text-amber-400 font-black">{c.avgScore} score</span>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                </div>
            </section>

            {/* Split timeline details */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                
                {/* Select Candidate list */}
                <div className="space-y-4">
                    <h3 className="font-extrabold text-sm text-slate-400 uppercase tracking-widest">Active Candidates</h3>
                    <div className="bg-[#0c1527] border border-[#1a243a] rounded-2xl p-4 shadow-xl space-y-2">
                        {candidateNames.length > 0 ? (
                            candidateNames.map(name => (
                                <button
                                    key={name}
                                    onClick={() => setSelectedCandidate(name)}
                                    className={`w-full text-left px-4 py-3 rounded-xl font-bold text-xs transition-all flex justify-between items-center border ${
                                        selectedCandidate === name
                                            ? 'bg-blue-600 text-white border-blue-500 shadow-md'
                                            : 'bg-[#131f37] border-[#1a243a] hover:bg-[#1c2c4c] text-slate-300 hover:text-white'
                                    }`}
                                >
                                    <span className="flex items-center gap-2">
                                        <User size={12} className={selectedCandidate === name ? 'text-white' : 'text-slate-400'} />
                                        {name}
                                    </span>
                                    <span className="text-[9px] font-mono opacity-80 bg-black/10 px-1.5 py-0.5 rounded">
                                        {candidatesData[name].length} sub
                                    </span>
                                </button>
                            ))
                        ) : (
                            <div className="text-center py-6 text-xs text-slate-500">No active candidates.</div>
                        )}
                    </div>
                </div>

                {/* Timeline display details */}
                {selectedCandidate && (
                    <div className="lg:col-span-3 space-y-6">
                        
                        <TimelineCard currentStage={currentStage} />

                        <div className="space-y-4">
                            <h3 className="font-extrabold text-sm text-slate-400 uppercase tracking-widest">Journey Event Log</h3>
                            
                            <div className="space-y-4 relative border-l border-[#1a243a] pl-6 ml-4">
                                {activeCandidateItems.map((item) => {
                                    const isPassed = item.evaluation_result === 'PASS' || item.status === 'pass';
                                    const dateFormatted = new Date(item.submitted_at).toLocaleDateString('en-US', {
                                        day: 'numeric',
                                        month: 'short',
                                        year: 'numeric'
                                    });

                                    return (
                                        <div key={item.submission_id} className="relative group">
                                            {/* Bullet dot */}
                                            <div className={`absolute -left-[31px] top-1.5 w-4 h-4 rounded-full border-4 bg-[#080d19] transition-colors ${
                                                isPassed ? 'border-emerald-500' : 'border-rose-500'
                                            }`} />
                                            
                                            {/* Card detail */}
                                            <div 
                                                onClick={() => navigate(`/review/${item.submission_id}`)}
                                                className="bg-[#0c1527] border border-[#1a243a] p-5 rounded-2xl hover:border-slate-600 transition-all cursor-pointer shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
                                            >
                                                <div className="space-y-1">
                                                    <div className="flex items-center gap-2.5 flex-wrap">
                                                        <span className="font-black text-white text-xs">{item.task_title}</span>
                                                        <span className="text-[9px] font-mono bg-[#131f37] border border-[#1a243a] px-1.5 py-0.5 rounded text-slate-400">{item.task_id}</span>
                                                    </div>
                                                    <div className="flex items-center gap-4 text-[10px] text-slate-500 font-semibold">
                                                        <span className="flex items-center gap-1"><Clock size={10} /> {dateFormatted}</span>
                                                        <span>ID: {item.submission_id.slice(0, 12)}</span>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-4">
                                                    <div className="text-right">
                                                        <div className="text-sm font-black text-white">{item.score}<span className="text-[9px] font-normal text-slate-500">/100</span></div>
                                                        <span className={`text-[9px] font-black uppercase tracking-wider ${isPassed ? 'text-emerald-400' : 'text-rose-400'}`}>
                                                            {isPassed ? 'PASS' : 'REVISION REQUIRED'}
                                                        </span>
                                                    </div>
                                                    <ArrowRight size={16} className="text-slate-500 group-hover:translate-x-1 group-hover:text-white transition-all" />
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>

                    </div>
                )}

            </div>
        </div>
    );
};

export default CandidateTimeline;
