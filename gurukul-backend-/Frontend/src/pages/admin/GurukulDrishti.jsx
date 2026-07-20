import React, { useState, useEffect } from 'react';
import { 
    FaDatabase, FaEye, FaUsers, FaGraduationCap, FaMapMarkedAlt, 
    FaUserTie, FaChevronRight, FaPlay, FaHeartbeat, FaExclamationTriangle, 
    FaChartLine, FaCheckCircle, FaLock, FaSync, FaShieldAlt, FaTerminal,
    FaInfoCircle, FaKey, FaHistory
} from 'react-icons/fa';
import { apiGet, apiPut, apiPost, checkBackendHealth, handleApiError } from '../../utils/apiClient';
import { useAuth } from '../../contexts/AuthContext';
import { useDemo } from '../../contexts/DemoContext';
import { Navigate } from 'react-router-dom';

// Import Reusable Dashboard Components
import KPICard from '../../components/dashboard/KPICard';
import AlertCard from '../../components/dashboard/AlertCard';
import ActionCard from '../../components/dashboard/ActionCard';
import ActivityCard from '../../components/dashboard/ActivityCard';
import StatusCard from '../../components/dashboard/StatusCard';

const MOCK_DASHBOARDS = {
    "student": {
        role: "student",
        kpis: {
            "learning_score": 85.5,
            "karma_balance": 340,
            "daily_goals_completed": 3,
            "cards_completed": 120
        },
        open_alerts: [
            { id: "alt-mock-1", type: "PACING", priority: "MEDIUM", status: "OPEN", owner_id: "student-1", created_at: new Date().toISOString() },
            { id: "alt-mock-2", type: "COMPREHENSION", priority: "HIGH", status: "OPEN", owner_id: "student-1", created_at: new Date().toISOString() }
        ],
        pending_actions: [
            { id: "act-mock-1", title: "Calibrate Voice Assistant", description: "Improve pronunciation thresholds for Marathi modules.", status: "Assigned", owner_id: "student-1", created_at: new Date().toISOString() },
            { id: "act-mock-2", title: "Submit Reflection Note", description: "Write down daily learning insights.", status: "Created", owner_id: "student-1", created_at: new Date().toISOString() }
        ],
        recent_activity: [
            { type: "TEST_COMPLETED", title: "Completed Quiz on Science - Chemical Reactions", timestamp: new Date().toISOString(), details: { score: 9, total: 10, percentage: 90.0 } },
            { type: "REFLECTION_SUBMITTED", title: "Submitted daily reflection note", timestamp: new Date(Date.now() - 3600000).toISOString(), details: { mood_score: 8 } }
        ],
        status_summary: {
            overall_status: "fully_compliant",
            active_goals: ["Arabic Mastery Level 3", "Interactive Science Intro"],
            pacing_coefficient: 1.15
        }
    },
    "teacher": {
        role: "teacher",
        kpis: {
            "total_assigned_students": 50,
            "avg_comprehension_score": 82.5,
            "active_students_today": 42,
            "average_pacing": 1.08
        },
        open_alerts: [
            { id: "alt-mock-3", type: "ATTENDANCE", priority: "CRITICAL", status: "OPEN", owner_id: "student-2", created_at: new Date().toISOString() },
            { id: "alt-mock-4", type: "PACING", priority: "LOW", status: "OPEN", owner_id: "student-3", created_at: new Date().toISOString() }
        ],
        pending_actions: [
            { id: "act-mock-3", title: "Comprehension remedial review", description: "Schedule extra time for Student 2 standard 9 maths.", status: "In Progress", owner_id: "teacher-1", created_at: new Date().toISOString() }
        ],
        recent_activity: [
            { type: "STUDENT_REFLECTION", title: "Student John Doe submitted a reflection", timestamp: new Date().toISOString(), details: { mood_score: 9 } }
        ],
        status_summary: {
            class_name: "Grade 9 Arabic Language & Science",
            average_comprehension: 82.5,
            warning_flags_count: 2
        }
    },
    "admin": {
        role: "institution-admin",
        kpis: {
            "total_students": 5000,
            "total_teachers": 200,
            "total_cohorts": 100,
            "avg_institution_score": 84.5
        },
        open_alerts: [
            { id: "alt-mock-5", type: "PACING", priority: "MEDIUM", status: "OPEN", owner_id: "teacher-1", created_at: new Date().toISOString() }
        ],
        pending_actions: [
            { id: "act-mock-4", title: "Force SQLite-EMS Database Sync", description: "Verify consistency in multi-tenant data sync logs.", status: "Created", owner_id: "admin-1", created_at: new Date().toISOString() }
        ],
        recent_activity: [
            { type: "AUDIT_LOG", title: "Teacher 1 executed UPDATE_STATUS on ALERT", timestamp: new Date().toISOString(), details: { old_status: "OPEN" } }
        ],
        status_summary: {
            infrastructure_state: "green",
            sqlite_write_locks_triggered: 0,
            average_response_time_ms: 145.0
        }
    },
    "regional-admin": {
        role: "regional-admin",
        kpis: {
            "total_institutions": 20,
            "total_teachers": 200,
            "total_students": 5000,
            "avg_system_score": 83.1
        },
        open_alerts: [],
        pending_actions: [],
        recent_activity: [
            { type: "AUDIT_LOG", title: "System Admin executed ASSIGN on ACTION", timestamp: new Date().toISOString(), details: { assigned_to: "teacher-2" } }
        ],
        status_summary: {
            redundancy_level: "triple_region",
            system_survivability_rate: 0.9999,
            active_replay_workers: 2
        }
    }
};

