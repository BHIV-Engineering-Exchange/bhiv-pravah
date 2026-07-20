import express from 'express';
import { body } from 'express-validator';
import mongoose from 'mongoose';
import Order from '../models/Order.js';
import Product from '../models/Product.js';
import User from '../models/User.js';
import InventoryLog from '../models/InventoryLog.js';
import RestockRequest from '../models/RestockRequest.js';
import { protect } from '../middleware/auth.js';
import { isAdminOrManager, isCustomer } from '../middleware/authorize.js';
import { validate } from '../middleware/validate.js';
import { HTTP_STATUS, ORDER_STATUS, INVENTORY_CHANGE_TYPE, RESTOCK_STATUS, USER_ROLES } from '../config/constants.js';
import emailService from '../services/emailService.js';

const router = express.Router();

// All routes require authentication
router.use(protect);

// @route   GET /api/orders
// @desc    Get all orders
// @access  Private
router.get('/', async (req, res) => {
  try {
    const { status, customerId, page = 1, limit = 50 } = req.query;
    
    const query = {};
    
    // Customers can only see their own orders
    if (req.user.role === USER_ROLES.CUSTOMER) {
      query.customerId = req.user._id;
    } else if (customerId) {
      query.customerId = customerId;
    }
    
    if (status) {
      query.status = status;
    }

    const orders = await Order.find(query)
      .sort({ createdAt: -1 })
      .limit(parseInt(limit))
      .skip((parseInt(page) - 1) * parseInt(limit))
      .populate('customerId', 'name email shopDetails')
      .populate('items.productId', 'name sku')
      .populate('tracking.dispatchedBy', 'name email');

    const total = await Order.countDocuments(query);

    res.json({
      success: true,
      data: {
        orders,
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

// @route   POST /api/orders
// @desc    Create new order (customer places order)
// @access  Private/Customer
router.post('/', isCustomer, [
  body('items').isArray({ min: 1 }).withMessage('Order must have at least one item'),
  body('items.*.productId').notEmpty().withMessage('Product ID is required'),
  body('items.*.quantity').isInt({ min: 1 }).withMessage('Quantity must be at least 1')
], validate, async (req, res) => {
  const session = await mongoose.startSession();
  session.startTransaction();

  try {
    const { items, notes } = req.body;
    
    // Validate and prepare order items
    const orderItems = [];
    let totalAmount = 0;

    for (const item of items) {
      const product = await Product.findById(item.productId).session(session);
      
      if (!product) {
        await session.abortTransaction();
        return res.status(HTTP_STATUS.NOT_FOUND).json({
          success: false,
          message: `Product not found: ${item.productId}`
        });
      }

      if (!product.isActive) {
        await session.abortTransaction();
        return res.status(HTTP_STATUS.BAD_REQUEST).json({
          success: false,
          message: `Product ${product.name} is not available`
        });
      }

      if (product.stockQuantity < item.quantity) {
        await session.abortTransaction();
        return res.status(HTTP_STATUS.BAD_REQUEST).json({
          success: false,
          message: `Insufficient stock for ${product.name}. Available: ${product.stockQuantity}`
        });
      }

      const itemTotal = product.sellingPrice * item.quantity;
      totalAmount += itemTotal;

      orderItems.push({
        productId: product._id,
        productName: product.name,
        sku: product.sku,
        quantity: item.quantity,
        price: product.sellingPrice,
        total: itemTotal
      });

      // Reduce inventory
      const previousStock = product.stockQuantity;
      product.stockQuantity -= item.quantity;
      await product.save({ session });

      // Log inventory change
      await InventoryLog.create([{
        productId: product._id,
        changeType: INVENTORY_CHANGE_TYPE.ORDER,
        quantityChanged: -item.quantity,
        previousStock,
        newStock: product.stockQuantity,
        performedBy: req.user._id
      }], { session });

      // Check if restock is needed
      if (product.stockQuantity < product.minThreshold) {
        const existingRequest = await RestockRequest.findOne({
          productId: product._id,
          status: { $in: [RESTOCK_STATUS.PENDING, RESTOCK_STATUS.EMAIL_SENT] }
        }).session(session);

        if (!existingRequest && product.supplier && product.supplier.email) {
          const requestedQuantity = Math.max(
            product.minThreshold * 2 - product.stockQuantity,
            product.minThreshold
          );

          const restockRequest = await RestockRequest.create([{
            productId: product._id,
            productName: product.name,
            sku: product.sku,
            currentStock: product.stockQuantity,
            threshold: product.minThreshold,
            requestedQuantity,
            supplierEmail: product.supplier.email,
            supplierName: product.supplier.name,
            status: RESTOCK_STATUS.PENDING
          }], { session });

          // Send email after transaction commits
          setImmediate(async () => {
            const emailResult = await emailService.sendRestockEmail(product, restockRequest[0]);
            if (emailResult.success) {
              restockRequest[0].status = RESTOCK_STATUS.EMAIL_SENT;
              restockRequest[0].emailSentAt = new Date();
              await restockRequest[0].save();
            }
          });
        }
      }
    }

    // Create order
    const order = await Order.create([{
      customerId: req.user._id,
      items: orderItems,
      totalAmount,
      notes,
      shippingAddress: req.user.shopDetails
    }], { session });

    await session.commitTransaction();

    // Send order confirmation email
    setImmediate(() => {
      emailService.sendOrderConfirmation(order[0], req.user);
    });

    // Populate order details
    const populatedOrder = await Order.findById(order[0]._id)
      .populate('customerId', 'name email shopDetails')
      .populate('items.productId', 'name sku');

    res.status(HTTP_STATUS.CREATED).json({
      success: true,
      message: 'Order placed successfully',
      data: { order: populatedOrder }
    });

  } catch (error) {
    await session.abortTransaction();
    res.status(HTTP_STATUS.INTERNAL_SERVER_ERROR).json({
      success: false,
      message: error.message
    });
  } finally {
    session.endSession();
  }
});

// @route   GET /api/orders/:id
// @desc    Get order by ID
// @access  Private
router.get('/:id', async (req, res) => {
  try {
    const order = await Order.findById(req.params.id)
      .populate('customerId', 'name email shopDetails')
      .populate('items.productId', 'name sku')
      .populate('tracking.dispatchedBy', 'name email');

    if (!order) {
      return res.status(HTTP_STATUS.NOT_FOUND).json({
        success: false,
        message: 'Order not found'
      });
    }

    // Customers can only view their own orders
    if (req.user.role === USER_ROLES.CUSTOMER && order.customerId._id.toString() !== req.user._id.toString()) {
      return res.status(HTTP_STATUS.FORBIDDEN).json({
        success: false,
        message: 'Not authorized to view this order'
      });
    }

    res.json({
      success: true,
      data: { order }
    });
  } catch (error) {
    res.status(HTTP_STATUS.INTERNAL_SERVER_ERROR).json({
      success: false,
      message: error.message
    });
  }
});

// @route   PUT /api/orders/:id/dispatch
// @desc    Mark order as dispatched
// @access  Private/Admin/Manager
router.put('/:id/dispatch', isAdminOrManager, async (req, res) => {
  try {
    const order = await Order.findById(req.params.id);

    if (!order) {
      return res.status(HTTP_STATUS.NOT_FOUND).json({
        success: false,
        message: 'Order not found'
      });
    }

    if (order.status !== ORDER_STATUS.PLACED) {
      return res.status(HTTP_STATUS.BAD_REQUEST).json({
        success: false,
        message: `Order cannot be dispatched. Current status: ${order.status}`
      });
    }

    order.status = ORDER_STATUS.DISPATCHED;
    order.tracking.dispatchedAt = new Date();
    order.tracking.dispatchedBy = req.user._id;

    await order.save();

    // Notify customer (email) after dispatch
    setImmediate(async () => {
      try {
        const customer = await User.findById(order.customerId).select('name email');
        if (customer?.email) {
          await emailService.sendOrderDispatched(order, customer);
        }
      } catch (e) {
        console.warn('Failed to send dispatched email:', e.message);
      }
    });

    const populatedOrder = await Order.findById(order._id)
      .populate('customerId', 'name email shopDetails')
      .populate('items.productId', 'name sku')
      .populate('tracking.dispatchedBy', 'name email');

    res.json({
      success: true,
      message: 'Order marked as dispatched',
      data: { order: populatedOrder }
    });
  } catch (error) {
    res.status(HTTP_STATUS.INTERNAL_SERVER_ERROR).json({
      success: false,
      message: error.message
    });
  }
});

// @route   PUT /api/orders/:id/deliver
// @desc    Confirm delivery (by customer)
// @access  Private/Customer
router.put('/:id/deliver', isCustomer, async (req, res) => {
  try {
    const order = await Order.findById(req.params.id);

    if (!order) {
      return res.status(HTTP_STATUS.NOT_FOUND).json({
        success: false,
        message: 'Order not found'
      });
    }

    // Verify order belongs to customer
    if (order.customerId.toString() !== req.user._id.toString()) {
      return res.status(HTTP_STATUS.FORBIDDEN).json({
        success: false,
        message: 'Not authorized to update this order'
      });
    }

    if (order.status !== ORDER_STATUS.DISPATCHED) {
      return res.status(HTTP_STATUS.BAD_REQUEST).json({
        success: false,
        message: `Order cannot be delivered. Current status: ${order.status}`
      });
    }

    order.status = ORDER_STATUS.DELIVERED;
    order.tracking.deliveredAt = new Date();
    order.tracking.confirmedByCustomer = true;

    await order.save();

    // Notify customer (email) after delivery confirmation
    setImmediate(async () => {
      try {
        const customer = await User.findById(order.customerId).select('name email');
        if (customer?.email) {
          await emailService.sendOrderDelivered(order, customer);
        }
      } catch (e) {
        console.warn('Failed to send delivered email:', e.message);
      }
    });

    const populatedOrder = await Order.findById(order._id)
      .populate('customerId', 'name email shopDetails')
      .populate('items.productId', 'name sku')
      .populate('tracking.dispatchedBy', 'name email');

    res.json({
      success: true,
      message: 'Order marked as delivered',
      data: { order: populatedOrder }
    });
  } catch (error) {
    res.status(HTTP_STATUS.INTERNAL_SERVER_ERROR).json({
      success: false,
      message: error.message
    });
  }
});

// @route   GET /api/orders/stats/summary
// @desc    Get order statistics
// @access  Private/Admin/Manager
router.get('/stats/summary', isAdminOrManager, async (req, res) => {
  try {
    const totalOrders = await Order.countDocuments();
    const placedOrders = await Order.countDocuments({ status: ORDER_STATUS.PLACED });
    const dispatchedOrders = await Order.countDocuments({ status: ORDER_STATUS.DISPATCHED });
    const deliveredOrders = await Order.countDocuments({ status: ORDER_STATUS.DELIVERED });

    // Get revenue statistics
    const orders = await Order.find({ status: ORDER_STATUS.DELIVERED });
    const totalRevenue = orders.reduce((sum, order) => sum + order.totalAmount, 0);

    res.json({
      success: true,
      data: {
        totalOrders,
        placedOrders,
        dispatchedOrders,
        deliveredOrders,
        totalRevenue: totalRevenue.toFixed(2)
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
