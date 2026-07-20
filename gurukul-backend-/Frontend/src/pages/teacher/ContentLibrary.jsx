import React, { useState, useEffect } from 'react';
import { FaBook, FaSearch, FaFilter, FaDownload, FaTrash, FaEdit } from 'react-icons/fa';
import { apiGet, apiDelete, handleApiError } from '../../utils/apiClient';
import { useModal } from '../../contexts/ModalContext';

const ContentLibrary = () => {
    const { alert, confirm } = useModal();
    const [content, setContent] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterSubject, setFilterSubject] = useState('all');

    useEffect(() => {
        fetchContent();
    }, []);

    const fetchContent = async () => {
        try {
            setLoading(true);
            // TODO: Replace with actual endpoint
            const data = await apiGet('/api/v1/ems/teacher/content').catch(() => []);
            setContent(data || []);
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'fetch content' });
            if (!errorInfo.message.includes('404')) {
                await alert(errorInfo.message, errorInfo.title);
            }
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteContent = async (contentId) => {
        const result = await confirm(
            'Are you sure you want to delete this content? This action cannot be undone.',
            'Delete Content'
        );
        if (!result) return;

        try {
            // TODO: Replace with actual endpoint
            await apiDelete(`/api/v1/ems/teacher/content/${contentId}`);
            await alert('Content deleted successfully!', 'Success');
            fetchContent();
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'delete content' });
            await alert(errorInfo.message, errorInfo.title);
        }
    };

    const filteredContent = content.filter(item => {
        const matchesSearch = item.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                             item.description?.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesFilter = filterSubject === 'all' || item.subject === filterSubject;
        return matchesSearch && matchesFilter;
    });

    if (loading) {
        return (
            <div className="glass-panel p-8 rounded-2xl border border-white/10 text-center">
                <div className="text-gray-400">Loading content library...</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <FaBook className="text-orange-400" />
                    Content Library
                </h3>
                <p className="text-gray-400 text-sm mt-1">Manage all your uploaded lectures, notes, and materials</p>
            </div>

            {/* Search and Filter */}
            <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1 relative">
                    <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search content..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-orange-500"
                    />
                </div>
                <div className="relative">
                    <FaFilter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <select
                        value={filterSubject}
                        onChange={(e) => setFilterSubject(e.target.value)}
                        className="pl-10 pr-8 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-orange-500 appearance-none"
                    >
                        <option value="all">All Subjects</option>
                        <option value="Mathematics">Mathematics</option>
                        <option value="Physics">Physics</option>
                        <option value="Chemistry">Chemistry</option>
                        <option value="Biology">Biology</option>
                        <option value="Computer Science">Computer Science</option>
                        <option value="History">History</option>
                        <option value="Geography">Geography</option>
                        <option value="Literature">Literature</option>
                        <option value="Economics">Economics</option>
                    </select>
                </div>
            </div>

            {/* Content Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredContent.length === 0 ? (
                    <div className="col-span-full glass-panel p-8 rounded-2xl border border-white/10 text-center text-gray-400">
                        No content found. Upload your first material!
                    </div>
                ) : (
                    filteredContent.map((item) => (
                        <div key={item.id} className="glass-panel p-6 rounded-2xl border border-white/10 hover:border-orange-500/50 transition-colors">
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex-1">
                                    <h4 className="text-lg font-semibold text-white mb-2">{item.title}</h4>
                                    {item.description && (
                                        <p className="text-gray-400 text-sm mb-2 line-clamp-2">{item.description}</p>
                                    )}
                                    <div className="flex items-center gap-2 text-xs text-gray-400">
                                        <span>{item.subject || 'All Subjects'}</span>
                                        <span>•</span>
                                        <span>{item.fileType || 'Document'}</span>
                                    </div>
                                </div>
                            </div>
                            <div className="flex items-center justify-between pt-4 border-t border-white/10">
                                <div className="text-xs text-gray-400">
                                    {new Date(item.createdAt).toLocaleDateString()}
                                </div>
                                <div className="flex items-center gap-2">
                                    <button className="p-2 text-gray-400 hover:text-blue-400 transition-colors">
                                        <FaDownload />
                                    </button>
                                    <button className="p-2 text-gray-400 hover:text-orange-400 transition-colors">
                                        <FaEdit />
                                    </button>
                                    <button
                                        onClick={() => handleDeleteContent(item.id)}
                                        className="p-2 text-gray-400 hover:text-red-400 transition-colors"
                                    >
                                        <FaTrash />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default ContentLibrary;

