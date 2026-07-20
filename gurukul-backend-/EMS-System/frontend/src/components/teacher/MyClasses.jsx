import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { teacherAPI } from '../../services/api';

const MyClasses = () => {
  const navigate = useNavigate();
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchClasses();
  }, []);

  const fetchClasses = async () => {
    try {
      setLoading(true);
      const data = await teacherAPI.getMyClasses();
      setClasses(data);
      setError('');
    } catch (err) {
      setError('Failed to load classes. Please try again.');
      console.error('Error fetching classes:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading classes...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">My Classes</h2>
        <button
          onClick={fetchClasses}
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

      {classes.length === 0 ? (
        <div className="card-dark overflow-hidden p-8 text-center">
          <p className="text-gray-400">No classes assigned yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {classes.map((classItem) => (
            <div
              key={classItem.id}
              className="card-dark p-6 hover:shadow-lg transition cursor-pointer"
              onClick={() => navigate(`/dashboard/classes/${classItem.id}/students`)}
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-white">{classItem.name}</h3>
                  <p className="text-sm text-gray-400 mt-1">{classItem.subject_name || 'No Subject'}</p>
                </div>
                <span className="px-3 py-1 bg-indigo-100 text-indigo-800 rounded-full text-sm font-medium">
                  Grade {classItem.grade}
                </span>
              </div>
              <div className="space-y-2 text-sm text-gray-400">
                <p><span className="font-medium">Academic Year:</span> {classItem.academic_year || 'N/A'}</p>
                <p><span className="font-medium">Subject:</span> {classItem.subject_name || 'N/A'}</p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/dashboard/classes/${classItem.id}/students`);
                }}
                className="mt-4 w-full px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition text-sm font-medium"
              >
                View Students
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default MyClasses;

