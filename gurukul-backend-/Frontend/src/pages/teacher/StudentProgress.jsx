import React, { useState, useEffect } from 'react';
import { FaChartLine, FaUserGraduate, FaSearch, FaEye } from 'react-icons/fa';
import { apiGet, handleApiError } from '../../utils/apiClient';
import { useModal } from '../../contexts/ModalContext';

const StudentProgress = () => {
    const { alert } = useModal();
    const [students, setStudents] = useState([]);
    const [selectedStudent, setSelectedStudent] = useState(null);
    const [progress, setProgress] = useState(null);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        fetchStudents();
    }, []);

    useEffect(() => {
        if (selectedStudent) {
            fetchStudentProgress(selectedStudent.id);
        }
    }, [selectedStudent]);

    const fetchStudents = async () => {
        try {
            setLoading(true);
            // TODO: Replace with actual endpoint
            const data = await apiGet('/api/v1/ems/teacher/students').catch(() => []);
            setStudents(data || []);
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'fetch students' });
            if (!errorInfo.message.includes('404')) {
                await alert(errorInfo.message, errorInfo.title);
            }
        } finally {
            setLoading(false);
        }
    };

    const fetchStudentProgress = async (studentId) => {
        try {
            // TODO: Replace with actual endpoint
            const data = await apiGet(`/api/v1/ems/teacher/students/${studentId}/progress`).catch(() => null);
            setProgress(data);
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'fetch progress' });
            await alert(errorInfo.message, errorInfo.title);
        }
    };

    const filteredStudents = students.filter(student =>
        student.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        student.email?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) {
        return (
            <div className="glass-panel p-8 rounded-2xl border border-white/10 text-center">
                <div className="text-gray-400">Loading...</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div>
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <FaChartLine className="text-orange-400" />
                    Student Progress
                </h3>
                <p className="text-gray-400 text-sm mt-1">Track individual student learning activity and performance</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Students List */}
                <div className="lg:col-span-1 glass-panel p-4 rounded-2xl border border-white/10">
                    <div className="mb-4">
                        <div className="relative">
                            <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                            <input
                                type="text"
                                placeholder="Search students..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-orange-500"
                            />
                        </div>
                    </div>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                        {filteredStudents.map((student) => (
                            <button
                                key={student.id}
                                onClick={() => setSelectedStudent(student)}
                                className={`w-full text-left p-3 rounded-lg transition-colors ${
                                    selectedStudent?.id === student.id
                                        ? 'bg-gradient-to-r from-orange-600 to-amber-600 text-white'
                                        : 'bg-white/5 text-gray-300 hover:bg-white/10'
                                }`}
                            >
                                <div className="flex items-center gap-2">
                                    <FaUserGraduate />
                                    <span className="font-medium">{student.full_name || student.email}</span>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Progress Details */}
                <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-white/10">
                    {selectedStudent ? (
                        progress ? (
                            <div className="space-y-6">
                                <div>
                                    <h4 className="text-lg font-semibold text-white mb-2">
                                        {selectedStudent.full_name || selectedStudent.email}
                                    </h4>
                                    <p className="text-gray-400 text-sm">{selectedStudent.email}</p>
                                </div>

                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    <div className="bg-white/5 p-4 rounded-lg border border-white/10">
                                        <div className="text-2xl font-bold text-orange-400">{progress.topicsStudied || 0}</div>
                                        <div className="text-xs text-gray-400 mt-1">Topics Studied</div>
                                    </div>
                                    <div className="bg-white/5 p-4 rounded-lg border border-white/10">
                                        <div className="text-2xl font-bold text-blue-400">{progress.flashcardsCreated || 0}</div>
                                        <div className="text-xs text-gray-400 mt-1">Flashcards</div>
                                    </div>
                                    <div className="bg-white/5 p-4 rounded-lg border border-white/10">
                                        <div className="text-2xl font-bold text-green-400">{progress.milestonesCompleted || 0}</div>
                                        <div className="text-xs text-gray-400 mt-1">Milestones</div>
                                    </div>
                                    <div className="bg-white/5 p-4 rounded-lg border border-white/10">
                                        <div className="text-2xl font-bold text-purple-400">{progress.lastActivity || 'N/A'}</div>
                                        <div className="text-xs text-gray-400 mt-1">Last Activity</div>
                                    </div>
                                </div>

                                <div className="pt-4 border-t border-white/10">
                                    <p className="text-gray-400 text-sm">More detailed analytics coming soon...</p>
                                </div>
                            </div>
                        ) : (
                            <div className="text-center py-8 text-gray-400">
                                Loading progress data...
                            </div>
                        )
                    ) : (
                        <div className="text-center py-8 text-gray-400">
                            <FaUserGraduate className="mx-auto text-4xl mb-4 opacity-50" />
                            <p>Select a student to view their progress</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default StudentProgress;

