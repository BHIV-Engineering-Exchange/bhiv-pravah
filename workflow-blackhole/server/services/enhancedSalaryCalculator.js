const DailyAttendance = require('../models/DailyAttendance');
const Salary = require('../models/Salary');
const User = require('../models/User');
const UserTag = require('../models/UserTag');
const mongoose = require('mongoose');

class EnhancedSalaryCalculator {
  constructor() {
    this.defaultDailyWage = 258;
    this.standardWorkingHours = 8;
    this.overtimeMultiplier = 1.5;
    this.standardWorkingDays = 26;
  }

  /**
   * Calculate comprehensive monthly salary for a user
   */
  async calculateMonthlySalary(userId, year, month, options = {}) {
    try {
      // Validate inputs
      if (!mongoose.Types.ObjectId.isValid(userId)) {
        throw new Error('Invalid user ID');
      }

      const startDate = new Date(year, month - 1, 1);
      const endDate = new Date(year, month, 0);
      const workingDaysInMonth = this.getWorkingDaysInMonth(year, month);

      // Get user information
      const user = await User.findById(userId).populate('department');
      if (!user) {
        throw new Error('User not found');
      }

      // Get user tag for employee type
      const userTag = await UserTag.findOne({ user: userId });
      const employeeType = userTag?.tag || 'Employee';

      // Get salary configuration
      const salaryConfig = await Salary.findOne({ user: userId });
      const baseSalary = salaryConfig?.baseSalary || this.defaultDailyWage * this.standardWorkingDays;
      const dailyWage = baseSalary / this.standardWorkingDays;

      // Get attendance records for the month
      const attendanceRecords = await DailyAttendance.find({
        user: userId,
        date: { $gte: startDate, $lte: endDate }
      }).sort({ date: 1 });

      // Calculate attendance statistics
      const attendanceStats = this.calculateAttendanceStats(attendanceRecords, workingDaysInMonth);

      // Calculate salary components
      const salaryComponents = this.calculateSalaryComponents(
        attendanceStats,
        dailyWage,
        salaryConfig,
        employeeType
      );

      // Calculate deductions and bonuses
      const adjustments = this.calculateAdjustments(
        attendanceStats,
        salaryComponents,
        salaryConfig,
        employeeType
      );

      // Generate recommendations
      const recommendations = this.generateRecommendations(
        attendanceStats,
        salaryComponents,
        adjustments
      );

      return {
        user: {
          id: user._id,
          name: user.name,
          email: user.email,
          department: user.department?.name || 'N/A',
          employeeType
        },
        period: {
          year,
          month,
          monthName: new Date(year, month - 1).toLocaleString('default', { month: 'long' }),
          startDate,
          endDate,
          workingDaysInMonth
        },
        attendance: attendanceStats,
        salary: salaryComponents,
        adjustments,
        recommendations,
        summary: {
          grossSalary: salaryComponents.grossSalary,
          totalDeductions: adjustments.totalDeductions,
          totalBonuses: adjustments.totalBonuses,
          netSalary: salaryComponents.grossSalary + adjustments.totalBonuses - adjustments.totalDeductions,
          paymentStatus: 'Calculated',
          calculatedAt: new Date()
        }
      };

    } catch (error) {
      console.error('Error calculating monthly salary:', error);
      throw error;
    }
  }

  /**
   * Calculate attendance statistics
   */
  calculateAttendanceStats(attendanceRecords, workingDaysInMonth) {
    const totalRecords = attendanceRecords.length;
    const presentDays = attendanceRecords.filter(record => record.isPresent).length;
    const absentDays = workingDaysInMonth - presentDays;
    const leaveDays = attendanceRecords.filter(record => record.isLeave).length;
    const halfDays = attendanceRecords.filter(record => record.status === 'Half Day').length;
    const lateDays = attendanceRecords.filter(record => record.status === 'Late').length;
    const discrepancies = attendanceRecords.filter(record => record.hasDiscrepancy).length;

    const totalHours = attendanceRecords.reduce((sum, record) => sum + (record.totalHoursWorked || 0), 0);
    const regularHours = attendanceRecords.reduce((sum, record) => sum + (record.regularHours || 0), 0);
    const overtimeHours = attendanceRecords.reduce((sum, record) => sum + (record.overtimeHours || 0), 0);

    const expectedHours = workingDaysInMonth * this.standardWorkingHours;
    const attendanceRate = workingDaysInMonth > 0 ? (presentDays / workingDaysInMonth) * 100 : 0;
    const hoursEfficiency = expectedHours > 0 ? (totalHours / expectedHours) * 100 : 0;

    return {
      workingDaysInMonth,
      totalRecords,
      presentDays,
      absentDays,
      leaveDays,
      halfDays,
      lateDays,
      discrepancies,
      attendanceRate: Math.round(attendanceRate * 100) / 100,
      hours: {
        totalHours: Math.round(totalHours * 100) / 100,
        regularHours: Math.round(regularHours * 100) / 100,
        overtimeHours: Math.round(overtimeHours * 100) / 100,
        expectedHours,
        avgHoursPerDay: presentDays > 0 ? Math.round((totalHours / presentDays) * 100) / 100 : 0,
        hoursEfficiency: Math.round(hoursEfficiency * 100) / 100
      }
    };
  }

