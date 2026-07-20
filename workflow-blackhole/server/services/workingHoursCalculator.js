const moment = require('moment');
const DailyAttendance = require('../models/DailyAttendance');
const Aim = require('../models/Aim');

/**
 * Working Hours Calculator Service
 * Based on payroll-n8n logic with enhancements for biometric data and 30-minute allowances
 */
class WorkingHoursCalculator {
  constructor() {
    // Configurable parameters
    this.OVERTIME_MULTIPLIER = 1.5;
    this.MAX_REGULAR_HOURS_PER_DAY = 8;
    this.DAYS_IN_MONTH = 31;
    this.START_DAY_ALLOWANCE_MINUTES = 30; // 30 minutes allowance for start of day
    this.END_DAY_ALLOWANCE_MINUTES = 30;   // 30 minutes allowance for end of day
    this.BIOMETRIC_GRACE_PERIOD = 15;      // 15 minutes grace period for biometric sync
  }

  /**
   * Extract time from string format
   * Supports: "09:00", "09:00:00", "9:00 AM", etc.
   */
  extractTimes(text) {
    if (!text || typeof text !== 'string') return [];
    const timeRegex = /\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b/g;
    return text.match(timeRegex) || [];
  }

  /**
   * Parse time string to minutes since midnight
   * @param {string} timeStr - Time string (e.g., "09:30", "9:30 AM")
   * @returns {number} - Minutes since midnight
   */
  parseTimeToMinutes(timeStr) {
    if (!timeStr) return null;

    try {
      const timeString = timeStr.toString().trim();
      
      // Handle Date objects
      if (timeString instanceof Date || !isNaN(Date.parse(timeString))) {
        const date = new Date(timeString);
        return date.getHours() * 60 + date.getMinutes();
      }

      // Handle AM/PM format
      const isPM = /PM/i.test(timeString);
      const isAM = /AM/i.test(timeString);
      const cleanTime = timeString.replace(/AM|PM/gi, '').trim();
      
      const parts = cleanTime.split(':');
      let hours = parseInt(parts[0]) || 0;
      const minutes = parseInt(parts[1]) || 0;
      const seconds = parseInt(parts[2]) || 0;

      // Convert 12-hour to 24-hour format
      if (isPM && hours !== 12) hours += 12;
      if (isAM && hours === 12) hours = 0;

      return hours * 60 + minutes + Math.floor(seconds / 60);
    } catch (error) {
      console.error('Error parsing time:', timeStr, error);
      return null;
    }
  }

  /**
   * Calculate hours between two time points with midnight crossing handling
   * @param {string|Date} startTime - Start time
   * @param {string|Date} endTime - End time
   * @returns {Object} - { regularHours, overtimeHours, totalHours, note }
   */
  calculateWorkingHours(startTime, endTime, applyAllowance = true) {
    let inMinutes = this.parseTimeToMinutes(startTime);
    let outMinutes = this.parseTimeToMinutes(endTime);

    if (inMinutes === null || outMinutes === null) {
      return {
        regularHours: 0,
        overtimeHours: 0,
        totalHours: 0,
        note: 'missing_time_data'
      };
    }

    // Apply start/end day allowances (grant 30 minutes on both ends)
    if (applyAllowance) {
      inMinutes = Math.max(0, inMinutes - this.START_DAY_ALLOWANCE_MINUTES);
      outMinutes = outMinutes + this.END_DAY_ALLOWANCE_MINUTES;
    }

    // Handle midnight crossing (e.g., night shift)
    if (outMinutes < inMinutes) {
      outMinutes += 24 * 60; // Add 24 hours in minutes
    }

    // Calculate total minutes worked
    const totalMinutes = outMinutes - inMinutes;
    const totalHours = totalMinutes / 60;

    // Check for suspicious data
    if (totalHours > 24) {
      return {
        regularHours: 0,
        overtimeHours: 0,
        totalHours: 0,
        note: 'worked_over_24h'
      };
    }

    if (totalHours < 0) {
      return {
        regularHours: 0,
        overtimeHours: 0,
        totalHours: 0,
        note: 'invalid_time_range'
      };
    }

    // Calculate regular and overtime hours
    let regularHours = Math.min(totalHours, this.MAX_REGULAR_HOURS_PER_DAY);
    let overtimeHours = Math.max(0, totalHours - this.MAX_REGULAR_HOURS_PER_DAY);

    // Round to 2 decimal places
    regularHours = Math.round(regularHours * 100) / 100;
    overtimeHours = Math.round(overtimeHours * 100) / 100;
    const roundedTotal = Math.round(totalHours * 100) / 100;

    return {
      regularHours,
      overtimeHours,
      totalHours: roundedTotal,
      note: 'ok'
    };
  }

