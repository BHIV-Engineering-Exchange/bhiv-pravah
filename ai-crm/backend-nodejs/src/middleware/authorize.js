import { USER_ROLES, HTTP_STATUS } from '../config/constants.js';

export const authorize = (...roles) => {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(HTTP_STATUS.UNAUTHORIZED).json({
        success: false,
        message: 'Not authenticated'
      });
    }

    if (!roles.includes(req.user.role)) {
      return res.status(HTTP_STATUS.FORBIDDEN).json({
        success: false,
        message: `Role '${req.user.role}' is not authorized to access this route`
      });
    }

    next();
  };
};

// Check if user is admin
export const isAdmin = authorize(USER_ROLES.ADMIN);

// Check if user is admin or manager
export const isAdminOrManager = authorize(USER_ROLES.ADMIN, USER_ROLES.MANAGER);

// Check if user is customer
export const isCustomer = authorize(USER_ROLES.CUSTOMER);
