const moment = require('moment');
const Attendance = require('../models/Attendance');
const Salary = require('../models/Salary');
const UserTag = require('../models/UserTag');
const User = require('../models/User');

class SalaryCalculator {
  constructor() {
    this.defaultWorkingDays = 22; // Standard working days per month
    this.standardWorkingHours = 8;
    this.overtimeMultiplier = 1.5;
    this.lateDeductionRate = 0.02; // 2% deduction per late day
    this.absentDeductionRate = 1; // Full day deduction for absence
  }

  /**
   * Calculate comprehensive salary for a user for a specific month
   */
  async calculateMonthlySalary(userId, year, month, workingDays = null) {
    try {
      console.log(`Calculating salary for user ${userId}, ${year}-${month}`);

      // Get user and salary information
      const user = await User.findById(userId);
      if (!user) {
        throw new Error('User not found');
      }

      const salaryRecord = await Salary.findOne({ user: userId });
      if (!salaryRecord) {
        throw new Error('Salary record not found for user');
      }

      const userTag = await UserTag.findOne({ user: userId });
      
      // Set working days (from parameter, user config, or default)
      const totalWorkingDays = workingDays || 
                              userTag?.workingHours?.daysPerWeek * 4.33 || 
                              this.defaultWorkingDays;

      // Get attendance data for the month
      const startDate = moment({ year, month: month - 1, day: 1 }).startOf('day');
      const endDate = moment({ year, month: month - 1 }).endOf('month').endOf('day');

      const attendanceRecords = await Attendance.find({
        user: userId,
        date: {
          $gte: startDate.toDate(),
          $lte: endDate.toDate()
        }
      }).sort({ date: 1 });

      // Analyze attendance patterns
      const attendanceAnalysis = this.analyzeAttendance(attendanceRecords, userTag);
      
      // Calculate genuine working hours
      const genuineHours = this.calculateGenuineWorkingHours(attendanceRecords);
      
      // Calculate salary components
      const salaryComponents = this.calculateSalaryComponents(
        salaryRecord,
        attendanceAnalysis,
        genuineHours,
        totalWorkingDays
      );

      // Generate recommendations
      const recommendations = this.generateRecommendations(
        attendanceAnalysis,
        genuineHours,
        salaryComponents
      );

      return {
        user: {
          id: user._id,
          name: user.name,
          email: user.email,
          employeeType: userTag?.tag || 'Employee'
        },
        period: {
          year,
          month,
          monthName: moment({ month: month - 1 }).format('MMMM'),
          totalWorkingDays,
          actualWorkingDays: attendanceAnalysis.presentDays
        },
        attendance: attendanceAnalysis,
        workingHours: genuineHours,
        salary: salaryComponents,
        recommendations,
        calculatedAt: new Date(),
        calculatedBy: 'Automated System'
      };

    } catch (error) {
      console.error('Error calculating salary:', error);
      throw error;
    }
  }

