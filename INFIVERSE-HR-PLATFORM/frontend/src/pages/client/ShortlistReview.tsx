import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { 
  getJobById, 
  getTopMatches, 
  reviewCandidate,
  type Job,
  type MatchResult
} from '../../services/api'
import Table from '../../components/Table'
import Loading from '../../components/Loading'

export default function ShortlistReview() {
  const { jobId } = useParams()
  const navigate = useNavigate()
  const [job, setJob] = useState<Job | null>(null)
  const [candidates, setCandidates] = useState<MatchResult[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'high' | 'medium'>('all')

  useEffect(() => {
    loadData()
  }, [jobId])

  const loadData = async () => {
    try {
      setLoading(true)
      const [jobData, matchResults] = await Promise.all([
        getJobById(jobId!).catch(() => null),
        getTopMatches(jobId!, 20).catch(() => [])
      ])
      setJob(jobData)
      setCandidates(matchResults)
    } catch (error) {
      console.error('Failed to load data:', error)
      toast.error('Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (candidateId: string) => {
    try {
      await reviewCandidate(candidateId, 'approved', 'Approved by client for interview')
      toast.success('Candidate approved for interview')
      loadData()
    } catch (error) {
      toast.error('Failed to approve candidate')
    }
  }

  const handleReject = async (candidateId: string) => {
    try {
      await reviewCandidate(candidateId, 'rejected', 'Rejected by client')
      toast.success('Candidate rejected')
      loadData()
    } catch (error) {
      toast.error('Failed to reject candidate')
    }
  }

  const handleRequestMore = () => {
    toast.success('Request sent to recruitment team for more profiles')
  }

  const filteredCandidates = candidates.filter(c => {
    if (filter === 'high') return c.match_score >= 80
    if (filter === 'medium') return c.match_score >= 60 && c.match_score < 80
    return true
  })

  if (loading) {
    return <Loading message="Loading shortlist..." />
  }

  return (
    <div>
      <div className="mb-8 p-6 rounded-2xl bg-gradient-to-r from-purple-500/5 to-pink-500/5 dark:from-purple-500/10 dark:to-pink-500/10 backdrop-blur-xl border border-purple-300/20 dark:border-purple-500/20">
        <button
          onClick={() => navigate('/client')}
          className="text-purple-400 hover:text-purple-300 mb-4 flex items-center space-x-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          <span>Back to Dashboard</span>
        </button>
        <h1 className="page-title">Shortlist Review</h1>
        <p className="text-gray-400">{job?.title} - {job?.location}</p>
      </div>

      {/* Job Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="card">
          <p className="text-gray-400 text-sm mb-1">Total Candidates</p>
          <p className="text-3xl font-bold text-white">{candidates.length}</p>
        </div>
        <div className="card">
          <p className="text-gray-400 text-sm mb-1">High Match (80%+)</p>
          <p className="text-3xl font-bold text-green-400">
            {candidates.filter(c => c.match_score >= 80).length}
          </p>
        </div>
        <div className="card">
          <p className="text-gray-400 text-sm mb-1">Medium Match (60-80%)</p>
          <p className="text-3xl font-bold text-yellow-400">
            {candidates.filter(c => c.match_score >= 60 && c.match_score < 80).length}
          </p>
        </div>
        <div className="card">
          <p className="text-gray-400 text-sm mb-1">Avg. Match Score</p>
          <p className="text-3xl font-bold text-blue-400">
            {candidates.length > 0 
              ? Math.round(candidates.reduce((sum, c) => sum + c.match_score, 0) / candidates.length)
              : 0}%
          </p>
        </div>
      </div>

      {/* Filters and Actions */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex space-x-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            All ({candidates.length})
          </button>
          <button
            onClick={() => setFilter('high')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'high' ? 'bg-green-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            High Match ({candidates.filter(c => c.match_score >= 80).length})
          </button>
          <button
            onClick={() => setFilter('medium')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filter === 'medium' ? 'bg-yellow-600 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
            }`}
          >
            Medium Match ({candidates.filter(c => c.match_score >= 60 && c.match_score < 80).length})
          </button>
        </div>

        <button onClick={handleRequestMore} className="btn-primary">
          Request More Profiles
        </button>
      </div>

      {/* Candidates Table */}
      <div className="card">
        <Table
          columns={['Candidate', 'Experience', 'Location', 'Key Skills', 'Match %', 'Actions']}
          data={filteredCandidates}
          renderRow={(candidate) => (
            <>
              <td>
                <div>
                  <p className="font-medium text-white">{candidate.candidate_name}</p>
                  <p className="text-sm text-gray-400">{candidate.email}</p>
                </div>
              </td>
              <td>{candidate.experience_match}%</td>
              <td>{candidate.location_match}%</td>
              <td>
                <div className="flex flex-wrap gap-1">
                  {candidate.matched_skills.slice(0, 2).map((skill: string, idx: number) => (
                    <span
                      key={idx}
                      className="px-2 py-1 bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 rounded text-xs"
                    >
                      {skill}
                    </span>
                  ))}
                  {candidate.matched_skills.length > 2 && (
                    <span className="px-2 py-1 bg-gray-700 text-gray-300 rounded text-xs">
                      +{candidate.matched_skills.length - 2}
                    </span>
                  )}
                </div>
              </td>
              <td>
                <div className="flex items-center space-x-2">
                  <div className="w-16 bg-gray-700 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        candidate.match_score >= 80 ? 'bg-green-500' :
                        candidate.match_score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${candidate.match_score}%` }}
                    />
                  </div>
                  <span className={`font-bold text-sm ${
                    candidate.match_score >= 80 ? 'text-green-400' :
                    candidate.match_score >= 60 ? 'text-yellow-400' : 'text-red-400'
                  }`}>
                    {candidate.match_score}%
                  </span>
                </div>
              </td>
              <td>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleApprove(candidate.candidate_id)}
                    className="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-white text-sm font-medium transition-colors"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => handleReject(candidate.candidate_id)}
                    className="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-white text-sm font-medium transition-colors"
                  >
                    Reject
                  </button>
                </div>
              </td>
            </>
          )}
        />
      </div>
    </div>
  )
}
