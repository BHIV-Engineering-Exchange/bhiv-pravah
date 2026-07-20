const mongoose = require('mongoose');

const salaryAdjustmentSchema = new mongoose.Schema({
  attendanceId: { type: mongoose.Schema.Types.ObjectId, ref: 'SalaryAttendance', required: true },
  userId: { type: String, required: true },
  originalSalary: { type: Number, required: true },
  adjustedSalary: { type: Number, required: true },
  adjustmentReason: { type: String, required: true },
  adjustedBy: { type: String, required: true }, // Admin user ID
  feedbackId: { type: mongoose.Schema.Types.ObjectId, ref: 'Feedback' },
  monthYear: { type: String, required: true },
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('SalaryAdjustment', salaryAdjustmentSchema);