  /**
   * Calculate salary based on hours worked
   * @param {number} regularHours - Regular working hours
   * @param {number} overtimeHours - Overtime hours
   * @param {number} salaryMonthly - Monthly salary
   * @param {number} salaryDaily - Daily salary (optional)
   * @param {number} perHour - Hourly rate (optional)
   * @returns {Object} - Salary breakdown
   */
  calculateSalary(regularHours, overtimeHours, salaryMonthly = null, salaryDaily = null, perHour = null) {
    // Determine rates
    let dailySalary = salaryDaily;
    let hourlyRate = perHour;

    if (salaryMonthly && !dailySalary) {
      dailySalary = salaryMonthly / this.DAYS_IN_MONTH;
    }

    if (dailySalary && !hourlyRate) {
      hourlyRate = dailySalary / this.MAX_REGULAR_HOURS_PER_DAY;
    }

    if (!hourlyRate) {
      throw new Error('Unable to determine hourly rate');
    }

    const overtimeRate = hourlyRate * this.OVERTIME_MULTIPLIER;
    const regularEarnings = regularHours * hourlyRate;
    const overtimeEarnings = overtimeHours * overtimeRate;
    const totalEarnings = regularEarnings + overtimeEarnings;

    return {
      hourlyRate: Math.round(hourlyRate * 100) / 100,
      overtimeRate: Math.round(overtimeRate * 100) / 100,
      dailySalary: Math.round(dailySalary * 100) / 100,
      regularEarnings: Math.round(regularEarnings * 100) / 100,
      overtimeEarnings: Math.round(overtimeEarnings * 100) / 100,
      totalEarnings: Math.round(totalEarnings * 100) / 100
    };
  }

  /**
   * Process biometric data with intelligent time reconciliation
   * Prefers biometric data but validates against start/end day times
   * @param {Object} attendanceRecord - Daily attendance record
   * @returns {Object} - Processed hours data
   */
  processAttendanceRecord(attendanceRecord) {
    const result = {
      date: attendanceRecord.date,
      userId: attendanceRecord.user,
      source: 'none',
      reconciliationNote: '',
      discrepancy: null
    };

    // Extract times from different sources
    const biometricIn = attendanceRecord.biometricTimeIn;
    const biometricOut = attendanceRecord.biometricTimeOut;
    const startDayIn = attendanceRecord.startDayTime;
    const startDayOut = attendanceRecord.endDayTime;

    // Case 1: Both biometric and start/end day available
    if (biometricIn && biometricOut && startDayIn && startDayOut) {
      result.source = 'both';

      // Calculate hours from both sources
      const biometricHours = this.calculateWorkingHours(biometricIn, biometricOut, true);
      const startDayHours = this.calculateWorkingHours(startDayIn, startDayOut, true);

      // Check for discrepancies
      const timeDiff = Math.abs(biometricHours.totalHours - startDayHours.totalHours);
      
      if (timeDiff > 1) { // More than 1 hour difference
        result.discrepancy = {
          type: 'significant_time_difference',
          biometricHours: biometricHours.totalHours,
          startDayHours: startDayHours.totalHours,
          difference: timeDiff,
          severity: timeDiff > 2 ? 'high' : 'medium'
        };
        result.reconciliationNote = 'manual_review_needed';
      }

      // Prefer biometric data (more reliable) but flag discrepancy
      Object.assign(result, biometricHours);
      result.alternativeHours = startDayHours;

    // Case 2: Only biometric data available
    } else if (biometricIn && biometricOut) {
      result.source = 'biometric';
      const hours = this.calculateWorkingHours(biometricIn, biometricOut, true);
      Object.assign(result, hours);
      result.reconciliationNote = 'biometric_only';

    // Case 3: Only start/end day available
    } else if (startDayIn && startDayOut) {
      result.source = 'start_day';
      const hours = this.calculateWorkingHours(startDayIn, startDayOut, true);
      Object.assign(result, hours);
      result.reconciliationNote = 'start_day_only';

    // Case 4: Incomplete data
    } else {
      result.source = 'incomplete';
      result.regularHours = 0;
      result.overtimeHours = 0;
      result.totalHours = 0;
      result.note = 'missing_checkout';
      result.reconciliationNote = 'incomplete_data';

      // Try to detect missing checkout
      if ((biometricIn || startDayIn) && !(biometricOut || startDayOut)) {
        result.note = 'missing_checkout';
      } else if (!(biometricIn || startDayIn)) {
        result.note = 'no_times';
      }
    }

    return result;
  }

