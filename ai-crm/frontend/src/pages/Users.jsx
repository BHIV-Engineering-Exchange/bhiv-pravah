import React, { useState, useEffect, useCallback } from 'react';
import { 
  UsersRound, Plus, Search, Filter, RefreshCw, Edit, Trash2,
  Shield, UserCheck, Mail, Calendar, AlertTriangle, CheckCircle
} from 'lucide-react';
import Card, { CardHeader, CardTitle, CardContent } from '../components/common/ui/Card';
import MetricCard from '../components/common/charts/MetricCard';
import Button from '../components/common/ui/Button';
import Input from '../components/common/forms/Input';
import Badge from '../components/common/ui/Badge';
import Alert from '../components/common/ui/Alert';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../components/common/ui/Table';
import { LoadingSpinner } from '../components/common/ui/Spinner';
import { Modal, ModalFooter } from '../components/common/ui/Modal';
import Select from '../components/common/forms/Select';
import { userAPI } from '../services/api/userAPI';
import { formatDate } from '@/utils/dateUtils';

export const Users = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [users, setUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [metrics, setMetrics] = useState({
    totalUsers: 0,
    activeUsers: 0,
    adminUsers: 0,
    operatorUsers: 0,
  });

  // Form state
  const [userForm, setUserForm] = useState({
    username: '',
    email: '',
    password: '',
    role: 'operator',
  });

  // Fetch users
  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await userAPI.getUsers();
      const usersData = response.data?.users || response.data || [];
      
      setUsers(usersData.map(user => ({
        id: user.user_id || user.id || user.username,
        username: user.username || user.email?.split('@')[0] || 'Unknown',
        email: user.email || '',
        role: user.role || 'operator',
        status: user.is_active !== false ? 'active' : 'inactive',
        lastLogin: user.last_login ? new Date(user.last_login) : null,
        createdAt: user.created_at ? new Date(user.created_at) : new Date(),
      })));

      // Calculate metrics
      const totalUsers = usersData.length;
      const activeUsers = usersData.filter(u => u.is_active !== false).length;
      const adminUsers = usersData.filter(u => (u.role || 'operator') === 'admin').length;
      const operatorUsers = usersData.filter(u => (u.role || 'operator') === 'operator').length;

      setMetrics({
        totalUsers,
        activeUsers,
        adminUsers,
        operatorUsers,
      });

    } catch (err) {
      console.error('Error fetching users:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load users');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUsers();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchUsers();
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchUsers]);

  const handleCreateUser = async () => {
    try {
      setLoading(true);
      setError(null);
      // Map username to name for MongoDB backend and map roles
      const roleMap = {
        'operator': 'manager',
        'user': 'customer',
        'admin': 'admin'
      };
      const userData = {
        name: userForm.username,
        email: userForm.email,
        password: userForm.password,
        role: roleMap[userForm.role] || 'customer'
      };
      await userAPI.createUser(userData);
      setSuccess('User created successfully');
      setShowAddModal(false);
      setUserForm({ username: '', email: '', password: '', role: 'operator' });
      setTimeout(() => {
        fetchUsers();
        setSuccess(null);
      }, 1000);
    } catch (err) {
      setError(err.response?.data?.message || err.message || 'Failed to create user');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateUser = async () => {
    if (!selectedUser) return;
    try {
      setLoading(true);
      setError(null);
      // Map username to name for MongoDB backend and map roles
      const roleMap = {
        'operator': 'manager',
        'user': 'customer',
        'admin': 'admin'
      };
      const userData = {
        ...(userForm.username && { name: userForm.username }),
        ...(userForm.email && { email: userForm.email }),
        ...(userForm.password && { password: userForm.password }),
        ...(userForm.role && { role: roleMap[userForm.role] || userForm.role })
      };
      await userAPI.updateUser(selectedUser.id, userData);
      setSuccess('User updated successfully');
      setShowEditModal(false);
      setSelectedUser(null);
      setUserForm({ username: '', email: '', password: '', role: 'operator' });
      setTimeout(() => {
        fetchUsers();
        setSuccess(null);
      }, 1000);
    } catch (err) {
      setError(err.response?.data?.message || err.message || 'Failed to update user');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try {
      setLoading(true);
      setError(null);
      await userAPI.deleteUser(userId);
      setSuccess('User deleted successfully');
      setTimeout(() => {
        fetchUsers();
        setSuccess(null);
      }, 1000);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to delete user');
    } finally {
      setLoading(false);
    }
  };

  const handleEditUser = (user) => {
    setSelectedUser(user);
    setUserForm({
      username: user.username,
      email: user.email,
      password: '',
      role: user.role,
    });
    setShowEditModal(true);
  };

  const getRoleVariant = (role) => {
    const variants = {
      admin: 'destructive',
      operator: 'primary',
      user: 'secondary',
    };
    return variants[role] || 'default';
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch = !searchQuery || 
      user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
      user.email.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesRole = roleFilter === 'all' || user.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-heading font-bold tracking-tight">User Management</h1>
          <p className="text-muted-foreground mt-1">
            Manage system users, roles, and permissions
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchUsers}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button onClick={() => {
            setUserForm({ username: '', email: '', password: '', role: 'operator' });
            setShowAddModal(true);
          }}>
            <Plus className="h-4 w-4 mr-2" />
            Add User
          </Button>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <Alert variant="destructive" onClose={() => setError(null)}>
          <AlertTriangle className="h-4 w-4 mr-2" />
          {error}
        </Alert>
      )}
      {success && (
        <Alert variant="success" onClose={() => setSuccess(null)}>
          <CheckCircle className="h-4 w-4 mr-2" />
          {success}
        </Alert>
      )}

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Users"
          value={metrics.totalUsers.toLocaleString()}
          icon={UsersRound}
          variant="primary"
        />
        <MetricCard
          title="Active Users"
          value={metrics.activeUsers.toLocaleString()}
          icon={UserCheck}
          variant="success"
        />
        <MetricCard
          title="Admin Users"
          value={metrics.adminUsers.toLocaleString()}
          icon={Shield}
          variant="destructive"
        />
        <MetricCard
          title="Operator Users"
          value={metrics.operatorUsers.toLocaleString()}
          icon={UsersRound}
          variant="secondary"
        />
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <Input
              placeholder="Search users..."
              icon={Search}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1"
            />
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="px-4 py-2 rounded-lg border border-border bg-background"
            >
              <option value="all">All Roles</option>
              <option value="admin">Admin</option>
              <option value="operator">Operator</option>
              <option value="user">User</option>
            </select>
            <Button variant="outline">
              <Filter className="h-4 w-4 mr-2" />
              More Filters
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardHeader>
          <CardTitle>Users ({filteredUsers.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <LoadingSpinner text="Loading users..." />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Username</TableHead>
                  <TableHead>Email</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Login</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredUsers.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell className="font-medium">{user.username}</TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Mail className="h-4 w-4 text-muted-foreground" />
                        {user.email}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getRoleVariant(user.role)}>
                        {user.role}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={user.status === 'active' ? 'success' : 'warning'}>
                        {user.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {user.lastLogin ? formatDate(user.lastLogin) : 'Never'}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {formatDate(user.createdAt)}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEditUser(user)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteUser(user.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
                {filteredUsers.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                      No users found
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Add User Modal */}
      <Modal
        isOpen={showAddModal}
        title="Add New User"
        onClose={() => setShowAddModal(false)}
      >
        <div className="space-y-4">
          <Input
            label="Username"
            value={userForm.username}
            onChange={(e) => setUserForm({ ...userForm, username: e.target.value })}
            placeholder="Enter username"
          />
          <Input
            label="Email"
            type="email"
            value={userForm.email}
            onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
            placeholder="Enter email"
          />
          <Input
            label="Password"
            type="password"
            value={userForm.password}
            onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
            placeholder="Enter password"
          />
          <Select
            label="Role"
            value={userForm.role}
            onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}
            options={[
              { value: 'admin', label: 'Admin' },
              { value: 'operator', label: 'Manager' },
              { value: 'user', label: 'Customer' },
            ]}
          />
        </div>
        <ModalFooter>
          <Button variant="outline" onClick={() => setShowAddModal(false)}>Cancel</Button>
          <Button onClick={handleCreateUser}>Create User</Button>
        </ModalFooter>
      </Modal>

      {/* Edit User Modal */}
      <Modal
        isOpen={showEditModal}
        title="Edit User"
        onClose={() => {
          setShowEditModal(false);
          setSelectedUser(null);
        }}
      >
        <div className="space-y-4">
          <Input
            label="Username"
            value={userForm.username}
            onChange={(e) => setUserForm({ ...userForm, username: e.target.value })}
            placeholder="Enter username"
          />
          <Input
            label="Email"
            type="email"
            value={userForm.email}
            onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
            placeholder="Enter email"
          />
          <Input
            label="Password (leave blank to keep current)"
            type="password"
            value={userForm.password}
            onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
            placeholder="Enter new password (optional)"
          />
          <Select
            label="Role"
            value={userForm.role}
            onChange={(e) => setUserForm({ ...userForm, role: e.target.value })}
            options={[
              { value: 'admin', label: 'Admin' },
              { value: 'operator', label: 'Manager' },
              { value: 'user', label: 'Customer' },
            ]}
          />
        </div>
        <ModalFooter>
          <Button variant="outline" onClick={() => {
            setShowEditModal(false);
            setSelectedUser(null);
          }}>Cancel</Button>
          <Button onClick={handleUpdateUser}>Update User</Button>
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default Users;
