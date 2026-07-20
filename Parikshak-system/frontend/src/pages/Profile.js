import React, { useState } from 'react';
import { User, Shield, Key, Copy, Check, LogOut, Award, Cpu } from 'lucide-react';

const Profile = () => {
    const [copiedToken, setCopiedToken] = useState(false);
    const token = localStorage.getItem('parikshak_token') || 'No active token';

    const handleCopyToken = () => {
        navigator.clipboard.writeText(token);
        setCopiedToken(true);
        setTimeout(() => setCopiedToken(false), 2000);
    };

    const handleResetToken = () => {
        localStorage.removeItem('parikshak_token');
        window.location.reload();
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8 fade-in">
            <header className="border-b border-[#1a243a] pb-6">
                <h1 className="text-3xl font-black tracking-tight text-white">Operator Profile</h1>
                <p className="text-slate-400 font-bold text-xs uppercase tracking-widest mt-1">BHIV Governance & Access Credentials</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Profile Card */}
                <div className="bg-[#0c1527] border border-[#1a243a] rounded-2xl p-6 flex flex-col items-center text-center space-y-4 shadow-xl">
                    <div className="w-24 h-24 rounded-full bg-blue-600/10 border border-blue-500/20 flex items-center justify-center text-blue-500 shadow-inner">
                        <User size={48} />
                    </div>
                    <div>
                        <h2 className="text-xl font-black text-white">Ishan Shirode</h2>
                        <p className="text-xs text-slate-400 font-bold uppercase tracking-wider mt-1">Senior Governance Engineer</p>
                    </div>
                    <div className="flex items-center gap-1.5 px-3 py-1 bg-emerald-500/10 text-emerald-400 rounded-full border border-emerald-500/20 text-[10px] font-black uppercase">
                        <Shield size={12} /> Governor Role
                    </div>
                </div>

                {/* Technical Credentials */}
                <div className="md:col-span-2 space-y-6">
                    <div className="bg-[#0c1527] border border-[#1a243a] rounded-2xl p-6 space-y-4 shadow-xl">
                        <h3 className="text-sm font-black uppercase tracking-wider text-slate-400 border-b border-[#1a243a] pb-2 flex items-center gap-2">
                            <Award size={16} className="text-blue-500" />
                            Authority Parameters
                        </h3>
                        <div className="grid grid-cols-2 gap-4 text-xs">
                            <div className="bg-[#131f37] p-3.5 rounded-xl border border-[#1a243a]">
                                <div className="text-slate-500 font-extrabold uppercase">Clearance Level</div>
                                <div className="text-sm font-black text-white mt-1">Level 3 Governor</div>
                            </div>
                            <div className="bg-[#131f37] p-3.5 rounded-xl border border-[#1a243a]">
                                <div className="text-slate-500 font-extrabold uppercase">Workload Capacity</div>
                                <div className="text-sm font-black text-white mt-1">0/3 Active allocations</div>
                            </div>
                            <div className="bg-[#131f37] p-3.5 rounded-xl border border-[#1a243a]">
                                <div className="text-slate-500 font-extrabold uppercase">Primary Cluster</div>
                                <div className="text-sm font-black text-white mt-1">bhiv.core.governance</div>
                            </div>
                            <div className="bg-[#131f37] p-3.5 rounded-xl border border-[#1a243a]">
                                <div className="text-slate-500 font-extrabold uppercase">Assigned Node</div>
                                <div className="text-sm font-black text-white mt-1">Parikshak-Core-Node-01</div>
                            </div>
                        </div>
                    </div>

                    {/* Active Cryptographic Token */}
                    <div className="bg-[#0c1527] border border-[#1a243a] rounded-2xl p-6 space-y-4 shadow-xl">
                        <div className="flex justify-between items-center border-b border-[#1a243a] pb-2">
                            <h3 className="text-sm font-black uppercase tracking-wider text-slate-400 flex items-center gap-2">
                                <Key size={16} className="text-indigo-500" />
                                Active Cryptographic Session Token
                            </h3>
                            <button 
                                onClick={handleResetToken}
                                className="text-[10px] font-black text-rose-400 hover:text-rose-300 uppercase flex items-center gap-1.5"
                            >
                                <LogOut size={12} /> Force Reset
                            </button>
                        </div>
                        <div className="relative">
                            <pre className="bg-[#080d19] border border-[#1a243a] rounded-xl p-4 text-[10px] font-mono text-indigo-400 overflow-x-auto whitespace-pre-wrap break-all h-28 pr-12 select-all leading-relaxed">
                                {token}
                            </pre>
                            <button 
                                onClick={handleCopyToken}
                                className="absolute right-3 top-3 p-2 bg-[#131f37] hover:bg-[#1e2e4f] text-slate-400 hover:text-white rounded-lg border border-[#1a243a] transition-all"
                                title="Copy Token"
                            >
                                {copiedToken ? <Check className="text-emerald-500" size={14} /> : <Copy size={14} />}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Profile;
