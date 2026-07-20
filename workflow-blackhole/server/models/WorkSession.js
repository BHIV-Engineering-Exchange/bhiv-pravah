const mongoose = require('mongoose');

const workSessionSchema = new mongoose.Schema({
  employee: {
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
  startTime: {
    type: Date,
    required: true
  },
  endTime: {
    type: Date
  },
  // Start/End Day Times from attendance
  startDayTime: {
    type: Date
  },
  endDayTime: {
    type: Date
  },
  // Work Location Information
  workLocation: {
    type: String,
    enum: ['Office', 'Home', 'Remote'],
    default: 'Office'
  },
  startLocation: {
    latitude: Number,
    longitude: Number,
    address: String,
    accuracy: Number
  },
  endLocation: {
    latitude: Number,
    longitude: Number,
    address: String,
    accuracy: Number
  },
  pausedAt: {
    type: Date
  },
  resumedAt: {
    type: Date
  },
  targetHours: {
    type: Number,
    default: 8,
    min: 1,
    max: 12
  },
  status: {
    type: String,
    enum: ['active', 'paused', 'completed'],
    default: 'active'
  },
  totalBreakTime: {
    type: Number,
    default: 0 // in minutes
  },
  productivity: {
    keystrokeCount: { type: Number, default: 0 },
    mouseActivity: { type: Number, default: 0 },
    activeTime: { type: Number, default: 0 }, // in minutes
    idleTime: { type: Number, default: 0 }, // in minutes
    violationCount: { type: Number, default: 0 },
    workRelatedTime: { type: Number, default: 0 }, // in minutes
    nonWorkTime: { type: Number, default: 0 } // in minutes
  },
  notes: {
    type: String,
    maxlength: 1000
  },
  metadata: {
    workHoursPolicy: {
      type: String,
      enum: ['flexible', 'fixed', 'hybrid'],
      default: 'flexible'
    },
    autoBreaks: { type: Boolean, default: false },
    overtimeAllowed: { type: Boolean, default: false },
    remindersSent: [Date]
  }
}, {
  timestamps: true,
  collection: 'work_sessions'
});

// Compound indexes for efficient queries
workSessionSchema.index({ employee: 1, date: 1 }, { unique: true });
workSessionSchema.index({ employee: 1, status: 1 });
workSessionSchema.index({ date: 1, status: 1 });

// Virtual for calculating actual work duration
workSessionSchema.virtual('actualWorkDuration').get(function() {
  if (!this.startTime) return 0;
  
  const endTime = this.endTime || new Date();
  const totalMinutes = Math.floor((endTime - this.startTime) / (1000 * 60));
  
  // Subtract break time
  return Math.max(0, totalMinutes - this.totalBreakTime);
});

// Virtual for calculating work completion percentage
workSessionSchema.virtual('completionPercentage').get(function() {
  const actualHours = this.actualWorkDuration / 60;
  return Math.min(100, (actualHours / this.targetHours) * 100);
});

// Virtual for calculating remaining work time
workSessionSchema.virtual('remainingTime').get(function() {
  const actualHours = this.actualWorkDuration / 60;
  return Math.max(0, this.targetHours - actualHours);
});

// Method to calculate productivity score
workSessionSchema.methods.calculateProductivityScore = function() {
  const { keystrokeCount, activeTime, workRelatedTime, violationCount } = this.productivity;
  
  // Base score from activity
  let score = 0;
  
  // Keystroke activity (0-30 points)
  score += Math.min(30, (keystrokeCount / 1000) * 30);
  
  // Active time ratio (0-40 points)
  const totalTime = this.actualWorkDuration;
  if (totalTime > 0) {
    score += (activeTime / totalTime) * 40;
  }
  
  // Work-related time ratio (0-25 points)
  if (totalTime > 0) {
    score += (workRelatedTime / totalTime) * 25;
  }
  
  // Violation penalty (0-5 points deduction)
  score -= Math.min(5, violationCount * 0.5);
  
  return Math.max(0, Math.min(100, score));
};

// Method to add break time
workSessionSchema.methods.addBreakTime = function(minutes) {
  this.totalBreakTime += minutes;
  return this.save();
};

// Method to update productivity metrics
workSessionSchema.methods.updateProductivity = function(metrics) {
  Object.assign(this.productivity, metrics);
  return this.save();
};

// Method to update work location and attendance times
workSessionSchema.methods.updateAttendanceInfo = function(attendanceData) {
  if (attendanceData.startDayTime) this.startDayTime = attendanceData.startDayTime;
  if (attendanceData.endDayTime) this.endDayTime = attendanceData.endDayTime;
  if (attendanceData.workLocation) this.workLocation = attendanceData.workLocation;
  if (attendanceData.startLocation) this.startLocation = attendanceData.startLocation;
  if (attendanceData.endLocation) this.endLocation = attendanceData.endLocation;
  return this.save();
};

// Static method to get today's session for employee
workSessionSchema.statics.getTodaySession = async function(employeeId) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  return this.findOne({
    employee: employeeId,
    date: {
      $gte: today,
      $lt: new Date(today.getTime() + 24 * 60 * 60 * 1000)
    }
  });
};

