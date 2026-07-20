import React, { useState, useEffect } from 'react';
import { schoolAdminAPI } from '../../services/api';

const TimetableManagement = () => {
  const [classes, setClasses] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [slots, setSlots] = useState([]);
  const [selectedClassId, setSelectedClassId] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingSlot, setEditingSlot] = useState(null);

  const [formData, setFormData] = useState({
    class_id: '',
    subject_id: '',
    teacher_id: '',
    day_of_week: 0,
    start_time: '',
    end_time: '',
    room: '',
  });

  const daysOfWeek = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  useEffect(() => {
    fetchInitialData();
  }, []);

  useEffect(() => {
    if (selectedClassId) {
      fetchTimetable(selectedClassId);
    }
  }, [selectedClassId]);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const [classesData, subjectsData, teachersData] = await Promise.all([
        schoolAdminAPI.getClasses(),
        schoolAdminAPI.getSubjects(),
        schoolAdminAPI.getTeachers(),
      ]);
      setClasses(classesData);
      setSubjects(subjectsData);
      setTeachers(teachersData);
      if (classesData.length > 0) {
        setSelectedClassId(classesData[0].id.toString());
        fetchTimetable(classesData[0].id);
      }
      setError('');
    } catch (err) {
      console.error('Error fetching timetable data:', err);
      setError('Failed to load timetable data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchTimetable = async (classId) => {
    try {
      const data = await schoolAdminAPI.getTimetable(classId);
      setSlots(data);
    } catch (err) {
      console.error('Error fetching timetable:', err);
      setError('Failed to load timetable. Please try again.');
    }
  };

  const handleCreateSlot = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.createTimetableSlot({
        class_id: parseInt(formData.class_id || selectedClassId, 10),
        subject_id: parseInt(formData.subject_id, 10),
        teacher_id: parseInt(formData.teacher_id, 10),
        day_of_week: parseInt(formData.day_of_week, 10),
        start_time: formData.start_time,
        end_time: formData.end_time,
        room: formData.room || null,
      });
      setShowCreateForm(false);
      setEditingSlot(null);
      setFormData({
        class_id: '',
        subject_id: '',
        teacher_id: '',
        day_of_week: 0,
        start_time: '',
        end_time: '',
        room: '',
      });
      fetchTimetable(selectedClassId);
      alert('Timetable slot created successfully!');
    } catch (err) {
      console.error('Error creating timetable slot:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to create timetable slot';
      console.error('Error details:', err.response?.data);
      alert(`Error: ${errorMessage}`);
    }
  };

  const handleEditSlot = (slot) => {
    setEditingSlot(slot);
    setFormData({
      class_id: slot.class_id.toString(),
      subject_id: slot.subject_id.toString(),
      teacher_id: slot.teacher_id.toString(),
      day_of_week: slot.day_of_week,
      start_time: slot.start_time,
      end_time: slot.end_time,
      room: slot.room || '',
    });
    setShowCreateForm(true);
  };

  const handleUpdateSlot = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.updateTimetableSlot(editingSlot.id, {
        class_id: parseInt(formData.class_id || selectedClassId, 10),
        subject_id: parseInt(formData.subject_id, 10),
        teacher_id: parseInt(formData.teacher_id, 10),
        day_of_week: parseInt(formData.day_of_week, 10),
        start_time: formData.start_time,
        end_time: formData.end_time,
        room: formData.room || null,
      });
      setShowCreateForm(false);
      setEditingSlot(null);
      setFormData({
        class_id: '',
        subject_id: '',
        teacher_id: '',
        day_of_week: 0,
        start_time: '',
        end_time: '',
        room: '',
      });
      fetchTimetable(selectedClassId);
      alert('Timetable slot updated successfully!');
    } catch (err) {
      console.error('Error updating timetable slot:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to update timetable slot';
      alert(`Error: ${errorMessage}`);
    }
  };

  const handleDeleteSlot = async (id) => {
    if (!window.confirm('Are you sure you want to delete this timetable slot?')) {
      return;
    }
    try {
      await schoolAdminAPI.deleteTimetableSlot(id);
      fetchTimetable(selectedClassId);
      alert('Timetable slot deleted successfully!');
    } catch (err) {
      console.error('Error deleting timetable slot:', err);
      alert(err.response?.data?.detail || 'Failed to delete timetable slot');
    }
  };

  const handleCancel = () => {
    setShowCreateForm(false);
    setEditingSlot(null);
    setFormData({
      class_id: '',
      subject_id: '',
      teacher_id: '',
      day_of_week: 0,
      start_time: '',
      end_time: '',
      room: '',
    });
  };

  const getClassName = (classId) => {
    const cls = classes.find((c) => c.id === classId);
    return cls ? cls.name : classId;
  };

  const getSubjectName = (subjectId) => {
    const subj = subjects.find((s) => s.id === subjectId);
    return subj ? subj.name : subjectId;
  };

  const getTeacherName = (teacherId) => {
    const t = teachers.find((teacher) => teacher.id === teacherId);
    return t ? t.name : teacherId;
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading timetable...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-white">Timetable Management</h1>
          <p className="text-gray-400 mt-2">Create and view weekly timetable per class</p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition"
        >
          ➕ Add Slot
        </button>
      </div>

      <div className="card-dark p-4 flex flex-wrap gap-4 items-center">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-1">
            Select Class
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

      {showCreateForm && (
        <div className="card-dark p-6">
          <h2 className="text-xl font-bold text-white mb-4">
            {editingSlot ? 'Edit Timetable Slot' : 'Create Timetable Slot'}
          </h2>
          <form onSubmit={editingSlot ? handleUpdateSlot : handleCreateSlot} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Class</label>
                <select
                  value={formData.class_id || selectedClassId}
                  onChange={(e) => setFormData({ ...formData, class_id: e.target.value })}
                  className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                >
                  {classes.map((cls) => (
                    <option key={cls.id} value={cls.id}>
                      {cls.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Day of Week</label>
                <select
                  value={formData.day_of_week}
                  onChange={(e) => setFormData({ ...formData, day_of_week: e.target.value })}
                  className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                >
                  {daysOfWeek.map((day, idx) => (
                    <option key={idx} value={idx}>
                      {day}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Subject</label>
                <select
                  value={formData.subject_id}
                  onChange={(e) => setFormData({ ...formData, subject_id: e.target.value })}
                  className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                >
                  <option value="">Select subject</option>
                  {subjects.map((subject) => (
                    <option key={subject.id} value={subject.id}>
                      {subject.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Teacher</label>
                <select
                  value={formData.teacher_id}
                  onChange={(e) => setFormData({ ...formData, teacher_id: e.target.value })}
                  className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                >
                  <option value="">Select teacher</option>
                  {teachers.map((teacher) => (
                    <option key={teacher.id} value={teacher.id}>
                      {teacher.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Start Time</label>
                <input
                  type="time"
                  value={formData.start_time}
                  onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
                  className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">End Time</label>
                <input
                  type="time"
                  value={formData.end_time}
                  onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
                  className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                  required
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Room</label>
                <input
                  type="text"
                  value={formData.room}
                  onChange={(e) => setFormData({ ...formData, room: e.target.value })}
                  className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                  placeholder="Optional"
                />
              </div>
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition"
              >
                {editingSlot ? 'Update Slot' : 'Create Slot'}
              </button>
              <button
                type="button"
                onClick={handleCancel}
                className="px-4 py-2 bg-gray-300 text-white rounded-lg hover:bg-gray-400 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Timetable Grid */}
      <div className="card-dark overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2A2A3E] flex justify-between items-center">
          <h2 className="text-xl font-bold text-white">
            Weekly Timetable - {getClassName(parseInt(selectedClassId, 10))}
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#16162A]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                  Day
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                  Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                  Subject
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                  Teacher
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                  Room
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-[#2A2A3E]">
              {slots.length === 0 ? (
                <tr>
                  <td colSpan="6" className="px-6 py-4 text-center text-gray-500">
                    No timetable slots defined for this class
                  </td>
                </tr>
              ) : (
                slots.map((slot) => (
                  <tr key={slot.id} className="hover:bg-[#16162A]">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white">
                      {daysOfWeek[slot.day_of_week]}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {slot.start_time} - {slot.end_time}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {getSubjectName(slot.subject_id)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {getTeacherName(slot.teacher_id)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {slot.room || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEditSlot(slot)}
                          className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                          title="Edit"
                        >
                          ✏️
                        </button>
                        <button
                          onClick={() => handleDeleteSlot(slot.id)}
                          className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition"
                          title="Delete"
                        >
                          🗑️
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TimetableManagement;

