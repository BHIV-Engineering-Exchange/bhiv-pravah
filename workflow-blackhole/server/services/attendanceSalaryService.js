const DailyAttendance = require('../models/DailyAttendance');
const EmployeeMaster = require('../models/EmployeeMaster');
const User = require('../models/User');
const Department = require('../models/Department');
const PublicHoliday = require('../models/PublicHoliday');
const PaidLeaveConfig = require('../models/PaidLeaveConfig');
const mongoose = require('mongoose');
const moment = require('moment');

class AttendanceSalaryService {
  constructor() {
    this.standardWorkingHours = 8;
    this.standardWorkingDays = 26;
  }

  /**
   * Calculate salary for date range
   */
  async calculateSalaryForDateRange(filters = {}) {
    try {
      const {
        startDate,
        endDate,
        userId,
        departmentId,
        workType // 'Office', 'WFH', or null for all
      } = filters;

      // Build query
      const query = {
        date: {
          $gte: new Date(startDate),
          $lte: new Date(endDate)
        }
      };

      if (userId) {
        query.user = userId;
      }

      if (workType) {
        query.workLocationType = workType;
      }

      // Get attendance records
      let attendanceRecords = await DailyAttendance.find(query)
        .populate('user', 'name email department')
        .sort({ date: 1 });

      // Filter by department if specified
      if (departmentId) {
        attendanceRecords = attendanceRecords.filter(
          record => record.user?.department?.toString() === departmentId
        );
      }

      // Group by user
      const userGroups = {};
      
      for (const record of attendanceRecords) {
        const userId = record.user._id.toString();
        
        if (!userGroups[userId]) {
          userGroups[userId] = {
            user: record.user,
            records: [],
            summary: {
              totalDays: 0,
              presentDays: 0,
              absentDays: 0,
              halfDays: 0,
              lateDays: 0,
              totalHours: 0,
              regularHours: 0,
              overtimeHours: 0,
              totalEarned: 0
            }
          };
        }

        userGroups[userId].records.push(record);
      }

      // Calculate summary for each user
      const results = [];

      for (const userId in userGroups) {
        const group = userGroups[userId];
        const summary = await this.calculateUserSummary(
          group.user._id,
          group.records,
          startDate,
          endDate
        );

        results.push({
          user: group.user,
          summary: summary,
          records: group.records
        });
      }

      // Calculate grand totals
      const grandTotal = {
        totalEmployees: results.length,
        totalPresentDays: results.reduce((sum, r) => sum + r.summary.presentDays, 0),
        totalAbsentDays: results.reduce((sum, r) => sum + r.summary.absentDays, 0),
        totalHours: results.reduce((sum, r) => sum + r.summary.totalHours, 0),
        totalOvertimeHours: results.reduce((sum, r) => sum + r.summary.overtimeHours, 0),
        totalPayable: results.reduce((sum, r) => sum + r.summary.totalPayable, 0)
      };

      return {
        success: true,
        dateRange: {
          start: startDate,
          end: endDate
        },
        grandTotal: grandTotal,
        employees: results
      };

    } catch (error) {
      console.error('❌ Error calculating salary:', error);
      throw error;
    }
  }

