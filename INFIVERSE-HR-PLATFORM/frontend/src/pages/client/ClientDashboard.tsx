import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  getClientJobs,
  getClientStats,
  getClientProfile,
  getJobById,
  deleteJob,
  getClientApplicants,
  setClientRequiredDocuments,
  getClientApplicantDocumentBlob,
  type ApplicationDocumentType,
  type ClientApplicantRecord,
  Job,
  ClientStats,
} from '../../services/api'
import StatsCard from '../../components/StatsCard'
import Loading from '../../components/Loading'
import Table from '../../components/Table'
import { toast } from 'react-hot-toast'
import { authStorage } from '../../utils/authStorage'

function ClientJobsTable({
  jobs,
  loading,
  onViewDetails,
}: {
  jobs: Job[]
  loading: boolean
  onViewDetails: (job: Job) => void
}) {
  return (
    <Table
      columns={['Job Title', 'Department', 'Location', 'Type', 'Applicants', 'Shortlisted', 'Actions']}
      data={jobs}
      renderRow={(job) => (
        <>
          <td className="font-semibold text-gray-900 dark:text-white">{job.title}</td>
          <td className="text-gray-600 dark:text-gray-400">{job.department || '—'}</td>
          <td className="text-gray-600 dark:text-gray-400">{job.location || '—'}</td>
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
            {loading ? (
              <span className="text-gray-400 text-sm">Loading...</span>
            ) : (
              <span className="font-semibold text-gray-900 dark:text-white">{job.applicants ?? 0}</span>
            )}
          </td>
          <td>
            {loading ? (
              <span className="text-gray-400 text-sm">Loading...</span>
            ) : (
              <span className="font-semibold text-emerald-600 dark:text-emerald-400">{job.shortlisted ?? 0}</span>
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
      )}
    />
  )
}

export default function ClientDashboard() {
  const navigate = useNavigate()
  const [jobs, setJobs] = useState<Job[]>([])
  const [stats, setStats] = useState<ClientStats | null>(null)
  const [connectionId, setConnectionId] = useState<string>('')
  const [activeTab, setActiveTab] = useState<'pipeline' | 'jobs' | 'applicants'>(() => {
    const saved = localStorage.getItem('clientDashboardActiveTab')
    return (saved === 'jobs' || saved === 'pipeline' || saved === 'applicants') ? saved : 'pipeline'
  })
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)
  const [canManageSelectedJob, setCanManageSelectedJob] = useState(false)
  const [loadingSelectedJobMeta, setLoadingSelectedJobMeta] = useState(false)
  const [jobPendingDelete, setJobPendingDelete] = useState<Job | null>(null)
  const [deletingJobId, setDeletingJobId] = useState<string | null>(null)
  const [jobsError, setJobsError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [applicants, setApplicants] = useState<ClientApplicantRecord[]>([])
  const [loadingApplicants, setLoadingApplicants] = useState(false)
  const [selectedDocumentsByApp, setSelectedDocumentsByApp] = useState<Record<string, ApplicationDocumentType[]>>({})
  const [submittingDocumentsForApp, setSubmittingDocumentsForApp] = useState<string | null>(null)
  const [openingDocumentKey, setOpeningDocumentKey] = useState<string | null>(null)

  useEffect(() => {
    loadDashboardData()
    // Auto-refresh every 30 seconds for real-time data
    const interval = setInterval(() => {
      void loadDashboardData(true)
      if (activeTab === 'applicants') {
        void loadApplicants(true)
      }
    }, 30000)
    return () => clearInterval(interval)
  }, [activeTab])

  useEffect(() => {
    localStorage.setItem('clientDashboardActiveTab', activeTab)
  }, [activeTab])

  // All data is client-scoped: APIs use logged-in client's JWT; backend returns only this client's jobs
  // (including jobs recruiters posted via this client's connection_id). No client_id param is sent.
  const loadDashboardData = async (silent = false) => {
    try {
      if (!silent) setLoading(true)
      setJobsError(null)
      const [jobsResult, statsData, profile] = await Promise.all([
        getClientJobs()
          .then((data) => ({ data, ok: true, error: null as unknown }))
          .catch((error: unknown) => ({ data: [] as Job[], ok: false, error })),
        getClientStats(),
        getClientProfile()
      ])
      if (!jobsResult.ok) {
        console.error('Failed to load client jobs:', jobsResult.error)
        setJobsError('Unable to load active job openings right now. Showing latest available data.')
      }
      setJobs(Array.isArray(jobsResult.data) ? jobsResult.data : [])
      setStats(statsData ?? null)
      setConnectionId(profile?.connection_id ?? '')
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    } finally {
      if (!silent) setLoading(false)
    }
  }

  const loadApplicants = async (silent = false) => {
    try {
      if (!silent) setLoadingApplicants(true)
      const rows = await getClientApplicants()
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
      console.error('Failed to load applicants:', error)
      setApplicants([])
    } finally {
      if (!silent) setLoadingApplicants(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'applicants') {
      loadApplicants()
    }
  }, [activeTab])

  useEffect(() => {
    const onNotificationsUpdated = (event: Event) => {
      const customEvent = event as CustomEvent<{ role?: string }>
      if (customEvent.detail?.role !== 'client') return
      void loadDashboardData(true)
      if (activeTab === 'applicants') {
        void loadApplicants(true)
      }
    }
    window.addEventListener('portal-notifications-updated', onNotificationsUpdated)
    return () => window.removeEventListener('portal-notifications-updated', onNotificationsUpdated)
  }, [activeTab])

  const copyConnectionId = async () => {
    if (!connectionId) return
    try {
      await navigator.clipboard.writeText(connectionId)
      toast.success('Connection ID copied to clipboard')
    } catch {
      toast.error('Failed to copy')
    }
  }

  const getCurrentClientId = (): string => {
    const direct = authStorage.getItem('client_id')
    if (direct) return String(direct)
    const userDataRaw = authStorage.getItem('user_data')
    if (!userDataRaw) return ''
    try {
      const parsed = JSON.parse(userDataRaw)
      return parsed?.id != null ? String(parsed.id) : ''
    } catch {
      return ''
    }
  }

  const handleOpenJobDetails = async (job: Job) => {
    setSelectedJob(job)
    setCanManageSelectedJob(false)
    setLoadingSelectedJobMeta(true)
    try {
      const detailed = await getJobById(job.id)
      const clientId = getCurrentClientId()
      const ownerClientId = detailed?.client_id != null ? String(detailed.client_id) : ''
      setCanManageSelectedJob(Boolean(ownerClientId && (!clientId || ownerClientId === clientId)))
    } catch (error: any) {
      const msg = error?.response?.data?.detail || error?.message
      if (typeof msg === 'string' && msg.includes('own jobs')) {
        setCanManageSelectedJob(false)
      } else {
        console.error('Failed to load job ownership metadata:', error)
      }
    } finally {
      setLoadingSelectedJobMeta(false)
    }
  }

  const closeSelectedJobModal = () => {
    setSelectedJob(null)
    setCanManageSelectedJob(false)
    setLoadingSelectedJobMeta(false)
  }

  const handleEditJob = (job: Job) => {
    if (!canManageSelectedJob) {
      toast.error('You can only edit jobs posted by your own client account.')
      return
    }
    navigate(`/client/jobs?edit=${encodeURIComponent(job.id)}`)
  }

  const handleDeleteJob = (job: Job) => {
    if (!canManageSelectedJob) {
      toast.error('You can only delete jobs posted by your own client account.')
      return
    }
    setJobPendingDelete(job)
  }

  const handleCancelDeleteJob = () => {
    if (deletingJobId) return
    setJobPendingDelete(null)
  }

  const handleConfirmDeleteJob = async () => {
    if (!jobPendingDelete) return
    setDeletingJobId(jobPendingDelete.id)
    try {
      await deleteJob(jobPendingDelete.id)
      toast.success('Job deleted successfully')
      setJobPendingDelete(null)
      closeSelectedJobModal()
      await loadDashboardData()
    } catch (error: any) {
      const msg = error?.response?.data?.detail || error?.message || 'Failed to delete job'
      toast.error(msg)
    } finally {
      setDeletingJobId(null)
    }
  }

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
      await setClientRequiredDocuments(applicationId, selected)
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
    // Lock until candidate uploads for latest request.
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
      const { blob, filename } = await getClientApplicantDocumentBlob(applicant.application_id, docType, download)
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

  // Use stats from dedicated client/stats endpoint (DB counts only)
  const activeJobs = stats?.active_jobs ?? jobs.filter(job => job.status === 'active' || !job.status).length
  const totalApplications = stats?.total_applications ?? 0
  const interviewsScheduled = stats?.interviews_scheduled ?? 0
  const offersMade = stats?.offers_made ?? 0

  // Pipeline data from stats (no match/top; shortlisted = screened/reviewed)
  const applied = totalApplications
  const shortlisted = stats?.shortlisted ?? 0
  const aiScreened = shortlisted
  const reviewed = shortlisted
  const interview = interviewsScheduled
  const offer = offersMade
  const hired = stats?.hired ?? 0

  // Conversion rates
  const conversionRates = {
    appliedToScreened: applied > 0 ? Math.round((aiScreened / applied) * 100) : 0,
    screenedToReviewed: aiScreened > 0 ? Math.round((reviewed / aiScreened) * 100) : 0,
    reviewedToInterview: reviewed > 0 ? Math.round((interview / reviewed) * 100) : 0,
    interviewToOffer: interview > 0 ? Math.round((offer / interview) * 100) : 0,
    offerToHired: offer > 0 ? Math.round((hired / offer) * 100) : 0,
  }

  if (loading) {
    return <Loading message="Loading dashboard..." />
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <div className="p-4 sm:p-6 rounded-2xl bg-gradient-to-r from-blue-500/5 to-indigo-500/5 dark:from-blue-500/10 dark:to-indigo-500/10 backdrop-blur-xl border border-blue-300/20 dark:border-blue-500/20 mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 dark:text-white mb-2">Sampada Client Portal</h1>
          <p className="text-sm sm:text-base text-gray-500 dark:text-gray-400">Dedicated Client Interface for Jobs & Candidate Review</p>
        </div>
      </div>

      {/* Connection ID – share with recruiters for real-time job linking */}
      {connectionId && (
        <div className="mb-6 sm:mb-8 p-4 sm:p-6 rounded-2xl bg-gradient-to-r from-emerald-500/5 to-teal-500/5 dark:from-emerald-500/10 dark:to-teal-500/10 border border-emerald-300/20 dark:border-emerald-500/20">
          <h2 className="text-lg font-heading font-bold text-gray-900 dark:text-white mb-2 flex items-center gap-2">
            <svg className="w-5 h-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
            Recruiter connection
          </h2>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">Share this ID with recruiters so they can post jobs for you and you can see activity in real time.</p>
          <div className="flex flex-wrap items-center gap-2">
            <code className="px-3 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm font-mono text-gray-900 dark:text-white break-all">
              {connectionId}
            </code>
            <button
              type="button"
              onClick={copyConnectionId}
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium transition-colors"
            >
              Copy
            </button>
          </div>
        </div>
      )}

      {/* Client Reports & Analytics */}
      <div className="mb-6 sm:mb-8">
        <h2 className="text-lg sm:text-xl font-heading font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Client Reports & Analytics
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          <StatsCard
            title="Active Jobs"
            value={activeJobs}
            color="blue"
            trend={{ value: 4, label: 'recent' }}
            icon={
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            }
          />
          <StatsCard
            title="Total Applications"
            value={totalApplications}
            color="green"
            trend={{ value: 0, label: 'this week' }}
            icon={
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            }
          />
          <StatsCard
            title="Interviews Scheduled"
            value={interviewsScheduled}
            color="yellow"
            trend={{ value: 0, label: 'this week' }}
            icon={
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            }
          />
          <StatsCard
            title="Offers Made"
            value={offersMade}
            color="purple"
            trend={{ value: 0, label: 'this week' }}
            icon={
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            }
          />
        </div>
      </div>

      {/* Application Pipeline / Active Jobs Tabs */}
      <div className="card">
        <div className="border-b border-gray-200 dark:border-gray-700 mb-6">
          <div className="flex space-x-1 overflow-x-auto">
            <button
              onClick={() => setActiveTab('pipeline')}
              className={`px-4 sm:px-6 py-3 font-medium text-sm transition-colors whitespace-nowrap ${
                activeTab === 'pipeline'
                  ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Application Pipeline
            </button>
            <button
              onClick={() => setActiveTab('jobs')}
              className={`px-4 sm:px-6 py-3 font-medium text-sm transition-colors whitespace-nowrap ${
                activeTab === 'jobs'
                  ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              Active Job Openings
            </button>
            <button
              onClick={() => setActiveTab('applicants')}
              className={`px-4 sm:px-6 py-3 font-medium text-sm transition-colors whitespace-nowrap ${
                activeTab === 'applicants'
                  ? 'border-b-2 border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              View Applicants
            </button>
          </div>
        </div>

        {activeTab === 'pipeline' && (
          <>
            <h2 className="section-title flex items-center gap-2">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
              </svg>
              Application Pipeline
            </h2>

            <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <p className="text-sm text-blue-800 dark:text-blue-300">
                Your pipeline: {totalApplications} candidates and {activeJobs} active jobs (only your company&apos;s data; includes jobs recruiters posted using your Connection ID).
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Pipeline Data */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Pipeline Data</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <span className="text-gray-700 dark:text-gray-300">Applied</span>
                    <span className="text-xl font-bold text-gray-900 dark:text-white">{applied}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <span className="text-gray-700 dark:text-gray-300">AI Screened</span>
                    <span className="text-xl font-bold text-gray-900 dark:text-white">{aiScreened}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <span className="text-gray-700 dark:text-gray-300">Reviewed</span>
                    <span className="text-xl font-bold text-gray-900 dark:text-white">{reviewed}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <span className="text-gray-700 dark:text-gray-300">Interview</span>
                    <span className="text-xl font-bold text-gray-900 dark:text-white">{interview}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <span className="text-gray-700 dark:text-gray-300">Offer</span>
                    <span className="text-xl font-bold text-gray-900 dark:text-white">{offer}</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <span className="text-gray-700 dark:text-gray-300">Hired</span>
                    <span className="text-xl font-bold text-gray-900 dark:text-white">{hired}</span>
                  </div>
                </div>
              </div>

              {/* Conversion Rates */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Conversion Rates (Based on Real Data)</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <span className="text-gray-700 dark:text-gray-300">Applied → AI Screened</span>
                    <span className="text-xl font-bold text-green-600 dark:text-green-400">{conversionRates.appliedToScreened}%</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <span className="text-gray-700 dark:text-gray-300">AI Screened → Reviewed</span>
                    <span className="text-xl font-bold text-green-600 dark:text-green-400">{conversionRates.screenedToReviewed}%</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <span className="text-gray-700 dark:text-gray-300">Reviewed → Interview</span>
                    <span className="text-xl font-bold text-green-600 dark:text-green-400">{conversionRates.reviewedToInterview}%</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <span className="text-gray-700 dark:text-gray-300">Interview → Offer</span>
                    <span className="text-xl font-bold text-green-600 dark:text-green-400">{conversionRates.interviewToOffer}%</span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <span className="text-gray-700 dark:text-gray-300">Offer → Hired</span>
                    <span className="text-xl font-bold text-green-600 dark:text-green-400">{conversionRates.offerToHired}%</span>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === 'jobs' && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
              <div>
                <h2 className="text-lg sm:text-xl font-heading font-bold text-gray-900 dark:text-white">Active Job Openings</h2>
                <p className="text-xs sm:text-sm text-gray-500 dark:text-gray-400">
                  {jobs.length} jobs currently active for your organization
                </p>
              </div>
              <button
                onClick={() => void loadDashboardData()}
                disabled={loading}
                className="px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-xl font-semibold transition-all duration-300 flex items-center gap-2 text-sm"
                title="Refresh jobs"
              >
                <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Refresh
              </button>
            </div>

            {jobsError && (
              <div className="p-3 rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-300 text-sm">
                {jobsError}
              </div>
            )}

            {loading ? (
              <Loading message="Loading jobs..." />
            ) : (
              <ClientJobsTable jobs={jobs} loading={loading} onViewDetails={handleOpenJobDetails} />
            )}
          </div>
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
                            className="mt-3 w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white text-sm font-semibold transition-colors"
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
                                      className="px-2.5 py-1.5 rounded-md bg-blue-600 text-xs text-white hover:bg-blue-700 disabled:opacity-60"
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
                  onClick={closeSelectedJobModal}
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
                  <p className="font-semibold text-gray-900 dark:text-white">{selectedJob.applicants ?? 0}</p>
                </div>
                <div className="text-center p-3 bg-gray-50 dark:bg-slate-700/50 rounded-lg">
                  <p className="text-xs text-gray-500 dark:text-gray-400">Shortlisted</p>
                  <p className="font-semibold text-emerald-600 dark:text-emerald-400">{selectedJob.shortlisted ?? 0}</p>
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

            <div className="p-6 border-t border-gray-100 dark:border-slate-700">
              {loadingSelectedJobMeta ? (
                <p className="text-sm text-gray-500 dark:text-gray-400">Checking job ownership…</p>
              ) : canManageSelectedJob ? (
                <div className="flex flex-col sm:flex-row gap-3">
                  <button
                    onClick={closeSelectedJobModal}
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
              ) : (
                <div className="space-y-3">
                  <p className="text-sm text-amber-700 dark:text-amber-300">
                    This job is visible in your dashboard, but only jobs posted directly by your client account can be edited or deleted here.
                  </p>
                  <button
                    onClick={closeSelectedJobModal}
                    className="w-full py-3 bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg transition-colors"
                  >
                    Close
                  </button>
                </div>
              )}
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
