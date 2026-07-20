const geolib = require('geolib');

class GeolocationService {
  constructor() {
    // Office coordinates (should be in environment variables) - Blackhole Infiverse LLP Mumbai
    this.officeCoordinates = {
      latitude: parseFloat(process.env.OFFICE_LAT) || 19.1628987,
      longitude: parseFloat(process.env.OFFICE_LNG) || 72.8355871
    };
    
    // Default office radius in meters
    this.officeRadius = parseInt(process.env.OFFICE_RADIUS) || 100;
    
    // Multiple office locations support
    this.officeLocations = this.parseOfficeLocations();
  }

  /**
   * Parse multiple office locations from environment variables
   */
  parseOfficeLocations() {
    const locations = [];
    
    // Add main office
    locations.push({
      id: 'main',
      name: 'Main Office',
      latitude: this.officeCoordinates.latitude,
      longitude: this.officeCoordinates.longitude,
      radius: this.officeRadius,
      address: process.env.OFFICE_ADDRESS || 'Main Office Location'
    });

    // Parse additional office locations
    const additionalOffices = process.env.ADDITIONAL_OFFICES;
    if (additionalOffices) {
      try {
        const offices = JSON.parse(additionalOffices);
        offices.forEach((office, index) => {
          locations.push({
            id: office.id || `office_${index + 1}`,
            name: office.name || `Office ${index + 1}`,
            latitude: parseFloat(office.latitude),
            longitude: parseFloat(office.longitude),
            radius: parseInt(office.radius) || this.officeRadius,
            address: office.address || `Office ${index + 1} Location`
          });
        });
      } catch (error) {
        console.warn('Failed to parse additional office locations:', error.message);
      }
    }

    return locations;
  }

  /**
   * Validate if user is within office premises
   */
  validateLocation(userLatitude, userLongitude, options = {}) {
    try {
      const userCoordinates = {
        latitude: parseFloat(userLatitude),
        longitude: parseFloat(userLongitude)
      };

      // Validate coordinates
      if (!this.isValidCoordinate(userCoordinates.latitude, userCoordinates.longitude)) {
        return {
          isValid: false,
          error: 'Invalid coordinates provided',
          code: 'INVALID_COORDINATES'
        };
      }

      // Check against all office locations
      const results = this.officeLocations.map(office => {
        const distance = geolib.getDistance(
          { latitude: office.latitude, longitude: office.longitude },
          userCoordinates
        );

        const isWithinRadius = distance <= office.radius;

        return {
          office: {
            id: office.id,
            name: office.name,
            address: office.address
          },
          distance,
          isWithinRadius,
          accuracy: this.calculateAccuracy(distance, office.radius)
        };
      });

      // Find the closest valid office
      const validOffices = results.filter(result => result.isWithinRadius);
      const closestOffice = results.reduce((closest, current) => 
        current.distance < closest.distance ? current : closest
      );

      if (validOffices.length > 0) {
        return {
          isValid: true,
          office: validOffices[0].office,
          distance: validOffices[0].distance,
          accuracy: validOffices[0].accuracy,
          allResults: results
        };
      } else {
        return {
          isValid: false,
          error: `You must be within ${this.officeRadius}m of an office location`,
          code: 'OUTSIDE_OFFICE_RADIUS',
          closestOffice: {
            office: closestOffice.office,
            distance: closestOffice.distance,
            requiredRadius: this.officeRadius
          },
          allResults: results
        };
      }

    } catch (error) {
      return {
        isValid: false,
        error: `Geolocation validation failed: ${error.message}`,
        code: 'VALIDATION_ERROR'
      };
    }
  }

  /**
   * Calculate distance between two points
   */
  calculateDistance(lat1, lng1, lat2, lng2) {
    return geolib.getDistance(
      { latitude: lat1, longitude: lng1 },
      { latitude: lat2, longitude: lng2 }
    );
  }

  /**
   * Check if coordinates are valid
   */
  isValidCoordinate(latitude, longitude) {
    return (
      typeof latitude === 'number' &&
      typeof longitude === 'number' &&
      latitude >= -90 && latitude <= 90 &&
      longitude >= -180 && longitude <= 180 &&
      !isNaN(latitude) && !isNaN(longitude)
    );
  }

  /**
   * Calculate accuracy percentage based on distance
   */
  calculateAccuracy(distance, radius) {
    if (distance <= radius) {
      return Math.max(0, Math.round((1 - distance / radius) * 100));
    }
    return 0;
  }

  /**
   * Get office information
   */
  getOfficeLocations() {
    return this.officeLocations.map(office => ({
      id: office.id,
      name: office.name,
      address: office.address,
      radius: office.radius,
      // Don't expose exact coordinates for security
      hasLocation: true
    }));
  }

