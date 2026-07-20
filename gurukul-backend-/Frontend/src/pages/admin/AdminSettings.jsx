import React, { useState, useEffect } from 'react';
import { FaCog, FaFileAlt, FaToggleOn, FaToggleOff, FaEye, FaCheckCircle, FaTimesCircle, FaUser, FaCalendar, FaBook, FaLightbulb, FaGraduationCap } from 'react-icons/fa';
import { apiGet, apiPut, apiDelete, handleApiError } from '../../utils/apiClient';
import { useModal } from '../../contexts/ModalContext';

const AdminSettings = () => {
    const { alert, confirm } = useModal();
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('content'); // content, features, activity
    const [submissions, setSubmissions] = useState([]);
    const [summaries, setSummaries] = useState([]);
    const [flashcards, setFlashcards] = useState([]);

    useEffect(() => {
        fetchContent();
    }, [activeTab]);

    const fetchContent = async () => {
        setLoading(true);
        try {
            if (activeTab === 'content') {
                // Fetch all student content for moderation
                const [summariesData, flashcardsData] = await Promise.all([
                    apiGet('/api/v1/ems/admin/content/summaries').catch(() => []),
                    apiGet('/api/v1/ems/admin/content/flashcards').catch(() => [])
                ]);
                setSummaries(summariesData || []);
                setFlashcards(flashcardsData || []);
            }
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'fetch content' });
            // Don't show error if endpoints don't exist yet
            if (!errorInfo.message.includes('404')) {
                await alert(errorInfo.message, errorInfo.title);
            }
        } finally {
            setLoading(false);
        }
    };

    const handleApproveContent = async (type, id, userName) => {
        const result = await confirm(
            `Approve this ${type} from ${userName}?`,
            'Approve Content'
        );
        if (!result) return;

        try {
            await apiPut(`/api/v1/ems/admin/content/${type}/${id}/approve`, {});
            await alert(`${type} approved successfully!`, 'Success');
            fetchContent();
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'approve content' });
            await alert(errorInfo.message, errorInfo.title);
        }
    };

    const handleRejectContent = async (type, id, userName) => {
        const result = await confirm(
            `Reject this ${type} from ${userName}? This action cannot be undone.`,
            'Reject Content'
        );
        if (!result) return;

        try {
            await apiDelete(`/api/v1/ems/admin/content/${type}/${id}`);
            await alert(`${type} rejected and removed!`, 'Success');
            fetchContent();
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'reject content' });
            await alert(errorInfo.message, errorInfo.title);
        }
    };

    const handleFeatureToggle = async (feature, currentValue) => {
        const result = await confirm(
            `Are you sure you want to ${currentValue ? 'disable' : 'enable'} ${feature} for all students?`,
            'Toggle Student Feature'
        );
        if (!result) return;

        try {
            await apiPut('/api/v1/ems/admin/features', {
                feature: feature.toLowerCase().replace(/\s+/g, '_'),
                enabled: !currentValue
            });
            await alert(`${feature} ${!currentValue ? 'enabled' : 'disabled'} for students!`, 'Success');
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'toggle feature' });
            await alert(errorInfo.message, errorInfo.title);
        }
    };

    const tabs = [
        { id: 'content', label: 'Content Moderation', icon: FaFileAlt },
        { id: 'features', label: 'Student Features', icon: FaToggleOn },
        { id: 'activity', label: 'Recent Activity', icon: FaEye },
    ];

    if (loading && activeTab === 'content') {
        return (
            <div className="glass-panel p-6 rounded-2xl border border-white/10">
                <div className="flex flex-col items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mb-4"></div>
                    <p className="text-gray-400">Loading content...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="glass-panel p-6 rounded-2xl border border-white/10">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
                    <div>
                        <h3 className="text-2xl font-bold text-white flex items-center gap-2 mb-2">
                            <FaCog className="text-orange-500" />
                            Platform Settings
                        </h3>
                        <p className="text-gray-400 text-sm">
                            Manage student content, features, and platform activities
                        </p>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex flex-wrap gap-2 mb-6 border-b border-white/10">
                    {tabs.map(tab => {
                        const Icon = tab.icon;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex items-center gap-2 px-4 py-2 rounded-t-lg transition-colors ${
                                    activeTab === tab.id
                                        ? 'bg-orange-600 text-white border-b-2 border-orange-500'
                                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                                }`}
                            >
                                <Icon />
                                <span className="text-sm font-medium">{tab.label}</span>
                            </button>
                        );
                    })}
                </div>

                {/* Tab Content */}
                <div className="mt-6">
                    {activeTab === 'content' && (
                        <div className="space-y-6">
                            <h4 className="text-lg font-bold text-white mb-4">Content Moderation</h4>
                            <p className="text-gray-400 text-sm mb-4">
                                Review and moderate content submitted by students (PDFs, summaries, flashcards)
                            </p>

                            {/* Summaries Section */}
                            <div>
                                <h5 className="text-white font-semibold mb-3 flex items-center gap-2">
                                    <FaBook className="text-blue-400" />
                                    Student Summaries ({summaries.length || 0})
                                </h5>
                                <div className="space-y-3">
                                    {summaries.length === 0 ? (
                                        <div className="bg-black/40 border border-white/10 rounded-lg p-6 text-center text-gray-400">
                                            No summaries submitted yet.
                                        </div>
                                    ) : (
                                        summaries.map(summary => (
                                            <div key={summary.id} className="bg-black/40 border border-white/10 rounded-lg p-4">
                                                <div className="flex items-start justify-between mb-3">
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-2 mb-2">
                                                            <FaUser className="text-gray-400 text-sm" />
                                                            <span className="text-white font-medium">{summary.user?.full_name || summary.user?.email || 'Unknown User'}</span>
                                                            <span className="text-gray-500 text-xs">•</span>
                                                            <FaCalendar className="text-gray-400 text-xs" />
                                                            <span className="text-gray-400 text-xs">
                                                                {new Date(summary.created_at).toLocaleDateString()}
                                                            </span>
                                                        </div>
                                                        <h6 className="text-white font-semibold mb-1">{summary.title}</h6>
                                                        <p className="text-gray-400 text-sm line-clamp-2">{summary.content.substring(0, 200)}...</p>
                                                        {summary.source && (
                                                            <p className="text-gray-500 text-xs mt-2">Source: {summary.source}</p>
                                                        )}
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2 mt-3">
                                                    <button
                                                        onClick={() => handleApproveContent('summary', summary.id, summary.user?.full_name || 'User')}
                                                        className="flex items-center gap-2 px-3 py-1.5 bg-green-600 hover:bg-green-500 rounded-lg text-white text-sm font-medium transition-colors"
                                                    >
                                                        <FaCheckCircle /> Approve
                                                    </button>
                                                    <button
                                                        onClick={() => handleRejectContent('summary', summary.id, summary.user?.full_name || 'User')}
                                                        className="flex items-center gap-2 px-3 py-1.5 bg-red-600 hover:bg-red-500 rounded-lg text-white text-sm font-medium transition-colors"
                                                    >
                                                        <FaTimesCircle /> Reject
                                                    </button>
                                                    <button
                                                        onClick={() => {
                                                            // View full content in modal
                                                            alert(summary.content, summary.title);
                                                        }}
                                                        className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded-lg text-white text-sm font-medium transition-colors"
                                                    >
                                                        <FaEye /> View Full
                                                    </button>
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>

                            {/* Flashcards Section */}
                            <div className="mt-6">
                                <h5 className="text-white font-semibold mb-3 flex items-center gap-2">
                                    <FaLightbulb className="text-yellow-400" />
                                    Student Flashcards ({flashcards.length || 0})
                                </h5>
                                <div className="space-y-3">
                                    {flashcards.length === 0 ? (
                                        <div className="bg-black/40 border border-white/10 rounded-lg p-6 text-center text-gray-400">
                                            No flashcards created yet.
                                        </div>
                                    ) : (
                                        flashcards.map(flashcard => (
                                            <div key={flashcard.id} className="bg-black/40 border border-white/10 rounded-lg p-4">
                                                <div className="flex items-start justify-between mb-3">
                                                    <div className="flex-1">
                                                        <div className="flex items-center gap-2 mb-2">
                                                            <FaUser className="text-gray-400 text-sm" />
                                                            <span className="text-white font-medium">{flashcard.user?.full_name || flashcard.user?.email || 'Unknown User'}</span>
                                                            <span className="text-gray-500 text-xs">•</span>
                                                            <FaCalendar className="text-gray-400 text-xs" />
                                                            <span className="text-gray-400 text-xs">
                                                                {new Date(flashcard.created_at).toLocaleDateString()}
                                                            </span>
                                                        </div>
                                                        <div className="space-y-2">
                                                            <div>
                                                                <span className="text-gray-400 text-xs">Question:</span>
                                                                <p className="text-white text-sm">{flashcard.question}</p>
                                                            </div>
                                                            <div>
                                                                <span className="text-gray-400 text-xs">Answer:</span>
                                                                <p className="text-gray-300 text-sm">{flashcard.answer}</p>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2 mt-3">
                                                    <button
                                                        onClick={() => handleApproveContent('flashcard', flashcard.id, flashcard.user?.full_name || 'User')}
                                                        className="flex items-center gap-2 px-3 py-1.5 bg-green-600 hover:bg-green-500 rounded-lg text-white text-sm font-medium transition-colors"
                                                    >
                                                        <FaCheckCircle /> Approve
                                                    </button>
                                                    <button
                                                        onClick={() => handleRejectContent('flashcard', flashcard.id, flashcard.user?.full_name || 'User')}
                                                        className="flex items-center gap-2 px-3 py-1.5 bg-red-600 hover:bg-red-500 rounded-lg text-white text-sm font-medium transition-colors"
                                                    >
                                                        <FaTimesCircle /> Reject
                                                    </button>
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'features' && (
                        <div className="space-y-4">
                            <h4 className="text-lg font-bold text-white mb-4">Student Features Control</h4>
                            <p className="text-gray-400 text-sm mb-4">
                                Enable or disable features available to students on their dashboard
                            </p>
                            
                            <div className="space-y-3">
                                <div className="bg-black/40 border border-white/10 rounded-lg p-4">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <div className="text-white font-semibold mb-1">PDF Upload & Summarization</div>
                                            <p className="text-gray-400 text-sm">Allow students to upload PDFs and get AI summaries</p>
                                        </div>
                                        <button
                                            onClick={() => handleFeatureToggle('PDF Upload', true)}
                                            className="text-green-400 hover:text-green-300 transition-colors"
                                        >
                                            <FaToggleOn className="text-3xl" />
                                        </button>
                                    </div>
                                </div>

                                <div className="bg-black/40 border border-white/10 rounded-lg p-4">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <div className="text-white font-semibold mb-1">Subject Explorer</div>
                                            <p className="text-gray-400 text-sm">Allow students to explore subjects and generate notes</p>
                                        </div>
                                        <button
                                            onClick={() => handleFeatureToggle('Subject Explorer', true)}
                                            className="text-green-400 hover:text-green-300 transition-colors"
                                        >
                                            <FaToggleOn className="text-3xl" />
                                        </button>
                                    </div>
                                </div>

                                <div className="bg-black/40 border border-white/10 rounded-lg p-4">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <div className="text-white font-semibold mb-1">Chatbot</div>
                                            <p className="text-gray-400 text-sm">Enable AI chatbot for student questions</p>
                                        </div>
                                        <button
                                            onClick={() => handleFeatureToggle('Chatbot', true)}
                                            className="text-green-400 hover:text-green-300 transition-colors"
                                        >
                                            <FaToggleOn className="text-3xl" />
                                        </button>
                                    </div>
                                </div>

                                <div className="bg-black/40 border border-white/10 rounded-lg p-4">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <div className="text-white font-semibold mb-1">Flashcards</div>
                                            <p className="text-gray-400 text-sm">Allow students to create and study flashcards</p>
                                        </div>
                                        <button
                                            onClick={() => handleFeatureToggle('Flashcards', true)}
                                            className="text-green-400 hover:text-green-300 transition-colors"
                                        >
                                            <FaToggleOn className="text-3xl" />
                                        </button>
                                    </div>
                                </div>

                                <div className="bg-black/40 border border-white/10 rounded-lg p-4">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <div className="text-white font-semibold mb-1">Reflections</div>
                                            <p className="text-gray-400 text-sm">Allow students to write learning reflections</p>
                                        </div>
                                        <button
                                            onClick={() => handleFeatureToggle('Reflections', true)}
                                            className="text-green-400 hover:text-green-300 transition-colors"
                                        >
                                            <FaToggleOn className="text-3xl" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'activity' && (
                        <div className="space-y-4">
                            <h4 className="text-lg font-bold text-white mb-4">Recent Student Activity</h4>
                            <p className="text-gray-400 text-sm mb-4">
                                View recent activities and submissions from students
                            </p>
                            
                            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                                <div className="flex items-start gap-3">
                                    <FaEye className="text-blue-400 mt-1" />
                                    <div>
                                        <h5 className="text-blue-400 font-semibold mb-1">Activity Feed</h5>
                                        <p className="text-gray-300 text-sm">
                                            Recent activity feed will show student submissions, PDF uploads, and learning progress.
                                            This feature will be implemented with backend endpoints.
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-3 mt-4">
                                <div className="bg-black/40 border border-white/10 rounded-lg p-4">
                                    <div className="flex items-center gap-3">
                                        <FaGraduationCap className="text-orange-400" />
                                        <div className="flex-1">
                                            <div className="text-white font-medium">Activity tracking coming soon</div>
                                            <p className="text-gray-400 text-sm">View when students upload PDFs, create summaries, or study flashcards</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default AdminSettings;
