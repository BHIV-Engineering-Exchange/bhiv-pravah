import { useState, useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  createJob,
  getClientByConnectionId,
  confirmRecruiterConnection,
  getJobById,
  RECRUITER_LAST_CONNECTION_KEY,
  updateJob,
} from '../../services/api'
import { useRecruiterConnection } from '../../context/RecruiterConnectionContext'
import FormInput from '../../components/FormInput'
import SalaryRangeInput from '../../components/SalaryRangeInput'
import { useAuth } from '../../context/AuthContext'
import { authStorage } from '../../utils/authStorage'

const CONNECTION_ID_LENGTH = 24
const CONNECTION_ID_REGEX = /^[0-9a-fA-F]+$/

function normalizeExperienceLevel(value?: string | null): 'Entry' | 'Mid' | 'Senior' | 'Lead' {
  const raw = (value || '').trim().toLowerCase()
  if (!raw) return 'Entry'

  if (raw === 'entry' || raw.includes('fresher') || raw.includes('junior') || raw.includes('0-1')) return 'Entry'
  if (raw === 'mid' || raw.includes('mid') || raw.includes('intermediate') || raw.includes('1-3') || raw.includes('2-4')) return 'Mid'
  if (raw === 'senior' || raw.includes('senior') || raw.includes('5-8') || raw.includes('4-6')) return 'Senior'
  if (raw === 'lead' || raw.includes('lead') || raw.includes('principal') || raw.includes('8+')) return 'Lead'

  return 'Entry'
}

function loadLastConnection(): { connectionId: string; companyName: string } | null {
  try {
    const raw = typeof localStorage !== 'undefined' ? localStorage.getItem(RECRUITER_LAST_CONNECTION_KEY) : null
    if (!raw) return null
    const parsed = JSON.parse(raw) as { connectionId?: string; companyName?: string }
    if (parsed?.connectionId && parsed.connectionId.length === CONNECTION_ID_LENGTH) return { connectionId: parsed.connectionId, companyName: parsed.companyName ?? '' }
    return null
  } catch {
    return null
  }
}

function saveLastConnection(connectionId: string, companyName: string) {
  try {
    localStorage.setItem(RECRUITER_LAST_CONNECTION_KEY, JSON.stringify({ connectionId, companyName }))
  } catch {
    // ignore
  }
}

function clearLastConnection() {
  try {
    localStorage.removeItem(RECRUITER_LAST_CONNECTION_KEY)
  } catch {
    // ignore
  }
}

