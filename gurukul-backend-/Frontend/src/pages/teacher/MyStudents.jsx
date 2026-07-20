import React, { useState, useEffect } from 'react';
import { FaUserGraduate, FaSearch, FaFilter, FaEye, FaEnvelope } from 'react-icons/fa';
import { apiGet, handleApiError } from '../../utils/apiClient';
import { useModal } from '../../contexts/ModalContext';

const MyStudents = () => {
    const { alert } = useModal();
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterRole, setFilterRole] = useState('all');

    useEffect(() => {
        fetchStudents();
    }, []);

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

    const filteredStudents = students.filter(student => {
        const matchesSearch = student.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                             student.email?.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesFilter = filterRole === 'all' || student.role === filterRole;
        return matchesSearch && matchesFilter;
    });

    if (loading) {
        return (
            <div className="glass-panel p-8 rounded-2xl border border-white/10 text-center">
                <div className="text-gray-400">Loading students...</div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        <FaUserGraduate className="text-orange-400" />
                        My Students
                    </h3>
                    <p className="text-gray-400 text-sm mt-1">View and manage your assigned students</p>
                </div>
                <div className="text-sm text-gray-400">
                    Total: <span className="text-white font-semibold">{filteredStudents.length}</span>
                </div>
            </div>

            {/* Search and Filter */}
            <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1 relative">
                    <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search by name or email..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-orange-500"
                    />
                </div>
                <div className="relative">
                    <FaFilter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <select
                        value={filterRole}
                        onChange={(e) => setFilterRole(e.target.value)}
                        className="pl-10 pr-8 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-orange-500 appearance-none"
                    >
                        <option value="all">All Roles</option>
                        <option value="STUDENT">Students</option>
                    </select>
                </div>
            </div>

            {/* Students Table */}
            <div className="glass-panel rounded-2xl border border-white/10 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-white/5 border-b border-white/10">
                            <tr>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Name</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Email</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Class</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Status</th>
                                <th className="px-4 py-3 text-left text-xs font-semibold text-gray-400 uppercase tracking-wider">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {filteredStudents.length === 0 ? (
                                <tr>
                                    <td colSpan="5" className="px-4 py-8 text-center text-gray-400">
                                        No students found
                                    </td>
                                </tr>
                            ) : (
                                filteredStudents.map((student) => (
                                    <tr key={student.id} className="hover:bg-white/5 transition-colors">
                                        <td className="px-4 py-3 text-white font-medium">{student.full_name || 'N/A'}</td>
                                        <td className="px-4 py-3 text-gray-300 text-sm">{student.email}</td>
                                        <td className="px-4 py-3 text-gray-300 text-sm">{student.cohort_id || 'N/A'}</td>
                                        <td className="px-4 py-3">
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                                student.is_active 
                                                    ? 'bg-green-500/20 text-green-400' 
                                                    : 'bg-red-500/20 text-red-400'
                                            }`}>
                                                {student.is_active ? 'Active' : 'Inactive'}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3">
                                            <div className="flex items-center gap-2">
                                                <button className="p-2 text-gray-400 hover:text-orange-400 transition-colors">
                                                    <FaEye />
                                                </button>
                                                <button className="p-2 text-gray-400 hover:text-blue-400 transition-colors">
                                                    <FaEnvelope />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default MyStudents;