  /**
   * Calculate salary components
   */
  calculateSalaryComponents(attendanceStats, dailyWage, salaryConfig, employeeType) {
    const { presentDays, hours } = attendanceStats;
    
    // Base salary calculation
    const basePay = presentDays * dailyWage;
    
    // Overtime calculation
    const overtimePay = hours.overtimeHours * (dailyWage / this.standardWorkingHours) * this.overtimeMultiplier;
    
    // Allowances from salary config
    const allowances = salaryConfig ? {
      housing: salaryConfig.allowances?.housing || 0,
      transport: salaryConfig.allowances?.transport || 0,
      medical: salaryConfig.allowances?.medical || 0,
      food: salaryConfig.allowances?.food || 0,
      communication: salaryConfig.allowances?.communication || 0,
      other: salaryConfig.allowances?.other || 0
    } : {};
    
    const totalAllowances = Object.values(allowances).reduce((sum, amount) => sum + (amount || 0), 0);
    
    // Gross salary
    const grossSalary = basePay + overtimePay + totalAllowances;
    
    return {
      basePay: Math.round(basePay * 100) / 100,
      overtimePay: Math.round(overtimePay * 100) / 100,
      allowances,
      totalAllowances: Math.round(totalAllowances * 100) / 100,
      grossSalary: Math.round(grossSalary * 100) / 100,
      dailyWage: Math.round(dailyWage * 100) / 100,
      hourlyRate: Math.round((dailyWage / this.standardWorkingHours) * 100) / 100
    };
  }

  /**
   * Calculate adjustments (bonuses and deductions)
   */
  calculateAdjustments(attendanceStats, salaryComponents, salaryConfig, employeeType) {
    const bonuses = [];
    const deductions = [];

    // Perfect attendance bonus
    if (attendanceStats.attendanceRate >= 100) {
      bonuses.push({
        type: 'Perfect Attendance',
        amount: salaryComponents.basePay * 0.05,
        description: 'Perfect attendance bonus (5%)'
      });
    }

    // Overtime bonus for excessive hours
    if (attendanceStats.hours.overtimeHours > 20) {
      bonuses.push({
        type: 'Overtime Excellence',
        amount: 500,
        description: 'Bonus for working more than 20 overtime hours'
      });
    }

    // Efficiency bonus
    if (attendanceStats.hours.hoursEfficiency >= 110) {
      bonuses.push({
        type: 'Efficiency Bonus',
        amount: salaryComponents.basePay * 0.03,
        description: 'High efficiency bonus (3%)'
      });
    }

    // Late arrival deduction
    if (attendanceStats.lateDays > 3) {
      deductions.push({
        type: 'Late Arrival',
        amount: attendanceStats.lateDays * 50,
        description: `Late arrival penalty: ${attendanceStats.lateDays} days × ₹50`
      });
    }

    // Absence deduction (already accounted for in base pay, but additional penalty for excessive absence)
    if (attendanceStats.attendanceRate < 80) {
      deductions.push({
        type: 'Poor Attendance',
        amount: salaryComponents.basePay * 0.05,
        description: 'Poor attendance penalty (5%)'
      });
    }

    // Discrepancy penalty
    if (attendanceStats.discrepancies > 2) {
      deductions.push({
        type: 'Data Discrepancy',
        amount: attendanceStats.discrepancies * 100,
        description: `Data discrepancy penalty: ${attendanceStats.discrepancies} × ₹100`
      });
    }

    // Statutory deductions from salary config
    if (salaryConfig?.deductions) {
      if (salaryConfig.deductions.tax > 0) {
        deductions.push({
          type: 'Income Tax',
          amount: salaryConfig.deductions.tax,
          description: 'Income tax deduction'
        });
      }
      if (salaryConfig.deductions.insurance > 0) {
        deductions.push({
          type: 'Insurance',
          amount: salaryConfig.deductions.insurance,
          description: 'Insurance premium'
        });
      }
      if (salaryConfig.deductions.providentFund > 0) {
        deductions.push({
          type: 'Provident Fund',
          amount: salaryConfig.deductions.providentFund,
          description: 'PF contribution'
        });
      }
    }

    const totalBonuses = bonuses.reduce((sum, bonus) => sum + bonus.amount, 0);
    const totalDeductions = deductions.reduce((sum, deduction) => sum + deduction.amount, 0);

    return {
      bonuses,
      deductions,
      totalBonuses: Math.round(totalBonuses * 100) / 100,
      totalDeductions: Math.round(totalDeductions * 100) / 100
    };
  }

