import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { ExecutiveMetricCard } from '../../components/cards'
import { 
  getCandidateDashboardStats, 
  getCandidateApplications, 
  getInterviews,
  type DashboardStats,
  type Application,
  type Interview 
} from '../../services/api'
import { useAuth } from '../../context/AuthContext'
import { authStorage } from '../../utils/authStorage'

export default function CandidateDashboard() {
  const navigate = useNavigate()
  const { userName: authUserName } = useAuth()
  const userName = authUserName || authStorage.getItem('user_name') || 'Candidate'

  const [stats, setStats] = useState<DashboardStats>({
    total_applications: 0,
    interviews_scheduled: 0,
    profile_views: 0,
    shortlisted: 0,
    offers_received: 0
  })
  const [recentApplications, setRecentApplications] = useState<Application[]>([])
  const [upcomingInterviews, setUpcomingInterviews] = useState<Interview[]>([])
  const [loading, setLoading] = useState(true)
  // Only trust token that was present at mount; do not set authReady from user updates,
  // since AuthContext may set user before token verification completes during signup.
  const [authReady] = useState(() => !!authStorage.getItem('auth_token'))

  useEffect(() => {
    const currentBackendId = authStorage.getItem('backend_candidate_id')
    if (!authReady || !currentBackendId) {
      setLoading(false)
      return
    }
    loadDashboardData()
  }, [authReady])

  const loadDashboardData = async () => {
    const token = authStorage.getItem('auth_token')
    const currentBackendId = authStorage.getItem('backend_candidate_id')
    if (!currentBackendId || !token) {
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      const [statsData, applicationsData, interviewsData] = await Promise.all([
        getCandidateDashboardStats(currentBackendId),
        getCandidateApplications(currentBackendId),
        getInterviews(currentBackendId)
      ])
      
      setStats(statsData)
      setRecentApplications(applicationsData.slice(0, 3))
      setUpcomingInterviews(interviewsData.filter(i => i.status === 'scheduled').slice(0, 2))
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
      toast.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  const statCards = [
    { label: 'Applied Jobs', value: stats.total_applications, color: 'from-blue-500 to-cyan-500' },
    { label: 'Interviews', value: stats.interviews_scheduled, color: 'from-emerald-500 to-teal-500' },
    { label: 'Shortlisted', value: stats.shortlisted, color: 'from-amber-500 to-orange-500' },
    { label: 'Offers', value: stats.offers_received, color: 'from-purple-500 to-pink-500' },
  ]

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      applied: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      screening: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
      shortlisted: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
      interview: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
      offer: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400',
      rejected: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    }
    return colors[status.toLowerCase()] || colors.applied
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric' 
    })
  }

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="p-4 sm:p-6 rounded-2xl bg-gradient-to-r from-blue-500/5 to-cyan-500/5 dark:from-blue-500/10 dark:to-cyan-500/10 backdrop-blur-xl border border-blue-300/20 dark:border-blue-500/20">
        <h1 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 dark:text-white mb-2">Welcome back, {userName}</h1>
        <p className="text-sm sm:text-base text-gray-500 dark:text-gray-400">Track your job applications and upcoming interviews</p>
        <div className="mt-4 sm:mt-6 flex flex-col sm:flex-row gap-3">
          <button 
            onClick={() => navigate('/candidate/jobs')}
            className="px-4 sm:px-6 py-2.5 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors text-sm sm:text-base"
          >
            Browse Jobs
          </button>
          <button 
            onClick={() => navigate('/candidate/profile')}
            className="px-4 sm:px-6 py-2.5 bg-blue-50/50 dark:bg-blue-900/20 backdrop-blur-sm text-blue-700 dark:text-blue-300 font-semibold rounded-lg hover:bg-blue-100/50 dark:hover:bg-blue-800/30 transition-colors border border-blue-200/30 dark:border-blue-500/20 text-sm sm:text-base"
          >
            Update Profile
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 md:gap-6">
        {statCards.map((stat) => (
          <ExecutiveMetricCard
            key={stat.label}
            label={stat.label}
            value={loading ? '…' : stat.value}
            sourceSystem="candidate-portal"
            readOnly
          />
        ))}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Applications */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 sm:p-6 shadow-sm border border-gray-100 dark:border-slate-700">
          <div className="flex items-center justify-between mb-4 sm:mb-6">
            <h2 className="text-lg sm:text-xl font-heading font-bold text-gray-900 dark:text-white">Recent Applications</h2>
            <button
              onClick={() => navigate('/candidate/applied-jobs')}
              className="text-blue-500 hover:text-blue-600 text-sm font-medium"
            >
              View All →
            </button>
          </div>
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3].map(i => (
                <div key={i} className="p-4 bg-gray-50 dark:bg-slate-700/50 rounded-xl animate-pulse">
                  <div className="h-4 bg-gray-200 dark:bg-slate-600 rounded w-2/3 mb-2"></div>
                  <div className="h-3 bg-gray-200 dark:bg-slate-600 rounded w-1/3"></div>
                </div>
              ))}
            </div>
          ) : recentApplications.length === 0 ? (
            <div className="text-center py-8">
              <svg className="w-12 h-12 mx-auto text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-gray-500 dark:text-gray-400">No applications yet</p>
              <button
                onClick={() => navigate('/candidate/jobs')}
                className="mt-3 text-blue-500 hover:text-blue-600 font-medium text-sm"
              >
                Start applying →
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {recentApplications.map((app) => (
                <div
                  key={app.id}
                  onClick={() => navigate('/candidate/applied-jobs')}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-700/50 rounded-xl hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors cursor-pointer"
                >
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">{app.job_title}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{app.company || 'Company'}</p>
                  </div>
                  <div className="text-right">
                    <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(app.status)}`}>
                      {app.status.charAt(0).toUpperCase() + app.status.slice(1)}
                    </span>
                    <p className="text-xs text-gray-400 mt-1">{formatDate(app.applied_date)}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Upcoming Interviews */}
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 sm:p-6 shadow-sm border border-gray-100 dark:border-slate-700">
          <div className="flex items-center justify-between mb-4 sm:mb-6">
            <h2 className="text-lg sm:text-xl font-heading font-bold text-gray-900 dark:text-white">Upcoming Interviews</h2>
            <button
              onClick={() => navigate('/candidate/interviews')}
              className="text-blue-500 hover:text-blue-600 text-sm font-medium"
            >
              View All →
            </button>
          </div>
          {loading ? (
            <div className="space-y-4">
              {[1, 2].map(i => (
                <div key={i} className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-xl animate-pulse">
                  <div className="h-4 bg-blue-100 dark:bg-blue-800 rounded w-2/3 mb-2"></div>
                  <div className="h-3 bg-blue-100 dark:bg-blue-800 rounded w-1/3"></div>
                </div>
              ))}
            </div>
          ) : upcomingInterviews.length === 0 ? (
            <div className="text-center py-8">
              <svg className="w-12 h-12 mx-auto text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <p className="text-gray-500 dark:text-gray-400">No upcoming interviews</p>
              <p className="text-xs text-gray-400 mt-1">Keep applying to get interviews!</p>
            </div>
          ) : (
            <div className="space-y-4">
              {upcomingInterviews.map((interview) => (
                <div
                  key={interview.id}
                  className="p-4 bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 rounded-xl border border-blue-100 dark:border-blue-800"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-semibold text-gray-900 dark:text-white">{interview.job_title}</p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{interview.company || 'Company'}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-blue-600 dark:text-blue-400">
                        {formatDate(interview.scheduled_date)}
                      </p>
                      {interview.scheduled_time && (
                        <p className="text-sm text-gray-500 dark:text-gray-400">{interview.scheduled_time}</p>
                      )}
                    </div>
                  </div>
                  {interview.meeting_link && (
                    <div className="mt-4 flex gap-2">
                      <a
                        href={interview.meeting_link}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex-1 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm font-medium rounded-lg transition-colors text-center"
                      >
                        Join Meeting
                      </a>
                      <button 
                        onClick={() => navigate('/candidate/interviews')}
                        className="px-4 py-2 bg-white dark:bg-slate-700 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-lg hover:bg-gray-50 dark:hover:bg-slate-600 transition-colors border border-gray-200 dark:border-slate-600"
                      >
                        Details
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white dark:bg-slate-800 rounded-2xl p-4 sm:p-6 shadow-sm border border-gray-100 dark:border-slate-700">
        <h2 className="text-lg sm:text-xl font-heading font-bold text-gray-900 dark:text-white mb-4 sm:mb-6">Quick Actions</h2>
        <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-5 gap-3 sm:gap-4">
          <button
            onClick={() => navigate('/candidate/profile')}
            className="p-4 bg-gradient-to-br from-gray-50 to-gray-100 dark:from-slate-700/50 dark:to-slate-700 rounded-xl hover:shadow-md transition-all text-center group"
          >
            <svg className="w-8 h-8 mx-auto mb-2 text-gray-600 dark:text-gray-300 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Update Profile</span>
          </button>
          <button
            onClick={() => navigate('/candidate/jobs')}
            className="p-4 bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 rounded-xl hover:shadow-md transition-all text-center group"
          >
            <svg className="w-8 h-8 mx-auto mb-2 text-blue-600 dark:text-blue-400 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Browse Jobs</span>
          </button>
          <button
            onClick={() => navigate('/candidate/applied-jobs')}
            className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-xl hover:shadow-md transition-all text-center group"
          >
            <svg className="w-8 h-8 mx-auto mb-2 text-purple-600 dark:text-purple-400 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Track Applications</span>
          </button>
          <button
            onClick={() => navigate('/candidate/tasks')}
            className="p-4 bg-gradient-to-br from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 rounded-xl hover:shadow-md transition-all text-center group"
          >
            <svg className="w-8 h-8 mx-auto mb-2 text-emerald-600 dark:text-emerald-400 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">My Tasks</span>
          </button>
          <button
            onClick={() => navigate('/candidate/feedback')}
            className="p-4 bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-xl hover:shadow-md transition-all text-center group"
          >
            <svg className="w-8 h-8 mx-auto mb-2 text-amber-600 dark:text-amber-400 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" /></svg>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">View Feedback</span>
          </button>
        </div>
      </div>
    </div>
  )
}
