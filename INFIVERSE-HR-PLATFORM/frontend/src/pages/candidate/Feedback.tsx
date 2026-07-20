import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { getCandidateFeedback, type Feedback } from '../../services/api'
import { useAuth } from '../../context/AuthContext'
import { authStorage } from '../../utils/authStorage'

export default function CandidateFeedback() {
  const { user } = useAuth()
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedFeedback, setSelectedFeedback] = useState<Feedback | null>(null)


  useEffect(() => {
    loadFeedback()
  }, [])

  const loadFeedback = async () => {
    // Check authentication first
    const isAuthenticated = authStorage.getItem('isAuthenticated') === 'true' || !!user
    
    if (!isAuthenticated) {
      toast.error('Please login to view feedback')
      setLoading(false)
      return
    }

    const currentBackendId = authStorage.getItem('backend_candidate_id')
    
    // If authenticated but no candidate ID, show empty state
    if (!currentBackendId) {
      setFeedbacks([])
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      const data = await getCandidateFeedback(currentBackendId).catch(() => [])
      setFeedbacks(data)
    } catch (error) {
      console.error('Failed to load feedback:', error)
      setFeedbacks([])
    } finally {
      setLoading(false)
    }
  }

  const getDecisionConfig = (decision?: string) => {
    const configs: Record<string, { color: string; label: string }> = {
      accept: { 
        color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400', 
        label: 'Accepted' 
      },
      reject: { 
        color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400', 
        label: 'Rejected' 
      },
      hold: { 
        color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400', 
        label: 'On Hold' 
      },
    }
    return configs[decision?.toLowerCase() || ''] || { color: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300', label: 'Pending' }
  }

  const getValueColor = (value: number) => {
    if (value >= 4) return 'from-emerald-500 to-teal-500'
    if (value >= 3) return 'from-amber-500 to-orange-500'
    return 'from-red-500 to-pink-500'
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-blue-500/5 to-cyan-500/5 dark:from-blue-500/10 dark:to-cyan-500/10 backdrop-blur-xl border border-blue-300/20 dark:border-blue-500/20">
        <h1 className="page-title">Employer Feedback</h1>
        <p className="page-subtitle">View feedback and assessments from employers</p>
      </div>

      {/* Feedback Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
              <svg className="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{feedbacks.length}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Total Feedback</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
              <svg className="w-5 h-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
            </div>
            <div>
              <p className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                {feedbacks.filter(f => f.decision === 'accept').length}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Accepted</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
              <svg className="w-5 h-5 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            </div>
            <div>
              <p className="text-2xl font-bold text-amber-600 dark:text-amber-400">
                {feedbacks.filter(f => f.decision === 'hold').length}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">On Hold</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
              <svg className="w-5 h-5 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
            </div>
            <div>
              <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                {feedbacks.filter(f => f.decision === 'reject').length}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Rejected</p>
            </div>
          </div>
        </div>
      </div>

      {/* Feedback List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <div key={i} className="bg-white dark:bg-slate-800 rounded-xl p-6 animate-pulse">
              <div className="h-5 bg-gray-200 dark:bg-slate-700 rounded w-1/3 mb-3"></div>
              <div className="h-4 bg-gray-200 dark:bg-slate-700 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      ) : feedbacks.length === 0 ? (
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-12 text-center shadow-sm border border-gray-100 dark:border-slate-700">
          <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
          </svg>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">No feedback received yet</h3>
          <p className="text-gray-500 dark:text-gray-400">Feedback will appear here after your interviews</p>
        </div>
      ) : (
        <div className="space-y-4">
          {feedbacks.map((feedback) => {
            const decisionConfig = getDecisionConfig(feedback.decision)
            return (
              <div
                key={feedback.id}
                className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-gray-100 dark:border-slate-700 hover:shadow-md transition-all cursor-pointer"
                onClick={() => setSelectedFeedback(feedback)}
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{feedback.job_title || 'Interview Feedback'}</h3>
                      {feedback.interviewer_name && (
                        <p className="text-sm text-gray-600 dark:text-gray-400">From: {feedback.interviewer_name}</p>
                      )}
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{formatDate(feedback.created_at)}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${decisionConfig.color}`}>
                      {decisionConfig.label}
                    </span>
                    {feedback.rating && (
                      <span className="flex items-center gap-1 text-amber-500">
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" /></svg>
                        {feedback.rating}/5
                      </span>
                    )}
                  </div>
                </div>
                
                {feedback.feedback_text && (
                  <p className="mt-4 text-gray-600 dark:text-gray-400 line-clamp-2">
                    {feedback.feedback_text}
                  </p>
                )}

                {/* Values Mini Preview */}
                {feedback.values_assessment && (
                  <div className="mt-4 pt-4 border-t border-gray-100 dark:border-slate-700">
                    <div className="flex flex-wrap gap-3">
                      {Object.entries(feedback.values_assessment).map(([key, value]) => (
                        <div key={key} className="flex items-center gap-2">
                          <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}:</span>
                          <div className="w-16 bg-gray-200 dark:bg-slate-700 rounded-full h-1.5">
                            <div
                              className={`h-1.5 rounded-full bg-gradient-to-r ${getValueColor(value)}`}
                              style={{ width: `${(value / 5) * 100}%` }}
                            />
                          </div>
                          <span className="text-xs font-medium text-gray-700 dark:text-gray-300">{value.toFixed(1)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Feedback Detail Modal */}
      {selectedFeedback && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-slate-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-100 dark:border-slate-700">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-white">{selectedFeedback.job_title || 'Interview Feedback'}</h2>
                  <p className="text-gray-600 dark:text-gray-400">{formatDate(selectedFeedback.created_at)}</p>
                </div>
                <button
                  onClick={() => setSelectedFeedback(null)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="p-6 space-y-6">
              {/* Decision */}
              <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-700/50 rounded-lg">
                <span className="text-gray-600 dark:text-gray-400">Decision</span>
                <span className={`px-4 py-2 rounded-full text-sm font-medium ${getDecisionConfig(selectedFeedback.decision).color}`}>
                  {getDecisionConfig(selectedFeedback.decision).label}
                </span>
              </div>

              {/* Interviewer */}
              {selectedFeedback.interviewer_name && (
                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-slate-700/50 rounded-lg">
                  <span className="text-gray-600 dark:text-gray-400">Interviewer</span>
                  <span className="font-medium text-gray-900 dark:text-white">{selectedFeedback.interviewer_name}</span>
                </div>
              )}

              {/* Feedback Text */}
              {selectedFeedback.feedback_text && (
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-3">Feedback</h3>
                  <p className="text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-slate-700/50 rounded-lg p-4 whitespace-pre-line">
                    {selectedFeedback.feedback_text}
                  </p>
                </div>
              )}

              {/* Values Assessment */}
              {selectedFeedback.values_assessment && (
                <div>
                  <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Values Assessment</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {Object.entries(selectedFeedback.values_assessment).map(([key, value]) => {
                      const displayName = key.replace(/([A-Z])/g, ' $1').trim()
                      return (
                        <div key={key} className="bg-gray-50 dark:bg-slate-700/50 rounded-lg p-4">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium text-gray-700 dark:text-gray-300 capitalize">{displayName}</span>
                            <span className="font-bold text-gray-900 dark:text-white">{value.toFixed(1)}/5</span>
                          </div>
                          <div className="w-full bg-gray-200 dark:bg-slate-600 rounded-full h-3">
                            <div
                              className={`h-3 rounded-full bg-gradient-to-r ${getValueColor(value)}`}
                              style={{ width: `${(value / 5) * 100}%` }}
                            />
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>

            <div className="p-6 border-t border-gray-100 dark:border-slate-700">
              <button
                onClick={() => setSelectedFeedback(null)}
                className="w-full py-3 bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 text-gray-700 dark:text-gray-300 font-medium rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
