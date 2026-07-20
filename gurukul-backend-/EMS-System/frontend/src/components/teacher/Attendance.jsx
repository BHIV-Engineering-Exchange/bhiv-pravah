import React, { useState, useEffect } from 'react';
import { teacherAPI } from '../../services/api';

const Attendance = () => {
  const [classes, setClasses] = useState([]);
  const [selectedClass, setSelectedClass] = useState(null);
  const [students, setStudents] = useState([]);
  const [attendanceRecords, setAttendanceRecords] = useState({}); // {studentId: status}
  const [attendanceDate, setAttendanceDate] = useState(new Date().toISOString().split('T')[0]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchClasses();
  }, []);

  useEffect(() => {
    if (selectedClass) {
      fetchStudents(selectedClass);
      fetchAttendance(selectedClass);
    }
  }, [selectedClass, attendanceDate]);

  const fetchClasses = async () => {
    try {
      const data = await teacherAPI.getMyClasses();
      setClasses(data);
      if (data.length > 0) {
        setSelectedClass(data[0].id);
      }
    } catch (err) {
      setError('Failed to load classes.');
      console.error('Error fetching classes:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchStudents = async (classId) => {
    try {
      setLoading(true);
      const data = await teacherAPI.getClassStudents(classId);
      setStudents(data);
      setError('');
    } catch (err) {
      setError('Failed to load students. Please try again.');
      console.error('Error fetching students:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAttendance = async (classId) => {
    try {
      const data = await teacherAPI.getAttendance(classId, attendanceDate);
      // Convert array to object for easy lookup
      const records = {};
      data.forEach(record => {
        records[record.student_id] = record.status;
      });
      setAttendanceRecords(records);
    } catch (err) {
      // If no attendance found, that's okay - start with empty records
      setAttendanceRecords({});
    }
  };

  const handleStatusChange = (studentId, status) => {
    setAttendanceRecords(prev => ({
      ...prev,
      [studentId]: status
    }));
  };

  const handleMarkAttendance = async () => {
    if (!selectedClass) {
      setError('Please select a class');
      return;
    }

    if (students.length === 0) {
      setError('No students to mark attendance for');
      return;
    }

    setSaving(true);
    setError('');
    setMessage('');

    try {
      // Prepare attendance records
      const attendance_records = students.map(student => {
        const record = {
          student_id: student.id,
          status: attendanceRecords[student.id] || 'PRESENT' // Default to PRESENT if not set
        };
        // Only include remarks if it's not null/empty
        if (attendanceRecords[student.id + '_remarks']) {
          record.remarks = attendanceRecords[student.id + '_remarks'];
        }
        return record;
      });

      const payload = {
        class_id: selectedClass,
        attendance_date: attendanceDate,
        attendance_records: attendance_records
      };

      await teacherAPI.markAttendance(payload);
      setMessage('Attendance marked successfully!');
      
      // Refresh attendance data
      setTimeout(() => {
        fetchAttendance(selectedClass);
      }, 1000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to mark attendance. Please try again.');
      console.error('Error marking attendance:', err);
    } finally {
      setSaving(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      'PRESENT': 'bg-green-100 text-accent-green',
      'ABSENT': 'bg-red-100 text-red-400',
      'LATE': 'bg-accent-amber/15 text-accent-amber',
      'EXCUSED': 'bg-accent-blue/15 text-accent-blue',
      'PENDING': 'bg-[#16162A] text-white'
    };
    return colors[status] || colors['PENDING'];
  };

  if (loading && classes.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">Mark Attendance</h2>
      </div>

      {error && (
        <div className="error-box">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {message && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-blue-800">{message}</p>
        </div>
      )}

      {/* Class and Date Selector */}
      {classes.length > 0 && (
        <div className="card-dark p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
                Select Class
              </label>
              <select
                value={selectedClass || ''}
                onChange={(e) => setSelectedClass(parseInt(e.target.value))}
                className="w-full input-dark !py-2"
              >
                {classes.map((cls) => (
                  <option key={cls.id} value={cls.id}>
                    {cls.name} - {cls.subject_name}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
                Attendance Date
              </label>
              <input
                type="date"
                value={attendanceDate}
                onChange={(e) => setAttendanceDate(e.target.value)}
                className="w-full input-dark !py-2"
              />
            </div>
          </div>
        </div>
      )}

      {!selectedClass ? (
        <div className="card-dark overflow-hidden p-8 text-center">
          <p className="text-gray-400">No classes available. Please contact your administrator.</p>
        </div>
      ) : students.length === 0 ? (
        <div className="card-dark overflow-hidden p-8 text-center">
          <p className="text-gray-400">No students enrolled in this class yet.</p>
        </div>
      ) : (
        <div className="card-dark overflow-hidden overflow-hidden">
          <div className="p-4 border-b border-[#2A2A3E] flex justify-between items-center">
            <h3 className="text-lg font-semibold text-white">
              Students in {classes.find(c => c.id === selectedClass)?.name}
            </h3>
            <button
              onClick={handleMarkAttendance}
              disabled={saving}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : 'Mark Attendance'}
            </button>
          </div>
          <table className="min-w-full divide-y divide-[#2A2A3E]">
            <thead className="bg-[#16162A]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Grade
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Attendance Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-[#2A2A3E]">
              {students.map((student) => (
                <tr key={student.id} className="hover:bg-[#16162A]">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-white">{student.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500">{student.email}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-indigo-100 text-indigo-800">
                      {student.grade || 'N/A'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <select
                      value={attendanceRecords[student.id] || 'PRESENT'}
                      onChange={(e) => handleStatusChange(student.id, e.target.value)}
                      className={`px-3 py-1 text-xs font-semibold rounded-full border-0 focus:ring-2 focus:ring-accent-green ${getStatusColor(attendanceRecords[student.id] || 'PRESENT')}`}
                    >
                      <option value="PRESENT">Present</option>
                      <option value="ABSENT">Absent</option>
                      <option value="LATE">Late</option>
                      <option value="EXCUSED">Excused</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default Attendance;

