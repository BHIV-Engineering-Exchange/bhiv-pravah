import React, { useState, useEffect } from 'react';
import { schoolAdminAPI } from '../../services/api';
import {
  BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, LineChart, Line
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658'];

const Analytics = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const data = await schoolAdminAPI.getAnalytics();
      setAnalytics(data);
      setError('');
    } catch (err) {
      setError('Failed to load analytics. Please try again.');
      console.error('Error fetching analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="spinner spinner-lg"></div>
        <p className="mt-4 text-gray-400">Loading analytics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-box p-6">
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  if (!analytics) {
    return <div>No analytics data available</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Analytics & Insights</h1>
        <p className="text-gray-400 mt-2">Deep insights into teachers, students, parents, and their relationships</p>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card-dark p-6 border-l-4 border-blue-500">
          <p className="text-sm font-medium text-gray-400">Total Teachers</p>
          <p className="text-3xl font-bold text-white mt-2">{analytics.total_teachers}</p>
        </div>
        <div className="card-dark p-6 border-l-4 border-green-500">
          <p className="text-sm font-medium text-gray-400">Total Students</p>
          <p className="text-3xl font-bold text-white mt-2">{analytics.total_students}</p>
        </div>
        <div className="card-dark p-6 border-l-4 border-purple-500">
          <p className="text-sm font-medium text-gray-400">Total Parents</p>
          <p className="text-3xl font-bold text-white mt-2">{analytics.total_parents}</p>
        </div>
        <div className="card-dark p-6 border-l-4 border-yellow-500">
          <p className="text-sm font-medium text-gray-400">Total Classes</p>
          <p className="text-3xl font-bold text-white mt-2">{analytics.total_classes}</p>
        </div>
      </div>

      {/* Teacher Analytics */}
      <div className="card-dark p-6">
        <h2 className="text-xl font-bold text-white mb-4">Teacher Analytics</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Teacher Workload */}
          <div>
            <h3 className="text-lg font-semibold text-gray-300 mb-3">Teacher Workload (Classes per Teacher)</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics.teacher_workload}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="teacher_name" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="total_classes" fill="#8884d8" name="Classes" />
                <Bar dataKey="total_students" fill="#82ca9d" name="Students" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Teachers by Subject */}
          <div>
            <h3 className="text-lg font-semibold text-gray-300 mb-3">Teachers by Subject</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analytics.teachers_by_subject}
                  dataKey="count"
                  nameKey="subject"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label
                >
                  {analytics.teachers_by_subject.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Student Analytics */}
      <div className="card-dark p-6">
        <h2 className="text-xl font-bold text-white mb-4">Student Analytics</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Students by Grade */}
          <div>
            <h3 className="text-lg font-semibold text-gray-300 mb-3">Students Distribution by Grade</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics.students_by_grade}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="grade" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="student_count" fill="#8884d8" name="Students" />
                <Bar dataKey="teacher_count" fill="#82ca9d" name="Teachers" />
                <Bar dataKey="class_count" fill="#ffc658" name="Classes" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Students by Subject */}
          <div>
            <h3 className="text-lg font-semibold text-gray-300 mb-3">Students Distribution by Subject</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics.students_by_subject}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="subject_name" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="student_count" fill="#0088FE" name="Students" />
                <Bar dataKey="teacher_count" fill="#00C49F" name="Teachers" />
                <Bar dataKey="class_count" fill="#FFBB28" name="Classes" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Parent Analytics */}
      <div className="card-dark p-6">
        <h2 className="text-xl font-bold text-white mb-4">Parent Analytics</h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Parents by Children Count */}
          <div>
            <h3 className="text-lg font-semibold text-gray-300 mb-3">Parents by Number of Children</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analytics.parents_by_children_count}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="children_count" label={{ value: 'Number of Children', position: 'insideBottom', offset: -5 }} />
                <YAxis label={{ value: 'Number of Parents', angle: -90, position: 'insideLeft' }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="parent_count" fill="#FF8042" name="Parents" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Linked vs Unlinked Students */}
          <div>
            <h3 className="text-lg font-semibold text-gray-300 mb-3">Student-Parent Linking Status</h3>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={[
                    { name: 'Linked Students', value: analytics.linked_students },
                    { name: 'Unlinked Students', value: analytics.unlinked_students }
                  ]}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label
                >
                  <Cell fill="#00C49F" />
                  <Cell fill="#FF8042" />
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Detailed Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Teacher Workload Table */}
        <div className="card-dark p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Teacher Workload Details</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#16162A]">
                <tr>
                  <th className="px-4 py-2 text-left text-white font-semibold">Teacher</th>
                  <th className="px-4 py-2 text-left text-white font-semibold">Subject</th>
                  <th className="px-4 py-2 text-center text-white font-semibold">Classes</th>
                  <th className="px-4 py-2 text-center text-white font-semibold">Students</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2A2A3E]">
                {analytics.teacher_workload.map((teacher) => (
                  <tr key={teacher.teacher_id}>
                    <td className="px-4 py-2 text-white">{teacher.teacher_name}</td>
                    <td className="px-4 py-2 text-white">{teacher.subject || '-'}</td>
                    <td className="px-4 py-2 text-center text-white">{teacher.total_classes}</td>
                    <td className="px-4 py-2 text-center text-white">{teacher.total_students}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Grade Distribution Table */}
        <div className="card-dark p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Grade Distribution Details</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-[#16162A]">
                <tr>
                  <th className="px-4 py-2 text-left text-white font-semibold">Grade</th>
                  <th className="px-4 py-2 text-center text-white font-semibold">Students</th>
                  <th className="px-4 py-2 text-center text-white font-semibold">Teachers</th>
                  <th className="px-4 py-2 text-center text-white font-semibold">Classes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#2A2A3E]">
                {analytics.students_by_grade.map((grade, idx) => (
                  <tr key={idx}>
                    <td className="px-4 py-2 font-medium text-white">{grade.grade}</td>
                    <td className="px-4 py-2 text-center text-white">{grade.student_count}</td>
                    <td className="px-4 py-2 text-center text-white">{grade.teacher_count}</td>
                    <td className="px-4 py-2 text-center text-white">{grade.class_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Parent-Student Relations */}
      <div className="card-dark p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Parent-Student Relations</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-[#16162A]">
              <tr>
                <th className="px-4 py-2 text-left text-white font-semibold">Parent Name</th>
                <th className="px-4 py-2 text-left text-white font-semibold">Parent Email</th>
                <th className="px-4 py-2 text-center text-white font-semibold">Children Count</th>
                <th className="px-4 py-2 text-left text-white font-semibold">Children</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#2A2A3E]">
              {analytics.parent_student_relations.map((relation) => (
                <tr key={relation.parent_id}>
                  <td className="px-4 py-2 font-medium text-white">{relation.parent_name}</td>
                  <td className="px-4 py-2 text-white">{relation.parent_email}</td>
                  <td className="px-4 py-2 text-center text-white">{relation.children_count}</td>
                  <td className="px-4 py-2">
                    {relation.children.map((child, idx) => (
                      <span key={idx} className="inline-block mr-2 mb-1 px-2 py-1 bg-accent-blue/15 text-accent-blue rounded text-xs">
                        {child.name} (Grade {child.grade || 'N/A'})
                      </span>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
