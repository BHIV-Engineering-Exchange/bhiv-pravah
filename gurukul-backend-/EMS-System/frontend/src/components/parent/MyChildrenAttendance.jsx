import React, { useState, useEffect } from 'react';
import { parentAPI } from '../../services/api';

const MyChildrenAttendance = () => {
  const [children, setChildren] = useState([]);
  const [selectedChildId, setSelectedChildId] = useState('');
  const [attendanceDate, setAttendanceDate] = useState('');
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchChildren();
  }, []);

  useEffect(() => {
    if (children.length > 0 || selectedChildId === '') {
      fetchAttendance(selectedChildId || null);
    }
  }, [selectedChildId, attendanceDate]);

  const fetchChildren = async () => {
    try {
      const data = await parentAPI.getMyChildren();
      setChildren(data);
      if (data.length > 0) {
        setSelectedChildId(data[0].id.toString());
      } else {
        setLoading(false);
      }
    } catch (err) {
      setError('Failed to load children.');
      console.error('Error fetching children:', err);
      setLoading(false);
    }
  };

  const fetchAttendance = async (childId) => {
    try {
      setLoading(true);
      const childIdInt = childId ? parseInt(childId, 10) : null;
      const dateParam = attendanceDate || null;
      const data = await parentAPI.getMyChildrenAttendance(childIdInt, dateParam);
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

  const getChildName = (studentId) => {
    const child = children.find(c => c.id === studentId);
    return child ? child.name : `Student #${studentId}`;
  };

  if (loading && children.length === 0) {
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
          <h1 className="text-3xl font-bold text-white">Children's Attendance</h1>
          <p className="text-gray-400 mt-2">View attendance records for your children</p>
        </div>
      </div>

      {error && (
        <div className="error-box">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Filters */}
      <div className="card-dark p-4 flex flex-wrap gap-4 items-center">
        {children.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Filter by Child
            </label>
            <select
              value={selectedChildId}
              onChange={(e) => setSelectedChildId(e.target.value)}
              className="px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
            >
              <option value="">All Children</option>
              {children.map((child) => (
                <option key={child.id} value={child.id.toString()}>
                  {child.name} {child.grade ? `(Grade ${child.grade})` : ''}
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
            <p className="text-gray-500 text-lg">No attendance records found for the selected filters.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-[#16162A]">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-white uppercase">Child</th>
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
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                      {getChildName(record.student_id)}
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

export default MyChildrenAttendance;

