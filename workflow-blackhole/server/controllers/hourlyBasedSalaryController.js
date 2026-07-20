const DailyAttendance = require('../models/DailyAttendance');
const Attendance = require('../models/Attendance');
const User = require('../models/User');
const Salary = require('../models/Salary');
const SalaryAttendance = require('../models/SalaryAttendance');
const mongoose = require('mongoose');

/**
 * Calculate salary based on hourly worked hours from daily attendance
 * Supports both hourly rate and monthly salary calculations
 * Includes real-time data from active attendance sessions
 */

/**
 * Calculate salary for a specific employee for a given month
 * Includes real-time calculation for ongoing sessions
 */
exports.calculateEmployeeMonthlySalary = async (req, res) => {
  try {
    const { userId, year, month } = req.params;
    
    if (!userId || !year || !month) {
      return res.status(400).json({ 
        success: false, 
        message: 'User ID, year, and month are required' 
      });
    }
    
    // Validate user
    const user = await User.findById(userId);
    if (!user) {
      return res.status(404).json({ 
        success: false, 
        message: 'User not found' 
      });
    }
    
    // Get salary information
    const salaryInfo = await Salary.findOne({ user: userId });
    const hourlyRate = user.hourlyRate || 25; // Default to $25/hour
    
    // Calculate date range for the month
    const startDate = new Date(year, month - 1, 1);
    const endDate = new Date(year, month, 0, 23, 59, 59, 999);
    
    // Get all attendance records for the month
    let attendanceRecords = await DailyAttendance.find({
      user: userId,
      date: { $gte: startDate, $lte: endDate }
    }).sort({ date: 1 });
    
    // REAL-TIME: Check for active Attendance records not yet synced to DailyAttendance
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    const activeAttendance = await Attendance.findOne({
      user: userId,
      date: { $gte: today }
    });
    
    // If there's an active session on today that's not in DailyAttendance, include it
    if (activeAttendance && activeAttendance.startDayTime) {
      const todayDailyRecord = attendanceRecords.find(r => {
        const recordDate = new Date(r.date);
        recordDate.setHours(0, 0, 0, 0);
        return recordDate.getTime() === today.getTime();
      });
      
      // If today's record is missing or outdated, calculate from live attendance
      if (!todayDailyRecord || !activeAttendance.endDayTime) {
        const now = new Date();
        const hoursWorked = (now - activeAttendance.startDayTime) / (1000 * 60 * 60);
        
        const liveRecord = {
          _id: activeAttendance._id,
          date: today,
          status: 'Present',
          isPresent: true,
          totalHoursWorked: Math.max(0, Math.round(hoursWorked * 100) / 100),
          regularHours: Math.min(hoursWorked, 8),
          overtimeHours: Math.max(0, hoursWorked - 8),
          officeHours: activeAttendance.workLocationType === 'Office' ? Math.max(0, Math.round(hoursWorked * 100) / 100) : 0,
          remoteHours: activeAttendance.workLocationType !== 'Office' ? Math.max(0, Math.round(hoursWorked * 100) / 100) : 0,
          workLocationType: activeAttendance.workLocationType || 'Office',
          biometricTimeIn: activeAttendance.biometricTimeIn,
          biometricTimeOut: activeAttendance.biometricTimeOut,
          startDayTime: activeAttendance.startDayTime,
          endDayTime: activeAttendance.endDayTime || now,
          isRealTime: true // Flag to indicate this is real-time data
        };
        
        // Replace or add today's record
        if (todayDailyRecord) {
          const index = attendanceRecords.indexOf(todayDailyRecord);
          attendanceRecords[index] = liveRecord;
        } else {
          attendanceRecords.push(liveRecord);
        }
      }
    }
    
    // Calculate totals
    const totalDays = attendanceRecords.length;
    const presentDays = attendanceRecords.filter(record => record.isPresent).length;
    const absentDays = totalDays - presentDays;
    
    const totalHours = attendanceRecords.reduce((sum, record) => sum + (record.totalHoursWorked || 0), 0);
    const regularHours = attendanceRecords.reduce((sum, record) => sum + (record.regularHours || 0), 0);
    const overtimeHours = attendanceRecords.reduce((sum, record) => sum + (record.overtimeHours || 0), 0);
    const officeHours = attendanceRecords.reduce((sum, record) => sum + (record.officeHours || 0), 0);
    const remoteHours = attendanceRecords.reduce((sum, record) => sum + (record.remoteHours || 0), 0);
    
    // Calculate salary
    const regularPay = regularHours * hourlyRate;
    const overtimePay = overtimeHours * hourlyRate * 1.5; // 1.5x for overtime
    const grossSalary = regularPay + overtimePay;
    
    // Add allowances if salary info exists
    let allowances = 0;
    let deductions = 0;
    if (salaryInfo) {
      allowances = Object.values(salaryInfo.allowances).reduce((sum, val) => sum + (val || 0), 0);
      deductions = Object.values(salaryInfo.deductions).reduce((sum, val) => sum + (val || 0), 0);
    }
    
    const netSalary = grossSalary + allowances - deductions;
    
    // Prepare detailed attendance breakdown
    const attendanceDetails = attendanceRecords.map(record => ({
      date: record.date,
      status: record.status,
      isPresent: record.isPresent,
      totalHoursWorked: record.totalHoursWorked,
      regularHours: record.regularHours,
      overtimeHours: record.overtimeHours,
      officeHours: record.officeHours,
      remoteHours: record.remoteHours,
      workLocationType: record.workLocationType,
      checkIn: record.biometricTimeIn || record.startDayTime,
      checkOut: record.biometricTimeOut || record.endDayTime,
      dailyEarning: (record.regularHours * hourlyRate) + (record.overtimeHours * hourlyRate * 1.5),
      isRealTime: record.isRealTime ? '(Live)' : ''
    }));
    
    // Calculate work location breakdown
    const officeDays = attendanceRecords.filter(r => r.workLocationType === 'Office').length;
    const remoteDays = attendanceRecords.filter(r => r.workLocationType === 'Home' || r.workLocationType === 'Remote').length;
    const hybridDays = attendanceRecords.filter(r => r.workLocationType === 'Hybrid').length;
    
    const result = {
      success: true,
      data: {
        employee: {
          id: user._id,
          name: user.name,
          email: user.email,
          employeeId: user.employeeId,
          department: user.department,
          hourlyRate: hourlyRate
        },
        period: {
          year: parseInt(year),
          month: parseInt(month),
          monthName: new Date(year, month - 1).toLocaleString('default', { month: 'long' }),
          startDate,
          endDate
        },
        attendance: {
          totalDays,
          presentDays,
          absentDays,
          attendanceRate: totalDays > 0 ? ((presentDays / totalDays) * 100).toFixed(2) : 0,
          workLocationBreakdown: {
            officeDays,
            remoteDays,
            hybridDays
          }
        },
        hours: {
          totalHours: Math.round(totalHours * 100) / 100,
          regularHours: Math.round(regularHours * 100) / 100,
          overtimeHours: Math.round(overtimeHours * 100) / 100,
          officeHours: Math.round(officeHours * 100) / 100,
          remoteHours: Math.round(remoteHours * 100) / 100,
          avgHoursPerDay: presentDays > 0 ? (totalHours / presentDays).toFixed(2) : 0,
          officePercentage: totalHours > 0 ? ((officeHours / totalHours) * 100).toFixed(2) : 0,
          remotePercentage: totalHours > 0 ? ((remoteHours / totalHours) * 100).toFixed(2) : 0
        },
        salary: {
          hourlyRate,
          regularPay: Math.round(regularPay * 100) / 100,
          overtimePay: Math.round(overtimePay * 100) / 100,
          grossSalary: Math.round(grossSalary * 100) / 100,
          allowances: Math.round(allowances * 100) / 100,
          deductions: Math.round(deductions * 100) / 100,
          netSalary: Math.round(netSalary * 100) / 100
        },
        attendanceDetails
      }
    };
    
    // Save to SalaryAttendance collection for historical records
    await SalaryAttendance.findOneAndUpdate(
      { 
        userId: userId, 
        monthYear: `${year}-${String(month).padStart(2, '0')}` 
      },
      {
        userId: userId,
        employeeId: user.employeeId || userId,
        name: user.name,
        dept: user.department || 'Not Assigned',
        daysPresent: presentDays,
        hoursWorked: Math.round(totalHours * 100) / 100,
        totalWorkingDays: totalDays,
        avgHoursPerDay: presentDays > 0 ? totalHours / presentDays : 0,
        dailyWage: hourlyRate * 8, // 8 hours per day
        baseSalary: salaryInfo ? salaryInfo.baseSalary : regularPay,
        calculatedSalary: grossSalary,
        adjustedSalary: netSalary,
        salaryPercentage: 100,
        hoursPercentage: totalDays > 0 ? (totalHours / (totalDays * 8)) * 100 : 0,
        attendancePercentage: totalDays > 0 ? (presentDays / totalDays) * 100 : 0,
        attendanceDetails: attendanceDetails.map(att => ({
          date: att.date.toISOString().split('T')[0],
          checkIn: att.checkIn ? att.checkIn.toISOString() : '',
          checkOut: att.checkOut ? att.checkOut.toISOString() : '',
          hoursWorked: att.totalHoursWorked,
          status: att.status
        })),
        monthYear: `${year}-${String(month).padStart(2, '0')}`,
        updatedAt: new Date()
      },
      { upsert: true, new: true }
    );
    
    res.json(result);
  } catch (error) {
    console.error('Error calculating employee salary:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Error calculating salary',
      error: error.message 
    });
  }
};

