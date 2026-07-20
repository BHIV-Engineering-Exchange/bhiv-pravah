const mongoose = require('mongoose');

const paidLeaveConfigSchema = new mongoose.Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    index: true
  },
  date: {
    type: Date,
    required: true,
    index: true
  },
  hours: {
    type: Number,
    required: true,
    default: 8,
    min: 0,
    max: 24
  },
  leaveType: {
    type: String,
    enum: ['Sick Leave', 'Casual Leave', 'Privilege Leave', 'Paid Leave', 'Compensatory Off', 'Maternity Leave', 'Paternity Leave', 'Other'],
    default: 'Paid Leave'
  },
  reason: {
    type: String,
    trim: true
  },
  isApproved: {
    type: Boolean,
    default: true
  },
  approvedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  countAsWorking: {
    type: Boolean,
    default: true // Paid leaves count as working hours for salary
  },
  createdBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  remarks: {
    type: String,
    trim: true
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  updatedAt: {
    type: Date,
    default: Date.now
  }
}, {
  timestamps: true
});

// Compound indexes
paidLeaveConfigSchema.index({ user: 1, date: 1 }, { unique: true });
paidLeaveConfigSchema.index({ date: 1, isApproved: 1 });

// Static method to get paid leaves for user in date range
paidLeaveConfigSchema.statics.getLeavesForUser = async function(userId, startDate, endDate) {
  return await this.find({
    user: userId,
    date: { $gte: startDate, $lte: endDate },
    isApproved: true,
    countAsWorking: true
  }).sort({ date: 1 });
};

// Static method to get total paid leave hours
paidLeaveConfigSchema.statics.getTotalPaidHours = async function(userId, startDate, endDate) {
  const result = await this.aggregate([
    {
      $match: {
        user: new mongoose.Types.ObjectId(userId),
        date: { $gte: startDate, $lte: endDate },
        isApproved: true,
        countAsWorking: true
      }
    },
    {
      $group: {
        _id: null,
        totalHours: { $sum: '$hours' }
      }
    }
  ]);
  
  return result.length > 0 ? result[0].totalHours : 0;
};

module.exports = mongoose.model('PaidLeaveConfig', paidLeaveConfigSchema);
