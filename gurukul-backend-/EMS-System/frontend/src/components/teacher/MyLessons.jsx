import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { teacherAPI } from '../../services/api';

const MyLessons = () => {
  const navigate = useNavigate();
  const [classes, setClasses] = useState([]);
  const [lessons, setLessons] = useState([]);
  const [selectedClassId, setSelectedClassId] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deletingLessonId, setDeletingLessonId] = useState(null);

  useEffect(() => {
    fetchClasses();
  }, []);

  useEffect(() => {
    if (selectedClassId) {
      fetchLessons(parseInt(selectedClassId));
    }
  }, [selectedClassId]);

  const fetchClasses = async () => {
    try {
      setLoading(true);
      const data = await teacherAPI.getMyClasses();
      setClasses(data);
      if (data.length > 0) {
        setSelectedClassId(data[0].id.toString());
        fetchLessons(data[0].id);
      } else {
        setLoading(false);
      }
      setError('');
    } catch (err) {
      setError('Failed to load classes. Please try again.');
      console.error('Error fetching classes:', err);
      setLoading(false);
    }
  };

  const fetchLessons = async (classId) => {
    try {
      setLoading(true);
      const data = await teacherAPI.getMyLessons(classId);
      setLessons(data);
      setError('');
    } catch (err) {
      setError('Failed to load lessons. Please try again.');
      console.error('Error fetching lessons:', err);
    } finally {
      setLoading(false);
    }
  };

  const getClassName = (classId) => {
    const cls = classes.find((c) => c.id === classId);
    return cls ? cls.name : classId;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  const handleEditLesson = (lesson) => {
    // Set lesson_id in sessionStorage for PRANA before navigation
    sessionStorage.setItem('current_lesson_id', lesson.id.toString());
    // Also update window context if it exists
    if (window.EMSUserContext) {
      window.EMSUserContext.currentLessonId = lesson.id.toString();
    }
    navigate(`/dashboard/lessons/edit/${lesson.id}`, { state: { lesson } });
  };

  const handleDeleteLesson = async (lessonId) => {
    if (!window.confirm('Are you sure you want to delete this lesson? This action cannot be undone.')) {
      return;
    }
    
    try {
      setDeletingLessonId(lessonId);
      await teacherAPI.deleteLesson(lessonId);
      // Refresh lessons
      if (selectedClassId) {
        fetchLessons(parseInt(selectedClassId));
      } else {
        // Fetch all lessons
        const allLessons = await teacherAPI.getMyLessons();
        setLessons(allLessons);
      }
      alert('Lesson deleted successfully!');
    } catch (err) {
      console.error('Error deleting lesson:', err);
      alert(err.response?.data?.detail || 'Failed to delete lesson');
    } finally {
      setDeletingLessonId(null);
    }
  };

  if (loading && lessons.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading lessons...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">My Lessons</h1>
          <p className="text-gray-400 mt-2">View and manage your lessons</p>
        </div>
        <button
          onClick={() => navigate('/dashboard/lessons/create')}
          className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition text-sm font-medium flex items-center gap-2"
        >
          <span>➕</span>
          <span>Create Lesson</span>
        </button>
      </div>

      {error && (
        <div className="error-box">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Class Filter */}
      {classes.length > 0 && (
        <div className="card-dark p-4 flex flex-wrap gap-4 items-center">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Filter by Class
            </label>
            <select
              value={selectedClassId}
              onChange={(e) => setSelectedClassId(e.target.value)}
              className="px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green focus:border-accent-green"
            >
              <option value="">All Classes</option>
              {classes.map((cls) => (
                <option key={cls.id} value={cls.id}>
                  {cls.name} {cls.subject_name ? `(${cls.subject_name})` : ''}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Lessons List */}
      <div className="card-dark overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2A2A3E] bg-[#16162A]">
          <h2 className="text-xl font-bold text-white">
            Lessons ({lessons.length}) 
            {selectedClassId && ` - ${getClassName(parseInt(selectedClassId))}`}
          </h2>
        </div>
        
        {lessons.length === 0 ? (
          <div className="px-6 py-12 text-center">
            <p className="text-gray-500 text-lg mb-4">No lessons found</p>
            <button
              onClick={() => navigate('/dashboard/lessons/create')}
              className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition text-sm font-medium"
            >
              Create Your First Lesson
            </button>
          </div>
        ) : (
          <div className="divide-y divide-[#2A2A3E]">
            {lessons.map((lesson) => (
              <div key={lesson.id} className="px-6 py-4 hover:bg-[#16162A] transition">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-white">{lesson.title}</h3>
                      {lesson.class_name && (
                        <span className="px-2 py-1 bg-accent-blue/15 text-accent-blue text-xs font-medium rounded">
                          {lesson.class_name}
                        </span>
                      )}
                      {lesson.subject_name && (
                        <span className="px-2 py-1 bg-accent-pink/15 text-accent-pink text-xs font-medium rounded">
                          {lesson.subject_name}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 mb-2">
                      Lesson Date: <span className="font-medium text-gray-300">{formatDate(lesson.lesson_date)}</span>
                    </p>
                    {lesson.description && (
                      <p className="text-sm text-gray-400 mb-3">{lesson.description}</p>
                    )}
                  </div>
                  <div className="flex gap-2 ml-4">
                    <button
                      onClick={() => handleEditLesson(lesson)}
                      className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                      title="Edit Lesson"
                    >
                      ✏️ Edit
                    </button>
                    <button
                      onClick={() => handleDeleteLesson(lesson.id)}
                      disabled={deletingLessonId === lesson.id}
                      className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition disabled:opacity-50 disabled:cursor-not-allowed"
                      title="Delete Lesson"
                    >
                      {deletingLessonId === lesson.id ? '⏳' : '🗑️'} Delete
                    </button>
                  </div>
                </div>
                
                {lesson.lectures && lesson.lectures.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-[#2A2A3E]">
                    <p className="text-sm font-semibold text-gray-300 mb-2">Lectures ({lesson.lectures.length}):</p>
                    <ul className="space-y-2">
                      {lesson.lectures.map((lecture) => (
                        <li key={lecture.id} className="text-sm text-gray-400 bg-[#16162A] p-3 rounded-lg">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <span className="font-medium text-white">{lecture.title}</span>
                              {lecture.content && (
                                <p className="text-xs text-gray-500 mt-1">{lecture.content}</p>
                              )}
                            </div>
                            <div className="text-xs text-gray-500 ml-4 text-right">
                              <div>{formatDate(lecture.lecture_date)}</div>
                              {lecture.start_time && (
                                <div className="mt-1">
                                  {lecture.start_time}
                                  {lecture.end_time && ` - ${lecture.end_time}`}
                                </div>
                              )}
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MyLessons;

