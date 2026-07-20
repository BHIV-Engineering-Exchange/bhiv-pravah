import { useQuery } from '@tanstack/react-query';
import { dashboardService } from '../services';

// Query keys
export const dashboardKeys = {
  all: ['dashboard'],
  stats: () => [...dashboardKeys.all, 'stats'],
  revenueChart: () => [...dashboardKeys.all, 'revenue-chart'],
  expenseChart: () => [...dashboardKeys.all, 'expense-chart'],
  recentInvoices: () => [...dashboardKeys.all, 'recent-invoices'],
  recentExpenses: () => [...dashboardKeys.all, 'recent-expenses'],
  pendingApprovals: () => [...dashboardKeys.all, 'pending-approvals'],
};

// Dashboard stats
export const useDashboardStats = () => {
  return useQuery({
    queryKey: dashboardKeys.stats(),
    queryFn: () => dashboardService.getStats().then((res) => res.data),
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: true,
  });
};

// Revenue chart data
export const useRevenueChart = (params = {}) => {
  return useQuery({
    queryKey: [...dashboardKeys.revenueChart(), params],
    queryFn: () => dashboardService.getRevenueChart(params).then((res) => res.data),
    staleTime: 5 * 60 * 1000,
  });
};

// Expense chart data
export const useExpenseChart = (params = {}) => {
  return useQuery({
    queryKey: [...dashboardKeys.expenseChart(), params],
    queryFn: () => dashboardService.getExpenseChart(params).then((res) => res.data),
    staleTime: 5 * 60 * 1000,
  });
};

// Recent invoices
export const useRecentInvoices = () => {
  return useQuery({
    queryKey: dashboardKeys.recentInvoices(),
    queryFn: () => dashboardService.getRecentInvoices().then((res) => res.data),
    staleTime: 2 * 60 * 1000,
  });
};

// Recent expenses
export const useRecentExpenses = () => {
  return useQuery({
    queryKey: dashboardKeys.recentExpenses(),
    queryFn: () => dashboardService.getRecentExpenses().then((res) => res.data),
    staleTime: 2 * 60 * 1000,
  });
};

// Pending approvals
export const usePendingApprovals = () => {
  return useQuery({
    queryKey: dashboardKeys.pendingApprovals(),
    queryFn: () => dashboardService.getPendingApprovals().then((res) => res.data),
    staleTime: 1 * 60 * 1000, // 1 minute
    refetchOnWindowFocus: true,
  });
};
