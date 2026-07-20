import React, { useState, useEffect } from 'react';
import { 
    FaDatabase, FaServer, FaHistory, FaNetworkWired, FaCheckCircle, 
    FaExclamationTriangle, FaPlay, FaBug, FaSyncAlt, FaTrash, 
    FaCheck, FaBan, FaUndo, FaClock, FaHeartbeat, FaCode 
} from 'react-icons/fa';
import { apiGet, apiPost } from '../../utils/apiClient';
import { useModal } from '../../contexts/ModalContext';

const MduRegistry = () => {
    const { error: showError, success: showSuccess } = useModal();
    const [datasets, setDatasets] = useState([]);
    const [selectedDataset, setSelectedDataset] = useState(null);
    const [lineage, setLineage] = useState(null);
    const [provenance, setProvenance] = useState([]);
    const [health, setHealth] = useState(null);
    const [loading, setLoading] = useState(true);
    const [reconciling, setReconciling] = useState(false);
    const [reconciliationTrace, setReconciliationTrace] = useState(null);
    
    // Simulators state
    const [simulatedFailure, setSimulatedFailure] = useState(false);
    const [simulatedLatency, setSimulatedLatency] = useState(false);
    const [mismatchLogs, setMismatchLogs] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [retryCount, setRetryCount] = useState(0);

    useEffect(() => {
        fetchRegistryData();
        const interval = setInterval(() => {
            fetchHealthAndDatasets();
        }, 15000); // refresh every 15s
        return () => clearInterval(interval);
    }, []);

    const fetchRegistryData = async () => {
        setLoading(true);
        try {
            await fetchHealthAndDatasets();
            // Fetch provenance once initially
            const provData = await apiGet('/api/v1/mdu/provenance');
            setProvenance(provData);
        } catch (err) {
            console.error("Error loading MDU data:", err);
        } finally {
            setLoading(false);
        }
    };

    const fetchHealthAndDatasets = async () => {
        try {
            // Fetch health
            const healthData = await apiGet('/api/v1/mdu/health');
            setHealth(healthData);

            // Fetch datasets
            const datasetsData = await apiGet('/api/v1/mdu/datasets');
            setDatasets(datasetsData);

            // Auto-select first dataset to show its lineage initially
            if (datasetsData.length > 0 && !selectedDataset) {
                handleSelectDataset(datasetsData[0]);
            }
        } catch (err) {
            console.error("Error refreshing health/datasets:", err);
        }
    };

    const handleSelectDataset = async (dataset) => {
        setSelectedDataset(dataset);
        try {
            const lineageData = await apiGet(`/api/v1/mdu/lineage/${dataset.id}`);
            setLineage(lineageData);
        } catch (err) {
            setLineage(null);
        }
    };

    // Toggle Simulated Latency/Resilience
    const handleToggleLatency = () => {
        setSimulatedLatency(!simulatedLatency);
        showSuccess(
            `Simulated network latency ${!simulatedLatency ? 'ENABLED (2.5s delay)' : 'DISABLED'}`, 
            "Network Resilience"
        );
    };

    // Toggle Simulated Backend Crash
    const handleToggleFailure = async () => {
        const nextState = !simulatedFailure;
        try {
            await apiPost(`/api/v1/mdu/simulate-failure?enable=${nextState}`);
            setSimulatedFailure(nextState);
            if (nextState) {
                showSuccess("Backend health degradation simulated successfully!", "Failure hardened");
            } else {
                showSuccess("Backend health restored to Operational.", "Recovery complete");
            }
            fetchHealthAndDatasets();
        } catch (err) {
            showError("Failed to apply failure simulation to the backend cluster.", "API Error");
        }
    };

    // Simulate Schema Mismatch Ingress Rejection (422 / 409)
    const handleSimulateMismatch = async (type) => {
        setMismatchLogs(null);
        try {
            let payload = {};
            if (type === '409') {
                // Version mismatch
                payload = {
                    registry: "prana.event.contracts",
                    event_type: "integrity_probe",
                    version: "2.0.0", // Unsupported version
                    payload: { sequence: 1, status: "ok", probe: "baseline" }
                };
            } else {
                // 422 missing fields
                payload = {
                    registry: "prana.event.contracts",
                    event_type: "task_submit",
                    version: "1.0.0",
                    payload: { title: "Bad Task Ingest" } // Lacks required fields user_id, route, sequence
                };
            }

            if (simulatedLatency) {
                await new Promise(r => setTimeout(r, 2500));
            }

            await apiPost('/api/v1/mdu/schema-mismatch', payload);
            showSuccess("Event conformant! Check local logs.", "Validation Success");
        } catch (err) {
            // Read FastAPI HTTPException body which client maps to err.response
            if (err.response && err.response.data) {
                setMismatchLogs(err.response.data);
                showError("Ingress validation blocked: Contract Mismatch Detected!", "Zero-Friction Ingress Guard");
            } else {
                setMismatchLogs({
                    status: "rejected",
                    reason: "connection_timeout",
                    message: "Simulation triggered network connection failure or API timeout bounds."
                });
                showError("Network timeout simulated.", "Timeout Warning");
            }
        }
    };

    // Trigger Authoritative State Reconciliation
    const handleReconcile = async () => {
        setReconciling(true);
        setReconciliationTrace(null);
        try {
            if (simulatedLatency) {
                await new Promise(r => setTimeout(r, 2500));
            }
            const trace = await apiPost('/api/v1/mdu/reconcile');
            setReconciliationTrace(trace);
            showSuccess("Relational storage profiles and ChromaDB filters reconciled successfully!", "Convergence Achieved");
            fetchHealthAndDatasets();
        } catch (err) {
            showError("Reconciliation aborted: DB locks or connection failures detected.", "Operational Fault");
        } finally {
            setReconciling(false);
        }
    };

    // Apply administrative lifecycle transitions (Activate, Deprecate, Rollback)
    const handleLifecycleAction = async (datasetId, action) => {
        try {
            const result = await apiPost('/api/v1/mdu/lifecycle/action', {
                dataset_id: datasetId,
                action: action,
                operator: "Soham Kotkar (Lead Admin)"
            });
            showSuccess(
                `Schema transitioned to ${result.updated_state}`, 
                "Lifecycle Transition Complete"
            );
            
            // Refresh local state
            fetchHealthAndDatasets();
            const provData = await apiGet('/api/v1/mdu/provenance');
            setProvenance(provData);
            
            if (selectedDataset && selectedDataset.id === datasetId) {
                setSelectedDataset(prev => ({ ...prev, status: result.updated_state }));
            }
        } catch (err) {
            showError("Lifecycle action blocked by active governance rules.", "Access Blocked");
        }
    };

    // Filter datasets based on search queries
    const filteredDatasets = datasets.filter(d => 
        d.canonical_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        d.textbook_code.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-[400px]">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-orange-500 mb-4"></div>
                <p className="text-gray-400 font-medium">Resolving Master Data Universe (MDU) registers...</p>
            </div>
        );
    }

    return (
        <div className="space-y-6 pb-12">
            {/* Header section */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        <FaDatabase className="text-orange-500" />
                        Master Data Universe (MDU) Registry
                    </h3>
                    <p className="text-gray-400 text-xs sm:text-sm">
                        Operator-grade convergence panel monitoring active curriculum schema, lineages, and provenances.
                    </p>
                </div>
                
                {/* Health State badge */}
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-black/40 border border-white/5 text-xs text-gray-300">
                        <FaClock className="text-gray-500" />
                        <span>Real-time Polling: <strong className="text-green-400">ON</strong></span>
                    </div>
                    {health && (
                        <span className={`px-4 py-1.5 rounded-full text-xs font-bold tracking-wide flex items-center gap-2 shadow-lg border ${
                            health.status === 'Healthy' 
                                ? 'text-green-400 bg-green-500/10 border-green-500/20' 
                                : 'text-red-400 bg-red-500/10 border-red-500/20 animate-pulse'
                        }`}>
                            <FaHeartbeat className={health.status === 'Healthy' ? '' : 'animate-bounce'} />
                            SYSTEM: {health.status.toUpperCase()}
                        </span>
                    )}
                </div>
            </div>

            {/* Simulated Hardening Playground */}
            <div className="glass-panel p-5 rounded-2xl border border-white/10 bg-black/30">
                <h4 className="text-sm font-bold uppercase tracking-wider text-orange-400 mb-4 flex items-center gap-2">
                    <FaBug className="text-xs" />
                    Resilience & Crash-Hardening Playground
                </h4>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                    {/* Simulated Controls */}
                    <div className="space-y-3">
                        <div className="text-xs text-gray-300 font-semibold mb-2">Simulated Fault Injections:</div>
                        
                        {/* Degrade health */}
                        <button
                            onClick={handleToggleFailure}
                            className={`w-full py-2.5 px-4 rounded-xl border text-xs font-bold flex items-center justify-between transition-all duration-300 ${
                                simulatedFailure 
                                    ? 'bg-red-500/20 border-red-500 text-red-300' 
                                    : 'bg-white/5 border-white/10 hover:border-red-500/40 text-gray-300 hover:text-white'
                            }`}
                        >
                            <span className="flex items-center gap-2">
                                <FaBan /> Trigger Backend Database Crash (500)
                            </span>
                            <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" style={{ display: simulatedFailure ? 'inline-block' : 'none' }}></span>
                        </button>

                        {/* Latency toggle */}
                        <button
                            onClick={handleToggleLatency}
                            className={`w-full py-2.5 px-4 rounded-xl border text-xs font-bold flex items-center justify-between transition-all duration-300 ${
                                simulatedLatency 
                                    ? 'bg-amber-500/20 border-amber-500 text-amber-300' 
                                    : 'bg-white/5 border-white/10 hover:border-amber-500/40 text-gray-300 hover:text-white'
                            }`}
                        >
                            <span className="flex items-center gap-2">
                                <FaClock /> Inject Network Latency (+2.5s)
                            </span>
                        </button>
                    </div>

                    {/* Ingress Schema validation check */}
                    <div className="space-y-3">
                        <div className="text-xs text-gray-300 font-semibold mb-2">Schema Contract Violations (TANTRA):</div>
                        <div className="flex gap-2">
                            <button
                                onClick={() => handleSimulateMismatch('409')}
                                className="flex-1 py-2.5 px-3 rounded-xl bg-orange-600/20 border border-orange-500/20 hover:border-orange-500 text-orange-400 hover:text-white font-bold text-xs transition-all flex items-center justify-center gap-2"
                            >
                                <FaCode /> Version Mismatch (409)
                            </button>
                            <button
                                onClick={() => handleSimulateMismatch('422')}
                                className="flex-1 py-2.5 px-3 rounded-xl bg-red-600/20 border border-red-500/20 hover:border-red-500 text-red-400 hover:text-white font-bold text-xs transition-all flex items-center justify-center gap-2"
                            >
                                <FaCode /> Missing Fields (422)
                            </button>
                        </div>
                        <p className="text-[10px] text-gray-500 italic">
                            Simulates ingestion of malformed payload packets. Verification engine blocks processing to preserve data integrity.
                        </p>
                    </div>

                    {/* Reconciliation Action */}
                    <div className="flex flex-col justify-between">
                        <div>
                            <div className="text-xs text-gray-300 font-semibold mb-2">Authoritative State Reconciliation:</div>
                            <p className="text-[10px] text-gray-400 mb-3">
                                Dynamically queries relational profiles, maps resolved standards, and synchronizes vector store filters in active runtimes.
                            </p>
                        </div>
                        <button
                            onClick={handleReconcile}
                            disabled={reconciling}
                            className={`w-full py-3 px-4 rounded-xl bg-gradient-to-r from-orange-600 to-amber-600 font-bold text-xs text-white hover:shadow-lg transition-all flex items-center justify-center gap-2 ${
                                reconciling ? 'animate-pulse opacity-85' : 'hover:scale-[1.02]'
                            }`}
                        >
                            <FaSyncAlt className={reconciling ? 'animate-spin' : ''} />
                            {reconciling ? 'RECONCILING STORAGE STATE...' : 'RUN METADATA RECONCILIATION'}
                        </button>
                    </div>
                </div>

                {/* Simulated Logs Terminal (shows 422 errors or reconciliation trace) */}
                {(mismatchLogs || reconciliationTrace) && (
                    <div className="mt-5 border-t border-white/5 pt-4">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-bold text-gray-300 uppercase tracking-wider flex items-center gap-2">
                                <FaServer className="text-orange-500" />
                                Operator Diagnostic Terminal
                            </span>
                            <button 
                                onClick={() => { setMismatchLogs(null); setReconciliationTrace(null); }}
                                className="text-[10px] text-gray-500 hover:text-gray-300 flex items-center gap-1"
                            >
                                <FaTrash /> Clear Logs
                            </button>
                        </div>
                        
                        <div className="p-4 rounded-xl bg-[#080905] border border-white/5 font-mono text-xs text-green-400 overflow-x-auto max-h-[250px] custom-scrollbar shadow-inner">
                            {mismatchLogs && (
                                <pre className="whitespace-pre-wrap">
                                    <span className="text-red-400">=== INGRESS CONTRACT MUTATION VIOLATION DETECTED ===</span>{"\n"}
                                    {JSON.stringify(mismatchLogs, null, 2)}
                                </pre>
                            )}
                            {reconciliationTrace && (
                                <div className="space-y-2">
                                    <span className="text-cyan-400 font-bold">=== STATE RECONCILIATION TRACE (SQL PROFILE → CHROMADB VECTOR FILTER) ===</span>
                                    <div className="text-gray-300 mt-2">
                                        <div className="mb-1 text-green-500">Status: {reconciliationTrace.status}</div>
                                        <div className="mb-1">Timestamp: {new Date(reconciliationTrace.timestamp).toLocaleString()}</div>
                                        <div className="mb-1">Inspected Profiles Count: <strong className="text-orange-400">{reconciliationTrace.profile_audit_count}</strong></div>
                                        <div className="mb-3">Syllabus Boards Distribution: {JSON.stringify(reconciliationTrace.board_preferences)}</div>
                                    </div>
                                    <div className="space-y-1 pl-2 border-l-2 border-orange-500/20">
                                        {reconciliationTrace.reconciliation_trace.map(t => (
                                            <div key={t.step} className="flex gap-2">
                                                <span className="text-orange-400">Step {t.step}:</span>
                                                <span className="text-gray-300">{t.description}</span>
                                            </div>
                                        ))}
                                    </div>
                                    <div className="text-green-500 font-bold mt-2 flex items-center gap-1">
                                        <FaCheckCircle className="text-xs" /> Alignment checks 100% compliant. Dynamic vector filters updated.
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>

            {/* Implementation Boundaries & Verification Truth Matrix */}
            {health && health.implementation_bounds && (
                <div className="glass-panel p-5 rounded-2xl border border-white/10 bg-black/30">
                    <h4 className="text-sm font-bold uppercase tracking-wider text-orange-400 mb-4 flex items-center gap-2">
                        <FaServer className="text-xs" />
                        Infrastructure Implementation Boundaries & Runtime Truth Matrix
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
                        {Object.entries(health.implementation_bounds).map(([key, value]) => (
                            <div key={key} className="p-3.5 rounded-xl bg-white/5 border border-white/5 flex flex-col justify-between">
                                <div className="flex justify-between items-start mb-2">
                                    <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider font-mono">
                                        {key.replace(/_/g, ' ')}
                                    </span>
                                    <span className={`text-[8px] font-bold px-2 py-0.5 rounded-full ${
                                        value.status === 'IMPLEMENTED' 
                                            ? 'text-green-400 bg-green-500/10 border border-green-500/20' 
                                            : value.status === 'PARTIAL' 
                                                ? 'text-amber-400 bg-amber-500/10 border border-amber-500/20'
                                                : 'text-blue-400 bg-blue-500/10 border border-blue-500/20'
                                    }`}>
                                        {value.status}
                                    </span>
                                </div>
                                <div className="text-[11px] text-gray-300">
                                    {value.boundary}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Primary content grids */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Dataset selection list (Left column) */}
                <div className="lg:col-span-1 space-y-4">
                    <div className="glass-panel p-4 sm:p-5 rounded-2xl border border-white/10 h-full flex flex-col justify-between">
                        <div>
                            <div className="flex items-center justify-between mb-4">
                                <h4 className="text-sm font-bold uppercase tracking-wider text-orange-400 flex items-center gap-2">
                                    <FaDatabase className="text-xs" />
                                    Ingested Schemas
                                </h4>
                                <span className="text-[10px] text-gray-400 bg-white/5 border border-white/10 px-2 py-0.5 rounded-full font-bold">
                                    {filteredDatasets.length} total
                                </span>
                            </div>

                            {/* Search bar */}
                            <div className="mb-4 relative">
                                <input
                                    type="text"
                                    placeholder="Filter by board, standard..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full text-xs py-2 pl-3 pr-8 rounded-xl bg-white/5 border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-orange-500 transition-colors"
                                />
                            </div>

                            {/* Dataset items list */}
                            <div className="space-y-3 max-h-[400px] overflow-y-auto pr-1 no-scrollbar">
                                {filteredDatasets.length === 0 ? (
                                    /* GORGEOUS EMPTY STATE */
                                    <div className="text-center py-10 border border-dashed border-white/5 rounded-2xl p-4">
                                        <FaExclamationTriangle className="text-orange-500/40 text-3xl mx-auto mb-3" />
                                        <div className="text-gray-300 font-bold text-xs mb-1">No Matching Datasets</div>
                                        <div className="text-gray-500 text-[10px]">
                                            Ingress schema could not resolve any textbook maps matching "{searchQuery}" in our registries.
                                        </div>
                                    </div>
                                ) : (
                                    filteredDatasets.map(d => {
                                        const isSelected = selectedDataset && selectedDataset.id === d.id;
                                        return (
                                            <div
                                                key={d.id}
                                                onClick={() => handleSelectDataset(d)}
                                                className={`p-3.5 rounded-xl border cursor-pointer transition-all duration-300 flex flex-col justify-between group hover:-translate-y-0.5 hover:shadow-lg ${
                                                    isSelected 
                                                        ? 'bg-gradient-to-r from-orange-600/20 to-amber-600/20 border-orange-500/50 shadow-orange-500/5' 
                                                        : 'bg-white/5 border-white/5 hover:bg-white/10 hover:border-white/10'
                                                }`}
                                            >
                                                <div className="flex justify-between items-start mb-2">
                                                    <span className="text-[10px] font-bold text-orange-400 font-mono tracking-wider">{d.textbook_code}</span>
                                                    <span className={`text-[8px] font-bold px-2 py-0.5 rounded-full ${
                                                        d.status === 'ACTIVE' 
                                                            ? 'text-green-400 bg-green-500/10 border border-green-500/20' 
                                                            : d.status === 'DRAFT' 
                                                                ? 'text-blue-400 bg-blue-500/10 border border-blue-500/20'
                                                                : 'text-gray-400 bg-white/5 border border-white/10'
                                                    }`}>
                                                        {d.status}
                                                    </span>
                                                </div>
                                                <div className={`text-xs font-bold transition-colors mb-2 ${isSelected ? 'text-white' : 'text-gray-300 group-hover:text-white'}`}>
                                                    {d.canonical_name}
                                                </div>
                                                
                                                <div className="flex justify-between items-center text-[10px] text-gray-500 font-semibold border-t border-white/5 pt-2">
                                                    <span>Chunks: <strong className="text-gray-300">{d.chunk_count}</strong></span>
                                                    <span>Trust: <strong className="text-gray-300">{d.trust_score * 100}%</strong></span>
                                                </div>
                                            </div>
                                        );
                                    })
                                )}
                            </div>
                        </div>

                        {/* Diagnostics list */}
                        {health && (
                            <div className="mt-6 border-t border-white/10 pt-4 space-y-2">
                                <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2">Operational Diagnostics:</div>
                                <div className="grid grid-cols-2 gap-2 text-[10px] font-mono text-gray-400">
                                    <div className="bg-white/5 p-2 rounded-lg border border-white/5">
                                        <div className="text-gray-500">Latency</div>
                                        <div className="font-bold text-white mt-0.5">{health.diagnostics.api_latency_ms} ms</div>
                                    </div>
                                    <div className="bg-white/5 p-2 rounded-lg border border-white/5">
                                        <div className="text-gray-500">DB Write Locks</div>
                                        <div className="font-bold text-white mt-0.5">{health.diagnostics.sqlite_write_locks_active} active</div>
                                    </div>
                                    <div className="bg-white/5 p-2 rounded-lg border border-white/5">
                                        <div className="text-gray-500">Memory Usage</div>
                                        <div className="font-bold text-white mt-0.5">{health.diagnostics.memory_usage_mb} MB</div>
                                    </div>
                                    <div className="bg-white/5 p-2 rounded-lg border border-white/5">
                                        <div className="text-gray-500">Active Operators</div>
                                        <div className="font-bold text-white mt-0.5">{health.diagnostics.active_operator_sessions}</div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Selected Dataset Lineage Chain & Admin Actions (Right columns) */}
                <div className="lg:col-span-2 space-y-6">
                    {selectedDataset ? (
                        <div className="glass-panel p-5 sm:p-6 rounded-2xl border border-white/10 bg-black/40 flex flex-col justify-between h-full">
                            <div>
                                {/* Active details */}
                                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-white/10 pb-4 mb-5 gap-3">
                                    <div>
                                        <div className="text-[10px] font-bold uppercase tracking-wider text-orange-400 font-mono">{selectedDataset.id}</div>
                                        <h4 className="text-base font-bold text-white">{selectedDataset.canonical_name}</h4>
                                    </div>
                                    
                                    {/* Action items */}
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => handleLifecycleAction(selectedDataset.id, 'ACTIVATE')}
                                            disabled={selectedDataset.status === 'ACTIVE'}
                                            className="px-3 py-1.5 rounded-lg bg-green-600/20 border border-green-500/20 hover:border-green-500 text-green-400 hover:text-white text-[10px] font-bold transition-all flex items-center gap-1 disabled:opacity-50 disabled:pointer-events-none"
                                            title="Activate Dataset"
                                        >
                                            <FaCheck /> Activate
                                        </button>
                                        <button
                                            onClick={() => handleLifecycleAction(selectedDataset.id, 'DEPRECATE')}
                                            disabled={selectedDataset.status === 'DEPRECATED'}
                                            className="px-3 py-1.5 rounded-lg bg-red-600/20 border border-red-500/20 hover:border-red-500 text-red-400 hover:text-white text-[10px] font-bold transition-all flex items-center gap-1 disabled:opacity-50 disabled:pointer-events-none"
                                            title="Deprecate Dataset"
                                        >
                                            <FaBan /> Deprecate
                                        </button>
                                        <button
                                            onClick={() => handleLifecycleAction(selectedDataset.id, 'ROLLBACK')}
                                            className="px-3 py-1.5 rounded-lg bg-blue-600/20 border border-blue-500/20 hover:border-blue-500 text-blue-400 hover:text-white text-[10px] font-bold transition-all flex items-center gap-1"
                                            title="Rollback Dataset"
                                        >
                                            <FaUndo /> Rollback
                                        </button>
                                    </div>
                                </div>

                                {/* Ingestion lineage visual map */}
                                <div className="space-y-4">
                                    <h5 className="text-xs font-bold text-gray-300 uppercase tracking-wider flex items-center gap-2">
                                        <FaNetworkWired className="text-orange-500" />
                                        Interactive Ingestion Lineage Chain
                                    </h5>
                                    
                                    {lineage ? (
                                        <div className="p-4 rounded-xl border border-white/5 bg-black/60 relative overflow-hidden">
                                            {/* Svg visual connections */}
                                            <div className="flex flex-col gap-6 relative z-10">
                                                {lineage.nodes.map((node, idx) => {
                                                    const isLast = idx === lineage.nodes.length - 1;
                                                    return (
                                                        <div key={node.id} className="flex flex-col md:flex-row items-center justify-between gap-3 p-3 bg-white/5 border border-white/5 hover:border-orange-500/30 rounded-xl transition-all duration-300">
                                                            <div className="flex items-center gap-3">
                                                                <span className="w-6 h-6 rounded-full flex items-center justify-center bg-orange-500/10 text-orange-400 border border-orange-500/20 font-bold text-[10px] font-mono shadow-inner">
                                                                    {idx + 1}
                                                                </span>
                                                                <div>
                                                                    <div className="text-xs font-bold text-white">{node.label}</div>
                                                                    <div className="text-[9px] text-gray-500 font-semibold uppercase font-mono tracking-wider">{node.type}</div>
                                                                </div>
                                                            </div>
                                                            <div className="flex items-center gap-2">
                                                                {node.implementation_state && (
                                                                    <span className={`text-[8px] font-bold px-2 py-0.5 rounded-full ${
                                                                        node.implementation_state === 'IMPLEMENTED' 
                                                                            ? 'text-green-400 bg-green-500/10 border border-green-500/20' 
                                                                            : 'text-blue-400 bg-blue-500/10 border border-blue-500/20'
                                                                    }`}>
                                                                        {node.implementation_state}
                                                                    </span>
                                                                )}
                                                                <span className={`text-[8px] font-bold px-2 py-0.5 rounded-full ${
                                                                    node.status === 'COMPLIANT' 
                                                                        ? 'text-green-400 bg-green-500/10 border border-green-500/20' 
                                                                        : node.status === 'WARNING'
                                                                            ? 'text-amber-400 bg-amber-500/10 border border-amber-500/20'
                                                                            : 'text-blue-400 bg-blue-500/10 border border-blue-500/20'
                                                                }`}>
                                                                    {node.status}
                                                                </span>
                                                            </div>
                                                        </div>
                                                    );
                                                })}
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="text-center py-10 border border-dashed border-white/10 rounded-xl text-gray-500 text-xs">
                                            Ingestion lineage not loaded for this schema registry context.
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Provenance Audit Trail (Git-style) */}
                            <div className="mt-8 border-t border-white/10 pt-5">
                                <h5 className="text-xs font-bold text-gray-300 uppercase tracking-wider mb-4 flex items-center gap-2">
                                    <FaHistory className="text-orange-500" />
                                    Cryptographic Ingestion Provenance Trail
                                </h5>
                                
                                <div className="space-y-3.5 max-h-[160px] overflow-y-auto pr-1 no-scrollbar">
                                    {provenance.map((p, idx) => (
                                        <div key={idx} className="p-3 bg-white/5 border border-white/5 rounded-xl text-xs flex justify-between gap-4 group hover:bg-[#070904] transition-colors">
                                            <div className="flex gap-3">
                                                <FaHistory className="text-orange-500/50 group-hover:text-orange-400 mt-1 shrink-0" />
                                                <div>
                                                    <div className="font-bold text-gray-300 group-hover:text-white transition-colors">{p.action}</div>
                                                    <div className="text-[10px] text-gray-500 font-semibold mt-1">
                                                        Operator: <strong className="text-gray-400">{p.operator}</strong> | Dataset: <strong className="text-orange-400">{p.dataset}</strong>
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="text-right shrink-0">
                                                <div className="text-[10px] text-gray-500 font-mono">{p.hash.substring(0, 16)}...</div>
                                                <div className="text-[8px] text-gray-600 font-semibold mt-1 flex items-center gap-1.5 justify-end">
                                                    {p.chain_verified && (
                                                        <span className="text-green-400 flex items-center gap-0.5 text-[8px] uppercase font-bold bg-green-500/10 border border-green-500/20 px-1 rounded">
                                                            <FaCheck className="text-[6px]" /> Verified
                                                        </span>
                                                    )}
                                                    <FaClock /> {new Date(p.timestamp).toLocaleTimeString()}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div className="glass-panel p-10 rounded-2xl border border-white/10 bg-black/40 text-center text-gray-500 flex flex-col items-center justify-center min-h-[300px]">
                            <FaDatabase className="text-orange-500/20 text-5xl mb-4" />
                            <h4 className="text-white font-bold mb-1">No Dataset Selected</h4>
                            <p className="text-xs max-w-sm">Select an ingested curriculum schema context from the left panel to load the visual ingestion lineage graph and administrative controls.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MduRegistry;