  /**
   * Calculate summary for single user
   */
  async calculateUserSummary(userId, records, startDate, endDate) {
    try {
      // Get employee master data
      const employeeMaster = await EmployeeMaster.findOne({ user: userId });
      
      if (!employeeMaster) {
        console.warn(`No employee master found for user ${userId}`);
      }

      const hourlyRate = employeeMaster?.calculatedHourlyRate || 0;
      const dailyRate = employeeMaster?.calculatedDailyRate || 0;
      const overtimeRate = employeeMaster?.overtimeRate || 1.5;
      const standardHours = employeeMaster?.standardShiftHours || 8;

      // Calculate working days in range
      const start = moment(startDate);
      const end = moment(endDate);
      const totalDaysInRange = end.diff(start, 'days') + 1;
      
      // Count weekdays
      let workingDaysInRange = 0;
      let currentDay = moment(start);
      while (currentDay <= end) {
        const dayOfWeek = currentDay.day();
        if (dayOfWeek !== 0 && dayOfWeek !== 6) { // Not Sunday or Saturday
          workingDaysInRange++;
        }
        currentDay.add(1, 'day');
      }

      // Initialize summary
      const summary = {
        totalDays: totalDaysInRange,
        workingDaysInRange: workingDaysInRange,
        presentDays: 0,
        absentDays: 0,
        halfDays: 0,
        lateDays: 0,
        leaveDays: 0,
        totalHours: 0,
        regularHours: 0,
        overtimeHours: 0,
        totalEarned: 0,
        regularPay: 0,
        overtimePay: 0,
        bonuses: 0,
        deductions: 0,
        allowances: 0,
        totalPayable: 0
      };

      // Get public holidays first to filter out holiday dates
      const user = await User.findById(userId).populate('department');
      const publicHolidays = await PublicHoliday.getHolidaysInRange(
        new Date(startDate),
        new Date(endDate),
        user?.department?._id
      );
      
      // Get holiday dates for filtering
      const holidayDates = new Set(
        publicHolidays.map(h => moment(h.date).format('YYYY-MM-DD'))
      );

      // IMPORTANT: Filter out records that fall on holidays
      // Admin can mark days as holidays, and those hours should NOT be counted in cumulative
      let excludedHolidayHours = 0;
      const filteredRecords = [];
      
      for (const record of records) {
        const recordDate = moment(record.date).format('YYYY-MM-DD');
        
        if (holidayDates.has(recordDate)) {
          // This day is a holiday - exclude its hours from cumulative
          const hoursToExclude = record.totalHoursWorked || 0;
          excludedHolidayHours += hoursToExclude;
          
          console.log(`🚫 Excluding holiday hours: ${recordDate} - ${hoursToExclude}h (${record.user?.name})`);
          
          // Don't add this record to filtered records (it's a holiday)
        } else {
          // Normal working day - include in salary calculation
          filteredRecords.push(record);
        }
      }

      // Process only non-holiday records
      for (const record of filteredRecords) {
        if (record.status === 'Present' || record.status === 'Late') {
          summary.presentDays++;
          if (record.status === 'Late') summary.lateDays++;
        } else if (record.status === 'Half Day') {
          summary.halfDays++;
          summary.presentDays += 0.5;
        } else if (record.status === 'Absent') {
          summary.absentDays++;
        } else if (record.status === 'On Leave') {
          summary.leaveDays++;
          summary.presentDays++; // Leave days count as present for salary
        }

        summary.totalHours += record.totalHoursWorked || 0;
        summary.regularHours += record.regularHours || 0;
        summary.overtimeHours += record.overtimeHours || 0;
        summary.bonuses += record.bonusAmount || 0;
        summary.deductions += record.deductionAmount || 0;
      }

      // Add paid leave hours
      const paidLeaveHours = await PaidLeaveConfig.getTotalPaidHours(
        userId,
        new Date(startDate),
        new Date(endDate)
      );
      
      summary.paidLeaveHours = paidLeaveHours;
      summary.totalHours += paidLeaveHours;
      summary.regularHours += paidLeaveHours;

      // Store holiday exclusion info
      summary.holidaysMarked = publicHolidays.length;
      summary.excludedHolidayHours = excludedHolidayHours;
      summary.holidayDates = publicHolidays.map(h => ({
        date: h.date,
        name: h.name,
        isPaidLeave: h.isPaidLeave
      }));
      
      // Add paid public holiday hours (standard 8h per paid holiday, not actual worked hours)
      const paidPublicHolidays = publicHolidays.filter(h => h.isPaidLeave);
      const publicHolidayHours = paidPublicHolidays.length * standardHours;
      
      summary.publicHolidayDays = paidPublicHolidays.length;
      summary.publicHolidayHours = publicHolidayHours;
      summary.totalHours += publicHolidayHours;
      summary.regularHours += publicHolidayHours;
      summary.presentDays += paidPublicHolidays.length;

      // Calculate salary based on salary type
      if (employeeMaster) {
        if (employeeMaster.salaryType === 'Hourly') {
          summary.regularPay = summary.regularHours * hourlyRate;
          summary.overtimePay = summary.overtimeHours * hourlyRate * overtimeRate;
        } else if (employeeMaster.salaryType === 'Daily') {
          summary.regularPay = summary.presentDays * dailyRate;
          summary.overtimePay = summary.overtimeHours * hourlyRate * overtimeRate;
        } else { // Monthly
          // Pro-rate monthly salary based on working days
          const monthlySalary = employeeMaster.monthlySalary || 0;
          const dailyWage = monthlySalary / employeeMaster.standardWorkingDays;
          summary.regularPay = summary.presentDays * dailyWage;
          summary.overtimePay = summary.overtimeHours * hourlyRate * overtimeRate;
        }

        // Add allowances
        const allowances = employeeMaster.allowances || {};
        summary.allowances = Object.values(allowances).reduce((sum, val) => sum + (val || 0), 0);

        // Add deductions
        const deductions = employeeMaster.deductions || {};
        const fixedDeductions = Object.values(deductions).reduce((sum, val) => sum + (val || 0), 0);
        summary.deductions += fixedDeductions;
      }

      summary.totalEarned = summary.regularPay + summary.overtimePay;
      summary.totalPayable = summary.totalEarned + summary.bonuses + summary.allowances - summary.deductions;

      // Absent days = working days - present days - leave days
      summary.absentDays = workingDaysInRange - summary.presentDays - summary.leaveDays;

      return summary;

    } catch (error) {
      console.error('Error calculating user summary:', error);
      throw error;
    }
  }

