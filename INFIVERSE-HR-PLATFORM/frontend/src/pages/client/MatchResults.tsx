import { useState, useEffect } from 'react'
import { useParams, useSearchParams, useNavigate } from 'react-router-dom'
import { getClientJobs, getTopMatches, getJobById, shortlistCandidate, rejectCandidate, scheduleInterview, Job, MatchResult } from '../../services/api'
import Loading from '../../components/Loading'
import BlobLoadingOverlay from '../../components/BlobLoadingOverlay'
import { toast } from 'react-hot-toast'

export default function MatchResults() {
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

  useEffect(() => {
    setJobId(effectiveJobId)
  }, [effectiveJobId])

  // Load only client's jobs for dropdown
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

  // Auto-refresh match list every 30 seconds (background only; no overlay or generating state)
  useEffect(() => {
    if (!jobId) return
    const interval = setInterval(() => {
      loadMatches(jobId, false)
    }, 30000)
    return () => clearInterval(interval)
  }, [jobId])

  const loadJobs = async () => {
    try {
      setLoading(true)
      const jobsData = await getClientJobs()
      setJobs(jobsData)
    } catch (error) {
      console.error('Failed to load client jobs:', error)
      toast.error('Failed to load jobs')
    } finally {
      setLoading(false)
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

  // Refresh button: only reload jobs list and current job details
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

  // Full reload including match results
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
      toast.error('Failed to load candidates')
    } finally {
      setLoading(false)
    }
  }

  const loadMatches = async (jobIdParam: string, showOverlay = true) => {
    if (showOverlay) setGenerating(true)
    try {
      const matchResults = await getTopMatches(jobIdParam, 20)
      setCandidates(matchResults)
      if (showOverlay) {
        if (matchResults.length === 0) {
          toast('No candidates found for this job. Try uploading candidates or check back later.', { icon: '⚠' })
        } else {
          toast.success(`Found ${matchResults.length} matched candidates`)
        }
      }
    } catch (error) {
      console.error('Failed to load matches:', error)
      if (showOverlay) toast.error('Failed to load AI matches')
      setCandidates([])
    } finally {
      if (showOverlay) setGenerating(false)
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

  const handleGetMatches = () => {
    if (jobId) {
      loadMatches(jobId, true)
    } else {
      toast.error('Please select a job first')
    }
  }

  if (loading) {
    return <Loading message="Loading jobs..." />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-500/5 to-indigo-500/5 dark:from-blue-500/10 dark:to-indigo-500/10 backdrop-blur-xl border border-blue-300/20 dark:border-blue-500/20 mb-8">
        <h1 className="page-title">AI Match Results</h1>
        <p className="page-subtitle">Get AI-powered candidate matches for your job postings</p>
      </div>

      {/* Job Selection */}
      <div className="card">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Select Job for AI Matching
        </label>
        <div className="flex gap-4">
          <select
            value={jobId}
            onChange={(e) => {
              setJobId(e.target.value)
              setJob(null)
              setCandidates([])
            }}
            className="flex-1 px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent text-lg"
          >
            {jobs.map((job) => (
              <option key={job.id} value={job.id}>
                {job.title} (ID: {job.id})
              </option>
            ))}
          </select>
          <button
            onClick={handleGetMatches}
            disabled={generating || !jobId}
            className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all duration-200 shadow-lg shadow-purple-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {generating ? (
              <>
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Loading...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Get AI Matches
              </>
            )}
          </button>
          <button
            onClick={handleRefresh}
            disabled={loading || generating}
            className="px-4 py-3 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium transition-all duration-200 flex items-center gap-2 hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Matches Results */}
      {loading ? (
        <Loading message="Loading candidates..." />
      ) : candidates.length === 0 ? (
        <div className="card text-center py-12">
          <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-gray-500 dark:text-gray-400 text-lg">No candidates found. Click "Get AI Matches" to find candidates.</p>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title">
              Top {candidates.length} Matches
            </h2>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Sorted by match score
            </span>
          </div>

          {candidates.map((match: MatchResult, index: number) => (
            <div
              key={match.candidate_id || index}
              className="card hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
                      {match.candidate_name?.charAt(0).toUpperCase() || 'C'}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                          {match.candidate_name || 'Unknown Candidate'}
                        </h3>
                        <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300 rounded-full text-xs font-semibold">
                          #{index + 1}
                        </span>
                      </div>
                      <p className="text-gray-600 dark:text-gray-400">{match.email}</p>
                    </div>
                  </div>

                  {/* Match Score */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Overall Match Score</span>
                      <span className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                        {Math.round(match.match_score || 0)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                      <div
                        className="bg-gradient-to-r from-purple-500 to-pink-500 h-4 rounded-full transition-all duration-300"
                        style={{ width: `${match.match_score || 0}%` }}
                      />
                    </div>
                  </div>

                  {/* Detailed Scores */}
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Skills Match</p>
                      <p className="text-lg font-bold text-blue-600 dark:text-blue-400">
                        {Math.round(match.skills_match || 0)}%
                      </p>
                    </div>
                    <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Experience</p>
                      <p className="text-lg font-bold text-green-600 dark:text-green-400">
                        {Math.round(match.experience_match || 0)}%
                      </p>
                    </div>
                    <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                      <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">Location</p>
                      <p className="text-lg font-bold text-yellow-600 dark:text-yellow-400">
                        {Math.round(match.location_match || 0)}%
                      </p>
                    </div>
                  </div>

                  {/* Matched Skills */}
                  {match.matched_skills && match.matched_skills.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Matched Skills</p>
                      <div className="flex flex-wrap gap-2">
                        {match.matched_skills.map((skill, idx) => (
                          <span
                            key={idx}
                            className="px-3 py-1 bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300 rounded-full text-sm"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recommendation */}
                  {match.recommendation && (
                    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                      <p className="text-sm text-blue-800 dark:text-blue-300">
                        <span className="font-semibold">AI Recommendation:</span> {match.recommendation}
                      </p>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="ml-4 flex flex-col gap-2">
                  <button
                    onClick={() => setSelectedCandidate(match)}
                    className="px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg text-blue-600 dark:text-blue-400 transition-colors text-sm font-medium"
                  >
                    View Details
                  </button>
                  <button
                    onClick={() => handleShortlist(match.candidate_id)}
                    className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors text-sm font-medium"
                  >
                    Shortlist
                  </button>
                  <button
                    onClick={() => handleScheduleInterview(match.candidate_id)}
                    className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors text-sm font-medium"
                  >
                    Schedule Interview
                  </button>
                  <button
                    onClick={() => navigate(`/client/feedback/${match.candidate_id}`)}
                    className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg transition-colors text-sm font-medium"
                  >
                    Add Feedback
                  </button>
                  <button
                    onClick={() => handleReject(match.candidate_id)}
                    className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors text-sm font-medium"
                  >
                    Reject
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Full-screen Loading Overlay with animated gradient blobs (same as AI Shortlist page) */}
      {generating && (
        <BlobLoadingOverlay
          title="Getting AI Matches"
          description="Finding the best candidates for your job..."
          variant="recruiter"
        />
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
                  <p className="text-gray-900 dark:text-white font-semibold mt-1">{selectedCandidate.matched_skills?.length || 0}</p>
                </div>
              </div>

              {/* Skills */}
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">Matched Skills</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedCandidate.matched_skills?.map((skill: string, idx: number) => (
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
                    navigate(`/client/feedback/${selectedCandidate.candidate_id}`)
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
    </div>
  )
}
