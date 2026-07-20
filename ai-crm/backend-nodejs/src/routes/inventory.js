import express from 'express';
import { body } from 'express-validator';
import Product from '../models/Product.js';
import InventoryLog from '../models/InventoryLog.js';
import { protect } from '../middleware/auth.js';
import { isAdminOrManager } from '../middleware/authorize.js';
import { validate } from '../middleware/validate.js';
import { HTTP_STATUS, INVENTORY_CHANGE_TYPE } from '../config/constants.js';

const router = express.Router();

// All routes require authentication
router.use(protect);

// @route   GET /api/inventory/logs
// @desc    Get inventory logs
// @access  Private/Admin/Manager
router.get('/logs', isAdminOrManager, async (req, res) => {
  try {
    const { productId, changeType, page = 1, limit = 50 } = req.query;
    
    const query = {};
    
    if (productId) {
      query.productId = productId;
    }
    
    if (changeType) {
      query.changeType = changeType;
    }

    const logs = await InventoryLog.find(query)
      .sort({ createdAt: -1 })
      .limit(parseInt(limit))
      .skip((parseInt(page) - 1) * parseInt(limit))
      .populate('productId', 'name sku')
      .populate('performedBy', 'name email role')
      .populate('orderId', 'orderNumber');

    const total = await InventoryLog.countDocuments(query);

    res.json({
      success: true,
      data: {
        logs,
        pagination: {
          page: parseInt(page),
          limit: parseInt(limit),
          total,
          pages: Math.ceil(total / parseInt(limit))
        }
      }
    });
  } catch (error) {
    res.status(HTTP_STATUS.INTERNAL_SERVER_ERROR).json({
      success: false,
      message: error.message
    });
  }
});

// @route   POST /api/inventory/adjust
// @desc    Manually adjust inventory
// @access  Private/Admin/Manager
router.post('/adjust', isAdminOrManager, [
  body('productId').notEmpty().withMessage('Product ID is required'),
  body('quantity').isNumeric().withMessage('Quantity must be a number'),
  body('changeType').isIn(Object.values(INVENTORY_CHANGE_TYPE)).withMessage('Invalid change type')
], validate, async (req, res) => {
  try {
    const { productId, quantity, changeType, notes } = req.body;

    const product = await Product.findById(productId);

    if (!product) {
      return res.status(HTTP_STATUS.NOT_FOUND).json({
        success: false,
        message: 'Product not found'
      });
    }

    const previousStock = product.stockQuantity;
    const newStock = previousStock + quantity;

    if (newStock < 0) {
      return res.status(HTTP_STATUS.BAD_REQUEST).json({
        success: false,
        message: 'Stock quantity cannot be negative'
      });
    }

    product.stockQuantity = newStock;
    await product.save();

    // Create inventory log
    const log = await InventoryLog.create({
      productId: product._id,
      changeType,
      quantityChanged: quantity,
      previousStock,
      newStock,
      performedBy: req.user._id,
      notes
    });

    const populatedLog = await InventoryLog.findById(log._id)
      .populate('productId', 'name sku')
      .populate('performedBy', 'name email role');

    res.status(HTTP_STATUS.CREATED).json({
      success: true,
      message: 'Inventory adjusted successfully',
      data: { log: populatedLog, product }
    });
  } catch (error) {
    res.status(HTTP_STATUS.INTERNAL_SERVER_ERROR).json({
      success: false,
      message: error.message
    });
  }
});

// @route   GET /api/inventory/low-stock
// @desc    Get low stock products
// @access  Private/Admin/Manager
router.get('/low-stock', isAdminOrManager, async (req, res) => {
  try {
    const products = await Product.find({
      $expr: { $lt: ['$stockQuantity', '$minThreshold'] },
      isActive: true
    })
      .populate('createdBy', 'name email')
      .sort({ stockQuantity: 1 });

    res.json({
      success: true,
      data: { products }
    });
  } catch (error) {
    res.status(HTTP_STATUS.INTERNAL_SERVER_ERROR).json({
      success: false,
      message: error.message
    });
  }
});

// @route   GET /api/inventory/stats
// @desc    Get inventory statistics
// @access  Private/Admin/Manager
router.get('/stats', isAdminOrManager, async (req, res) => {
  try {
    const totalProducts = await Product.countDocuments({ isActive: true });
    const lowStockCount = await Product.countDocuments({
      $expr: { $lt: ['$stockQuantity', '$minThreshold'] },
      isActive: true
    });
    const outOfStockCount = await Product.countDocuments({ stockQuantity: 0, isActive: true });

    const products = await Product.find({ isActive: true });
    const totalStockValue = products.reduce((sum, p) => sum + (p.costPrice * p.stockQuantity), 0);
    const totalStockItems = products.reduce((sum, p) => sum + p.stockQuantity, 0);

    res.json({
      success: true,
      data: {
        totalProducts,
        lowStockCount,
        outOfStockCount,
        totalStockValue: totalStockValue.toFixed(2),
        totalStockItems
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
