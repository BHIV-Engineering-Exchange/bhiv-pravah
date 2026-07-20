import mongoose from 'mongoose';

const supplierSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: [true, 'Supplier name is required'],
      trim: true,
      unique: true
    },
    email: {
      type: String,
      trim: true,
      lowercase: true,
      default: ''
    },
    phone: {
      type: String,
      trim: true,
      default: ''
    },
    address: {
      type: String,
      trim: true,
      default: ''
    },
    isActive: {
      type: Boolean,
      default: true
    },
    leadTimeDays: {
      type: Number,
      default: 7,
      min: 0
    },
    rating: {
      type: Number,
      min: 0,
      max: 5,
      default: 0
    },
    notes: {
      type: String,
      default: ''
    }
  },
  {
    timestamps: true,
    toJSON: { virtuals: true },
    toObject: { virtuals: true }
  }
);

// Add index for faster queries
supplierSchema.index({ name: 1 });
supplierSchema.index({ isActive: 1 });

// Virtual for ID
supplierSchema.virtual('id').get(function () {
  return this._id.toString();
});

const Supplier = mongoose.model('Supplier', supplierSchema);

export default Supplier;
