import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import API_BASE_URL from '../config';
import Sidebar from '../components/Sidebar';
import { FaBookOpen, FaFlipboard, FaClipboardList, FaFileAlt, FaSpinner, FaFilter, FaSearch, FaSync } from 'react-icons/fa';
import { handleApiError } from '../utils/apiClient';
import { createLesson } from '../utils/contextManager';
import { useDebounce } from '../hooks/useDebounce';

const MyContent = () => {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState('all'); // 'all', 'summaries', 'flashcards', 'tests', 'subjects'
    const [content, setContent] = useState({
        summaries: [],
        flashcards: [],
        testResults: [],
        subjectData: []
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [searchQuery, setSearchQuery] = useState('');
    const debouncedSearchQuery = useDebounce(searchQuery, 300); // Debounce search by 300ms
    const [syncing, setSyncing] = useState(false);
    const [syncMessage, setSyncMessage] = useState('');

    useEffect(() => {
        fetchAllContent();
        
        // Create a general lesson context when the user enters MyContent
        const createLearningSession = async () => {
            try {
                console.log('[MyContent] Attempting to create learning session...');
                const result = await createLesson(
                    'Learning Session',
                    'General',
                    'Self-directed Learning',
                    'User is exploring their generated content and learning materials.'
                );
                if (result) {
                    console.log('[MyContent] Learning session created successfully:', result.lesson_id);
                } else {
                    console.error('[MyContent] Failed to create learning session - no result returned');
                }
            } catch (error) {
                console.error('[MyContent] Error creating learning session:', error);
            }
        };
        
        createLearningSession();
    }, []);

    const fetchAllContent = async () => {
        try {
            setLoading(true);
            setError('');
            
            const token = localStorage.getItem('auth_token');
            const headers = {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            };

            // Fetch all content types in parallel
            const [summariesRes, flashcardsRes, testResultsRes, subjectDataRes] = await Promise.allSettled([
                fetch(`${API_BASE_URL}/api/v1/learning/summaries`, { headers }),
                fetch(`${API_BASE_URL}/api/v1/flashcards`, { headers }),
                fetch(`${API_BASE_URL}/api/v1/quiz/results`, { headers }),
                fetch(`${API_BASE_URL}/api/v1/learning/subject-data`, { headers })
            ]);

            const summaries = summariesRes.status === 'fulfilled' && summariesRes.value.ok
                ? await summariesRes.value.json()
                : [];
            const flashcards = flashcardsRes.status === 'fulfilled' && flashcardsRes.value.ok
                ? await flashcardsRes.value.json()
                : [];
            const testResults = testResultsRes.status === 'fulfilled' && testResultsRes.value.ok
                ? await testResultsRes.value.json()
                : [];
            const subjectData = subjectDataRes.status === 'fulfilled' && subjectDataRes.value.ok
                ? await subjectDataRes.value.json()
                : [];

            setContent({
                summaries: Array.isArray(summaries) ? summaries : [],
                flashcards: Array.isArray(flashcards) ? flashcards : [],
                testResults: Array.isArray(testResults) ? testResults : [],
                subjectData: Array.isArray(subjectData) ? subjectData : []
            });
        } catch (err) {
            console.error('Error fetching content:', err);
            setError('Failed to load your content. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const filterContent = (items, query) => {
        if (!query) return items;
        const lowerQuery = query.toLowerCase();
        return items.filter(item => {
            const title = (item.title || item.subject || item.topic || '').toLowerCase();
            const content = (item.content || item.notes || item.question || '').toLowerCase();
            return title.includes(lowerQuery) || content.includes(lowerQuery);
        });
    };

    const getFilteredContent = () => {
        let filtered = [];
        
        // Use debounced search query for filtering
        if (activeTab === 'all' || activeTab === 'summaries') {
            filtered = [...filtered, ...filterContent(content.summaries, debouncedSearchQuery).map(s => ({ ...s, type: 'summary' }))];
        }
        if (activeTab === 'all' || activeTab === 'flashcards') {
            filtered = [...filtered, ...filterContent(content.flashcards, debouncedSearchQuery).map(f => ({ ...f, type: 'flashcard' }))];
        }
        if (activeTab === 'all' || activeTab === 'tests') {
            filtered = [...filtered, ...filterContent(content.testResults, debouncedSearchQuery).map(t => ({ ...t, type: 'test' }))];
        }
        if (activeTab === 'all' || activeTab === 'subjects') {
            filtered = [...filtered, ...filterContent(content.subjectData, debouncedSearchQuery).map(s => ({ ...s, type: 'subject' }))];
        }
        
        // Sort by date (newest first)
        return filtered.sort((a, b) => {
            const dateA = new Date(a.created_at || a.synced_at || 0);
            const dateB = new Date(b.created_at || b.synced_at || 0);
            return dateB - dateA;
        });
    };

    const handleSyncToEMS = async () => {
        try {
            setSyncing(true);
            setSyncMessage('');
            setError('');
            
            const token = localStorage.getItem('auth_token');
            const response = await fetch(`${API_BASE_URL}/api/v1/ems/sync/all-content`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: response.statusText }));
                throw new Error(errorData.detail || 'Failed to sync content');
            }
            
            const result = await response.json();
            
            if (result.total_synced > 0) {
                setSyncMessage(`✅ Successfully synced ${result.total_synced} items to EMS!${result.total_failed > 0 ? ` (${result.total_failed} failed)` : ''}`);
            } else if (result.total_failed > 0) {
                // Show detailed errors
                const errorDetails = [];
                if (result.results.summaries.errors.length > 0) errorDetails.push(...result.results.summaries.errors);
                if (result.results.flashcards.errors.length > 0) errorDetails.push(...result.results.flashcards.errors);
                if (result.results.test_results.errors.length > 0) errorDetails.push(...result.results.test_results.errors);
                if (result.results.subject_data.errors.length > 0) errorDetails.push(...result.results.subject_data.errors);
                
                const errorMsg = errorDetails.slice(0, 3).join('; '); // Show first 3 errors
                setSyncMessage(`❌ Sync failed: ${errorMsg}${errorDetails.length > 3 ? '...' : ''}`);
            } else {
                setSyncMessage('⚠️ No content found to sync.');
            }
            
            // Refresh content after sync
            setTimeout(() => {
                fetchAllContent();
                setSyncMessage('');
            }, 5000);
        } catch (err) {
            console.error('Sync error:', err);
            setSyncMessage(`❌ Sync failed: ${err.message}`);
        } finally {
            setSyncing(false);
        }
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'Unknown';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateString;
        }
    };

    const tabs = [
        { id: 'all', label: 'All Content', icon: FaFilter },
        { id: 'summaries', label: 'Summaries', icon: FaFileAlt, count: content.summaries.length },
        { id: 'flashcards', label: 'Flashcards', icon: FaFlipboard, count: content.flashcards.length },
        { id: 'tests', label: 'Tests', icon: FaClipboardList, count: content.testResults.length },
        { id: 'subjects', label: 'Subjects', icon: FaBookOpen, count: content.subjectData.length }
    ];

    const filteredContent = getFilteredContent();

    if (loading) {
        return (
            <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6 pb-20">
                <Sidebar />
                <div className="flex-grow flex justify-center items-center">
                    <div className="text-center">
                        <FaSpinner className="animate-spin text-4xl text-orange-400 mx-auto mb-4" />
                        <p className="text-gray-300 text-lg">Loading your content...</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6 pb-20">
            <Sidebar />
            <div className="flex-grow flex flex-col gap-3 sm:gap-6">
            <div className="w-full max-w-7xl mx-auto">
                <div className="mb-6 sm:mb-8">
                    <div className="flex justify-between items-start mb-2">
                        <div>
                            <h2 className="text-2xl sm:text-3xl font-bold font-heading text-white flex items-center gap-3 mb-2">
                                <FaFilter className="text-orange-400" />
                                My Content
                            </h2>
                            <p className="text-gray-200 text-xs sm:text-sm font-medium">
                                View all your generated summaries, flashcards, tests, and subject explorations
                            </p>
                        </div>
                        <button
                            onClick={handleSyncToEMS}
                            disabled={syncing}
                            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 text-white rounded-xl font-medium shadow-lg transition-transform hover:-translate-y-1 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0"
                        >
                            {syncing ? (
                                <>
                                    <FaSpinner className="animate-spin" />
                                    <span>Syncing...</span>
                                </>
                            ) : (
                                <>
                                    <FaSync />
                                    <span>Sync to EMS</span>
                                </>
                            )}
                        </button>
                    </div>
                    {syncMessage && (
                        <div className={`mt-3 p-3 rounded-lg text-sm ${
                            syncMessage.includes('success') 
                                ? 'bg-green-500/20 text-green-300 border border-green-500/30' 
                                : 'bg-red-500/20 text-red-300 border border-red-500/30'
                        }`}>
                            {syncMessage}
                        </div>
                    )}
                </div>

                {/* Search Bar */}
                <div className="mb-6">
                    <div className="relative">
                        <FaSearch className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search your content..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-12 pr-4 py-3 bg-black/60 border border-white/20 rounded-xl text-white placeholder-gray-500 focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition"
                        />
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex flex-wrap gap-2 mb-6 overflow-x-auto">
                    {tabs.map((tab) => {
                        const Icon = tab.icon;
                        const isActive = activeTab === tab.id;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`
                                    flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all
                                    ${isActive
                                        ? 'bg-gradient-to-r from-orange-600 to-amber-600 text-white shadow-lg'
                                        : 'bg-white/5 text-gray-300 hover:bg-white/10 hover:text-white'
                                    }
                                `}
                            >
                                <Icon />
                                <span>{tab.label}</span>
                                {tab.count !== undefined && (
                                    <span className={`px-2 py-0.5 rounded-full text-xs ${isActive ? 'bg-white/20' : 'bg-white/10'}`}>
                                        {tab.count}
                                    </span>
                                )}
                            </button>
                        );
                    })}
                </div>

                {error && (
                    <div className="mb-6 glass-panel border border-red-500/30 bg-red-500/10 p-4 rounded-xl">
                        <p className="text-red-300 text-sm">{error}</p>
                    </div>
                )}

                {/* Content List */}
                {filteredContent.length === 0 ? (
                    <div className="glass-panel p-8 sm:p-12 text-center border border-white/10 rounded-2xl">
                        <div className="text-6xl mb-4">📚</div>
                        <h3 className="text-xl font-semibold text-white mb-2">No Content Found</h3>
                        <p className="text-gray-300">
                            {searchQuery ? 'No content matches your search.' : 'Start generating content to see it here!'}
                        </p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                        {filteredContent.map((item) => (
                            <ContentCard key={`${item.type}-${item.id}`} item={item} formatDate={formatDate} />
                        ))}
                    </div>
                )}
            </div>
            </div>
        </div>
    );
};

