import React, { useState, useEffect } from 'react';
import { FaChalkboardTeacher, FaUsers, FaPlus, FaEdit, FaTrash } from 'react-icons/fa';
import { apiGet, apiPost, apiDelete, handleApiError } from '../../utils/apiClient';
import { useModal } from '../../contexts/ModalContext';

const ClassManagement = () => {
    const { alert, confirm } = useModal();
    const [classes, setClasses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showAddModal, setShowAddModal] = useState(false);
    const [formData, setFormData] = useState({ name: '', description: '' });

    useEffect(() => {
        fetchClasses();
    }, []);

    const fetchClasses = async () => {
        try {
            setLoading(true);
            // TODO: Replace with actual endpoint
            const data = await apiGet('/api/v1/ems/teacher/classes').catch(() => []);
            setClasses(data || []);
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'fetch classes' });
            if (!errorInfo.message.includes('404')) {
                await alert(errorInfo.message, errorInfo.title);
            }
        } finally {
            setLoading(false);
        }
    };

    const handleAddClass = async (e) => {
        e.preventDefault();
        try {
            // TODO: Replace with actual endpoint
            await apiPost('/api/v1/ems/teacher/classes', formData);
            await alert('Class created successfully!', 'Success');
            setShowAddModal(false);
            setFormData({ name: '', description: '' });
            fetchClasses();
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'create class' });
            await alert(errorInfo.message, errorInfo.title);
        }
    };

    const handleDeleteClass = async (classId) => {
        const result = await confirm(
            'Are you sure you want to delete this class? This action cannot be undone.',
            'Delete Class'
        );
        if (!result) return;

        try {
            // TODO: Replace with actual endpoint
            await apiDelete(`/api/v1/ems/teacher/classes/${classId}`);
            await alert('Class deleted successfully!', 'Success');
            fetchClasses();
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'delete class' });
            await alert(errorInfo.message, errorInfo.title);
        }
    };

    if (loading) {
        return (
            <div className="glass-panel p-8 rounded-2xl border border-white/10 text-center">
                <div className="text-gray-400">Loading classes...</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        <FaChalkboardTeacher className="text-orange-400" />
                        Class Management
                    </h3>
                    <p className="text-gray-400 text-sm mt-1">Manage your classes and student assignments</p>
                </div>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-600 to-amber-600 text-white font-semibold rounded-lg hover:from-orange-700 hover:to-amber-700 transition-all"
                >
                    <FaPlus />
                    Add Class
                </button>
            </div>

            {/* Classes Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {classes.length === 0 ? (
                    <div className="col-span-full glass-panel p-8 rounded-2xl border border-white/10 text-center text-gray-400">
                        No classes found. Create your first class!
                    </div>
                ) : (
                    classes.map((classItem) => (
                        <div key={classItem.id} className="glass-panel p-6 rounded-2xl border border-white/10 hover:border-orange-500/50 transition-colors">
                            <div className="flex items-start justify-between mb-4">
                                <div>
                                    <h4 className="text-lg font-semibold text-white mb-1">{classItem.name}</h4>
                                    {classItem.description && (
                                        <p className="text-gray-400 text-sm">{classItem.description}</p>
                                    )}
                                </div>
                                <div className="flex items-center gap-2">
                                    <button className="p-2 text-gray-400 hover:text-orange-400 transition-colors">
                                        <FaEdit />
                                    </button>
                                    <button
                                        onClick={() => handleDeleteClass(classItem.id)}
                                        className="p-2 text-gray-400 hover:text-red-400 transition-colors"
                                    >
                                        <FaTrash />
                                    </button>
                                </div>
                            </div>
                            <div className="flex items-center gap-4 text-sm text-gray-400">
                                <div className="flex items-center gap-1">
                                    <FaUsers />
                                    <span>{classItem.student_count || 0} students</span>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Add Class Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
                    <div className="glass-panel p-6 rounded-2xl border border-white/10 max-w-md w-full">
                        <h4 className="text-xl font-bold text-white mb-4">Create New Class</h4>
                        <form onSubmit={handleAddClass} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Class Name <span className="text-red-400">*</span>
                                </label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-orange-500"
                                    placeholder="e.g., Grade 10 Mathematics"
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
                                    placeholder="Optional description..."
                                />
                            </div>
                            <div className="flex gap-3">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setShowAddModal(false);
                                        setFormData({ name: '', description: '' });
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

export default ClassManagement;

