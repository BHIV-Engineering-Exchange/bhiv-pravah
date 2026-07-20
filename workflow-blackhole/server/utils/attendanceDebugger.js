const fs = require('fs');
const path = require('path');
const moment = require('moment');

/**
 * PART C: DEBUG LOGGING & ERROR HANDLING
 * 
 * Comprehensive logging system for attendance reconciliation
 * - Issue detection and categorization
 * - Audit trail generation
 * - Error recovery suggestions
 */

class AttendanceDebugger {
  constructor(logsDir = './logs/attendance-debug') {
    this.logsDir = logsDir;
    this.issues = [];
    this.metrics = {
      totalRecords: 0,
      processedRecords: 0,
      errorsFound: 0,
      warningsFound: 0,
      fixesApplied: 0
    };

    // Ensure logs directory exists
    if (!fs.existsSync(logsDir)) {
      fs.mkdirSync(logsDir, { recursive: true });
    }
  }

  /**
   * Debug check: Detect wrong ID mapping
   */
  checkIdMappingIssues(biometricPunches, employees) {
    const issues = [];

    for (const punch of biometricPunches) {
      if (!punch.user || punch.user === null) {
        issues.push({
          type: 'UNRESOLVED_BIOMETRIC_ID',
          severity: 'ERROR',
          record: punch,
          message: `Biometric punch has no mapped employee: ${punch.biometricId}`,
          suggestion: 'Check if biometric ID exists in employee master or try fuzzy matching'
        });
      }
    }

    if (issues.length > 0) {
      this._logIssues('ID Mapping Issues', issues);
    }

    return issues;
  }

  /**
   * Debug check: Detect duplicate biometric punches
   */
  checkDuplicatePunches(punches) {
    const issues = [];
    const seen = new Map();

    for (const punch of punches) {
      const key = `${punch.user}_${punch.date}_${punch.punchTime}`;

      if (seen.has(key)) {
        issues.push({
          type: 'DUPLICATE_PUNCH',
          severity: 'WARNING',
          records: [punch, seen.get(key)],
          message: `Duplicate punch detected for user ${punch.user} at ${punch.punchTime}`,
          suggestion: 'Remove or merge duplicate records'
        });
      } else {
        seen.set(key, punch);
      }
    }

    if (issues.length > 0) {
      this._logIssues('Duplicate Punches', issues);
    }

    return issues;
  }

  /**
   * Debug check: Incorrect grouping by date
   */
  checkDateGroupingIssues(attendance) {
    const issues = [];

    for (const record of attendance) {
      // Check if IN and OUT times are on same date
      if (record.biometricTimeIn && record.biometricTimeOut) {
        const inDate = moment(record.biometricTimeIn).format('YYYY-MM-DD');
        const outDate = moment(record.biometricTimeOut).format('YYYY-MM-DD');

        if (inDate !== outDate) {
          issues.push({
            type: 'MIDNIGHT_CROSSOVER',
            severity: 'WARNING',
            record: record,
            message: `Shift crosses midnight: IN on ${inDate}, OUT on ${outDate}`,
            suggestion: 'Verify if this is a night shift or data entry error'
          });
        }
      }

      // Check if record date matches IN/OUT times
      const recordDate = moment(record.date).format('YYYY-MM-DD');
      if (record.biometricTimeIn) {
        const inDate = moment(record.biometricTimeIn).format('YYYY-MM-DD');
        if (recordDate !== inDate) {
          issues.push({
            type: 'DATE_MISMATCH',
            severity: 'ERROR',
            record: record,
            message: `Record date ${recordDate} doesn't match IN time date ${inDate}`,
            suggestion: 'Check timezone configuration or IN time value'
          });
        }
      }
    }

    if (issues.length > 0) {
      this._logIssues('Date Grouping Issues', issues);
    }

    return issues;
  }

  /**
   * Debug check: Timezone offset causing IN/OUT on wrong days
   */
  checkTimezoneIssues(attendance) {
    const issues = [];

    for (const record of attendance) {
      if (!record.biometricTimeIn) continue;

      const inTime = moment(record.biometricTimeIn);
      const recordDate = moment(record.date);

      // Check if there's a timezone offset issue
      const diffDays = inTime.diff(recordDate, 'days');

      if (diffDays !== 0) {
        issues.push({
          type: 'TIMEZONE_OFFSET_ISSUE',
          severity: 'WARNING',
          record: record,
          message: `Timezone offset causing IN time to appear on different day (${diffDays} days difference)`,
          suggestion: `Adjust timezone from ${inTime.tz()} to consistent timezone (IST)`
        });
      }
    }

    if (issues.length > 0) {
      this._logIssues('Timezone Issues', issues);
    }

    return issues;
  }