  /**
   * Get dashboard KPIs for today
   */
  async getTodayKPIs(filters = {}) {
    try {
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const query = { date: today };
      
      if (filters.departmentId) {
        const users = await User.find({ department: filters.departmentId }).select('_id');
        query.user = { $in: users.map(u => u._id) };
      }

      if (filters.workType) {
        query.workLocationType = filters.workType;
      }

      const records = await DailyAttendance.find(query).populate('user');

      const kpis = {
        totalEmployees: 0,
        presentToday: 0,
        absentToday: 0,
        lateToday: 0,
        onLeaveToday: 0,
        wfhToday: 0,
        officeToday: 0,
        averageHoursToday: 0,
        totalHoursToday: 0,
        overtimeToday: 0
      };

      // Get total active employees
      const totalEmployeesQuery = filters.departmentId 
        ? { stillExist: 1, department: filters.departmentId }
        : { stillExist: 1 };
      
      kpis.totalEmployees = await User.countDocuments(totalEmployeesQuery);

      // Calculate KPIs
      let totalHours = 0;
      let presentCount = 0;

      for (const record of records) {
        if (record.status === 'Present' || record.status === 'Late') {
          kpis.presentToday++;
          presentCount++;
        } else if (record.status === 'Absent') {
          kpis.absentToday++;
        } else if (record.status === 'On Leave') {
          kpis.onLeaveToday++;
        }

        if (record.status === 'Late') {
          kpis.lateToday++;
        }

        if (record.workLocationType === 'WFH') {
          kpis.wfhToday++;
        } else if (record.workLocationType === 'Office') {
          kpis.officeToday++;
        }

        totalHours += record.totalHoursWorked || 0;
        kpis.overtimeToday += record.overtimeHours || 0;
      }

      kpis.totalHoursToday = Math.round(totalHours * 100) / 100;
      kpis.averageHoursToday = presentCount > 0 
        ? Math.round((totalHours / presentCount) * 100) / 100 
        : 0;

      // Calculate absent (employees not marked present or on leave)
      kpis.absentToday = kpis.totalEmployees - kpis.presentToday - kpis.onLeaveToday;

      return kpis;

    } catch (error) {
      console.error('Error getting today KPIs:', error);
      throw error;
    }
  }

