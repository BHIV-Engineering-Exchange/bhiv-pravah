import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { teacherAPI } from '../../services/api';

const CreateLesson = () => {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const isEditing = !!id;
  const [classes, setClasses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  // Lesson form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    class_id: '',
    lesson_date: '',
    lectures: []
  });

  useEffect(() => {
    fetchClasses();
    if (isEditing && id) {
      loadLessonData();
      // Set lesson_id in sessionStorage for PRANA
      const lessonId = id.toString();
      sessionStorage.setItem('current_lesson_id', lessonId);
      // Also update window context if it exists
      if (window.EMSUserContext) {
        window.EMSUserContext.currentLessonId = lessonId;
      }
      console.log('[CreateLesson] Set lesson_id from URL param:', lessonId);
    } else if (!isEditing) {
      // Clear lesson_id when creating new lesson (only if not editing)
      sessionStorage.removeItem('current_lesson_id');
      if (window.EMSUserContext) {
        window.EMSUserContext.currentLessonId = null;
      }
      console.log('[CreateLesson] Cleared lesson_id (creating new lesson)');
    }
  }, [id, isEditing]);

  const loadLessonData = () => {
    // Try to get lesson from location state first (passed from MyLessons)
    if (location.state?.lesson) {
      const lesson = location.state.lesson;
      setFormData({
        title: lesson.title || '',
        description: lesson.description || '',
        class_id: lesson.class_id?.toString() || '',
        lesson_date: lesson.lesson_date || '',
        lectures: (lesson.lectures || []).map(lec => ({
          title: lec.title || '',
          content: lec.content || '',
          lecture_date: lec.lecture_date || lesson.lesson_date || '',
          start_time: lec.start_time || '',
          end_time: lec.end_time || ''
        }))
      });
    } else if (id) {
      // If no state, fetch the lesson
      fetchLesson(id);
    }
  };

  const fetchLesson = async (lessonId) => {
    try {
      setLoading(true);
      const lessons = await teacherAPI.getMyLessons();
      const lesson = lessons.find(l => l.id === parseInt(lessonId));
      if (lesson) {
        setFormData({
          title: lesson.title || '',
          description: lesson.description || '',
          class_id: lesson.class_id?.toString() || '',
          lesson_date: lesson.lesson_date || '',
          lectures: (lesson.lectures || []).map(lec => ({
            title: lec.title || '',
            content: lec.content || '',
            lecture_date: lec.lecture_date || lesson.lesson_date || '',
            start_time: lec.start_time || '',
            end_time: lec.end_time || ''
          }))
        });
      }
    } catch (err) {
      setError('Failed to load lesson data.');
      console.error('Error fetching lesson:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchClasses = async () => {
    try {
      setLoading(true);
      const data = await teacherAPI.getMyClasses();
      setClasses(data);
      if (data.length > 0) {
        setFormData(prev => ({ ...prev, class_id: data[0].id.toString() }));
      }
      setError('');
    } catch (err) {
      setError('Failed to load classes. Please try again.');
      console.error('Error fetching classes:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const addLecture = () => {
    setFormData(prev => ({
      ...prev,
      lectures: [...prev.lectures, {
        title: '',
        content: '',
        lecture_date: prev.lesson_date || '',
        start_time: '',
        end_time: ''
      }]
    }));
  };

  const removeLecture = (index) => {
    setFormData(prev => ({
      ...prev,
      lectures: prev.lectures.filter((_, i) => i !== index)
    }));
  };

  const updateLecture = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      lectures: prev.lectures.map((lec, i) =>
        i === index ? { ...lec, [field]: value } : lec
      )
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setSubmitting(true);

    try {
      // Validate required fields
      if (!formData.title.trim()) {
        throw new Error('Lesson title is required');
      }
      if (!formData.class_id) {
        throw new Error('Please select a class');
      }
      if (!formData.lesson_date) {
        throw new Error('Lesson date is required');
      }

      // Prepare data
      const lessonData = {
        title: formData.title.trim(),
        description: formData.description.trim() || null,
        class_id: parseInt(formData.class_id),
        lesson_date: formData.lesson_date,
        lectures: formData.lectures
          .filter(lec => lec.title.trim()) // Only include lectures with titles
          .map(lec => ({
            title: lec.title.trim(),
            content: lec.content.trim() || null,
            lecture_date: lec.lecture_date || formData.lesson_date,
            start_time: lec.start_time || null,
            end_time: lec.end_time || null
          }))
      };

      if (isEditing) {
        await teacherAPI.updateLesson(id, lessonData);
        setSuccess(true);
        // Keep lesson_id in sessionStorage since we're still viewing this lesson
        setTimeout(() => {
          navigate('/dashboard/lessons');
          // Clear lesson_id when navigating back to lessons list
          sessionStorage.removeItem('current_lesson_id');
          if (window.EMSUserContext) {
            window.EMSUserContext.currentLessonId = null;
          }
        }, 1500);
      } else {
        const createdLesson = await teacherAPI.createLesson(lessonData);
        setSuccess(true);
        
        // Set lesson_id after creating new lesson (so PRANA can track it)
        if (createdLesson && createdLesson.id) {
          const lessonId = createdLesson.id.toString();
          sessionStorage.setItem('current_lesson_id', lessonId);
          if (window.EMSUserContext) {
            window.EMSUserContext.currentLessonId = lessonId;
          }
          console.log('[CreateLesson] Set lesson_id after creation:', lessonId);
        } else {
          console.warn('[CreateLesson] Created lesson but no ID in response:', createdLesson);
        }
        
        // Reset form
        setFormData({
          title: '',
          description: '',
          class_id: classes.length > 0 ? classes[0].id.toString() : '',
          lesson_date: '',
          lectures: []
        });

        // Clear success message after 3 seconds
        setTimeout(() => setSuccess(false), 3000);
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to create lesson. Please try again.';
      setError(errorMessage);
    } finally {
      setSubmitting(false);
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

  if (classes.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <p className="text-yellow-800">You don't have any classes assigned yet. Please contact your administrator.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">
          {isEditing ? 'Edit Lesson' : 'Create New Lesson'}
        </h1>
        <p className="text-gray-400 mt-2">
          {isEditing ? 'Update lesson details' : 'Create a lesson for one of your classes'}
        </p>
      </div>

      {error && (
        <div className="error-box">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {success && (
        <div className="success-box p-4">
          <p className="text-accent-green font-semibold">
            Lesson {isEditing ? 'updated' : 'created'} successfully!
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit} className="card-dark p-6 space-y-6">
        {/* Basic Lesson Information */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-white border-b pb-2">Lesson Information</h2>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Class <span className="text-red-400">*</span>
            </label>
            <select
              name="class_id"
              value={formData.class_id}
              onChange={handleInputChange}
              required
              className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green focus:border-accent-green"
            >
              <option value="">Select a class</option>
              {classes.map((cls) => (
                <option key={cls.id} value={cls.id}>
                  {cls.name} {cls.subject_name ? `(${cls.subject_name})` : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Lesson Title <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              required
              placeholder="e.g., Introduction to Algebra"
              className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green focus:border-accent-green"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Description
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              rows={3}
              placeholder="Brief description of the lesson..."
              className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green focus:border-accent-green"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">
              Lesson Date <span className="text-red-400">*</span>
            </label>
            <input
              type="date"
              name="lesson_date"
              value={formData.lesson_date}
              onChange={handleInputChange}
              required
              className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green focus:border-accent-green"
            />
          </div>
        </div>

        {/* Lectures Section */}
        <div className="space-y-4">
          <div className="flex justify-between items-center border-b pb-2">
            <h2 className="text-xl font-semibold text-white">Lectures (Optional)</h2>
            <button
              type="button"
              data-ems-task="true"
              onClick={addLecture}
              className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition text-sm font-medium"
            >
              + Add Lecture
            </button>
          </div>

          {formData.lectures.length === 0 && (
            <p className="text-sm text-gray-500 italic">No lectures added. Click "Add Lecture" to add one.</p>
          )}

          {formData.lectures.map((lecture, index) => (
            <div key={index} className="border border-[#2A2A3E] rounded-lg p-4 space-y-3 bg-[#16162A]">
              <div className="flex justify-between items-center">
                <h3 className="font-medium text-gray-300">Lecture {index + 1}</h3>
                <button
                  type="button"
                  onClick={() => removeLecture(index)}
                  className="text-red-600 hover:text-red-400 text-sm font-medium"
                >
                  Remove
                </button>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Lecture Title
                </label>
                <input
                  type="text"
                  value={lecture.title}
                  onChange={(e) => updateLecture(index, 'title', e.target.value)}
                  placeholder="e.g., Variables and Expressions"
                  className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green focus:border-accent-green"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Content/Notes
                </label>
                <textarea
                  value={lecture.content}
                  onChange={(e) => updateLecture(index, 'content', e.target.value)}
                  rows={2}
                  placeholder="Lecture content or notes..."
                  className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green focus:border-accent-green"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Lecture Date
                  </label>
                  <input
                    type="date"
                    value={lecture.lecture_date || formData.lesson_date}
                    onChange={(e) => updateLecture(index, 'lecture_date', e.target.value)}
                    className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green focus:border-accent-green"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    Start Time
                  </label>
                  <input
                    type="time"
                    value={lecture.start_time}
                    onChange={(e) => updateLecture(index, 'start_time', e.target.value)}
                    className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green focus:border-accent-green"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-1">
                    End Time
                  </label>
                  <input
                    type="time"
                    value={lecture.end_time}
                    onChange={(e) => updateLecture(index, 'end_time', e.target.value)}
                    className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green focus:border-accent-green"
                  />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Submit Button */}
        <div className="flex justify-end gap-4 pt-4 border-t">
          <button
            type="button"
            onClick={() => window.history.back()}
            className="px-6 py-2 border border-[#2A2A3E] rounded-lg text-gray-300 hover:bg-[#16162A] transition font-medium"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            data-ems-task="true"
            className="px-6 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? (isEditing ? 'Updating...' : 'Creating...') : (isEditing ? 'Update Lesson' : 'Create Lesson')}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateLesson;

