import { useState, useEffect, useRef } from 'react'
import toast from 'react-hot-toast'
import {
  scheduleInterview,
  getInterviews,
  getRecruiterJobs,
  searchCandidates,
  type Interview,
  type CandidateProfile,
  type Job
} from '../../services/api'
import Loading from '../../components/Loading'

const INTERVIEW_TYPES = [
  { value: 'on-site', label: 'On-site' },
  { value: 'remote', label: 'Remote' },
  { value: 'video_meet', label: 'Video meet' },
  { value: 'voice_call', label: 'Voice call' }
] as const
type InterviewTypeValue = typeof INTERVIEW_TYPES[number]['value']

/** Indian phone: +91XXXXXXXXXX, 91XXXXXXXXXX, 0XXXXXXXXXX, XXXXXXXXXX (10 digits, first digit 6-9). Same as backend gateway main.py. */
const INDIAN_PHONE_REGEX = /^(\+91|91)?[6-9]\d{9}$/

function normalizePhoneForValidation(phone: string): string {
  const stripped = phone.replace(/[\s\-\.()]/g, '').trim()
  if (stripped.startsWith('0') && stripped.length === 11) return stripped.slice(1)
  return stripped
}

function validateIndianPhone(phone: string): { valid: boolean; message?: string; normalized?: string } {
  if (!phone || !phone.trim()) return { valid: false, message: 'Phone number is required' }
  const normalized = normalizePhoneForValidation(phone)
  if (normalized.length < 10) return { valid: false, message: 'Enter a valid 10-digit Indian mobile number' }
  const valid = INDIAN_PHONE_REGEX.test(normalized)
  if (!valid) return { valid: false, message: 'Invalid format. Use e.g. +91XXXXXXXXXX, 0XXXXXXXXXX, or XXXXXXXXXX (10 digits, 6-9)' }
  const digitsOnly = normalized.replace(/\D/g, '')
  const canonical = digitsOnly.length === 10 ? `+91${digitsOnly}` : digitsOnly.startsWith('91') ? `+${digitsOnly}` : `+91${digitsOnly}`
  return { valid: true, normalized: canonical }
}

function formatPhoneDisplay(value: string): string {
  const n = normalizePhoneForValidation(value)
  if (n.length === 10 && /^[6-9]/.test(n)) return `+91 ${n.slice(0, 5)} ${n.slice(5)}`
  return value
}

