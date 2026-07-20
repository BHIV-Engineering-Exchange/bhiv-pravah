/**
 * NEW ATTENDANCE TYPES - Aligned with Backend Schema
 * Based on DailyAttendance model and enhanced biometric merge logic
 */

export interface AttendanceMergeDetails {
  case: 'CASE1_BOTH_MATCHED' | 'CASE1_BOTH_MISMATCH' | 'CASE2_WF_ONLY' | 'CASE3_BIO_ONLY' | 'CASE4_NO_OUT' | 'CASE5_INCOMPLETE';
  remarks: 'MATCHED' | 'BIO_MISSING' | 'WF_MISSING' | 'MISMATCH_20+' | 'NO_PUNCH_OUT' | 'INCOMPLETE_DATA' | string;
  wfTimeIn: Date | string | null;
  wfTimeOut: Date | string | null;
  bioTimeIn: Date | string | null;
  bioTimeOut: Date | string | null;
  timeDifferences?: {
    inDiff: number | null;
    outDiff: number | null;
    inWithinTolerance: boolean;
    outWithinTolerance: boolean;
  };
}

export interface DailyAttendanceRecord {
  _id: string;
  employee: {
    _id: string;
    name: string;
    email: string;
    department?: string | { _id: string; name: string };
  };
  date: Date | string;
  
  // Final times (source of truth)
  times: {
    final_in: Date | string | null;
    final_out: Date | string | null;
    worked_hours: number;
  };
  
  // Status fields
  status: 'Present' | 'Absent' | 'Half Day' | 'Late' | 'On Leave' | 'Holiday';
  isPresent: boolean;
  
  // Merge details (NEW)
  mergeDetails?: AttendanceMergeDetails;
  
  // Salary information
  salary?: {
    basicForDay: number;
    hourlyRate: number;
  };
  
  // Verification
  verification?: {
    method: 'StartDay' | 'Biometric' | 'Both' | 'Manual' | 'Leave';
    isVerified: boolean;
  };
  
  // Source metadata
  source?: 'StartDay' | 'Biometric' | 'Both' | 'Manual' | 'Leave' | 'Holiday';
}

// For backward compatibility with existing components
export interface LegacyAttendanceRecord {
  _id: string;
  user: {
    _id: string;
    name: string;
    email: string;
    department?: any;
  };
  date: Date | string;
  startDayTime?: Date | string;
  endDayTime?: Date | string;
  biometricTimeIn?: Date | string;
  biometricTimeOut?: Date | string;
  totalHoursWorked: number;
  status: string;
  isPresent: boolean;
  workLocationType?: string;
  location?: any;
}

// Biometric Upload Response
export interface BiometricUploadResult {
  success: boolean;
  message: string;
  data: {
    processed: number;
    created: number;
    updated: number;
    errors: Array<{
      row: number;
      error: string;
    }>;
    identityMatches: {
      exact: number;
      fuzzy: number;
      ambiguous: number;
      notFound: number;
    };
    ambiguousMatches?: Array<{
      biometricName: string;
      candidates: string[];
      score: number;
    }>;
  };
  recommendations?: string[];
}

// Monthly Payroll (for future use)
export interface MonthlyPayrollRecord {
  _id: string;
  employee: {
    _id: string;
    name: string;
    department: string;
  };
  year: number;
  month: number;
  period: {
    startDate: Date | string;
    endDate: Date | string;
  };
  attendance: {
    totalDays: number;
    presentDays: number;
    absentDays: number;
    leaveDays: number;
    attendanceRate: number;
  };
  hours: {
    totalHours: number;
    regularHours: number;
    overtimeHours: number;
    avgHoursPerDay: number;
  };
  salary: {
    baseSalary: number;
    regularPay: number;
    overtimePay: number;
    allowances: number;
    deductions: number;
    netSalary: number;
  };
}

// Dashboard Stats
export interface AttendanceDashboardStats {
  totalEmployees: number;
  presentToday: number;
  absentToday: number;
  presentPercentage: number;
  absentPercentage: number;
  avgHoursToday: number;
  totalHoursToday: number;
  withAims?: number;
  working?: number;
  offline?: number;
  withLocation?: number;
  earliestStart?: string;
  latestStart?: string;
  departmentStats?: any[];
}

// Filters
export interface AttendanceFilters {
  startDate?: string;
  endDate?: string;
  date?: string;
  departmentId?: string;
  userId?: string;
  status?: 'all' | 'Present' | 'Absent' | 'Half Day' | 'Late' | 'On Leave';
  workType?: string;
}

// Reconciliation Summary
export interface ReconciliationSummary {
  success: boolean;
  dateRange: {
    start: Date | string;
    end: Date | string;
  };
  summary: {
    totalRecords: number;
    withinTolerance: number;
    mismatchesDetected: number;
    mergeDistribution: Record<string, number>;
    remarksDistribution: Record<string, number>;
  };
}

// Employee Aggregate Data
export interface EmployeeAggregateData {
  _id: string;
  employee: {
    name: string;
    department: string;
  };
  totalDays: number;
  presentDays: number;
  totalHours: number;
  avgHoursPerDay: number;
  totalSalary: number;
  source: {
    bothSources: number;
    biometricOnly: number;
    workflowOnly: number;
  };
}

// Detailed Log Entry
export interface DetailedLogEntry {
  _id: string;
  date: Date | string;
  employee: {
    name: string;
    department: string;
  };
  finalIn: Date | string | null;
  finalOut: Date | string | null;
  workedHours: number;
  status: string;
  remarks: string;
  case: string;
  salary: number;
}
