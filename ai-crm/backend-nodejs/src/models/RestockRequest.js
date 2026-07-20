import mongoose from 'mongoose';
import { RESTOCK_STATUS } from '../config/constants.js';

const restockRequestSchema = new mongoose.Schema({
  productId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Product',
    required: true
  },
  productName: {
    type: String,
    required: true
  },
  sku: {
    type: String,
    required: true
  },
  currentStock: {
    type: Number,
    required: true
  },
  threshold: {
    type: Number,
    required: true
  },
  requestedQuantity: {
    type: Number,
    required: true
  },
  supplierEmail: {
    type: String,
    required: true,
    trim: true
  },
  supplierName: {
    type: String,
    trim: true
  },
  status: {
    type: String,
    enum: Object.values(RESTOCK_STATUS),
    default: RESTOCK_STATUS.PENDING
  },
  emailSentAt: {
    type: Date
  },
  restockedAt: {
    type: Date
  },
  restockedBy: {
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
restockRequestSchema.index({ productId: 1, createdAt: -1 });
restockRequestSchema.index({ status: 1 });

// Virtual for emailSent status
restockRequestSchema.virtual('emailSent').get(function() {
  return !!this.emailSentAt;
});

// Ensure virtuals are included in JSON
restockRequestSchema.set('toJSON', { virtuals: true });
restockRequestSchema.set('toObject', { virtuals: true });

const RestockRequest = mongoose.model('RestockRequest', restockRequestSchema);

export default RestockRequest;
