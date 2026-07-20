import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import {
  getNotificationServiceHealth,
  sendNotification,
  testNotificationSequence,
  triggerAutomation,
} from '../../services/api'

export default function AutomationPanel() {
  const [loading, setLoading] = useState<string | null>(null)
  const [serviceStatus, setServiceStatus] = useState<'checking' | 'online' | 'offline'>('checking')
  const [testing, setTesting] = useState(false)
  
  // Multi-channel test form
  const [testForm, setTestForm] = useState({
    candidate_name: 'Test Candidate',
    candidate_email: '',
    candidate_phone: '',
    job_title: 'Software Engineer',
    message: 'Your application has been updated'
  })

  useEffect(() => {
    checkServiceStatus()
  }, [])

  const checkServiceStatus = async () => {
    setServiceStatus('checking')
    try {
      const response = await getNotificationServiceHealth()

      if (response?.status || response?.service || response?.environment) {
        setServiceStatus('online')
      } else {
        setServiceStatus('offline')
      }
    } catch (error) {
      setServiceStatus('offline')
    }
  }

  const automations = [
    {
      id: 'shortlist',
      title: 'Shortlist Notification',
      description: 'Send email to candidates who have been shortlisted',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: 'green',
    },
    {
      id: 'interview',
      title: 'Interview Notification',
      description: 'Send interview schedules to candidates',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      ),
      color: 'blue',
    },
    {
      id: 'offer',
      title: 'Offer Notification',
      description: 'Send offer letters to selected candidates',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      color: 'purple',
    },
    {
      id: 'rejection',
      title: 'Rejection Notification',
      description: 'Send polite rejection emails to candidates',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: 'red',
    },
    {
      id: 'reminder',
      title: 'Task Reminder',
      description: 'Remind candidates about pending tasks',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
      ),
      color: 'yellow',
    },
    {
      id: 'feedback',
      title: 'Feedback Request',
      description: 'Request feedback from interviewers',
      icon: (
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
      ),
      color: 'blue',
    },
  ]

  const colorClasses = {
    green: 'from-green-500 to-green-700',
    blue: 'from-blue-500 to-blue-700',
    purple: 'from-purple-500 to-purple-700',
    red: 'from-red-500 to-red-700',
    yellow: 'from-yellow-500 to-yellow-700',
  }

  const handleTrigger = async (type: string, title: string) => {
    setLoading(type)
    try {
      await triggerAutomation(type)
      toast.success(`${title} triggered successfully!`)
    } catch (error) {
      toast.error(`Failed to trigger ${title}`)
      console.error(error)
    } finally {
      setLoading(null)
    }
  }

  const handleMultiChannelTest = async (e: React.FormEvent) => {
    e.preventDefault()

    const hasEmail = Boolean(testForm.candidate_email && testForm.candidate_email.trim())
    const hasPhone = Boolean(testForm.candidate_phone && testForm.candidate_phone.trim())

    if (!hasEmail && !hasPhone) {
      toast.error('Please provide at least one contact: email or WhatsApp number')
      return
    }

    const detectedChannels: string[] = []
    if (hasEmail) detectedChannels.push('email')
    if (hasPhone) detectedChannels.push('whatsapp')

    setTesting(true)
    try {
      const result = await sendNotification({
        candidate_name: testForm.candidate_name,
        candidate_email: testForm.candidate_email,
        candidate_phone: testForm.candidate_phone,
        job_title: testForm.job_title,
        message: testForm.message,
        channels: detectedChannels,
        application_status: 'updated'
      })

      toast.success(`Notification sent via ${detectedChannels.join(' + ')}`)
      console.log('Test result:', result)
    } catch (error) {
      console.error('Test error:', error)
      toast.error('Failed to send notification. Service may be offline.')
    } finally {
      setTesting(false)
    }
  }

  const handleSequenceTest = async (sequenceType: string) => {
    setTesting(true)
    try {
      const testData = {
        candidate_name: 'John Doe',
        candidate_email: 'john.doe@example.com',
        candidate_phone: '+1234567890',
        job_title: 'Software Engineer',
        sequence_type: sequenceType
      }

      const result = await testNotificationSequence(testData)
      toast.success(`${sequenceType} notification sent!`)
      console.log('Sequence result:', result)
    } catch (error) {
      console.error('Sequence test error:', error)
      toast.error('Failed to send test sequence. Service may be offline.')
    } finally {
      setTesting(false)
    }
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="p-6 rounded-2xl bg-gradient-to-r from-green-500/5 to-emerald-500/5 dark:from-green-500/10 dark:to-emerald-500/10 backdrop-blur-xl border border-green-300/20 dark:border-green-500/20">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Auto-Messaging System</h1>
        <p className="text-gray-600 dark:text-gray-400">Send live email and WhatsApp notifications to candidates</p>
      </div>

      {/* Communication Service Status */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-title">Communication Service Status</h2>
          <button
            onClick={checkServiceStatus}
            className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Refresh
          </button>
        </div>
        
        <div className="flex items-center gap-3">
          {serviceStatus === 'checking' && (
            <>
              <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse"></div>
              <span className="text-gray-600 dark:text-gray-400">Checking service status...</span>
            </>
          )}
          {serviceStatus === 'online' && (
            <>
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-green-600 dark:text-green-400 font-medium">LangGraph Communication Service: Online</span>
            </>
          )}
          {serviceStatus === 'offline' && (
            <>
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <span className="text-red-600 dark:text-red-400 font-medium">LangGraph Communication Service: Offline</span>
            </>
          )}
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
          Note: Service status indicates whether messaging delivery is currently available.
        </p>
      </div>

      {/* Multi-Channel Notification Test */}
      <div className="card">
        <h2 className="section-title mb-4">Send Candidate Notification</h2>
        
        <form onSubmit={handleMultiChannelTest} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Candidate Name
              </label>
              <input
                type="text"
                value={testForm.candidate_name}
                onChange={(e) => setTestForm({ ...testForm, candidate_name: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Candidate Email
              </label>
              <input
                type="email"
                value={testForm.candidate_email}
                onChange={(e) => setTestForm({ ...testForm, candidate_email: e.target.value })}
                placeholder="candidate@example.com"
                className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Candidate Phone
              </label>
              <input
                type="tel"
                value={testForm.candidate_phone}
                onChange={(e) => setTestForm({ ...testForm, candidate_phone: e.target.value })}
                placeholder="+1234567890"
                className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Job Title
              </label>
              <input
                type="text"
                value={testForm.job_title}
                onChange={(e) => setTestForm({ ...testForm, job_title: e.target.value })}
                className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Notification Message
            </label>
            <textarea
              value={testForm.message}
              onChange={(e) => setTestForm({ ...testForm, message: e.target.value })}
              rows={3}
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
            />
          </div>

          <p className="text-sm text-gray-600 dark:text-gray-400">
            Channel auto-detection: if email is provided, an email is sent; if phone is provided, a WhatsApp message is sent; if both are provided, both are sent.
          </p>

          <button
            type="submit"
            disabled={testing}
            className="w-full bg-green-500 hover:bg-green-600 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg font-semibold transition-colors"
          >
            {testing ? 'Sending...' : 'Send Notification'}
          </button>
        </form>
      </div>

      {/* Automated Sequences Testing */}
      <div className="card">
        <h2 className="section-title mb-4">Quick Sequence Sends</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => handleSequenceTest('shortlisted')}
            disabled={testing}
            className="p-4 bg-green-50 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-900/30 border border-green-200 dark:border-green-800 rounded-xl transition-colors disabled:opacity-50"
          >
            <div className="flex items-center gap-3 mb-2">
              <svg className="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <h3 className="font-semibold text-gray-900 dark:text-white">Shortlist Notification</h3>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Test shortlist notification sequence</p>
          </button>

          <button
            onClick={() => handleSequenceTest('interview_scheduled')}
            disabled={testing}
            className="p-4 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30 border border-blue-200 dark:border-blue-800 rounded-xl transition-colors disabled:opacity-50"
          >
            <div className="flex items-center gap-3 mb-2">
              <svg className="w-6 h-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <h3 className="font-semibold text-gray-900 dark:text-white">Interview Notification</h3>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Test interview scheduling sequence</p>
          </button>

          <button
            onClick={() => handleSequenceTest('feedback_request')}
            disabled={testing}
            className="p-4 bg-purple-50 dark:bg-purple-900/20 hover:bg-purple-100 dark:hover:bg-purple-900/30 border border-purple-200 dark:border-purple-800 rounded-xl transition-colors disabled:opacity-50"
          >
            <div className="flex items-center gap-3 mb-2">
              <svg className="w-6 h-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              <h3 className="font-semibold text-gray-900 dark:text-white">Feedback Request</h3>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">Test feedback request sequence</p>
          </button>
        </div>
      </div>

      {/* Automation Triggers */}
      <div className="card">
        <h2 className="section-title mb-4">Automation Triggers</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {automations.map((automation) => (
            <div key={automation.id} className="p-4 bg-gray-50 dark:bg-gray-800/50 rounded-xl border border-gray-200 dark:border-gray-700 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className={`w-12 h-12 bg-gradient-to-br ${colorClasses[automation.color as keyof typeof colorClasses]} rounded-lg flex items-center justify-center text-white`}>
                  {automation.icon}
                </div>
              </div>
              
              <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">{automation.title}</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">{automation.description}</p>
              
              <button
                onClick={() => handleTrigger(automation.id, automation.title)}
                disabled={loading === automation.id}
                className="w-full bg-green-500 hover:bg-green-600 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium transition-colors"
              >
                {loading === automation.id ? (
                  <span className="flex items-center justify-center">
                    <svg className="animate-spin h-4 w-4 mr-2" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Triggering...
                  </span>
                ) : (
                  'Trigger Now'
                )}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
