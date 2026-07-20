import axios from 'axios';

// Use environment variable for production, fallback to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Handle 401 errors (unauthorized)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid, clear it and redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      // Use window.location for HashRouter compatibility
      window.location.hash = '#/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: async (email, password) => {
    const response = await api.post('/v1/auth/login-json', { email, password });
    return response.data;
  },
  register: async (userData) => {
    const response = await api.post('/v1/auth/register', userData);
    return response.data;
  },
  getMe: async () => {
    const response = await api.get('/v1/auth/me');
    return response.data;
  },
  setPassword: async (token, password) => {
    const response = await api.post('/v1/auth/set-password', { token, password });
    return response.data;
  },
  resetPassword: async (token, oldPassword, newPassword) => {
    const response = await api.post('/v1/auth/reset-password', { 
      token, 
      old_password: oldPassword, 
      new_password: newPassword 
    });
    return response.data;
  },
  changePassword: async (currentPassword, newPassword) => {
    const response = await api.post('/v1/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword
    });
    return response.data;
  },
};

// Schools API
export const schoolsAPI = {
  getPublicList: async () => {
    const response = await api.get('/schools/public/list');
    return response.data;
  },
  // Note: GET /schools/ endpoint has been removed
  // Use specific school endpoints instead
  getById: async (schoolId) => {
    const response = await api.get(`/schools/${schoolId}`);
    return response.data;
  },
  create: async (schoolData) => {
    const response = await api.post('/schools/', schoolData);
    return response.data;
  },
  update: async (schoolId, schoolData) => {
    const response = await api.put(`/schools/${schoolId}`, schoolData);
    return response.data;
  },
  delete: async (schoolId) => {
    await api.delete(`/schools/${schoolId}`);
    return true;
  },
};

// Admins API
export const adminsAPI = {
  getAll: async (search = null, schoolId = null) => {
    const params = {};
    if (search) params.search = search;
    if (schoolId) params.school_id = schoolId;
    const response = await api.get('/schools/admins', { params });
    return response.data;
  },
  getById: async (adminId) => {
    const response = await api.get(`/schools/admins/${adminId}`);
    return response.data;
  },
  getBySchool: async (schoolId) => {
    const response = await api.get(`/schools/${schoolId}/admins`);
    return response.data;
  },
  // Invite admin via email (new email-based flow)
  invite: async (adminData) => {
    const response = await api.post('/super/invite-admin', {
      name: adminData.name,
      email: adminData.email,
      school_id: parseInt(adminData.school_id)
    });
    return response.data;
  },
  // Legacy create endpoint (still available but not recommended)
  create: async (schoolId, adminData) => {
    const response = await api.post(`/schools/${schoolId}/admins`, adminData);
    return response.data;
  },
  update: async (adminId, adminData) => {
    const response = await api.put(`/schools/admins/${adminId}`, adminData);
    return response.data;
  },
  delete: async (adminId) => {
    await api.delete(`/schools/admins/${adminId}`);
    return true;
  },
};

// Dashboard API
export const dashboardAPI = {
  getStats: async () => {
    const response = await api.get('/dashboard/stats');
    return response.data;
  },
  getUsers: async (search = null, role = null, schoolId = null) => {
    const params = {};
    if (search) params.search = search;
    if (role) params.role = role;
    if (schoolId) params.school_id = schoolId;
    const response = await api.get('/dashboard/users', { params });
    return response.data;
  },
  getUserById: async (userId) => {
    const response = await api.get(`/dashboard/users/${userId}`);
    return response.data;
  },
};

