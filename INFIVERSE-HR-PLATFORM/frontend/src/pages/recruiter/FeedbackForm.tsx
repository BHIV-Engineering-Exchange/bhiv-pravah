import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { submitFeedback, getCandidateProfile } from '../../services/api'
import Loading from '../../components/Loading'

type DecisionType = 'accept' | 'reject' | 'hold' | ''

export default function FeedbackForm() {
  const { candidateId } = useParams()
  const navigate = useNavigate()
  const [candidate, setCandidate] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [formData, setFormData] = useState<{
    comment: string
    integrity: number
    honesty: number
    discipline: number
    hardWork: number
    gratitude: number
    decision: DecisionType
  }>({
    comment: '',
    integrity: 3,
    honesty: 3,
    discipline: 3,
    hardWork: 3,
    gratitude: 3,
    decision: '',
  })

  useEffect(() => {
    loadCandidate()
  }, [candidateId])

  const loadCandidate = async () => {
    try {
      setLoading(true)
      const data = await getCandidateProfile(candidateId!)
      setCandidate(data)
    } catch (error) {
      console.error('Failed to load candidate:', error)
      toast.error('Failed to load candidate details')
    } finally {
      setLoading(false)
    }
  }

  const handleSliderChange = (name: string, value: number) => {
    setFormData({ ...formData, [name]: value })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!formData.decision) {
      toast.error('Please select a decision')
      return
    }

    setSubmitting(true)
    try {
      const feedbackData = {
        comment: formData.comment,
        integrity: formData.integrity,
        honesty: formData.honesty,
        discipline: formData.discipline,
        hardWork: formData.hardWork,
        gratitude: formData.gratitude,
        decision: formData.decision as 'accept' | 'reject' | 'hold'
      }
      await submitFeedback(candidateId!, feedbackData)
      toast.success('Feedback submitted successfully!')
      navigate(-1)
    } catch (error) {
      toast.error('Failed to submit feedback')
      console.error(error)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return <Loading message="Loading candidate details..." />
  }

  const valueLabels = [
    { key: 'integrity', label: 'Integrity' },
    { key: 'honesty', label: 'Honesty' },
    { key: 'discipline', label: 'Discipline' },
    { key: 'hardWork', label: 'Hard Work' },
    { key: 'gratitude', label: 'Gratitude' },
  ]

  return (
    <div>
      <div className="mb-8 p-6 rounded-2xl bg-gradient-to-r from-green-500/5 to-emerald-500/5 dark:from-green-500/10 dark:to-emerald-500/10 backdrop-blur-xl border border-green-300/20 dark:border-green-500/20">
        <button
          onClick={() => navigate(-1)}
          className="text-green-400 hover:text-green-300 mb-4 flex items-center space-x-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          <span>Back</span>
        </button>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Candidate Feedback</h1>
        <p className="text-gray-400">Provide feedback and assessment for {candidate?.name}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Candidate Summary */}
        <div className="card">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-4">Candidate Summary</h3>
          <div className="space-y-3">
            <div>
              <p className="text-gray-500 dark:text-gray-400 text-sm">Name</p>
              <p className="text-gray-900 dark:text-white font-medium">{candidate?.name}</p>
            </div>
            <div>
              <p className="text-gray-500 dark:text-gray-400 text-sm">Email</p>
              <p className="text-gray-900 dark:text-white">{candidate?.email}</p>
            </div>
            <div>
              <p className="text-gray-500 dark:text-gray-400 text-sm">Phone</p>
              <p className="text-gray-900 dark:text-white">{candidate?.phone}</p>
            </div>
            <div>
              <p className="text-gray-500 dark:text-gray-400 text-sm">Location</p>
              <p className="text-gray-900 dark:text-white">{candidate?.location}</p>
            </div>
            <div>
              <p className="text-gray-500 dark:text-gray-400 text-sm">Experience</p>
              <p className="text-gray-900 dark:text-white">{candidate?.totalExperience} years</p>
            </div>
            <div>
              <p className="text-gray-500 dark:text-gray-400 text-sm">Skills</p>
              <div className="flex flex-wrap gap-1 mt-1">
                {candidate?.skills.map((skill: string, idx: number) => (
                  <span
                    key={idx}
                    className="px-2 py-1 bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300 rounded text-xs"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Feedback Form */}
        <div className="lg:col-span-2 card">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-6">Evaluation Form</h3>
          
          <form onSubmit={handleSubmit}>
            {/* Comment */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Comments / Feedback
                <span className="text-red-500 ml-1">*</span>
              </label>
              <textarea
                value={formData.comment}
                onChange={(e) => setFormData({ ...formData, comment: e.target.value })}
                rows={4}
                required
                className="input-field"
                placeholder="Provide detailed feedback about the candidate..."
              />
            </div>

            {/* Values Sliders */}
            <div className="mb-6">
              <h4 className="text-md font-semibold text-gray-900 dark:text-white mb-4">Core Values Assessment (0-5)</h4>
              <div className="space-y-4">
                {valueLabels.map(({ key, label }) => (
                  <div key={key}>
                    <div className="flex justify-between items-center mb-2">
                      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</label>
                      <span className="text-gray-900 dark:text-white font-bold text-lg">
                        {formData[key as keyof typeof formData]}
                      </span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="5"
                      step="0.5"
                      value={formData[key as keyof typeof formData] as number}
                      onChange={(e) => handleSliderChange(key, parseFloat(e.target.value))}
                      className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                      style={{
                        background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${((formData[key as keyof typeof formData] as number) / 5) * 100}%, #e5e7eb ${((formData[key as keyof typeof formData] as number) / 5) * 100}%, #e5e7eb 100%)`
                      }}
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>0</span>
                      <span>1</span>
                      <span>2</span>
                      <span>3</span>
                      <span>4</span>
                      <span>5</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Decision */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Decision
                <span className="text-red-500 ml-1">*</span>
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {[
                  { value: 'accept', label: 'Accept', color: 'green' },
                  { value: 'reject', label: 'Reject', color: 'red' },
                  { value: 'hold', label: 'Hold', color: 'yellow' }
                ].map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setFormData({ ...formData, decision: option.value as DecisionType })}
                    className={`px-4 py-3 rounded-lg font-medium transition-all ${
                      formData.decision === option.value
                        ? option.color === 'green' ? 'bg-green-600 text-white ring-2 ring-green-400' :
                          option.color === 'red' ? 'bg-red-600 text-white ring-2 ring-red-400' :
                          'bg-yellow-600 text-white ring-2 ring-yellow-400'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                    }`}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Submit */}
            <div className="flex space-x-4">
              <button
                type="submit"
                disabled={submitting}
                className="btn-primary"
              >
                {submitting ? 'Submitting...' : 'Submit Feedback'}
              </button>
              <button
                type="button"
                onClick={() => navigate(-1)}
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
