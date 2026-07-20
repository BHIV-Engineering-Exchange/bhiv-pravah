const moment = require('moment-timezone');

/**
 * PART B: ATTENDANCE MERGE LOGIC (20-MINUTE ALLOWANCE)
 * 
 * Merges workflow and biometric attendance with intelligent conflict resolution
 * - Timezone standardization (IST)
 * - 20-minute tolerance window
 * - Reliable source selection
 * - Worked hours calculation
 * - Presence determination
 */

class AttendanceMergeLogic {
  constructor(config = {}) {
    this.timezone = config.timezone || 'Asia/Kolkata'; // IST
    this.tolerance = config.tolerance || 20; // minutes
    this.minRequiredHours = config.minRequiredHours || 4; // for half-day
    this.standardShiftHours = config.standardShiftHours || 8;
    this.debug = config.debug !== false;
  }

  /**
   * Main merge function
   * 
   * @param {Object} data - { employee_id, date, wf_in, wf_out, bio_in, bio_out }
   * @returns {Object} Merged attendance with final times and calculated values
   */
  async mergeAttendance(data) {
    const {
      employee_id,
      date,
      wf_in,
      wf_out,
      bio_in,
      bio_out
    } = data;

    // Step 1: Normalize timestamps to IST
    const normalizedData = this._normalizeTimestamps({
      date,
      wf_in,
      wf_out,
      bio_in,
      bio_out
    });

    this._log(`Processing: Employee ${employee_id} on ${date}`);
    this._log(`  Workflow: IN=${normalizedData.wf_in}, OUT=${normalizedData.wf_out}`);
    this._log(`  Biometric: IN=${normalizedData.bio_in}, OUT=${normalizedData.bio_out}`);

    // Step 2: Calculate time differences
    const timeDiffs = this._calculateTimeDifferences(normalizedData);
    this._log(`  Time differences: IN Δ=${timeDiffs.inDiff}min, OUT Δ=${timeDiffs.outDiff}min`);

    // Step 3: Apply merge logic based on availability
    const mergeResult = this._applyMergeLogic(normalizedData, timeDiffs);

    // Step 4: Calculate worked hours
    const workedHours = this._calculateWorkedHours(
      mergeResult.final_in,
      mergeResult.final_out
    );

    // Step 5: Determine presence status
    const presence = this._determinePresence(workedHours);

    return {
      employee_id,
      date,
      // Final times (source of truth)
      final_in: mergeResult.final_in,
      final_out: mergeResult.final_out,
      // Calculated values
      worked_hours: workedHours.total,
      worked_hours_decimal: workedHours.decimal,
      is_present: presence.is_present,
      status: presence.status, // 'Present', 'Absent', 'Half Day', 'Late'
      // Metadata
      merge_remarks: mergeResult.remarks,
      merge_case: mergeResult.case,
      wf_in_used: mergeResult.wf_in_used,
      bio_in_used: mergeResult.bio_in_used,
      wf_out_used: mergeResult.wf_out_used,
      bio_out_used: mergeResult.bio_out_used,
      time_diffs: timeDiffs,
      // Original values (for audit trail)
      original: {
        wf_in: normalizedData.wf_in,
        wf_out: normalizedData.wf_out,
        bio_in: normalizedData.bio_in,
        bio_out: normalizedData.bio_out
      }
    };
  }

  /**
   * Normalize timestamps to IST timezone
   */
  _normalizeTimestamps(data) {
    const { date, wf_in, wf_out, bio_in, bio_out } = data;

    return {
      date: moment(date).tz(this.timezone).startOf('day').toDate(),
      wf_in: wf_in ? moment(wf_in).tz(this.timezone).toDate() : null,
      wf_out: wf_out ? moment(wf_out).tz(this.timezone).toDate() : null,
      bio_in: bio_in ? moment(bio_in).tz(this.timezone).toDate() : null,
      bio_out: bio_out ? moment(bio_out).tz(this.timezone).toDate() : null
    };
  }

