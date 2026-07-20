import express from 'express';
import { protect } from '../middleware/auth.js';
import Product from '../models/Product.js';
import Order from '../models/Order.js';

const router = express.Router();

// All routes require authentication
router.use(protect);

// @route   POST /api/llm-query
// @desc    Process a natural language query about the CRM data
// @access  Private
router.post('/', async (req, res) => {
  try {
    const { query, context = {} } = req.body;

    if (!query) {
      return res.status(400).json({
        success: false,
        message: 'Query is required'
      });
    }

    const queryLower = query.toLowerCase();
    let response = {};

    // Simple keyword-based query processing
    if (queryLower.includes('product') || queryLower.includes('inventory') || queryLower.includes('stock')) {
      const totalProducts = await Product.countDocuments();
      const lowStockProducts = await Product.countDocuments({
        $expr: { $lte: ['$stockQuantity', '$minStockLevel'] }
      });
      const activeProducts = await Product.countDocuments({ isActive: true });

      response = {
        answer: `You have ${totalProducts} products in inventory. ${activeProducts} are active and ${lowStockProducts} are low on stock.`,
        data: { totalProducts, activeProducts, lowStockProducts },
        type: 'inventory_summary'
      };
    } else if (queryLower.includes('order') || queryLower.includes('sales')) {
      const totalOrders = await Order.countDocuments();
      const pendingOrders = await Order.countDocuments({ status: 'pending' });
      const completedOrders = await Order.countDocuments({ status: { $in: ['completed', 'delivered'] } });

      response = {
        answer: `You have ${totalOrders} total orders. ${pendingOrders} are pending and ${completedOrders} are completed/delivered.`,
        data: { totalOrders, pendingOrders, completedOrders },
        type: 'order_summary'
      };
    } else if (queryLower.includes('help') || queryLower.includes('what can')) {
      response = {
        answer: 'I can help you with:\n- Product and inventory queries (e.g., "How many products do I have?")\n- Order information (e.g., "Show me pending orders")\n- Stock alerts (e.g., "Which products are low on stock?")\n\nTry asking me about your products, orders, or inventory!',
        type: 'help'
      };
    } else {
      // Generic query - provide a summary
      const totalProducts = await Product.countDocuments();
      const totalOrders = await Order.countDocuments();

      response = {
        answer: `Here's a quick overview: You have ${totalProducts} products and ${totalOrders} orders in the system. Try asking more specific questions about your inventory or orders for detailed information!`,
        data: { totalProducts, totalOrders },
        type: 'general_summary'
      };
    }

    res.json({
      success: true,
      data: {
        query,
        ...response,
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('LLM Query error:', error);
    res.status(500).json({
      success: false,
      message: error.message || 'Failed to process query'
    });
  }
});

// @route   GET /api/llm-query/examples  
// @desc    Get example queries
// @access  Private
router.get('/examples', async (req, res) => {
  try {
    res.json({
      success: true,
      data: {
        examples: [
          'How many products do I have?',
          'Show me pending orders',
          'Which products are low on stock?',
          'Give me an inventory summary',
          'What are my recent sales?',
          'How many active products are there?'
        ]
      }
    });
  } catch (error) {
    res.status(500).json({ success: false, message: error.message });
  }
});

export default router;
