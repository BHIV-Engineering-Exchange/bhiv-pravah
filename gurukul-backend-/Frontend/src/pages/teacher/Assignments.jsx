import React, { useState, useEffect } from 'react';
import { FaClipboardList, FaPlus, FaEdit, FaTrash, FaCheckCircle, FaClock } from 'react-icons/fa';
import { apiGet, apiPost, apiPut, apiDelete, handleApiError } from '../../utils/apiClient';
import { useModal } from '../../contexts/ModalContext';

const Assignments = () => {
    const { alert, confirm } = useModal();
    const [assignments, setAssignments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showAddModal, setShowAddModal] = useState(false);
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        subject: '',
        dueDate: '',
        maxScore: 100
    });

    useEffect(() => {
        fetchAssignments();
    }, []);

    const fetchAssignments = async () => {
        try {
            setLoading(true);
            // TODO: Replace with actual endpoint
            const data = await apiGet('/api/v1/ems/teacher/assignments').catch(() => []);
            setAssignments(data || []);
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'fetch assignments' });
            if (!errorInfo.message.includes('404')) {
                await alert(errorInfo.message, errorInfo.title);
            }
        } finally {
            setLoading(false);
        }
    };

    const handleAddAssignment = async (e) => {
        e.preventDefault();
        try {
            // TODO: Replace with actual endpoint
            await apiPost('/api/v1/ems/teacher/assignments', formData);
            await alert('Assignment created successfully!', 'Success');
            setShowAddModal(false);
            setFormData({ title: '', description: '', subject: '', dueDate: '', maxScore: 100 });
            fetchAssignments();
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'create assignment' });
            await alert(errorInfo.message, errorInfo.title);
        }
    };

    const handleDeleteAssignment = async (assignmentId) => {
        const result = await confirm(
            'Are you sure you want to delete this assignment? This action cannot be undone.',
            'Delete Assignment'
        );
        if (!result) return;

        try {
            // TODO: Replace with actual endpoint
            await apiDelete(`/api/v1/ems/teacher/assignments/${assignmentId}`);
            await alert('Assignment deleted successfully!', 'Success');
            fetchAssignments();
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'delete assignment' });
            await alert(errorInfo.message, errorInfo.title);
        }
    };

    if (loading) {
        return (
            <div className="glass-panel p-8 rounded-2xl border border-white/10 text-center">
                <div className="text-gray-400">Loading assignments...</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        <FaClipboardList className="text-orange-400" />
                        Assignments & Tasks
                    </h3>
                    <p className="text-gray-400 text-sm mt-1">Create and manage assignments for your students</p>
                </div>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-600 to-amber-600 text-white font-semibold rounded-lg hover:from-orange-700 hover:to-amber-700 transition-all"
                >
                    <FaPlus />
                    Create Assignment
                </button>
            </div>

            {/* Assignments List */}
            <div className="space-y-4">
                {assignments.length === 0 ? (
                    <div className="glass-panel p-8 rounded-2xl border border-white/10 text-center text-gray-400">
                        No assignments found. Create your first assignment!
                    </div>
                ) : (
                    assignments.map((assignment) => (
                        <div key={assignment.id} className="glass-panel p-6 rounded-2xl border border-white/10 hover:border-orange-500/50 transition-colors">
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex-1">
                                    <h4 className="text-lg font-semibold text-white mb-2">{assignment.title}</h4>
                                    {assignment.description && (
                                        <p className="text-gray-400 text-sm mb-2">{assignment.description}</p>
                                    )}
                                    <div className="flex items-center gap-4 text-sm text-gray-400">
                                        <span>{assignment.subject || 'All Subjects'}</span>
                                        {assignment.dueDate && (
                                            <span className="flex items-center gap-1">
                                                <FaClock />
                                                Due: {new Date(assignment.dueDate).toLocaleDateString()}
                                            </span>
                                        )}
                                        <span>Max Score: {assignment.maxScore || 100}</span>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <button className="p-2 text-gray-400 hover:text-orange-400 transition-colors">
                                        <FaEdit />
                                    </button>
                                    <button
                                        onClick={() => handleDeleteAssignment(assignment.id)}
                                        className="p-2 text-gray-400 hover:text-red-400 transition-colors"
                                    >
                                        <FaTrash />
                                    </button>
                                </div>
                            </div>
                            <div className="flex items-center gap-4 text-sm">
                                <div className="flex items-center gap-1 text-gray-400">
                                    <FaCheckCircle />
                                    <span>{assignment.submissions || 0} submissions</span>
                                </div>
                                <div className="flex items-center gap-1 text-gray-400">
                                    <FaClock />
                                    <span>{assignment.pending || 0} pending</span>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Add Assignment Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
                    <div className="glass-panel p-6 rounded-2xl border border-white/10 max-w-md w-full">
                        <h4 className="text-xl font-bold text-white mb-4">Create New Assignment</h4>
                        <form onSubmit={handleAddAssignment} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Title <span className="text-red-400">*</span>
                                </label>
                                <input
                                    type="text"
                                    value={formData.title}
                                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-orange-500"
                                    placeholder="Assignment title"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Description
                                </label>
                                <textarea
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-orange-500"
                                    rows="3"
                                    placeholder="Assignment description..."
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Subject
                                    </label>
                                    <select
                                        value={formData.subject}
                                        onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                                        className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-orange-500"
                                    >
                                        <option value="">All Subjects</option>
                                        <option value="Mathematics">Mathematics</option>
                                        <option value="Physics">Physics</option>
                                        <option value="Chemistry">Chemistry</option>
                                        <option value="Biology">Biology</option>
                                        <option value="Computer Science">Computer Science</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Max Score
                                    </label>
                                    <input
                                        type="number"
                                        value={formData.maxScore}
                                        onChange={(e) => setFormData({ ...formData, maxScore: parseInt(e.target.value) })}
                                        className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-orange-500"
                                        min="1"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Due Date
                                </label>
                                <input
                                    type="datetime-local"
                                    value={formData.dueDate}
                                    onChange={(e) => setFormData({ ...formData, dueDate: e.target.value })}
                                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-orange-500"
                                />
                            </div>
                            <div className="flex gap-3">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setShowAddModal(false);
                                        setFormData({ title: '', description: '', subject: '', dueDate: '', maxScore: 100 });
                                    }}
                                    className="flex-1 py-2 bg-white/5 text-white font-semibold rounded-lg hover:bg-white/10 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 py-2 bg-gradient-to-r from-orange-600 to-amber-600 text-white font-semibold rounded-lg hover:from-orange-700 hover:to-amber-700 transition-all"
                                >
                                    Create
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Assignments;