  /**
   * Calculate time differences between workflow and biometric
   */
  _calculateTimeDifferences(data) {
    let inDiff = null;
    let outDiff = null;

    if (data.wf_in && data.bio_in) {
      inDiff = Math.abs(moment(data.wf_in).diff(moment(data.bio_in), 'minutes'));
    }

    if (data.wf_out && data.bio_out) {
      outDiff = Math.abs(moment(data.wf_out).diff(moment(data.bio_out), 'minutes'));
    }

    return {
      inDiff,
      outDiff,
      inWithinTolerance: inDiff !== null && inDiff <= this.tolerance,
      outWithinTolerance: outDiff !== null && outDiff <= this.tolerance
    };
  }

  /**
   * Apply merge logic based on data availability
   * 
   * Cases:
   * 1. Both workflow and biometric exist
   *    - Within 20 min: use earliest IN, latest OUT
   *    - > 20 min: use bio IN, wf OUT
   * 2. Only workflow exists: use workflow times
   * 3. Only biometric exists: use biometric times
   */
  _applyMergeLogic(data, timeDiffs) {
    const { wf_in, wf_out, bio_in, bio_out } = data;

    // CASE 1: Both exist
    if (wf_in && wf_out && bio_in && bio_out) {
      if (timeDiffs.inWithinTolerance && timeDiffs.outWithinTolerance) {
        // Within tolerance: use most extreme times (earliest IN, latest OUT)
        return {
          case: 'CASE1_BOTH_MATCHED',
          final_in: moment.min(moment(wf_in), moment(bio_in)).toDate(),
          final_out: moment.max(moment(wf_out), moment(bio_out)).toDate(),
          remarks: 'MATCHED (within 20min tolerance)',
          wf_in_used: wf_in,
          bio_in_used: bio_in,
          wf_out_used: wf_out,
          bio_out_used: bio_out
        };
      } else {
        // Mismatch > 20 min: trust biometric IN (more reliable), workflow OUT (logout)
        return {
          case: 'CASE1_BOTH_MISMATCH',
          final_in: bio_in, // Gate entry more reliable
          final_out: wf_out, // Workflow logout usually accurate
          remarks: `MISMATCH_20+ (IN Δ=${timeDiffs.inDiff}min, OUT Δ=${timeDiffs.outDiff}min)`,
          wf_in_used: false,
          bio_in_used: true,
          wf_out_used: true,
          bio_out_used: false
        };
      }
    }

    // CASE 2: Only workflow exists
    if (wf_in && wf_out && !bio_in && !bio_out) {
      return {
        case: 'CASE2_WF_ONLY',
        final_in: wf_in,
        final_out: wf_out,
        remarks: 'BIO_MISSING',
        wf_in_used: true,
        bio_in_used: false,
        wf_out_used: true,
        bio_out_used: false
      };
    }

    // CASE 3: Only biometric exists
    if (bio_in && bio_out && !wf_in && !wf_out) {
      return {
        case: 'CASE3_BIO_ONLY',
        final_in: bio_in,
        final_out: bio_out,
        remarks: 'WF_MISSING',
        wf_in_used: false,
        bio_in_used: true,
        wf_out_used: false,
        bio_out_used: true
      };
    }

    // CASE 4: Only IN times exist (no OUT)
    if ((wf_in || bio_in) && !wf_out && !bio_out) {
      const finalIn = wf_in || bio_in;
      return {
        case: 'CASE4_NO_OUT',
        final_in: finalIn,
        final_out: null,
        remarks: 'NO_PUNCH_OUT',
        wf_in_used: !!wf_in,
        bio_in_used: !!bio_in,
        wf_out_used: false,
        bio_out_used: false
      };
    }

    // CASE 5: Incomplete data
    return {
      case: 'CASE5_INCOMPLETE',
      final_in: null,
      final_out: null,
      remarks: 'INCOMPLETE_DATA',
      wf_in_used: false,
      bio_in_used: false,
      wf_out_used: false,
      bio_out_used: false
    };
  }