// School Admin API
export const schoolAdminAPI = {
  // Dashboard Stats
  getDashboardStats: async () => {
    const response = await api.get('/admin/dashboard/stats');
    return response.data;
  },
  
  // Teachers
  getTeachers: async (search = null) => {
    const params = {};
    if (search) params.search = search;
    const response = await api.get('/admin/teachers', { params });
    return response.data;
  },
  createTeacher: async (teacherData) => {
    const response = await api.post('/admin/teachers', teacherData);
    return response.data;
  },
  updateTeacher: async (teacherId, teacherData) => {
    const response = await api.put(`/admin/teachers/${teacherId}`, teacherData);
    return response.data;
  },
  deleteTeacher: async (teacherId) => {
    const response = await api.delete(`/admin/teachers/${teacherId}`);
    return response.data;
  },
  uploadTeachersExcel: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/admin/teachers/upload-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
  
  // Students
  getStudents: async (search = null, grade = null) => {
    const params = {};
    if (search) params.search = search;
    if (grade) params.grade = grade;
    const response = await api.get('/admin/students', { params });
    return response.data;
  },
  createStudent: async (studentData) => {
    const response = await api.post('/admin/students', studentData);
    return response.data;
  },
  updateStudent: async (studentId, studentData) => {
    const response = await api.put(`/admin/students/${studentId}`, studentData);
    return response.data;
  },
  deleteStudent: async (studentId) => {
    const response = await api.delete(`/admin/students/${studentId}`);
    return response.data;
  },
  uploadStudentsExcel: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/admin/students/upload-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
  
  // Parents
  getParents: async (search = null) => {
    const params = {};
    if (search) params.search = search;
    const response = await api.get('/admin/parents', { params });
    return response.data;
  },
  createParent: async (parentData) => {
    const response = await api.post('/admin/parents', parentData);
    return response.data;
  },
  updateParent: async (parentId, parentData) => {
    const response = await api.put(`/admin/parents/${parentId}`, parentData);
    return response.data;
  },
  deleteParent: async (parentId) => {
    const response = await api.delete(`/admin/parents/${parentId}`);
    return response.data;
  },
  uploadParentsExcel: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/admin/parents/upload-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
  
  // Subjects
  getSubjects: async () => {
    const response = await api.get('/admin/subjects');
    return response.data;
  },
  createSubject: async (subjectData) => {
    const response = await api.post('/admin/subjects', subjectData);
    return response.data;
  },
  updateSubject: async (subjectId, subjectData) => {
    const response = await api.put(`/admin/subjects/${subjectId}`, subjectData);
    return response.data;
  },
  deleteSubject: async (subjectId) => {
    await api.delete(`/admin/subjects/${subjectId}`);
    return true;
  },
  
  // Classes
  getClasses: async () => {
    const response = await api.get('/admin/classes');
    return response.data;
  },
  createClass: async (classData) => {
    const response = await api.post('/admin/classes', classData);
    return response.data;
  },
  updateClass: async (classId, classData) => {
    const response = await api.put(`/admin/classes/${classId}`, classData);
    return response.data;
  },
  deleteClass: async (classId) => {
    await api.delete(`/admin/classes/${classId}`);
    return true;
  },
  assignStudentToClass: async (classId, studentId) => {
    const response = await api.post(`/admin/classes/${classId}/students/${studentId}`);
    return response.data;
  },
  getClassStudents: async (classId) => {
    const response = await api.get(`/admin/classes/${classId}/students`);
    return response.data;
  },
  removeStudentFromClass: async (classId, studentId) => {
    const response = await api.delete(`/admin/classes/${classId}/students/${studentId}`);
    return response.data;
  },
  
  // Timetable
  getTimetable: async (classId = null) => {
    const params = {};
    if (classId) params.class_id = classId;
    const response = await api.get('/admin/timetable', { params });
    return response.data;
  },
  createTimetableSlot: async (slotData) => {
    const response = await api.post('/admin/timetable', slotData);
    return response.data;
  },
  updateTimetableSlot: async (slotId, slotData) => {
    const response = await api.put(`/admin/timetable/${slotId}`, slotData);
    return response.data;
  },
  deleteTimetableSlot: async (slotId) => {
    await api.delete(`/admin/timetable/${slotId}`);
    return true;
  },
  
  // Holidays
  getHolidays: async () => {
    const response = await api.get('/admin/holidays');
    return response.data;
  },
  createHoliday: async (holidayData) => {
    const response = await api.post('/admin/holidays', holidayData);
    return response.data;
  },
  updateHoliday: async (holidayId, holidayData) => {
    const response = await api.put(`/admin/holidays/${holidayId}`, holidayData);
    return response.data;
  },
  deleteHoliday: async (holidayId) => {
    await api.delete(`/admin/holidays/${holidayId}`);
    return true;
  },
  
  // Events
  getEvents: async () => {
    const response = await api.get('/admin/events');
    return response.data;
  },
  createEvent: async (eventData) => {
    const response = await api.post('/admin/events', eventData);
    return response.data;
  },
  updateEvent: async (eventId, eventData) => {
    const response = await api.put(`/admin/events/${eventId}`, eventData);
    return response.data;
  },
  deleteEvent: async (eventId) => {
    await api.delete(`/admin/events/${eventId}`);
    return true;
  },
  
  // Announcements
  getAnnouncements: async (targetAudience = null) => {
    const params = {};
    if (targetAudience) params.target_audience = targetAudience;
    const response = await api.get('/admin/announcements', { params });
    return response.data;
  },
  createAnnouncement: async (announcementData) => {
    const response = await api.post('/admin/announcements', announcementData);
    return response.data;
  },
  updateAnnouncement: async (announcementId, announcementData) => {
    const response = await api.put(`/admin/announcements/${announcementId}`, announcementData);
    return response.data;
  },
  deleteAnnouncement: async (announcementId) => {
    await api.delete(`/admin/announcements/${announcementId}`);
    return true;
  },
  
  // Lessons
  getLessons: async (classId = null) => {
    const params = {};
    if (classId) params.class_id = classId;
    const response = await api.get('/admin/lessons', { params });
    return response.data;
  },
  
  // Parent-Student Mapping
  getStudentParents: async (studentId) => {
    const response = await api.get(`/admin/students/${studentId}/parents`);
    return response.data;
  },
  getParentStudents: async (parentId) => {
    const response = await api.get(`/admin/parents/${parentId}/students`);
    return response.data;
  },
  createParentStudentLink: async (linkData) => {
    const response = await api.post('/admin/parent-student/link', linkData);
    return response.data;
  },
  deleteParentStudentLink: async (linkId) => {
    const response = await api.delete(`/admin/parent-student/link/${linkId}`);
    return response.data;
  },
  getStudentsWithParents: async (search = null) => {
    const params = search ? { search } : {};
    const response = await api.get('/admin/students-with-parents', { params });
    return response.data;
  },
  getParentsWithStudents: async (search = null) => {
    const params = search ? { search } : {};
    const response = await api.get('/admin/parents-with-students', { params });
    return response.data;
  },
  getParentStudentStats: async () => {
    const response = await api.get('/admin/parent-student/stats');
    return response.data;
  },
  uploadStudentsParentsCombined: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/admin/parent-student/upload-combined-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  },
  
  // Analytics
  getAnalytics: async () => {
    const response = await api.get('/admin/analytics');
    return response.data;
  },
  
  // Student-generated content (Gurukul)
  getStudentSummaries: async (studentId) => {
    const response = await api.get(`/admin/students/${studentId}/content/summaries`);
    return response.data;
  },
  getStudentFlashcards: async (studentId) => {
    const response = await api.get(`/admin/students/${studentId}/content/flashcards`);
    return response.data;
  },
  getStudentTestResults: async (studentId) => {
    const response = await api.get(`/admin/students/${studentId}/content/test-results`);
    return response.data;
  },
  getStudentSubjectData: async (studentId) => {
    const response = await api.get(`/admin/students/${studentId}/content/subject-data`);
    return response.data;
  },
};

