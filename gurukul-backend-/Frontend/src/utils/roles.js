/**
 * Role Management Utilities
 * Handles role-based access control for EMS + Governance
 */

export const ROLES = {
    STUDENT: 'student',
    TEACHER: 'teacher',
    PARENT: 'parent',
    ADMIN: 'admin'
};

/**
 * Get current user role from localStorage or default to student
 */
export const getCurrentRole = () => {
    return localStorage.getItem('gurukul_user_role') || ROLES.STUDENT;
};

/**
 * Set user role
 */
export const setUserRole = (role) => {
    if (Object.values(ROLES).includes(role)) {
        localStorage.setItem('gurukul_user_role', role);
    }
};

/**
 * Check if user has a specific role
 */
export const hasRole = (role) => {
    return getCurrentRole() === role;
};

/**
 * Check if user has any of the specified roles
 */
export const hasAnyRole = (roles) => {
    const currentRole = getCurrentRole();
    return roles.includes(currentRole);
};

/**
 * Get role display name
 */
export const getRoleDisplayName = (role) => {
    const names = {
        [ROLES.STUDENT]: 'Student',
        [ROLES.TEACHER]: 'Teacher',
        [ROLES.PARENT]: 'Parent',
        [ROLES.ADMIN]: 'Administrator'
    };
    return names[role] || 'Student';
};

export const getDashboardPath = (role) => {
    if (['teacher', 'admin', 'institution_admin', 'regional_admin'].includes(role)) {
        return '/drishti';
    }
    return '/dashboard';
};

