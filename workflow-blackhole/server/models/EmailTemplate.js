const mongoose = require('mongoose');

const emailTemplateSchema = new mongoose.Schema({
  templateId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  name: {
    type: String,
    required: true
  },
  subject: {
    type: String,
    required: true
  },
  htmlBody: {
    type: String,
    required: true
  },
  textBody: {
    type: String
  },
  category: {
    type: String,
    enum: ['task', 'attendance', 'system', 'notification'],
    default: 'task'
  },
  isActive: {
    type: Boolean,
    default: true
  },
  createdBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true
  }
}, {
  timestamps: true
});

module.exports = mongoose.model('EmailTemplate', emailTemplateSchema);