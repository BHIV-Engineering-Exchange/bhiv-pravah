import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/auth-context';
import { toast } from './use-toast';
import api from '../lib/api';

export const useLeave = () => {
  const { user } = useAuth();
  const [leaves, setLeaves] = useState([]);
  const [leaveStats, setLeaveStats] = useState(null);
  const [pendingLeaves, setPendingLeaves] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Submit leave request
  const submitLeaveRequest = useCallback(async (leaveData) => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/leave/request', leaveData);
      
      if (response.data.success) {
        toast({
          title: "Success",
          description: "Leave request submitted successfully",
          variant: "default"
        });
        
        // Refresh leave history
        await fetchLeaveHistory();
        return true;
      } else {
        throw new Error(response.data.error || 'Failed to submit leave request');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to submit leave request';
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch user's leave history
  const fetchLeaveHistory = useCallback(async (userId = user?.id, options = {}) => {
    if (!userId) return;

    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (options.status) params.append('status', options.status);
      if (options.year) params.append('year', options.year);
      if (options.page) params.append('page', options.page);
      if (options.limit) params.append('limit', options.limit);

      const response = await api.get(`/leave/user/${userId}?${params}`);
      
      if (response.data.success) {
        setLeaves(response.data.data.leaves);
        setLeaveStats(response.data.data.stats);
        return response.data.data;
      } else {
        throw new Error(response.data.error || 'Failed to fetch leave history');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to fetch leave history';
      setError(errorMessage);
      
      // Don't show toast for 404 errors (no leave records)
      if (err.response?.status !== 404) {
        toast({
          title: "Error",
          description: errorMessage,
          variant: "destructive"
        });
      }
      return null;
    } finally {
      setLoading(false);
    }
  }, [user?.id]);

  // Fetch pending leave requests (admin/manager only)
  const fetchPendingLeaves = useCallback(async (options = {}) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (options.department) params.append('department', options.department);
      if (options.priority) params.append('priority', options.priority);
      if (options.page) params.append('page', options.page);
      if (options.limit) params.append('limit', options.limit);

      const response = await api.get(`/leave/pending?${params}`);
      
      if (response.data.success) {
        setPendingLeaves(response.data.data.pendingLeaves);
        return response.data.data;
      } else {
        throw new Error(response.data.error || 'Failed to fetch pending leaves');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to fetch pending leaves';
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Approve leave request (admin/manager only)
  const approveLeaveRequest = useCallback(async (leaveId, notes = '') => {
    setLoading(true);

    try {
      const response = await api.put(`/leave/${leaveId}/approve`, { notes });
      
      if (response.data.success) {
        toast({
          title: "Success",
          description: "Leave request approved successfully",
          variant: "default"
        });
        
        // Refresh pending leaves
        await fetchPendingLeaves();
        return true;
      } else {
        throw new Error(response.data.error || 'Failed to approve leave request');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to approve leave request';
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
      return false;
    } finally {
      setLoading(false);
    }
  }, [fetchPendingLeaves]);

  // Reject leave request (admin/manager only)
  const rejectLeaveRequest = useCallback(async (leaveId, rejectionReason) => {
    if (!rejectionReason) {
      toast({
        title: "Error",
        description: "Rejection reason is required",
        variant: "destructive"
      });
      return false;
    }

    setLoading(true);

    try {
      const response = await api.put(`/leave/${leaveId}/reject`, { rejectionReason });
      
      if (response.data.success) {
        toast({
          title: "Success",
          description: "Leave request rejected",
          variant: "default"
        });
        
        // Refresh pending leaves
        await fetchPendingLeaves();
        return true;
      } else {
        throw new Error(response.data.error || 'Failed to reject leave request');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to reject leave request';
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
      return false;
    } finally {
      setLoading(false);
    }
  }, [fetchPendingLeaves]);

  // Cancel leave request (employee only)
  const cancelLeaveRequest = useCallback(async (leaveId, reason = 'Cancelled by employee') => {
    setLoading(true);

    try {
      const response = await api.put(`/leave/${leaveId}/cancel`, { reason });
      
      if (response.data.success) {
        toast({
          title: "Success",
          description: "Leave request cancelled successfully",
          variant: "default"
        });
        
        // Refresh leave history
        await fetchLeaveHistory();
        return true;
      } else {
        throw new Error(response.data.error || 'Failed to cancel leave request');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to cancel leave request';
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
      return false;
    } finally {
      setLoading(false);
    }
  }, [fetchLeaveHistory]);

  // Fetch leave analytics (admin/manager only)
  const fetchLeaveAnalytics = useCallback(async (options = {}) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (options.year) params.append('year', options.year);
      if (options.department) params.append('department', options.department);

      const response = await api.get(`/leave/analytics?${params}`);
      
      if (response.data.success) {
        return response.data.data;
      } else {
        throw new Error(response.data.error || 'Failed to fetch leave analytics');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to fetch leave analytics';
      setError(errorMessage);
      toast({
        title: "Error",
        description: errorMessage,
        variant: "destructive"
      });
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Calculate leave balance
  const calculateLeaveBalance = useCallback((leaveType = 'all') => {
    if (!leaveStats) return 0;

    const currentYear = new Date().getFullYear();
    const yearlyAllowance = {
      'Sick': 12,
      'Vacation': 21,
      'Personal': 5,
      'Emergency': 3,
      'Maternity': 90,
      'Paternity': 15
    };

    if (leaveType === 'all') {
      const totalAllowance = Object.values(yearlyAllowance).reduce((sum, days) => sum + days, 0);
      return totalAllowance - (leaveStats.totalDays || 0);
    }

    const allowance = yearlyAllowance[leaveType] || 0;
    const used = leaveStats.byType?.[leaveType] || 0;
    return allowance - used;
  }, [leaveStats]);

  // Auto-fetch leave history on mount
  useEffect(() => {
    if (user?.id) {
      fetchLeaveHistory();
    }
  }, [user?.id, fetchLeaveHistory]);

  return {
    // State
    leaves,
    leaveStats,
    pendingLeaves,
    loading,
    error,

    // Actions
    submitLeaveRequest,
    fetchLeaveHistory,
    fetchPendingLeaves,
    approveLeaveRequest,
    rejectLeaveRequest,
    cancelLeaveRequest,
    fetchLeaveAnalytics,

    // Utilities
    calculateLeaveBalance
  };
};

// Hook for leave management with real-time updates
export const useLeaveManagement = (options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [refreshInterval, setRefreshInterval] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await api.get('/leave/pending', {
        params: options
      });
      
      if (response.data.success) {
        setData(response.data.data);
        return response.data.data;
      } else {
        throw new Error(response.data.error || 'Failed to fetch leave data');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to fetch leave data';
      setError(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  }, [options]);

  // Auto-refresh functionality
  const startAutoRefresh = useCallback((interval = 60000) => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
    }
    
    const id = setInterval(fetchData, interval);
    setRefreshInterval(id);
    
    return () => clearInterval(id);
  }, [fetchData, refreshInterval]);

  const stopAutoRefresh = useCallback(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval);
      setRefreshInterval(null);
    }
  }, [refreshInterval]);

  // Initial fetch
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    };
  }, [refreshInterval]);

  return {
    data,
    loading,
    error,
    refresh: fetchData,
    startAutoRefresh,
    stopAutoRefresh,
    isAutoRefreshing: !!refreshInterval
  };
};