  /**
   * Analyze attendance patterns and discrepancies
   */
  analyzeAttendance(attendanceRecords, userTag) {
    const analysis = {
      totalDays: attendanceRecords.length,
      presentDays: 0,
      absentDays: 0,
      lateDays: 0,
      earlyDepartures: 0,
      perfectDays: 0,
      discrepancies: [],
      biometricOnlyDays: 0,
      startDayOnlyDays: 0,
      bothSourcesDays: 0,
      averageArrivalTime: null,
      averageDepartureTime: null,
      attendanceRate: 0
    };

    const arrivalTimes = [];
    const departureTimes = [];
    const expectedStartTime = userTag?.workingHours?.coreHours?.start || '09:00';
    const expectedEndTime = userTag?.workingHours?.coreHours?.end || '17:00';

    for (const record of attendanceRecords) {
      if (record.isPresent) {
        analysis.presentDays++;

        // Determine data source
        if (record.biometricTimeIn && record.startDayTime) {
          analysis.bothSourcesDays++;
          
          // Check for discrepancies
          const timeDiff = Math.abs(
            moment(record.biometricTimeIn).diff(moment(record.startDayTime), 'minutes')
          );
          
          if (timeDiff > 15) { // 15-minute threshold
            analysis.discrepancies.push({
              date: record.date,
              type: 'Time Discrepancy',
              biometricTime: record.biometricTimeIn,
              startDayTime: record.startDayTime,
              difference: timeDiff,
              severity: timeDiff > 60 ? 'High' : timeDiff > 30 ? 'Medium' : 'Low'
            });
          }
        } else if (record.biometricTimeIn) {
          analysis.biometricOnlyDays++;
        } else if (record.startDayTime) {
          analysis.startDayOnlyDays++;
        }

        // Use the most reliable time source (biometric preferred)
        const arrivalTime = record.biometricTimeIn || record.startDayTime;
        const departureTime = record.biometricTimeOut || record.endDayTime;

        if (arrivalTime) {
          arrivalTimes.push(moment(arrivalTime));
          
          // Check if late
          const expectedStart = moment(arrivalTime).clone()
            .hour(parseInt(expectedStartTime.split(':')[0]))
            .minute(parseInt(expectedStartTime.split(':')[1]));
          
          if (moment(arrivalTime).isAfter(expectedStart)) {
            analysis.lateDays++;
          }
        }

        if (departureTime) {
          departureTimes.push(moment(departureTime));
          
          // Check if early departure
          const expectedEnd = moment(departureTime).clone()
            .hour(parseInt(expectedEndTime.split(':')[0]))
            .minute(parseInt(expectedEndTime.split(':')[1]));
          
          if (moment(departureTime).isBefore(expectedEnd)) {
            analysis.earlyDepartures++;
          }
        }

        // Check if perfect day (on time arrival and departure, full hours)
        if (arrivalTime && departureTime) {
          const workingHours = moment(departureTime).diff(moment(arrivalTime), 'hours', true);
          const isOnTime = !moment(arrivalTime).isAfter(
            moment(arrivalTime).clone()
              .hour(parseInt(expectedStartTime.split(':')[0]))
              .minute(parseInt(expectedStartTime.split(':')[1]))
          );
          
          if (isOnTime && workingHours >= this.standardWorkingHours) {
            analysis.perfectDays++;
          }
        }
      } else {
        analysis.absentDays++;
      }
    }

    // Calculate averages
    if (arrivalTimes.length > 0) {
      const avgArrival = arrivalTimes.reduce((sum, time) => {
        return sum + time.hour() * 60 + time.minute();
      }, 0) / arrivalTimes.length;
      
      analysis.averageArrivalTime = moment().startOf('day')
        .add(Math.floor(avgArrival / 60), 'hours')
        .add(avgArrival % 60, 'minutes')
        .format('HH:mm');
    }

    if (departureTimes.length > 0) {
      const avgDeparture = departureTimes.reduce((sum, time) => {
        return sum + time.hour() * 60 + time.minute();
      }, 0) / departureTimes.length;
      
      analysis.averageDepartureTime = moment().startOf('day')
        .add(Math.floor(avgDeparture / 60), 'hours')
        .add(avgDeparture % 60, 'minutes')
        .format('HH:mm');
    }

    analysis.attendanceRate = analysis.totalDays > 0 
      ? Math.round((analysis.presentDays / analysis.totalDays) * 100) 
      : 0;

    return analysis;
  }

  /**
   * Calculate genuine working hours based on most reliable data source
   */
  calculateGenuineWorkingHours(attendanceRecords) {
    const hoursAnalysis = {
      totalHours: 0,
      regularHours: 0,
      overtimeHours: 0,
      underTimeHours: 0,
      averageHoursPerDay: 0,
      dailyBreakdown: []
    };

    let totalWorkingDays = 0;

    for (const record of attendanceRecords) {
      if (!record.isPresent) {
        hoursAnalysis.dailyBreakdown.push({
          date: record.date,
          hours: 0,
          type: 'Absent',
          source: 'N/A'
        });
        continue;
      }

      // Determine the most reliable time source
      let startTime, endTime, source;
      
      if (record.biometricTimeIn && record.biometricTimeOut) {
        startTime = record.biometricTimeIn;
        endTime = record.biometricTimeOut;
        source = 'Biometric';
      } else if (record.startDayTime && record.endDayTime) {
        startTime = record.startDayTime;
        endTime = record.endDayTime;
        source = 'Start Day';
      } else if (record.biometricTimeIn) {
        startTime = record.biometricTimeIn;
        endTime = null;
        source = 'Biometric (Incomplete)';
      } else if (record.startDayTime) {
        startTime = record.startDayTime;
        endTime = null;
        source = 'Start Day (Incomplete)';
      }

      let dailyHours = 0;
      let dayType = 'Incomplete';

      if (startTime && endTime) {
        dailyHours = moment(endTime).diff(moment(startTime), 'hours', true);
        
        // Subtract break time (assuming 1 hour lunch break for full days)
        if (dailyHours > 6) {
          dailyHours -= 1;
        }

        dailyHours = Math.max(0, dailyHours); // Ensure non-negative

        if (dailyHours >= this.standardWorkingHours) {
          const regularHours = Math.min(dailyHours, this.standardWorkingHours);
          const overtime = Math.max(0, dailyHours - this.standardWorkingHours);
          
          hoursAnalysis.regularHours += regularHours;
          hoursAnalysis.overtimeHours += overtime;
          dayType = overtime > 0 ? 'Overtime' : 'Full Day';
        } else {
          hoursAnalysis.regularHours += dailyHours;
          hoursAnalysis.underTimeHours += (this.standardWorkingHours - dailyHours);
          dayType = 'Under Time';
        }

        totalWorkingDays++;
      }

      hoursAnalysis.totalHours += dailyHours;
      hoursAnalysis.dailyBreakdown.push({
        date: record.date,
        hours: Math.round(dailyHours * 100) / 100,
        type: dayType,
        source,
        startTime,
        endTime
      });
    }

    hoursAnalysis.averageHoursPerDay = totalWorkingDays > 0 
      ? Math.round((hoursAnalysis.totalHours / totalWorkingDays) * 100) / 100 
      : 0;

    return hoursAnalysis;
  }