const ContentCard = ({ item, formatDate }) => {
    const [expanded, setExpanded] = useState(false);
    const [lessonCreated, setLessonCreated] = useState(false);
    
    const getTypeIcon = (type) => {
        switch (type) {
            case 'summary': return <FaFileAlt className="text-orange-400" />;
            case 'flashcard': return <FaFlipboard className="text-blue-400" />;
            case 'test': return <FaClipboardList className="text-green-400" />;
            case 'subject': return <FaBookOpen className="text-purple-400" />;
            default: return <FaFileAlt className="text-gray-400" />;
        }
    };

    const getTypeLabel = (type) => {
        switch (type) {
            case 'summary': return 'Summary';
            case 'flashcard': return 'Flashcard';
            case 'test': return 'Test';
            case 'subject': return 'Subject';
            default: return 'Content';
        }
    };

    const getTypeColor = (type) => {
        switch (type) {
            case 'summary': return 'border-orange-500/50 bg-orange-500/10';
            case 'flashcard': return 'border-blue-500/50 bg-blue-500/10';
            case 'test': return 'border-green-500/50 bg-green-500/10';
            case 'subject': return 'border-purple-500/50 bg-purple-500/10';
            default: return 'border-white/10 bg-white/5';
        }
    };

    const previewText = (item.type === 'summary' ? item.content : 
                         item.type === 'flashcard' ? item.question :
                         item.type === 'test' ? `${item.subject} - ${item.topic}` :
                         item.type === 'subject' ? item.notes : '').substring(0, 150);

    const handleExpand = async () => {
        const newExpandedState = !expanded;
        setExpanded(newExpandedState);
        
        // Create lesson context when user starts engaging with specific content
        if (newExpandedState && !lessonCreated) {
            try {
                console.log('[ContentCard] Attempting to create specific lesson for item:', item.id);
                const result = await createLesson(
                    item.title || item.subject || item.question || item.topic || 'Learning Content',
                    item.subject || 'General',
                    item.topic || item.type || 'Learning Activity',
                    item.content || item.notes || item.question || 'Detailed learning content'
                );
                if (result) {
                    setLessonCreated(true);
                    console.log('[ContentCard] Specific lesson created successfully:', result.lesson_id);
                } else {
                    console.error('[ContentCard] Failed to create specific lesson - no result returned');
                }
            } catch (error) {
                console.error('[ContentCard] Error creating lesson context:', error);
            }
        }
    };

    return (
        <div className={`glass-panel p-6 border rounded-2xl hover:shadow-xl hover:-translate-y-1 transition-all ${getTypeColor(item.type)}`}>
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                    {getTypeIcon(item.type)}
                    <span className="text-xs font-semibold text-gray-300 uppercase">{getTypeLabel(item.type)}</span>
                </div>
                {item.percentage !== undefined && (
                    <span className="px-2 py-1 bg-green-500/20 text-green-300 rounded-full text-xs font-medium border border-green-500/30">
                        {item.percentage}%
                    </span>
                )}
            </div>

            <h3 className="text-lg font-bold text-white mb-2 line-clamp-2">
                {item.title || item.subject || item.question || item.topic || 'Untitled'}
            </h3>

            {item.type === 'test' && (
                <div className="mb-3 text-sm text-gray-300">
                    <span>Score: {item.score}/{item.total_questions}</span>
                    {item.difficulty && (
                        <span className="ml-2 px-2 py-0.5 bg-white/10 rounded text-xs">
                            {item.difficulty}
                        </span>
                    )}
                </div>
            )}

            {item.type === 'subject' && (
                <div className="mb-3 text-sm text-gray-300">
                    <span>{item.subject} • {item.topic}</span>
                </div>
            )}

            <p className="text-sm text-gray-300 mb-4 line-clamp-3">
                {previewText}...
            </p>

            <div className="flex items-center justify-between pt-3 border-t border-white/10">
                <span className="text-xs text-gray-400">{formatDate(item.created_at)}</span>
                <button
                    onClick={handleExpand}
                    className="text-xs text-orange-400 hover:text-orange-300 font-medium"
                >
                    {expanded ? 'Show Less' : 'View Details'}
                </button>
            </div>

            {expanded && (
                <div className="mt-4 pt-4 border-t border-white/10 text-sm text-gray-300">
                    {item.type === 'summary' && (
                        <div className="whitespace-pre-wrap">{item.content}</div>
                    )}
                    {item.type === 'flashcard' && (
                        <div>
                            <p className="font-semibold mb-2">Q: {item.question}</p>
                            <p>A: {item.answer}</p>
                        </div>
                    )}
                    {item.type === 'test' && (
                        <div>
                            <p className="mb-2"><strong>Subject:</strong> {item.subject}</p>
                            <p className="mb-2"><strong>Topic:</strong> {item.topic}</p>
                            <p><strong>Questions:</strong> {item.num_questions || item.total_questions}</p>
                        </div>
                    )}
                    {item.type === 'subject' && (
                        <div className="whitespace-pre-wrap max-h-96 overflow-y-auto">{item.notes}</div>
                    )}
                </div>
            )}
        </div>
    );
};

export default MyContent;

