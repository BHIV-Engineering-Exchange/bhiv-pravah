import { useState, useEffect, useCallback, useRef } from 'react'
import toast from 'react-hot-toast'
import { searchCandidates, getAllInterviews, getRecruiterStats, type RecruiterStats } from '../../services/api'
import Loading from '../../components/Loading'
import StatsCard from '../../components/StatsCard'

const PREVIEW_PAGE_SIZE = 5
const EXPORT_FETCH_LIMIT = 2000

export default function ExportReports() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<RecruiterStats | null>(null)
  const [candidates, setCandidates] = useState<any[]>([])
  const [totalCandidates, setTotalCandidates] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [interviews, setInterviews] = useState<any[]>([])
  const [exporting, setExporting] = useState(false)
  const currentPageRef = useRef(currentPage)
  currentPageRef.current = currentPage

  const maxPage = Math.max(1, Math.ceil(totalCandidates / PREVIEW_PAGE_SIZE))
  const startItem = totalCandidates === 0 ? 0 : (currentPage - 1) * PREVIEW_PAGE_SIZE + 1
  const endItem = Math.min(currentPage * PREVIEW_PAGE_SIZE, totalCandidates)

  const loadData = useCallback(async (preservePage = false) => {
    try {
      setLoading(true)
      const pageToUse = preservePage ? currentPageRef.current : 1
      const offset = (pageToUse - 1) * PREVIEW_PAGE_SIZE
      const [statsData, candidatesRes, interviewsData] = await Promise.all([
        getRecruiterStats().catch(() => null),
        searchCandidates('', { limit: PREVIEW_PAGE_SIZE, offset }).catch(() => ({ candidates: [], total: 0 })),
        getAllInterviews().catch(() => [])
      ])
      setStats(statsData ?? null)
      const total = candidatesRes.total ?? 0
      setTotalCandidates(total)
      const newMaxPage = Math.max(1, Math.ceil(total / PREVIEW_PAGE_SIZE))
      if (preservePage && pageToUse > newMaxPage && newMaxPage >= 1) {
        setCurrentPage(newMaxPage)
        const clampedOffset = (newMaxPage - 1) * PREVIEW_PAGE_SIZE
        const res = await searchCandidates('', { limit: PREVIEW_PAGE_SIZE, offset: clampedOffset }).catch(() => ({ candidates: [], total: 0 }))
        setCandidates(res.candidates ?? [])
      } else {
        if (!preservePage) setCurrentPage(1)
        setCandidates(candidatesRes.candidates ?? [])
      }
      setInterviews(interviewsData)
    } catch (error) {
      console.error('Failed to load data:', error)
      toast.error('Failed to load assessment data')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData(false)
    const interval = setInterval(() => loadData(true), 30000)
    return () => clearInterval(interval)
  }, [])

  const goToPage = useCallback((page: number) => {
    const p = Math.max(1, Math.min(page, maxPage))
    setCurrentPage(p)
    const offset = (p - 1) * PREVIEW_PAGE_SIZE
    setLoading(true)
    searchCandidates('', { limit: PREVIEW_PAGE_SIZE, offset })
      .then((res) => {
        setCandidates(res.candidates ?? [])
        setTotalCandidates(res.total ?? 0)
      })
      .catch(() => {
        setCandidates([])
        toast.error('Failed to load page')
      })
      .finally(() => setLoading(false))
  }, [maxPage])

  const handleRefresh = () => loadData(true)

  const exportToCSV = (data: any[], filename: string) => {
    if (data.length === 0) {
      toast.error('No data to export')
      return
    }

    // Get all unique keys from all objects
    const allKeys = new Set<string>()
    data.forEach(item => {
      Object.keys(item).forEach(key => allKeys.add(key))
    })

    const headers = Array.from(allKeys)
    
    // Create CSV content
    const csvRows = []
    csvRows.push(headers.join(','))
    
    data.forEach(item => {
      const values = headers.map(header => {
        const value = item[header] || ''
        // Escape commas and quotes in values
        const stringValue = String(value).replace(/"/g, '""')
        return `"${stringValue}"`
      })
      csvRows.push(values.join(','))
    })

    const csvContent = csvRows.join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    
    link.setAttribute('href', url)
    link.setAttribute('download', filename)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    toast.success(`Exported ${data.length} records to ${filename}`)
  }

  const exportCompleteReport = async () => {
    setExporting(true)
    try {
      const allCandidates: any[] = []
      let offset = 0
      let hasMore = true
      while (hasMore) {
        const res = await searchCandidates('', { limit: EXPORT_FETCH_LIMIT, offset })
        const list = res.candidates ?? []
        allCandidates.push(...list)
        hasMore = list.length === EXPORT_FETCH_LIMIT && allCandidates.length < (res.total ?? 0)
        offset += EXPORT_FETCH_LIMIT
      }
      if (allCandidates.length === 0) {
        toast.error('No data to export')
        setExporting(false)
        return
      }
      const reportData = allCandidates.map(candidate => {
        const candidateInterview = interviews.find(i => 
          String(i.candidate_id) === String(candidate.id || candidate.candidate_id)
        )

        return {
          name: candidate.name || '',
          email: candidate.email || '',
          phone: candidate.phone || '',
          location: candidate.location || '',
          skills: candidate.technical_skills || candidate.skills || '',
          experience: candidate.experience_years || 0,
          education: candidate.education_level || candidate.education || '',
          interview_status: candidateInterview ? 'Scheduled' : 'Not Scheduled',
          interviewer: candidateInterview?.interviewer || 'Not Assigned',
          interview_date: candidateInterview?.scheduled_date || 'Not Scheduled',
          feedback_submitted: candidateInterview?.notes ? 'Yes' : 'No',
          values_integrity: candidate.values_score?.integrity || candidate.values_integrity || 'Not Assessed',
          values_honesty: candidate.values_score?.honesty || candidate.values_honesty || 'Not Assessed',
          values_discipline: candidate.values_score?.discipline || candidate.values_discipline || 'Not Assessed',
          values_hardwork: candidate.values_score?.hardWork || candidate.values_hardwork || 'Not Assessed',
          values_gratitude: candidate.values_score?.gratitude || candidate.values_gratitude || 'Not Assessed',
          overall_recommendation: candidate.overall_recommendation || 'Pending',
          shortlist_status: candidate.status || 'Applied'
        }
      })

      exportToCSV(reportData, `assessment_report_${new Date().toISOString().split('T')[0]}.csv`)
    } catch (error) {
      console.error('Export error:', error)
      toast.error('Failed to export report')
    } finally {
      setExporting(false)
    }
  }

  const exportAssessmentSummary = async () => {
    setExporting(true)
    try {
      const allCandidates: any[] = []
      let offset = 0
      let hasMore = true
      while (hasMore) {
        const res = await searchCandidates('', { limit: EXPORT_FETCH_LIMIT, offset })
        const list = res.candidates ?? []
        allCandidates.push(...list)
        hasMore = list.length === EXPORT_FETCH_LIMIT && allCandidates.length < (res.total ?? 0)
        offset += EXPORT_FETCH_LIMIT
      }
      const summaryData = allCandidates
        .filter(c => interviews.some(i => String(i.candidate_id) === String(c.id || c.candidate_id)))
        .map(candidate => {
          const interview = interviews.find(i => 
            String(i.candidate_id) === String(candidate.id || candidate.candidate_id)
          )

          return {
            rank: '',
            name: candidate.name || '',
            email: candidate.email || '',
            job_applied: interview?.job_title || 'N/A',
            interview_date: interview?.scheduled_date || 'Not Scheduled',
            interviewer: interview?.interviewer || 'Not Assigned',
            feedback_submitted: interview?.notes ? 'Yes' : 'No',
            values_integrity: candidate.values_score?.integrity || 'Not Assessed',
            values_honesty: candidate.values_score?.honesty || 'Not Assessed',
            values_discipline: candidate.values_score?.discipline || 'Not Assessed',
            values_hardwork: candidate.values_score?.hardWork || 'Not Assessed',
            values_gratitude: candidate.values_score?.gratitude || 'Not Assessed',
            overall_recommendation: candidate.overall_recommendation || 'Pending',
            shortlist_decision: candidate.status === 'shortlisted' ? 'Yes' : 'Under Review'
          }
        })

      exportToCSV(summaryData, `assessment_summary_${new Date().toISOString().split('T')[0]}.csv`)
    } catch (error) {
      console.error('Export error:', error)
      toast.error('Failed to export summary')
    } finally {
      setExporting(false)
    }
  }

  // Assessment Overview: same source as Recruiter Dashboard – GET /v1/recruiter/stats (recruiter-scoped only)
  const totalApplicants = stats?.total_applicants ?? 0       // Applicants to this recruiter's jobs
  const totalInterviewsScheduled = stats?.interviewed ?? 0    // Interviews for this recruiter's jobs
  const assessmentsCompleted = stats?.assessments_completed ?? 0  // Values assessments (feedback) for this recruiter's jobs
  const shortlistedCount = stats?.shortlisted ?? 0           // Shortlisted applicants to this recruiter's jobs

  if (loading) {
    return <Loading message="Loading assessment data..." />
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-green-500/5 to-emerald-500/5 dark:from-green-500/10 dark:to-emerald-500/10 backdrop-blur-xl border border-green-300/20 dark:border-green-500/20">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">🏆 Values Assessment & Export Reports</h1>
        <p className="text-gray-600 dark:text-gray-400">Comprehensive assessment reports with all feedback, interviews, and shortlist data</p>
      </div>

      {/* Assessment Overview */}
      <div>
        <h2 className="section-title mb-6">Assessment Overview</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatsCard
            title="Total Applicants"
            value={totalApplicants}
            color="blue"
            icon={
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            }
          />
          <StatsCard
            title="Interviews Scheduled"
            value={totalInterviewsScheduled}
            color="purple"
            icon={
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            }
          />
          <StatsCard
            title="Assessments Completed"
            value={assessmentsCompleted}
            color="green"
            icon={
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            }
          />
          <StatsCard
            title="Shortlisted Candidates"
            value={shortlistedCount}
            color="yellow"
            icon={
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
              </svg>
            }
          />
        </div>
      </div>

      {/* Export Options */}
      <div className="card">
        <h2 className="section-title mb-4">Export Assessment Reports</h2>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          All exports include assessments, feedback, interviews, and shortlist data
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Complete Candidate Report */}
          <div className="p-6 bg-blue-50 dark:bg-blue-900/20 rounded-xl border border-blue-200 dark:border-blue-800">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Complete Candidate Report
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              All candidates with assessments, interviews, and shortlist status
            </p>
            <button
              onClick={exportCompleteReport}
              disabled={exporting || totalCandidates === 0}
              className="w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {exporting ? 'Exporting...' : `Export All (${totalCandidates})`}
            </button>
          </div>

          {/* Assessment Summary */}
          <div className="p-6 bg-purple-50 dark:bg-purple-900/20 rounded-xl border border-purple-200 dark:border-purple-800">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Assessment Summary
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Candidates with interviews and all assessment data
            </p>
            <button
              onClick={exportAssessmentSummary}
              disabled={exporting || interviews.length === 0}
              className="w-full bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {exporting ? 'Exporting...' : `Export Summary (${interviews.length})`}
            </button>
          </div>

          {/* Quick Actions */}
          <div className="p-6 bg-green-50 dark:bg-green-900/20 rounded-xl border border-green-200 dark:border-green-800">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Quick Actions
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              View and manage assessment data
            </p>
            <div className="space-y-2">
              <button
                onClick={handleRefresh}
                className="w-full bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg font-medium transition-colors text-sm"
              >
                Refresh Data
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Data Preview */}
      {totalCandidates > 0 && (
        <div className="card">
          <h2 className="section-title mb-4">Data Preview</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
            Showing {startItem}&ndash;{endItem} of {totalCandidates} candidates
          </p>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Email</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Interview</th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                {candidates.map((candidate, idx) => {
                  const hasInterview = interviews.some(i =>
                    String(i.candidate_id) === String(candidate.id || candidate.candidate_id)
                  )
                  return (
                    <tr key={candidate.id || idx}>
                      <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">
                        {candidate.name || 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                        {candidate.email || 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          candidate.status === 'shortlisted' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
                          candidate.status === 'interviewed' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' :
                          'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                        }`}>
                          {candidate.status || 'Applied'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                        <span className={hasInterview ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'}>
                          {hasInterview ? 'Scheduled' : 'Not Scheduled'}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage <= 1 || loading}
              className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Page {currentPage} of {maxPage}
            </span>
            <button
              type="button"
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage >= maxPage || loading}
              className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

