import mongoose from 'mongoose';
import { randomUUID } from 'crypto';

const accountSchema = new mongoose.Schema(
  {
    id: {
      type: String,
      default: randomUUID,
      unique: true,
      index: true,
    },
    name: {
      type: String,
      required: true,
      trim: true,
    },
    type: {
      type: String,
      required: true,
      enum: ['ASSET', 'LIABILITY', 'INCOME', 'EXPENSE'],
    },
    chartAccount: {
      type: mongoose.Schema.Types.ObjectId,
      ref: 'ChartOfAccounts',
      default: null,
    },
  },
  {
    timestamps: true,
  }
);

export default mongoose.model('Account', accountSchema);