// Teacher API
export const teacherAPI = {
  // Dashboard Stats
  getDashboardStats: async () => {
    const response = await api.get('/teacher/dashboard/stats');
    return response.data;
  },
  
  // Classes
  getMyClasses: async () => {
    const response = await api.get('/teacher/classes');
    return response.data;
  },
  getClassStudents: async (classId) => {
    const response = await api.get(`/teacher/classes/${classId}/students`);
    return response.data;
  },
  
  // Lessons
  getMyLessons: async (classId = null) => {
    const params = {};
    if (classId) params.class_id = classId;
    const response = await api.get('/teacher/lessons', { params });
    return response.data;
  },
  createLesson: async (lessonData) => {
    const response = await api.post('/teacher/lessons', lessonData);
    return response.data;
  },
  updateLesson: async (lessonId, lessonData) => {
    const response = await api.put(`/teacher/lessons/${lessonId}`, lessonData);
    return response.data;
  },
  deleteLesson: async (lessonId) => {
    await api.delete(`/teacher/lessons/${lessonId}`);
    return true;
  },
  
  // Timetable
  getMyTimetable: async () => {
    const response = await api.get('/teacher/timetable');
    return response.data;
  },
  
  // Announcements
  getMyAnnouncements: async () => {
    const response = await api.get('/teacher/announcements');
    return response.data;
  },
  
  // Attendance
  getAttendance: async (classId, attendanceDate = null) => {
    const params = { class_id: classId };
    if (attendanceDate) params.attendance_date = attendanceDate;
    const response = await api.get('/teacher/attendance', { params });
    return response.data;
  },
  // Student-generated content (Gurukul)
  getStudentSummaries: async (studentId) => {
    const response = await api.get(`/teacher/students/${studentId}/content/summaries`);
    return response.data;
  },
  getStudentFlashcards: async (studentId) => {
    const response = await api.get(`/teacher/students/${studentId}/content/flashcards`);
    return response.data;
  },
  getStudentTestResults: async (studentId) => {
    const response = await api.get(`/teacher/students/${studentId}/content/test-results`);
    return response.data;
  },
  getStudentSubjectData: async (studentId) => {
    const response = await api.get(`/teacher/students/${studentId}/content/subject-data`);
    return response.data;
  },
  
  markAttendance: async (attendanceData) => {
    const response = await api.post('/teacher/attendance/mark', attendanceData);
    return response.data;
  },
};

