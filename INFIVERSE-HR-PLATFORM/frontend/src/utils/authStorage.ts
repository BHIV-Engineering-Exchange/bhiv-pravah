/**
 * Per-tab auth storage using sessionStorage so each browser tab maintains
 * its own authentication session (candidate / recruiter / client).
 * localStorage is shared across all tabs, so the last-logged-in role would
 * appear in every tab after refresh. sessionStorage is per-tab.
 */
const storage =
  typeof sessionStorage !== 'undefined'
    ? sessionStorage
    : typeof localStorage !== 'undefined'
      ? localStorage
      : null;

export const authStorage = {
  getItem: (key: string): string | null => (storage ? storage.getItem(key) : null),
  setItem: (key: string, value: string): void => {
    storage?.setItem(key, value);
  },
  removeItem: (key: string): void => {
    storage?.removeItem(key);
  },
};

export const AUTH_KEYS = [
  'auth_token',
  'user_data',
  'user_role',
  'user_email',
  'user_name',
  'isAuthenticated',
  'candidate_id',
  'backend_candidate_id',
  'client_id',
  'candidate_profile_data',
] as const;

export function clearAuthStorage(): void {
  AUTH_KEYS.forEach((key) => authStorage.removeItem(key));
}
