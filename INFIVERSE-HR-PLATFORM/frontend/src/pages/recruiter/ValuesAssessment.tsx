import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { searchCandidates, getRecruiterJobs, getCandidateFeedback, submitFeedback, type Job } from '../../services/api'
import Loading from '../../components/Loading'

const EXPERIENCE_LEVELS = ['Entry', 'Mid', 'Senior', 'Lead'] as const
const VALUE_SLIDER_MIN = 1
const VALUE_SLIDER_MAX = 5

export default function ValuesAssessment() {
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [duplicateWarning, setDuplicateWarning] = useState<string | null>(null)
  const [candidates, setCandidates] = useState<{ id: string; name?: string; email?: string }[]>([])
  const [jobs, setJobs] = useState<Job[]>([])
  
  const [formData, setFormData] = useState({
    candidate_name: '',
    candidate_id: '',
    job_title: '',
    job_id: '',
    experience_level: 'Entry' as typeof EXPERIENCE_LEVELS[number],
    reviewer_name: '',
    interview_date: '',
    feedback_text: '',
    integrity: 3,
    honesty: 3,
    discipline: 3,
    hardWork: 3,
    gratitude: 3,
    overall_recommendation: 'Neutral',
  })

  useEffect(() => {
    loadData()
    // Auto-refresh every 30 seconds for real-time data
    const interval = setInterval(loadData, 30000)
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [candidatesRes, jobsData] = await Promise.all([
        searchCandidates('', {}).catch(() => ({ candidates: [], total: 0 })),
        getRecruiterJobs().catch(() => [])
      ])
      setCandidates(Array.isArray(candidatesRes.candidates) ? candidatesRes.candidates : [])
      setJobs(jobsData)
    } catch (error) {
      console.error('Failed to load data:', error)
      toast.error('Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setDuplicateWarning(null)
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSliderChange = (value: string, valueName: string) => {
    setDuplicateWarning(null)
    const num = Math.min(VALUE_SLIDER_MAX, Math.max(VALUE_SLIDER_MIN, parseInt(value, 10) || VALUE_SLIDER_MIN))
    setFormData(prev => ({ ...prev, [valueName]: num }))
  }

  const requiredFilled =
    !!formData.candidate_id &&
    !!formData.job_id &&
    !!formData.experience_level &&
    !!formData.reviewer_name?.trim() &&
    !!formData.interview_date &&
    !!formData.overall_recommendation
  const canSubmit = requiredFilled && !duplicateWarning

  const getValueRating = (key: string): number => {
    const v = formData[key as keyof typeof formData]
    if (typeof v !== 'number') return VALUE_SLIDER_MIN
    return Math.min(VALUE_SLIDER_MAX, Math.max(VALUE_SLIDER_MIN, v))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) return

    setDuplicateWarning(null)
    setSubmitting(true)
    try {
      const existingList = await getCandidateFeedback(formData.candidate_id)
      const jobId = (formData.job_id || '').trim()
      const experienceLevel = (formData.experience_level || '').trim()
      const comments = (formData.feedback_text || '').trim()
      const integrity = getValueRating('integrity')
      const honesty = getValueRating('honesty')
      const discipline = getValueRating('discipline')
      const hardWork = getValueRating('hardWork')
      const gratitude = getValueRating('gratitude')

      const isDuplicate = existingList.some((ex) => {
        const exJob = (ex.job_id ?? '').toString().trim()
        const exExp = (ex as { experience_level?: string }).experience_level ?? ''
        const exComments = (ex.feedback_text ?? (ex as { comments?: string }).comments ?? '').toString().trim()
        const exVal = ex.values_assessment ?? (ex as { values_scores?: Record<string, number> }).values_scores
        if (exJob !== jobId) return false
        if (exExp !== experienceLevel) return false
        if (exComments !== comments) return false
        if (exVal?.integrity !== integrity) return false
        if (exVal?.honesty !== honesty) return false
        if (exVal?.discipline !== discipline) return false
        if ((exVal?.hardWork ?? (exVal as Record<string, number>)?.['hard_work']) !== hardWork) return false
        if (exVal?.gratitude !== gratitude) return false
        return true
      })

      if (isDuplicate) {
        setDuplicateWarning(
          'This values assessment is identical to an existing one for this candidate and job. Please change at least one value (e.g. ratings, feedback, experience level, or job) to submit a new assessment.'
        )
        setSubmitting(false)
        return
      }

      const feedbackData = {
        job_id: formData.job_id || '',
        integrity,
        honesty,
        discipline,
        hard_work: hardWork,
        gratitude,
        comments: comments || undefined,
        experience_level: formData.experience_level,
      }

      await submitFeedback(formData.candidate_id, feedbackData)
      setDuplicateWarning(null)
      toast.success('Values assessment submitted successfully!')
      
      // Reset form
      setFormData({
        candidate_name: '',
        candidate_id: '',
        job_title: '',
        job_id: '',
        experience_level: 'Entry',
        reviewer_name: '',
        interview_date: '',
        feedback_text: '',
        integrity: 3,
        honesty: 3,
        discipline: 3,
        hardWork: 3,
        gratitude: 3,
        overall_recommendation: 'Neutral',
      })
    } catch (error) {
      console.error('Failed to submit assessment:', error)
      toast.error('Failed to submit assessment')
    } finally {
      setSubmitting(false)
    }
  }

  const valueDescriptions = {
    integrity: 'Moral uprightness, ethical behavior, and honesty in all actions',
    honesty: 'Truthfulness, transparency, and sincerity in communication',
    discipline: 'Self-control, consistency, and commitment to excellence',
    hardWork: 'Dedication, perseverance, and going above and beyond expectations',
    gratitude: 'Appreciation, humility, and recognition of others\' contributions',
  }

  if (loading) {
    return <Loading message="Loading values assessment..." />
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="mb-8">
        <div className="p-6 rounded-2xl bg-gradient-to-r from-green-500/5 to-emerald-500/5 dark:from-green-500/10 dark:to-emerald-500/10 backdrop-blur-xl border border-green-300/20 dark:border-green-500/20 mb-8">
          <h1 className="page-title">Values-Based Candidate Assessment</h1>
          <p className="page-subtitle">Assess candidates on our core organizational values</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Candidate Information */}
        <div className="card">
          <h2 className="section-title flex items-center gap-2">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Candidate Information
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Candidate *
              </label>
              <select
                name="candidate_id"
                value={formData.candidate_id}
                onChange={(e) => {
                  const id = e.target.value
                  const c = candidates.find((x) => x.id === id)
                  setFormData(prev => ({
                    ...prev,
                    candidate_id: id,
                    candidate_name: c ? (c.name || '') : '',
                  }))
                }}
                className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                required
              >
                <option value="">Select candidate (applicants for your jobs)</option>
                {candidates.map((c) => (
                  <option key={c.id} value={c.id}>
                    {(c.name || 'Unknown')} - {c.id}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Applied Job *
              </label>
              <select
                name="job_id"
                value={formData.job_id}
                onChange={(e) => {
                  const id = e.target.value
                  const j = jobs.find((x) => (x.id?.toString?.() ?? String(x.id)) === id)
                  setFormData(prev => ({
                    ...prev,
                    job_id: id,
                    job_title: j ? (j.title || '') : '',
                  }))
                }}
                className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              >
                <option value="">Select job (your posted jobs)</option>
                {jobs.map((job) => (
                  <option key={job.id} value={job.id?.toString?.() ?? String(job.id)}>
                    {(job.title ?? 'Untitled')} - {job.id}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Experience Level *
              </label>
              <select
                name="experience_level"
                value={formData.experience_level}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              >
                {EXPERIENCE_LEVELS.map((level) => (
                  <option key={level} value={level}>{level}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Reviewer Name *
              </label>
              <input
                type="text"
                name="reviewer_name"
                value={formData.reviewer_name}
                onChange={handleChange}
                placeholder="Your full name"
                className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Interview Date *
              </label>
              <input
                type="date"
                name="interview_date"
                value={formData.interview_date}
                onChange={handleChange}
                className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>

        {/* Interview Feedback */}
        <div className="card">
          <h2 className="section-title flex items-center gap-2">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Interview Feedback
          </h2>
          
          <textarea
            name="feedback_text"
            value={formData.feedback_text}
            onChange={handleChange}
            placeholder="Provide comprehensive feedback about the candidate's performance, technical skills, communication, and overall fit..."
            rows={6}
            className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>

        {/* Values Assessment */}
        <div className="card">
          <h2 className="section-title flex items-center gap-2">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
            </svg>
            Values Assessment (1-5 scale)
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Rate the candidate on each of our core organizational values:
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {Object.entries(valueDescriptions).map(([key, description]) => (
              <div key={key} className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="mb-2">
                  <label className="block text-sm font-semibold text-gray-900 dark:text-white mb-1 capitalize">
                    {key === 'hardWork' ? 'Hard Work' : key}
                  </label>
                  <p className="text-xs text-gray-600 dark:text-gray-400">{description}</p>
                </div>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={getValueRating(key)}
                    onChange={(e) => handleSliderChange(e.target.value, key)}
                    className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                  />
                  <span className="text-lg font-bold text-emerald-600 dark:text-emerald-400 w-8 text-center">
                    {getValueRating(key)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Overall Assessment */}
        <div className="card">
          <h2 className="section-title flex items-center gap-2">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Overall Assessment
          </h2>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Overall Recommendation *
            </label>
            <select
              name="overall_recommendation"
              value={formData.overall_recommendation}
              onChange={handleChange}
              className="w-full px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            >
              <option value="Strongly Recommend">Strongly Recommend</option>
              <option value="Recommend">Recommend</option>
              <option value="Neutral">Neutral</option>
              <option value="Do Not Recommend">Do Not Recommend</option>
              <option value="Strongly Do Not Recommend">Strongly Do Not Recommend</option>
            </select>
          </div>
        </div>

        {duplicateWarning && (
          <div className="rounded-lg border border-amber-300 bg-amber-50 dark:border-amber-600 dark:bg-amber-900/20 p-4 text-amber-800 dark:text-amber-200" role="alert">
            {duplicateWarning}
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={submitting || !canSubmit}
            className="px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-semibold rounded-lg transition-all duration-200 flex items-center gap-2 shadow-lg shadow-emerald-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? (
              <>
                <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Submitting...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                </svg>
                Submit Assessment
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}

