import React, { useState, useEffect } from 'react';
import { studentAPI } from '../../services/api';

const MyAttendance = () => {
  const [classes, setClasses] = useState([]);
  const [selectedClassId, setSelectedClassId] = useState('');
  const [attendanceDate, setAttendanceDate] = useState(''); // Empty by default to show all records
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchClasses();
  }, []);

  useEffect(() => {
    if (classes.length > 0 || selectedClassId === '') {
      fetchAttendance(selectedClassId || null);
    }
  }, [selectedClassId, attendanceDate]);

  const fetchClasses = async () => {
    try {
      const data = await studentAPI.getMyClasses();
      setClasses(data);
      if (data.length > 0) {
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
      const data = await studentAPI.getMyAttendance(classIdInt, dateParam);
      setAttendance(data || []);
      setError('');
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load attendance. Please try again.';
      setError(errorMessage);
      console.error('Error fetching attendance:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status?.toUpperCase()) {
      case 'PRESENT':
        return 'bg-green-100 text-accent-green';
      case 'ABSENT':
        return 'bg-red-100 text-red-400';
      case 'LATE':
        return 'bg-accent-amber/15 text-accent-amber';
      case 'EXCUSED':
        return 'bg-accent-blue/15 text-accent-blue';
      default:
        return 'bg-[#16162A] text-white';
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

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading attendance...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">My Attendance</h1>
          <p className="text-gray-400 mt-2">View your attendance records</p>
        </div>
      </div>

      {error && (
        <div className="error-box">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Filters */}
      <div className="card-dark p-4 flex flex-wrap gap-4 items-center">
        {classes.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Filter by Class
            </label>
            <select
              value={selectedClassId}
              onChange={(e) => setSelectedClassId(e.target.value)}
              className="px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
            >
              <option value="">All Classes</option>
              {classes.map((cls) => (
                <option key={cls.id} value={cls.id.toString()}>
                  {cls.name} {cls.subject_name ? `(${cls.subject_name})` : ''}
                </option>
              ))}
            </select>
          </div>
        )}
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Date (Leave empty for all records)
          </label>
          <input
            type="date"
            value={attendanceDate}
            onChange={(e) => setAttendanceDate(e.target.value)}
            className="px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
          />
          <button
            onClick={() => setAttendanceDate('')}
            className="ml-2 px-3 py-2 text-sm bg-gray-200 text-gray-300 rounded-lg hover:bg-gray-300 transition"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Attendance List */}
      <div className="card-dark overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2A2A3E] bg-[#16162A]">
          <h2 className="text-xl font-bold text-white">
            Attendance Records ({attendance.length})
          </h2>
        </div>
        {attendance.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <p className="text-gray-500 text-lg">No attendance records found for the selected date.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-[#16162A]">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase">Class</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase">Remarks</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-[#2A2A3E]">
                {attendance.map((record) => (
                  <tr key={record.id} className="hover:bg-[#16162A]">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                      {formatDate(record.attendance_date)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {record.class_name || `Class #${record.class_id}`}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(record.status)}`}>
                        {record.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
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
  );
};

export default MyAttendance;

