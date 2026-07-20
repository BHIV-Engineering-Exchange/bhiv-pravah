import React, { useState, useEffect } from 'react';
import { dashboardAPI, schoolsAPI } from '../services/api';

const ViewAllUsers = () => {
  const [users, setUsers] = useState([]);
  const [schools, setSchools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [schoolFilter, setSchoolFilter] = useState('');

  useEffect(() => { fetchData(); }, [search, roleFilter, schoolFilter]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const usersData = await dashboardAPI.getUsers(search || null, roleFilter || null, schoolFilter ? parseInt(schoolFilter) : null);
      const { adminsAPI, schoolsAPI } = await import('../services/api');
      const allAdmins = await adminsAPI.getAll();
      const schoolIds = [...new Set(allAdmins.map(admin => admin.school_id).filter(id => id !== null))];
      const schoolsPromises = schoolIds.map(schoolId => schoolsAPI.getById(schoolId).catch(() => null));
      const schoolsArray = (await Promise.all(schoolsPromises)).filter(school => school !== null);
      setUsers(usersData);
      setSchools(schoolsArray);
      setError('');
    } catch (err) {
      setError('Failed to load users. Please try again.');
      console.error('Error fetching users:', err);
    } finally { setLoading(false); }
  };

  const getSchoolName = (schoolId) => {
    if (!schoolId) return 'N/A';
    const school = schools.find((s) => s.id === schoolId);
    return school ? school.name : `School ID: ${schoolId}`;
  };

  const getRoleBadge = (role) => {
    const badges = {
      SUPER_ADMIN: 'badge-pink',
      ADMIN: 'badge-blue',
      TEACHER: 'badge-green',
      STUDENT: 'badge-amber',
      PARENT: 'badge-pink',
    };
    return badges[role] || 'badge-blue';
  };

  if (loading) {
    return (<div className="card-dark p-6"><div className="text-center py-8"><div className="spinner"></div><p className="mt-4 text-gray-400">Loading users...</p></div></div>);
  }

  return (
    <div className="card-dark overflow-hidden animate-fade-in">
      <div className="px-6 py-4 border-b border-[#2A2A3E]">
        <h2 className="text-lg font-semibold text-white mb-4">All Users</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label htmlFor="search" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Search</label>
            <input type="text" id="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by name or email..." className="input-dark text-sm !py-2" />
          </div>
          <div>
            <label htmlFor="role-filter" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Filter by Role</label>
            <select id="role-filter" value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} className="input-dark text-sm !py-2">
              <option value="">All Roles</option>
              <option value="SUPER_ADMIN">Super Admin</option>
              <option value="ADMIN">Admin</option>
              <option value="TEACHER">Teacher</option>
              <option value="STUDENT">Student</option>
              <option value="PARENT">Parent</option>
            </select>
          </div>
          <div>
            <label htmlFor="school-filter" className="block text-xs font-semibold text-gray-400 mb-2 uppercase tracking-wider">Filter by School</label>
            <select id="school-filter" value={schoolFilter} onChange={(e) => setSchoolFilter(e.target.value)} className="input-dark text-sm !py-2">
              <option value="">All Schools</option>
              {schools.map((school) => (<option key={school.id} value={school.id}>{school.name}</option>))}
            </select>
          </div>
        </div>
      </div>

      {error && (<div className="error-box m-6"><p>{error}</p></div>)}

      {users.length === 0 ? (
        <div className="p-8 text-center text-gray-500"><p>No users found matching your filters.</p></div>
      ) : (
        <div className="overflow-x-auto">
          <table className="table-dark">
            <thead>
              <tr><th>User ID</th><th>Name</th><th>Email</th><th>Role</th><th>School (School ID)</th></tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td><span className="badge badge-green">ID: {user.id}</span></td>
                  <td className="font-medium text-white">{user.name}</td>
                  <td>{user.email}</td>
                  <td><span className={`badge ${getRoleBadge(user.role)}`}>{user.role}</span></td>
                  <td>
                    {user.school_id ? (
                      <span>
                        <span className="font-medium text-gray-200">{getSchoolName(user.school_id)}</span>
                        <span className="badge badge-green ml-2">ID: {user.school_id}</span>
                      </span>
                    ) : 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="px-6 py-4 border-t border-[#2A2A3E] bg-[#16162A]">
        <p className="text-sm text-gray-500">
          Showing {users.length} user{users.length !== 1 ? 's' : ''}
          {search && ` matching "${search}"`}
          {roleFilter && ` with role "${roleFilter}"`}
          {schoolFilter && ` in selected school`}
        </p>
      </div>
    </div>
  );
};

export default ViewAllUsers;