/**
 * Get activity log showing all employees' worked hours
 */
exports.getEmployeeActivityLog = async (req, res) => {
  try {
    const { year, month, startDate, endDate } = req.query;
    
    let dateFilter = {};
    
    if (year && month) {
      const start = new Date(year, month - 1, 1);
      const end = new Date(year, month, 0, 23, 59, 59, 999);
      dateFilter = { date: { $gte: start, $lte: end } };
    } else if (startDate && endDate) {
      dateFilter = { 
        date: { 
          $gte: new Date(startDate), 
          $lte: new Date(endDate) 
        } 
      };
    } else {
      // Default to current month
      const now = new Date();
      const start = new Date(now.getFullYear(), now.getMonth(), 1);
      const end = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59, 999);
      dateFilter = { date: { $gte: start, $lte: end } };
    }
    
    // Get all attendance records for the period
    let activityLogData = await DailyAttendance.aggregate([
      { $match: dateFilter },
      {
        $lookup: {
          from: 'users',
          localField: 'user',
          foreignField: '_id',
          as: 'userDetails'
        }
      },
      { $unwind: '$userDetails' },
      {
        $group: {
          _id: {
            userId: '$user',
            date: {
              $dateToString: { format: '%Y-%m-%d', date: '$date' }
            }
          },
          userName: { $first: '$userDetails.name' },
          userEmail: { $first: '$userDetails.email' },
          employeeId: { $first: '$userDetails.employeeId' },
          department: { $first: '$userDetails.department' },
          date: { $first: '$date' },
          status: { $first: '$status' },
          isPresent: { $first: '$isPresent' },
          totalHoursWorked: { $sum: '$totalHoursWorked' },
          regularHours: { $sum: '$regularHours' },
          overtimeHours: { $sum: '$overtimeHours' },
          officeHours: { $sum: '$officeHours' },
          remoteHours: { $sum: '$remoteHours' },
          workLocationType: { $first: '$workLocationType' },
          checkIn: { $first: { $ifNull: ['$biometricTimeIn', '$startDayTime'] } },
          checkOut: { $first: { $ifNull: ['$biometricTimeOut', '$endDayTime'] } }
        }
      },
      {
        $project: {
          _id: 0,
          userId: '$_id.userId',
          userName: 1,
          userEmail: 1,
          employeeId: 1,
          department: 1,
          date: 1,
          status: 1,
          isPresent: 1,
          totalHoursWorked: { $round: ['$totalHoursWorked', 2] },
          regularHours: { $round: ['$regularHours', 2] },
          overtimeHours: { $round: ['$overtimeHours', 2] },
          officeHours: { $round: ['$officeHours', 2] },
          remoteHours: { $round: ['$remoteHours', 2] },
          workLocationType: 1,
          checkIn: 1,
          checkOut: 1
        }
      },
      { $sort: { date: -1, userName: 1 } }
    ]);
    
    // REAL-TIME: Add active Attendance records that haven't been synced yet
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    // Check if today is in the requested date range
    let queryStart = startDate ? new Date(startDate) : null;
    let queryEnd = endDate ? new Date(endDate) : null;
    
    if (!queryStart && !queryEnd && year && month) {
      queryStart = new Date(year, month - 1, 1);
      queryEnd = new Date(year, month, 0);
    }
    
    const isTodayInRange = !queryStart || !queryEnd || 
                          (today >= new Date(queryStart).setHours(0,0,0,0) && 
                           today <= new Date(queryEnd).setHours(23,59,59,999));
    
    if (isTodayInRange) {
      // Get active attendance sessions for today
      const activeRecords = await Attendance.find({
        date: { $gte: today, $lt: tomorrow },
        startDayTime: { $exists: true, $ne: null }
      }).populate('user', 'name email employeeId department hourlyRate');
      
      for (const record of activeRecords) {
        if (!record.user) continue;
        
        // Check if this record is already in the activity log (already synced)
        const existsInLog = activityLogData.some(log => 
          log.userId.toString() === record.user._id.toString()
        );
        
        if (!existsInLog && record.startDayTime) {
          // Calculate real-time hours
          const now = new Date();
          const hoursWorked = (now - record.startDayTime) / (1000 * 60 * 60);
          const regularHours = Math.min(hoursWorked, 8);
          const overtimeHours = Math.max(0, hoursWorked - 8);
          const officeHours = record.workLocationType === 'Office' ? hoursWorked : 0;
          const remoteHours = record.workLocationType !== 'Office' ? hoursWorked : 0;
          
          // Add to activity log with real-time flag
          activityLogData.push({
            userId: record.user._id,
            userName: record.user.name,
            userEmail: record.user.email,
            employeeId: record.user.employeeId,
            department: record.user.department,
            date: today,
            status: 'Present (Active)',
            isPresent: true,
            totalHoursWorked: Math.round(hoursWorked * 100) / 100,
            regularHours: Math.round(regularHours * 100) / 100,
            overtimeHours: Math.round(overtimeHours * 100) / 100,
            officeHours: Math.round(officeHours * 100) / 100,
            remoteHours: Math.round(remoteHours * 100) / 100,
            workLocationType: record.workLocationType || 'Office',
            checkIn: record.biometricTimeIn || record.startDayTime,
            checkOut: now,
            isRealTime: true
          });
        }
      }
    }
    
    const activityLog = activityLogData.sort((a, b) => {
      const dateA = new Date(b.date);
      const dateB = new Date(a.date);
      return dateA - dateB;
    });
    
    // Calculate summary statistics
    const summary = {
      totalRecords: activityLog.length,
      totalEmployees: [...new Set(activityLog.map(log => log.userId.toString()))].length,
      totalHours: activityLog.reduce((sum, log) => sum + log.totalHoursWorked, 0),
      totalOfficeHours: activityLog.reduce((sum, log) => sum + log.officeHours, 0),
      totalRemoteHours: activityLog.reduce((sum, log) => sum + log.remoteHours, 0),
      presentDays: activityLog.filter(log => log.isPresent).length,
      absentDays: activityLog.filter(log => !log.isPresent).length
    };
    
    res.json({
      success: true,
      data: {
        summary,
        activityLog
      }
    });
  } catch (error) {
    console.error('Error fetching activity log:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Error fetching activity log',
      error: error.message 
    });
  }
};

