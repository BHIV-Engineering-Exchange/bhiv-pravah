import React, { useState } from 'react';
import { 
    Settings as SettingsIcon, ShieldCheck, ToggleLeft, ToggleRight, 
    Save, RotateCcw, Sliders, Database, Server, Key, ShieldAlert 
} from 'lucide-react';

const Settings = () => {
    const [activeTab, setActiveTab] = useState('integration'); // 'integration', 'database', 'security'
    const [autoAssign, setAutoAssign] = useState(true);
    const [auditInterval, setAuditInterval] = useState('15s');
    const [dualWriteLock, setDualWriteLock] = useState(true);
    const [observabilityLogLevel, setObservabilityLogLevel] = useState('INFO');
    const [requireSeniorApproval, setRequireSeniorApproval] = useState(true);
    const [operatorRole, setOperatorRole] = useState('governor');
    const [saved, setSaved] = useState(false);

    const handleSave = (e) => {
        if (e) e.preventDefault();
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8 fade-in">
            <header className="border-b border-[#1a243a] pb-6">
                <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-2">
                    <SettingsIcon className="text-slate-400" size={28} /> Settings
                </h1>
                <p className="text-slate-400 font-bold text-xs uppercase tracking-widest mt-1">BHIV Governance Node Controls</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                
                {/* Control categories list */}
                <div className="space-y-4">
                    <div className="bg-[#0c1527] border border-[#1a243a] rounded-2xl p-4 shadow-xl">
                        <h3 className="text-[10px] font-black uppercase tracking-wider text-slate-500 px-3 py-2 border-b border-[#1a243a] mb-2 flex items-center gap-2">
                            <Sliders size={14} className="text-blue-500" /> Categories
                        </h3>
                        <div className="flex flex-col gap-1">
                            <button 
                                type="button" 
                                onClick={() => setActiveTab('integration')}
                                className={`text-left text-xs font-bold px-4 py-2.5 rounded-xl transition-all ${
                                    activeTab === 'integration'
                                        ? 'text-blue-400 bg-blue-500/10 border border-blue-500/20'
                                        : 'text-slate-400 hover:text-slate-200 hover:bg-[#131f37]'
                                }`}
                            >
                                Integration & Assignment
                            </button>
                            <button 
                                type="button" 
                                onClick={() => setActiveTab('database')}
                                className={`text-left text-xs font-bold px-4 py-2.5 rounded-xl transition-all ${
                                    activeTab === 'database'
                                        ? 'text-blue-400 bg-blue-500/10 border border-blue-500/20'
                                        : 'text-slate-400 hover:text-slate-200 hover:bg-[#131f37]'
                                }`}
                            >
                                Database & Sync Ledger
                            </button>
                            <button 
                                type="button" 
                                onClick={() => setActiveTab('security')}
                                className={`text-left text-xs font-bold px-4 py-2.5 rounded-xl transition-all ${
                                    activeTab === 'security'
                                        ? 'text-blue-400 bg-blue-500/10 border border-blue-500/20'
                                        : 'text-slate-400 hover:text-slate-200 hover:bg-[#131f37]'
                                }`}
                            >
                                Security & Authorization
                            </button>
                        </div>
                    </div>
                </div>

                {/* Form Content panel */}
                <div className="md:col-span-2 space-y-6">
                    <form onSubmit={handleSave} className="bg-[#0c1527] border border-[#1a243a] rounded-2xl p-6 space-y-6 shadow-xl">
                        
                        {activeTab === 'integration' && (
                            <div className="space-y-6 fade-in">
                                <h3 className="text-sm font-black uppercase tracking-wider text-slate-400 border-b border-[#1a243a] pb-2 flex items-center gap-2">
                                    <Database size={16} className="text-blue-500" />
                                    Niyantran Integration & Assignment Rules
                                </h3>
                                
                                {/* Auto assign toggle */}
                                <div className="flex items-center justify-between p-3.5 bg-[#131f37] rounded-xl border border-[#1a243a]">
                                    <div>
                                        <h4 className="text-xs font-black text-white">Niyantran Auto-Allocation Mode</h4>
                                        <p className="text-[10px] text-slate-500 font-semibold mt-0.5">Automatically allocate tasks based on minimum workload match index.</p>
                                    </div>
                                    <button 
                                        type="button"
                                        onClick={() => setAutoAssign(!autoAssign)}
                                        className={`p-1 rounded-full transition-colors duration-200 ${autoAssign ? 'text-blue-400' : 'text-slate-500'}`}
                                    >
                                        {autoAssign ? <ToggleRight size={38} /> : <ToggleLeft size={38} />}
                                    </button>
                                </div>

                                <div className="space-y-1.5">
                                    <label className="text-[10px] font-black text-slate-400 uppercase">Audit Sync Interval</label>
                                    <select 
                                        value={auditInterval}
                                        onChange={(e) => setAuditInterval(e.target.value)}
                                        className="w-full bg-[#131f37] border border-[#1a243a] rounded-xl px-3.5 py-2.5 text-xs font-bold text-white focus:outline-none focus:border-blue-500"
                                    >
                                        <option value="5s">5 Seconds</option>
                                        <option value="15s">15 Seconds (Default)</option>
                                        <option value="30s">30 Seconds</option>
                                        <option value="60s">60 Seconds</option>
                                    </select>
                                </div>
                            </div>
                        )}

                        {activeTab === 'database' && (
                            <div className="space-y-6 fade-in">
                                <h3 className="text-sm font-black uppercase tracking-wider text-slate-400 border-b border-[#1a243a] pb-2 flex items-center gap-2">
                                    <Server size={16} className="text-indigo-500" />
                                    Gov-OS Journal & Sync Settings
                                </h3>

                                {/* Dual write lock toggle */}
                                <div className="flex items-center justify-between p-3.5 bg-[#131f37] rounded-xl border border-[#1a243a]">
                                    <div>
                                        <h4 className="text-xs font-black text-white">Gov-OS Journal Thread Locks</h4>
                                        <p className="text-[10px] text-slate-500 font-semibold mt-0.5">Enforce strict transaction write locks on SQLite database mutations.</p>
                                    </div>
                                    <button 
                                        type="button"
                                        onClick={() => setDualWriteLock(!dualWriteLock)}
                                        className={`p-1 rounded-full transition-colors duration-200 ${dualWriteLock ? 'text-blue-400' : 'text-slate-500'}`}
                                    >
                                        {dualWriteLock ? <ToggleRight size={38} /> : <ToggleLeft size={38} />}
                                    </button>
                                </div>

                                <div className="space-y-1.5">
                                    <label className="text-[10px] font-black text-slate-400 uppercase">Log Level Filter</label>
                                    <select 
                                        value={observabilityLogLevel}
                                        onChange={(e) => setObservabilityLogLevel(e.target.value)}
                                        className="w-full bg-[#131f37] border border-[#1a243a] rounded-xl px-3.5 py-2.5 text-xs font-bold text-white focus:outline-none focus:border-blue-500"
                                    >
                                        <option value="DEBUG">DEBUG (All events)</option>
                                        <option value="INFO">INFO (Default)</option>
                                        <option value="WARN">WARN (Only warnings)</option>
                                        <option value="ERROR">ERROR (Only errors)</option>
                                    </select>
                                </div>
                            </div>
                        )}

                        {activeTab === 'security' && (
                            <div className="space-y-6 fade-in">
                                <h3 className="text-sm font-black uppercase tracking-wider text-slate-400 border-b border-[#1a243a] pb-2 flex items-center gap-2">
                                    <Key size={16} className="text-rose-500" />
                                    Security & Authorization Gates
                                </h3>

                                {/* Require Senior Approval token */}
                                <div className="flex items-center justify-between p-3.5 bg-[#131f37] rounded-xl border border-[#1a243a]">
                                    <div>
                                        <h4 className="text-xs font-black text-white">Require Senior Operator Signatures</h4>
                                        <p className="text-[10px] text-slate-500 font-semibold mt-0.5">Force secondary approval verification envelope checking on all task mutations.</p>
                                    </div>
                                    <button 
                                        type="button"
                                        onClick={() => setRequireSeniorApproval(!requireSeniorApproval)}
                                        className={`p-1 rounded-full transition-colors duration-200 ${requireSeniorApproval ? 'text-blue-400' : 'text-slate-500'}`}
                                    >
                                        {requireSeniorApproval ? <ToggleRight size={38} /> : <ToggleLeft size={38} />}
                                    </button>
                                </div>

                                <div className="space-y-1.5">
                                    <label className="text-[10px] font-black text-slate-400 uppercase">Simulated Operator Role</label>
                                    <select 
                                        value={operatorRole}
                                        onChange={(e) => setOperatorRole(e.target.value)}
                                        className="w-full bg-[#131f37] border border-[#1a243a] rounded-xl px-3.5 py-2.5 text-xs font-bold text-white focus:outline-none focus:border-blue-500"
                                    >
                                        <option value="operator">Operator</option>
                                        <option value="reviewer">Reviewer</option>
                                        <option value="governor">Governor (All Rights)</option>
                                    </select>
                                </div>
                            </div>
                        )}

                        {/* Save Actions */}
                        <div className="flex items-center justify-end gap-3 border-t border-[#1a243a] pt-4">
                            <button 
                                type="button"
                                className="px-5 py-2.5 bg-[#131f37] hover:bg-[#1e2e4f] text-slate-400 hover:text-white rounded-xl font-bold text-xs transition-colors border border-[#1a243a]"
                            >
                                Reset Defaults
                            </button>
                            <button 
                                type="submit"
                                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-bold text-xs transition-colors flex items-center gap-2 shadow-lg shadow-blue-500/20"
                            >
                                <Save size={14} /> {saved ? 'Configuration Saved!' : 'Save System Rules'}
                            </button>
                        </div>

                    </form>
                </div>

            </div>
        </div>
    );
};

export default Settings;