export default function InterviewScheduling() {
  const [activeTab, setActiveTab] = useState<'schedule' | 'view'>('schedule')
  const [loading, setLoading] = useState(false)
  const [interviews, setInterviews] = useState<Interview[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  const [candidates, setCandidates] = useState<CandidateProfile[]>([])
  const [candidatesLoading, setCandidatesLoading] = useState(false)
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([])
  const [candidateDropdownOpen, setCandidateDropdownOpen] = useState(false)
  const candidateDropdownRef = useRef<HTMLDivElement>(null)
  const [duplicateWarning, setDuplicateWarning] = useState<string | null>(null)

  const [formData, setFormData] = useState({
    job_id: '',
    interview_date: '',
    interview_time: '',
    interview_type: '' as InterviewTypeValue | '',
    interviewer: '',
    meeting_link: '',
    meeting_address: '',
    meeting_phone: '',
    notes: ''
  })

  useEffect(() => {
    if (activeTab === 'view') {
      loadInterviews()
      const interval = setInterval(loadInterviews, 30000)
      return () => clearInterval(interval)
    }
    loadJobs()
    loadCandidates()
  }, [activeTab])

  const loadInterviews = async () => {
    try {
      setLoading(true)
      const data = await getInterviews()
      setInterviews(data)
    } catch (error) {
      console.error('Failed to load interviews:', error)
      toast.error('Failed to load interviews')
    } finally {
      setLoading(false)
    }
  }

  const loadJobs = async () => {
    try {
      const jobsData = await getRecruiterJobs()
      setJobs(jobsData)
      if (jobsData.length > 0 && !formData.job_id) {
        setFormData(prev => ({ ...prev, job_id: jobsData[0].id?.toString?.() ?? String(jobsData[0].id) }))
      }
    } catch (error) {
      console.error('Failed to load jobs:', error)
      toast.error('Failed to load recruiter jobs')
    }
  }

  const loadCandidates = async () => {
    try {
      setCandidatesLoading(true)
      const result = await searchCandidates('', {})
      setCandidates(Array.isArray(result.candidates) ? result.candidates : [])
    } catch (error) {
      console.error('Failed to load candidates:', error)
      setCandidates([])
    } finally {
      setCandidatesLoading(false)
    }
  }

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (candidateDropdownRef.current && !candidateDropdownRef.current.contains(e.target as Node)) {
        setCandidateDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Clear duplicate warning when user changes form data or selection
  useEffect(() => {
    setDuplicateWarning(null)
  }, [formData.job_id, formData.interview_date, formData.interview_time, formData.interview_type, formData.interviewer, formData.meeting_link, formData.meeting_address, formData.meeting_phone, formData.notes, selectedCandidateIds])

  const toggleCandidate = (id: string) => {
    setSelectedCandidateIds(prev =>
      prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
    )
  }

  const getValidationErrors = (): string[] => {
    const err: string[] = []
    if (selectedCandidateIds.length === 0) err.push('Select at least one candidate')
    if (!formData.job_id) err.push('Select a job')
    if (!formData.interview_date) err.push('Select interview date')
    if (!formData.interview_time) err.push('Select interview time')
    if (!formData.interview_type) err.push('Select interview type')
    if (!formData.interviewer?.trim()) err.push('Enter interviewer name')
    const type = formData.interview_type
    const hasAddress = !!formData.meeting_address?.trim()
    const hasPhone = !!formData.meeting_phone?.trim()
    const hasLink = !!formData.meeting_link?.trim()

    if (type === 'on-site' || type === 'remote') {
      if (!hasAddress && !hasPhone) err.push('Enter address and/or phone number for Meet Type')
      else if (hasPhone) {
        const phoneCheck = validateIndianPhone(formData.meeting_phone!)
        if (!phoneCheck.valid) err.push(phoneCheck.message || 'Invalid phone number for Meet Type')
      }
    } else if (type === 'video_meet') {
      if (!hasLink && !hasPhone) err.push('Enter meeting link and/or phone number for Meet Type')
      else if (hasPhone) {
        const phoneCheck = validateIndianPhone(formData.meeting_phone!)
        if (!phoneCheck.valid) err.push(phoneCheck.message || 'Invalid phone number for Meet Type')
      }
    } else if (type === 'voice_call') {
      if (!hasPhone) err.push('Enter phone number for Meet Type')
      else {
        const phoneCheck = validateIndianPhone(formData.meeting_phone!)
        if (!phoneCheck.valid) err.push(phoneCheck.message || 'Invalid phone number for Meet Type')
      }
    }
    return err
  }

  const validationErrors = getValidationErrors()
  const canSubmit = validationErrors.length === 0

  const getNormalizedPhone = (): string | undefined => {
    const p = formData.meeting_phone?.trim()
    if (!p) return undefined
    const result = validateIndianPhone(p)
    return result.valid ? (result.normalized ?? p) : undefined
  }

  /** Normalize date/time to YYYY-MM-DDTHH:mm for duplicate comparison. */
  const normalizeDateTime = (dateStr: string): string => {
    if (!dateStr) return ''
    try {
      const d = new Date(dateStr)
      const y = d.getFullYear()
      const m = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      const h = String(d.getHours()).padStart(2, '0')
      const min = String(d.getMinutes()).padStart(2, '0')
      return `${y}-${m}-${day}T${h}:${min}`
    } catch {
      return dateStr.slice(0, 16)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return
    const interviewDateTime = `${formData.interview_date}T${formData.interview_time}:00`
    const normalizedPhone = getNormalizedPhone()
    setLoading(true)
    setDuplicateWarning(null)
    try {
      const existingList = await getInterviews()
      const proposedDateTime = normalizeDateTime(interviewDateTime)
      const proposedType = (formData.interview_type || '').trim()
      const proposedInterviewer = (formData.interviewer || '').trim()
      const proposedLink = (formData.meeting_link || '').trim()
      const proposedAddress = (formData.meeting_address || '').trim()
      const proposedPhoneNorm = (normalizedPhone || '').replace(/\D/g, '')
      const proposedNotes = (formData.notes || '').trim()

      for (const candidateId of selectedCandidateIds) {
        const isDup = existingList.some((ex) => {
          if (String(ex.candidate_id) !== String(candidateId)) return false
          if (String(ex.job_id) !== String(formData.job_id)) return false
          const exDateTime = normalizeDateTime(ex.scheduled_date || ex.interview_date || '')
          if (exDateTime !== proposedDateTime) return false
          if ((ex.interview_type || '').trim() !== proposedType) return false
          if ((ex.interviewer || '').trim() !== proposedInterviewer) return false
          if ((ex.meeting_link || '').trim() !== proposedLink) return false
          if ((ex.meeting_address || '').trim() !== proposedAddress) return false
          const exPhoneNorm = (ex.meeting_phone || '').replace(/\D/g, '')
          if (exPhoneNorm !== proposedPhoneNorm) return false
          if ((ex.notes || '').trim() !== proposedNotes) return false
          return true
        })
        if (isDup) {
          setDuplicateWarning(
            'This interview is identical to a previously scheduled one. Scheduling has been prevented. Please change the date/time, interview type, meeting details, interviewer, or notes and try again.'
          )
          setLoading(false)
          return
        }
      }

      let scheduled = 0
      for (const candidateId of selectedCandidateIds) {
        await scheduleInterview({
          candidate_id: candidateId,
          job_id: formData.job_id,
          interview_date: interviewDateTime,
          interviewer: formData.interviewer.trim(),
          interview_type: formData.interview_type || undefined,
          meeting_link: formData.meeting_link?.trim() || undefined,
          meeting_address: formData.meeting_address?.trim() || undefined,
          meeting_phone: normalizedPhone,
          notes: formData.notes?.trim() || undefined,
          status: 'scheduled'
        })
        scheduled++
      }
      setDuplicateWarning(null)
      toast.success(`Interview scheduled for ${scheduled} candidate(s)`)
      setSelectedCandidateIds([])
      setFormData({
        job_id: jobs.length > 0 ? (jobs[0].id?.toString?.() ?? String(jobs[0].id)) : '',
        interview_date: '',
        interview_time: '',
        interview_type: '',
        interviewer: '',
        meeting_link: '',
        meeting_address: '',
        meeting_phone: '',
        notes: ''
      })
      setActiveTab('view')
      setTimeout(loadInterviews, 500)
    } catch (error: unknown) {
      const msg = error && typeof error === 'object' && 'response' in error
        ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
        : null
      toast.error(msg || 'Failed to schedule interview')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
    } catch {
      return dateStr
    }
  }

  const formatTime = (dateStr: string) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    } catch {
      return dateStr
    }
  }

  const meetTypeDisabled = !formData.interview_type
  const phoneValidation = formData.meeting_phone?.trim()
    ? validateIndianPhone(formData.meeting_phone)
    : { valid: true as const, message: undefined }
  const showPhoneError = !!formData.meeting_phone?.trim() && !phoneValidation.valid
  const selectedCandidatesLabel = selectedCandidateIds.length === 0
    ? 'Select candidates'
    : `${selectedCandidateIds.length} candidate(s) selected`

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="p-6 rounded-2xl bg-gradient-to-r from-green-500/5 to-emerald-500/5 dark:from-green-500/10 dark:to-emerald-500/10 backdrop-blur-xl border border-green-300/20 dark:border-green-500/20">
        <h1 className="page-title">Interview Management System</h1>
        <p className="page-subtitle">Schedule, track, and manage candidate interviews</p>
      </div>

      <div className="card">
        <div className="flex border-b border-gray-200 dark:border-gray-700 mb-6">
          <button
            onClick={() => setActiveTab('schedule')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'schedule'
                ? 'border-b-2 border-green-500 text-green-600 dark:text-green-400'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            Schedule Interview
          </button>
          <button
            onClick={() => setActiveTab('view')}
            className={`px-6 py-3 font-medium transition-colors ${
              activeTab === 'view'
                ? 'border-b-2 border-green-500 text-green-600 dark:text-green-400'
                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            View Interviews
          </button>
        </div>

        {activeTab === 'schedule' && (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Candidate multi-select */}
            <div ref={candidateDropdownRef} className="relative">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Candidates *
              </label>
              <button
                type="button"
                onClick={() => setCandidateDropdownOpen(!candidateDropdownOpen)}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-left flex items-center justify-between text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
              >
                <span className={selectedCandidateIds.length === 0 ? 'text-gray-500' : ''}>
                  {candidatesLoading ? 'Loading applicants...' : selectedCandidatesLabel}
                </span>
                <svg className={`w-5 h-5 transition-transform ${candidateDropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              {candidateDropdownOpen && (
                <div className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                  {candidates.length === 0 && !candidatesLoading ? (
                    <div className="p-4 text-sm text-gray-500 dark:text-gray-400">No applicants for your jobs yet</div>
                  ) : (
                    <div className="p-2 space-y-1">
                      {candidates.map((c) => (
                        <label
                          key={c.id}
                          className="flex items-center gap-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700/50 p-2 rounded"
                        >
                          <input
                            type="checkbox"
                            checked={selectedCandidateIds.includes(c.id)}
                            onChange={() => toggleCandidate(c.id)}
                            className="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                          />
                          <span className="text-sm text-gray-700 dark:text-gray-300">
                            {(c.name || 'Unknown')} - {c.email || ''}
                          </span>
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Job ID */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Job ID *</label>
              <select
                value={formData.job_id}
                onChange={(e) => setFormData({ ...formData, job_id: e.target.value })}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
              >
                {jobs.length === 0 ? (
                  <option value="">No jobs posted</option>
                ) : (
                  jobs.map((job) => (
                    <option key={job.id} value={job.id?.toString?.() ?? String(job.id)}>
                      {job.title ?? 'Untitled'} - {job.id}
                    </option>
                  ))
                )}
              </select>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Interview Date *</label>
                <input
                  type="date"
                  value={formData.interview_date}
                  onChange={(e) => setFormData({ ...formData, interview_date: e.target.value })}
                  min={new Date().toISOString().split('T')[0]}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Interview Time *</label>
                <input
                  type="time"
                  value={formData.interview_time}
                  onChange={(e) => setFormData({ ...formData, interview_time: e.target.value })}
                  className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Interview Type *</label>
              <select
                value={formData.interview_type}
                onChange={(e) => setFormData({
                  ...formData,
                  interview_type: e.target.value as InterviewTypeValue,
                  meeting_link: '',
                  meeting_address: '',
                  meeting_phone: ''
                })}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
              >
                <option value="">Select type</option>
                {INTERVIEW_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Meet Type {formData.interview_type ? '*' : ''}
              </label>
              <div className={`rounded-lg border p-4 ${meetTypeDisabled ? 'bg-gray-100 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700 opacity-75 pointer-events-none' : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800'}`}>
                {!formData.interview_type && (
                  <p className="text-sm text-gray-500 dark:text-gray-400">Select an interview type above to enter meet details.</p>
                )}
                {(formData.interview_type === 'on-site' || formData.interview_type === 'remote') && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Address</label>
                      <input
                        type="text"
                        value={formData.meeting_address}
                        onChange={(e) => setFormData({ ...formData, meeting_address: e.target.value })}
                        placeholder="Address or location"
                        className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Phone number</label>
                      <input
                        type="tel"
                        value={formData.meeting_phone}
                        onChange={(e) => setFormData({ ...formData, meeting_phone: e.target.value })}
                        placeholder="Contact number"
                        className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      />
                    </div>
                  </div>
                )}
                {formData.interview_type === 'video_meet' && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Meeting link (or phone)</label>
                      <input
                        type="url"
                        value={formData.meeting_link}
                        onChange={(e) => setFormData({ ...formData, meeting_link: e.target.value })}
                        placeholder="https://meet.google.com/..."
                        className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Phone number (optional if link provided)</label>
                      <input
                        type="tel"
                        value={formData.meeting_phone}
                        onChange={(e) => setFormData({ ...formData, meeting_phone: e.target.value })}
                        placeholder="Backup phone"
                        className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                      />
                    </div>
                  </div>
                )}
                {formData.interview_type === 'voice_call' && (
                  <div>
                    <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">Phone number *</label>
                    <input
                      type="tel"
                      value={formData.meeting_phone}
                      onChange={(e) => setFormData({ ...formData, meeting_phone: e.target.value })}
                      onBlur={(e) => {
                        const v = e.target.value.trim()
                        if (v && validateIndianPhone(v).valid) setFormData(prev => ({ ...prev, meeting_phone: formatPhoneDisplay(v) }))
                      }}
                      placeholder="e.g. +91 98765 43210, 09876543210, 9876543210"
                      className={`w-full px-3 py-2 rounded-lg border bg-white dark:bg-gray-800 text-gray-900 dark:text-white ${showPhoneError ? 'border-red-500 dark:border-red-500' : 'border-gray-300 dark:border-gray-600'}`}
                    />
                    {showPhoneError && <p className="mt-1 text-xs text-red-600 dark:text-red-400">{phoneValidation.message}</p>}
                  </div>
                )}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Interviewer Name *</label>
              <input
                type="text"
                value={formData.interviewer}
                onChange={(e) => setFormData({ ...formData, interviewer: e.target.value })}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Notes (Optional)</label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                rows={4}
                placeholder="Additional notes about the interview..."
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
              />
            </div>

            {duplicateWarning && (
              <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 flex items-start gap-3">
                <svg className="w-6 h-6 flex-shrink-0 text-red-500 dark:text-red-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-red-800 dark:text-red-200">Duplicate interview detected</p>
                  <p className="text-sm text-red-700 dark:text-red-300 mt-1">{duplicateWarning}</p>
                  <p className="text-xs text-red-600 dark:text-red-400 mt-2">Your form data has been preserved. Update any field above and try again.</p>
                </div>
                <button
                  type="button"
                  onClick={() => setDuplicateWarning(null)}
                  className="flex-shrink-0 text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-200 text-sm font-medium"
                >
                  Dismiss
                </button>
              </div>
            )}

            {validationErrors.length > 0 && (
              <div className="p-4 rounded-lg bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
                <p className="text-sm font-medium text-amber-800 dark:text-amber-200 mb-1">Please fix the following to schedule:</p>
                <ul className="list-disc list-inside text-sm text-amber-700 dark:text-amber-300">
                  {validationErrors.map((msg, i) => (
                    <li key={i}>{msg}</li>
                  ))}
                </ul>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !canSubmit}
              className="w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-6 py-3 rounded-xl font-semibold transition-all duration-300 flex items-center justify-center gap-2 shadow-lg shadow-green-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Scheduling...
                </>
              ) : (
                <>Schedule Interview</>
              )}
            </button>
          </form>
        )}

        {activeTab === 'view' && (
          <div>
            {loading ? (
              <Loading message="Loading interviews..." />
            ) : interviews.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-gray-500 dark:text-gray-400 text-lg">No interviews scheduled yet</p>
                <button
                  onClick={() => setActiveTab('schedule')}
                  className="mt-4 text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 font-medium"
                >
                  Schedule your first interview →
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {interviews.map((interview) => (
                  <div
                    key={interview.id}
                    className="p-6 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-200 dark:border-gray-700"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                          {interview.candidate_name || interview.candidate_id || 'Candidate'}
                        </h3>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                          <div>
                            <p className="text-gray-500 dark:text-gray-400">Date</p>
                            <p className="font-semibold text-gray-900 dark:text-white">{formatDate(interview.scheduled_date)}</p>
                          </div>
                          <div>
                            <p className="text-gray-500 dark:text-gray-400">Time</p>
                            <p className="font-semibold text-gray-900 dark:text-white">{interview.scheduled_time || formatTime(interview.scheduled_date)}</p>
                          </div>
                          <div>
                            <p className="text-gray-500 dark:text-gray-400">Job</p>
                            <p className="font-semibold text-gray-900 dark:text-white">{interview.job_title || `Job ID ${interview.job_id}`}</p>
                          </div>
                          <div>
                            <p className="text-gray-500 dark:text-gray-400">Type</p>
                            <p className="font-semibold text-gray-900 dark:text-white capitalize">{interview.interview_type?.replace('_', ' ') || '—'}</p>
                          </div>
                          <div>
                            <p className="text-gray-500 dark:text-gray-400">Status</p>
                            <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                              interview.status === 'scheduled' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                              interview.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                              'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400'
                            }`}>
                              {interview.status}
                            </span>
                          </div>
                        </div>
                        {interview.meeting_link && (
                          <div className="mt-4">
                            <a href={interview.meeting_link} target="_blank" rel="noopener noreferrer" className="text-green-600 dark:text-green-400 hover:underline text-sm">
                              Join Meeting →
                            </a>
                          </div>
                        )}
                        {interview.notes && (
                          <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                            <p className="text-sm text-blue-700 dark:text-blue-400">{interview.notes}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
