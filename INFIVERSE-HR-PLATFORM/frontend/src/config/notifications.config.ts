/**
 * Notification System Configuration
 * 
 * Centralized configuration for bulk notification filtering and validation
 */

// Validation Regex Patterns
export const VALIDATION_PATTERNS = {
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PHONE: /^[\d\s+\-().]{10,}$/,
} as const

// Filtering Thresholds
export const FILTER_CONFIG = {
  MIN_MATCHING_SCORE: 70,           // Minimum score for AI matching (backend uses 0.7 = 70%)
  NEW_APPLICANT_DAYS: 7,            // Days to consider application as "new" (last 7 days)
  MAX_CANDIDATES: 100,              // Maximum candidates to load per request
  BULK_SEND_WARNING_THRESHOLD: 20, // Show confirmation dialog if exceeding this many
} as const

// Test/Demo Values to Block (Quality Control)
export const BLOCKED_TEST_VALUES = {
  EMAILS: [
    'test@example.com',
    'test@test.com',
    'demo@example.com',
    'sample@example.com',
  ] as string[],
  EMAIL_PREFIXES: ['test@', 'demo@', 'sample@'] as string[],
  PHONES: [
    '+1234567890',
    '1234567890',
    '+9999999999',
    '0000000000',
  ] as string[],
} as const

// Candidate Status Definitions
export const CANDIDATE_STATUS = {
  // Application Stage
  PENDING: 'pending',
  NEW: 'new',
  APPLICATION_RECEIVED: 'application_received',
  
  // Screening Stage
  SCREENING: 'screening',
  SHORTLISTED: 'shortlisted',
  
  // Interview Stage
  INTERVIEW_SCHEDULED: 'interview_scheduled',
  INTERVIEWED: 'interviewed',
  AWAITING_FEEDBACK: 'awaiting_feedback',
  
  // Final Stages
  OFFERED: 'offered',
  HIRED: 'hired',
  REJECTED: 'rejected',
  WITHDRAWN: 'withdrawn',
  WITHDRAWN_BY_CANDIDATE: 'withdrawn_by_candidate',
} as const

// Notification Type Definitions
export const NOTIFICATION_TYPES = {
  SHORTLISTED: {
    id: 'shortlisted',
    label: '🎯 Shortlisted (Passed Screening)',
    description: 'Candidates who have been shortlisted (status-based, no score requirement)',
    filterCriteria: {
      status: CANDIDATE_STATUS.SHORTLISTED,
      // NOTE: No matching_score_gte filter - this is purely status-based
      // These candidates were already manually shortlisted by recruiter
      excludeStatuses: [
        CANDIDATE_STATUS.REJECTED,
        CANDIDATE_STATUS.WITHDRAWN,
        CANDIDATE_STATUS.HIRED,
      ],
    },
  },
  INTERVIEW_SCHEDULED: {
    id: 'interview_scheduled',
    label: '📅 Interview Scheduled',
    description: 'Candidates who have been selected for interviews (status: interview_scheduled)',
    filterCriteria: {
      // Show candidates with interview_scheduled status in job_applications
      // Matches dashboard logic: counts from job_applications with this status
      status: CANDIDATE_STATUS.INTERVIEW_SCHEDULED,
    },
  },
  APPLICATION_RECEIVED: {
    id: 'application_received',
    label: '✉️ Application Received',
    description: 'Candidates who applied to jobs but not yet shortlisted, interviewed, or rejected',
    filterCriteria: {
      // Applicants in pending status - not yet processed
      // Excludes: shortlisted, interview_scheduled, rejected, withdrawn, hired
      statuses: [
        CANDIDATE_STATUS.PENDING,
        CANDIDATE_STATUS.NEW,
        CANDIDATE_STATUS.APPLICATION_RECEIVED,
      ],
      createdWithinDays: FILTER_CONFIG.NEW_APPLICANT_DAYS,
      includeNeverApplied: true, // Special flag for candidates with no applications
    },
  },
  REJECTION_SENT: {
    id: 'rejection_sent',
    label: '❌ Rejection Notification',
    description: 'Candidates who have been rejected (status-based only)',
    filterCriteria: {
      // Show ONLY rejected candidates - no other filters
      status: CANDIDATE_STATUS.REJECTED,
      excludeStatuses: [CANDIDATE_STATUS.WITHDRAWN_BY_CANDIDATE],
    },
  },
} as const

// Validation Messages
export const VALIDATION_MESSAGES = {
  EMAIL_REQUIRED: 'Email is required',
  EMAIL_INVALID: 'Invalid email format (e.g., user@example.com)',
  EMAIL_TEST: 'Please use a real email address',
  
  PHONE_INVALID: 'Invalid phone format (min 10 digits)',
  PHONE_TEST: 'Please use a real phone number',
  
  CONTACT_REQUIRED: 'Email or phone is required',
} as const

// Toast Messages
export const TOAST_MESSAGES = {
  NO_CANDIDATES: (type: string) => `No candidates found for ${type.replace('_', ' ')} notifications`,
  CANDIDATES_LOADED: (count: number) => `Found ${count} candidate(s) for notifications`,
  LOADING_FAILED: 'Failed to load candidates. Please try again.',
  NETWORK_ERROR: 'Network error: Cannot connect to server. Please check your connection.',
  
  VALIDATION_ERROR: 'Please fix validation errors before sending notifications',
  INVALID_CONTACTS: (count: number) => `${count} candidate(s) have invalid contact info (need real email or 10+ digit phone)`,
  
  BULK_SEND_SUCCESS: (success: number, total: number, failed: number) => 
    `✅ Bulk notifications sent to ${success}/${total} candidates (${failed} failed)`,
  BULK_SEND_FAILED: (count: number) => 
    `❌ Failed to send notifications to all ${count} candidates. Check backend logs for details.`,
  BULK_SEND_PARTIAL: '⚠️ Notifications processed but no confirmations received',
  BULK_SEND_ERROR: (error: string) => 
    `Failed to send bulk notifications: ${error}`,
  
  BULK_SEND_CONFIRM: (count: number) => 
    `You are about to send notifications to ${count} candidates. This action cannot be undone. Continue?`,
} as const

// UI Configuration
export const UI_CONFIG = {
  // Loading states
  LOADING_SPINNER_SIZE: 'h-4 w-4',
  DEBOUNCE_DELAY_MS: 300,
  
  // Status badge colors
  STATUS_COLORS: {
    [CANDIDATE_STATUS.SHORTLISTED]: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    [CANDIDATE_STATUS.INTERVIEW_SCHEDULED]: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    [CANDIDATE_STATUS.INTERVIEWED]: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
    [CANDIDATE_STATUS.REJECTED]: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    DEFAULT: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  } as Record<string, string>,
  
  // Toast durations
  TOAST_DURATION: {
    SHORT: 3000,
    MEDIUM: 5000,
    LONG: 6000,
  },
} as const

// Type exports for TypeScript
export type NotificationType = keyof typeof NOTIFICATION_TYPES
export type CandidateStatus = typeof CANDIDATE_STATUS[keyof typeof CANDIDATE_STATUS]
