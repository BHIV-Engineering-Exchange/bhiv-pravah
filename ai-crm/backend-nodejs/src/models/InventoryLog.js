import mongoose from 'mongoose';
import { INVENTORY_CHANGE_TYPE } from '../config/constants.js';

const inventoryLogSchema = new mongoose.Schema({
  productId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Product',
    required: true
  },
  changeType: {
    type: String,
    enum: Object.values(INVENTORY_CHANGE_TYPE),
    required: true
  },
  quantityChanged: {
    type: Number,
    required: true
  },
  previousStock: {
    type: Number,
    required: true
  },
  newStock: {
    type: Number,
    required: true
  },
  orderId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Order'
  },
  performedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  notes: {
    type: String,
    trim: true
  }
}, {
  timestamps: true
});

// Index for efficient queries
inventoryLogSchema.index({ productId: 1, createdAt: -1 });
inventoryLogSchema.index({ changeType: 1 });

const InventoryLog = mongoose.model('InventoryLog', inventoryLogSchema);

export default InventoryLog;