  /**
   * Calculate monthly working hours for an employee
   * @param {string} userId - User ID
   * @param {number} year - Year
   * @param {number} month - Month (1-12)
   * @returns {Object} - Monthly hours summary
   */
  async calculateMonthlyHours(userId, year, month) {
    try {
      const startDate = moment({ year, month: month - 1, day: 1 }).startOf('day');
      const endDate = moment({ year, month: month - 1 }).endOf('month').endOf('day');

      // Fetch attendance records
      const attendanceRecords = await DailyAttendance.find({
        user: userId,
        date: {
          $gte: startDate.toDate(),
          $lte: endDate.toDate()
        }
      }).sort({ date: 1 });

      // Fetch WFH days from AIM records
      const aimRecords = await Aim.find({
        user: userId,
        createdAt: {
          $gte: startDate.toDate(),
          $lte: endDate.toDate()
        }
      });

      const wfhDaysMap = new Map();
      aimRecords.forEach(aim => {
        if (aim.workSessionInfo?.workLocationType === 'Home' || 
            aim.workSessionInfo?.workLocationTag === 'WFH') {
          const dateKey = moment(aim.createdAt).format('YYYY-MM-DD');
          wfhDaysMap.set(dateKey, true);
        }
      });

      // Process each day
      const dailyBreakdown = [];
      let totalRegularHours = 0;
      let totalOvertimeHours = 0;
      let totalHoursWorked = 0;
      let daysPresent = 0;
      let daysAbsent = 0;
      let wfhDays = 0;
      let officeDays = 0;
      const discrepancies = [];

      for (const record of attendanceRecords) {
        const dateKey = moment(record.date).format('YYYY-MM-DD');
        const processedData = this.processAttendanceRecord(record);
        const isWFH = wfhDaysMap.has(dateKey);

        dailyBreakdown.push({
          date: dateKey,
          ...processedData,
          workLocation: isWFH ? 'WFH' : 'Office',
          isPresent: record.isPresent
        });

        if (record.isPresent) {
          daysPresent++;
          totalRegularHours += processedData.regularHours || 0;
          totalOvertimeHours += processedData.overtimeHours || 0;
          totalHoursWorked += processedData.totalHours || 0;

          if (isWFH) {
            wfhDays++;
          } else {
            officeDays++;
          }
        } else {
          daysAbsent++;
        }

        if (processedData.discrepancy) {
          discrepancies.push({
            date: dateKey,
            ...processedData.discrepancy
          });
        }
      }

      return {
        userId,
        period: {
          year,
          month,
          monthName: moment({ month: month - 1 }).format('MMMM')
        },
        summary: {
          daysPresent,
          daysAbsent,
          wfhDays,
          officeDays,
          totalHoursWorked: Math.round(totalHoursWorked * 100) / 100,
          totalRegularHours: Math.round(totalRegularHours * 100) / 100,
          totalOvertimeHours: Math.round(totalOvertimeHours * 100) / 100,
          averageHoursPerDay: daysPresent > 0 ? Math.round((totalHoursWorked / daysPresent) * 100) / 100 : 0
        },
        dailyBreakdown,
        discrepancies,
        calculatedAt: new Date(),
        notes: {
          allowanceApplied: `${this.START_DAY_ALLOWANCE_MINUTES} min start + ${this.END_DAY_ALLOWANCE_MINUTES} min end`,
          overtimeMultiplier: this.OVERTIME_MULTIPLIER,
          maxRegularHours: this.MAX_REGULAR_HOURS_PER_DAY
        }
      };
    } catch (error) {
      console.error('Error calculating monthly hours:', error);
      throw error;
    }
  }

