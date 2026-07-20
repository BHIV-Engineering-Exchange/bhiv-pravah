const Attendance = require('../models/Attendance');
const User = require('../models/User');
const UserTag = require('../models/UserTag');
const Leave = require('../models/Leave');
const groqAIService = require('./groqAIService');

class AttendanceService {
  constructor() {
    this.verificationThreshold = 15; // minutes
    this.workingHoursStart = 9; // 9 AM
    this.workingHoursEnd = 17; // 5 PM
    this.standardWorkingHours = 8;
  }

  /**
   * Verify attendance for a specific user and date
   */
  async verifyAttendance(userId, date) {
    try {
      const targetDate = new Date(date);
      targetDate.setHours(0, 0, 0, 0);

      const attendance = await Attendance.findOne({
        user: userId,
        date: targetDate
      }).populate('user', 'name email').populate('leaveReference');

      if (!attendance) {
        return {
          isVerified: false,
          status: 'No Record',
          message: 'No attendance record found for this date',
          recommendation: 'Create manual attendance record or check if employee was on leave'
        };
      }

      // Check if it's a leave day
      if (attendance.isLeave) {
        return {
          isVerified: true,
          status: 'On Leave',
          message: `Employee was on ${attendance.leaveType} leave`,
          leaveDetails: attendance.leaveReference,
          recommendation: 'No action required - legitimate leave'
        };
      }

      // Verify biometric and start day data
      const verification = this.performVerification(attendance);
      
      // Update attendance record with verification results
      attendance.isVerified = verification.isVerified;
      attendance.verificationMethod = verification.method;
      attendance.hasDiscrepancy = verification.hasDiscrepancy;
      attendance.discrepancyReason = verification.discrepancyReason;
      attendance.discrepancyDetails = verification.discrepancyDetails;

      await attendance.save();

      return {
        ...verification,
        attendance: attendance.toObject(),
        statusDisplay: attendance.statusDisplay,
        statusColor: attendance.statusColor
      };

    } catch (error) {
      console.error('Attendance verification error:', error);
      throw new Error(`Failed to verify attendance: ${error.message}`);
    }
  }

  /**
   * Perform verification logic
   */
  performVerification(attendance) {
    const verification = {
      isVerified: false,
      method: 'Manual',
      hasDiscrepancy: false,
      discrepancyReason: null,
      discrepancyDetails: {},
      score: 0,
      recommendations: []
    };

    // Check if both biometric and start day data exist
    if (attendance.biometricTimeIn && attendance.startDayTime) {
      const timeDiff = Math.abs(
        attendance.biometricTimeIn.getTime() - attendance.startDayTime.getTime()
      ) / (1000 * 60); // minutes

      if (timeDiff <= this.verificationThreshold) {
        verification.isVerified = true;
        verification.method = 'Both';
        verification.score = 100;
        verification.recommendations.push('Perfect attendance verification');
      } else {
        verification.hasDiscrepancy = true;
        verification.discrepancyReason = 'Time Mismatch';
        verification.discrepancyDetails.timeDifference = Math.round(timeDiff);
        verification.score = Math.max(0, 100 - (timeDiff * 2));
        verification.recommendations.push(`Time difference of ${Math.round(timeDiff)} minutes detected`);
      }
    } else if (attendance.biometricTimeIn || attendance.startDayTime) {
      verification.isVerified = true;
      verification.method = attendance.biometricTimeIn ? 'Biometric' : 'StartDay';
      verification.score = 75;
      verification.recommendations.push('Single source verification - consider implementing dual verification');
    } else {
      verification.score = 0;
      verification.recommendations.push('No attendance data available - manual verification required');
    }

    // Additional checks
    this.performAdditionalChecks(attendance, verification);

    return verification;
  }