// Student API
export const studentAPI = {
  // Dashboard Stats
  getDashboardStats: async () => {
    const response = await api.get('/student/dashboard/stats');
    return response.data;
  },
  
  // Classes
  getMyClasses: async () => {
    const response = await api.get('/student/classes');
    return response.data;
  },
  
  // Teachers
  getMyTeachers: async () => {
    const response = await api.get('/student/teachers');
    return response.data;
  },
  
  // Lessons
  getMyLessons: async (classId = null) => {
    const params = {};
    if (classId) params.class_id = classId;
    const response = await api.get('/student/lessons', { params });
    return response.data;
  },
  
  // Timetable/Schedule
  getMyTimetable: async () => {
    const response = await api.get('/student/timetable');
    return response.data;
  },
  
  // Announcements
  getMyAnnouncements: async () => {
    const response = await api.get('/student/announcements');
    return response.data;
  },
  
  // Attendance
  getMyAttendance: async (classId = null, attendanceDate = null) => {
    const params = {};
    if (classId) params.class_id = classId;
    if (attendanceDate) params.attendance_date = attendanceDate;
    const response = await api.get('/student/attendance', { params });
    return response.data;
  },
  
  // Grades
  getMyGrades: async (classId = null) => {
    const params = {};
    if (classId) params.class_id = classId;
    const response = await api.get('/student/grades', { params });
    return response.data;
  },
};

// Parent API
export const parentAPI = {
  // Dashboard Stats
  getDashboardStats: async () => {
    const response = await api.get('/parent/dashboard/stats');
    return response.data;
  },
  
  // Children
  getMyChildren: async () => {
    const response = await api.get('/parent/children');
    return response.data;
  },
  
  // Grades
  getMyChildrenGrades: async (childId = null) => {
    const params = {};
    if (childId) params.child_id = childId;
    const response = await api.get('/parent/grades', { params });
    return response.data;
  },
  
  // Attendance
  getMyChildrenAttendance: async (childId = null, attendanceDate = null) => {
    const params = {};
    if (childId) params.child_id = childId;
    if (attendanceDate) params.attendance_date = attendanceDate;
    const response = await api.get('/parent/attendance', { params });
    return response.data;
  },
  
  // Announcements
  getMyAnnouncements: async () => {
    const response = await api.get('/parent/announcements');
    return response.data;
  },
  
  // Student-generated content (Gurukul)
  getChildSummaries: async (childId) => {
    const response = await api.get(`/parent/children/${childId}/content/summaries`);
    return response.data;
  },
  getChildFlashcards: async (childId) => {
    const response = await api.get(`/parent/children/${childId}/content/flashcards`);
    return response.data;
  },
  getChildTestResults: async (childId) => {
    const response = await api.get(`/parent/children/${childId}/content/test-results`);
    return response.data;
  },
  getChildSubjectData: async (childId) => {
    const response = await api.get(`/parent/children/${childId}/content/subject-data`);
    return response.data;
  },
};

export default api;
