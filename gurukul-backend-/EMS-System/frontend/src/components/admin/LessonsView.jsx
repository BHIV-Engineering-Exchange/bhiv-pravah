import React, { useState, useEffect } from 'react';
import { schoolAdminAPI } from '../../services/api';

const LessonsView = () => {
  const [classes, setClasses] = useState([]);
  const [lessons, setLessons] = useState([]);
  const [selectedClassId, setSelectedClassId] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchClassesAndLessons();
  }, []);

  useEffect(() => {
    if (selectedClassId) {
      fetchLessons(selectedClassId);
    }
  }, [selectedClassId]);

  const fetchClassesAndLessons = async () => {
    try {
      setLoading(true);
      const classesData = await schoolAdminAPI.getClasses();
      setClasses(classesData);
      if (classesData.length > 0) {
        setSelectedClassId(classesData[0].id.toString());
        fetchLessons(classesData[0].id);
      } else {
        setLoading(false);
      }
      setError('');
    } catch (err) {
      console.error('Error fetching classes/lessons:', err);
      setError('Failed to load lessons. Please try again.');
      setLoading(false);
    }
  };

  const fetchLessons = async (classId) => {
    try {
      setLoading(true);
      const data = await schoolAdminAPI.getLessons(classId);
      setLessons(data);
      setError('');
    } catch (err) {
      console.error('Error fetching lessons:', err);
      setError('Failed to load lessons. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getClassName = (classId) => {
    const cls = classes.find((c) => c.id === classId);
    return cls ? cls.name : classId;
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
          <h1 className="text-3xl font-bold text-white">Lessons & Lectures</h1>
          <p className="text-gray-400 mt-2">View lessons and lectures created by teachers</p>
        </div>
      </div>

      <div className="card-dark p-4 flex flex-wrap gap-4 items-center">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Filter by Class
          </label>
          <select
            value={selectedClassId}
            onChange={(e) => setSelectedClassId(e.target.value)}
            className="px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
          >
            {classes.map((cls) => (
              <option key={cls.id} value={cls.id}>
                {cls.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {error && (
        <div className="error-box">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Lessons List */}
      <div className="card-dark overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2A2A3E]">
          <h2 className="text-xl font-bold text-white">
            Lessons ({lessons.length}) - {selectedClassId ? getClassName(parseInt(selectedClassId, 10)) : ''}
          </h2>
        </div>
        <div className="divide-y divide-[#2A2A3E]">
          {lessons.length === 0 ? (
            <div className="px-6 py-4 text-center text-gray-500">No lessons found</div>
          ) : (
            lessons.map((lesson) => (
              <div key={lesson.id} className="px-6 py-4 hover:bg-[#16162A]">
                <div className="flex justify-between items-center mb-1">
                  <div>
                    <h3 className="text-lg font-semibold text-white">{lesson.title}</h3>
                    <p className="text-xs text-gray-500">
                      Lesson Date: {lesson.lesson_date}
                    </p>
                  </div>
                </div>
                {lesson.description && (
                  <p className="text-sm text-gray-400 mb-2">{lesson.description}</p>
                )}
                {lesson.lectures && lesson.lectures.length > 0 && (
                  <div className="mt-2">
                    <p className="text-sm font-semibold text-gray-300 mb-1">Lectures:</p>
                    <ul className="list-disc list-inside text-sm text-gray-400">
                      {lesson.lectures.map((lec) => (
                        <li key={lec.id}>
                          <span className="font-medium">{lec.title}</span> — {lec.lecture_date}
                          {lec.start_time && ` (${lec.start_time} - ${lec.end_time || ''})`}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default LessonsView;

