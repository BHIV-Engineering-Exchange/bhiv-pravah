import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import emsApi from '../../services/emsApi';
import { handleApiError } from '../../utils/apiClient';
import Sidebar from '../../components/Sidebar';
import { FaCalendarAlt, FaRedo, FaSpinner, FaClock, FaChalkboardTeacher, FaBook, FaBuilding } from 'react-icons/fa';
import EMSAuthentication from '../../components/EMSAuthentication';

const MySchedule = () => {
    const { user } = useAuth();
    const [slots, setSlots] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [emsToken, setEmsToken] = useState(null);
    const [showAuth, setShowAuth] = useState(false);

    const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

    useEffect(() => {
        const token = localStorage.getItem('ems_token');
        if (token) {
            setEmsToken(token);
            fetchTimetable(token);
        } else {
            setShowAuth(true);
            setLoading(false);
        }
    }, []);

    const handleAuthSuccess = (token) => {
        setEmsToken(token);
        setShowAuth(false);
        fetchTimetable(token);
    };

    const fetchTimetable = async (token) => {
        try {
            setLoading(true);
            setError('');
            const data = await emsApi.getTimetable(token);
            setSlots(data || []);
        } catch (err) {
            const errorInfo = handleApiError(err, { context: 'Loading timetable' });
            setError(errorInfo.message || 'Failed to load timetable');
            console.error('Error fetching timetable:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleRefresh = () => {
        if (emsToken) {
            fetchTimetable(emsToken);
        }
    };

    // Group slots by day
    const groupedSlots = {};
    daysOfWeek.forEach((day, index) => {
        groupedSlots[index] = slots.filter(slot => slot.day_of_week === index);
    });

    if (showAuth) {
        return <EMSAuthentication onSuccess={handleAuthSuccess} onCancel={() => setShowAuth(false)} />;
    }

    if (loading) {
        return (
            <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6 pb-20">
                <Sidebar />
                <div className="flex-grow flex justify-center items-center">
                    <div className="text-center">
                        <FaSpinner className="animate-spin text-4xl text-orange-400 mx-auto mb-4" />
                        <p className="text-gray-300 text-lg">Loading your schedule...</p>
                    </div>
                </div>
            </div>
        );
    }

    if (error && !slots.length) {
        return (
            <div className="flex pt-20 sm:pt-24 min-h-screen container mx-auto px-2 sm:px-4 gap-3 sm:gap-6 pb-20">
                <Sidebar />
                <div className="flex-grow flex justify-center items-start pt-8">
                    <div className="w-full max-w-4xl mx-auto">
                        <div className="glass-panel border border-red-500/30 bg-red-500/10 p-6 rounded-2xl">
                            <p className="text-red-300 text-center mb-4">{error}</p>
                            {emsToken && (
                                <button
                                    onClick={handleRefresh}
                                    className="w-full px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-xl transition-colors font-medium"
                                >
                                    Retry
                                </button>
                            )}
                        </div>
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
                            My Schedule
                        </h2>
                        <p className="text-gray-200 text-xs sm:text-sm font-medium mt-2">
                            View your weekly class timetable
                        </p>
                    </div>
                    {emsToken && (
                        <button
                            onClick={handleRefresh}
                            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-600 to-amber-600 hover:from-orange-500 hover:to-amber-500 text-white rounded-xl font-medium shadow-lg transition-transform hover:-translate-y-1"
                        >
                            <FaRedo className="text-sm" />
                            <span>Refresh</span>
                        </button>
                    )}
                </div>

                {error && (
                    <div className="mb-6 glass-panel border border-red-500/30 bg-red-500/10 p-4 rounded-xl">
                        <p className="text-red-300 text-sm">{error}</p>
                    </div>
                )}

                {slots.length === 0 ? (
                    <div className="glass-panel p-8 sm:p-12 text-center border border-white/10 rounded-2xl">
                        <FaCalendarAlt className="text-6xl text-gray-400 mx-auto mb-4 opacity-50" />
                        <h3 className="text-xl font-semibold text-white mb-2">No Schedule Found</h3>
                        <p className="text-gray-300">No schedule has been assigned yet.</p>
                    </div>
                ) : (
                    <div className="glass-panel border border-white/10 rounded-2xl overflow-hidden bg-black/40">
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-white/5 border-b border-white/10">
                                    <tr>
                                        <th className="px-4 sm:px-6 py-4 text-left text-xs font-bold text-gray-300 uppercase tracking-wider">
                                            Day
                                        </th>
                                        <th className="px-4 sm:px-6 py-4 text-left text-xs font-bold text-gray-300 uppercase tracking-wider">
                                            Time
                                        </th>
                                        <th className="px-4 sm:px-6 py-4 text-left text-xs font-bold text-gray-300 uppercase tracking-wider">
                                            Class
                                        </th>
                                        <th className="px-4 sm:px-6 py-4 text-left text-xs font-bold text-gray-300 uppercase tracking-wider">
                                            Subject
                                        </th>
                                        <th className="px-4 sm:px-6 py-4 text-left text-xs font-bold text-gray-300 uppercase tracking-wider">
                                            Teacher
                                        </th>
                                        <th className="px-4 sm:px-6 py-4 text-left text-xs font-bold text-gray-300 uppercase tracking-wider">
                                            Room
                                        </th>
                                    </tr>
                                </thead>
                                <tbody className="bg-black/20 divide-y divide-white/10">
                                    {daysOfWeek.map((day, dayIndex) => {
                                        const daySlots = groupedSlots[dayIndex] || [];
                                        if (daySlots.length === 0) {
                                            return (
                                                <tr key={dayIndex} className="hover:bg-white/5 transition-colors">
                                                    <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-sm font-medium text-white">
                                                        {day}
                                                    </td>
                                                    <td colSpan="5" className="px-4 sm:px-6 py-4 text-sm text-gray-400">
                                                        No classes scheduled
                                                    </td>
                                                </tr>
                                            );
                                        }
                                        return daySlots.map((slot, slotIndex) => (
                                            <tr key={`${dayIndex}-${slotIndex}`} className="hover:bg-white/5 transition-colors">
                                                {slotIndex === 0 && (
                                                    <td
                                                        rowSpan={daySlots.length}
                                                        className="px-4 sm:px-6 py-4 whitespace-nowrap text-sm font-bold text-white align-top border-r border-white/10"
                                                    >
                                                        {day}
                                                    </td>
                                                )}
                                                <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                                                    <div className="flex items-center gap-2">
                                                        <FaClock className="text-orange-400 text-xs" />
                                                        {slot.start_time} - {slot.end_time}
                                                    </div>
                                                </td>
                                                <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                                                    {slot.class_name || `Class #${slot.class_id}`}
                                                </td>
                                                <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                                                    <div className="flex items-center gap-2">
                                                        <FaBook className="text-orange-400 text-xs" />
                                                        {slot.subject_name || `Subject #${slot.subject_id}`}
                                                    </div>
                                                </td>
                                                <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                                                    <div className="flex items-center gap-2">
                                                        <FaChalkboardTeacher className="text-orange-400 text-xs" />
                                                        {slot.teacher_name || `Teacher #${slot.teacher_id}`}
                                                    </div>
                                                </td>
                                                <td className="px-4 sm:px-6 py-4 whitespace-nowrap text-sm text-gray-300">
                                                    <div className="flex items-center gap-2">
                                                        <FaBuilding className="text-orange-400 text-xs" />
                                                        {slot.room || '-'}
                                                    </div>
                                                </td>
                                            </tr>
                                        ));
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
            </div>
        </div>
    );
};

export default MySchedule;

