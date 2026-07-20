import React, { useState, useEffect } from 'react';
import { studentAPI } from '../../services/api';

const MySchedule = () => {
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

  useEffect(() => {
    fetchTimetable();
  }, []);

  const fetchTimetable = async () => {
    try {
      setLoading(true);
      const data = await studentAPI.getMyTimetable();
      setSlots(data);
      setError('');
    } catch (err) {
      setError('Failed to load schedule. Please try again.');
      console.error('Error fetching timetable:', err);
    } finally {
      setLoading(false);
    }
  };

  // Group slots by day
  const groupedSlots = {};
  daysOfWeek.forEach((day, index) => {
    groupedSlots[index] = slots.filter(slot => slot.day_of_week === index);
  });

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading schedule...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">My Schedule</h1>
          <p className="text-gray-400 mt-2">View your weekly class timetable</p>
        </div>
        <button
          onClick={fetchTimetable}
          className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition text-sm font-medium"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="error-box">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {slots.length === 0 ? (
        <div className="card-dark p-8 text-center">
          <p className="text-gray-400">No schedule assigned yet.</p>
        </div>
      ) : (
        <div className="card-dark overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-[#16162A]">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">Day</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">Time</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">Class</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">Subject</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">Teacher</th>
                  <th className="px-6 py-4 text-left text-xs font-medium text-gray-400 uppercase">Room</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-[#2A2A3E]">
                {daysOfWeek.map((day, dayIndex) => {
                  const daySlots = groupedSlots[dayIndex] || [];
                  if (daySlots.length === 0) {
                    return (
                      <tr key={dayIndex} className="hover:bg-[#16162A]">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{day}</td>
                        <td colSpan="5" className="px-6 py-4 text-sm text-gray-500">No classes scheduled</td>
                      </tr>
                    );
                  }
                  return daySlots.map((slot, slotIndex) => (
                    <tr key={`${dayIndex}-${slotIndex}`} className="hover:bg-[#16162A]">
                      {slotIndex === 0 && (
                        <td
                          rowSpan={daySlots.length}
                          className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white align-top"
                        >
                          {day}
                        </td>
                      )}
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {slot.start_time} - {slot.end_time}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {slot.class_name || `Class #${slot.class_id}`}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {slot.subject_name || `Subject #${slot.subject_id}`}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {slot.teacher_name || `Teacher #${slot.teacher_id}`}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {slot.room || '-'}
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
  );
};

export default MySchedule;

