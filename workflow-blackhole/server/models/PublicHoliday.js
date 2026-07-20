const mongoose = require('mongoose');

const publicHolidaySchema = new mongoose.Schema({
  date: {
    type: Date,
    required: true,
    index: true
  },
  name: {
    type: String,
    required: true,
    trim: true
  },
  description: {
    type: String,
    trim: true
  },
  isPaidLeave: {
    type: Boolean,
    default: true
  },
  isOptional: {
    type: Boolean,
    default: false
  },
  departments: [{
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Department'
  }],
  createdBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
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

// Compound index for efficient date range queries
publicHolidaySchema.index({ date: 1, isPaidLeave: 1 });

// Static method to get holidays in a date range
publicHolidaySchema.statics.getHolidaysInRange = async function(startDate, endDate, departmentId = null) {
  const query = {
    date: { $gte: startDate, $lte: endDate }
  };
  
  if (departmentId) {
    query.$or = [
      { departments: { $size: 0 } }, // Applies to all departments
      { departments: departmentId }
    ];
  }
  
  return await this.find(query).sort({ date: 1 });
};

// Static method to check if a date is a holiday
publicHolidaySchema.statics.isHoliday = async function(date, departmentId = null) {
  const startOfDay = new Date(date);
  startOfDay.setHours(0, 0, 0, 0);
  
  const endOfDay = new Date(date);
  endOfDay.setHours(23, 59, 59, 999);
  
  const query = {
    date: { $gte: startOfDay, $lte: endOfDay }
  };
  
  if (departmentId) {
    query.$or = [
      { departments: { $size: 0 } },
      { departments: departmentId }
    ];
  }
  
  const holiday = await this.findOne(query);
  return holiday;
};

module.exports = mongoose.model('PublicHoliday', publicHolidaySchema);
