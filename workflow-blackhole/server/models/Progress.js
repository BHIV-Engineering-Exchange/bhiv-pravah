const mongoose = require("mongoose");

const ProgressSchema = new mongoose.Schema({
  task: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "Task",
    required: false, // Allow progress without specific task for general daily progress
  },
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "User",
    required: true,
  },
  date: {
    type: Date,
    default: Date.now,
    required: true,
  },
  progressPercentage: {
    type: Number,
    min: 0,
    max: 100,
    required: true,
  },
  notes: {
    type: String,
    trim: true,
  },
  blockers: {
    type: String,
    trim: true,
  },
  achievements: {
    type: String,
    trim: true,
  },
  progressImages: [{
    url: {
      type: String,
      required: true
    },
    publicId: String,
    uploadedAt: {
      type: Date,
      default: Date.now
    }
  }],
  createdAt: {
    type: Date,
    default: Date.now,
  },
  updatedAt: {
    type: Date,
    default: Date.now,
  },
});

// Update the updatedAt field before saving
ProgressSchema.pre("save", function (next) {
  this.updatedAt = Date.now();
  next();
});

module.exports = mongoose.model("Progress", ProgressSchema);

