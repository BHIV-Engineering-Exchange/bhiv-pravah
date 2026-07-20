import express from 'express';
import { body } from 'express-validator';
import User from '../models/User.js';
import { generateToken, protect } from '../middleware/auth.js';
import { validate } from '../middleware/validate.js';
import { HTTP_STATUS, USER_ROLES } from '../config/constants.js';

const router = express.Router();

// @route   POST /api/auth/register
// @desc    Register new user (Admin only can create users via separate endpoint)
// @access  Public (for first admin only)
router.post('/register', [
  body('email').isEmail().withMessage('Please provide a valid email'),
  body('password').isLength({ min: 6 }).withMessage('Password must be at least 6 characters'),
  body('name').notEmpty().withMessage('Name is required')
], validate, async (req, res) => {
  try {
    const { email, password, name } = req.body;

    // Check if this is the first user (will be admin)
    const userCount = await User.countDocuments();
    
    if (userCount > 0) {
      return res.status(HTTP_STATUS.FORBIDDEN).json({
        success: false,
        message: 'Registration is disabled. Contact admin to create an account.'
      });
    }

    // Create first admin user
    const user = await User.create({
      name,
      email,
      password,
      role: USER_ROLES.ADMIN
    });

    const token = generateToken(user._id);

    res.status(HTTP_STATUS.CREATED).json({
      success: true,
      message: 'Admin account created successfully',
      data: {
        user: user.toPublicJSON(),
        token
      }
    });
  } catch (error) {
    res.status(HTTP_STATUS.INTERNAL_SERVER_ERROR).json({
      success: false,
      message: error.message
    });
  }
});

// @route   POST /api/auth/login
// @desc    Login user
// @access  Public
router.post('/login', [
  body('email').isEmail().withMessage('Please provide a valid email'),
  body('password').notEmpty().withMessage('Password is required')
], validate, async (req, res) => {
  try {
    const { email, password } = req.body;

    // Find user with password field
    const user = await User.findOne({ email }).select('+password');

    if (!user) {
      return res.status(HTTP_STATUS.UNAUTHORIZED).json({
        success: false,
        message: 'Invalid credentials'
      });
    }

    // Check if account is active
    if (!user.isActive) {
      return res.status(HTTP_STATUS.FORBIDDEN).json({
        success: false,
        message: 'Account is deactivated. Contact administrator.'
      });
    }

    // Check password
    const isPasswordValid = await user.comparePassword(password);

    if (!isPasswordValid) {
      return res.status(HTTP_STATUS.UNAUTHORIZED).json({
        success: false,
        message: 'Invalid credentials'
      });
    }

    // Update last login
    user.lastLogin = new Date();
    await user.save();

    const token = generateToken(user._id);

    res.json({
      success: true,
      message: 'Login successful',
      data: {
        user: user.toPublicJSON(),
        token
      }
    });
  } catch (error) {
    res.status(HTTP_STATUS.INTERNAL_SERVER_ERROR).json({
      success: false,
      message: error.message
    });
  }
});

// @route   GET /api/auth/me
// @desc    Get current user
// @access  Private
router.get('/me', protect, async (req, res) => {
  try {
    res.json({
      success: true,
      data: {
        user: req.user.toPublicJSON()
      }
    });
  } catch (error) {
    res.status(HTTP_STATUS.INTERNAL_SERVER_ERROR).json({
      success: false,
      message: error.message
    });
  }
});

export default router;
