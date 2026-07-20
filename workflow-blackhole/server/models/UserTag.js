const mongoose = require('mongoose');

const userTagSchema = new mongoose.Schema({
  user: { 
    type: mongoose.Schema.Types.ObjectId, 
    ref: 'User', 
    required: true, 
    unique: true,
    index: true
  },
  tag: { 
    type: String, 
    enum: ['Employee', 'Intern', 'Contractor', 'Freelancer', 'Consultant'], 
    required: true,
    index: true
  },
  subCategory: {
    type: String,
    enum: ['Full-time', 'Part-time', 'Remote', 'Hybrid', 'On-site'],
    default: 'Full-time'
  },
  level: {
    type: String,
    enum: ['Junior', 'Mid', 'Senior', 'Lead', 'Manager', 'Director'],
    default: 'Junior'
  },
  skills: [{
    name: String,
    proficiency: {
      type: String,
      enum: ['Beginner', 'Intermediate', 'Advanced', 'Expert'],
      default: 'Beginner'
    }
  }],
  contractDetails: {
    startDate: Date,
    endDate: Date,
    duration: String, // e.g., "6 months", "1 year"
    renewalDate: Date,
    isRenewable: { type: Boolean, default: true }
  },
  workingHours: {
    hoursPerDay: { type: Number, default: 8 },
    daysPerWeek: { type: Number, default: 5 },
    flexibleHours: { type: Boolean, default: false },
    coreHours: {
      start: String, // e.g., "09:00"
      end: String    // e.g., "17:00"
    }
  },
  benefits: {
    healthInsurance: { type: Boolean, default: false },
    paidLeave: { type: Boolean, default: true },
    performanceBonus: { type: Boolean, default: false },
    stockOptions: { type: Boolean, default: false },
    trainingBudget: { type: Number, default: 0 }
  },
  performance: {
    rating: { type: Number, min: 1, max: 5, default: 3 },
    lastReviewDate: Date,
    nextReviewDate: Date,
    goals: [{
      title: String,
      description: String,
      targetDate: Date,
      status: {
        type: String,
        enum: ['Not Started', 'In Progress', 'Completed', 'Overdue'],
        default: 'Not Started'
      }
    }]
  },
  mentor: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  team: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Department'
  },
  location: {
    office: String,
    city: String,
    country: String,
    timezone: String
  },
  emergencyContact: {
    name: String,
    relationship: String,
    phone: String,
    email: String
  },
  notes: {
    type: String,
    maxlength: 1000
  },
  isActive: {
    type: Boolean,
    default: true,
    index: true
  },
  createdAt: { 
    type: Date, 
    default: Date.now,
    index: true
  },
  updatedAt: { 
    type: Date, 
    default: Date.now 
  }
}, {
  timestamps: true
});

// Update the updatedAt field before saving
userTagSchema.pre('save', function(next) {
  this.updatedAt = Date.now();
  next();
});

// Compound indexes for efficient queries
userTagSchema.index({ tag: 1, isActive: 1 });
userTagSchema.index({ level: 1, tag: 1 });
userTagSchema.index({ team: 1, tag: 1 });

// Virtual for tag color coding
userTagSchema.virtual('tagColor').get(function() {
  const colors = {
    'Employee': '#3b82f6',
    'Intern': '#10b981',
    'Contractor': '#f59e0b',
    'Freelancer': '#8b5cf6',
    'Consultant': '#ef4444'
  };
  return colors[this.tag] || '#6b7280';
});

// Virtual for contract status
userTagSchema.virtual('contractStatus').get(function() {
  if (!this.contractDetails.endDate) return 'Permanent';
  
  const now = new Date();
  const endDate = new Date(this.contractDetails.endDate);
  const daysLeft = Math.ceil((endDate - now) / (1000 * 60 * 60 * 24));
  
  if (daysLeft < 0) return 'Expired';
  if (daysLeft <= 30) return 'Expiring Soon';
  return 'Active';
});

// Static method to get tag statistics
userTagSchema.statics.getTagStats = async function() {
  const stats = await this.aggregate([
    { $match: { isActive: true } },
    {
      $group: {
        _id: '$tag',
        count: { $sum: 1 },
        levels: { $push: '$level' }
      }
    },
    {
      $project: {
        tag: '$_id',
        count: 1,
        levelDistribution: {
          $reduce: {
            input: '$levels',
            initialValue: {},
            in: {
              $mergeObjects: [
                '$$value',
                { $arrayToObject: [[ { k: '$$this', v: 1 } ]] }
              ]
            }
          }
        }
      }
    }
  ]);
  
  return stats;
};

module.exports = mongoose.model('UserTag', userTagSchema);
