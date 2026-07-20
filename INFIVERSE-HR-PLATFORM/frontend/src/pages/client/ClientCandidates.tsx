import { useState, useEffect } from 'react'
import { getClientJobs, getCandidatesForJobReview, Job, MatchResult } from '../../services/api'
import Loading from '../../components/Loading'

export default function ClientCandidates() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [selectedJobId, setSelectedJobId] = useState<string>('')
  const [candidates, setCandidates] = useState<MatchResult[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingCandidates, setLoadingCandidates] = useState(false)

  useEffect(() => {
    loadJobs()
  }, [])

  useEffect(() => {
    if (selectedJobId) {
      loadCandidates(selectedJobId)
    }
    // Auto-refresh every 30 seconds for real-time data
    const interval = setInterval(() => {
      if (selectedJobId) {
        loadCandidates(selectedJobId)
      }
    }, 30000)
    return () => clearInterval(interval)
  }, [selectedJobId])

  const loadJobs = async () => {
    try {
      setLoading(true)
      const jobsData = await getClientJobs()
      setJobs(jobsData)
      if (jobsData.length > 0) {
        setSelectedJobId(jobsData[0].id)
      }
    } catch (error) {
      console.error('Failed to load jobs:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadCandidates = async (jobId: string) => {
    try {
      setLoadingCandidates(true)
      const matches = await getCandidatesForJobReview(jobId)
      setCandidates(matches)
    } catch (error) {
      console.error('Failed to load candidates:', error)
      setCandidates([])
    } finally {
      setLoadingCandidates(false)
    }
  }

  if (loading) {
    return <Loading message="Loading jobs..." />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-500/5 to-indigo-500/5 dark:from-blue-500/10 dark:to-indigo-500/10 backdrop-blur-xl border border-blue-300/20 dark:border-blue-500/20 mb-8">
        <h1 className="page-title">Review Candidates</h1>
        <p className="page-subtitle">Select a job to review and evaluate candidates</p>
      </div>

      {/* Job Selection */}
      <div className="card">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Select Job
        </label>
        <select
          value={selectedJobId}
          onChange={(e) => setSelectedJobId(e.target.value)}
          className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent text-lg"
        >
          {jobs.map((job) => (
            <option key={job.id} value={job.id}>
              {job.title} (ID: {job.id})
            </option>
          ))}
        </select>
      </div>

      {/* Candidates List */}
      {loadingCandidates ? (
        <Loading message="Loading candidates..." />
      ) : candidates.length === 0 ? (
        <div className="card text-center py-12">
          <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
          <p className="text-gray-500 dark:text-gray-400 text-lg">No candidates found for this job</p>
        </div>
      ) : (
        <div className="space-y-4">
          {candidates.map((candidate, index) => (
            <div
              key={candidate.candidate_id || index}
              className="card hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
                      {candidate.candidate_name?.charAt(0).toUpperCase() || 'C'}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {candidate.candidate_name || 'Unknown Candidate'}
                      </h3>
                      <p className="text-gray-600 dark:text-gray-400">{candidate.email}</p>
                    </div>
                  </div>

                  {/* Match Score */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Match Score</span>
                      <span className="text-lg font-bold text-purple-600 dark:text-purple-400">
                        {Math.round(candidate.match_score || 0)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                      <div
                        className="bg-gradient-to-r from-purple-500 to-pink-500 h-3 rounded-full transition-all duration-300"
                        style={{ width: `${candidate.match_score || 0}%` }}
                      />
                    </div>
                  </div>

                  {/* Skills Match */}
                  {candidate.matched_skills && candidate.matched_skills.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Matched Skills</p>
                      <div className="flex flex-wrap gap-2">
                        {candidate.matched_skills.map((skill, idx) => (
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

                  {/* Missing Skills */}
                  {candidate.missing_skills && candidate.missing_skills.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Missing Skills</p>
                      <div className="flex flex-wrap gap-2">
                        {candidate.missing_skills.map((skill, idx) => (
                          <span
                            key={idx}
                            className="px-3 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 rounded-full text-sm"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recommendation */}
                  {candidate.recommendation && (
                    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                      <p className="text-sm text-blue-800 dark:text-blue-300">
                        <span className="font-semibold">Recommendation:</span> {candidate.recommendation}
                      </p>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="ml-4 flex flex-col gap-2">
                  <button className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors text-sm font-medium">
                    Approve
                  </button>
                  <button className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors text-sm font-medium">
                    Reject
                  </button>
                  <button className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors text-sm font-medium">
                    View Profile
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