  /**
   * Validate location with enhanced security checks
   */
  validateLocationWithSecurity(userLatitude, userLongitude, options = {}) {
    const basicValidation = this.validateLocation(userLatitude, userLongitude, options);
    
    if (!basicValidation.isValid) {
      return basicValidation;
    }

    // Additional security checks
    const securityChecks = {
      spoofingDetection: this.detectLocationSpoofing(userLatitude, userLongitude, options),
      velocityCheck: this.checkVelocity(userLatitude, userLongitude, options),
      timeBasedCheck: this.checkTimeBasedPatterns(userLatitude, userLongitude, options)
    };

    // If any security check fails, flag as suspicious
    const suspiciousActivity = Object.values(securityChecks).some(check => check.suspicious);

    return {
      ...basicValidation,
      security: {
        checks: securityChecks,
        suspicious: suspiciousActivity,
        riskLevel: this.calculateRiskLevel(securityChecks)
      }
    };
  }

  /**
   * Detect potential location spoofing
   */
  detectLocationSpoofing(latitude, longitude, options = {}) {
    const checks = {
      accuracyCheck: options.accuracy && options.accuracy < 10, // Very high accuracy might be suspicious
      patternCheck: this.checkForRepeatingPatterns(latitude, longitude),
      deviceCheck: this.validateDeviceConsistency(options.deviceInfo)
    };

    const suspicious = Object.values(checks).some(check => check === true);

    return {
      suspicious,
      details: checks,
      confidence: suspicious ? 0.7 : 0.1
    };
  }

  /**
   * Check velocity between location updates
   */
  checkVelocity(latitude, longitude, options = {}) {
    if (!options.previousLocation || !options.previousTimestamp) {
      return { suspicious: false, reason: 'No previous location data' };
    }

    const distance = this.calculateDistance(
      options.previousLocation.latitude,
      options.previousLocation.longitude,
      latitude,
      longitude
    );

    const timeDiff = (Date.now() - options.previousTimestamp) / 1000; // seconds
    const velocity = distance / timeDiff; // meters per second

    // Flag if velocity suggests impossible movement (e.g., > 50 m/s = 180 km/h)
    const maxReasonableVelocity = 50;
    const suspicious = velocity > maxReasonableVelocity;

    return {
      suspicious,
      velocity,
      distance,
      timeDiff,
      reason: suspicious ? 'Impossible movement velocity detected' : 'Normal movement'
    };
  }

  /**
   * Check for time-based patterns
   */
  checkTimeBasedPatterns(latitude, longitude, options = {}) {
    // This would typically check against historical data
    // For now, return basic time validation
    const currentHour = new Date().getHours();
    const isBusinessHours = currentHour >= 6 && currentHour <= 22;

    return {
      suspicious: !isBusinessHours && !options.allowAfterHours,
      reason: isBusinessHours ? 'Within business hours' : 'Outside business hours',
      currentHour
    };
  }

  /**
   * Check for repeating coordinate patterns
   */
  checkForRepeatingPatterns(latitude, longitude) {
    // Simple check for exact coordinate repetition
    // In a real implementation, this would check against a database of recent locations
    const coordString = `${latitude.toFixed(6)},${longitude.toFixed(6)}`;
    
    // This is a simplified check - in production, you'd maintain a cache of recent locations
    return false;
  }

  /**
   * Validate device consistency
   */
  validateDeviceConsistency(deviceInfo) {
    if (!deviceInfo) return false;
    
    // Check for suspicious device information patterns
    const suspiciousPatterns = [
      /emulator/i,
      /simulator/i,
      /fake/i,
      /mock/i
    ];

    return suspiciousPatterns.some(pattern => 
      pattern.test(deviceInfo.userAgent || '') ||
      pattern.test(deviceInfo.deviceType || '')
    );
  }

  /**
   * Calculate overall risk level
   */
  calculateRiskLevel(securityChecks) {
    let riskScore = 0;
    
    if (securityChecks.spoofingDetection.suspicious) riskScore += 3;
    if (securityChecks.velocityCheck.suspicious) riskScore += 2;
    if (securityChecks.timeBasedCheck.suspicious) riskScore += 1;

    if (riskScore >= 4) return 'HIGH';
    if (riskScore >= 2) return 'MEDIUM';
    return 'LOW';
  }

  /**
   * Generate location report for admin dashboard
   */
  generateLocationReport(validations) {
    const totalValidations = validations.length;
    const successfulValidations = validations.filter(v => v.isValid).length;
    const suspiciousValidations = validations.filter(v => v.security?.suspicious).length;

    const officeUsage = this.officeLocations.map(office => {
      const usage = validations.filter(v => v.office?.id === office.id).length;
      return {
        office: office.name,
        usage,
        percentage: totalValidations > 0 ? Math.round((usage / totalValidations) * 100) : 0
      };
    });

    return {
      summary: {
        totalValidations,
        successfulValidations,
        successRate: totalValidations > 0 ? Math.round((successfulValidations / totalValidations) * 100) : 0,
        suspiciousValidations,
        suspiciousRate: totalValidations > 0 ? Math.round((suspiciousValidations / totalValidations) * 100) : 0
      },
      officeUsage,
      securityMetrics: {
        spoofingAttempts: validations.filter(v => v.security?.checks.spoofingDetection.suspicious).length,
        velocityViolations: validations.filter(v => v.security?.checks.velocityCheck.suspicious).length,
        timeViolations: validations.filter(v => v.security?.checks.timeBasedCheck.suspicious).length
      }
    };
  }
}

module.exports = new GeolocationService();
