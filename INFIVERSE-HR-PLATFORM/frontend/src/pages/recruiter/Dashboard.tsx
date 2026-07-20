import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import {
  deleteJob,
  getRecruiterJobs,
  getRecruiterStats,
  getAllInterviews,
  getAllOffers,
  getRecruiterApplicants,
  setRecruiterRequiredDocuments,
  getRecruiterApplicantDocumentBlob,
  type Job,
  type RecruiterStats,
  type ApplicationDocumentType,
  type ClientApplicantRecord,
} from '../../services/api'
import StatsCard from '../../components/StatsCard'
import Table from '../../components/Table'
import Loading from '../../components/Loading'

// Component to display jobs with applicant counts; stats come from parent (single source, no duplicate fetches)
function JobTableWithStats({
  jobs,
  jobStats,
  loading,
  onViewDetails,
}: {
  jobs: Job[]
  jobStats: Record<string, { applicants: number; shortlisted: number }>
  loading: boolean
  onViewDetails: (job: Job) => void
}) {
  return (
    <Table
      columns={['Job Title', 'Department', 'Location', 'Type', 'Applicants', 'Shortlisted', 'Actions']}
      data={jobs}
      renderRow={(job) => {
        const stats = jobStats[job.id] || { applicants: 0, shortlisted: 0 }
        const isLoading = loading
        return (
          <>
            <td className="font-semibold text-gray-900 dark:text-white">{job.title}</td>
            <td className="text-gray-600 dark:text-gray-400">{job.department}</td>
            <td className="text-gray-600 dark:text-gray-400">{job.location}</td>
            <td>
              <span className={`badge ${
                job.job_type === 'Remote' || job.job_type === 'remote' ? 'badge-success' :
                job.job_type === 'On-site' || job.job_type === 'on-site' ? 'badge-info' :
                'badge-purple'
              }`}>
                {job.job_type || job.employment_type || 'Full-time'}
              </span>
            </td>
            <td>
              {isLoading ? (
                <span className="text-gray-400 text-sm">Loading...</span>
              ) : (
                <span className="font-semibold text-gray-900 dark:text-white">{stats.applicants}</span>
              )}
            </td>
            <td>
              {isLoading ? (
                <span className="text-gray-400 text-sm">Loading...</span>
              ) : (
                <span className="font-semibold text-emerald-600 dark:text-emerald-400">{stats.shortlisted}</span>
              )}
            </td>
            <td>
              <button
                type="button"
                onClick={() => onViewDetails(job)}
                className="inline-flex items-center gap-1 text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 font-semibold transition-colors"
              >
                View Details
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </td>
          </>
        )
      }}
    />
  )
}