  /**
   * Perform additional verification checks
   */
  performAdditionalChecks(attendance, verification) {
    // Check working hours compliance
    if (attendance.biometricTimeIn || attendance.startDayTime) {
      const checkInTime = attendance.biometricTimeIn || attendance.startDayTime;
      const checkInHour = checkInTime.getHours();

      if (checkInHour < this.workingHoursStart - 2 || checkInHour > this.workingHoursStart + 2) {
        verification.recommendations.push('Unusual check-in time detected');
        verification.score = Math.max(verification.score - 10, 0);
      }
    }

    // Check location consistency
    if (attendance.startDayLocation && attendance.endDayLocation) {
      const distance = this.calculateDistance(
        attendance.startDayLocation.latitude,
        attendance.startDayLocation.longitude,
        attendance.endDayLocation.latitude,
        attendance.endDayLocation.longitude
      );

      if (distance > 1000) { // More than 1km difference
        verification.recommendations.push('Significant location difference between start and end');
        verification.score = Math.max(verification.score - 5, 0);
      }
    }

    // Check hours worked
    if (attendance.hoursWorked > 12) {
      verification.recommendations.push('Excessive working hours detected - verify overtime');
    } else if (attendance.hoursWorked < 4) {
      verification.recommendations.push('Insufficient working hours - check for half day or early departure');
      verification.score = Math.max(verification.score - 20, 0);
    }
  }

  /**
   * Bulk verify attendance for multiple users
   */
  async bulkVerifyAttendance(userIds, startDate, endDate) {
    const results = [];
    const start = new Date(startDate);
    const end = new Date(endDate);

    for (const userId of userIds) {
      const userResults = [];
      const currentDate = new Date(start);

      while (currentDate <= end) {
        try {
          const verification = await this.verifyAttendance(userId, currentDate);
          userResults.push({
            date: new Date(currentDate),
            ...verification
          });
        } catch (error) {
          userResults.push({
            date: new Date(currentDate),
            error: error.message,
            isVerified: false
          });
        }

        currentDate.setDate(currentDate.getDate() + 1);
      }

      // Get user info
      const user = await User.findById(userId).select('name email');
      results.push({
        user,
        results: userResults,
        summary: this.calculateUserSummary(userResults)
      });
    }

    return {
      results,
      summary: this.calculateBulkSummary(results)
    };
  }

  /**
   * Calculate summary for a user's verification results
   */
  calculateUserSummary(userResults) {
    const total = userResults.length;
    const verified = userResults.filter(r => r.isVerified).length;
    const discrepancies = userResults.filter(r => r.hasDiscrepancy).length;
    const avgScore = userResults.reduce((sum, r) => sum + (r.score || 0), 0) / total;

    return {
      totalDays: total,
      verifiedDays: verified,
      discrepancies,
      verificationRate: Math.round((verified / total) * 100),
      averageScore: Math.round(avgScore),
      reliability: this.calculateReliabilityGrade(verified / total, avgScore / 100)
    };
  }

  /**
   * Calculate bulk summary
   */
  calculateBulkSummary(results) {
    const totalUsers = results.length;
    const totalDays = results.reduce((sum, r) => sum + r.summary.totalDays, 0);
    const totalVerified = results.reduce((sum, r) => sum + r.summary.verifiedDays, 0);
    const totalDiscrepancies = results.reduce((sum, r) => sum + r.summary.discrepancies, 0);

    return {
      totalUsers,
      totalDays,
      totalVerified,
      totalDiscrepancies,
      overallVerificationRate: Math.round((totalVerified / totalDays) * 100),
      discrepancyRate: Math.round((totalDiscrepancies / totalDays) * 100)
    };
  }

