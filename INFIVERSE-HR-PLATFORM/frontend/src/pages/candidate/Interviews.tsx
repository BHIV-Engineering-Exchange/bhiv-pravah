import { useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { getInterviews, type Interview } from '../../services/api'
import { useAuth } from '../../context/AuthContext'
import { authStorage } from '../../utils/authStorage'

export default function CandidateInterviews() {
  const { user } = useAuth()
  const [interviews, setInterviews] = useState<Interview[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadInterviews()
  }, [user])

  const loadInterviews = async () => {
    const isAuthenticated = authStorage.getItem('isAuthenticated') === 'true' || !!user
    if (!isAuthenticated) {
      toast.error('Please login to view interviews')
      setLoading(false)
      return
    }

    const candidateId = authStorage.getItem('backend_candidate_id')
    if (!candidateId) {
      setInterviews([])
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      const interviewsData = await getInterviews(candidateId)
      setInterviews(interviewsData)
    } catch (error) {
      console.error('Failed to load interviews:', error)
      setInterviews([])
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateStr: string) =>
    new Date(dateStr).toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })

  const getInterviewStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      scheduled: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
      completed: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
      cancelled: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
      rescheduled: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    }
    return colors[status] || colors.scheduled
  }

  const { upcomingInterviews, pastInterviews } = useMemo(() => {
    const now = new Date()
    const upcoming = interviews.filter((i) => i.status === 'scheduled' && new Date(i.scheduled_date) > now)
    const past = interviews.filter((i) => i.status !== 'scheduled' || new Date(i.scheduled_date) <= now)
    return { upcomingInterviews: upcoming, pastInterviews: past }
  }, [interviews])

  return (
    <div className="space-y-6">
      <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-500/5 to-cyan-500/5 dark:from-blue-500/10 dark:to-cyan-500/10 backdrop-blur-xl border border-blue-300/20 dark:border-blue-500/20">
        <h1 className="page-title">Interviews</h1>
        <p className="page-subtitle">Track your upcoming and completed interviews</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-slate-700">
          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{upcomingInterviews.length}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Upcoming Interviews</p>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-slate-700">
          <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{pastInterviews.length}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400">Completed / Past</p>
        </div>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white dark:bg-slate-800 rounded-xl p-6 animate-pulse">
              <div className="h-5 bg-gray-200 dark:bg-slate-700 rounded w-1/3 mb-3" />
              <div className="h-4 bg-gray-200 dark:bg-slate-700 rounded w-1/2" />
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-6">
          {upcomingInterviews.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Upcoming Interviews</h3>
              <div className="space-y-4">
                {upcomingInterviews.map((interview) => (
                  <div
                    key={interview.id}
                    className="bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 rounded-xl p-6 border border-blue-100 dark:border-blue-800"
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div>
                        <h4 className="text-xl font-bold text-gray-900 dark:text-white">{interview.job_title}</h4>
                        <p className="text-gray-600 dark:text-gray-400">{interview.company || 'Company'}</p>
                        <p className="text-sm mt-2 text-blue-600 dark:text-blue-400">{formatDate(interview.scheduled_date)}</p>
                        {interview.scheduled_time && (
                          <p className="text-sm text-cyan-600 dark:text-cyan-400">{interview.scheduled_time}</p>
                        )}
                        <p className="text-sm mt-1 text-gray-500 dark:text-gray-400">
                          {interview.interview_type || 'Video Call'}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getInterviewStatusColor(interview.status)}`}>
                          {interview.status.charAt(0).toUpperCase() + interview.status.slice(1)}
                        </span>
                        {interview.meeting_link && (
                          <a
                            href={interview.meeting_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg transition-colors"
                          >
                            Join Meeting
                          </a>
                        )}
                      </div>
                    </div>
                    {interview.notes && (
                      <div className="mt-4 pt-4 border-t border-blue-100 dark:border-blue-800">
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          <span className="font-medium">Notes:</span> {interview.notes}
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {pastInterviews.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Past Interviews</h3>
              <div className="space-y-4">
                {pastInterviews.map((interview) => (
                  <div
                    key={interview.id}
                    className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-slate-700"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="font-semibold text-gray-900 dark:text-white">{interview.job_title}</h4>
                        <p className="text-sm text-gray-500 dark:text-gray-400">{interview.company || 'Company'}</p>
                        <p className="text-sm text-gray-400 mt-1">{formatDate(interview.scheduled_date)}</p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getInterviewStatusColor(interview.status)}`}>
                        {interview.status.charAt(0).toUpperCase() + interview.status.slice(1)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {interviews.length === 0 && (
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-12 text-center shadow-sm border border-gray-100 dark:border-slate-700">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">No interviews scheduled</h3>
              <p className="text-gray-500 dark:text-gray-400">Your scheduled interviews will appear here</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
