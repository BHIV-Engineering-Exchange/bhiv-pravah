const mongoose = require('mongoose');

const scheduledEmailSchema = new mongoose.Schema({
  subject: {
    type: String,
    required: true
  },
  htmlBody: {
    type: String,
    required: true
  },
  recipients: [{
    type: String,
    required: true
  }],
  scheduledTime: {
    type: Date,
    required: true,
    index: true
  },
  priority: {
    type: String,
    enum: ['low', 'medium', 'high', 'critical'],
    default: 'medium'
  },
  status: {
    type: String,
    enum: ['scheduled', 'sent', 'failed', 'cancelled'],
    default: 'scheduled',
    index: true
  },
  eventType: {
    type: String,
    enum: ['task_assignment', 'task_reminder', 'task_overdue', 'attendance_alert', 'system_notification'],
    required: true
  },
  createdBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  },
  sentAt: {
    type: Date
  },
  errorMessage: {
    type: String
  }
}, {
  timestamps: true
});

scheduledEmailSchema.index({ scheduledTime: 1, status: 1 });

module.exports = mongoose.model('ScheduledEmail', scheduledEmailSchema);