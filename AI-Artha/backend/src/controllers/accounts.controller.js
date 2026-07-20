import chartOfAccountsService from '../services/chartOfAccounts.service.js';
import logger from '../config/logger.js';

// @desc    Get all accounts
// @route   GET /api/v1/accounts
// @access  Private
export const getAccounts = async (req, res) => {
  try {
    const filters = {
      type: req.query.type,
      isActive: req.query.isActive === 'true' ? true : req.query.isActive === 'false' ? false : undefined,
      search: req.query.search,
    };

    const accounts = await chartOfAccountsService.getAllAccounts(filters);

    res.json({
      success: true,
      data: accounts,
    });
  } catch (error) {
    logger.error('Get accounts error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Get single account
// @route   GET /api/v1/accounts/:id
// @access  Private
export const getAccount = async (req, res) => {
  try {
    const account = await chartOfAccountsService.getAccountById(req.params.id);

    res.json({
      success: true,
      data: account,
    });
  } catch (error) {
    logger.error('Get account error:', error);
    res.status(404).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Create account
// @route   POST /api/v1/accounts
// @access  Private (admin, accountant)
export const createAccount = async (req, res) => {
  try {
    const account = await chartOfAccountsService.createAccount(req.body);

    res.status(201).json({
      success: true,
      data: account,
    });
  } catch (error) {
    logger.error('Create account error:', error);
    res.status(400).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Update account
// @route   PUT /api/v1/accounts/:id
// @access  Private (admin, accountant)
export const updateAccount = async (req, res) => {
  try {
    const account = await chartOfAccountsService.updateAccount(req.params.id, req.body);

    res.json({
      success: true,
      data: account,
    });
  } catch (error) {
    logger.error('Update account error:', error);
    res.status(400).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Deactivate account
// @route   DELETE /api/v1/accounts/:id
// @access  Private (admin)
  export const deactivateAccount = async (req, res) => {
  try {
    const account = await chartOfAccountsService.deactivateAccount(req.params.id);

    res.json({
      success: true,
      data: account,
    });
  } catch (error) {
    logger.error('Deactivate account error:', error);
    res.status(404).json({
      success: false,
      message: error.message,
    });
  }
};

// @desc    Seed default accounts
// @route   POST /api/v1/accounts/seed
// @access  Private (admin)
export const seedAccounts = async (req, res) => {
  try {
    const result = await chartOfAccountsService.seedDefaultAccounts();

    res.json({
      success: true,
      data: result,
    });
  } catch (error) {
    logger.error('Seed accounts error:', error);
    res.status(500).json({
      success: false,
      message: error.message,
    });
  }
};