  /**
   * Get detailed attendance logs for date range
   */
  async getDetailedLogs(filters = {}) {
    try {
      const {
        startDate,
        endDate,
        userId,
        departmentId,
        workType,
        status
      } = filters;

      const query = {};

      if (startDate && endDate) {
        query.date = {
          $gte: new Date(startDate),
          $lte: new Date(endDate)
        };
      }

      if (userId) {
        query.user = userId;
      }

      if (workType) {
        query.workLocationType = workType;
      }

      if (status) {
        query.status = status;
      }

      let records = await DailyAttendance.find(query)
        .populate('user', 'name email department')
        .populate({
          path: 'user',
          populate: {
            path: 'department',
            select: 'name'
          }
        })
        .sort({ date: -1, user: 1 })
        .lean();

      // Filter by department if specified
      if (departmentId) {
        records = records.filter(
          record => record.user?.department?._id?.toString() === departmentId
        );
      }

      return records;

    } catch (error) {
      console.error('Error getting detailed logs:', error);
      throw error;
    }
  }

  /**
   * Get employee-wise aggregated data for date range
   */
  async getEmployeeAggregates(filters = {}) {
    try {
      const {
        startDate,
        endDate,
        departmentId,
        workType
      } = filters;

      const matchStage = {
        date: {
          $gte: new Date(startDate),
          $lte: new Date(endDate)
        }
      };

      if (workType) {
        matchStage.workLocationType = workType;
      }

      const pipeline = [
        { $match: matchStage },
        {
          $group: {
            _id: '$user',
            presentDays: {
              $sum: {
                $cond: [
                  { $in: ['$status', ['Present', 'Late']] },
                  1,
                  0
                ]
              }
            },
            absentDays: {
              $sum: {
                $cond: [{ $eq: ['$status', 'Absent'] }, 1, 0]
              }
            },
            halfDays: {
              $sum: {
                $cond: [{ $eq: ['$status', 'Half Day'] }, 1, 0]
              }
            },
            leaveDays: {
              $sum: {
                $cond: [{ $eq: ['$status', 'On Leave'] }, 1, 0]
              }
            },
            lateDays: {
              $sum: {
                $cond: [{ $eq: ['$status', 'Late'] }, 1, 0]
              }
            },
            totalHours: { $sum: '$totalHoursWorked' },
            regularHours: { $sum: '$regularHours' },
            overtimeHours: { $sum: '$overtimeHours' },
            totalEarned: { $sum: '$earnedAmount' }
          }
        },
        {
          $lookup: {
            from: 'users',
            localField: '_id',
            foreignField: '_id',
            as: 'user'
          }
        },
        {
          $unwind: '$user'
        },
        {
          $lookup: {
            from: 'departments',
            localField: 'user.department',
            foreignField: '_id',
            as: 'department'
          }
        },
        {
          $unwind: {
            path: '$department',
            preserveNullAndEmptyArrays: true
          }
        }
      ];

      // Add department filter if specified
      if (departmentId) {
        pipeline.push({
          $match: {
            'user.department': new mongoose.Types.ObjectId(departmentId)
          }
        });
      }

      pipeline.push({
        $project: {
          _id: 1,
          userName: '$user.name',
          userEmail: '$user.email',
          departmentName: '$department.name',
          presentDays: 1,
          absentDays: 1,
          halfDays: 1,
          leaveDays: 1,
          lateDays: 1,
          totalHours: { $round: ['$totalHours', 2] },
          regularHours: { $round: ['$regularHours', 2] },
          overtimeHours: { $round: ['$overtimeHours', 2] },
          totalEarned: { $round: ['$totalEarned', 2] }
        }
      });

      pipeline.push({ $sort: { userName: 1 } });

      const results = await DailyAttendance.aggregate(pipeline);

      return results;

    } catch (error) {
      console.error('Error getting employee aggregates:', error);
      throw error;
    }
  }
}

module.exports = new AttendanceSalaryService();