  /**
   * Generate attendance insights using AI
   */
  async generateAttendanceInsights(userId, period = 30) {
    try {
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - period);

      const attendanceRecords = await Attendance.find({
        user: userId,
        date: { $gte: startDate, $lte: endDate }
      }).sort({ date: 1 });

      if (attendanceRecords.length === 0) {
        return {
          insights: ['No attendance data available for analysis'],
          patterns: [],
          recommendations: ['Ensure regular attendance tracking']
        };
      }

      // Analyze patterns
      const patterns = this.analyzeAttendancePatterns(attendanceRecords);
      
      // Generate AI insights if available
      let aiInsights = [];
      try {
        const context = {
          userId,
          period,
          attendanceData: attendanceRecords.map(r => ({
            date: r.date,
            isPresent: r.isPresent,
            hoursWorked: r.hoursWorked,
            hasDiscrepancy: r.hasDiscrepancy
          })),
          patterns
        };

        // Use AI service for deeper insights
        aiInsights = await this.generateAIInsights(context);
      } catch (aiError) {
        console.warn('AI insights generation failed:', aiError.message);
      }

      return {
        period: { startDate, endDate, days: period },
        statistics: this.calculateAttendanceStatistics(attendanceRecords),
        patterns,
        insights: aiInsights.length > 0 ? aiInsights : this.generateBasicInsights(patterns),
        recommendations: this.generateRecommendations(patterns)
      };

    } catch (error) {
      console.error('Generate insights error:', error);
      throw new Error(`Failed to generate attendance insights: ${error.message}`);
    }
  }

  /**
   * Analyze attendance patterns
   */
  analyzeAttendancePatterns(records) {
    const patterns = {
      weeklyPattern: this.analyzeWeeklyPattern(records),
      punctualityTrend: this.analyzePunctualityTrend(records),
      workingHoursPattern: this.analyzeWorkingHoursPattern(records),
      consistencyScore: this.calculateConsistencyScore(records)
    };

    return patterns;
  }

  /**
   * Analyze weekly attendance pattern
   */
  analyzeWeeklyPattern(records) {
    const dayOfWeekStats = Array(7).fill(0).map(() => ({ present: 0, total: 0 }));

    records.forEach(record => {
      const dayOfWeek = record.date.getDay();
      dayOfWeekStats[dayOfWeek].total++;
      if (record.isPresent) {
        dayOfWeekStats[dayOfWeek].present++;
      }
    });

    const weekDays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    
    return dayOfWeekStats.map((stats, index) => ({
      day: weekDays[index],
      attendanceRate: stats.total > 0 ? Math.round((stats.present / stats.total) * 100) : 0,
      totalDays: stats.total
    }));
  }

  /**
   * Analyze punctuality trend
   */
  analyzePunctualityTrend(records) {
    const punctualityData = records
      .filter(r => r.biometricTimeIn || r.startDayTime)
      .map(record => {
        const checkInTime = record.biometricTimeIn || record.startDayTime;
        const checkInHour = checkInTime.getHours() + checkInTime.getMinutes() / 60;
        const isLate = checkInHour > this.workingHoursStart + 0.25; // 15 minutes grace period
        
        return {
          date: record.date,
          checkInTime: checkInHour,
          isLate,
          minutesLate: isLate ? Math.round((checkInHour - this.workingHoursStart) * 60) : 0
        };
      });

    const lateCount = punctualityData.filter(d => d.isLate).length;
    const avgCheckInTime = punctualityData.reduce((sum, d) => sum + d.checkInTime, 0) / punctualityData.length;

    return {
      punctualityRate: Math.round(((punctualityData.length - lateCount) / punctualityData.length) * 100),
      averageCheckInTime: this.formatTime(avgCheckInTime),
      lateCount,
      averageLateness: lateCount > 0 ? 
        Math.round(punctualityData.filter(d => d.isLate).reduce((sum, d) => sum + d.minutesLate, 0) / lateCount) : 0
    };
  }

  /**
   * Helper methods
   */
  calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371e3; // Earth's radius in meters
    const φ1 = lat1 * Math.PI/180;
    const φ2 = lat2 * Math.PI/180;
    const Δφ = (lat2-lat1) * Math.PI/180;
    const Δλ = (lng2-lng1) * Math.PI/180;

    const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ/2) * Math.sin(Δλ/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));

    return R * c;
  }

  calculateReliabilityGrade(verificationRate, scoreRate) {
    const combined = (verificationRate + scoreRate) / 2;
    if (combined >= 0.9) return 'A+';
    if (combined >= 0.8) return 'A';
    if (combined >= 0.7) return 'B';
    if (combined >= 0.6) return 'C';
    return 'D';
  }

  formatTime(decimalHours) {
    const hours = Math.floor(decimalHours);
    const minutes = Math.round((decimalHours - hours) * 60);
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
  }

  analyzeWorkingHoursPattern(records) {
    const workingHoursData = records
      .filter(r => r.hoursWorked > 0)
      .map(r => r.hoursWorked);

    if (workingHoursData.length === 0) {
      return { averageHours: 0, consistency: 'No data' };
    }

    const avgHours = workingHoursData.reduce((sum, h) => sum + h, 0) / workingHoursData.length;
    const variance = workingHoursData.reduce((sum, h) => sum + Math.pow(h - avgHours, 2), 0) / workingHoursData.length;
    const standardDeviation = Math.sqrt(variance);

    return {
      averageHours: Math.round(avgHours * 100) / 100,
      standardDeviation: Math.round(standardDeviation * 100) / 100,
      consistency: standardDeviation < 1 ? 'High' : standardDeviation < 2 ? 'Medium' : 'Low'
    };
  }

  calculateConsistencyScore(records) {
    const presentDays = records.filter(r => r.isPresent).length;
    const totalDays = records.length;
    const attendanceRate = presentDays / totalDays;

    const verifiedDays = records.filter(r => r.isVerified).length;
    const verificationRate = verifiedDays / totalDays;

    const discrepancies = records.filter(r => r.hasDiscrepancy).length;
    const discrepancyRate = discrepancies / totalDays;

    const score = (attendanceRate * 0.4) + (verificationRate * 0.4) - (discrepancyRate * 0.2);
    return Math.max(0, Math.min(100, Math.round(score * 100)));
  }

  calculateAttendanceStatistics(records) {
    const total = records.length;
    const present = records.filter(r => r.isPresent).length;
    const verified = records.filter(r => r.isVerified).length;
    const discrepancies = records.filter(r => r.hasDiscrepancy).length;
    const totalHours = records.reduce((sum, r) => sum + (r.hoursWorked || 0), 0);

    return {
      totalDays: total,
      presentDays: present,
      absentDays: total - present,
      verifiedDays: verified,
      discrepancies,
      attendanceRate: Math.round((present / total) * 100),
      verificationRate: Math.round((verified / total) * 100),
      discrepancyRate: Math.round((discrepancies / total) * 100),
      totalHours: Math.round(totalHours * 100) / 100,
      averageHoursPerDay: Math.round((totalHours / present) * 100) / 100
    };
  }

  generateBasicInsights(patterns) {
    const insights = [];

    if (patterns.punctualityTrend.punctualityRate < 80) {
      insights.push('Punctuality needs improvement - consider flexible working hours');
    }

    if (patterns.consistencyScore < 70) {
      insights.push('Attendance consistency is below average');
    }

    if (patterns.workingHoursPattern.consistency === 'Low') {
      insights.push('Working hours vary significantly - review workload distribution');
    }

    return insights.length > 0 ? insights : ['Overall attendance pattern is satisfactory'];
  }

  generateRecommendations(patterns) {
    const recommendations = [];

    if (patterns.punctualityTrend.punctualityRate < 90) {
      recommendations.push('Implement punctuality improvement program');
    }

    if (patterns.consistencyScore < 80) {
      recommendations.push('Review attendance policies and provide feedback');
    }

    return recommendations;
  }

  async generateAIInsights(context) {
    // This would integrate with your AI service
    // For now, return basic insights
    return [
      'AI analysis suggests reviewing attendance patterns for optimization opportunities',
      'Consider implementing flexible working arrangements based on attendance data'
    ];
  }
}

module.exports = new AttendanceService();