export default function JobCreation() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { status: connectionStatus, setConnection: setRecruiterConnection, clearConnection: clearRecruiterConnection } = useRecruiterConnection()
  const { user, userName: authUserName } = useAuth()
  const [loading, setLoading] = useState(false)
  const [loadingJob, setLoadingJob] = useState(false)
  const [recruiterName, setRecruiterName] = useState<string>('')
  const [connectionIdError, setConnectionIdError] = useState<string | null>(null)
  const [linkedCompany, setLinkedCompany] = useState<string | null>(null)
  const [showConfirmConnection, setShowConfirmConnection] = useState(false)
  const [isConnectionIdLocked, setIsConnectionIdLocked] = useState(false)
  const editJobId = searchParams.get('edit')
  const isEditMode = Boolean(editJobId)
  const shouldSyncConnectionContext = !isEditMode
  const connectionInputRef = useRef<HTMLInputElement>(null)
  const [formData, setFormData] = useState({
    title: '',
    department: 'Engineering',
    location: '',
    experience_level: 'Entry',
    employment_type: 'Full-time',
    salary_range: '',
    connection_id: '',
    description: '',
    requirements: '',
  })
  const [initialJobPayload, setInitialJobPayload] = useState<string | null>(null)

  // Load recruiter name on component mount
  useEffect(() => {
    const fetchRecruiterName = () => {
      try {
        // First try to get from auth context (current user)
        if (user?.name) {
          setRecruiterName(user.name);
          return;
        }
        
        // Try to get from auth storage
        const userData = authStorage.getItem('user_data');
        if (userData) {
          const parsed = JSON.parse(userData);
          if (parsed.name) {
            setRecruiterName(parsed.name);
            return;
          }
        }
        
        // Fallback to auth context userName
        if (authUserName) {
          setRecruiterName(authUserName);
          return;
        }
        
        // Final fallback to user email
        if (user?.email) {
          setRecruiterName(user.email);
          return;
        }
        
        const userEmail = authStorage.getItem('user_email');
        if (userEmail) {
          setRecruiterName(userEmail);
          return;
        }
        
        // Ultimate fallback
        setRecruiterName('Recruiter');
      } catch (error) {
        console.error('Error fetching recruiter name:', error);
        // Fallback to user email or default
        const userEmail = user?.email || authStorage.getItem('user_email') || 'Recruiter';
        setRecruiterName(userEmail);
      }
    };

    fetchRecruiterName();
  }, [user, authUserName]);

  // Load persisted connection_id (locked from previous session)
  useEffect(() => {
    if (isEditMode) return
    const last = loadLastConnection()
    if (last) {
      setFormData(prev => ({ ...prev, connection_id: last.connectionId }))
      setLinkedCompany(last.companyName || null)
      setIsConnectionIdLocked(true)
    }
  }, [])

  useEffect(() => {
    if (!editJobId) return

    let isMounted = true

    const loadJobForEdit = async () => {
      setLoadingJob(true)
      try {
        const job = await getJobById(editJobId)
        if (!isMounted) return

        const salaryRange = job.salary_min != null || job.salary_max != null
          ? `${job.salary_min ?? ''}${job.salary_min != null || job.salary_max != null ? ' - ' : ''}${job.salary_max ?? ''}`.trim()
          : ''

        const nextFormData = {
          title: job.title || '',
          department: job.department || 'Engineering',
          location: job.location || '',
          experience_level: normalizeExperienceLevel(job.experience_level || job.experience_required),
          employment_type: job.employment_type || job.job_type || 'Full-time',
          salary_range: salaryRange === '-' ? '' : salaryRange,
          connection_id: job.connection_id || '',
          description: job.description || '',
          requirements: job.requirements || (Array.isArray(job.skills_required) ? job.skills_required.join(', ') : job.skills_required || ''),
        }

        setFormData(nextFormData)
        setLinkedCompany(job.company || null)
        setConnectionIdError(null)
        setShowConfirmConnection(false)
        setIsConnectionIdLocked(Boolean(job.connection_id))
        if (shouldSyncConnectionContext && job.connection_id && job.company) {
          setRecruiterConnection(job.connection_id, job.company)
        }

        const basePayload = buildJobPayload(nextFormData)
        setInitialJobPayload(serializeJobPayload(basePayload))
      } catch (error) {
        console.error('Error loading job for edit:', error)
        toast.error('Failed to load job details for editing')
        navigate('/recruiter')
      } finally {
        if (isMounted) {
          setLoadingJob(false)
        }
      }
    }

    loadJobForEdit()

    return () => {
      isMounted = false
    }
  }, [editJobId, navigate, setRecruiterConnection, shouldSyncConnectionContext])

  const buildJobPayload = (source = formData): Record<string, any> => {
    const jobData: Record<string, any> = {
      title: source.title.trim(),
      department: source.department.trim(),
      location: source.location.trim(),
      experience_level: source.experience_level.trim(),
      employment_type: source.employment_type.trim(),
      description: source.description.trim(),
      requirements: source.requirements.trim(),
      connection_id: source.connection_id.trim(),
    }

    if (source.salary_range) {
      const [minRaw, maxRaw] = source.salary_range.split('-')
      const min = minRaw ? parseInt(minRaw.trim(), 10) : NaN
      const max = maxRaw ? parseInt(maxRaw.trim(), 10) : NaN
      if (!Number.isNaN(min)) jobData.salary_min = min
      if (!Number.isNaN(max)) jobData.salary_max = max
    }

    return jobData
  }

  const serializeJobPayload = (payload: Record<string, any>) => JSON.stringify({
    title: payload.title || '',
    department: payload.department || '',
    location: payload.location || '',
    experience_level: payload.experience_level || '',
    employment_type: payload.employment_type || '',
    description: payload.description || '',
    requirements: payload.requirements || '',
    connection_id: payload.connection_id || '',
    salary_min: payload.salary_min ?? null,
    salary_max: payload.salary_max ?? null,
  })

  // When health check or SSE detects disconnection, unlock form and clear connection
  useEffect(() => {
    if (isEditMode) return
    // Unlock form when connection status becomes 'none' or 'invalid' while form was locked
    if ((connectionStatus === 'invalid' || connectionStatus === 'none') && isConnectionIdLocked) {
      console.log('Connection lost - unlocking job creation form')
      toast.error('Connection to client lost. Please reconnect.')
      setFormData(prev => ({ ...prev, connection_id: '' }))
      setLinkedCompany(null)
      setConnectionIdError(null)
      setShowConfirmConnection(false)
      setIsConnectionIdLocked(false)
      clearLastConnection()
      clearRecruiterConnection()
    }
  }, [connectionStatus, isConnectionIdLocked, clearRecruiterConnection, isEditMode])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    if (name === 'connection_id') {
      setConnectionIdError(null)
      setLinkedCompany(null)
    }
  }

  const validateConnectionIdFormat = (id: string): string | null => {
    const trimmed = id.trim()
    if (!trimmed) return 'Connection ID is required'
    if (trimmed.length !== CONNECTION_ID_LENGTH) return `Connection ID must be exactly ${CONNECTION_ID_LENGTH} characters`
    if (!CONNECTION_ID_REGEX.test(trimmed)) return 'Connection ID must contain only letters and numbers (hexadecimal)'
    return null
  }

  // Verify only: show company name, do NOT lock. User confirms by pressing Enter.
  const verifyConnectionId = async (id: string): Promise<boolean> => {
    const formatError = validateConnectionIdFormat(id)
    if (formatError) {
      setConnectionIdError(formatError)
      setLinkedCompany(null)
      toast.error(formatError)
      return false
    }
    setConnectionIdError(null)
    try {
      const client = await getClientByConnectionId(id)
      if (client) {
        setLinkedCompany(client.company_name)
        return true
      } else {
        setLinkedCompany(null)
        setConnectionIdError('Invalid Connection ID. Please ask your client for the correct ID from their dashboard.')
        toast.error('Invalid Connection ID. Please ask your client for the correct ID from their dashboard.')
        return false
      }
    } catch {
      setLinkedCompany(null)
      setConnectionIdError('Could not verify Connection ID. Please check your connection and try again.')
      toast.error('Could not verify Connection ID. Please check your connection and try again.')
      return false
    }
  }

  const handleConnectionIdBlur = async () => {
    const id = formData.connection_id.trim()
    if (!id || isConnectionIdLocked || showConfirmConnection) return
    await verifyConnectionId(id)
  }

  // Show confirmation when user presses Enter after seeing company name
  const handleConnectionIdKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== 'Enter') return
    if (isConnectionIdLocked || showConfirmConnection) return
    e.preventDefault()
    if (linkedCompany) {
      setShowConfirmConnection(true)
    } else {
      verifyConnectionId(formData.connection_id.trim()).then((ok) => ok && setShowConfirmConnection(true))
    }
  }

  // Lock and persist only when user clicks OK in confirmation; establish connection on backend so client sees activated only now
  const confirmAndLockConnectionId = async () => {
    const id = formData.connection_id.trim()
    if (!id || !linkedCompany) return
    setLoading(true)
    try {
      await confirmRecruiterConnection(id)
      clearLastConnection()
      saveLastConnection(id, linkedCompany)
      if (shouldSyncConnectionContext) {
        setRecruiterConnection(id, linkedCompany)
      }
      setIsConnectionIdLocked(true)
      setShowConfirmConnection(false)
      toast.success('Connection ID confirmed')
    } catch (err: unknown) {
      const msg = err && typeof err === 'object' && 'response' in err && typeof (err as { response?: { data?: { detail?: string } } }).response?.data?.detail === 'string'
        ? (err as { response: { data: { detail: string } } }).response.data.detail
        : 'Failed to confirm connection. Please try again.'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  // Revert to input, clear connection ID and confirmation (from confirmation UI)
  const cancelConfirmAndClear = () => {
    setFormData(prev => ({ ...prev, connection_id: '' }))
    setLinkedCompany(null)
    setConnectionIdError(null)
    setShowConfirmConnection(false)
    clearLastConnection()
    if (shouldSyncConnectionContext) {
      clearRecruiterConnection()
    }
    setTimeout(() => connectionInputRef.current?.focus(), 0)
  }

  // Edit from locked state: return to input, clear and remove persisted value
  const handleUnlockConnectionId = () => {
    setFormData(prev => ({ ...prev, connection_id: '' }))
    setLinkedCompany(null)
    setConnectionIdError(null)
    setShowConfirmConnection(false)
    setIsConnectionIdLocked(false)
    clearLastConnection()
    if (shouldSyncConnectionContext) {
      clearRecruiterConnection()
    }
    setTimeout(() => connectionInputRef.current?.focus(), 0)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.title || !formData.description || !formData.requirements) {
      toast.error('Please fill in all required fields')
      return
    }

    const id = formData.connection_id.trim()
    if (!id) {
      toast.error('Connection ID is required. Ask your client for their Connection ID from their dashboard.')
      setConnectionIdError('Connection ID is required')
      return
    }
    const formatError = validateConnectionIdFormat(id)
    if (formatError) {
      toast.error(formatError)
      setConnectionIdError(formatError)
      return
    }
    if (!isConnectionIdLocked || !linkedCompany) {
      toast.error('Please confirm the Connection ID: enter the ID, blur to see the company name, press Enter, then click OK.')
      return
    }

    setLoading(true)
    setConnectionIdError(null)

    try {
      const jobData = buildJobPayload({ ...formData, connection_id: id })

      if (isEditMode && initialJobPayload && serializeJobPayload(jobData) === initialJobPayload) {
        toast.error('Job already exists. No changes detected.')
        return
      }

      if (isEditMode && editJobId) {
        await updateJob(editJobId, jobData)
        toast.success('Job updated successfully!')
      } else {
        await createJob(jobData)
        toast.success('Job created successfully!')
        // Keep connection_id and linked company for next job; only reset other fields
        setFormData(prev => ({
          title: '',
          department: 'Engineering',
          location: '',
          experience_level: 'Entry',
          employment_type: 'Full-time',
          salary_range: '',
          connection_id: prev.connection_id,
          description: '',
          requirements: '',
        }))
      }
      setTimeout(() => navigate('/recruiter'), 1200)
    } catch (error: any) {
      const msg = error?.response?.data?.detail || error?.message
      const isInvalidConnection = typeof msg === 'string' && (msg.includes('Connection ID') || msg.includes('connection_id'))
      if (isInvalidConnection) {
        setConnectionIdError('Invalid Connection ID. Please ask your client for the correct ID from their dashboard.')
        toast.error('Invalid Connection ID. Please ask your client for the correct ID from their dashboard.')
      } else if (typeof msg === 'string' && msg.includes('Job already exists')) {
        toast.error(msg)
      } else {
        toast.error(isEditMode ? 'Failed to update job' : 'Failed to create job')
      }
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div className="mb-6 sm:mb-8 p-4 sm:p-6 rounded-2xl bg-gradient-to-r from-green-500/5 to-emerald-500/5 dark:from-green-500/10 dark:to-emerald-500/10 backdrop-blur-xl border border-green-300/20 dark:border-green-500/20">
        <h1 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 dark:text-white mb-2">{isEditMode ? 'Edit Job Position' : 'Create New Job Position'}</h1>
        <p className="text-sm sm:text-base text-gray-500 dark:text-gray-400">{isEditMode ? 'Update the details of your existing job posting' : 'Fill in the details to post a new job opening'}</p>
        <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
          <p className="text-sm text-green-800 dark:text-green-300">
            Posting as: <span className="font-semibold">{recruiterName || 'Loading...'}</span>
          </p>
        </div>
      </div>

      {loadingJob ? (
        <div className="card max-w-4xl">
          <p className="text-gray-600 dark:text-gray-400">Loading job details...</p>
        </div>
      ) : (

      <form onSubmit={handleSubmit} className="card max-w-4xl">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6">
          <FormInput
            label="Job Title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="e.g., Senior Software Engineer"
            required
          />

          <FormInput
            label="Department"
            name="department"
            value={formData.department}
            onChange={handleChange}
            required
            options={[
              { value: 'Engineering', label: 'Engineering' },
              { value: 'Marketing', label: 'Marketing' },
              { value: 'Sales', label: 'Sales' },
              { value: 'HR', label: 'HR' },
              { value: 'Operations', label: 'Operations' },
            ]}
          />

          <FormInput
            label="Location"
            name="location"
            value={formData.location}
            onChange={handleChange}
            placeholder="e.g., Remote, New York, London"
            required
          />

          <FormInput
            label="Experience Level"
            name="experience_level"
            value={formData.experience_level}
            onChange={handleChange}
            required
            options={[
              { value: 'Entry', label: 'Entry' },
              { value: 'Mid', label: 'Mid' },
              { value: 'Senior', label: 'Senior' },
              { value: 'Lead', label: 'Lead' },
            ]}
          />

          <FormInput
            label="Employment Type"
            name="employment_type"
            value={formData.employment_type}
            onChange={handleChange}
            required
            options={[
              { value: 'Full-time', label: 'Full-time' },
              { value: 'Part-time', label: 'Part-time' },
              { value: 'Contract', label: 'Contract' },
              { value: 'Intern', label: 'Intern' },
            ]}
          />

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Salary Range (Optional)
            </label>
            <SalaryRangeInput
              name="salary_range"
              value={formData.salary_range}
              onChange={(value) => setFormData(prev => ({ ...prev, salary_range: value }))}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500 focus:border-transparent"
              placeholder="e.g., 80000 - 120000"
              required={false}
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Connection ID <span className="text-red-500">*</span>
            </label>
            {isConnectionIdLocked && formData.connection_id ? (
              <div>
                <div className="flex items-center gap-2 w-full h-11 sm:h-12 rounded-lg sm:rounded-xl bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm border-2 border-gray-200 dark:border-gray-700 px-3 sm:px-4">
                  <code className="font-mono text-sm sm:text-base font-medium text-gray-900 dark:text-white truncate flex-1 min-w-0" title={formData.connection_id}>{formData.connection_id}</code>
                  <button
                    type="button"
                    onClick={handleUnlockConnectionId}
                    className="inline-flex items-center justify-center shrink-0 rounded-lg h-8 sm:h-9 px-3 sm:px-4 text-xs sm:text-sm font-bold text-white bg-emerald-600 hover:bg-emerald-700 transition-colors"
                  >
                    Edit
                  </button>
                </div>
                {linkedCompany && connectionStatus === 'connected' && (
                  <div className="mt-2 flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400">
                    <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse"></span>
                    <span>Connected to {linkedCompany} • Health check active</span>
                  </div>
                )}
                {connectionStatus === 'none' && (
                  <div className="mt-2 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                    <span className="w-2 h-2 bg-gray-400 rounded-full"></span>
                    <span>Connection monitoring paused</span>
                  </div>
                )}
              </div>
            ) : showConfirmConnection && linkedCompany ? (
              <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800">
                <p className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                  Connect to <strong>{linkedCompany}</strong>
                </p>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => void confirmAndLockConnectionId()}
                    disabled={loading}
                    className="px-4 py-2 text-sm font-medium rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? 'Confirming…' : 'OK'}
                  </button>
                  <button
                    type="button"
                    onClick={cancelConfirmAndClear}
                    className="px-4 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                  >
                    Edit
                  </button>
                </div>
              </div>
            ) : (
              <>
                <input
                  ref={connectionInputRef}
                  type="text"
                  name="connection_id"
                  value={formData.connection_id}
                  onChange={handleChange}
                  onBlur={handleConnectionIdBlur}
                  onKeyDown={handleConnectionIdKeyDown}
                  placeholder="Paste your Connection_id"
                  className={`input-field w-full font-mono ${connectionIdError ? 'border-red-500 dark:border-red-500' : ''}`}
                  maxLength={CONNECTION_ID_LENGTH}
                  required
                />
                {connectionIdError && (
                  <p className="mt-1 text-sm text-red-600 dark:text-red-400" role="alert">
                    {connectionIdError}
                  </p>
                )}
                {linkedCompany && !connectionIdError && !showConfirmConnection && (
                  <p className="mt-1 text-sm text-green-600 dark:text-green-400">
                    Linked to: <strong>{linkedCompany}</strong> — Press Enter to confirm
                  </p>
                )}
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Ask your client for their Connection ID from the Client Dashboard (Recruiter connection section). Press enter for validation.
                </p>
              </>
            )}
          </div>
        </div>

        <div className="mt-6">
          <FormInput
            label="Job Description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            placeholder="Describe the role, responsibilities, and requirements..."
            textarea
            rows={6}
            required
          />

          <FormInput
            label="Key Requirements"
            name="requirements"
            value={formData.requirements}
            onChange={handleChange}
            placeholder="List the essential skills, experience, and qualifications..."
            textarea
            rows={6}
            required
          />
        </div>

        <div className="mt-8 flex space-x-4">
          <button
            type="submit"
            disabled={loading || loadingJob}
            className="btn-primary"
          >
            {loading ? (isEditMode ? 'Updating...' : 'Creating...') : (isEditMode ? 'Update Job' : 'Create Job')}
          </button>
          <button
            type="button"
            onClick={() => navigate('/recruiter')}
            className="btn-secondary"
          >
            Cancel
          </button>
        </div>
      </form>
      )}
    </div>
  )
}
