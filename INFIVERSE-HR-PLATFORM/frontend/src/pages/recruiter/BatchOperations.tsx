import { useState, useEffect, useRef } from 'react'
import toast from 'react-hot-toast'
import {
  getAllCandidates,
  getRecruiterJobs,
  previewNotification,
  sendBulkNotifications,
  sendGroupedNotifications,
  type Job,
  type CandidateFilters,
} from '../../services/api'
import BulkCandidateUploadPanel from '../../components/recruiter/BulkCandidateUploadPanel'
import { authStorage } from '../../utils/authStorage'
import {
  VALIDATION_PATTERNS,
  FILTER_CONFIG,
  BLOCKED_TEST_VALUES,
  CANDIDATE_STATUS,
  VALIDATION_MESSAGES,
  TOAST_MESSAGES,
  UI_CONFIG,
} from '../../config/notifications.config'

// Helper function for date calculations
const getTodayDate = (): string => {
  return new Date().toISOString().split('T')[0]
}

export default function BatchOperations() {
  // Persist active tab across page refreshes
  const [activeTab, setActiveTab] = useState<'upload' | 'notifications'>(() => {
    const saved = localStorage.getItem('batchOperationsActiveTab')
    return (saved === 'notifications' || saved === 'upload') ? saved : 'upload'
  })
  const [sendingNotifications, setSendingNotifications] = useState(false)
  
  // Notifications tab states
  const [notificationType, setNotificationType] = useState<string>('')
  const [candidates, setCandidates] = useState<any[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [selectedJobId, setSelectedJobId] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [validationErrors, setValidationErrors] = useState<Map<number, { email?: string; phone?: string }>>(new Map())
  const [lastRefreshTime, setLastRefreshTime] = useState<Date | null>(null)
  const [showPreviewModal, setShowPreviewModal] = useState(false)
  const [previewData, setPreviewData] = useState<any>(null)
  const [loadingPreview, setLoadingPreview] = useState(false)
  
  // Abort controller for canceling requests
  const abortControllerRef = useRef<AbortController | null>(null)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  // Auto-refresh for application_received every 24 hours
  useEffect(() => {
    if (notificationType === 'application_received') {
      const TWENTY_FOUR_HOURS = 24 * 60 * 60 * 1000 // 24 hours in milliseconds
      
      const intervalId = setInterval(() => {
        console.log('🔄 Auto-refreshing application_received candidates (24h interval)')
        loadCandidates('application_received')
        toast.success('🔄 New applicants list auto-refreshed')
      }, TWENTY_FOUR_HOURS)

      return () => {
        clearInterval(intervalId)
      }
    }
  }, [notificationType])

  // Get filter criteria based on notification type
  const getFiltersForNotificationType = (type: string): CandidateFilters => {
    // Try multiple possible ID storage keys
    const recruiterId = authStorage.getItem('user_id') || 
                        authStorage.getItem('recruiter_id') || 
                        authStorage.getItem('backend_candidate_id') ||
                        authStorage.getItem('candidate_id')
    
    // Debug: Log auth storage contents if no recruiter_id found
    if (!recruiterId) {
      console.log('🔍 AUTH DEBUG - All storage keys:', {
        user_id: authStorage.getItem('user_id'),
        recruiter_id: authStorage.getItem('recruiter_id'),
        backend_candidate_id: authStorage.getItem('backend_candidate_id'),
        candidate_id: authStorage.getItem('candidate_id'),
        user_data: (() => {
          try {
            const ud = authStorage.getItem('user_data')
            return ud ? JSON.parse(ud) : null
          } catch (e) {
            return null
          }
        })(),
        auth_token: authStorage.getItem('auth_token') ? 'PRESENT' : 'MISSING',
        all_keys: typeof sessionStorage !== 'undefined' ? Object.keys(sessionStorage) : []
      })
    }
    
    const baseFilter: CandidateFilters = {
      limit: FILTER_CONFIG.MAX_CANDIDATES,
      ...(recruiterId && { recruiter_id: recruiterId }), // Data isolation
      ...(selectedJobId && { job_id: selectedJobId }) // Job-specific filtering
    }
    
    switch(type) {
      case 'shortlisted':
        // ONLY status-based filtering - these are already manually shortlisted candidates
        // NO matching_score requirement 
        return {
          ...baseFilter,
          status: CANDIDATE_STATUS.SHORTLISTED,
          exclude_statuses: [CANDIDATE_STATUS.REJECTED, CANDIDATE_STATUS.WITHDRAWN, CANDIDATE_STATUS.HIRED]
        }
      
      case 'interview_scheduled':
        // Show candidates with interview_scheduled status (from job_applications)
        // Filter for interviews scheduled for today or future (not past)
        return {
          ...baseFilter,
          status: CANDIDATE_STATUS.INTERVIEW_SCHEDULED,
          interview_date_gte: getTodayDate()  // Only show current and future interviews
        }
      
      case 'application_received':
        // Candidates who applied to jobs but NOT yet shortlisted/interviewed/rejected
        // Shows applicants in early stages (pending, new, application_received)
        return {
          ...baseFilter,
          exclude_statuses: [
            CANDIDATE_STATUS.SHORTLISTED,
            CANDIDATE_STATUS.INTERVIEW_SCHEDULED,
            CANDIDATE_STATUS.REJECTED,
            CANDIDATE_STATUS.WITHDRAWN,
            CANDIDATE_STATUS.HIRED
          ]
        }
      
      case 'rejection_sent':
        // ONLY status-based filtering - purely rejected candidates
        return {
          ...baseFilter,
          status: CANDIDATE_STATUS.REJECTED,
          exclude_statuses: [CANDIDATE_STATUS.WITHDRAWN_BY_CANDIDATE]
        }
      
      default:
        return baseFilter
    }
  }

  // Load candidates with notification type filtering
  useEffect(() => {
    if (activeTab === 'notifications' && notificationType) {
      loadCandidates(notificationType)
    }
  }, [notificationType, activeTab])

  // Reload candidates when job selection changes
  useEffect(() => {
    if (activeTab === 'notifications' && notificationType) {
      loadCandidates(notificationType)
    }
  }, [selectedJobId])

  useEffect(() => {
    loadJobs()
  }, [])

  // Save active tab to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('batchOperationsActiveTab', activeTab)
  }, [activeTab])

  const loadCandidates = async (notificationTypeFilter?: string) => {
    try {
      setLoading(true)
      
      // Cancel any pending requests
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
      abortControllerRef.current = new AbortController()
      
      // Get filters based on notification type
      const filters = notificationTypeFilter 
        ? getFiltersForNotificationType(notificationTypeFilter)
        : { limit: 100 }
      
      console.log(`🔍 Loading candidates for ${notificationTypeFilter || 'all'}:`, {
        ...filters,
        selectedJobId: selectedJobId || 'none',
        recruiter_id_present: !!filters.recruiter_id
      })
      
      const candidatesData = await getAllCandidates(filters)
      
      console.log(`✅ Loaded ${candidatesData.length} candidates`)
      
      // Map backend candidate data to notification format with validation
      const mappedCandidates = candidatesData.map((c: any) => ({
        name: c.name || '',
        email: c.email || '',
        phone: c.phone || '',
        candidate_id: c.id || c.candidate_id,
        status: c.status,
        matching_score: c.matching_score,
        interview_date: c.interview_date
      }))
      
      setCandidates(mappedCandidates)
      setLastRefreshTime(new Date())
      
      // Show user-friendly message only for manual actions (not auto-load)
      if (mappedCandidates.length === 0) {
        const notificationLabel = notificationTypeFilter?.replace('_', ' ') || 'this type'
        toast(TOAST_MESSAGES.NO_CANDIDATES(notificationLabel), {
          icon: 'ℹ️',
          duration: UI_CONFIG.TOAST_DURATION.SHORT
        })
      }
      // Toast only shown for manual refresh, not auto-load
      
      // Clear validation errors when loading new candidates
      setValidationErrors(new Map())
    } catch (error: any) {
      console.error('Failed to load candidates:', error)
      
      if (error.name === 'AbortError') {
        console.log('Request was cancelled')
        return
      }
      
      if (error.isNetworkError) {
        toast.error(TOAST_MESSAGES.NETWORK_ERROR)
      } else {
        toast.error(TOAST_MESSAGES.LOADING_FAILED)
      }
      setCandidates([])
    } finally {
      setLoading(false)
      abortControllerRef.current = null
    }
  }

  const handleManualRefresh = () => {
    if (!notificationType) {
      toast.error('Please select a notification type first')
      return
    }
    loadCandidates(notificationType)
    toast.success('🔄 Candidate list refreshed')
  }

  const handlePreviewNotification = async () => {
    setLoadingPreview(true)
    try {
      const selectedJob = selectedJobId ? jobs.find(j => j.id === selectedJobId) : null
      const sampleData = {
        candidate_name: candidates[0]?.name || 'Candidate Name',
        job_title: selectedJob?.title || 'Job Title',
        job_id: selectedJob?.id || 'job_123',
        matching_score: '00',
        interview_date: 'YYYY-MM-DD',
        interview_time: 'HH:MM PM',
        interviewer: 'HR Team',
        application_id: 'APP_001'
      }
      
      const preview = await previewNotification(notificationType, sampleData)
      setPreviewData(preview)
      setShowPreviewModal(true)
    } catch (error) {
      console.error('Failed to load preview:', error)
      toast.error('Failed to load notification preview')
    } finally {
      setLoadingPreview(false)
    }
  }

  const loadJobs = async () => {
    try {
      const jobsData = await getRecruiterJobs()
      setJobs(jobsData)
      // Don't auto-select first job - keep it optional
      setSelectedJobId('')
    } catch (error) {
      console.error('Failed to load jobs:', error)
      toast.error('Failed to load jobs. You can still send notifications without job data.')
      setJobs([])
      setSelectedJobId('')
    }
  }

  const handleBulkNotifications = async () => {
    if (candidates.length === 0) {
      toast.error('Please add at least one candidate')
      return
    }

    // Validate all candidates
    if (!validateAllCandidates()) {
      toast.error(TOAST_MESSAGES.VALIDATION_ERROR, {
        duration: UI_CONFIG.TOAST_DURATION.MEDIUM
      })
      return
    }

    // Validate candidates have required fields with quality check
    const invalidCandidates = candidates.filter(c => {
      const hasValidEmail = c.email && c.email.trim() && c.email.includes('@') && 
                           !BLOCKED_TEST_VALUES.EMAILS.includes(c.email) && 
                           !BLOCKED_TEST_VALUES.EMAIL_PREFIXES.some(prefix => c.email.startsWith(prefix))
      const hasValidPhone = c.phone && c.phone.trim() && 
                           c.phone.replace(/[^0-9+]/g, '').length >= 10 && 
                           !BLOCKED_TEST_VALUES.PHONES.includes(c.phone)
      return !hasValidEmail && !hasValidPhone
    })
    
    if (invalidCandidates.length > 0) {
      toast.error(TOAST_MESSAGES.INVALID_CONTACTS(invalidCandidates.length), {
        duration: UI_CONFIG.TOAST_DURATION.LONG
      })
      return
    }

    // Confirmation for large batches
    if (candidates.length > FILTER_CONFIG.BULK_SEND_WARNING_THRESHOLD) {
      const confirm = window.confirm(TOAST_MESSAGES.BULK_SEND_CONFIRM(candidates.length))
      if (!confirm) return
    }

    if (sendingNotifications) {
      return
    }

    setSendingNotifications(true)
    try {
      // SMART LOGIC FOR APPLICATION RECEIVED:
      // - If NO job selected: Send grouped notifications (1 email per candidate with all their jobs)
      // - If JOB selected: Send individual notifications (1 email per candidate for that job)
      
      if (notificationType === 'application_received' && !selectedJobId) {
        // GROUPED NOTIFICATIONS: 1 email per candidate with ALL their jobs listed
        console.log('📧 Sending grouped notifications (Application Received - No Job Selected):', {
          candidatesCount: candidates.length,
          notificationType,
          mode: 'grouped-by-candidate'
        })

        const result = await sendGroupedNotifications({
          candidate_ids: candidates.map(c => c.candidate_id),
          notification_type: notificationType,
        })

        console.log('✅ Grouped notification response:', result)

        const successCount = result.success_count || 0
        const failedCount = result.failed_count || 0
        const totalEmails = result.total_emails_sent || 0

        if (successCount > 0) {
          toast.success(`Successfully sent ${totalEmails} email(s) to ${successCount} candidate(s). ${failedCount > 0 ? `${failedCount} failed.` : ''}`, {
            duration: UI_CONFIG.TOAST_DURATION.LONG
          })
        } else {
          toast.error(`Failed to send notifications. ${failedCount} failed.`)
        }
      } else {
        // STANDARD BULK NOTIFICATION: 1 email per candidate (for selected job or other notification types)
        // Get job title if a job is selected, otherwise use generic title
        const selectedJob = selectedJobId ? jobs.find(j => j.id === selectedJobId) : null
        const jobTitle = selectedJob?.title || 'Position'
        const jobIdForNotification = selectedJob?.id || null
        
        console.log('📧 Sending standard bulk notifications:', {
          candidatesCount: candidates.length,
          notificationType,
          jobTitle,
          jobId: jobIdForNotification,
          candidates: candidates.map(c => ({ name: c.name, email: c.email, phone: c.phone }))
        })

        const result = await sendBulkNotifications({
          candidates: candidates.map(c => ({
            candidate_name: c.name,
            candidate_email: c.email,
            candidate_phone: c.phone,
            candidate_id: c.candidate_id
          })),
          sequence_type: notificationType,
          job_title: jobTitle,
          job_id: jobIdForNotification,
          matching_score: 'High'
        })

        console.log('✅ Notification response:', result)

        const successCount = result.bulk_result?.success_count || 0
        const failedCount = result.bulk_result?.failed_count || 0
        const totalCount = result.bulk_result?.total_candidates || candidates.length

        if (successCount > 0) {
          toast.success(TOAST_MESSAGES.BULK_SEND_SUCCESS(successCount, totalCount, failedCount), {
            duration: UI_CONFIG.TOAST_DURATION.MEDIUM
          })
        } else if (failedCount > 0) {
          toast.error(TOAST_MESSAGES.BULK_SEND_FAILED(failedCount))
        } else {
          toast(TOAST_MESSAGES.BULK_SEND_PARTIAL, {
            icon: '⚠️',
            duration: UI_CONFIG.TOAST_DURATION.MEDIUM
          })
        }
      }
    } catch (error) {
      console.error('❌ Notification error:', error)
      const errorMsg = error instanceof Error ? error.message : 'Service may be offline'
      toast.error(TOAST_MESSAGES.BULK_SEND_ERROR(errorMsg))
    } finally {
      setSendingNotifications(false)
    }
  }

  const addCandidate = () => {
    setCandidates([...candidates, { name: '', email: '', phone: '' }])
  }

  const removeCandidate = (index: number) => {
    setCandidates(candidates.filter((_, i) => i !== index))
  }

  const updateCandidate = (index: number, field: string, value: string) => {
    const updated = [...candidates]
    updated[index] = { ...updated[index], [field]: value }
    setCandidates(updated)
    
    // Real-time validation for email and phone
    if (field === 'email' || field === 'phone') {
      validateCandidateField(index, field, value)
    }
  }
  
  const validateCandidateField = (index: number, field: 'email' | 'phone', value: string) => {
    setValidationErrors((prevErrors) => {
      const newErrors = new Map(prevErrors)
      const currentError = newErrors.get(index) || {}
      
      if (field === 'email') {
        const email = value.trim()
        if (!email) {
          currentError.email = VALIDATION_MESSAGES.EMAIL_REQUIRED
        } else if (!VALIDATION_PATTERNS.EMAIL.test(email)) {
          currentError.email = VALIDATION_MESSAGES.EMAIL_INVALID
        } else if (BLOCKED_TEST_VALUES.EMAILS.includes(email) || BLOCKED_TEST_VALUES.EMAIL_PREFIXES.some(p => email.startsWith(p))) {
          currentError.email = VALIDATION_MESSAGES.EMAIL_TEST
        } else {
          delete currentError.email
        }
      }
      
      if (field === 'phone') {
        const phone = value.trim()
        if (phone && !VALIDATION_PATTERNS.PHONE.test(phone)) {
          currentError.phone = VALIDATION_MESSAGES.PHONE_INVALID
        } else if (phone && BLOCKED_TEST_VALUES.PHONES.includes(phone)) {
          currentError.phone = VALIDATION_MESSAGES.PHONE_TEST
        } else {
          delete currentError.phone
        }
      }
      
      if (Object.keys(currentError).length === 0) {
        newErrors.delete(index)
      } else {
        newErrors.set(index, currentError)
      }
      
      return newErrors
    })
  }
  
  const validateAllCandidates = (): boolean => {
    let isValid = true
    const newErrors = new Map<number, { email?: string; phone?: string }>()
    
    candidates.forEach((candidate, index) => {
      const errors: { email?: string; phone?: string } = {}
      
      // Email validation
      const email = (candidate.email || '').trim()
      if (!email) {
        errors.email = VALIDATION_MESSAGES.EMAIL_REQUIRED
        isValid = false
      } else if (!VALIDATION_PATTERNS.EMAIL.test(email)) {
        errors.email = VALIDATION_MESSAGES.EMAIL_INVALID
        isValid = false
      } else if (BLOCKED_TEST_VALUES.EMAILS.includes(email) || BLOCKED_TEST_VALUES.EMAIL_PREFIXES.some(p => email.startsWith(p))) {
        errors.email = VALIDATION_MESSAGES.EMAIL_TEST
        isValid = false
      }
      
      // Phone validation (optional but must be valid if provided)
      const phone = (candidate.phone || '').trim()
      if (phone && !VALIDATION_PATTERNS.PHONE.test(phone)) {
        errors.phone = VALIDATION_MESSAGES.PHONE_INVALID
        isValid = false
      } else if (phone && BLOCKED_TEST_VALUES.PHONES.includes(phone)) {
        errors.phone = VALIDATION_MESSAGES.PHONE_TEST
        isValid = false
      }
      
      // At least one contact method required
      if (!email && !phone) {
        errors.email = VALIDATION_MESSAGES.CONTACT_REQUIRED
        errors.phone = VALIDATION_MESSAGES.CONTACT_REQUIRED
        isValid = false
      }
      
      if (Object.keys(errors).length > 0) {
        newErrors.set(index, errors)
      }
    })
    
    setValidationErrors(newErrors)
    return isValid
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-green-500/5 to-emerald-500/5 dark:from-green-500/10 dark:to-emerald-500/10 backdrop-blur-xl border border-green-300/20 dark:border-green-500/20">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">📁 Batch Operations</h1>
        <p className="text-gray-600 dark:text-gray-400">Perform bulk operations on candidates and jobs</p>
      </div>

      {/* Tabs */}
      <div className="card">
        <div className="border-b border-gray-200 dark:border-gray-700 mb-6">
          <div className="flex space-x-1">
            <button
              onClick={() => setActiveTab('upload')}
              className={`px-6 py-3 font-medium text-sm transition-colors ${
                activeTab === 'upload'
                  ? 'border-b-2 border-green-500 text-green-600 dark:text-green-400'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Bulk Upload
            </button>
            <button
              onClick={() => setActiveTab('notifications')}
              className={`px-6 py-3 font-medium text-sm transition-colors ${
                activeTab === 'notifications'
                  ? 'border-b-2 border-green-500 text-green-600 dark:text-green-400'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Bulk Notifications
            </button>
          </div>
        </div>

        {/* Bulk Upload Tab */}
        {activeTab === 'upload' && (
          <BulkCandidateUploadPanel
            jobSelectLabel="Select job id for bulk upload"
            showHeader={false}
            showDashboardLink={false}
          />
        )}

        {/* Bulk Notifications Tab */}
        {activeTab === 'notifications' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">📧 Bulk Notification System</h2>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Send automated notifications to multiple candidates
              </p>
            </div>

            {/* Notification Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Notification Type
              </label>
              <div className="flex gap-3">
                <select
                  value={notificationType}
                  onChange={(e) => setNotificationType(e.target.value)}
                  disabled={loading}
                  className="flex-1 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <option value="">Select Notification Type</option>
                  <option value="shortlisted">🎯 Shortlisted</option>
                  <option value="interview_scheduled">📅 Interview Scheduled</option>
                  <option value="application_received">✉️ Application Received</option>
                  <option value="rejection_sent">❌ Rejection Notification</option>
                </select>
                
                {/* Manual Refresh Button */}
                <button
                  onClick={handleManualRefresh}
                  disabled={loading}
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors flex items-center gap-2 whitespace-nowrap"
                  title="Refresh candidate list"
                >
                  <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  Refresh
                </button>
              </div>
              <div className="flex items-center justify-between mt-1">
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {notificationType 
                    ? 'Candidates are automatically filtered based on their status and notification type'
                    : 'Select a notification type to load candidates'}
                </p>
                {lastRefreshTime && notificationType && (
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Last refreshed: {lastRefreshTime.toLocaleTimeString()}
                  </p>
                )}
              </div>
            </div>

            {/* Job Selection (Optional) */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Job Name-ID (Optional)
              </label>
              {jobs.length === 0 ? (
                <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    No jobs available. You can still send notifications without job data.
                  </p>
                </div>
              ) : (
                <select
                  value={selectedJobId}
                  onChange={(e) => setSelectedJobId(e.target.value)}
                  disabled={!notificationType || loading}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500 focus:border-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <option value="">Select Job Title</option>
                  {jobs.map((job) => (
                    <option key={job.id} value={job.id}>
                      {job.title} – Job ID {job.id}
                    </option>
                  ))}
                </select>
              )}
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                {selectedJobId 
                  ? '✓ Showing candidates for the selected job only' 
                  : 'Leave empty to show all candidates, or select a job to filter candidates'}
              </p>
            </div>

            {/* Candidates List */}
            {notificationType && (
              <div>
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
                    {loading ? (
                      <span className="flex items-center gap-2">
                        <div className="animate-spin h-4 w-4 border-2 border-green-500 border-t-transparent rounded-full"></div>
                        Loading candidates...
                      </span>
                    ) : (
                      <>
                        Candidates for {notificationType.replace('_', ' ')} ({candidates.length})
                      </>
                    )}
                  </h3>
                <button
                  onClick={addCandidate}
                  disabled={loading}
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
                >
                  + Add Candidate
                </button>
              </div>

              {validationErrors.size > 0 && (
                <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                  <p className="text-sm font-medium text-red-800 dark:text-red-300 mb-2">
                    ⚠️ Validation Errors Found ({validationErrors.size} candidate{validationErrors.size > 1 ? 's' : ''})
                  </p>
                  <p className="text-xs text-red-600 dark:text-red-400">
                    Please fix the errors highlighted below before sending notifications.
                  </p>
                </div>
              )}

              {candidates.length === 0 && !loading ? (
                <div className="p-8 text-center bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-200 dark:border-gray-700">
                  <p className="text-gray-500 dark:text-gray-400 mb-2">
                    No candidates found for this notification type
                  </p>
                  <p className="text-sm text-gray-400 dark:text-gray-500 mb-4">
                    Try selecting a different notification type or manually add candidates using the button above
                  </p>
                  <div className="text-xs text-gray-400 dark:text-gray-500">
                    <p className="mb-1">💡 Tips:</p>
                    <ul className="list-disc list-inside text-left inline-block">
                      <li>Shortlisted: Candidates with status 'shortlisted'</li>
                      <li>Interview Scheduled: Candidates with future interview dates</li>
                      <li>Feedback Request: Interviewed candidates without feedback</li>
                      <li>Application Received: Recent applicants (last 7 days)</li>
                      <li>Rejection: Candidates with status 'rejected'</li>
                    </ul>
                  </div>
                </div>
              ) : (
                <div className="space-y-3">
                  {candidates.map((candidate, index) => {
                    const errors = validationErrors.get(index)
                    const hasError = errors && (errors.email || errors.phone)
                    
                    return (
                      <div 
                        key={index} 
                        className={`p-4 rounded-xl border transition-colors ${
                          hasError 
                            ? 'bg-red-50 dark:bg-red-900/10 border-red-300 dark:border-red-800' 
                            : 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700'
                        }`}
                      >
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                          <div className="flex flex-col">
                            <input
                              type="text"
                              placeholder="Name"
                              value={candidate.name}
                              onChange={(e) => updateCandidate(index, 'name', e.target.value)}
                              className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                            />
                            {candidate.status && (
                              <span className={`mt-1 px-2 py-0.5 text-xs rounded-full inline-block w-fit ${
                                UI_CONFIG.STATUS_COLORS[candidate.status] || UI_CONFIG.STATUS_COLORS.DEFAULT
                              }`}>
                                {candidate.status}
                              </span>
                            )}
                          </div>
                          <div className="flex flex-col">
                            <input
                              type="email"
                              placeholder="Email *"
                              value={candidate.email}
                              onChange={(e) => updateCandidate(index, 'email', e.target.value)}
                              className={`px-3 py-2 rounded-lg border ${
                                errors?.email 
                                  ? 'border-red-500 focus:ring-red-500' 
                                  : 'border-gray-300 dark:border-gray-600 focus:ring-green-500'
                              } bg-white dark:bg-gray-800 text-gray-900 dark:text-white`}
                            />
                            {errors?.email && (
                              <span className="mt-1 text-xs text-red-600 dark:text-red-400">
                                {errors.email}
                              </span>
                            )}
                          </div>
                          <div className="flex flex-col">
                            <input
                              type="tel"
                              placeholder="Phone"
                              value={candidate.phone}
                              onChange={(e) => updateCandidate(index, 'phone', e.target.value)}
                              className={`px-3 py-2 rounded-lg border ${
                                errors?.phone 
                                  ? 'border-red-500 focus:ring-red-500' 
                                  : 'border-gray-300 dark:border-gray-600 focus:ring-green-500'
                              } bg-white dark:bg-gray-800 text-gray-900 dark:text-white`}
                            />
                            {errors?.phone && (
                              <span className="mt-1 text-xs text-red-600 dark:text-red-400">
                                {errors.phone}
                              </span>
                            )}
                          </div>
                          
                          {/* Action Button */}
                          <div className="flex justify-end">
                            <button
                              onClick={() => removeCandidate(index)}
                              className="px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors"
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
              </div>
            )}

            {/* Action Buttons */}
            {notificationType && (
            <div className="flex gap-3">
              <button
                onClick={handlePreviewNotification}
                disabled={loadingPreview}
                className="flex-1 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
              >
                {loadingPreview ? (
                  <>
                    <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Loading...
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    Preview Message
                  </>
                )}
              </button>
              
              <button
                onClick={handleBulkNotifications}
                disabled={candidates.length === 0 || sendingNotifications || loading || !notificationType}
                className="flex-1 bg-purple-500 hover:bg-purple-600 disabled:bg-gray-400 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-semibold transition-colors flex items-center justify-center gap-2"
              >
                {sendingNotifications ? (
                  <>
                    <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Sending...
                  </>
                ) : (
                  '📧 Send Notifications'
                )}
              </button>
            </div>
            )}
          </div>
        )}
      </div>

      {/* Preview Modal */}
      {showPreviewModal && previewData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                📧 Notification Preview: {previewData.notification_type}
              </h3>
              <button
                onClick={() => setShowPreviewModal(false)}
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto flex-1">
              {/* Email Preview */}
              <div className="mb-6">
                <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  Email
                </h4>
                <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    <strong>Subject:</strong> {previewData.templates?.email?.subject}
                  </p>
                  <div className="mt-3 p-4 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700">
                    <div 
                      className="text-sm text-gray-700 dark:text-gray-300 prose dark:prose-invert max-w-none"
                      dangerouslySetInnerHTML={{ __html: previewData.templates?.email?.html_body || previewData.templates?.email?.body?.replace(/\n/g, '<br>') }}
                    />
                  </div>
                </div>
              </div>

              {/* WhatsApp Preview */}
              <div>
                <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
                  </svg>
                  WhatsApp
                </h4>
                <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                  <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm max-w-md">
                    <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-sans">
                      {previewData.templates?.whatsapp}
                    </pre>
                  </div>
                </div>
              </div>
            </div>

            <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex justify-end">
              <button
                onClick={() => setShowPreviewModal(false)}
                className="px-6 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg font-medium transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}