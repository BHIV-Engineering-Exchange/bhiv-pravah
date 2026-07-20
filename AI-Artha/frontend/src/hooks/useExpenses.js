import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { expenseService } from '../services';
import toast from 'react-hot-toast';

// Query keys
export const expenseKeys = {
  all: ['expenses'],
  lists: () => [...expenseKeys.all, 'list'],
  list: (filters) => [...expenseKeys.lists(), filters],
  details: () => [...expenseKeys.all, 'detail'],
  detail: (id) => [...expenseKeys.details(), id],
  pending: () => [...expenseKeys.all, 'pending'],
};

// Fetch all expenses
export const useExpenses = (params = {}) => {
  return useQuery({
    queryKey: expenseKeys.list(params),
    queryFn: () => expenseService.getAll(params).then((res) => res.data),
    staleTime: 5 * 60 * 1000,
  });
};

// Fetch single expense
export const useExpense = (id) => {
  return useQuery({
    queryKey: expenseKeys.detail(id),
    queryFn: () => expenseService.getById(id).then((res) => res.data),
    enabled: !!id,
  });
};

// Fetch pending expenses
export const usePendingExpenses = () => {
  return useQuery({
    queryKey: expenseKeys.pending(),
    queryFn: () => expenseService.getPending().then((res) => res.data),
    staleTime: 2 * 60 * 1000,
  });
};

// Create expense
export const useCreateExpense = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: expenseService.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: expenseKeys.lists() });
      toast.success('Expense created successfully');
    },
    onError: (error) => {
      toast.error(error.response?.data?.message || 'Failed to create expense');
    },
  });
};

// Update expense
export const useUpdateExpense = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }) => expenseService.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: expenseKeys.lists() });
      queryClient.invalidateQueries({ queryKey: expenseKeys.detail(id) });
      toast.success('Expense updated successfully');
    },
    onError: (error) => {
      toast.error(error.response?.data?.message || 'Failed to update expense');
    },
  });
};

// Delete expense
export const useDeleteExpense = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: expenseService.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: expenseKeys.lists() });
      toast.success('Expense deleted successfully');
    },
    onError: (error) => {
      toast.error(error.response?.data?.message || 'Failed to delete expense');
    },
  });
};

// Approve expense
export const useApproveExpense = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: expenseService.approve,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: expenseKeys.lists() });
      queryClient.invalidateQueries({ queryKey: expenseKeys.pending() });
      toast.success('Expense approved');
    },
    onError: (error) => {
      toast.error(error.response?.data?.message || 'Failed to approve expense');
    },
  });
};

// Reject expense
export const useRejectExpense = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reason }) => expenseService.reject(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: expenseKeys.lists() });
      queryClient.invalidateQueries({ queryKey: expenseKeys.pending() });
      toast.success('Expense rejected');
    },
    onError: (error) => {
      toast.error(error.response?.data?.message || 'Failed to reject expense');
    },
  });
};

// OCR Scan
export const useScanReceipt = () => {
  return useMutation({
    mutationFn: expenseService.scanReceipt,
    onSuccess: () => {
      toast.success('Receipt scanned successfully');
    },
    onError: (error) => {
      toast.error(error.response?.data?.message || 'Failed to scan receipt');
    },
  });
};