const getMockKey = (role) => {
    if (!role) return "admin";
    const r = role.toLowerCase().replace(/_/g, '-');
    if (r === 'institution-admin' || r === 'admin') return 'admin';
    if (r === 'regional-admin') return 'regional-admin';
    if (r === 'teacher') return 'teacher';
    if (r === 'student') return 'student';
    return 'admin';
};

const GurukulDrishti = () => {
    const { user } = useAuth();
    const { isDemoMode } = useDemo();
    
    // Redirect to login page if demo mode is off and user is not authenticated
    if (!isDemoMode && !user) {
        return <Navigate to="/signin" replace />;
    }
    
    // Configurable role context simulation
    const [selectedRole, setSelectedRole] = useState(user?.role ? user.role.toLowerCase() : "admin");
    const [useMockData, setUseMockData] = useState(false);

    // States for staff to select a student's telemetry
    const [students, setStudents] = useState([]);
    const [selectedStudentId, setSelectedStudentId] = useState("");
    const [selectedStudentName, setSelectedStudentName] = useState("");

    // Fetch student users to populate the telemetry selector dropdown
    const fetchStudentsList = async () => {
        try {
            if (!user) return;
            const users = await apiGet('/api/v1/ems/users');
            const studentUsers = (users || []).filter(u => u.role?.toUpperCase() === 'STUDENT');
            setStudents(studentUsers);
        } catch (err) {
            console.warn("Failed to fetch students from backend, falling back to mock list:", err);
            setStudents([
                { id: "student-1", full_name: "Eklavya Sharma", email: "student_1@test.gurukul" },
                { id: "student-2", full_name: "Aarav Patel", email: "student_2@test.gurukul" },
                { id: "student-3", full_name: "Mira Nair", email: "student_3@test.gurukul" }
            ]);
        }
    };

    useEffect(() => {
        fetchStudentsList();
    }, [user]);

    // Sync simulated role with actual logged in user role when demo mode is off
    useEffect(() => {
        if (!isDemoMode && user?.role && !selectedStudentId) {
            const normalizeRole = (r) => {
                if (!r) return '';
                const clean = r.toLowerCase().replace(/_/g, '-');
                if (clean === 'institution-admin') return 'admin';
                return clean;
            };
            setSelectedRole(normalizeRole(user.role));
            setUseMockData(false);
        }
    }, [isDemoMode, user, selectedStudentId]);
    
    // API loading and backend status states
    const [isOnline, setIsOnline] = useState(null); // null = checking, true/false
    const [isWarmingUp, setIsWarmingUp] = useState(false); // Render cold-start warmup
    const [loading, setLoading] = useState(true);
    const [errorMsg, setErrorMsg] = useState(null);
    const [updatingId, setUpdatingId] = useState(null);
    
    // Core dashboard data models
    const [dashboardData, setDashboardData] = useState({
        role: "student",
        kpis: {},
        open_alerts: [],
        pending_actions: [],
        recent_activity: [],
        status_summary: {}
    });

    const [terminalLogs, setTerminalLogs] = useState([
        "System Initialized. Drishti Foundation Active.",
        "Awaiting Operator Action..."
    ]);

    const logAction = (msg) => {
        const timestamp = new Date().toLocaleTimeString();
        setTerminalLogs(prev => [`[${timestamp}] ${msg}`, ...prev.slice(0, 15)]);
    };

    // Verify backend health — with auto-retry for Render cold-start warmup
    const checkSystemHealth = async (autoRetry = false) => {
        logAction("Initiating service health ping...");
        const healthy = await checkBackendHealth();
        setIsOnline(healthy);
        if (healthy) {
            setIsWarmingUp(false);
            logAction("➔ System Status: ONLINE");
        } else {
            logAction("➔ System Status: OFFLINE (Backend unavailable or cold-starting)");
            if (autoRetry) {
                // Render free tier cold-starts in ~30–60s. Auto-retry every 10s up to 6 times.
                setIsWarmingUp(true);
                let attempts = 0;
                const maxAttempts = 6;
                const retryInterval = setInterval(async () => {
                    attempts++;
                    logAction(`➔ Warmup retry ${attempts}/${maxAttempts} — pinging backend...`);
                    const alive = await checkBackendHealth();
                    if (alive) {
                        clearInterval(retryInterval);
                        setIsOnline(true);
                        setIsWarmingUp(false);
                        logAction("➔ Backend is now ONLINE. Reloading live data...");
                        await loadDashboardData();
                    } else if (attempts >= maxAttempts) {
                        clearInterval(retryInterval);
                        setIsWarmingUp(false);
                        logAction("➔ Backend did not respond after warmup period. Displaying cached data.");
                    }
                }, 10000);
            }
        }
        return healthy;
    };

    // Load active dashboard data based on simulated role and mock toggles
    const loadDashboardData = async (roleName = selectedRole, forceMock = useMockData) => {
        setLoading(true);
        setErrorMsg(null);
        logAction(`Loading dashboard data context for [${roleName.toUpperCase()}]`);

        if (forceMock) {
            logAction("➔ Using mock simulation data context (offline toggle active)");
            const key = getMockKey(roleName);
            setDashboardData(MOCK_DASHBOARDS[key] || MOCK_DASHBOARDS.admin);
            setLoading(false);
            return;
        }

        try {
            // Determine endpoints based on selected roles
            let endpoint = '/api/v1/dashboard/aggregate';
            
            if (selectedStudentId) {
                endpoint = `/api/v1/dashboard/aggregate?student_id=${selectedStudentId}`;
            } else {
                // Normalize roles for robust comparison and routing
                const normalizeRole = (r) => {
                    if (!r) return '';
                    const clean = r.toLowerCase().replace(/_/g, '-');
                    if (clean === 'institution-admin') return 'admin';
                    return clean;
                };
                const userRole = normalizeRole(user?.role);
                const targetRole = normalizeRole(roleName);
                
                if (userRole !== targetRole) {
                    if (targetRole === 'student') endpoint = '/api/v1/dashboard/student';
                    else if (targetRole === 'teacher') endpoint = '/api/v1/dashboard/teacher';
                    else if (targetRole === 'admin') endpoint = '/api/v1/dashboard/institution-admin';
                    else if (targetRole === 'regional-admin') endpoint = '/api/v1/dashboard/regional-admin';
                }
            }

            logAction(`➔ API Request: GET ${endpoint}`);
            const data = await apiGet(endpoint);
            setDashboardData(data);
            logAction(`➔ API Response: 200 OK (${data.open_alerts?.length} alerts, ${data.pending_actions?.length} actions)`);
        } catch (err) {
            console.error("Dashboard aggregation failed:", err);
            const apiErr = handleApiError(err);
            setErrorMsg(apiErr.message);
            const displayStatus = err.status !== undefined ? err.status : 0;
            logAction(`➔ API Error: ${displayStatus} - ${apiErr.message}`);
            
            if (isDemoMode || forceMock) {
                // In demo mode: fall back to mock data so visitors can explore the UI
                logAction("➔ Demo mode: falling back to local simulation data.");
                const key = getMockKey(roleName);
                setDashboardData(MOCK_DASHBOARDS[key] || MOCK_DASHBOARDS.admin);
            } else {
                // In normal mode: clear data so dummy numbers are never shown as real
                logAction("➔ Live mode: clearing dashboard — data unavailable while backend is offline.");
                setDashboardData({ role: roleName, kpis: {}, open_alerts: [], pending_actions: [], recent_activity: [], status_summary: {} });
            }
        } finally {
            setLoading(false);
        }
    };

    // Initialize health check and fetch initial dashboard payload
    useEffect(() => {
        const init = async () => {
            const healthy = await checkSystemHealth(true); // enable auto-retry for cold-start
            await loadDashboardData();
        };
        init();
    }, [selectedRole, useMockData, selectedStudentId]);

    // Handle alert status transition (OPEN -> RESOLVED -> CLOSED)
    const handleAlertStatus = async (id, status) => {
        setUpdatingId(id);
        logAction(`Transitioning alert status: ${id} ➔ ${status}`);
        
        if (useMockData || id.startsWith('alt-mock')) {
            // Update local state mock
            setDashboardData(prev => ({
                ...prev,
                open_alerts: prev.open_alerts.map(a => a.id === id ? { ...a, status } : a)
            }));
            logAction(`➔ Mock status updated: ${id} is now ${status}`);
            setUpdatingId(null);
            return;
        }

        try {
            logAction(`➔ API Request: PUT /api/v1/alerts/${id}/status`);
            await apiPut(`/api/v1/alerts/${id}/status`, { status });
            logAction(`➔ API Response: Status updated successfully.`);
            await loadDashboardData(); // Reload to fetch live updates and audit trail logs
        } catch (err) {
            const apiErr = handleApiError(err);
            logAction(`➔ API Error: Failed to update alert status - ${apiErr.message}`);
        } finally {
            setUpdatingId(null);
        }
    };

    // Handle alert assignee changes
    const handleAlertAssign = async (id, ownerId) => {
        setUpdatingId(id);
        logAction(`Assigning alert: ${id} to owner ${ownerId}`);

        if (useMockData || id.startsWith('alt-mock')) {
            setDashboardData(prev => ({
                ...prev,
                open_alerts: prev.open_alerts.map(a => a.id === id ? { ...a, owner_id: ownerId } : a)
            }));
            logAction(`➔ Mock assignment updated: ${id} assigned to ${ownerId}`);
            setUpdatingId(null);
            return;
        }

        try {
            logAction(`➔ API Request: PUT /api/v1/alerts/${id}/assign`);
            await apiPut(`/api/v1/alerts/${id}/assign`, { owner_id: ownerId });
            logAction(`➔ API Response: Assignment complete.`);
            await loadDashboardData();
        } catch (err) {
            const apiErr = handleApiError(err);
            logAction(`➔ API Error: Failed to assign alert - ${apiErr.message}`);
        } finally {
            setUpdatingId(null);
        }
    };

    // Handle action status updates
    const handleActionStatus = async (id, status) => {
        setUpdatingId(id);
        logAction(`Transitioning action status: ${id} ➔ ${status}`);

        if (useMockData || id.startsWith('act-mock')) {
            setDashboardData(prev => ({
                ...prev,
                pending_actions: prev.pending_actions.map(a => a.id === id ? { ...a, status } : a)
            }));
            logAction(`➔ Mock status updated: ${id} is now ${status}`);
            setUpdatingId(null);
            return;
        }

        try {
            logAction(`➔ API Request: PUT /api/v1/actions/${id}/status`);
            await apiPut(`/api/v1/actions/${id}/status`, { status });
            logAction(`➔ API Response: Status updated successfully.`);
            await loadDashboardData();
        } catch (err) {
            const apiErr = handleApiError(err);
            logAction(`➔ API Error: Failed to update action status - ${apiErr.message}`);
        } finally {
            setUpdatingId(null);
        }
    };

    // Handle action assignee changes
    const handleActionAssign = async (id, ownerId) => {
        setUpdatingId(id);
        logAction(`Assigning action: ${id} to owner ${ownerId}`);

        if (useMockData || id.startsWith('act-mock')) {
            setDashboardData(prev => ({
                ...prev,
                pending_actions: prev.pending_actions.map(a => a.id === id ? { ...a, owner_id: ownerId } : a)
            }));
            logAction(`➔ Mock assignment updated: ${id} assigned to ${ownerId}`);
            setUpdatingId(null);
            return;
        }

        try {
            logAction(`➔ API Request: PUT /api/v1/actions/${id}/assign`);
            await apiPut(`/api/v1/actions/${id}/assign`, { owner_id: ownerId });
            logAction(`➔ API Response: Assignment complete.`);
            await loadDashboardData();
        } catch (err) {
            const apiErr = handleApiError(err);
            logAction(`➔ API Error: Failed to assign action - ${apiErr.message}`);
        } finally {
            setUpdatingId(null);
        }
    };

    // Helper for KPI styling class mapping
    const getKpiColor = (key) => {
        switch (key) {
            case 'learning_score':
            case 'avg_comprehension_score':
            case 'avg_institution_score':
            case 'avg_system_score':
                return 'text-green-400';
            case 'karma_balance':
            case 'active_students_today':
            case 'total_teachers':
                return 'text-blue-400';
            case 'daily_goals_completed':
            case 'average_pacing':
            case 'total_cohorts':
                return 'text-purple-400';
            case 'cards_completed':
            case 'total_assigned_students':
            case 'total_students':
            case 'total_institutions':
            default:
                return 'text-orange-400';
        }
    };

    const getKpiTitle = (key) => {
        return key.replace(/_/g, ' ').toUpperCase();
    };

    const getKpiValueString = (key, val) => {
        if (key === 'average_pacing') return `${val}x`;
        if (key.includes('score') || key.includes('comprehension')) return `${val}%`;
        return val.toLocaleString();
    };

    const isStudent = selectedRole === 'student';
    const isTeacher = selectedRole === 'teacher';
    const isAdmin = ['admin', 'institution_admin', 'regional_admin'].includes(selectedRole);
    const isStaff = user?.role && ['teacher', 'admin', 'institution_admin', 'regional_admin'].includes(user.role.toLowerCase());

    return (
        <div className="space-y-6 pb-12">
            {/* Header section with live health flag */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        <FaEye className="text-orange-500 animate-pulse" />
                        Gurukul Drishti Control Panel
                    </h3>
                    <p className="text-gray-400 text-xs sm:text-sm">
                        Canonical institutional operating dashboard with live aggregate signals, alert flows, and audit trail monitors.
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">Health Status:</span>
                    {isOnline === null ? (
                        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-gray-400 text-[10px] font-bold">
                            <span className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-pulse"></span>
                            <span>PINGING...</span>
                        </div>
                    ) : isOnline ? (
                        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-[10px] font-bold">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-ping"></span>
                            <span>SYSTEM ONLINE</span>
                        </div>
                    ) : isWarmingUp ? (
                        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 text-[10px] font-bold">
                            <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse"></span>
                            <span>WARMING UP...</span>
                        </div>
                    ) : (
                        <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-[10px] font-bold">
                            <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
                            <span>SYSTEM OFFLINE</span>
                        </div>
                    )}
                    <button 
                        onClick={() => { checkSystemHealth(true); loadDashboardData(); }}
                        className="p-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-xs transition-colors"
                        title="Sync Data"
                    >
                        <FaSync className={loading ? "animate-spin text-orange-500" : "text-gray-300"} />
                    </button>
                </div>
            </div>

            {/* Student Telemetry Selector Row for Staff Roles */}
            {isStaff && (
                <div className="glass-panel p-4 rounded-2xl border border-white/10 bg-black/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                        <span className="text-xs font-semibold text-gray-400">Student Telemetry Selector:</span>
                        <select
                            value={selectedStudentId}
                            onChange={(e) => {
                                const id = e.target.value;
                                setSelectedStudentId(id);
                                if (id) {
                                    const studentObj = students.find(s => s.id === id);
                                    setSelectedStudentName(studentObj?.full_name || studentObj?.email || "Student");
                                    setSelectedRole("student");
                                } else {
                                    setSelectedStudentName("");
                                    // Reset role back to authentic user role
                                    const normalizeRole = (r) => {
                                        if (!r) return '';
                                        const clean = r.toLowerCase().replace(/_/g, '-');
                                        if (clean === 'institution-admin') return 'admin';
                                        return clean;
                                    };
                                    setSelectedRole(normalizeRole(user?.role));
                                }
                            }}
                            className="bg-black/60 border border-white/10 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-orange-500/50 cursor-pointer min-w-[200px]"
                        >
                            <option value="">-- Select Student (Self) --</option>
                            {students.map((student) => (
                                <option key={student.id} value={student.id}>
                                    {student.full_name || student.email}
                                </option>
                            ))}
                        </select>
                    </div>

                    {selectedStudentId && (
                        <div className="flex items-center gap-3">
                            <span className="text-xs text-orange-400 font-bold animate-pulse">
                                ➔ Viewing student: {selectedStudentName}
                            </span>
                            <button
                                onClick={() => {
                                    setSelectedStudentId("");
                                    setSelectedStudentName("");
                                    const normalizeRole = (r) => {
                                        if (!r) return '';
                                        const clean = r.toLowerCase().replace(/_/g, '-');
                                        if (clean === 'institution-admin') return 'admin';
                                        return clean;
                                    };
                                    setSelectedRole(normalizeRole(user?.role));
                                }}
                                className="px-3 py-1 rounded-lg bg-orange-600/20 hover:bg-orange-600/40 border border-orange-500/30 text-orange-300 text-[10px] font-bold uppercase transition-all"
                            >
                                Clear Selection
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* Backend cold-start notice (non-demo, offline state) */}
            {!isDemoMode && !isOnline && (
                <div className="flex items-start gap-3 p-3.5 rounded-xl bg-yellow-600/10 border border-yellow-500/20 text-yellow-300 text-xs leading-relaxed">
                    <FaExclamationTriangle className="text-base shrink-0 mt-0.5 text-yellow-400" />
                    <div>
                        <span className="font-bold text-yellow-300">Backend is Starting Up</span>
                        {isWarmingUp ? (
                            <span className="ml-1">— The Render server is waking from sleep. Live data will load automatically in ~30–60 seconds. The data shown below is cached from your last session.</span>
                        ) : (
                            <span className="ml-1">— The backend could not be reached. This may be a temporary Render cold-start. Click the sync button above to retry, or wait a moment and refresh.</span>
                        )}
                    </div>
                </div>
            )}

            {/* Simulation controls & configuration dashboard options */}
            {isDemoMode && (
                <div className="glass-panel p-4 rounded-2xl border border-white/10 bg-black/30 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                    <div className="flex flex-wrap items-center gap-2">
                        <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider mr-2">Simulate Dashboard View:</span>
                        <button 
                            onClick={() => setSelectedRole("student")}
                            className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all ${
                                selectedRole === "student"
                                    ? 'bg-gradient-to-r from-orange-600/20 to-amber-600/20 border-orange-500/40 text-white' 
                                    : 'bg-white/5 border-transparent text-gray-400 hover:bg-white/10'
                            }`}
                        >
                            Student View
                        </button>
                        <button 
                            onClick={() => setSelectedRole("teacher")}
                            className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all ${
                                selectedRole === "teacher"
                                    ? 'bg-gradient-to-r from-orange-600/20 to-amber-600/20 border-orange-500/40 text-white' 
                                    : 'bg-white/5 border-transparent text-gray-400 hover:bg-white/10'
                            }`}
                        >
                            Teacher View
                        </button>
                        <button 
                            onClick={() => setSelectedRole("admin")}
                            className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all ${
                                selectedRole === "admin"
                                    ? 'bg-gradient-to-r from-orange-600/20 to-amber-600/20 border-orange-500/40 text-white' 
                                    : 'bg-white/5 border-transparent text-gray-400 hover:bg-white/10'
                            }`}
                        >
                            Institution Admin
                        </button>
                        <button 
                            onClick={() => setSelectedRole("regional-admin")}
                            className={`px-3 py-1.5 rounded-xl border text-xs font-bold transition-all ${
                                selectedRole === "regional-admin"
                                    ? 'bg-gradient-to-r from-orange-600/20 to-amber-600/20 border-orange-500/40 text-white' 
                                    : 'bg-white/5 border-transparent text-gray-400 hover:bg-white/10'
                            }`}
                        >
                            Regional Admin
                        </button>
                    </div>

                    <div className="flex items-center gap-3">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input 
                                type="checkbox" 
                                checked={useMockData} 
                                onChange={(e) => setUseMockData(e.target.checked)}
                                className="form-checkbox bg-black/60 border-white/10 text-orange-500 rounded focus:ring-0"
                            />
                            <span className="text-xs font-bold text-gray-300">Force Mock Simulation Mode</span>
                        </label>
                    </div>
                </div>
            )}

            {/* Live Data Connection warning for RBAC restrictions */}
            {isDemoMode && !useMockData && user?.role?.toLowerCase() !== selectedRole && (
                <div className="flex items-start gap-3 p-3.5 rounded-xl bg-orange-600/10 border border-orange-500/20 text-orange-400 text-xs leading-relaxed">
                    <FaInfoCircle className="text-base shrink-0 mt-0.5" />
                    <div>
                        <span className="font-bold">Access Warning:</span> You are currently viewing the simulated <span className="font-semibold underline capitalize">{selectedRole}</span> dashboard while authenticated as an <span className="font-semibold underline capitalize">{user?.role}</span>. Real-time API edits may fail or default to mock data fallback due to backend RBAC boundaries. Use the credentials reference below to test real authorization states.
                    </div>
                </div>
            )}

            {/* KPI grid section */}
            <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-orange-400 mb-4 flex items-center gap-2">
                    <FaChartLine className="text-xs" />
                    Drishti Reusable Dashboard Primitives
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {loading ? (
                        Array.from({ length: 4 }).map((_, idx) => (
                            <KPICard key={idx} loading={true} />
                        ))
                    ) : (
                        Object.keys(dashboardData?.kpis || {}).map((key) => (
                            <KPICard 
                                key={key}
                                title={getKpiTitle(key)}
                                value={getKpiValueString(key, dashboardData?.kpis?.[key])}
                                subText={key === 'learning_score' ? '➔ System average' : '➔ Active telemetry'}
                                color={getKpiColor(key)}
                                icon={FaCheckCircle}
                            />
                        ))
                    )}
                </div>
            </div>

            {/* Alert, action, and summary status layout grids */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Column 1: Alerts */}
                <div className="lg:col-span-1">
                    <div className="glass-panel p-5 rounded-2xl border border-white/10 bg-black/30 h-full flex flex-col justify-between">
                        <div>
                            <h4 className="text-xs font-bold uppercase tracking-wider text-gray-300 mb-4">Active Anomaly Signal Feed</h4>
                            <div className="space-y-3">
                                {loading ? (
                                    <div className="text-center py-6 text-gray-500 text-xs">Loading alerts...</div>
                                ) : (dashboardData?.open_alerts || []).length === 0 ? (
                                    <div className="text-center py-8 text-gray-500 text-xs border border-dashed border-white/5 rounded-xl">
                                        No active anomaly signals detected.
                                    </div>
                                ) : (
                                    (dashboardData?.open_alerts || []).map((alt) => (
                                        <AlertCard 
                                            key={alt.id}
                                            alert={alt}
                                            userRole={selectedRole}
                                            onStatusUpdate={handleAlertStatus}
                                            onAssign={handleAlertAssign}
                                            updating={updatingId === alt.id}
                                        />
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Column 2: Actions */}
                <div className="lg:col-span-1">
                    <div className="glass-panel p-5 rounded-2xl border border-white/10 bg-black/30 h-full flex flex-col justify-between">
                        <div>
                            <h4 className="text-xs font-bold uppercase tracking-wider text-gray-300 mb-4">Urgent Governance Actions</h4>
                            <div className="space-y-3">
                                {loading ? (
                                    <div className="text-center py-6 text-gray-500 text-xs">Loading actions...</div>
                                ) : (dashboardData?.pending_actions || []).length === 0 ? (
                                    <div className="text-center py-8 text-gray-500 text-xs border border-dashed border-white/5 rounded-xl">
                                        No pending governance actions.
                                    </div>
                                ) : (
                                    (dashboardData?.pending_actions || []).map((act) => (
                                        <ActionCard 
                                            key={act.id}
                                            action={act}
                                            userRole={selectedRole}
                                            onStatusUpdate={handleActionStatus}
                                            onAssign={handleActionAssign}
                                            updating={updatingId === act.id}
                                        />
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Column 3: Status Summary */}
                <div className="lg:col-span-1">
                    {loading ? (
                        <div className="glass-panel p-5 rounded-2xl border border-white/10 bg-black/30 h-full flex items-center justify-center text-xs text-gray-500">
                            Loading status...
                        </div>
                    ) : (
                        <StatusCard 
                            title={`${selectedRole.toUpperCase()} compliance status`}
                            statusSummary={dashboardData?.status_summary || {}}
                            role={selectedRole}
                        />
                    )}
                </div>
            </div>

            {/* Bottom Section: Activity History & Trace Telemetry Monitor */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Activity Feed logs */}
                <div className="lg:col-span-2 space-y-4">
                    <div className="glass-panel p-5 rounded-2xl border border-white/10 bg-black/30">
                        <h4 className="text-xs font-bold uppercase tracking-wider text-orange-400 mb-4 flex items-center gap-2">
                            <FaHistory className="text-xs" />
                            Recent Operations & Event Activity Feed
                        </h4>
                        
                        <div className="space-y-3 max-h-[350px] overflow-y-auto pr-1 custom-scrollbar">
                            {loading ? (
                                <div className="text-center py-6 text-gray-500 text-xs">Loading events...</div>
                            ) : (dashboardData?.recent_activity || []).length === 0 ? (
                                <div className="text-center py-8 text-gray-500 text-xs">
                                    No recent activity logs found.
                                </div>
                            ) : (
                                (dashboardData?.recent_activity || []).map((act, idx) => (
                                    <ActivityCard key={idx} activity={act} />
                                ))
                            )}
                        </div>
                    </div>
                </div>

                {/* Terminal logs monitor */}
                <div className="lg:col-span-1">
                    <div className="glass-panel p-5 rounded-2xl border border-white/10 bg-[#080905] h-full flex flex-col justify-between min-h-[250px]">
                        <div>
                            <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-2">
                                <span className="text-xs font-bold text-green-400 font-mono flex items-center gap-2">
                                    <FaTerminal />
                                    Drishti Telemetry Trace Monitor
                                </span>
                                <span className="w-2.5 h-2.5 rounded-full bg-green-500 animate-ping"></span>
                            </div>
                            <div className="font-mono text-[10px] text-green-400 space-y-2 overflow-y-auto max-h-[200px] custom-scrollbar">
                                {terminalLogs.map((log, idx) => (
                                    <div key={idx} className="whitespace-pre-wrap">{log}</div>
                                ))}
                            </div>
                        </div>
                        <button 
                            onClick={() => setTerminalLogs(["Cleared. Awaiting Operator Action..."])}
                            className="w-full py-2 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 text-xs font-bold text-gray-400 hover:text-white transition-colors mt-4"
                        >
                            Reset Console Logs
                        </button>
                    </div>
                </div>
            </div>

            {/* Developer credentials quick reference guide */}
            {isDemoMode && (
                <div className="glass-panel p-5 sm:p-6 rounded-2xl border border-white/10 bg-black/40">
                    <h4 className="text-sm font-bold uppercase tracking-wider text-orange-400 mb-3 flex items-center gap-2">
                        <FaKey className="text-xs text-orange-500" />
                        Developer Credentials Quick Reference (Testing RBAC)
                    </h4>
                    <p className="text-xs text-gray-400 mb-4 leading-relaxed">
                        The backend SQLite database was pre-seeded with 5,000 students and 200 teachers. If you encounter <span className="text-orange-300">403 Forbidden</span> bounds restrictions when requesting live data, logout of the app and authenticate using these accounts:
                    </p>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="p-4 rounded-xl border border-white/5 bg-white/5">
                            <div className="text-[10px] font-bold text-blue-400 uppercase tracking-widest mb-2">Student Account</div>
                            <div className="space-y-1 text-xs">
                                <div><span className="text-gray-500 font-medium">Email:</span> <code className="text-gray-200 font-mono select-all">student_1@test.gurukul</code></div>
                                <div><span className="text-gray-500 font-medium">Password:</span> <code className="text-gray-200 font-mono">GurukulTest@123</code></div>
                            </div>
                        </div>

                        <div className="p-4 rounded-xl border border-white/5 bg-white/5">
                            <div className="text-[10px] font-bold text-purple-400 uppercase tracking-widest mb-2">Teacher Account</div>
                            <div className="space-y-1 text-xs">
                                <div><span className="text-gray-500 font-medium">Email:</span> <code className="text-gray-200 font-mono select-all">teacher_1@test.gurukul</code></div>
                                <div><span className="text-gray-500 font-medium">Password:</span> <code className="text-gray-200 font-mono">GurukulTest@123</code></div>
                            </div>
                        </div>

                        <div className="p-4 rounded-xl border border-white/5 bg-white/5">
                            <div className="text-[10px] font-bold text-orange-400 uppercase tracking-widest mb-2">Admin Account</div>
                            <div className="space-y-1 text-xs">
                                <div><span className="text-gray-500 font-medium">Email:</span> <code className="text-gray-200 font-mono select-all">admin@test.gurukul</code></div>
                                <div><span className="text-gray-500 font-mono">Password:</span> <code className="text-gray-200 font-mono">GurukulTest@123</code></div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default GurukulDrishti;
