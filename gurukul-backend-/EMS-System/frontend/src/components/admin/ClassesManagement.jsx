import React, { useState, useEffect } from 'react';
import { schoolAdminAPI } from '../../services/api';

const ClassesManagement = () => {
  const [classes, setClasses] = useState([]);
  const [subjects, setSubjects] = useState([]);
  const [teachers, setTeachers] = useState([]);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showCreateSubjectForm, setShowCreateSubjectForm] = useState(false);
  const [selectedClass, setSelectedClass] = useState(null);
  const [classStudents, setClassStudents] = useState({}); // { classId: [students] }
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assigningClassId, setAssigningClassId] = useState(null);
  const [editingClass, setEditingClass] = useState(null);
  const [editingSubject, setEditingSubject] = useState(null);
  const [subjectFormData, setSubjectFormData] = useState({
    name: '',
    code: ''
  });

  const [formData, setFormData] = useState({
    name: '',
    grade: '',
    subject_id: '',
    teacher_id: '',
    academic_year: '',
  });

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const [classesData, subjectsData, teachersData, studentsData] = await Promise.all([
        schoolAdminAPI.getClasses(),
        schoolAdminAPI.getSubjects(),
        schoolAdminAPI.getTeachers(),
        schoolAdminAPI.getStudents(),
      ]);
      setClasses(classesData);
      setSubjects(subjectsData || []);
      setTeachers(teachersData || []);
      setStudents(studentsData || []);
      setError('');
      
      // Fetch students for each class
      const studentsMap = {};
      for (const cls of classesData) {
        try {
          const enrolledStudents = await schoolAdminAPI.getClassStudents(cls.id);
          studentsMap[cls.id] = enrolledStudents;
        } catch (err) {
          console.error(`Error fetching students for class ${cls.id}:`, err);
          studentsMap[cls.id] = [];
        }
      }
      setClassStudents(studentsMap);
      
      // Show warning if no subjects exist
      if (!subjectsData || subjectsData.length === 0) {
        setError('No subjects found. Please create subjects first before creating classes.');
      }
    } catch (err) {
      console.error('Error fetching classes data:', err);
      const errorMsg = err.response?.data?.detail || err.message || 'Failed to load classes. Please try again.';
      setError(`Error: ${errorMsg}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSubject = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.createSubject({
        name: subjectFormData.name,
        code: subjectFormData.code || null,
      });
      setShowCreateSubjectForm(false);
      setEditingSubject(null);
      setSubjectFormData({ name: '', code: '' });
      fetchInitialData();
      alert('Subject created successfully!');
    } catch (err) {
      console.error('Error creating subject:', err);
      alert(err.response?.data?.detail || 'Failed to create subject');
    }
  };

  const handleEditSubject = (subject) => {
    setEditingSubject(subject);
    setSubjectFormData({
      name: subject.name,
      code: subject.code || '',
    });
    setShowCreateSubjectForm(true);
  };

  const handleUpdateSubject = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.updateSubject(editingSubject.id, {
        name: subjectFormData.name,
        code: subjectFormData.code || null,
      });
      setShowCreateSubjectForm(false);
      setEditingSubject(null);
      setSubjectFormData({ name: '', code: '' });
      fetchInitialData();
      alert('Subject updated successfully!');
    } catch (err) {
      console.error('Error updating subject:', err);
      alert(err.response?.data?.detail || 'Failed to update subject');
    }
  };

  const handleDeleteSubject = async (id) => {
    if (!window.confirm('Are you sure you want to delete this subject? This will fail if it is used in any classes.')) {
      return;
    }
    try {
      await schoolAdminAPI.deleteSubject(id);
      fetchInitialData();
      alert('Subject deleted successfully!');
    } catch (err) {
      console.error('Error deleting subject:', err);
      alert(err.response?.data?.detail || 'Failed to delete subject');
    }
  };

  const handleCreateClass = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.createClass({
        name: formData.name,
        grade: formData.grade,
        subject_id: parseInt(formData.subject_id, 10),
        teacher_id: parseInt(formData.teacher_id, 10),
        academic_year: formData.academic_year || null,
      });
      setShowCreateForm(false);
      setEditingClass(null);
      setFormData({
        name: '',
        grade: '',
        subject_id: '',
        teacher_id: '',
        academic_year: '',
      });
      fetchInitialData();
      alert('Class created successfully!');
    } catch (err) {
      console.error('Error creating class:', err);
      alert(err.response?.data?.detail || 'Failed to create class');
    }
  };

  const handleEditClass = (classObj) => {
    setEditingClass(classObj);
    setFormData({
      name: classObj.name,
      grade: classObj.grade,
      subject_id: classObj.subject_id.toString(),
      teacher_id: classObj.teacher_id.toString(),
      academic_year: classObj.academic_year || '',
    });
    setShowCreateForm(true);
  };

  const handleUpdateClass = async (e) => {
    e.preventDefault();
    try {
      await schoolAdminAPI.updateClass(editingClass.id, {
        name: formData.name,
        grade: formData.grade,
        subject_id: parseInt(formData.subject_id, 10),
        teacher_id: parseInt(formData.teacher_id, 10),
        academic_year: formData.academic_year || null,
      });
      setShowCreateForm(false);
      setEditingClass(null);
      setFormData({
        name: '',
        grade: '',
        subject_id: '',
        teacher_id: '',
        academic_year: '',
      });
      fetchInitialData();
      alert('Class updated successfully!');
    } catch (err) {
      console.error('Error updating class:', err);
      alert(err.response?.data?.detail || 'Failed to update class');
    }
  };

  const handleDeleteClass = async (id) => {
    if (!window.confirm('Are you sure you want to delete this class? This will fail if it has students, lessons, or timetable slots.')) {
      return;
    }
    try {
      await schoolAdminAPI.deleteClass(id);
      fetchInitialData();
      alert('Class deleted successfully!');
    } catch (err) {
      console.error('Error deleting class:', err);
      alert(err.response?.data?.detail || 'Failed to delete class');
    }
  };

  const handleAssignStudent = async (classId, studentId) => {
    try {
      await schoolAdminAPI.assignStudentToClass(classId, studentId);
      // Refresh class students
      const enrolledStudents = await schoolAdminAPI.getClassStudents(classId);
      setClassStudents({ ...classStudents, [classId]: enrolledStudents });
      setShowAssignModal(false);
      setAssigningClassId(null);
      alert('Student assigned to class successfully!');
      fetchInitialData(); // Refresh to update counts
    } catch (err) {
      console.error('Error assigning student:', err);
      alert(err.response?.data?.detail || 'Failed to assign student to class');
    }
  };

  const handleRemoveStudent = async (classId, studentId) => {
    if (!window.confirm('Are you sure you want to remove this student from the class?')) {
      return;
    }
    try {
      await schoolAdminAPI.removeStudentFromClass(classId, studentId);
      // Refresh class students
      const enrolledStudents = await schoolAdminAPI.getClassStudents(classId);
      setClassStudents({ ...classStudents, [classId]: enrolledStudents });
      alert('Student removed from class successfully!');
      fetchInitialData(); // Refresh to update counts
    } catch (err) {
      console.error('Error removing student:', err);
      alert(err.response?.data?.detail || 'Failed to remove student from class');
    }
  };

  const openAssignModal = (classId) => {
    setAssigningClassId(classId);
    setShowAssignModal(true);
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
        <div>
          <h1 className="text-3xl font-bold text-white">Classes Management</h1>
          <p className="text-gray-400 mt-2">Manage classes, subjects, and teachers</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowCreateSubjectForm(!showCreateSubjectForm)}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
          >
            ➕ Create Subject
          </button>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition"
          >
            ➕ Create Class
          </button>
        </div>
      </div>

      {/* Create/Edit Subject Form */}
      {showCreateSubjectForm && (
        <div className="card-dark p-6">
          <h2 className="text-xl font-bold text-white mb-4">
            {editingSubject ? 'Edit Subject' : 'Create New Subject'}
          </h2>
          <form onSubmit={editingSubject ? handleUpdateSubject : handleCreateSubject} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Subject Name *</label>
              <input
                type="text"
                required
                value={subjectFormData.name}
                onChange={(e) => setSubjectFormData({ ...subjectFormData, name: e.target.value })}
                className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                placeholder="e.g., Mathematics"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Subject Code (Optional)</label>
              <input
                type="text"
                value={subjectFormData.code}
                onChange={(e) => setSubjectFormData({ ...subjectFormData, code: e.target.value })}
                className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                placeholder="e.g., MATH"
              />
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition"
              >
                {editingSubject ? 'Update Subject' : 'Create Subject'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateSubjectForm(false);
                  setEditingSubject(null);
                  setSubjectFormData({ name: '', code: '' });
                }}
                className="px-4 py-2 bg-gray-300 text-white rounded-lg hover:bg-gray-400 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {showCreateForm && (
        <div className="card-dark p-6">
          <h2 className="text-xl font-bold text-white mb-4">
            {editingClass ? 'Edit Class' : 'Create New Class'}
          </h2>
          <form onSubmit={editingClass ? handleUpdateClass : handleCreateClass} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Class Name *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                placeholder="e.g., Grade 5A"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Grade *</label>
              <input
                type="text"
                required
                value={formData.grade}
                onChange={(e) => setFormData({ ...formData, grade: e.target.value })}
                className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                placeholder="e.g., 5"
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Subject *</label>
                <select
                  required
                  value={formData.subject_id}
                  onChange={(e) => setFormData({ ...formData, subject_id: e.target.value })}
                  className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                  disabled={subjects.length === 0}
                >
                  <option value="">
                    {subjects.length === 0 ? 'No subjects available. Create subjects first.' : 'Select subject'}
                  </option>
                  {subjects.map((subject) => (
                    <option key={subject.id} value={subject.id}>
                      {subject.name} {subject.code ? `(${subject.code})` : ''}
                    </option>
                  ))}
                </select>
                {subjects.length === 0 && (
                  <p className="mt-1 text-sm text-red-600">
                    No subjects found. Click "Create Subject" button above to add subjects.
                  </p>
                )}
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Teacher *</label>
                <select
                  required
                  value={formData.teacher_id}
                  onChange={(e) => setFormData({ ...formData, teacher_id: e.target.value })}
                  className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                >
                  <option value="">Select teacher</option>
                  {teachers.map((teacher) => (
                    <option key={teacher.id} value={teacher.id}>
                      {teacher.name} ({teacher.email})
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Academic Year</label>
              <input
                type="text"
                value={formData.academic_year}
                onChange={(e) => setFormData({ ...formData, academic_year: e.target.value })}
                className="w-full px-4 py-2 border border-[#2A2A3E] rounded-lg focus:ring-2 focus:ring-accent-green"
                placeholder="e.g., 2024-2025"
              />
            </div>
            <div className="flex gap-3">
              <button
                type="submit"
                className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 transition"
              >
                {editingClass ? 'Update Class' : 'Create Class'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowCreateForm(false);
                  setEditingClass(null);
                  setFormData({
                    name: '',
                    grade: '',
                    subject_id: '',
                    teacher_id: '',
                    academic_year: '',
                  });
                }}
                className="px-4 py-2 bg-gray-300 text-white rounded-lg hover:bg-gray-400 transition"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {error && (
        <div className="error-box">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Subjects List */}
      <div className="card-dark overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2A2A3E]">
          <h2 className="text-xl font-bold text-white">All Subjects ({subjects.length})</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#16162A]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Code</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-[#2A2A3E]">
              {subjects.length === 0 ? (
                <tr>
                  <td colSpan="4" className="px-6 py-4 text-center text-gray-500">
                    No subjects found. Create a subject to get started.
                  </td>
                </tr>
              ) : (
                subjects.map((subject) => (
                  <tr key={subject.id} className="hover:bg-[#16162A]">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-white">{subject.id}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{subject.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{subject.code || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEditSubject(subject)}
                          className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition"
                          title="Edit"
                        >
                          ✏️ Edit
                        </button>
                        <button
                          onClick={() => handleDeleteSubject(subject.id)}
                          className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 transition"
                          title="Delete"
                        >
                          🗑️ Delete
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

      <div className="card-dark overflow-hidden">
        <div className="px-6 py-4 border-b border-[#2A2A3E]">
          <h2 className="text-xl font-bold text-white">All Classes ({classes.length})</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#16162A]">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Grade</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Subject</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Teacher</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Students</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Academic Year</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-[#2A2A3E]">
              {classes.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-6 py-4 text-center text-gray-500">
                    No classes found
                  </td>
                </tr>
              ) : (
                classes.map((cls) => {
                  const enrolledStudents = classStudents[cls.id] || [];
                  const isExpanded = selectedClass === cls.id;
                  return (
                    <React.Fragment key={cls.id}>
                      <tr className="hover:bg-[#16162A]">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-white">{cls.id}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-white">{cls.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{cls.grade}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {cls.subject_name || `Subject #${cls.subject_id}`}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {cls.teacher_name || `Teacher #${cls.teacher_id}`}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          <span className="font-semibold">{enrolledStudents.length}</span> enrolled
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {cls.academic_year || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div className="flex gap-2 flex-wrap">
                            <button
                              onClick={() => setSelectedClass(isExpanded ? null : cls.id)}
                              className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-xs"
                            >
                              {isExpanded ? '▼ Hide' : '▶ View'} Students
                            </button>
                            <button
                              onClick={() => openAssignModal(cls.id)}
                              className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-xs"
                            >
                              ➕ Assign
                            </button>
                            <button
                              onClick={() => handleEditClass(cls)}
                              className="px-3 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600 text-xs"
                              title="Edit"
                            >
                              ✏️ Edit
                            </button>
                            <button
                              onClick={() => handleDeleteClass(cls.id)}
                              className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-xs"
                              title="Delete"
                            >
                              🗑️ Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr>
                          <td colSpan="7" className="px-6 py-4 bg-[#16162A]">
                            <div className="space-y-2">
                              <h4 className="font-semibold text-gray-300">Enrolled Students ({enrolledStudents.length}):</h4>
                              {enrolledStudents.length === 0 ? (
                                <p className="text-gray-500 text-sm">No students enrolled yet. Click "Assign" to add students.</p>
                              ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                                  {enrolledStudents.map((student) => (
                                    <div key={student.id} className="flex items-center justify-between bg-white p-2 rounded border">
                                      <div>
                                        <span className="font-medium text-sm">{student.name}</span>
                                        <span className="text-xs text-gray-500 ml-2">({student.email})</span>
                                      </div>
                                      <button
                                        onClick={() => handleRemoveStudent(cls.id, student.id)}
                                        className="px-2 py-1 bg-red-500 text-white rounded hover:bg-red-600 text-xs"
                                      >
                                        Remove
                                      </button>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Assign Student Modal */}
      {showAssignModal && assigningClassId && (
        <div className="modal-overlay">
          <div className="bg-[#1A1A2E] border border-[#2A2A3E] rounded-2xl p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-white mb-4">Assign Student to Class</h2>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {students
                .filter(student => {
                  // Filter out students already enrolled in this class
                  const enrolled = classStudents[assigningClassId] || [];
                  return !enrolled.some(s => s.id === student.id);
                })
                .map((student) => (
                  <div key={student.id} className="flex items-center justify-between p-3 border rounded hover:bg-[#16162A]">
                    <div>
                      <span className="font-medium">{student.name}</span>
                      <span className="text-sm text-gray-500 ml-2">({student.email})</span>
                      {student.grade && (
                        <span className="text-xs text-gray-400 ml-2">Grade: {student.grade}</span>
                      )}
                    </div>
                    <button
                      onClick={() => handleAssignStudent(assigningClassId, student.id)}
                      className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
                    >
                      Assign
                    </button>
                  </div>
                ))}
              {students.filter(student => {
                const enrolled = classStudents[assigningClassId] || [];
                return !enrolled.some(s => s.id === student.id);
              }).length === 0 && (
                <p className="text-gray-500 text-center py-4">All students are already assigned to this class.</p>
              )}
            </div>
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => {
                  setShowAssignModal(false);
                  setAssigningClassId(null);
                }}
                className="px-4 py-2 bg-gray-300 text-white rounded hover:bg-gray-400"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ClassesManagement;

