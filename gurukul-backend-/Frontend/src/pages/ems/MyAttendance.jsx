import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import emsApi from '../../services/emsApi';
import { handleApiError } from '../../utils/apiClient';
import Sidebar from '../../components/Sidebar';
import { FaCheckCircle, FaTimesCircle, FaClock, FaSpinner, FaRedo, FaCalendarAlt } from 'react-icons/fa';
import EMSAuthentication from '../../components/EMSAuthentication';

const MyAttendance = () => {
    const { user } = useAuth();
    const [classes, setClasses] = useState([]);
    const [selectedClassId, setSelectedClassId] = useState('');
    const [attendanceDate, setAttendanceDate] = useState('');
    const [attendance, setAttendance] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [emsToken, setEmsToken] = useState(null);
    const [showAuth, setShowAuth] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem('ems_token');
        if (token) {
            setEmsToken(token);
            fetchClasses(token);
        } else {
            setShowAuth(true);
            setLoading(false);
        }
    }, []);

    const handleAuthSuccess = (token) => {
        setEmsToken(token);
        setShowAuth(false);
        fetchClasses(token);
    };

    useEffect(() => {
        if (emsToken && (classes.length > 0 || selectedClassId === '')) {
            fetchAttendance(selectedClassId || null);
        }
    }, [selectedClassId, attendanceDate, emsToken]);

    const fetchClasses = async (token) => {
        try {
            const data = await emsApi.getClasses(token);
            setClasses(data || []);
            if (data && data.length > 0) {
                setSelectedClassId(data[0].id.toString());
            } else {
                setLoading(false);
            }
        } catch (err) {
            setError('Failed to load classes.');
            console.error('Error fetching classes:', err);
            setLoading(false);
        }
    };

    const fetchAttendance = async (classId) => {
        try {
            setLoading(true);
            const classIdInt = classId ? parseInt(classId, 10) : null;
            const dateParam = attendanceDate || null;
            const data = await emsApi.getAttendance(emsToken, classIdInt, dateParam);
            setAttendance(data || []);
            setError('');
        } catch (err) {
            const errorInfo = handleApiError(err, { context: 'Loading attendance' });
            setError(errorInfo.message || 'Failed to load attendance');
            console.error('Error fetching attendance:', err);
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status) => {
        switch (status?.toUpperCase()) {
            case 'PRESENT':
                return 'bg-green-500/20 text-green-300 border-green-500/30';
            case 'ABSENT':
                return 'bg-red-500/20 text-red-300 border-red-500/30';
            case 'LATE':
                return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
            case 'EXCUSED':
                return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
            default:
                return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
        }
    };

    const getStatusIcon = (status) => {
        switch (status?.toUpperCase()) {
            case 'PRESENT':
                return <FaCheckCircle className="text-green-400" />;
            case 'ABSENT':
                return <FaTimesCircle className="text-red-400" />;
            case 'LATE':
                return <FaClock className="text-yellow-400" />;
            default:
                return <FaCalendarAlt className="text-gray-400" />;
        }
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    if (showAuth) {
        return <EMSAuthentication onSuccess={handleAuthSuccess} onCancel={() => setShowAuth(false)} />;
    }

    if (loading && attendance.length === 0 && classes.length === 0) {
        return (
            <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6 pb-20">
                <Sidebar />
                <div className="flex-grow flex justify-center items-center">
                    <div className="text-center">
                        <FaSpinner className="animate-spin text-4xl text-orange-400 mx-auto mb-4" />
                        <p className="text-gray-300 text-lg">Loading attendance...</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6 pb-20">
            <Sidebar />
            <div className="flex-grow">
            <div className="w-full max-w-7xl mx-auto">
                <div className="mb-6 sm:mb-8 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div>
                        <h2 className="text-2xl sm:text-3xl font-bold font-heading text-white flex items-center gap-3">
                            <FaCalendarAlt className="text-orange-400" />
                            My Attendance
                        </h2>
                        <p className="text-gray-200 text-xs sm:text-sm font-medium mt-2">
                            View your attendance records
                        </p>
                    </div>
                </div>

                {error && (
                    <div className="mb-6 glass-panel border border-red-500/30 bg-red-500/10 p-4 rounded-xl">
                        <p className="text-red-300 text-sm">{error}</p>
                    </div>
                )}

                {/* Filters */}
                <div className="glass-panel p-4 border border-white/10 rounded-2xl mb-6 flex flex-wrap gap-4 items-end bg-black/40">
                    {classes.length > 0 && (
                        <div className="flex-1 min-w-[200px]">
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Filter by Class
                            </label>
                            <select
                                value={selectedClassId}
                                onChange={(e) => setSelectedClassId(e.target.value)}
                                className="w-full px-4 py-2 bg-black/60 border border-white/20 rounded-xl text-white focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition"
                            >
                                <option value="">All Classes</option>
                                {classes.map((cls) => (
                                    <option key={cls.id} value={cls.id.toString()} className="bg-black text-white">
                                        {cls.name} {cls.subject_name ? `(${cls.subject_name})` : ''}
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}
                    <div className="flex-1 min-w-[200px]">
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            Date (Leave empty for all records)
                        </label>
                        <div className="flex gap-2">
                            <input
                                type="date"
                                value={attendanceDate}
                                onChange={(e) => setAttendanceDate(e.target.value)}
                                className="flex-1 px-4 py-2 bg-black/60 border border-white/20 rounded-xl text-white focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition"
                            />
                            <button
                                onClick={() => setAttendanceDate('')}
                                className="px-4 py-2 bg-gray-600/60 hover:bg-gray-600/80 text-white rounded-xl transition text-sm font-medium"
                            >
                                Clear
                            </button>
                        </div>
                    </div>
                </div>

                {/* Attendance List */}
                <div className="glass-panel border border-white/10 rounded-2xl overflow-hidden bg-black/40">
                    <div className="px-4 sm:px-6 py-4 border-b border-white/10 bg-white/5">
                        <h3 className="text-xl font-bold text-white">
                            Attendance Records ({attendance.length})
                        </h3>
                    </div>
                    {loading ? (
                        <div className="p-12 text-center">
                            <FaSpinner className="animate-spin text-3xl text-orange-400 mx-auto mb-4" />
                            <p className="text-gray-300">Loading attendance records...</p>
                        </div>
                    ) : attendance.length === 0 ? (
                        <div className="px-6 py-12 text-center">
                            <FaCalendarAlt className="text-5xl text-gray-400 mx-auto mb-4 opacity-50" />
                            <p className="text-gray-300 text-lg">No attendance records found for the selected filters.</p>
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-white/5 border-b border-white/10">
                                    <tr>
                                        <th className="px-4 sm:px-6 py-3 text-left text-xs font-bold text-gray-300 uppercase tracking-wider">
                                            Date
                                        </th>
                                        <th className="px-4 sm:px-6 py-3 text-left text-xs font-bold text-gray-300 uppercase tracking-wider">
                                            Class
                                        </th>
                                        <th className="px-4 sm:px-6 py-3 text-left text-xs font-bold text-gray-300 uppercase tracking-wider">
                                            Status
                                        </th>
                                        <th className="px-4 sm:px-6 py-3 text-left text-xs font-bold text-gray-300 uppercase tracking-wider">
                                            Remarks
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="bg-black/20 divide-y divide-white/10">
                                    {attendance.map((record) => (
                                        <tr key={record.id} className="hover:bg-white/5 transition-colors">
                                            <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-sm text-white">
                                                {formatDate(record.attendance_date)}
                                            </td>
                                            <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                                                {record.class_name || `Class #${record.class_id}`}
                                            </td>
                                            <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-sm">
                                                <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(record.status)}`}>
                                                    {getStatusIcon(record.status)}
                                                    {record.status}
                                                </span>
                                            </td>
                                            <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                                                {record.remarks || '-'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
            </div>
        </div>
    );
};

export default MyAttendance;