  /**
   * Generate recommendations based on attendance and salary data
   */
  generateRecommendations(attendanceStats, salaryComponents, adjustments) {
    const recommendations = [];

    // Attendance recommendations
    if (attendanceStats.attendanceRate < 90) {
      recommendations.push({
        type: 'Attendance',
        severity: 'High',
        message: `Attendance rate is ${attendanceStats.attendanceRate.toFixed(1)}%. Needs improvement.`,
        action: 'Schedule meeting with HR to discuss attendance issues'
      });
    } else if (attendanceStats.attendanceRate < 95) {
      recommendations.push({
        type: 'Attendance',
        severity: 'Medium',
        message: `Attendance rate is ${attendanceStats.attendanceRate.toFixed(1)}%. Room for improvement.`,
        action: 'Monitor attendance closely and provide support if needed'
      });
    }

    // Hours efficiency recommendations
    if (attendanceStats.hours.hoursEfficiency < 80) {
      recommendations.push({
        type: 'Productivity',
        severity: 'High',
        message: `Hours efficiency is ${attendanceStats.hours.hoursEfficiency.toFixed(1)}%. Below expectations.`,
        action: 'Investigate productivity issues and provide training if necessary'
      });
    }

    // Overtime recommendations
    if (attendanceStats.hours.overtimeHours > 30) {
      recommendations.push({
        type: 'Work-Life Balance',
        severity: 'Medium',
        message: `Excessive overtime: ${attendanceStats.hours.overtimeHours} hours this month.`,
        action: 'Review workload distribution and consider additional resources'
      });
    }

    // Discrepancy recommendations
    if (attendanceStats.discrepancies > 5) {
      recommendations.push({
        type: 'Data Quality',
        severity: 'High',
        message: `${attendanceStats.discrepancies} attendance discrepancies found.`,
        action: 'Review attendance tracking methods and provide training'
      });
    }

    // Positive recommendations
    if (attendanceStats.attendanceRate >= 98) {
      recommendations.push({
        type: 'Recognition',
        severity: 'Low',
        message: 'Excellent attendance record!',
        action: 'Consider for employee recognition program'
      });
    }

    if (attendanceStats.hours.hoursEfficiency >= 110) {
      recommendations.push({
        type: 'Recognition',
        severity: 'Low',
        message: 'Outstanding productivity and dedication!',
        action: 'Consider for performance bonus or promotion'
      });
    }

    return recommendations;
  }

  /**
   * Calculate working days in a month (excluding Sundays)
   */
  getWorkingDaysInMonth(year, month) {
    const startDate = new Date(year, month - 1, 1);
    const endDate = new Date(year, month, 0);
    let workingDays = 0;

    for (let date = new Date(startDate); date <= endDate; date.setDate(date.getDate() + 1)) {
      // Exclude Sundays (0 = Sunday)
      if (date.getDay() !== 0) {
        workingDays++;
      }
    }

    return workingDays;
  }

  /**
   * Calculate bulk salaries for multiple users
   */
  async calculateBulkSalary(userIds, year, month, options = {}) {
    const results = {
      successful: [],
      failed: [],
      summary: {
        totalUsers: userIds.length,
        successCount: 0,
        failureCount: 0,
        totalPayroll: 0,
        avgSalary: 0
      }
    };

    for (const userId of userIds) {
      try {
        const calculation = await this.calculateMonthlySalary(userId, year, month, options);
        results.successful.push(calculation);
        results.summary.successCount++;
        results.summary.totalPayroll += calculation.summary.netSalary;
      } catch (error) {
        results.failed.push({
          userId,
          error: error.message
        });
        results.summary.failureCount++;
      }
    }

    results.summary.avgSalary = results.summary.successCount > 0 
      ? results.summary.totalPayroll / results.summary.successCount 
      : 0;

    return results;
  }

  /**
   * Generate salary slip data
   */
  async generateSalarySlip(userId, year, month) {
    const calculation = await this.calculateMonthlySalary(userId, year, month);
    
    return {
      ...calculation,
      slip: {
        slipNumber: `SAL-${year}${month.toString().padStart(2, '0')}-${userId.toString().slice(-6)}`,
        generatedAt: new Date(),
        payPeriod: `${calculation.period.monthName} ${year}`,
        earnings: [
          { description: 'Basic Salary', amount: calculation.salary.basePay },
          { description: 'Overtime Pay', amount: calculation.salary.overtimePay },
          ...Object.entries(calculation.salary.allowances).map(([key, value]) => ({
            description: key.charAt(0).toUpperCase() + key.slice(1) + ' Allowance',
            amount: value
          })),
          ...calculation.adjustments.bonuses.map(bonus => ({
            description: bonus.type,
            amount: bonus.amount
          }))
        ],
        deductions: calculation.adjustments.deductions.map(deduction => ({
          description: deduction.type,
          amount: deduction.amount
        })),
        netPay: calculation.summary.netSalary
      }
    };
  }
}

module.exports = new EnhancedSalaryCalculator();