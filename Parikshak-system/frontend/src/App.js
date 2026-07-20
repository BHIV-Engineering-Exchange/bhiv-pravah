import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from './contexts/ThemeContext';
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import SubmitTask from './pages/SubmitTask';
import ReviewResult from './pages/ReviewResult';
import NextTask from './pages/NextTask';
import TaskHistory from './pages/TaskHistory';
import ReviewDashboard from './pages/ReviewDashboard';
import NiyantranAssignment from './pages/NiyantranAssignment';
import CandidateTimeline from './pages/CandidateTimeline';
import DesignSystem from './pages/DesignSystem';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import Profile from './pages/Profile';
import GCShakti from './pages/GCShakti';
import './index.css';

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            refetchOnWindowFocus: false,
            retry: 1,
            staleTime: 30000,
        },
    },
});

function App() {
    return (
        <ErrorBoundary>
            <QueryClientProvider client={queryClient}>
                <ThemeProvider>
                    <Router>
                        <Layout>
                            <Routes>
                                <Route path="/" element={<Dashboard />} />
                                <Route path="/submit" element={<SubmitTask />} />
                                <Route path="/review/:taskId" element={<ReviewResult />} />
                                <Route path="/next/:taskId" element={<NextTask />} />
                                <Route path="/history" element={<TaskHistory />} />
                                <Route path="/review-queue" element={<ReviewDashboard />} />
                                <Route path="/assign/:submissionId" element={<NiyantranAssignment />} />
                                <Route path="/candidate-timeline" element={<CandidateTimeline />} />
                                <Route path="/design-system" element={<DesignSystem />} />
                                <Route path="/analytics" element={<Analytics />} />
                                <Route path="/settings" element={<Settings />} />
                                <Route path="/profile" element={<Profile />} />
                                <Route path="/shakti" element={<GCShakti />} />
                            </Routes>
                        </Layout>
                    </Router>
                </ThemeProvider>
            </QueryClientProvider>
        </ErrorBoundary>
    );
}

export default App;