import { useState, useEffect } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { 
  getTopMatches, 
  getJobById, 
  shortlistCandidate, 
  rejectCandidate,
  scheduleInterview,
  getRecruiterJobs,
  type MatchResult,
  type Job
} from '../../services/api'
import Table from '../../components/Table'
import Loading from '../../components/Loading'
import BlobLoadingOverlay from '../../components/BlobLoadingOverlay'

export default function ApplicantsMatching() {
  const { jobId: urlJobId } = useParams()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const jobIdFromQuery = searchParams.get('jobId')
  const effectiveJobId = urlJobId || jobIdFromQuery || ''

  const [jobId, setJobId] = useState<string>(effectiveJobId)
  const [job, setJob] = useState<Job | null>(null)
  const [jobs, setJobs] = useState<Job[]>([])
  const [candidates, setCandidates] = useState<MatchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [selectedCandidate, setSelectedCandidate] = useState<MatchResult | null>(null)
  const [showLoadingOverlay, setShowLoadingOverlay] = useState(false)

  useEffect(() => {
    setJobId(effectiveJobId)
  }, [effectiveJobId])

  // Load only recruiter's jobs for dropdown; do NOT auto-load candidates or trigger Generate
  useEffect(() => {
    loadJobs()
  }, [])

  useEffect(() => {
    if (jobs.length > 0 && !jobId && jobs[0].id) {
      setJobId(jobs[0].id)
    }
  }, [jobs, jobId])

  useEffect(() => {
    if (jobId) loadJobDetails()
  }, [jobId])

  const loadJobs = async () => {
    try {
      const jobsData = await getRecruiterJobs()
      setJobs(jobsData)
    } catch (error) {
      console.error('Failed to load recruiter jobs:', error)
    }
  }

  const loadJobDetails = async () => {
    if (!jobId) return
    try {
      const jobData = await getJobById(jobId)
      setJob(jobData)
    } catch (error) {
      console.error('Failed to load job:', error)
      setJob(null)
    }
  }

  // Refresh button: only reload jobs list and current job details. Do NOT call the match endpoint.
  const handleRefresh = async () => {
    try {
      setLoading(true)
      await loadJobs()
      if (jobId) {
        const jobData = await getJobById(jobId).catch(() => null)
        setJob(jobData)
      }
    } catch (error) {
      console.error('Failed to refresh:', error)
      toast.error('Failed to refresh page data')
    } finally {
      setLoading(false)
    }
  }

  // Full reload including match results (used after shortlist/reject to update the list)
  const loadData = async () => {
    if (!jobId) {
      toast.error('Please select a job')
      return
    }
    try {
      setLoading(true)
      await loadJobs()
      const [jobData, matchResults] = await Promise.all([
        getJobById(jobId).catch(() => null),
        getTopMatches(jobId, 20).catch(() => [])
      ])
      setJob(jobData)
      setCandidates(matchResults)
    } catch (error) {
      console.error('Failed to load data:', error)
      toast.error('Failed to load applicants')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateShortlist = async () => {
    if (!jobId) {
      toast.error('Please select a job')
      return
    }

    setGenerating(true)
    setShowLoadingOverlay(true)
    try {
      // Use gateway /v1/match/{jobId}/top (AI or DB fallback) instead of calling agent directly
      const [jobData, matchResults] = await Promise.all([
        getJobById(jobId).catch(() => null),
        getTopMatches(jobId, 20).catch(() => [])
      ])
      setJob(jobData)
      setCandidates(matchResults)
      if (matchResults.length === 0) {
        toast('No candidates found for this job. Try uploading candidates or check back later.', { icon: '⚠' })
      } else {
        toast.success(`Found ${matchResults.length} matched candidates`)
      }
    } catch (error) {
      console.error('Generate shortlist error:', error)
      toast.error('Failed to generate AI shortlist')
    } finally {
      setGenerating(false)
      setShowLoadingOverlay(false)
    }
  }

  const handleShortlist = async (candidateId: string) => {
    try {
      await shortlistCandidate(jobId, candidateId)
      toast.success('Candidate shortlisted successfully')
      loadData()
    } catch (error) {
      toast.error('Failed to shortlist candidate')
    }
  }

  const handleReject = async (candidateId: string) => {
    try {
      await rejectCandidate(jobId.toString(), candidateId)
      toast.success('Candidate rejected')
      loadData()
    } catch (error) {
      toast.error('Failed to reject candidate')
    }
  }

  const handleScheduleInterview = async (candidateId: string) => {
    try {
      await scheduleInterview({
        candidate_id: candidateId,
        job_id: jobId,
        job_title: job?.title,
        scheduled_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        interview_type: 'video',
        status: 'scheduled'
      })
      toast.success('Interview scheduled')
    } catch (error) {
      toast.error('Failed to schedule interview')
    }
  }

  const getMatchScoreColor = (score: number) => {
    if (score >= 80) return 'badge-success'
    if (score >= 60) return 'badge-warning'
    return 'badge-danger'
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-green-500/5 to-emerald-500/5 dark:from-green-500/10 dark:to-emerald-500/10 backdrop-blur-xl border border-green-300/20 dark:border-green-500/20">
        <h1 className="page-title">AI-Powered Candidate Shortlist</h1>
        <p className="page-subtitle">Get the top candidates matched by AI using advanced semantic analysis and values alignment</p>
      </div>

      {/* Job Selection & Actions */}
      <div className="card">
        <h2 className="section-title mb-4">Generate AI Shortlist</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          {/* Job selection - dropdown of recruiter's jobs only (same as Upload Candidates) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Job
            </label>
            {jobs.length === 0 ? (
              <p className="text-sm text-gray-500 dark:text-gray-400 py-2 italic">No jobs posted</p>
            ) : (
              <select
                value={jobId}
                onChange={(e) => {
                  setJobId(e.target.value)
                  setJob(null)
                  setCandidates([])
                }}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500 focus:border-transparent"
              >
                <option value="">Select a job</option>
                {jobs.map((j) => (
                  <option key={j.id} value={j.id}>{j.title} – {j.id}</option>
                ))}
              </select>
            )}
          </div>

          {/* Generate Button */}
          <div className="flex items-end">
            <button
              onClick={handleGenerateShortlist}
              disabled={generating || loading}
              className="group w-full bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-6 py-2.5 rounded-lg font-semibold text-sm transition-all duration-200 flex items-center justify-center gap-2 shadow-md shadow-green-500/25 hover:shadow-lg hover:shadow-green-500/40 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {generating ? (
                <>
                  <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Generating...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span>Generate AI Shortlist</span>
                </>
              )}
            </button>
          </div>

          {/* Refresh Button - only refreshes jobs and job details, does not trigger AI shortlist */}
          <div className="flex items-end">
            <button
              onClick={handleRefresh}
              disabled={loading || generating}
              className="w-full px-4 py-2.5 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium text-sm transition-all duration-200 flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Job Info */}
        {job && (
          <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg mb-4">
            <div className="flex flex-wrap items-center gap-3">
              <span className="font-semibold text-gray-900 dark:text-white">{job.title}</span>
              <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded text-xs font-medium">{job.location}</span>
              <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded text-xs font-medium">{job.job_type}</span>
              <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded text-xs font-medium">{job.department}</span>
            </div>
          </div>
        )}
      </div>

      {/* Candidates Table */}
      {loading ? (
        <Loading message="Loading candidates..." />
      ) : candidates.length === 0 ? (
        <div className="card text-center py-12">
          <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-gray-500 dark:text-gray-400 text-lg">No candidates found</p>
          <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">Click "Generate AI Shortlist" to find matched candidates</p>
        </div>
      ) : (
        <div className="card">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
            <div>
              <h2 className="section-title mb-1">Matched Candidates ({candidates.length})</h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">AI-ranked based on job requirements</p>
            </div>
            <div className="flex gap-2">
              <span className="badge badge-success">High Match (80%+)</span>
              <span className="badge badge-warning">Medium (60-79%)</span>
              <span className="badge badge-danger">Low (&lt;60%)</span>
            </div>
          </div>
          
          <Table
            columns={['Candidate', 'Match Score', 'Skills Match', 'Experience', 'Location', 'Matched Skills', 'Actions']}
            data={candidates}
            renderRow={(candidate) => (
              <>
                <td>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                      {candidate.candidate_name.split(' ').map((n: string) => n[0]).join('')}
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900 dark:text-white">{candidate.candidate_name}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{candidate.email}</p>
                    </div>
                  </div>
                </td>
                <td>
                  <span className={`badge ${getMatchScoreColor(candidate.match_score)}`}>
                    {candidate.match_score}%
                  </span>
                </td>
                <td className="text-gray-600 dark:text-gray-400">{candidate.skills_match}%</td>
                <td className="text-gray-600 dark:text-gray-400">{candidate.experience_match}%</td>
                <td className="text-gray-600 dark:text-gray-400">{candidate.location_match}%</td>
                <td>
                  <div className="flex flex-wrap gap-1 max-w-[200px]">
                    {candidate.matched_skills.slice(0, 3).map((skill: string, idx: number) => (
                      <span key={idx} className="px-2 py-0.5 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-xs font-medium">
                        {skill}
                      </span>
                    ))}
                    {candidate.matched_skills.length > 3 && (
                      <span className="px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded text-xs font-medium">
                        +{candidate.matched_skills.length - 3}
                      </span>
                    )}
                  </div>
                </td>
                <td>
                  <div className="flex items-center gap-1">
                    <button
                      onClick={() => setSelectedCandidate(candidate)}
                      className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-blue-600 dark:text-blue-400 transition-colors"
                      title="View Details"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => handleShortlist(candidate.candidate_id)}
                      className="p-2 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 rounded-lg text-emerald-600 dark:text-emerald-400 transition-colors"
                      title="Shortlist"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </button>
                    <button
                      onClick={() => handleScheduleInterview(candidate.candidate_id)}
                      className="p-2 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg text-blue-600 dark:text-blue-400 transition-colors"
                      title="Schedule Interview"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => navigate(`/recruiter/feedback/${candidate.candidate_id}`)}
                      className="p-2 hover:bg-amber-50 dark:hover:bg-amber-900/20 rounded-lg text-amber-600 dark:text-amber-400 transition-colors"
                      title="Add Feedback"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    <button
                      onClick={() => handleReject(candidate.candidate_id)}
                      className="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg text-red-600 dark:text-red-400 transition-colors"
                      title="Reject"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </td>
              </>
            )}
          />
        </div>
      )}

      {/* Candidate Detail Modal */}
      {selectedCandidate && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border-2 border-gray-200 dark:border-gray-700 animate-scale-in">
            <div className="p-6">
              {/* Modal Header */}
              <div className="flex justify-between items-start mb-6">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center text-white font-bold text-xl">
                    {selectedCandidate.candidate_name.split(' ').map((n: string) => n[0]).join('')}
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900 dark:text-white">{selectedCandidate.candidate_name}</h3>
                    <p className="text-gray-500 dark:text-gray-400">{selectedCandidate.email}</p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedCandidate(null)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-xl transition-colors text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Match Score Banner */}
              <div className={`rounded-xl p-4 mb-6 ${
                selectedCandidate.match_score >= 80 ? 'bg-emerald-50 dark:bg-emerald-900/20 border-2 border-emerald-200 dark:border-emerald-800' :
                selectedCandidate.match_score >= 60 ? 'bg-amber-50 dark:bg-amber-900/20 border-2 border-amber-200 dark:border-amber-800' :
                'bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800'
              }`}>
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-gray-700 dark:text-gray-300">Match Score</span>
                  <span className={`text-3xl font-bold ${
                    selectedCandidate.match_score >= 80 ? 'text-emerald-600 dark:text-emerald-400' :
                    selectedCandidate.match_score >= 60 ? 'text-amber-600 dark:text-amber-400' :
                    'text-red-600 dark:text-red-400'
                  }`}>{selectedCandidate.match_score}%</span>
                </div>
              </div>

              {/* Info Grid */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl">
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Experience Match</p>
                  <p className="text-gray-900 dark:text-white font-semibold mt-1">{selectedCandidate.experience_match}%</p>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl">
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Location Match</p>
                  <p className="text-gray-900 dark:text-white font-semibold mt-1">{selectedCandidate.location_match}%</p>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl">
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Skills Match</p>
                  <p className="text-gray-900 dark:text-white font-semibold mt-1">{selectedCandidate.skills_match}%</p>
                </div>
                <div className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl">
                  <p className="text-sm font-medium text-gray-500 dark:text-gray-400">Matched Skills</p>
                  <p className="text-gray-900 dark:text-white font-semibold mt-1">{selectedCandidate.matched_skills.length}</p>
                </div>
              </div>

              {/* Skills */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">Matched Skills</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedCandidate.matched_skills.map((skill: string, idx: number) => (
                    <span key={idx} className="px-3 py-1.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded-lg font-medium text-sm">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Missing Skills */}
              {selectedCandidate.missing_skills && selectedCandidate.missing_skills.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">Missing Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedCandidate.missing_skills.map((skill: string, idx: number) => (
                      <span key={idx} className="px-3 py-1.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400 rounded-lg font-medium text-sm">
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3 mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={() => {
                    handleShortlist(selectedCandidate.candidate_id)
                    setSelectedCandidate(null)
                  }}
                  className="flex-1 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white px-6 py-2.5 rounded-lg font-semibold text-sm transition-all duration-200 flex items-center justify-center gap-2 shadow-md shadow-green-500/25 hover:shadow-lg hover:shadow-green-500/40 hover:scale-[1.02] active:scale-[0.98]"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Shortlist</span>
                </button>
                <button
                  onClick={() => {
                    navigate(`/recruiter/feedback/${selectedCandidate.candidate_id}`)
                  }}
                  className="flex-1 px-4 py-2.5 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium text-sm transition-all duration-200 flex items-center justify-center gap-2 hover:scale-[1.02] active:scale-[0.98]"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                  <span>Feedback</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Full-screen Loading Overlay with animated gradient blobs */}
      {showLoadingOverlay && (
        <BlobLoadingOverlay
          title="Generating AI Shortlist"
          description="Analyzing candidates and matching with job requirements..."
          variant="recruiter"
        />
      )}
    </div>
  )
}