  /**
   * Calculate salary for employee based on monthly hours
   * @param {Object} monthlyHours - Result from calculateMonthlyHours
   * @param {Object} salaryInfo - { salaryMonthly, salaryDaily, perHour }
   * @returns {Object} - Complete salary calculation
   */
  calculateMonthlySalary(monthlyHours, salaryInfo) {
    try {
      const salaryBreakdown = this.calculateSalary(
        monthlyHours.summary.totalRegularHours,
        monthlyHours.summary.totalOvertimeHours,
        salaryInfo.salaryMonthly,
        salaryInfo.salaryDaily,
        salaryInfo.perHour
      );

      // Calculate per-day salary details
      const dailySalaryBreakdown = monthlyHours.dailyBreakdown.map(day => {
        if (!day.isPresent || day.totalHours === 0) {
          return {
            ...day,
            earnings: 0,
            regularEarnings: 0,
            overtimeEarnings: 0
          };
        }

        const dayEarnings = this.calculateSalary(
          day.regularHours || 0,
          day.overtimeHours || 0,
          salaryInfo.salaryMonthly,
          salaryInfo.salaryDaily,
          salaryInfo.perHour
        );

        return {
          ...day,
          earnings: dayEarnings.totalEarnings,
          regularEarnings: dayEarnings.regularEarnings,
          overtimeEarnings: dayEarnings.overtimeEarnings
        };
      });

      return {
        ...monthlyHours,
        salary: salaryBreakdown,
        dailyBreakdown: dailySalaryBreakdown,
        totalSalaryEarned: salaryBreakdown.totalEarnings,
        status: monthlyHours.discrepancies.length > 0 ? 'needs_review' : 'processed'
      };
    } catch (error) {
      console.error('Error calculating monthly salary:', error);
      throw error;
    }
  }

  /**
   * Generate data quality report
   * @param {Object} monthlyHours - Result from calculateMonthlyHours
   * @returns {Object} - Quality report
   */
  generateQualityReport(monthlyHours) {
    const issues = [];
    const warnings = [];
    const info = [];

    // Check for missing data
    const incompleteDays = monthlyHours.dailyBreakdown.filter(d => d.note === 'missing_checkout' || d.note === 'no_times');
    if (incompleteDays.length > 0) {
      issues.push({
        type: 'incomplete_data',
        count: incompleteDays.length,
        days: incompleteDays.map(d => d.date),
        severity: 'high'
      });
    }

    // Check for discrepancies
    if (monthlyHours.discrepancies.length > 0) {
      const highSeverity = monthlyHours.discrepancies.filter(d => d.severity === 'high');
      if (highSeverity.length > 0) {
        issues.push({
          type: 'time_discrepancies',
          count: highSeverity.length,
          severity: 'high',
          details: highSeverity
        });
      }

      const mediumSeverity = monthlyHours.discrepancies.filter(d => d.severity === 'medium');
      if (mediumSeverity.length > 0) {
        warnings.push({
          type: 'time_discrepancies',
          count: mediumSeverity.length,
          severity: 'medium',
          details: mediumSeverity
        });
      }
    }

    // Check for excessive overtime
    const daysWithExcessiveOT = monthlyHours.dailyBreakdown.filter(d => d.overtimeHours > 4);
    if (daysWithExcessiveOT.length > 0) {
      warnings.push({
        type: 'excessive_overtime',
        count: daysWithExcessiveOT.length,
        days: daysWithExcessiveOT.map(d => ({ date: d.date, hours: d.overtimeHours })),
        severity: 'medium'
      });
    }

    // Check attendance rate
    const attendanceRate = (monthlyHours.summary.daysPresent / monthlyHours.dailyBreakdown.length) * 100;
    if (attendanceRate < 80) {
      warnings.push({
        type: 'low_attendance',
        rate: Math.round(attendanceRate),
        severity: 'medium'
      });
    }

    // Info about data sources
    const biometricOnly = monthlyHours.dailyBreakdown.filter(d => d.source === 'biometric').length;
    const startDayOnly = monthlyHours.dailyBreakdown.filter(d => d.source === 'start_day').length;
    const both = monthlyHours.dailyBreakdown.filter(d => d.source === 'both').length;

    info.push({
      type: 'data_sources',
      biometricOnly,
      startDayOnly,
      both,
      total: monthlyHours.dailyBreakdown.length
    });

    return {
      overallStatus: issues.length > 0 ? 'needs_attention' : warnings.length > 0 ? 'review_recommended' : 'good',
      issues,
      warnings,
      info,
      summary: {
        totalIssues: issues.length,
        totalWarnings: warnings.length,
        attendanceRate: Math.round(attendanceRate),
        dataCompleteness: Math.round(((monthlyHours.dailyBreakdown.length - incompleteDays.length) / monthlyHours.dailyBreakdown.length) * 100)
      }
    };
  }
}

module.exports = new WorkingHoursCalculator();