export default function RecruiterDashboard() {
  const navigate = useNavigate()
  const [jobs, setJobs] = useState<Job[]>([])
  const [jobStats, setJobStats] = useState<Record<string, { applicants: number; shortlisted: number }>>({})
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)
  const [jobPendingDelete, setJobPendingDelete] = useState<Job | null>(null)
  const [deletingJobId, setDeletingJobId] = useState<string | null>(null)
  const [stats, setStats] = useState<RecruiterStats>({
    total_jobs: 0,
    total_applicants: 0,
    shortlisted: 0,
    interviewed: 0,
    offers_sent: 0,
    hired: 0
  })
  const [loading, setLoading] = useState(true)
  const loadingRef = useRef(false)
  const [activeTab, setActiveTab] = useState<'jobs' | 'applicants'>(() => {
    const saved = localStorage.getItem('recruiterDashboardActiveTab')
    return saved === 'applicants' ? 'applicants' : 'jobs'
  })
  const [applicants, setApplicants] = useState<ClientApplicantRecord[]>([])
  const [loadingApplicants, setLoadingApplicants] = useState(false)
  const [selectedDocumentsByApp, setSelectedDocumentsByApp] = useState<Record<string, ApplicationDocumentType[]>>({})
  const [submittingDocumentsForApp, setSubmittingDocumentsForApp] = useState<string | null>(null)
  const [openingDocumentKey, setOpeningDocumentKey] = useState<string | null>(null)

  useEffect(() => {
    loadDashboardData()
    // Auto-refresh every 60s; skip if previous load still in progress to avoid overlapping
    // match requests and agent overload during extended run.
    const interval = setInterval(() => {
      if (!loadingRef.current) {
        void loadDashboardData()
      }
      if (activeTab === 'applicants') {
        void loadApplicants(true)
      }
    }, 60000)
    return () => clearInterval(interval)
  }, [activeTab])

  useEffect(() => {
    localStorage.setItem('recruiterDashboardActiveTab', activeTab)
  }, [activeTab])

  const loadDashboardData = async () => {
    if (loadingRef.current) return
    loadingRef.current = true
    setLoading(true)
    let hasError = false
    try {
      // Single batch: jobs (with per-job applicants/shortlisted), stats, interviews, offers – no N+1
      const [jobsData, statsData, interviewsData, offersData] = await Promise.all([
        getRecruiterJobs().catch((err) => {
          if (import.meta.env.DEV) console.warn('getRecruiterJobs failed:', err)
          hasError = true
          return [] as Job[]
        }),
        getRecruiterStats().catch((err) => {
          if (import.meta.env.DEV) console.warn('getRecruiterStats failed:', err)
          hasError = true
          return null
        }),
        getAllInterviews().catch((err) => {
          if (import.meta.env.DEV) console.warn('getAllInterviews failed:', err)
          hasError = true
          return []
        }),
        getAllOffers().catch((err) => {
          if (import.meta.env.DEV) console.warn('getAllOffers failed:', err)
          hasError = true
          return []
        })
      ])

      setJobs(jobsData)

      // Per-job stats from jobs response (backend includes applicants/shortlisted); no extra API calls
      const perJob: Record<string, { applicants: number; shortlisted: number }> = {}
      for (const job of jobsData) {
        perJob[job.id] = {
          applicants: job.applicants ?? 0,
          shortlisted: job.shortlisted ?? 0
        }
      }
      setJobStats(perJob)

      const jobIds = new Set(jobsData.map((j: Job) => j.id))
      const myInterviews = interviewsData.filter((i: { job_id?: string }) => jobIds.has(i.job_id ?? ''))
      const myOffers = offersData.filter((o: { job_id?: string }) => jobIds.has(o.job_id ?? ''))
      if (statsData && (statsData.total_jobs > 0 || statsData.total_applicants > 0)) {
        setStats(statsData)
      } else {
        const totalApplicants = jobsData.reduce((sum, j) => sum + (j.applicants ?? 0), 0)
        const totalShortlisted = jobsData.reduce((sum, j) => sum + (j.shortlisted ?? 0), 0)
        setStats({
          total_jobs: jobsData.length,
          total_applicants: totalApplicants,
          shortlisted: totalShortlisted,
          interviewed: myInterviews.filter((i: { status?: string }) => i.status === 'scheduled' || i.status === 'completed').length,
          offers_sent: myOffers.length,
          hired: myOffers.filter((o: { status?: string }) => o.status === 'accepted').length
        })
      }
      if (hasError) toast.error('Some data could not be loaded. Try refreshing.')
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      toast.error('Failed to connect to backend. Check your connection and try again.')
    } finally {
      loadingRef.current = false
      setLoading(false)
    }
  }

  const loadApplicants = async (silent = false) => {
    try {
      if (!silent) setLoadingApplicants(true)
      const rows = await getRecruiterApplicants()
      setApplicants(Array.isArray(rows) ? rows : [])
      setSelectedDocumentsByApp((prev) => {
        const next: Record<string, ApplicationDocumentType[]> = {}
        for (const app of rows || []) {
          const existing = prev[app.application_id]
          next[app.application_id] = existing && existing.length > 0
            ? existing
            : (app.required_documents || [])
        }
        return next
      })
    } catch (error) {
      console.error('Failed to load recruiter applicants:', error)
      setApplicants([])
    } finally {
      if (!silent) setLoadingApplicants(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'applicants') {
      void loadApplicants()
    }
  }, [activeTab])

  useEffect(() => {
    const onNotificationsUpdated = (event: Event) => {
      const customEvent = event as CustomEvent<{ role?: string }>
      if (customEvent.detail?.role !== 'recruiter') return
      if (activeTab === 'applicants') {
        void loadApplicants(true)
      }
      void loadDashboardData()
    }
    window.addEventListener('portal-notifications-updated', onNotificationsUpdated)
    return () => window.removeEventListener('portal-notifications-updated', onNotificationsUpdated)
  }, [activeTab])

  const toggleDocumentSelection = (applicationId: string, docType: ApplicationDocumentType) => {
    setSelectedDocumentsByApp((prev) => {
      const current = prev[applicationId] || []
      const exists = current.includes(docType)
      const next = exists
        ? current.filter((d) => d !== docType)
        : [...current, docType]
      return { ...prev, [applicationId]: next }
    })
  }

  const handleSubmitRequiredDocuments = async (applicationId: string) => {
    const selected = selectedDocumentsByApp[applicationId] || []
    if (selected.length === 0) {
      toast.error('Select at least one document: CV/Resume or NDA')
      return
    }
    try {
      setSubmittingDocumentsForApp(applicationId)
      await setRecruiterRequiredDocuments(applicationId, selected)
      toast.success('Document request sent to candidate')
      await loadApplicants()
    } catch (error: any) {
      const msg = error?.response?.data?.detail || error?.message || 'Failed to send document request'
      toast.error(msg)
    } finally {
      setSubmittingDocumentsForApp(null)
    }
  }

  const parseIsoMillis = (value?: string | null): number => {
    if (!value) return 0
    const t = new Date(value).getTime()
    return Number.isFinite(t) ? t : 0
  }

  const isDocRequestLocked = (applicant: ClientApplicantRecord, docType: ApplicationDocumentType): boolean => {
    const required = Array.isArray(applicant.required_documents) && applicant.required_documents.includes(docType)
    if (!required) return false
    const requestedAt = parseIsoMillis(applicant.required_documents_updated_at || null)
    const uploadedAt = parseIsoMillis(applicant.documents_uploaded?.[docType]?.uploaded_at || null)
    if (requestedAt <= 0) {
      return uploadedAt === 0
    }
    return uploadedAt < requestedAt || uploadedAt === 0
  }

  const documentBadge = (pending: boolean) => (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold ${
        pending
          ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
          : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
      }`}
    >
      {pending ? 'Pending' : 'Submitted'}
    </span>
  )

  const openDocument = async (applicant: ClientApplicantRecord, docType: ApplicationDocumentType, download: boolean) => {
    try {
      const key = `${applicant.application_id}:${docType}:${download ? 'download' : 'view'}`
      setOpeningDocumentKey(key)
      const { blob, filename } = await getRecruiterApplicantDocumentBlob(applicant.application_id, docType, download)
      const url = URL.createObjectURL(blob)
      if (download) {
        const a = document.createElement('a')
        a.href = url
        a.download = filename || `${docType}.pdf`
        document.body.appendChild(a)
        a.click()
        a.remove()
      } else {
        window.open(url, '_blank', 'noopener,noreferrer')
      }
      setTimeout(() => URL.revokeObjectURL(url), 10_000)
    } catch (error: any) {
      const msg = error?.response?.data?.detail || error?.message || 'Unable to fetch document'
      toast.error(msg)
    } finally {
      setOpeningDocumentKey(null)
    }
  }

  // Use stats from API when available; fallback to aggregating from jobs (applicants/shortlisted per job)
  const totalApplicants = stats.total_applicants ?? jobs.reduce((sum, job: Job) => sum + (job.applicants ?? 0), 0)
  const totalShortlisted = stats.shortlisted ?? jobs.reduce((sum, job: Job) => sum + (job.shortlisted ?? 0), 0)
  const totalInterviewed = stats.interviewed ?? 0
  const totalOffers = stats.offers_sent ?? 0
  const totalJobs = stats.total_jobs ?? jobs.length

  const handleEditJob = (job: Job) => {
    setSelectedJob(null)
    navigate(`/recruiter/create-job?edit=${encodeURIComponent(job.id)}`)
  }

  const executeDeleteJob = async (job: Job) => {
    setDeletingJobId(job.id)
    try {
      await deleteJob(job.id)
      toast.success('Job deleted successfully')
      setSelectedJob(null)
      await loadDashboardData()
    } catch (error: any) {
      const msg = error?.response?.data?.detail || error?.message || 'Failed to delete job'
      toast.error(msg)
    } finally {
      setDeletingJobId(null)
    }
  }

  const handleDeleteJob = (job: Job) => {
    setJobPendingDelete(job)
  }

  const handleConfirmDeleteJob = async () => {
    if (!jobPendingDelete) return
    await executeDeleteJob(jobPendingDelete)
    setJobPendingDelete(null)
  }

  const handleCancelDeleteJob = () => {
    if (deletingJobId) return
    setJobPendingDelete(null)
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 p-4 sm:p-6 rounded-2xl bg-gradient-to-r from-green-500/5 to-emerald-500/5 dark:from-green-500/10 dark:to-emerald-500/10 backdrop-blur-xl border border-green-300/20 dark:border-green-500/20">
        <div>
          <h1 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 dark:text-white mb-2">Recruiter Console</h1>
          <p className="text-sm sm:text-base text-gray-500 dark:text-gray-400">Manage jobs and track applicants efficiently</p>
        </div>
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 w-full sm:w-auto">
          <button
            onClick={loadDashboardData}
            disabled={loading}
            className="px-4 py-2.5 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-xl font-semibold transition-all duration-300 flex items-center justify-center gap-2 text-sm sm:text-base"
            title="Refresh data"
          >
            <svg className={`w-4 h-4 sm:w-5 sm:h-5 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>Refresh</span>
          </button>
          <Link to="/recruiter/create-job" className="bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-4 sm:px-6 py-2.5 rounded-xl font-semibold transition-all duration-300 flex items-center justify-center gap-2 shadow-lg shadow-green-500/20 text-sm sm:text-base">
            <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>Create New Job</span>
          </Link>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        <StatsCard
          title="Total Jobs"
          value={totalJobs}
          color="blue"
          trend={{ value: jobs.length, label: 'active jobs' }}
          icon={
            <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          }
        />
        <StatsCard
          title="Total Applicants"
          value={totalApplicants}
          color="green"
          trend={{ value: totalShortlisted, label: 'shortlisted' }}
          icon={
            <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          }
        />
        <StatsCard
          title="Shortlisted"
          value={totalShortlisted}
          color="emerald"
          trend={{ value: totalInterviewed, label: 'interviewed' }}
          icon={
            <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatsCard
          title="Interviewed"
          value={totalInterviewed}
          color="amber"
          trend={{ value: totalOffers, label: 'offers sent' }}
          icon={
            <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          }
        />
        <StatsCard
          title="Offers Sent"
          value={totalOffers}
          color="purple"
          trend={{ value: stats.hired || 0, label: 'hired' }}
          icon={
            <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
        />
      </div>

      {/* Jobs / Applicants Tabs */}
      <div className="card">
        <div className="border-b border-gray-200 dark:border-gray-700 mb-6">
          <div className="flex space-x-1 overflow-x-auto">
            <button
              onClick={() => setActiveTab('jobs')}
              className={`px-4 sm:px-6 py-3 font-medium text-sm transition-colors whitespace-nowrap ${
                activeTab === 'jobs'
                  ? 'border-b-2 border-emerald-500 text-emerald-600 dark:text-emerald-400'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Active Job Openings
            </button>
            <button
              onClick={() => setActiveTab('applicants')}
              className={`px-4 sm:px-6 py-3 font-medium text-sm transition-colors whitespace-nowrap ${
                activeTab === 'applicants'
                  ? 'border-b-2 border-emerald-500 text-emerald-600 dark:text-emerald-400'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              View Applicants
            </button>
          </div>
        </div>

        {activeTab === 'jobs' && (
          <>
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4 sm:mb-6">
              <div>
                <h2 className="text-lg sm:text-xl font-heading font-bold text-gray-900 dark:text-white mb-1">Active Job Openings</h2>
                <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">{jobs.length} jobs currently active</p>
              </div>
              <div className="flex gap-2 sm:gap-3 w-full sm:w-auto">
                <Link to="/recruiter/automation" className="btn-outline text-xs sm:text-sm h-9 sm:h-10 flex-1 sm:flex-none flex items-center justify-center">
                  <svg className="w-3 h-3 sm:w-4 sm:h-4 sm:mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span className="hidden sm:inline">Auto-Messaging</span>
                </Link>
              </div>
            </div>

            {loading ? (
              <Loading message="Loading jobs..." />
            ) : (
              <JobTableWithStats jobs={jobs} jobStats={jobStats} loading={loading} onViewDetails={setSelectedJob} />
            )}
          </>
        )}

        {activeTab === 'applicants' && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
              <div>
                <h2 className="text-lg sm:text-xl font-heading font-bold text-gray-900 dark:text-white">Applicants</h2>
                <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                  Review candidates who applied to your jobs and request required documents.
                </p>
              </div>
              <button
                onClick={() => void loadApplicants()}
                disabled={loadingApplicants}
                className="px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-xl font-semibold transition-all duration-300 flex items-center gap-2 text-sm"
              >
                <svg className={`w-4 h-4 ${loadingApplicants ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh
              </button>
            </div>

            {loadingApplicants ? (
              <Loading message="Loading applicants..." />
            ) : applicants.length === 0 ? (
              <div className="p-8 rounded-xl border border-gray-100 dark:border-slate-700 bg-white dark:bg-slate-800 text-center">
                <p className="text-gray-500 dark:text-gray-400">No applicants found for your jobs yet.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {applicants.map((applicant) => {
                  const selectedDocs = selectedDocumentsByApp[applicant.application_id] || []
                  const uploadedKeys = Object.keys(applicant.documents_uploaded || {}) as ApplicationDocumentType[]
                  const resumeLocked = isDocRequestLocked(applicant, 'resume')
                  const ndaLocked = isDocRequestLocked(applicant, 'nda')
                  const allLocked = resumeLocked && ndaLocked
                  return (
                    <div key={applicant.application_id} className="rounded-xl border border-gray-100 dark:border-slate-700 bg-white dark:bg-slate-800 p-5">
                      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{applicant.candidate_name || 'Candidate'}</h3>
                          <p className="text-sm text-gray-600 dark:text-gray-400">{applicant.candidate_email || 'No email'}</p>
                          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                            Applied for <span className="font-medium text-gray-700 dark:text-gray-300">{applicant.job_title || 'Job'}</span>
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            Status: {applicant.status} • Applied: {applicant.applied_date ? new Date(applicant.applied_date).toLocaleDateString() : '—'}
                          </p>
                        </div>

                        <div className="w-full lg:w-[340px]">
                          <p className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-2">Upload Documents</p>
                          <div className="rounded-lg border border-gray-200 dark:border-slate-700 p-3 space-y-2 bg-gray-50 dark:bg-slate-900/40">
                            <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                              <input
                                type="checkbox"
                                checked={selectedDocs.includes('resume')}
                                onChange={() => toggleDocumentSelection(applicant.application_id, 'resume')}
                                disabled={resumeLocked}
                                className="rounded border-gray-300 dark:border-slate-600"
                              />
                              <span className="inline-flex items-center gap-2">
                                <span>CV / Resume</span>
                                {applicant.required_documents?.includes('resume') && documentBadge(resumeLocked)}
                              </span>
                            </label>
                            <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
                              <input
                                type="checkbox"
                                checked={selectedDocs.includes('nda')}
                                onChange={() => toggleDocumentSelection(applicant.application_id, 'nda')}
                                disabled={ndaLocked}
                                className="rounded border-gray-300 dark:border-slate-600"
                              />
                              <span className="inline-flex items-center gap-2">
                                <span>NDA</span>
                                {applicant.required_documents?.includes('nda') && documentBadge(ndaLocked)}
                              </span>
                            </label>
                          </div>
                          <button
                            onClick={() => void handleSubmitRequiredDocuments(applicant.application_id)}
                            disabled={submittingDocumentsForApp === applicant.application_id || allLocked}
                            className="mt-3 w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white text-sm font-semibold transition-colors"
                          >
                            {submittingDocumentsForApp === applicant.application_id ? 'Submitting...' : 'Submit Request'}
                          </button>

                          <div className="mt-3 text-xs text-gray-600 dark:text-gray-400 space-y-1">
                            <p>Requested:</p>
                            <div className="flex flex-wrap gap-2">
                              {(applicant.required_documents || []).length === 0 ? (
                                <span className="text-gray-500 dark:text-gray-400">None</span>
                              ) : (
                                (applicant.required_documents || []).map((docType) => (
                                  <span
                                    key={`req-${applicant.application_id}-${docType}`}
                                    className="inline-flex items-center gap-1.5 rounded-md border border-gray-200 dark:border-slate-700 px-2 py-1 bg-white dark:bg-slate-800"
                                  >
                                    <span>{docType === 'resume' ? 'CV / Resume' : 'NDA'}</span>
                                    {documentBadge(isDocRequestLocked(applicant, docType))}
                                  </span>
                                ))
                              )}
                            </div>
                            <p>Uploaded: {uploadedKeys.length ? uploadedKeys.join(', ') : 'None'}</p>
                          </div>

                          {uploadedKeys.length > 0 && (
                            <div className="mt-3 space-y-2">
                              {uploadedKeys.map((docType) => (
                                <div key={docType} className="flex items-center justify-between rounded-lg border border-gray-200 dark:border-slate-700 px-3 py-2">
                                  <div>
                                    <p className="text-xs font-semibold text-gray-700 dark:text-gray-300">
                                      {docType === 'resume' ? 'CV / Resume' : 'NDA'}
                                    </p>
                                    <p className="text-[11px] text-gray-500 dark:text-gray-400">
                                      {applicant.documents_uploaded?.[docType]?.filename || 'Uploaded file'}
                                    </p>
                                  </div>
                                  <div className="flex items-center gap-2">
                                    <button
                                      onClick={() => void openDocument(applicant, docType, false)}
                                      disabled={openingDocumentKey === `${applicant.application_id}:${docType}:view`}
                                      className="px-2.5 py-1.5 rounded-md bg-slate-100 dark:bg-slate-700 text-xs text-gray-700 dark:text-gray-200 hover:bg-slate-200 dark:hover:bg-slate-600 disabled:opacity-60"
                                    >
                                      {openingDocumentKey === `${applicant.application_id}:${docType}:view` ? 'Opening...' : 'View'}
                                    </button>
                                    <button
                                      onClick={() => void openDocument(applicant, docType, true)}
                                      disabled={openingDocumentKey === `${applicant.application_id}:${docType}:download`}
                                      className="px-2.5 py-1.5 rounded-md bg-emerald-600 text-xs text-white hover:bg-emerald-700 disabled:opacity-60"
                                    >
                                      {openingDocumentKey === `${applicant.application_id}:${docType}:download` ? 'Downloading...' : 'Download'}
                                    </button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {selectedJob && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-gray-200 dark:border-slate-700">
            <div className="p-6 border-b border-gray-100 dark:border-slate-700">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{selectedJob.title}</h2>
                  <p className="text-gray-600 dark:text-gray-400">{selectedJob.company || selectedJob.department || 'Job Details'}</p>
                </div>
                <button
                  onClick={() => setSelectedJob(null)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
                <div className="text-center p-3 bg-gray-50 dark:bg-slate-700/50 rounded-lg">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Location</p>
                  <p className="font-semibold text-gray-900 dark:text-white">{selectedJob.location || '—'}</p>
                </div>
                <div className="text-center p-3 bg-gray-50 dark:bg-slate-700/50 rounded-lg">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Department</p>
                  <p className="font-semibold text-gray-900 dark:text-white">{selectedJob.department || '—'}</p>
                </div>
                <div className="text-center p-3 bg-gray-50 dark:bg-slate-700/50 rounded-lg">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Type</p>
                  <p className="font-semibold text-gray-900 dark:text-white">{selectedJob.employment_type || selectedJob.job_type || '—'}</p>
                </div>
                <div className="text-center p-3 bg-gray-50 dark:bg-slate-700/50 rounded-lg">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Experience</p>
                  <p className="font-semibold text-gray-900 dark:text-white">{selectedJob.experience_level || selectedJob.experience_required || '—'}</p>
                </div>
                <div className="text-center p-3 bg-gray-50 dark:bg-slate-700/50 rounded-lg">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Salary</p>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {selectedJob.salary_min != null || selectedJob.salary_max != null
                      ? `${selectedJob.salary_min != null ? `₹${selectedJob.salary_min.toLocaleString('en-IN')}` : '—'}${selectedJob.salary_max != null ? ` - ₹${selectedJob.salary_max.toLocaleString('en-IN')}` : ''}`
                      : 'Not mentioned'}
                  </p>
                </div>
                <div className="text-center p-3 bg-gray-50 dark:bg-slate-700/50 rounded-lg">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Applicants</p>
                  <p className="font-semibold text-gray-900 dark:text-white">{jobStats[selectedJob.id]?.applicants ?? selectedJob.applicants ?? 0}</p>
                </div>
                <div className="text-center p-3 bg-gray-50 dark:bg-slate-700/50 rounded-lg">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Shortlisted</p>
                  <p className="font-semibold text-emerald-600 dark:text-emerald-400">{jobStats[selectedJob.id]?.shortlisted ?? selectedJob.shortlisted ?? 0}</p>
                </div>
              </div>

              {selectedJob.skills_required && (Array.isArray(selectedJob.skills_required) ? selectedJob.skills_required.length > 0 : selectedJob.skills_required.length > 0) && (
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-3">Skills Required</h3>
                  <div className="flex flex-wrap gap-2">
                    {(Array.isArray(selectedJob.skills_required)
                      ? selectedJob.skills_required
                      : selectedJob.skills_required.split(','))
                      .map((skill: string, index: number) => (
                        <span key={index} className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-lg text-sm">
                          {skill.trim()}
                        </span>
                      ))}
                  </div>
                </div>
              )}

              <div>
                <h3 className="font-semibold text-gray-900 dark:text-white mb-3">Job Description</h3>
                <p className="text-gray-600 dark:text-gray-400 whitespace-pre-line">{selectedJob.description || 'No description available.'}</p>
              </div>
            </div>

            <div className="p-6 border-t border-gray-100 dark:border-slate-700 flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => setSelectedJob(null)}
                className="flex-1 py-3 bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg transition-colors"
              >
                Close
              </button>
              <button
                onClick={() => handleEditJob(selectedJob)}
                className="flex-1 py-3 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg transition-colors"
              >
                Edit
              </button>
              <button
                onClick={() => handleDeleteJob(selectedJob)}
                disabled={deletingJobId === selectedJob.id}
                className="flex-1 py-3 bg-red-500 hover:bg-red-600 disabled:bg-red-300 text-white font-medium rounded-lg transition-colors"
              >
                {deletingJobId === selectedJob.id ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}

      {jobPendingDelete && (
        <div className="fixed inset-0 z-[60] bg-slate-900/55 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg rounded-2xl border border-red-200/60 dark:border-red-900/50 bg-white/95 dark:bg-slate-900/95 shadow-2xl overflow-hidden">
            <div className="p-6 border-b border-red-100 dark:border-red-900/40 bg-gradient-to-r from-red-50 to-rose-50 dark:from-red-950/40 dark:to-rose-950/30">
              <div className="flex items-start gap-3">
                <div className="shrink-0 w-10 h-10 rounded-xl bg-red-100 dark:bg-red-900/50 text-red-600 dark:text-red-300 flex items-center justify-center">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v3.75m0 3h.007M4.93 19h14.14c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.198 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-xl font-heading font-bold text-gray-900 dark:text-white">Delete Job Posting</h3>
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-300">This action is permanent and cannot be undone.</p>
                </div>
              </div>
            </div>

            <div className="p-6 space-y-3">
              <p className="text-sm text-gray-700 dark:text-gray-200">
                You are deleting <span className="font-semibold text-gray-900 dark:text-white">{jobPendingDelete.title}</span>.
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Related applications, interviews, offers, feedback, and notification logs will also be removed.
              </p>
            </div>

            <div className="p-6 pt-0 flex flex-col sm:flex-row gap-3">
              <button
                type="button"
                onClick={handleCancelDeleteJob}
                disabled={Boolean(deletingJobId)}
                className="flex-1 py-3 rounded-xl border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-gray-700 dark:text-gray-200 font-medium hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => void handleConfirmDeleteJob()}
                disabled={deletingJobId === jobPendingDelete.id}
                className="flex-1 py-3 rounded-xl bg-gradient-to-r from-red-500 to-rose-600 hover:from-red-600 hover:to-rose-700 text-white font-semibold shadow-lg shadow-red-500/20 transition-all disabled:opacity-60"
              >
                {deletingJobId === jobPendingDelete.id ? 'Deleting...' : 'Yes, Delete Job'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
