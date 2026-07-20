import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { createJob, getClientProfile, getJobById, updateJob } from '../../services/api'
import { toast } from 'react-hot-toast'
import { authStorage } from '../../utils/authStorage'
import SalaryRangeInput from '../../components/SalaryRangeInput'

function normalizeExperienceLevel(value?: string | null): 'Entry' | 'Mid' | 'Senior' | 'Lead' {
  const raw = (value || '').trim().toLowerCase()
  if (!raw) return 'Entry'

  if (raw === 'entry' || raw.includes('fresher') || raw.includes('junior') || raw.includes('0-1')) return 'Entry'
  if (raw === 'mid' || raw.includes('mid') || raw.includes('intermediate') || raw.includes('1-3') || raw.includes('2-4')) return 'Mid'
  if (raw === 'senior' || raw.includes('senior') || raw.includes('5-8') || raw.includes('4-6')) return 'Senior'
  if (raw === 'lead' || raw.includes('lead') || raw.includes('principal') || raw.includes('8+')) return 'Lead'

  return 'Entry'
}

export default function ClientJobPosting() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const editJobId = searchParams.get('edit')
  const isEditMode = Boolean(editJobId)
  const [loading, setLoading] = useState(false)
  const [loadingJob, setLoadingJob] = useState(false)
  const [clientCompany, setClientCompany] = useState<string>('')
  const [initialJobPayload, setInitialJobPayload] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    title: '',
    department: 'Engineering',
    location: '',
    experience_level: 'Entry',
    employment_type: 'Full-time',
    salary_range: '',
    description: '',
    required_skills: '',
  })

  const departments = ['Engineering', 'Marketing', 'Sales', 'HR', 'Operations', 'Finance']
  const experienceLevels = ['Entry', 'Mid', 'Senior', 'Lead']
  const employmentTypes = ['Full-time', 'Part-time', 'Contract', 'Intern']

  // Fetch client profile on component mount
  useEffect(() => {
    const fetchClientProfile = async () => {
      try {
        // First try to get from auth storage (faster)
        const userData = authStorage.getItem('user_data');
        if (userData) {
          const parsed = JSON.parse(userData);
          if (parsed.company) {
            setClientCompany(parsed.company);
            return;
          }
        }
        
        // Fallback to API call
        const profile = await getClientProfile();
        if (profile) {
          setClientCompany(profile.company_name);
        } else {
          // Fallback to auth storage name
          const userName = authStorage.getItem('user_name') || 'Client';
          setClientCompany(userName);
        }
      } catch (error) {
        console.error('Error fetching client profile:', error);
        // Use fallback values
        const userName = authStorage.getItem('user_name') || 'Client';
        setClientCompany(userName);
      }
    };

    fetchClientProfile();
  }, []);

  const buildJobPayload = (source = formData): Record<string, any> => {
    const jobData: Record<string, any> = {
      title: source.title.trim(),
      department: source.department.trim(),
      location: source.location.trim(),
      experience_level: source.experience_level.toLowerCase(),
      requirements: source.required_skills.trim() || source.description.trim(),
      description: source.description.trim(),
      employment_type: source.employment_type.trim(),
      status: 'active',
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
    salary_min: payload.salary_min ?? null,
    salary_max: payload.salary_max ?? null,
    status: payload.status || 'active',
  })

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
          description: job.description || '',
          required_skills: job.requirements || (Array.isArray(job.skills_required) ? job.skills_required.join(', ') : job.skills_required || ''),
        }

        setFormData(nextFormData)
        const basePayload = buildJobPayload(nextFormData)
        setInitialJobPayload(serializeJobPayload(basePayload))
      } catch (error: any) {
        console.error('Error loading client job for edit:', error)
        const msg = error?.response?.data?.detail || error?.message || ''
        if (typeof msg === 'string' && (msg.includes('own jobs') || msg.includes('Access denied') || msg.includes('403'))) {
          toast.error('You can only edit jobs posted by your own client account.')
        } else {
          toast.error('Failed to load job details for editing')
        }
        navigate('/client/dashboard')
      } finally {
        if (isMounted) setLoadingJob(false)
      }
    }

    loadJobForEdit()
    return () => {
      isMounted = false
    }
  }, [editJobId, navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const jobData = buildJobPayload()

      if (isEditMode && editJobId && initialJobPayload && serializeJobPayload(jobData) === initialJobPayload) {
        toast.error('Job already exists. No changes detected.')
        return
      }

      if (isEditMode && editJobId) {
        await updateJob(editJobId, jobData)
        toast.success('Job updated successfully!')
      } else {
        await createJob(jobData)
        toast.success('Job posted successfully!')
      }
      
      // Reset form
      if (!isEditMode) {
        setFormData({
          title: '',
          department: 'Engineering',
          location: '',
          experience_level: 'Entry',
          employment_type: 'Full-time',
          salary_range: '',
          description: '',
          required_skills: '',
        })
      }
      
      // Refresh jobs list in background
      setTimeout(() => {
        window.dispatchEvent(new Event('jobs-updated'))
      }, 1000)
      setTimeout(() => {
        navigate('/client/dashboard')
      }, 1200)
    } catch (error: any) {
      console.error('Error posting job:', error)
      const msg = error?.response?.data?.detail || error?.response?.data?.error || error?.message || ''
      if (typeof msg === 'string' && msg.includes('No changes detected')) {
        toast.error('No changes detected.')
      } else if (typeof msg === 'string' && msg.includes('own jobs')) {
        toast.error('You can only update jobs posted by your own client account.')
      } else if (typeof msg === 'string' && msg.includes('already exists')) {
        toast.error(msg)
      } else {
        toast.error(isEditMode ? 'Failed to update job' : 'Failed to post job')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-500/5 to-indigo-500/5 dark:from-blue-500/10 dark:to-indigo-500/10 backdrop-blur-xl border border-blue-300/20 dark:border-blue-500/20 mb-8">
        <h1 className="page-title">{isEditMode ? 'Edit Job' : 'Post New Job'}</h1>
        <p className="page-subtitle">
          {isEditMode ? 'Update your existing job opening details' : 'Create and publish new job openings for your organization'}
        </p>
        <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
          <p className="text-sm text-blue-800 dark:text-blue-300">
            Posting as: <span className="font-semibold">{clientCompany || 'Loading...'}</span>
          </p>
        </div>
      </div>

      {/* Job Posting Form */}
      <div className="card">
        {loadingJob ? (
          <p className="text-gray-600 dark:text-gray-400">Loading job details...</p>
        ) : (
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Job Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Job Title
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="e.g., Senior Python Developer"
              />
            </div>

            {/* Department */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Department
              </label>
              <select
                name="department"
                value={formData.department}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                {departments.map((dept) => (
                  <option key={dept} value={dept}>{dept}</option>
                ))}
              </select>
            </div>

            {/* Location */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Location
              </label>
              <input
                type="text"
                name="location"
                value={formData.location}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="e.g., Remote, New York, San Francisco"
              />
            </div>

            {/* Experience Level */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Experience Level
              </label>
              <select
                name="experience_level"
                value={formData.experience_level}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                {experienceLevels.map((level) => (
                  <option key={level} value={level}>{level}</option>
                ))}
              </select>
            </div>

            {/* Employment Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Type
              </label>
              <select
                name="employment_type"
                value={formData.employment_type}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              >
                {employmentTypes.map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>

            {/* Salary Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Salary Range (Optional)
              </label>
              <SalaryRangeInput
                name="salary_range"
                value={formData.salary_range}
                onChange={(value) => setFormData(prev => ({ ...prev, salary_range: value }))}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                placeholder="e.g., 80000 - 120000"
                required={false}
              />
            </div>
          </div>

          {/* Job Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Job Description
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              required
              rows={6}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Describe the role, responsibilities, and requirements..."
            />
          </div>

          {/* Required Skills */}
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
              Required Skills
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </label>
            <textarea
              name="required_skills"
              value={formData.required_skills}
              onChange={handleChange}
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Describe the skills and qualifications needed for this role..."
            />
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Enter skills in natural language - no need for comma separation
            </p>
          </div>

          {/* Preview Section */}
          {formData.title && formData.description && (
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Job Preview</h3>
              <div className="space-y-2 text-gray-700 dark:text-gray-300">
                <p className="font-semibold">{formData.title} - {formData.department} | {formData.location} | {formData.employment_type}</p>
                <p className="text-sm">Experience: {formData.experience_level} Level</p>
                {formData.salary_range && (
                  <p className="text-sm">Salary: {formData.salary_range}</p>
                )}
              </div>
            </div>
          )}

          {/* Submit Button */}
          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={() => navigate('/client/dashboard')}
              className="px-6 py-3 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 font-semibold rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-all duration-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all duration-200 shadow-lg shadow-purple-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  {isEditMode ? 'Updating...' : 'Posting...'}
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isEditMode ? "M5 13l4 4L19 7" : "M12 4v16m8-8H4"} />
                  </svg>
                  {isEditMode ? 'Update Job' : 'Post Job'}
                </>
              )}
            </button>
          </div>
        </form>
        )}
      </div>
    </div>
  )
}