/**
 * Get admin dashboard with summary of all employees' hours and salary
 */
exports.getAdminDashboard = async (req, res) => {
  try {
    const { year, month } = req.params;
    
    if (!year || !month) {
      return res.status(400).json({ 
        success: false, 
        message: 'Year and month are required' 
      });
    }
    
    const startDate = new Date(year, month - 1, 1);
    const endDate = new Date(year, month, 0, 23, 59, 59, 999);
    
    // Get all users
    const users = await User.find({ stillExist: 1 }).select('_id name email employeeId department hourlyRate');
    
    // Get attendance summary for all employees
    const employeeSummaries = await Promise.all(
      users.map(async (user) => {
        const attendanceRecords = await DailyAttendance.find({
          user: user._id,
          date: { $gte: startDate, $lte: endDate }
        });
        
        const totalDays = attendanceRecords.length;
        const presentDays = attendanceRecords.filter(record => record.isPresent).length;
        const totalHours = attendanceRecords.reduce((sum, record) => sum + (record.totalHoursWorked || 0), 0);
        const regularHours = attendanceRecords.reduce((sum, record) => sum + (record.regularHours || 0), 0);
        const overtimeHours = attendanceRecords.reduce((sum, record) => sum + (record.overtimeHours || 0), 0);
        const officeHours = attendanceRecords.reduce((sum, record) => sum + (record.officeHours || 0), 0);
        const remoteHours = attendanceRecords.reduce((sum, record) => sum + (record.remoteHours || 0), 0);
        
        const hourlyRate = user.hourlyRate || 25;
        const regularPay = regularHours * hourlyRate;
        const overtimePay = overtimeHours * hourlyRate * 1.5;
        const grossSalary = regularPay + overtimePay;
        
        // Get salary info for allowances and deductions
        const salaryInfo = await Salary.findOne({ user: user._id });
        let allowances = 0;
        let deductions = 0;
        if (salaryInfo) {
          allowances = Object.values(salaryInfo.allowances).reduce((sum, val) => sum + (val || 0), 0);
          deductions = Object.values(salaryInfo.deductions).reduce((sum, val) => sum + (val || 0), 0);
        }
        
        const netSalary = grossSalary + allowances - deductions;
        
        return {
          userId: user._id,
          name: user.name,
          email: user.email,
          employeeId: user.employeeId,
          department: user.department,
          hourlyRate,
          attendance: {
            totalDays,
            presentDays,
            absentDays: totalDays - presentDays,
            attendanceRate: totalDays > 0 ? ((presentDays / totalDays) * 100).toFixed(2) : 0
          },
          hours: {
            totalHours: Math.round(totalHours * 100) / 100,
            regularHours: Math.round(regularHours * 100) / 100,
            overtimeHours: Math.round(overtimeHours * 100) / 100,
            officeHours: Math.round(officeHours * 100) / 100,
            remoteHours: Math.round(remoteHours * 100) / 100,
            avgHoursPerDay: presentDays > 0 ? (totalHours / presentDays).toFixed(2) : 0
          },
          salary: {
            regularPay: Math.round(regularPay * 100) / 100,
            overtimePay: Math.round(overtimePay * 100) / 100,
            grossSalary: Math.round(grossSalary * 100) / 100,
            allowances: Math.round(allowances * 100) / 100,
            deductions: Math.round(deductions * 100) / 100,
            netSalary: Math.round(netSalary * 100) / 100
          }
        };
      })
    );
    
    // Calculate overall statistics
    const overallStats = {
      totalEmployees: employeeSummaries.length,
      totalHoursWorked: employeeSummaries.reduce((sum, emp) => sum + emp.hours.totalHours, 0),
      totalOfficeHours: employeeSummaries.reduce((sum, emp) => sum + emp.hours.officeHours, 0),
      totalRemoteHours: employeeSummaries.reduce((sum, emp) => sum + emp.hours.remoteHours, 0),
      totalOvertimeHours: employeeSummaries.reduce((sum, emp) => sum + emp.hours.overtimeHours, 0),
      totalGrossSalary: employeeSummaries.reduce((sum, emp) => sum + emp.salary.grossSalary, 0),
      totalNetSalary: employeeSummaries.reduce((sum, emp) => sum + emp.salary.netSalary, 0),
      avgAttendanceRate: employeeSummaries.length > 0 
        ? (employeeSummaries.reduce((sum, emp) => sum + parseFloat(emp.attendance.attendanceRate), 0) / employeeSummaries.length).toFixed(2)
        : 0,
      avgHoursPerEmployee: employeeSummaries.length > 0
        ? (employeeSummaries.reduce((sum, emp) => sum + emp.hours.totalHours, 0) / employeeSummaries.length).toFixed(2)
        : 0
    };
    
    res.json({
      success: true,
      data: {
        period: {
          year: parseInt(year),
          month: parseInt(month),
          monthName: new Date(year, month - 1).toLocaleString('default', { month: 'long' }),
          startDate,
          endDate
        },
        overallStats,
        employees: employeeSummaries
      }
    });
  } catch (error) {
    console.error('Error fetching admin dashboard:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Error fetching admin dashboard',
      error: error.message 
    });
  }
};

