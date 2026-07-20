import React, { useState, useEffect } from 'react';
import { FaPlus, FaTrash, FaEdit, FaUserShield, FaChalkboardTeacher, FaUserGraduate, FaUserFriends, FaSearch, FaToggleOn, FaToggleOff } from 'react-icons/fa';
import API_BASE_URL from '../../config';
import { useAuth } from '../../contexts/AuthContext';
import { useModal } from '../../contexts/ModalContext';
import { apiGet, apiPost, apiPut, apiDelete, handleApiError } from '../../utils/apiClient';

const UserManagement = () => {
    const { user: currentUser } = useAuth(); // Rename to avoid conflict
    const { alert, confirm } = useModal();
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterRole, setFilterRole] = useState('ALL');

    // Form State
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [editingUserId, setEditingUserId] = useState(null);
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        full_name: '',
        role: 'STUDENT',
        tenant_id: '' // Will be auto-filled if known, or handled by backend if admin context implies it
    });

    const [adminProfile, setAdminProfile] = useState(null);

    useEffect(() => {
        fetchAdminProfile();
        fetchUsers();
    }, []);

    const fetchAdminProfile = async () => {
        try {
            const token = localStorage.getItem('auth_token');
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setAdminProfile(data);
                // Also set formData tenant_id default
                setFormData(prev => ({ ...prev, tenant_id: data.tenant_id }));
            }
        } catch (error) {
            console.error("Error fetching admin profile:", error);
        }
    };

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const data = await apiGet('/api/v1/ems/users');
            console.log('Fetched users:', data);
            if (Array.isArray(data)) {
                setUsers(data);
            } else {
                console.error('Invalid users data format:', data);
                setUsers([]);
            }
        } catch (error) {
            console.error('Error fetching users:', error);
            const errorInfo = handleApiError(error, { operation: 'fetch users' });
            // Don't show alert on initial load, just log
            if (users.length > 0) {
                await alert(errorInfo.message, errorInfo.title);
            }
            setUsers([]);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateUser = async (e) => {
        e.preventDefault();
        try {
            // Get tenant_id from admin profile or first user
            let tenantId = adminProfile?.tenant_id;
            if (!tenantId && users.length > 0) tenantId = users[0].tenant_id;
            if (!tenantId) {
                // Get default tenant or create one
                const defaultTenant = await apiGet('/api/v1/ems/tenants').catch(() => null);
                if (defaultTenant && defaultTenant.length > 0) {
                    tenantId = defaultTenant[0].id;
                }
            }

            const payload = { ...formData, tenant_id: tenantId || '' };

            await apiPost('/api/v1/ems/users', payload);
            await alert('User created successfully!', 'Success');
            setIsFormOpen(false);
            setFormData({ email: '', password: '', full_name: '', role: 'STUDENT', tenant_id: '' });
            fetchUsers();
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'create user' });
            await alert(errorInfo.message, errorInfo.title);
        }
    };

    const handleEditUser = (user) => {
        setFormData({
            email: user.email,
            full_name: user.full_name || '',
            role: user.role,
            password: '', // Don't pre-fill password
            tenant_id: user.tenant_id || ''
        });
        setIsFormOpen(true);
        setEditingUserId(user.id);
    };

    const handleUpdateUser = async (e) => {
        e.preventDefault();
        try {
            if (editingUserId) {
                // Update existing user
                await apiPut(`/api/v1/ems/users/${editingUserId}`, {
                    email: formData.email,
                    full_name: formData.full_name,
                    role: formData.role
                });
                await alert('User updated successfully!', 'Success');
            } else {
                // Create new user
                await handleCreateUser(e);
                return;
            }
            setIsFormOpen(false);
            setEditingUserId(null);
            setFormData({ email: '', password: '', full_name: '', role: 'STUDENT', tenant_id: '' });
            fetchUsers();
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'update user' });
            await alert(errorInfo.message, errorInfo.title);
        }
    };

    const handleDeleteUser = async (userId, userName) => {
        const result = await confirm(
            `Are you sure you want to delete ${userName || 'this user'}? This action cannot be undone.`,
            'Delete User'
        );
        if (!result) return;

        try {
            await apiDelete(`/api/v1/ems/users/${userId}`);
            await alert('User deleted successfully!', 'Success');
            fetchUsers();
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'delete user' });
            await alert(errorInfo.message, errorInfo.title);
        }
    };

    const handleToggleActive = async (user) => {
        try {
            await apiPut(`/api/v1/ems/users/${user.id}`, {
                is_active: !user.is_active
            });
            await alert(`User ${user.is_active ? 'deactivated' : 'activated'} successfully!`, 'Success');
            fetchUsers();
        } catch (error) {
            const errorInfo = handleApiError(error, { operation: 'toggle user status' });
            await alert(errorInfo.message, errorInfo.title);
        }
    };

    const getRoleIcon = (role) => {
        switch (role) {
            case 'ADMIN': return <FaUserShield className="text-red-400" />;
            case 'TEACHER': return <FaChalkboardTeacher className="text-purple-400" />;
            case 'STUDENT': return <FaUserGraduate className="text-green-400" />;
            case 'PARENT': return <FaUserFriends className="text-orange-400" />;
            default: return <FaUserShield className="text-gray-400" />;
        }
    };

    const filteredUsers = users.filter(u => {
        const matchesSearch = u.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
            u.email?.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesRole = filterRole === 'ALL' || u.role === filterRole;
        return matchesSearch && matchesRole;
    });

    const totalUsers = filteredUsers.length;
    const activeUsers = filteredUsers.filter(u => u.is_active).length;

    // Debug: Log when component renders
    React.useEffect(() => {
        console.log('UserManagement component rendered. Users:', users.length, 'Loading:', loading);
    }, [users.length, loading]);

    return (
        <div className="glass-panel p-6 rounded-2xl border border-white/10">
            {/* Header Section */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
                <div>
                    <h3 className="text-2xl font-bold text-white flex items-center gap-2 mb-2">
                        <FaUserFriends className="text-orange-500" />
                        User Management
                    </h3>
                    <p className="text-gray-400 text-sm">
                        Manage all users in the database. View, edit, activate/deactivate, or delete user accounts.
                    </p>
                </div>
                <button
                    onClick={() => {
                        setEditingUserId(null);
                        setFormData({ email: '', password: '', full_name: '', role: 'STUDENT', tenant_id: '' });
                        setIsFormOpen(true);
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-500 rounded-lg text-white font-medium transition-colors whitespace-nowrap"
                >
                    <FaPlus className="text-sm" /> Add New User
                </button>
            </div>

            {/* Stats Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                <div className="bg-black/40 border border-white/10 rounded-lg p-3">
                    <div className="text-gray-400 text-xs uppercase mb-1">Total Users</div>
                    <div className="text-2xl font-bold text-white">{totalUsers}</div>
                </div>
                <div className="bg-black/40 border border-white/10 rounded-lg p-3">
                    <div className="text-gray-400 text-xs uppercase mb-1">Active</div>
                    <div className="text-2xl font-bold text-green-400">{activeUsers}</div>
                </div>
                <div className="bg-black/40 border border-white/10 rounded-lg p-3">
                    <div className="text-gray-400 text-xs uppercase mb-1">Inactive</div>
                    <div className="text-2xl font-bold text-red-400">{totalUsers - activeUsers}</div>
                </div>
                <div className="bg-black/40 border border-white/10 rounded-lg p-3">
                    <div className="text-gray-400 text-xs uppercase mb-1">Filtered</div>
                    <div className="text-2xl font-bold text-orange-400">{filteredUsers.length}</div>
                </div>
            </div>

            {/* Filters */}
            <div className="flex flex-col sm:flex-row gap-4 mb-6">
                <div className="relative flex-grow">
                    <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                    <input
                        type="text"
                        placeholder="Search users..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full bg-black/40 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-white focus:outline-none focus:border-orange-500"
                    />
                </div>
                <select
                    value={filterRole}
                    onChange={(e) => setFilterRole(e.target.value)}
                    className="bg-black/40 border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-orange-500"
                >
                    <option value="ALL">All Roles</option>
                    <option value="STUDENT">Students</option>
                    <option value="TEACHER">Teachers</option>
                    <option value="PARENT">Parents</option>
                    <option value="ADMIN">Admins</option>
                </select>
            </div>

            {/* Database-Style Table */}
            <div className="overflow-x-auto rounded-lg border border-white/20 bg-black/40">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-black/60 border-b-2 border-white/20">
                        <tr className="text-gray-300 text-xs uppercase tracking-wider font-bold">
                            <th className="py-4 px-4 border-r border-white/10">ID</th>
                            <th className="py-4 px-4 border-r border-white/10">Full Name</th>
                            <th className="py-4 px-4 border-r border-white/10">Email</th>
                            <th className="py-4 px-4 border-r border-white/10">Role</th>
                            <th className="py-4 px-4 border-r border-white/10">Tenant ID</th>
                            <th className="py-4 px-4 border-r border-white/10">Cohort ID</th>
                            <th className="py-4 px-4 border-r border-white/10">Status</th>
                            <th className="py-4 px-4 border-r border-white/10">Created At</th>
                            <th className="py-4 px-4 text-center">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/10">
                        {loading ? (
                            <tr>
                                <td colSpan="9" className="py-12 text-center text-gray-400">
                                    <div className="flex flex-col items-center gap-2">
                                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
                                        <span>Loading users from database...</span>
                                    </div>
                                </td>
                            </tr>
                        ) : filteredUsers.length === 0 ? (
                            <tr>
                                <td colSpan="9" className="py-12 text-center text-gray-400">
                                    No users found in database.
                                </td>
                            </tr>
                        ) : (
                            filteredUsers.map(u => (
                                <tr key={u.id} className="hover:bg-white/5 transition-colors border-b border-white/5">
                                    <td className="py-3 px-4 text-xs font-mono text-gray-400 border-r border-white/10">
                                        {u.id.substring(0, 8)}...
                                    </td>
                                    <td className="py-3 px-4 font-medium text-white border-r border-white/10">
                                        {u.full_name || <span className="text-gray-500 italic">NULL</span>}
                                    </td>
                                    <td className="py-3 px-4 text-gray-300 text-sm border-r border-white/10">
                                        {u.email}
                                    </td>
                                    <td className="py-3 px-4 border-r border-white/10">
                                        <div className="flex items-center gap-2 text-sm">
                                            {getRoleIcon(u.role)}
                                            <span className="capitalize font-medium text-gray-300">{u.role.toLowerCase()}</span>
                                        </div>
                                    </td>
                                    <td className="py-3 px-4 text-xs font-mono text-gray-400 border-r border-white/10">
                                        {u.tenant_id ? (
                                            <span className="text-gray-400">{u.tenant_id.substring(0, 8)}...</span>
                                        ) : (
                                            <span className="text-gray-600 italic">NULL</span>
                                        )}
                                    </td>
                                    <td className="py-3 px-4 text-xs font-mono text-gray-400 border-r border-white/10">
                                        {u.cohort_id ? (
                                            <span className="text-gray-400">{u.cohort_id.substring(0, 8)}...</span>
                                        ) : (
                                            <span className="text-gray-600 italic">NULL</span>
                                        )}
                                    </td>
                                    <td className="py-3 px-4 border-r border-white/10">
                                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                                            u.is_active 
                                                ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                                                : 'bg-red-500/20 text-red-400 border border-red-500/30'
                                        }`}>
                                            {u.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                    </td>
                                    <td className="py-3 px-4 text-xs text-gray-400 border-r border-white/10">
                                        {u.created_at ? new Date(u.created_at).toLocaleDateString() : 'N/A'}
                                    </td>
                                    <td className="py-3 px-4">
                                        <div className="flex items-center justify-center gap-2">
                                            <button
                                                onClick={() => handleToggleActive(u)}
                                                className="text-gray-400 hover:text-orange-400 transition-colors p-2 rounded hover:bg-white/10"
                                                title={u.is_active ? 'Deactivate User' : 'Activate User'}
                                            >
                                                {u.is_active ? (
                                                    <FaToggleOn className="text-green-400 text-lg" />
                                                ) : (
                                                    <FaToggleOff className="text-red-400 text-lg" />
                                                )}
                                            </button>
                                            <button
                                                onClick={() => handleEditUser(u)}
                                                className="text-gray-400 hover:text-blue-400 transition-colors p-2 rounded hover:bg-white/10"
                                                title="Edit User"
                                            >
                                                <FaEdit />
                                            </button>
                                            <button
                                                onClick={() => handleDeleteUser(u.id, u.full_name)}
                                                className="text-gray-400 hover:text-red-400 transition-colors p-2 rounded hover:bg-white/10"
                                                title="Delete User"
                                            >
                                                <FaTrash />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>

            {/* Modal Form */}
            {isFormOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                    <div className="bg-gray-900 border border-white/10 rounded-2xl w-full max-w-md p-6 relative animate-fade-in-up">
                        <h3 className="text-xl font-bold text-white mb-4">
                            {editingUserId ? 'Edit User' : 'Create New User'}
                        </h3>

                        <form onSubmit={editingUserId ? handleUpdateUser : handleCreateUser} className="space-y-4">
                            <div>
                                <label className="block text-xs font-bold text-gray-400 uppercase mb-1">Full Name</label>
                                <input
                                    type="text" required
                                    value={formData.full_name}
                                    onChange={e => setFormData({ ...formData, full_name: e.target.value })}
                                    className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-orange-500 outline-none"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-gray-400 uppercase mb-1">Email</label>
                                <input
                                    type="email" required
                                    value={formData.email}
                                    onChange={e => setFormData({ ...formData, email: e.target.value })}
                                    className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-orange-500 outline-none"
                                />
                            </div>
                            {!editingUserId && (
                                <div>
                                    <label className="block text-xs font-bold text-gray-400 uppercase mb-1">Password</label>
                                    <input
                                        type="password" required
                                        value={formData.password}
                                        onChange={e => setFormData({ ...formData, password: e.target.value })}
                                        className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-orange-500 outline-none"
                                    />
                                </div>
                            )}
                            <div>
                                <label className="block text-xs font-bold text-gray-400 uppercase mb-1">Role</label>
                                <select
                                    value={formData.role}
                                    onChange={e => setFormData({ ...formData, role: e.target.value })}
                                    className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-orange-500 outline-none"
                                >
                                    <option value="STUDENT">Student</option>
                                    <option value="TEACHER">Teacher</option>
                                    <option value="PARENT">Parent</option>
                                    <option value="ADMIN">Admin</option>
                                </select>
                            </div>

                            <div className="flex gap-3 mt-6">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setIsFormOpen(false);
                                        setEditingUserId(null);
                                        setFormData({ email: '', password: '', full_name: '', role: 'STUDENT', tenant_id: '' });
                                    }}
                                    className="flex-1 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white font-medium transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 py-2 rounded-lg bg-orange-600 hover:bg-orange-500 text-white font-medium transition-colors"
                                >
                                    {editingUserId ? 'Update User' : 'Create User'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default UserManagement;
