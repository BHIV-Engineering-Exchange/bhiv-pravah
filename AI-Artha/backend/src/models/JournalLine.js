import mongoose from 'mongoose';
import { randomUUID } from 'crypto';

const journalLineSchema = new mongoose.Schema(
  {
    id: {
      type: String,
      default: randomUUID,
      unique: true,
      index: true,
    },
    journal_id: {
      type: String,
      required: true,
      index: true,
    },
    account_id: {
      type: String,
      required: true,
      index: true,
    },
    debit: {
      type: Number,
      default: 0,
      min: 0,
    },
    credit: {
      type: Number,
      default: 0,
      min: 0,
    },
  },
  {
    timestamps: true,
  }
);

export default mongoose.model('JournalLine', journalLineSchema);
