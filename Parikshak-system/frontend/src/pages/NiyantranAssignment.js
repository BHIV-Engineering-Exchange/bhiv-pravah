import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
    ArrowLeft, UserPlus, CheckCircle, AlertTriangle, Cpu, Users, 
    ShieldCheck, Database, Zap, BookOpen, Clock, Copy, Check, ChevronRight, User
} from 'lucide-react';
import LoadingState from '../components/LoadingState';

const NiyantranAssignment = () => {
    const { submissionId: paramSubmissionId } = useParams();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [pendingReviews, setPendingReviews] = useState([]);
    const [selectedSubmissionId, setSelectedSubmissionId] = useState('');
    const [recommendation, setRecommendation] = useState(null);
    const [assigned, setAssigned] = useState(false);
    const [copiedTrace, setCopiedTrace] = useState(false);

    // Form inputs
    const [assignee, setAssignee] = useState('');
    const [priority, setPriority] = useState('Medium');
    const [assignMode, setAssignMode] = useState('Auto');
    const [reason, setReason] = useState('');
    const [taskId, setTaskId] = useState('');

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

    // 1. Fetch pending reviews list to populate the "Select Task" dropdown
    const fetchPendingReviews = async () => {
        try {
            setLoading(true);
            const baseUrl = getBackendUrl();
            const response = await fetch(`${baseUrl}/review/pending`, { headers: getHeaders() });
            if (!response.ok) {
                throw new Error(`Failed to load pending queue (HTTP ${response.status})`);
            }
            const data = await response.json();
            setPendingReviews(data);
            
            // Set default selected submission ID
            if (paramSubmissionId && paramSubmissionId !== 'general') {
                setSelectedSubmissionId(paramSubmissionId);
            } else if (data.length > 0) {
                setSelectedSubmissionId(data[0].submission_id);
            } else {
                setLoading(false);
            }
        } catch (err) {
            console.error('Failed to load pending queue:', err);
            setError(err.message);
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchPendingReviews();
    }, [paramSubmissionId]);

    // 2. Fetch recommendations whenever the selected submission ID changes
    useEffect(() => {
        if (selectedSubmissionId) {
            fetchRecommendation(selectedSubmissionId);
        }
    }, [selectedSubmissionId]);

    const fetchRecommendation = async (submissionId) => {
        try {
            setLoading(true);
            const baseUrl = getBackendUrl();
            const response = await fetch(`${baseUrl}/review/assignment-recommendation/${submissionId}`, { headers: getHeaders() });
            if (!response.ok) throw new Error('Failed to load assignment recommendation');
            const data = await response.json();
            setRecommendation(data);
            
            // Pre-fill form inputs
            setAssignee(data.suggested_assignee);
            setPriority(data.priority || 'Medium');
            setReason(data.reason || '');
            setTaskId(data.task_id || '');
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleAssign = async (e) => {
        if (e) e.preventDefault();
        if (!selectedSubmissionId) return;

        try {
            setLoading(true);
            const baseUrl = getBackendUrl();
            
            const payload = {
                submission_id: selectedSubmissionId,
                trace_id: `trace-assign-${selectedSubmissionId.slice(4)}`,
                operator_id: 'Ishan Shirode',
                assignee: assignee,
                priority: priority,
                eta: '2 days',
                reason: reason,
                task_id: taskId
            };

            const response = await fetch(`${baseUrl}/review/assign`, {
                method: 'POST',
                headers: getHeaders(),
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Assignment allocation failed');
            }

            setAssigned(true);
            setError(null);
            setTimeout(() => {
                navigate(`/review/${selectedSubmissionId}`);
            }, 2500);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleCopyTrace = (text) => {
        navigator.clipboard.writeText(text);
        setCopiedTrace(true);
        setTimeout(() => setCopiedTrace(false), 2000);
    };

    if (loading && !recommendation) return <LoadingState message="Connecting to Niyantran auto-assignment engine..." />;

    if (error) return (
        <div className="max-w-4xl mx-auto card text-center py-12 bg-[#0c1527] border border-[#1a243a] rounded-2xl shadow-xl space-y-4">
            <AlertTriangle className="mx-auto text-rose-500" size={56} />
            <h3 className="text-xl font-black text-white">Failed to Load Niyantran Matrix</h3>
            <p className="text-slate-400 text-xs">{error}</p>
            <button onClick={() => navigate('/')} className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all">
                Back to Dashboard
            </button>
        </div>
    );

    if (assigned) return (
        <div className="max-w-4xl mx-auto card text-center py-12 bg-[#0c1527] border border-[#1a243a] rounded-2xl shadow-xl space-y-4">
            <CheckCircle className="mx-auto text-emerald-500 animate-bounce" size={56} />
            <h3 className="text-2xl font-black text-white">Assignment Dispatched</h3>
            <p className="text-slate-400 text-xs max-w-md mx-auto">
                Task allocation committed in Gov-OS ledger journals, Saarthi progress maps, and local Niyantran files successfully.
            </p>
            <p className="text-[10px] text-slate-500 font-mono">Redirecting back to review summary...</p>
        </div>
    );

    // Map backend workload data to rich display properties
    const teamMembers = [
        { name: 'Akash', role: 'Backend Engineer', skills: 'Python, SQLite, APIs', load: '40%', status: 'Available', matchScore: '95%' },
        { name: 'Ansh', role: 'DevOps / Performance', skills: 'CI/CD, Testing, Docker', load: '100%', status: 'Busy', matchScore: '72%' },
        { name: 'Saarthi_Governor', role: 'Automation Specialist', skills: 'QA, Automation, Playwright', load: '0%', status: 'Available', matchScore: '88%' }
    ];

    const selectedMemberInfo = teamMembers.find(m => m.name === assignee) || {
        name: assignee || 'Manual Selection',
        role: 'Assigned workforce',
        load: 'Unknown'
    };

    const generatedTrace = {
        trace_id: selectedSubmissionId ? `trace-assign-${selectedSubmissionId.slice(4)}` : 'trace-assign-genesis',
        schema_version: "v1.0",
        actor: "Ishan Shirode",
        actor_role: "operator",
        timestamp: new Date().toISOString(),
        event_type: "task_assignment",
        payload: {
            submission_id: selectedSubmissionId,
            task_id: taskId,
            assignee: assignee,
            priority: priority,
            eta: '2 days',
            reason: reason
        }
    };

    return (
        <div className="max-w-7xl mx-auto space-y-8 fade-in">
            {/* Header */}
            <div className="flex items-center gap-4">
                <button 
                    onClick={() => navigate(selectedSubmissionId ? `/review/${selectedSubmissionId}` : '/')}
                    className="p-2.5 bg-[#0c1527] hover:bg-[#131f37] text-slate-400 hover:text-white rounded-xl border border-[#1a243a] transition-all"
                >
                    <ArrowLeft size={18} />
                </button>
                <div>
                    <h1 className="text-3xl font-black text-white tracking-tight">Niyantran Task Assignment</h1>
                    <p className="text-slate-400 font-bold text-xs uppercase tracking-widest mt-1">Auto-assignment and team orchestration</p>
                </div>
            </div>

            {/* Selector parameters block */}
            <section className="bg-[#0c1527] border border-[#1a243a] rounded-2xl p-6 shadow-xl grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Select Task Dropdown */}
                <div className="space-y-1.5">
                    <label className="text-[10px] font-black text-slate-400 uppercase">Select Task / Submission</label>
                    <select 
                        value={selectedSubmissionId}
                        onChange={(e) => setSelectedSubmissionId(e.target.value)}
                        className="w-full bg-[#131f37] border border-[#1a243a] rounded-xl px-3.5 py-2.5 text-xs font-bold text-white focus:outline-none focus:border-blue-500"
                    >
                        {pendingReviews.length > 0 ? (
                            pendingReviews.map((r) => (
                                <option key={r.submission_id} value={r.submission_id}>
                                    {r.selected_task_id || 'T-GOV-003'} - {r.task_title}
                                </option>
                            ))
                        ) : (
                            <option value="">No pending reviews in queue</option>
                        )}
                    </select>
                </div>

                {/* Priority Selection */}
                <div className="space-y-1.5">
                    <label className="text-[10px] font-black text-slate-400 uppercase">Priority</label>
                    <select 
                        value={priority}
                        onChange={(e) => setPriority(e.target.value)}
                        className="w-full bg-[#131f37] border border-[#1a243a] rounded-xl px-3.5 py-2.5 text-xs font-bold text-white focus:outline-none focus:border-blue-500"
                    >
                        <option value="Critical">Critical</option>
                        <option value="High">High</option>
                        <option value="Medium">Medium</option>
                        <option value="Low">Low</option>
                    </select>
                </div>

                {/* Assign Mode Selection */}
                <div className="space-y-1.5">
                    <label className="text-[10px] font-black text-slate-400 uppercase">Assign Mode</label>
                    <select 
                        value={assignMode}
                        onChange={(e) => setAssignMode(e.target.value)}
                        className="w-full bg-[#131f37] border border-[#1a243a] rounded-xl px-3.5 py-2.5 text-xs font-bold text-white focus:outline-none focus:border-blue-500"
                    >
                        <option value="Auto">Auto (Recommended)</option>
                        <option value="Manual">Manual Override</option>
                    </select>
                </div>
            </section>

            {/* Split view: Suggestions and Trace */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                <div className="lg:col-span-2 space-y-8">
                    
                    {/* Auto assignment suggestions table */}
                    <section className="bg-[#0c1527] border border-[#1a243a] rounded-2xl p-6 shadow-xl space-y-4">
                        <h3 className="text-sm font-black uppercase tracking-wider text-slate-400 border-b border-[#1a243a] pb-2 flex items-center gap-2">
                            <Users size={16} className="text-indigo-400" />
                            Auto Assignment Suggestions
                        </h3>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-xs">
                                <thead>
                                    <tr className="border-b border-[#1a243a] text-slate-500 font-black uppercase text-[10px]">
                                        <th className="pb-3">Team Member</th>
                                        <th className="pb-3">Role / Skills Match</th>
                                        <th className="pb-3 text-center">Current Load</th>
                                        <th className="pb-3 text-center">Availability</th>
                                        <th className="pb-3 text-center">Match Score</th>
                                        <th className="pb-3 text-right">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-[#1a243a]/50 font-bold">
                                    {teamMembers.map((member, idx) => {
                                        const isAvailable = member.status === 'Available';
                                        return (
                                            <tr key={idx} className="hover:bg-[#131f37]/35 transition-all">
                                                <td className="py-4 flex items-center gap-2.5">
                                                    <div className="w-8 h-8 rounded-full bg-[#131f37] border border-[#1a243a] flex items-center justify-center text-slate-400">
                                                        <User size={14} />
                                                    </div>
                                                    <div>
                                                        <div className="text-white text-xs">{member.name}</div>
                                                        <div className="text-[10px] text-slate-500 mt-0.5">{member.role}</div>
                                                    </div>
                                                </td>
                                                <td className="py-4 text-slate-300 font-semibold">{member.skills}</td>
                                                <td className="py-4 text-center text-slate-400">{member.load}</td>
                                                <td className="py-4 text-center">
                                                    <span className={`text-[9px] font-black uppercase px-2 py-0.5 rounded border ${
                                                        isAvailable 
                                                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                                                            : 'bg-rose-500/10 text-rose-400 border-rose-500/20'
                                                    }`}>
                                                        {member.status}
                                                    </span>
                                                </td>
                                                <td className="py-4 text-center text-indigo-400">{member.matchScore}</td>
                                                <td className="py-4 text-right">
                                                    <button 
                                                        onClick={() => setAssignee(member.name)}
                                                        className={`px-3.5 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-wide border transition-all ${
                                                            assignee === member.name
                                                                ? 'bg-blue-600 text-white border-blue-500 shadow-sm'
                                                                : 'bg-transparent text-slate-400 hover:text-white border-[#1a243a] hover:border-slate-500'
                                                        }`}
                                                    >
                                                        {assignee === member.name ? 'Selected' : 'Assign'}
                                                    </button>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </section>

                    {/* Assignment preview section */}
                    <section className="bg-[#0c1527] border border-[#1a243a] rounded-2xl p-6 shadow-xl space-y-6">
                        <h3 className="text-sm font-black uppercase tracking-wider text-slate-400 border-b border-[#1a243a] pb-2">
                            Assignment Preview
                        </h3>

                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 rounded-xl bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-500">
                                    <User size={22} />
                                </div>
                                <div className="space-y-1">
                                    <h4 className="text-sm font-black text-white">{selectedMemberInfo.name}</h4>
                                    <p className="text-xs text-slate-500 font-bold uppercase tracking-wider">{selectedMemberInfo.role} • Current Load: {selectedMemberInfo.load}</p>
                                </div>
                            </div>

                            <div className="flex gap-4 text-xs font-bold">
                                <div>
                                    <span className="text-[10px] text-slate-500 uppercase block">Estimated Effort</span>
                                    <span className="text-white">6-8 Hours</span>
                                </div>
                                <div>
                                    <span className="text-[10px] text-slate-500 uppercase block">Earliest Start</span>
                                    <span className="text-white">8 Jul 2026</span>
                                </div>
                                <div>
                                    <span className="text-[10px] text-slate-500 uppercase block">ETA</span>
                                    <span className="text-white">9 Jul 2026</span>
                                </div>
                            </div>
                        </div>

                        {/* Justification input */}
                        <div className="space-y-1.5">
                            <label className="text-[10px] font-black text-slate-400 uppercase">Assignment Justification / Reason</label>
                            <textarea 
                                value={reason}
                                onChange={(e) => setReason(e.target.value)}
                                rows={2}
                                className="w-full bg-[#131f37] border border-[#1a243a] rounded-xl px-3.5 py-2.5 text-xs font-semibold text-white focus:outline-none focus:border-blue-500"
                                placeholder="Enter justification taxonomy or manual override explanation"
                            />
                        </div>

                        <div className="flex gap-4 pt-4 border-t border-[#1a243a]">
                            <button 
                                onClick={handleAssign}
                                className="flex-1 px-5 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl text-xs uppercase tracking-wide flex items-center justify-center gap-2 shadow-lg shadow-emerald-600/20 transition-all"
                            >
                                <ShieldCheck size={16} /> Auto Assign in Niyantran
                            </button>
                            <button 
                                onClick={() => navigate(selectedSubmissionId ? `/review/${selectedSubmissionId}` : '/')}
                                className="px-5 py-3 bg-[#131f37] hover:bg-[#1e2e4f] text-slate-400 hover:text-white rounded-xl text-xs font-bold border border-[#1a243a] transition-all"
                            >
                                Open in Niyantran
                            </button>
                        </div>
                    </section>

                </div>

                {/* Right side: Mutation Trace */}
                <div className="space-y-6">
                    {/* Skills Fit */}
                    <div className="bg-[#0c1527] border border-[#1a243a] rounded-2xl p-6 shadow-xl space-y-4">
                        <h3 className="text-sm font-black uppercase tracking-wider text-slate-400 border-b border-[#1a243a] pb-2 flex items-center gap-2">
                            <Zap size={16} className="text-yellow-500" />
                            Skills Fit Taxonomy
                        </h3>
                        <div className="text-center py-4">
                            <div className="text-5xl font-black text-indigo-400">
                                {recommendation ? recommendation.skill_match_percent : '95'}%
                            </div>
                            <span className="text-[10px] font-bold uppercase text-slate-500 block mt-2">Engineers Skill Alignment Ratio</span>
                        </div>
                        <div className="text-xs text-slate-500 leading-relaxed bg-[#131f37] p-3 rounded-xl border border-[#1a243a]">
                            <strong>Dependencies:</strong> {recommendation && recommendation.dependencies ? recommendation.dependencies.join(', ') : 'T-GOV-001, T-GOV-002'}
                        </div>
                    </div>

                    {/* Trace display */}
                    <div className="bg-[#0c1527] border border-[#1a243a] rounded-2xl p-6 shadow-xl space-y-4">
                        <div className="flex justify-between items-center border-b border-[#1a243a] pb-2">
                            <h3 className="text-sm font-black uppercase tracking-wider text-slate-400 flex items-center gap-2">
                                <Database size={16} className="text-emerald-500" />
                                Mutation Scaffold Trace
                            </h3>
                            <button 
                                onClick={() => handleCopyTrace(JSON.stringify(generatedTrace, null, 2))}
                                className="p-1.5 bg-[#131f37] hover:bg-[#1e2e4f] text-slate-400 hover:text-white rounded-lg border border-[#1a243a] transition-all"
                            >
                                {copiedTrace ? <Check className="text-emerald-500" size={12} /> : <Copy size={12} />}
                            </button>
                        </div>
                        <pre className="p-3 bg-[#080d19] border border-[#1a243a] text-indigo-400 text-[10px] font-mono rounded-xl max-h-72 overflow-y-auto whitespace-pre-wrap break-all leading-normal">
                            {JSON.stringify(generatedTrace, null, 2)}
                        </pre>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default NiyantranAssignment;
