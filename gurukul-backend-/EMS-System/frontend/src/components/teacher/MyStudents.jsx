import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { teacherAPI } from '../../services/api';
import { useParams } from 'react-router-dom';

const MyStudents = () => {
  const { classId } = useParams();
  const [students, setStudents] = useState([]);
  const [classes, setClasses] = useState([]);
  const [selectedClass, setSelectedClass] = useState(classId ? parseInt(classId) : null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchClasses();
  }, []);

  useEffect(() => {
    if (selectedClass) {
      fetchStudents(selectedClass);
    } else if (classes.length > 0) {
      setSelectedClass(classes[0].id);
      fetchStudents(classes[0].id);
    }
  }, [selectedClass, classes]);

  const fetchClasses = async () => {
    try {
      const data = await teacherAPI.getMyClasses();
      setClasses(data);
      if (data.length > 0 && !selectedClass) {
        setSelectedClass(data[0].id);
      }
    } catch (err) {
      setError('Failed to load classes.');
      console.error('Error fetching classes:', err);
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

  if (loading && students.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading students...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">My Students</h2>
        {selectedClass && (
          <button
            onClick={() => fetchStudents(selectedClass)}
            className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition text-sm font-medium"
          >
            Refresh
          </button>
        )}
      </div>

      {/* Class Selector */}
      {classes.length > 0 && (
        <div className="card-dark p-4">
          <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">
            Select Class
          </label>
          <select
            value={selectedClass || ''}
            onChange={(e) => setSelectedClass(parseInt(e.target.value))}
            className="w-full md:w-64 input-dark !py-2"
          >
            {classes.map((cls) => (
              <option key={cls.id} value={cls.id}>
                {cls.name} - {cls.subject_name}
              </option>
            ))}
          </select>
        </div>
      )}

      {error && (
        <div className="error-box">
          <p className="text-red-400">{error}</p>
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
                  Actions
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
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <Link
                      to={`/dashboard/students/${student.id}/content`}
                      className="text-accent-green hover:text-accent-green/80 font-medium"
                    >
                      📚 View Content
                    </Link>
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

export default MyStudents;

