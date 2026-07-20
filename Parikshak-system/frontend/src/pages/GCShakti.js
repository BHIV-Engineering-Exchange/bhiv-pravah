import React from 'react';
import { Sparkles, Shield, Cpu, RefreshCw, Key, Award, FileText } from 'lucide-react';

const GCShakti = () => {
    const checks = [
        { name: 'DFA Validation Boundary Enforcement', status: 'ACTIVE', desc: 'Validates task state changes against a deterministic transition graph.' },
        { name: 'Immutable Log Journaling (Gov-OS)', status: 'ENFORCED', desc: 'Appends atomic transaction details to the sqlite-backed journal ledger.' },
        { name: 'Sri Satya Rule Hardening', status: 'LOCKED', desc: 'Secures rubric evaluation parameters against external drift/spoofing.' },
        { name: 'Replay Continuities Verification', status: 'ACTIVE', desc: 'Runs verification checkpoints to compare replay log checksums.' }
    ];

    return (
        <div className="max-w-4xl mx-auto space-y-8 fade-in">
            <header className="border-b border-[#1a243a] pb-6 flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-2">
                        <Sparkles className="text-indigo-400" size={28} /> GC Shakti Authority Engine
                    </h1>
                    <p className="text-slate-400 font-bold text-xs uppercase tracking-widest mt-1">Ecosystem-level Authority Alignment Gate</p>
                </div>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Visual Architecture */}
                <div className="bg-[#0c1527] border border-[#1a243a] rounded-2xl p-6 shadow-xl space-y-6 flex flex-col justify-between">
                    <div className="space-y-4">
                        <div className="w-12 h-12 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl flex items-center justify-center">
                            <Shield size={24} />
                        </div>
                        <h3 className="text-sm font-black uppercase tracking-wider text-white">Shakti Boundary</h3>
                        <p className="text-xs text-slate-400 leading-relaxed">
                            The Shakti validation gate realigns all parikshak evaluation results with the official Gov-OS requirements repository before tasks are dispatched.
                        </p>
                    </div>

                    <div className="p-4 bg-[#131f37] rounded-xl border border-[#1a243a] space-y-2">
                        <div className="text-[10px] font-black uppercase text-slate-500">Security Standard</div>
                        <div className="text-xs font-black text-white flex items-center gap-1.5">
                            <Key size={14} className="text-indigo-400" /> SECURE-LEDGER-V1
                        </div>
                    </div>
                </div>

                {/* Validation list */}
                <div className="md:col-span-2 space-y-6">
                    <div className="bg-[#0c1527] border border-[#1a243a] rounded-2xl p-6 shadow-xl space-y-4">
                        <h3 className="text-sm font-black uppercase tracking-wider text-slate-400 border-b border-[#1a243a] pb-2 flex items-center gap-2">
                            <Cpu size={16} className="text-indigo-500" /> Active Verification Gates
                        </h3>

                        <div className="space-y-3">
                            {checks.map((check, idx) => (
                                <div key={idx} className="p-4 bg-[#131f37] rounded-xl border border-[#1a243a] flex items-center justify-between gap-4">
                                    <div className="space-y-1">
                                        <h4 className="text-xs font-black text-white">{check.name}</h4>
                                        <p className="text-[10px] text-slate-500 font-semibold leading-normal">{check.desc}</p>
                                    </div>
                                    <span className="shrink-0 text-[10px] font-black px-2.5 py-0.5 rounded border bg-emerald-500/10 text-emerald-400 border-emerald-500/20 uppercase">
                                        {check.status}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default GCShakti;
