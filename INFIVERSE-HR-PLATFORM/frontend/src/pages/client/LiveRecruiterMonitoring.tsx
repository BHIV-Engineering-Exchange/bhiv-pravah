import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { getClientJobs } from '../../services/api'
import Loading from '../../components/Loading'

export default function LiveRecruiterMonitoring() {
  const navigate = useNavigate()
  const [jobs, setJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedClient, setSelectedClient] = useState<string>('all')

  useEffect(() => {
    loadJobs()
    // Auto-refresh every 30 seconds for real-time data
    const interval = setInterval(loadJobs, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadJobs = async () => {
    try {
      setLoading(true)
      const jobsData = await getClientJobs()
      setJobs(jobsData)
    } catch (error) {
      console.error('Failed to load jobs:', error)
      toast.error('Failed to load jobs')
    } finally {
      setLoading(false)
    }
  }

  // Group jobs by client
  const clientJobsMap: Record<string, any[]> = {}
  jobs.forEach(job => {
    const clientId = job.client_id || 'Unknown'
    if (!clientJobsMap[clientId]) {
      clientJobsMap[clientId] = []
    }
    clientJobsMap[clientId].push(job)
  })

  const clients = Object.keys(clientJobsMap).sort()
  const totalJobs = jobs.length
  const activeClients = clients.length
  const recentJobs = jobs.filter(job => {
    if (!job.created_at) return false
    const jobDate = new Date(job.created_at)
    const thirtyDaysAgo = new Date()
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30)
    return jobDate >= thirtyDaysAgo
  }).length

  const filteredJobs = selectedClient === 'all' 
    ? jobs 
    : jobs.filter(job => String(job.client_id || 'Unknown') === selectedClient)

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
      closed: 'bg-gray-100 text-gray-700 dark:bg-gray-900/30 dark:text-gray-400',
      draft: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
    }
    return colors[status?.toLowerCase()] || colors.active
  }

  if (loading) {
    return <Loading message="Loading jobs..." />
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-green-500/5 to-emerald-500/5 dark:from-green-500/10 dark:to-emerald-500/10 backdrop-blur-xl border border-green-300/20 dark:border-green-500/20">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="page-title">Live Recruiter Monitoring</h1>
            <p className="text-gray-600 dark:text-gray-400">Real-time view of jobs posted by recruiters for your organization</p>
          </div>
          <button
            onClick={loadJobs}
            className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="card bg-blue-50 dark:bg-blue-900/20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Jobs</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">{totalJobs}</p>
            </div>
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
        </div>

        <div className="card bg-purple-50 dark:bg-purple-900/20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Clients</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">{activeClients}</p>
            </div>
            <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
          </div>
        </div>

        <div className="card bg-emerald-50 dark:bg-emerald-900/20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Recent Jobs (30 days)</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">{recentJobs}</p>
            </div>
            <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* Client Filter */}
      <div className="card">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Filter by Client
            </label>
            <select
              value={selectedClient}
              onChange={(e) => setSelectedClient(e.target.value)}
              className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-green-500"
            >
              <option value="all">All Recruiters</option>
              {clients.map((clientId) => (
                <option key={clientId} value={clientId}>
                  Recruiter {clientId} ({clientJobsMap[clientId].length} jobs)
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Jobs by Client */}
      {selectedClient === 'all' ? (
        <div className="space-y-6">
          {clients.map((clientId) => (
            <div key={clientId} className="card">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
                Recruiter {clientId} ({clientJobsMap[clientId].length} jobs)
              </h2>
              <div className="space-y-4">
                {clientJobsMap[clientId].map((job) => (
                  <div
                    key={job.id}
                    className="p-6 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-200 dark:border-gray-700"
                  >
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">
                          {job.title || 'Untitled Job'} - {job.department || 'N/A'}
                        </h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <p className="text-gray-500 dark:text-gray-400">Job ID</p>
                            <p className="font-semibold text-gray-900 dark:text-white">{job.id || 'N/A'}</p>
                          </div>
                          <div>
                            <p className="text-gray-500 dark:text-gray-400">Department</p>
                            <p className="font-semibold text-gray-900 dark:text-white">{job.department || 'N/A'}</p>
                          </div>
                          <div>
                            <p className="text-gray-500 dark:text-gray-400">Location</p>
                            <p className="font-semibold text-gray-900 dark:text-white">{job.location || 'N/A'}</p>
                          </div>
                          <div>
                            <p className="text-gray-500 dark:text-gray-400">Experience</p>
                            <p className="font-semibold text-gray-900 dark:text-white">{job.experience_level || 'N/A'}</p>
                          </div>
                          <div>
                            <p className="text-gray-500 dark:text-gray-400">Type</p>
                            <p className="font-semibold text-gray-900 dark:text-white">{job.employment_type || 'N/A'}</p>
                          </div>
                          <div>
                            <p className="text-gray-500 dark:text-gray-400">Status</p>
                            <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                              {job.status || 'active'}
                            </span>
                          </div>
                          <div>
                            <p className="text-gray-500 dark:text-gray-400">Posted</p>
                            <p className="font-semibold text-gray-900 dark:text-white">
                              {job.created_at ? new Date(job.created_at).toLocaleDateString() : 'Unknown'}
                            </p>
                          </div>
                        </div>
                        {job.description && (
                          <div className="mt-4">
                            <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Description</p>
                            <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                              {job.description.substring(0, 300)}...
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-3 mt-4">
                      <button
                        onClick={() => navigate(`/recruiter/applicants/${job.id}`)}
                        className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors text-sm"
                      >
                        Get AI Matches
                      </button>
                      <button
                        onClick={() => navigate(`/recruiter/applicants/${job.id}`)}
                        className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors text-sm"
                      >
                        View Candidates
                      </button>
                      <button
                        onClick={() => navigate(`/recruiter`)}
                        className="px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg font-medium transition-colors text-sm"
                      >
                        Analytics
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            Recruiter {selectedClient} ({clientJobsMap[selectedClient]?.length || 0} jobs)
          </h2>
          {filteredJobs.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 dark:text-gray-400">No jobs found for this client</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredJobs.map((job) => (
                <div
                  key={job.id}
                  className="p-6 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-200 dark:border-gray-700"
                >
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                    {job.title || 'Untitled Job'} - {job.department || 'N/A'}
                  </h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm mb-4">
                    <div>
                      <p className="text-gray-500 dark:text-gray-400">Location</p>
                      <p className="font-semibold text-gray-900 dark:text-white">{job.location || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-gray-500 dark:text-gray-400">Experience</p>
                      <p className="font-semibold text-gray-900 dark:text-white">{job.experience_level || 'N/A'}</p>
                    </div>
                    <div>
                      <p className="text-gray-500 dark:text-gray-400">Status</p>
                      <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                        {job.status || 'active'}
                      </span>
                    </div>
                    <div>
                      <p className="text-gray-500 dark:text-gray-400">Posted</p>
                      <p className="font-semibold text-gray-900 dark:text-white">
                        {job.created_at ? new Date(job.created_at).toLocaleDateString() : 'Unknown'}
                      </p>
                    </div>
                  </div>
                  {job.description && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                      {job.description.substring(0, 300)}...
                    </p>
                  )}
                  <div className="flex gap-3">
                    <button
                      onClick={() => navigate(`/recruiter/applicants/${job.id}`)}
                      className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg font-medium transition-colors text-sm"
                    >
                      Get AI Matches
                    </button>
                    <button
                      onClick={() => navigate(`/recruiter/applicants/${job.id}`)}
                      className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors text-sm"
                    >
                      View Candidates
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {jobs.length === 0 && (
        <div className="card text-center py-12">
          <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-gray-500 dark:text-gray-400 text-lg">No jobs found</p>
          <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">Recruiters haven't posted any jobs for your organization yet</p>
        </div>
      )}
    </div>
  )
}