/**
 * Get detailed hours breakdown for an employee (office vs remote)
 */
exports.getEmployeeHoursBreakdown = async (req, res) => {
  try {
    const { userId, year, month } = req.params;
    
    if (!userId || !year || !month) {
      return res.status(400).json({ 
        success: false, 
        message: 'User ID, year, and month are required' 
      });
    }
    
    const startDate = new Date(year, month - 1, 1);
    const endDate = new Date(year, month, 0, 23, 59, 59, 999);
    
    // Get work location breakdown
    const breakdown = await DailyAttendance.getWorkLocationBreakdown(
      userId,
      startDate,
      endDate
    );
    
    // Get daily breakdown
    const dailyRecords = await DailyAttendance.find({
      user: userId,
      date: { $gte: startDate, $lte: endDate },
      isPresent: true
    }).sort({ date: 1 });
    
    const dailyBreakdown = dailyRecords.map(record => ({
      date: record.date,
      workLocationType: record.workLocationType,
      totalHours: record.totalHoursWorked,
      officeHours: record.officeHours,
      remoteHours: record.remoteHours,
      regularHours: record.regularHours,
      overtimeHours: record.overtimeHours
    }));
    
    res.json({
      success: true,
      data: {
        summary: breakdown,
        dailyBreakdown
      }
    });
  } catch (error) {
    console.error('Error fetching hours breakdown:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Error fetching hours breakdown',
      error: error.message 
    });
  }
};