// Static method to get work sessions by date range
workSessionSchema.statics.getSessionsByDateRange = async function(employeeId, startDate, endDate) {
  return this.find({
    employee: employeeId,
    date: {
      $gte: new Date(startDate),
      $lte: new Date(endDate)
    }
  }).sort({ date: -1 });
};

// Static method to create or update work session from attendance
workSessionSchema.statics.createOrUpdateFromAttendance = async function(attendanceData) {
  const { user, date, startDayTime, endDayTime, workLocation, startDayLocation, endDayLocation } = attendanceData;
  
  let session = await this.findOne({
    employee: user,
    date: new Date(date.getFullYear(), date.getMonth(), date.getDate())
  });
  
  if (!session) {
    session = new this({
      employee: user,
      date: new Date(date.getFullYear(), date.getMonth(), date.getDate()),
      startTime: startDayTime || new Date(),
      startDayTime,
      workLocation: workLocation || 'Office',
      startLocation: startDayLocation
    });
  } else {
    if (startDayTime) session.startDayTime = startDayTime;
    if (endDayTime) session.endDayTime = endDayTime;
    if (workLocation) session.workLocation = workLocation;
    if (startDayLocation) session.startLocation = startDayLocation;
    if (endDayLocation) session.endLocation = endDayLocation;
    
    if (endDayTime) {
      session.endTime = endDayTime;
      session.status = 'completed';
    }
  }
  
  return session.save();
};

// Pre-save middleware to validate work hours
workSessionSchema.pre('save', function(next) {
  // Ensure end time is after start time (with minimum 1 minute difference)
  if (this.endTime && this.startTime) {
    const timeDifference = this.endTime.getTime() - this.startTime.getTime();
    const minimumDuration = 60 * 1000; // 1 minute in milliseconds
    
    if (timeDifference < minimumDuration) {
      // If endTime is too close to startTime, adjust it to be 1 minute later
      this.endTime = new Date(this.startTime.getTime() + minimumDuration);
      console.warn(`⚠️ Adjusted work session end time for employee ${this.employee} to ensure minimum duration`);
    }
  }
  
  // Ensure target hours is reasonable
  if (this.targetHours < 1 || this.targetHours > 12) {
    return next(new Error('Target hours must be between 1 and 12'));
  }
  
  next();
});

// Post-save middleware to update related monitoring data
workSessionSchema.post('save', async function(doc) {
  try {
    // Update employee's current work status in activity tracker
    if (doc.status === 'active') {
      console.log(`📊 Work session activated for employee ${doc.employee} at ${doc.workLocation}`);
    } else if (doc.status === 'completed') {
      console.log(`✅ Work session completed for employee ${doc.employee} - ${doc.actualWorkDuration} minutes worked at ${doc.workLocation}`);
    }
  } catch (error) {
    console.error('Error in WorkSession post-save middleware:', error);
  }
});

module.exports = mongoose.model('WorkSession', workSessionSchema);