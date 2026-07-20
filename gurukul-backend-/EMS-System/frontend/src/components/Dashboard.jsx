import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Layout from './Layout';
import DashboardOverview from './DashboardOverview';
import SchoolList from './SchoolList';
import CreateSchool from './CreateSchool';
import EditSchool from './EditSchool';
import SchoolDetails from './SchoolDetails';
import AdminList from './AdminList';
import CreateAdmin from './CreateAdmin';
import EditAdmin from './EditAdmin';
import ViewAllUsers from './ViewAllUsers';
import ChangePassword from './ChangePassword';

// School Admin Components
import SchoolAdminDashboard from './admin/SchoolAdminDashboard';
import TeachersManagement from './admin/TeachersManagement';
import StudentsManagement from './admin/StudentsManagement';
import ParentsManagement from './admin/ParentsManagement';
import ClassesManagement from './admin/ClassesManagement';
import TimetableManagement from './admin/TimetableManagement';
import HolidaysEvents from './admin/HolidaysEvents';
import Announcements from './admin/Announcements';
import LessonsView from './admin/LessonsView';
import Analytics from './admin/Analytics';
import ParentStudentLinking from './admin/ParentStudentLinking';
import AdminStudentContent from './admin/AdminStudentContent';

// Teacher Components
import TeacherDashboard from './teacher/TeacherDashboard';
import TeacherMyClasses from './teacher/MyClasses';
import MyStudents from './teacher/MyStudents';
import MyLessons from './teacher/MyLessons';
import Attendance from './teacher/Attendance';
import CreateLesson from './teacher/CreateLesson';
import MyTimetable from './teacher/MyTimetable';
import MyAnnouncements from './teacher/MyAnnouncements';
import StudentContent from './teacher/StudentContent';

// Student Components
import StudentDashboard from './student/StudentDashboard';
import MyClasses from './student/MyClasses';
import MyTeachers from './student/MyTeachers';
import MySchedule from './student/MySchedule';
import MyAttendance from './student/MyAttendance';
import StudentAnnouncements from './student/MyAnnouncements';

// Parent Components
import ParentDashboard from './parent/ParentDashboard';
import MyChildren from './parent/MyChildren';
import MyChildrenAttendance from './parent/MyChildrenAttendance';
import ParentAnnouncements from './parent/MyAnnouncements';
import MyChildContent from './parent/MyChildContent';

const Dashboard = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';
  const isTeacher = user?.role === 'TEACHER';
  const isStudent = user?.role === 'STUDENT';
  const isParent = user?.role === 'PARENT';

  return (
    <Layout>
      <Routes>
        {isAdmin ? (
          // School Admin Routes
          <>
            <Route index element={<SchoolAdminDashboard />} />
            <Route path="/teachers" element={<TeachersManagement />} />
            <Route path="/students" element={<StudentsManagement />} />
            <Route path="/parents" element={<ParentsManagement />} />
            <Route path="/classes" element={<ClassesManagement />} />
            <Route path="/timetable" element={<TimetableManagement />} />
            <Route path="/holidays-events" element={<HolidaysEvents />} />
            <Route path="/announcements" element={<Announcements />} />
            <Route path="/lessons" element={<LessonsView />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/parent-student-linking" element={<ParentStudentLinking />} />
            <Route path="/students/:studentId/content" element={<AdminStudentContent />} />
            <Route path="/reset-password" element={<ChangePassword />} />
          </>
        ) : isTeacher ? (
          // Teacher Routes
          <>
            <Route index element={<TeacherDashboard />} />
            <Route path="/classes" element={<TeacherMyClasses />} />
            <Route path="/classes/:classId/students" element={<MyStudents />} />
            <Route path="/students" element={<MyStudents />} />
            <Route path="/students/:studentId/content" element={<StudentContent />} />
            <Route path="/lessons" element={<MyLessons />} />
            <Route path="/lessons/create" element={<CreateLesson />} />
            <Route path="/lessons/edit/:id" element={<CreateLesson />} />
            <Route path="/attendance" element={<Attendance />} />
            <Route path="/timetable" element={<MyTimetable />} />
            <Route path="/announcements" element={<MyAnnouncements />} />
            <Route path="/reset-password" element={<ChangePassword />} />
          </>
        ) : isStudent ? (
          // Student Routes
          <>
            <Route index element={<StudentDashboard />} />
            <Route path="/classes" element={<MyClasses />} />
            <Route path="/teachers" element={<MyTeachers />} />
            <Route path="/attendance" element={<MyAttendance />} />
            <Route path="/schedule" element={<MySchedule />} />
            <Route path="/announcements" element={<StudentAnnouncements />} />
            <Route path="/reset-password" element={<ChangePassword />} />
          </>
        ) : isParent ? (
          // Parent Routes
          <>
            <Route index element={<ParentDashboard />} />
            <Route path="/children" element={<MyChildren />} />
            <Route path="/children/:studentId/content" element={<MyChildContent />} />
            <Route path="/attendance" element={<MyChildrenAttendance />} />
            <Route path="/announcements" element={<ParentAnnouncements />} />
            <Route path="/reset-password" element={<ChangePassword />} />
          </>
        ) : (
          // Super Admin Routes
          <>
            <Route index element={<DashboardOverview />} />
            <Route path="/schools/:id/edit" element={<EditSchool />} />
            <Route path="/schools/:id" element={<SchoolDetails />} />
            <Route path="/schools" element={<SchoolList />} />
            <Route path="/create-school" element={<CreateSchool />} />
            <Route path="/admins/:id/edit" element={<EditAdmin />} />
            <Route path="/admins" element={<AdminList />} />
            <Route path="/create-admin" element={<CreateAdmin />} />
            <Route path="/users" element={<ViewAllUsers />} />
          </>
        )}
      </Routes>
    </Layout>
  );
};

export default Dashboard;
