import React from 'react';
import { 
    ReviewCard, TaskCard, EvidenceCard, TraceCard, ReplayCard, 
    TimelineCard, RiskCard, MetricCard, AssignmentCard, CandidateCard 
} from '../components/ui/BHIVPrimitives';

const DesignSystem = () => {
    const colors = [
        { name: 'slate-50', hex: '#f8fafc', type: 'Neutral Background Light' },
        { name: 'slate-100', hex: '#f1f5f9', type: 'Neutral Card Light' },
        { name: 'slate-200', hex: '#e2e8f0', type: 'Neutral Border Light' },
        { name: 'slate-500', hex: '#64748b', type: 'Neutral Muted Text' },
        { name: 'slate-800', hex: '#1e293b', type: 'Neutral Card Dark' },
        { name: 'slate-900', hex: '#0f172a', type: 'Neutral Background Dark' },
        { name: 'emerald-500', hex: '#10b981', type: 'PASS / READY State' },
        { name: 'rose-500', hex: '#f43f5e', type: 'FAIL / DANGER State' },
        { name: 'amber-500', hex: '#f59e0b', type: 'BORDERLINE / WARNING State' },
        { name: 'blue-500', hex: '#3b82f6', type: 'REINFORCEMENT / INFO State' },
    ];

    const typography = [
        { token: 'h1', size: 'text-4xl (36px)', weight: 'font-black', desc: 'Page headers, verdict scores' },
        { token: 'h2', size: 'text-2xl (24px)', weight: 'font-bold', desc: 'Card headings, sub-sections' },
        { token: 'h3', size: 'text-lg (18px)', weight: 'font-extrabold', desc: 'Inner block headers' },
        { token: 'body-large', size: 'text-base (16px)', weight: 'font-normal', desc: 'Main details descriptive text' },
        { token: 'body-regular', size: 'text-sm (14px)', weight: 'font-medium', desc: 'Compact parameters' },
        { token: 'caption', size: 'text-xs (12px)', weight: 'font-bold uppercase', desc: 'Subtitles and labels' },
        { token: 'code', size: 'text-xs (12px) mono', weight: 'font-mono', desc: 'Trace IDs, checksums' },
    ];

    return (
        <div className="space-y-12 max-w-7xl mx-auto pb-12 fade-in">
            {/* Header */}
            <header className="border-b border-slate-200 dark:border-slate-800 pb-6">
                <h1 className="text-4xl font-black text-slate-900 dark:text-white tracking-tight">BHIV Design System</h1>
                <p className="text-slate-500 dark:text-slate-400 mt-2">Common Core UI Tokens and Visual Primitive Components</p>
            </header>

            {/* Colors Grid */}
            <section className="space-y-4">
                <h2 className="text-2xl font-bold">1. Colors Palette</h2>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    {colors.map(color => (
                        <div key={color.name} className="p-4 rounded-2xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col gap-2">
                            <div className="h-12 w-full rounded-lg shadow-inner" style={{ backgroundColor: color.hex }} />
                            <div>
                                <div className="font-extrabold text-sm">{color.name}</div>
                                <div className="text-xs font-mono text-slate-500">{color.hex}</div>
                                <div className="text-[10px] text-slate-400 mt-1">{color.type}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Typography */}
            <section className="space-y-4">
                <h2 className="text-2xl font-bold">2. Typography Scale</h2>
                <div className="card space-y-4">
                    {typography.map(t => (
                        <div key={t.token} className="flex flex-col md:flex-row md:items-center justify-between border-b border-slate-100 dark:border-slate-800/80 pb-4 last:border-b-0 last:pb-0">
                            <div>
                                <span className="font-mono text-xs text-blue-500 font-bold">{t.token}</span>
                                <div className="text-xs text-slate-400 mt-0.5">{t.size} • {t.weight} • {t.desc}</div>
                            </div>
                            <div className="mt-2 md:mt-0">
                                {t.token === 'h1' && <h1 className="text-4xl font-black">Verdict PASSED</h1>}
                                {t.token === 'h2' && <h2 className="text-2xl font-bold">Execution Review</h2>}
                                {t.token === 'h3' && <h3 className="text-lg font-extrabold">Evidence Ingest</h3>}
                                {t.token === 'body-large' && <p className="text-base font-normal">Layered architecture verification passed.</p>}
                                {t.token === 'body-regular' && <p className="text-sm font-medium">Verify credentials via Governor registry.</p>}
                                {t.token === 'caption' && <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Muted Parameter</span>}
                                {t.token === 'code' && <code className="text-xs font-mono bg-slate-100 dark:bg-slate-900 px-2 py-1 rounded">trace-hv-2026-001</code>}
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* Visual Primitives Previews */}
            <section className="space-y-6">
                <h2 className="text-2xl font-bold">3. Reusable Primitives Library (10 Component Previews)</h2>
                
                <div className="grid md:grid-cols-2 gap-8">
                    
                    {/* Column 1 */}
                    <div className="space-y-8">
                        <div>
                            <h3 className="text-xs font-black uppercase text-slate-400 tracking-wider mb-2">1. Review Card (Pass / Fail)</h3>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <ReviewCard 
                                    score={92} 
                                    readiness={95} 
                                    verdict="PASS" 
                                    title="Governance Review Engine" 
                                    candidate="Akash" 
                                    traceId="trace-prod-ready-12345" 
                                />
                                <ReviewCard 
                                    score={45} 
                                    readiness={40} 
                                    verdict="FAIL" 
                                    title="System Traversal" 
                                    candidate="Ansh" 
                                    traceId="trace-prod-fail-67890" 
                                />
                            </div>
                        </div>

                        <div>
                            <h3 className="text-xs font-black uppercase text-slate-400 tracking-wider mb-2">2. Task Card</h3>
                            <TaskCard 
                                taskId="T-GOV-002" 
                                title="Dynamic Task Adaptability Engine" 
                                purpose="Implement strict deterministic graph traversal rules for candidate next-task routing without alternative mappings." 
                                expectedRuntime="3-4 hours" 
                                difficulty="intermediate" 
                            />
                        </div>

                        <div>
                            <h3 className="text-xs font-black uppercase text-slate-400 tracking-wider mb-2">3. Evidence Card</h3>
                            <div className="space-y-2">
                                <EvidenceCard label="validation_decision.json" status="VERIFIED" details="Schema alignment trace" />
                                <EvidenceCard label="governance_record.json" status="VERIFIED" details="Governor signature verify" />
                            </div>
                        </div>

                        <div>
                            <h3 className="text-xs font-black uppercase text-slate-400 tracking-wider mb-2">4. Trace Card</h3>
                            <TraceCard 
                                traceId="trace-ui-2026-b3525b3f-8c4c-48a4-841d" 
                                actor="Akash" 
                                role="Level 3 Governor" 
                                timestamp={new Date().toISOString()} 
                            />
                        </div>

                        <div>
                            <h3 className="text-xs font-black uppercase text-slate-400 tracking-wider mb-2">5. Replay Card</h3>
                            <ReplayCard 
                                isDeterministic={true} 
                                matchPercent={100} 
                                details="No divergence found across 3 consecutive replay runs." 
                            />
                        </div>
                    </div>

                    {/* Column 2 */}
                    <div className="space-y-8">
                        <div>
                            <h3 className="text-xs font-black uppercase text-slate-400 tracking-wider mb-2">6. Timeline Card</h3>
                            <TimelineCard currentStage="Testing" />
                        </div>

                        <div>
                            <h3 className="text-xs font-black uppercase text-slate-400 tracking-wider mb-2">7. Risk Card</h3>
                            <div className="space-y-3">
                                <RiskCard 
                                    riskType="Security Vulnerability" 
                                    severity="Critical" 
                                    description="SQL injection vulnerability flagged inside core query builders due to unescaped string interpolations." 
                                    mitigation="Enforce parameter bindings inside raw database execution adapters." 
                                />
                                <RiskCard 
                                    riskType="Ecosystem Integration" 
                                    severity="Medium" 
                                    description="Workload metrics collection timeout from Niyantran API endpoints." 
                                    mitigation="Configure local sqlite cache synchronization." 
                                />
                            </div>
                        </div>

                        <div>
                            <h3 className="text-xs font-black uppercase text-slate-400 tracking-wider mb-2">8. Metric Card</h3>
                            <div className="grid grid-cols-2 gap-4">
                                <MetricCard title="Reviews Today" value={14} status="up" trend="12%" />
                                <MetricCard title="Avg score" value="8.5/10" status="up" trend="4%" />
                            </div>
                        </div>

                        <div>
                            <h3 className="text-xs font-black uppercase text-slate-400 tracking-wider mb-2">9. Assignment Card</h3>
                            <AssignmentCard 
                                title="Resolve System Traversal Failures" 
                                assignee="Akash" 
                                skillMatch={95} 
                                workload={1} 
                                eta="2 days" 
                                onAssign={() => alert('Assigned to Akash')}
                            />
                        </div>

                        <div>
                            <h3 className="text-xs font-black uppercase text-slate-400 tracking-wider mb-2">10. Candidate Card</h3>
                            <div className="space-y-2">
                                <CandidateCard name="Akash" activeTasks={1} skills={['python', 'sqlite', 'governance']} completedCount={12} status="deliverer" />
                                <CandidateCard name="Ansh" activeTasks={3} skills={['react', 'node', 'tailwind']} completedCount={4} status="help" />
                            </div>
                        </div>
                    </div>

                </div>
            </section>
        </div>
    );
};

export default DesignSystem;