  /**
   * Debug check: Wrong punch selection (mid-day instead of earliest/latest)
   */
  checkPunchSelectionIssues(punchGroups) {
    const issues = [];

    for (const group of punchGroups) {
      if (group.punches.length < 2) continue;

      // Sort by time
      const sorted = [...group.punches].sort((a, b) => 
        new Date(a.punchTime) - new Date(b.punchTime)
      );

      const firstPunch = sorted[0];
      const lastPunch = sorted[sorted.length - 1];

      // Check if selected times are first and last
      if (group.selectedIn && group.selectedIn.punchTime !== firstPunch.punchTime) {
        issues.push({
          type: 'INCORRECT_IN_PUNCH_SELECTION',
          severity: 'ERROR',
          record: group,
          message: `Selected IN time is not the earliest punch`,
          expected: firstPunch.punchTime,
          actual: group.selectedIn.punchTime,
          suggestion: 'Always select earliest punch as IN time'
        });
      }

      if (group.selectedOut && group.selectedOut.punchTime !== lastPunch.punchTime) {
        issues.push({
          type: 'INCORRECT_OUT_PUNCH_SELECTION',
          severity: 'ERROR',
          record: group,
          message: `Selected OUT time is not the latest punch`,
          expected: lastPunch.punchTime,
          actual: group.selectedOut.punchTime,
          suggestion: 'Always select latest punch as OUT time'
        });
      }
    }

    if (issues.length > 0) {
      this._logIssues('Punch Selection Issues', issues);
    }

    return issues;
  }

  /**
   * Debug check: Out-of-order punch sequence
   */
  checkPunchSequence(punches) {
    const issues = [];

    for (const punch of punches) {
      if (punch.punchOut && new Date(punch.punchOut) < new Date(punch.punchIn)) {
        issues.push({
          type: 'OUT_OF_ORDER_PUNCH_SEQUENCE',
          severity: 'ERROR',
          record: punch,
          message: `OUT time (${punch.punchOut}) is before IN time (${punch.punchIn})`,
          suggestion: 'Reverse times or mark as data entry error'
        });
      }
    }

    if (issues.length > 0) {
      this._logIssues('Punch Sequence Issues', issues);
    }

    return issues;
  }

  /**
   * Debug check: Multiple IN/OUT punches
   */
  checkMultiplePunches(punchGroups) {
    const issues = [];

    for (const group of punchGroups) {
      const inPunches = group.punches.filter(p => p.punchType === 'In');
      const outPunches = group.punches.filter(p => p.punchType === 'Out');

      if (inPunches.length > 1) {
        issues.push({
          type: 'MULTIPLE_IN_PUNCHES',
          severity: 'WARNING',
          record: group,
          message: `Multiple IN punches found (${inPunches.length}): using earliest`,
          suggestion: 'Review for duplicate/accidental punches'
        });
      }

      if (outPunches.length > 1) {
        issues.push({
          type: 'MULTIPLE_OUT_PUNCHES',
          severity: 'WARNING',
          record: group,
          message: `Multiple OUT punches found (${outPunches.length}): using latest`,
          suggestion: 'Review for early departures and returns'
        });
      }
    }

    if (issues.length > 0) {
      this._logIssues('Multiple Punches', issues);
    }

    return issues;
  }

  /**
   * Debug check: Invalid date formats in CSV
   */
  checkDateFormats(records) {
    const issues = [];
    const dateFormats = [
      'YYYY-MM-DD HH:mm:ss',
      'DD/MM/YYYY HH:mm:ss',
      'MM/DD/YYYY HH:mm:ss',
      'DD-MM-YYYY HH:mm:ss'
    ];

    for (const record of records) {
      const dateStr = record.punchTime || record.timestamp || record.date;
      
      if (!dateStr) continue;

      let valid = false;
      for (const format of dateFormats) {
        if (moment(dateStr, format, true).isValid()) {
          valid = true;
          break;
        }
      }

      if (!valid) {
        issues.push({
          type: 'INVALID_DATE_FORMAT',
          severity: 'ERROR',
          record: record,
          message: `Invalid date format: "${dateStr}"`,
          suggestion: `Use one of: ${dateFormats.join(', ')}`
        });
      }
    }

    if (issues.length > 0) {
      this._logIssues('Date Format Issues', issues);
    }

    return issues;
  }

  /**
   * Debug check: Missing biometric logs tagged as absent
   */
  checkMissingBiometricLogs(attendance) {
    const issues = [];

    for (const record of attendance) {
      if (!record.biometricTimeIn && record.status === 'Absent' && !record.isOnLeave) {
        // Double-check that it's truly absent (no workflow data either)
        if (!record.startDayTime && !record.endDayTime) {
          issues.push({
            type: 'MISSING_BIOMETRIC_MARKED_ABSENT',
            severity: 'INFO',
            record: record,
            message: `Employee marked absent - no biometric or workflow data found`,
            suggestion: 'Verify if employee was actually absent or biometric data is missing'
          });
        }
      }
    }

    return issues;
  }