  /**
   * Calculate all salary components
   */
  calculateSalaryComponents(salaryRecord, attendanceAnalysis, genuineHours, totalWorkingDays) {
    const baseSalary = salaryRecord.baseSalary;
    const dailyRate = baseSalary / totalWorkingDays;
    const hourlyRate = baseSalary / (totalWorkingDays * this.standardWorkingHours);

    // Base pay calculation
    const basePay = dailyRate * attendanceAnalysis.presentDays;

    // Overtime calculation
    const overtimePay = genuineHours.overtimeHours * hourlyRate * this.overtimeMultiplier;

    // Deductions
    const lateDeduction = attendanceAnalysis.lateDays * baseSalary * this.lateDeductionRate;
    const absentDeduction = attendanceAnalysis.absentDays * dailyRate;
    const underTimeDeduction = genuineHours.underTimeHours * hourlyRate;

    // Allowances (from salary record)
    const totalAllowances = salaryRecord.totalAllowances || 0;

    // Other deductions (from salary record)
    const otherDeductions = salaryRecord.totalDeductions || 0;

    // Calculate totals
    const grossPay = basePay + overtimePay + totalAllowances;
    const totalDeductions = lateDeduction + absentDeduction + underTimeDeduction + otherDeductions;
    const netPay = grossPay - totalDeductions;

    return {
      baseSalary,
      dailyRate: Math.round(dailyRate * 100) / 100,
      hourlyRate: Math.round(hourlyRate * 100) / 100,
      basePay: Math.round(basePay * 100) / 100,
      overtimePay: Math.round(overtimePay * 100) / 100,
      totalAllowances,
      grossPay: Math.round(grossPay * 100) / 100,
      deductions: {
        late: Math.round(lateDeduction * 100) / 100,
        absent: Math.round(absentDeduction * 100) / 100,
        underTime: Math.round(underTimeDeduction * 100) / 100,
        other: otherDeductions,
        total: Math.round(totalDeductions * 100) / 100
      },
      netPay: Math.round(netPay * 100) / 100,
      currency: salaryRecord.currency || 'USD'
    };
  }

  /**
   * Generate recommendations based on analysis
   */
  generateRecommendations(attendanceAnalysis, genuineHours, salaryComponents) {
    const recommendations = [];

    // Attendance recommendations
    if (attendanceAnalysis.attendanceRate < 90) {
      recommendations.push({
        type: 'Attendance',
        severity: 'High',
        message: `Low attendance rate (${attendanceAnalysis.attendanceRate}%). Consider discussing with employee.`,
        action: 'Review Required'
      });
    }

    if (attendanceAnalysis.lateDays > 5) {
      recommendations.push({
        type: 'Punctuality',
        severity: 'Medium',
        message: `High number of late arrivals (${attendanceAnalysis.lateDays} days). Consider flexible timing or counseling.`,
        action: 'Policy Review'
      });
    }

    // Discrepancy recommendations
    if (attendanceAnalysis.discrepancies.length > 0) {
      const highSeverityDiscrepancies = attendanceAnalysis.discrepancies.filter(d => d.severity === 'High');
      if (highSeverityDiscrepancies.length > 0) {
        recommendations.push({
          type: 'Data Integrity',
          severity: 'High',
          message: `${highSeverityDiscrepancies.length} high-severity time discrepancies found. Manual review required.`,
          action: 'Manual Review'
        });
      }
    }

    // Working hours recommendations
    if (genuineHours.averageHoursPerDay < 6) {
      recommendations.push({
        type: 'Productivity',
        severity: 'Medium',
        message: `Low average working hours (${genuineHours.averageHoursPerDay}h/day). Consider workload review.`,
        action: 'Workload Assessment'
      });
    }

    if (genuineHours.overtimeHours > 20) {
      recommendations.push({
        type: 'Work-Life Balance',
        severity: 'Medium',
        message: `High overtime hours (${genuineHours.overtimeHours}h). Consider workload redistribution.`,
        action: 'Workload Redistribution'
      });
    }

    // Salary recommendations
    if (salaryComponents.deductions.total > salaryComponents.basePay * 0.2) {
      recommendations.push({
        type: 'Compensation',
        severity: 'High',
        message: 'High deduction percentage. Consider performance improvement plan.',
        action: 'Performance Review'
      });
    }

    return recommendations;
  }

  /**
   * Calculate salary for multiple employees
   */
  async calculateBulkSalary(userIds, year, month, workingDays = null) {
    const results = [];
    const errors = [];

    for (const userId of userIds) {
      try {
        const calculation = await this.calculateMonthlySalary(userId, year, month, workingDays);
        results.push(calculation);
      } catch (error) {
        errors.push({
          userId,
          error: error.message
        });
      }
    }

    return {
      results,
      errors,
      summary: {
        totalProcessed: userIds.length,
        successful: results.length,
        failed: errors.length
      }
    };
  }
}

module.exports = new SalaryCalculator();