/**
 * Update work location type for a specific attendance record
 */
exports.updateWorkLocationType = async (req, res) => {
  try {
    const { attendanceId } = req.params;
    const { workLocationType } = req.body;
    
    if (!workLocationType || !['Office', 'Home', 'Remote', 'Hybrid'].includes(workLocationType)) {
      return res.status(400).json({ 
        success: false, 
        message: 'Valid work location type is required (Office, Home, Remote, or Hybrid)' 
      });
    }
    
    const attendance = await DailyAttendance.findById(attendanceId);
    if (!attendance) {
      return res.status(404).json({ 
        success: false, 
        message: 'Attendance record not found' 
      });
    }
    
    attendance.workLocationType = workLocationType;
    await attendance.save(); // This will trigger the pre-save hook to recalculate office/remote hours
    
    res.json({
      success: true,
      message: 'Work location type updated successfully',
      data: attendance
    });
  } catch (error) {
    console.error('Error updating work location type:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Error updating work location type',
      error: error.message 
    });
  }
};

/**
 * Bulk update hourly rates for employees
 */
exports.bulkUpdateHourlyRates = async (req, res) => {
  try {
    const { updates } = req.body; // Array of { userId, hourlyRate }
    
    if (!Array.isArray(updates) || updates.length === 0) {
      return res.status(400).json({ 
        success: false, 
        message: 'Updates array is required' 
      });
    }
    
    const results = await Promise.all(
      updates.map(async ({ userId, hourlyRate }) => {
        try {
          const user = await User.findByIdAndUpdate(
            userId,
            { hourlyRate },
            { new: true }
          );
          return { userId, success: true, user };
        } catch (error) {
          return { userId, success: false, error: error.message };
        }
      })
    );
    
    res.json({
      success: true,
      message: 'Hourly rates updated',
      results
    });
  } catch (error) {
    console.error('Error updating hourly rates:', error);
    res.status(500).json({ 
      success: false, 
      message: 'Error updating hourly rates',
      error: error.message 
    });
  }
};

module.exports = exports;