  /**
   * Calculate worked hours from IN and OUT times
   */
  _calculateWorkedHours(inTime, outTime) {
    if (!inTime || !outTime) {
      return {
        total: 0,
        decimal: 0,
        regular: 0,
        overtime: 0,
        status: 'INCOMPLETE'
      };
    }

    const start = moment(inTime);
    const end = moment(outTime);

    // Calculate total hours (with decimal precision)
    const diffMs = end.diff(start);
    const diffHours = diffMs / (1000 * 60 * 60);
    const decimalHours = Math.round(diffHours * 100) / 100; // 2 decimal places

    // Split into regular and overtime
    const regularHours = Math.min(decimalHours, this.standardShiftHours);
    const overtimeHours = Math.max(0, decimalHours - this.standardShiftHours);

    return {
      total: Math.floor(diffHours), // Total hours as integer
      decimal: decimalHours, // Total hours with decimals
      regular: regularHours,
      overtime: overtimeHours,
      status: 'COMPLETE'
    };
  }

  /**
   * Determine presence status based on worked hours
   */
  _determinePresence(workedHours) {
    const hours = workedHours.decimal;

    let status = 'Absent';
    let is_present = false;

    if (hours >= this.standardShiftHours) {
      status = 'Present';
      is_present = true;
    } else if (hours >= this.minRequiredHours) {
      status = 'Half Day';
      is_present = true;
    } else if (hours > 0) {
      status = 'Late'; // Came but left early or very late check-in
      is_present = false;
    }

    return {
      status,
      is_present,
      hours_worked: hours
    };
  }

  /**
   * Validate punch sequence (no crossing IN/OUT)
   */
  validatePunchSequence(inTime, outTime) {
    if (!inTime || !outTime) {
      return { valid: true };
    }

    if (moment(outTime).isBefore(moment(inTime))) {
      return {
        valid: false,
        error: 'OUT_BEFORE_IN',
        message: 'Out time is before in time'
      };
    }

    return { valid: true };
  }

  /**
   * Detect and report anomalies
   */
  detectAnomalies(data) {
    const anomalies = [];

    // Check for extremely long shifts
    if (data.worked_hours > 16) {
      anomalies.push({
        type: 'UNUSUALLY_LONG_SHIFT',
        severity: 'warning',
        message: `Worked ${data.worked_hours} hours (> 16 hours)`
      });
    }

    // Check for time sequence anomaly
    if (data.time_diffs.inDiff && data.time_diffs.inDiff > 60) {
      anomalies.push({
        type: 'LARGE_IN_TIME_MISMATCH',
        severity: 'warning',
        message: `IN time mismatch: ${data.time_diffs.inDiff} minutes`
      });
    }

    // Check for midnight crossover
    const inDate = moment(data.final_in);
    const outDate = moment(data.final_out);
    if (inDate.date() !== outDate.date()) {
      anomalies.push({
        type: 'MIDNIGHT_CROSSOVER',
        severity: 'info',
        message: 'Shift crosses midnight'
      });
    }

    return anomalies;
  }

  /**
   * Logging helper
   */
  _log(message) {
    if (this.debug) {
      console.log(`[AttendanceMerge] ${message}`);
    }
  }

  /**
   * Batch merge for multiple days
   */
  async batchMergeAttendance(attendanceRecords) {
    const results = {
      successful: [],
      failed: [],
      anomalies: [],
      summary: {
        total: attendanceRecords.length,
        processed: 0,
        errors: 0,
        withAnomalies: 0
      }
    };

    for (const record of attendanceRecords) {
      try {
        const merged = await this.mergeAttendance(record);
        const anomalies = this.detectAnomalies(merged);

        if (anomalies.length > 0) {
          results.anomalies.push({
            employee_id: record.employee_id,
            date: record.date,
            anomalies
          });
          results.summary.withAnomalies++;
        }

        results.successful.push(merged);
        results.summary.processed++;
      } catch (error) {
        results.failed.push({
          record,
          error: error.message
        });
        results.summary.errors++;
      }
    }

    return results;
  }
}

module.exports = AttendanceMergeLogic;
