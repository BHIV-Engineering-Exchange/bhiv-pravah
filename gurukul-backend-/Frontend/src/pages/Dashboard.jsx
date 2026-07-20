import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import { StudyTimeWidget, KarmaWidget, AchievementsWidget, GoalWidget } from '../components/DashboardWidgets';
import LearningFlow from '../components/LearningFlow';
import LearningProgress from '../components/LearningProgress';
import ReflectionModal from '../components/ReflectionModal';
import NextStepCard from '../components/NextStepCard';
import AlertCard from '../components/dashboard/AlertCard';
import ActionCard from '../components/dashboard/ActionCard';
import { apiGet, apiPut, handleApiError } from '../utils/apiClient';
import { FaHeart } from 'react-icons/fa';
import { SkeletonGrid } from '../components/LoadingSkeleton';
import ErrorBoundary from '../components/ErrorBoundary';
import { usePerformanceMonitor } from '../hooks/usePerformance';

const Dashboard = ({
    studyTimeSeconds,
    targetGoalSeconds,
    timeLeft,
    isActive,
    onStartGoal,
    onStopGoal
}) => {
    // Performance monitoring
    usePerformanceMonitor('Dashboard');

    // Soul / Journey State
    const [journeyStep, setJourneyStep] = useState('improve'); // Default fallback
    const [isReflectionOpen, setIsReflectionOpen] = useState(false);
    const [loadingJourney, setLoadingJourney] = useState(true);

    // Alerts & Actions state
    const [alerts, setAlerts] = useState([]);
    const [actions, setActions] = useState([]);
    const [loadingTelemetry, setLoadingTelemetry] = useState(true);
    const [updatingId, setUpdatingId] = useState(null);

    useEffect(() => {
        fetchJourney();
        fetchTelemetry();
    }, []);

    const fetchTelemetry = async () => {
        try {
            setLoadingTelemetry(true);
            const data = await apiGet('/api/v1/dashboard/student');
            setAlerts(data.open_alerts || []);
            setActions(data.pending_actions || []);
        } catch (err) {
            console.warn("Failed to fetch student dashboard telemetry:", err);
        } finally {
            setLoadingTelemetry(false);
        }
    };

    const handleAlertStatus = async (id, status) => {
        setUpdatingId(id);
        try {
            await apiPut(`/api/v1/alerts/${id}/status`, { status });
            await fetchTelemetry();
        } catch (err) {
            console.error("Failed to update alert status:", err);
        } finally {
            setUpdatingId(null);
        }
    };

    const handleActionStatus = async (id, status) => {
        setUpdatingId(id);
        try {
            await apiPut(`/api/v1/actions/${id}/status`, { status });
            await fetchTelemetry();
        } catch (err) {
            console.error("Failed to update action status:", err);
        } finally {
            setUpdatingId(null);
        }
    };

    const fetchJourney = async () => {
        try {
            // Fetch journey data from backend
            // For MVP, if no tracks found, we default to 'enter' or 'improve'
            // If tracks found, we check the first non-completed milestone?
            // Or simplified: We just allow user to manually reflect which is a key part of the journey.

            // NOTE: Since the backend currently returns a list of tracks, 
            // and we don't have a sophisticated logic to map arbitrary tracks to 'steps',
            // we will simulate the connection for now by checking if ANY track is active.

            // Real implementation would be:
            const tracks = await apiGet('/api/v1/soul/journey');

            if (tracks && tracks.length > 0) {
                // Heuristic: Find first milestone that is NOT_STARTED or IN_PROGRESS
                // This is a simplification. 
                // Let's just persist the default 'improve' for now but log specific data if needed.
                // Or better: Checking if they have done a reflection recently?
            }
            setLoadingJourney(false);
        } catch (err) {
            console.warn("Failed to fetch journey:", err);
            setLoadingJourney(false);
        }
    };

    return (
        <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6 pb-20">
            {/* Left Sidebar */}
            <Sidebar />

            <ReflectionModal
                isOpen={isReflectionOpen}
                onClose={() => setIsReflectionOpen(false)}
                onSuccess={() => {
                    // Refresh journey or karma?
                    // Maybe change step to 'improve' if they were on 'reflect'
                    setJourneyStep('improve');
                }}
            />

            {/* Main Content Area */}
            <main className="flex-grow animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
                <div className="mb-4 sm:mb-8 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                        <h2 className="text-2xl sm:text-3xl font-bold font-heading text-white">Dashboard</h2>
                        <p className="text-gray-200 text-xs sm:text-sm font-medium notranslate">
                            {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                        </p>
                    </div>

                    {/* Soul Action: Log Reflection */}
                    <button
                        onClick={() => setIsReflectionOpen(true)}
                        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 hover:to-rose-500 text-white rounded-xl font-bold shadow-lg transition-transform hover:-translate-y-1"
                    >
                        <FaHeart className="text-white" />
                        <span>Daily Reflection</span>
                    </button>
                </div>

                {/* Next Step Recommendation */}
                <NextStepCard currentStep={journeyStep} />

                {/* Learning Flow - Guided Journey */}
                <div className="mb-6 sm:mb-8">
                    <LearningFlow currentStep={journeyStep} />
                </div>

                {/* Improved Grid Layout */}
                <ErrorBoundary>
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6">
                        {/* Column 1 & 2 */}
                        <div className="lg:col-span-2 flex flex-col gap-4 sm:gap-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
                                <ErrorBoundary>
                                    <StudyTimeWidget
                                        targetGoalSeconds={targetGoalSeconds}
                                        timeLeft={timeLeft}
                                        isActive={isActive}
                                        totalStudyTime={studyTimeSeconds}
                                    />
                                </ErrorBoundary>
                                <ErrorBoundary>
                                    <KarmaWidget />
                                </ErrorBoundary>
                            </div>
                            <ErrorBoundary>
                                <GoalWidget
                                    timeLeft={timeLeft}
                                    isActive={isActive}
                                    onStart={onStartGoal}
                                    onStop={onStopGoal}
                                />
                            </ErrorBoundary>
                        </div>

                        {/* Column 3 */}
                        <div className="flex flex-col gap-4 sm:gap-6">
                            <ErrorBoundary>
                                <LearningProgress />
                            </ErrorBoundary>
                            <ErrorBoundary>
                                <AchievementsWidget />
                            </ErrorBoundary>
                        </div>
                    </div>

                    {/* Active Alerts and Action Items */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 mt-6 sm:mt-8">
                        {/* Alerts Card */}
                        <div className="glass-panel p-5 rounded-2xl border border-white/10 bg-black/40">
                            <h3 className="text-sm font-bold uppercase tracking-wider text-red-400 mb-4 flex items-center gap-2">
                                <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></span>
                                Active Anomaly Signals
                            </h3>
                            <div className="space-y-3">
                                {loadingTelemetry ? (
                                    <div className="text-gray-400 text-xs">Loading alerts...</div>
                                ) : alerts.length === 0 ? (
                                    <div className="text-gray-500 text-xs py-8 border border-dashed border-white/5 rounded-xl text-center">
                                        No active anomaly signals detected.
                                    </div>
                                ) : (
                                    alerts.map(alert => (
                                        <AlertCard
                                            key={alert.id}
                                            alert={alert}
                                            userRole="student"
                                            onStatusUpdate={handleAlertStatus}
                                            updating={updatingId === alert.id}
                                        />
                                    ))
                                )}
                            </div>
                        </div>

                        {/* Actions Card */}
                        <div className="glass-panel p-5 rounded-2xl border border-white/10 bg-black/40">
                            <h3 className="text-sm font-bold uppercase tracking-wider text-orange-400 mb-4 flex items-center gap-2">
                                <span className="w-2.5 h-2.5 rounded-full bg-orange-500 animate-pulse"></span>
                                Pending Governance Actions
                            </h3>
                            <div className="space-y-3">
                                {loadingTelemetry ? (
                                    <div className="text-gray-400 text-xs">Loading actions...</div>
                                ) : actions.length === 0 ? (
                                    <div className="text-gray-500 text-xs py-8 border border-dashed border-white/5 rounded-xl text-center">
                                        No pending governance actions.
                                    </div>
                                ) : (
                                    actions.map(action => (
                                        <ActionCard
                                            key={action.id}
                                            action={action}
                                            userRole="student"
                                            onStatusUpdate={handleActionStatus}
                                            updating={updatingId === action.id}
                                        />
                                    ))
                                )}
                            </div>
                        </div>
                    </div>
                </ErrorBoundary>
            </main>
        </div>
    );
};

export default Dashboard;