  /**
   * Debug check: Department filter consistency
   */
  checkDepartmentFilterConsistency(attendance, departments) {
    const issues = [];
    const departmentMap = new Map(departments.map(d => [d._id.toString(), d.name]));

    for (const record of attendance) {
      if (!record.user || !record.user.department) continue;

      const deptId = record.user.department.toString();
      if (!departmentMap.has(deptId)) {
        issues.push({
          type: 'INVALID_DEPARTMENT_REFERENCE',
          severity: 'WARNING',
          record: record,
          message: `Department reference ${deptId} not found in department master`,
          suggestion: 'Verify department exists or update reference'
        });
      }
    }

    if (issues.length > 0) {
      this._logIssues('Department Consistency Issues', issues);
    }

    return issues;
  }

  /**
   * Comprehensive audit report
   */
  async generateAuditReport(attendance, biometricPunches, employees) {
    const report = {
      timestamp: new Date(),
      summary: {
        totalAttendanceRecords: attendance.length,
        totalBiometricPunches: biometricPunches.length,
        totalEmployees: employees.length
      },
      issues: {
        idMappingIssues: this.checkIdMappingIssues(biometricPunches, employees),
        duplicatePunches: this.checkDuplicatePunches(biometricPunches),
        dateGroupingIssues: this.checkDateGroupingIssues(attendance),
        timezoneIssues: this.checkTimezoneIssues(attendance),
        punchSequenceIssues: this.checkPunchSequence(attendance),
        multiPunchIssues: this.checkMultiplePunches(biometricPunches),
        missingBioLogs: this.checkMissingBiometricLogs(attendance),
        dateFormatIssues: this.checkDateFormats(biometricPunches)
      },
      totalIssuesFound: 0
    };

    // Count total issues
    for (const category in report.issues) {
      if (Array.isArray(report.issues[category])) {
        report.totalIssuesFound += report.issues[category].length;
      }
    }

    // Save report
    const reportFile = path.join(
      this.logsDir,
      `audit-report-${moment().format('YYYY-MM-DD-HHmmss')}.json`
    );
    fs.writeFileSync(reportFile, JSON.stringify(report, null, 2));

    console.log(`📋 Audit report saved: ${reportFile}`);

    return report;
  }

  /**
   * Log issues to file
   */
  _logIssues(category, issues) {
    const logFile = path.join(
      this.logsDir,
      `${category.toLowerCase().replace(/\s+/g, '-')}-${moment().format('YYYY-MM-DD')}.log`
    );

    let logContent = `${moment().format('YYYY-MM-DD HH:mm:ss')} - ${category}\n`;
    logContent += '='.repeat(80) + '\n\n';

    for (const issue of issues) {
      logContent += `[${issue.severity}] ${issue.type}\n`;
      logContent += `Message: ${issue.message}\n`;
      if (issue.suggestion) {
        logContent += `Suggestion: ${issue.suggestion}\n`;
      }
      logContent += '\n';
    }

    fs.appendFileSync(logFile, logContent);
  }

  /**
   * Generate fix recommendations
   */
  generateFixRecommendations(auditReport) {
    const recommendations = [];

    // ID Mapping fixes
    if (auditReport.issues.idMappingIssues.length > 0) {
      recommendations.push({
        category: 'ID Mapping',
        priority: 'HIGH',
        fixes: [
          'Re-run biometric upload with enhanced identity resolver',
          'Manually map ambiguous biometric IDs to employees',
          'Add missing biometric codes to employee master',
          'Review and update employee name format for better matching'
        ]
      });
    }

    // Duplicate fixes
    if (auditReport.issues.duplicatePunches.length > 0) {
      recommendations.push({
        category: 'Duplicate Punches',
        priority: 'HIGH',
        fixes: [
          'Remove duplicate punch records',
          'Merge duplicate punches into single record',
          'Implement duplicate detection in upload processor'
        ]
      });
    }

    // Timezone fixes
    if (auditReport.issues.timezoneIssues.length > 0) {
      recommendations.push({
        category: 'Timezone',
        priority: 'HIGH',
        fixes: [
          'Standardize all timestamps to IST (Asia/Kolkata)',
          'Check biometric device timezone settings',
          'Update attendance records with correct timezone'
        ]
      });
    }

    // Missing data fixes
    if (auditReport.issues.missingBioLogs.length > 0) {
      recommendations.push({
        category: 'Missing Data',
        priority: 'MEDIUM',
        fixes: [
          'Check biometric device logs for upload failures',
          'Request manual attendance entries for missing days',
          'Review leave records for that period'
        ]
      });
    }

    return recommendations;
  }
}

module.exports = AttendanceDebugger;
