const mongoose = require('mongoose');

const locationDiscrepancySchema = new mongoose.Schema({
  user: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    index: true
  },
  attendance: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'Attendance',
    required: true,
    index: true
  },
  date: {
    type: Date,
    required: true,
    index: true
  },
  startLocation: {
    latitude: { type: Number, required: true },
    longitude: { type: Number, required: true },
    address: String,
    accuracy: Number,
    timestamp: Date
  },
  endLocation: {
    latitude: { type: Number, required: true },
    longitude: { type: Number, required: true },
    address: String,
    accuracy: Number,
    timestamp: Date
  },
  distance: {
    type: Number,
    required: true, // Distance in meters
    index: true
  },
  distanceKm: {
    type: Number,
    required: true // Distance in kilometers
  },
  threshold: {
    type: Number,
    default: 5000 // Default threshold: 5km (5000 meters)
  },
  severity: {
    type: String,
    enum: ['low', 'medium', 'high', 'critical'],
    default: 'medium',
    index: true
  },
  status: {
    type: String,
    enum: ['pending', 'reviewed', 'resolved', 'dismissed'],
    default: 'pending',
    index: true
  },
  reviewedBy: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User'
  },
  reviewedAt: Date,
  resolutionNotes: String,
  alertSent: {
    type: Boolean,
    default: false
  },
  alertSentAt: Date
}, {
  timestamps: true,
  collection: 'location_discrepancies'
});

// Indexes for efficient queries
locationDiscrepancySchema.index({ user: 1, date: -1 });
locationDiscrepancySchema.index({ status: 1, severity: 1 });
locationDiscrepancySchema.index({ date: -1 });
locationDiscrepancySchema.index({ distance: -1 });

// Static method to calculate distance between two coordinates
locationDiscrepancySchema.statics.calculateDistance = function(lat1, lon1, lat2, lon2) {
  const R = 6371; // Radius of the Earth in kilometers
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = 
    Math.sin(dLat/2) * Math.sin(dLat/2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
    Math.sin(dLon/2) * Math.sin(dLon/2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
  const distanceKm = R * c;
  const distanceM = distanceKm * 1000;
  
  return {
    meters: Math.round(distanceM),
    kilometers: Math.round(distanceKm * 100) / 100
  };
};

// Static method to determine severity based on distance
locationDiscrepancySchema.statics.determineSeverity = function(distanceMeters, threshold = 5000) {
  if (distanceMeters >= threshold * 3) {
    return 'critical'; // > 15km
  } else if (distanceMeters >= threshold * 2) {
    return 'high'; // > 10km
  } else if (distanceMeters >= threshold) {
    return 'medium'; // > 5km
  } else {
    return 'low'; // < 5km
  }
};

// Static method to create discrepancy record
locationDiscrepancySchema.statics.createDiscrepancy = async function(data) {
  const { user, attendance, date, startLocation, endLocation, threshold = 5000 } = data;
  
  if (!startLocation || !endLocation || !startLocation.latitude || !endLocation.latitude) {
    throw new Error('Both start and end locations are required');
  }
  
  const distance = this.calculateDistance(
    startLocation.latitude,
    startLocation.longitude,
    endLocation.latitude,
    endLocation.longitude
  );
  
  // Only create discrepancy if distance exceeds threshold
  if (distance.meters <= threshold) {
    return null; // No discrepancy
  }
  
  const severity = this.determineSeverity(distance.meters, threshold);
  
  // Check if discrepancy already exists for this attendance record
  const existing = await this.findOne({ attendance });
  if (existing) {
    // Update existing record
    existing.startLocation = startLocation;
    existing.endLocation = endLocation;
    existing.distance = distance.meters;
    existing.distanceKm = distance.kilometers;
    existing.severity = severity;
    existing.status = 'pending';
    existing.alertSent = false;
    return existing.save();
  }
  
  return this.create({
    user,
    attendance,
    date,
    startLocation: {
      ...startLocation,
      timestamp: startLocation.timestamp || new Date()
    },
    endLocation: {
      ...endLocation,
      timestamp: endLocation.timestamp || new Date()
    },
    distance: distance.meters,
    distanceKm: distance.kilometers,
    threshold,
    severity
  });
};

module.exports = mongoose.model('LocationDiscrepancy', locationDiscrepancySchema);

