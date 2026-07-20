import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { authStorage } from '../../utils/authStorage'

export default function CandidateLogin() {
  const navigate = useNavigate()
  const [loginId, setLoginId] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault()
    if (!loginId.trim()) {
      toast.error('Please enter your Email or Candidate ID')
      return
    }
    if (!password) {
      toast.error('Please enter your password')
      return
    }
    // TODO: Add real password check here
    authStorage.setItem('candidate_id', loginId)
    toast.success('Login successful!')
    navigate('/candidate/profile')
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center">
      <div className="card max-w-md w-full">
        <div className="text-center mb-8">
          <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Candidate Portal</h2>
          <p className="text-gray-400">Login to access your profile and applications</p>
        </div>

        <form onSubmit={handleLogin}>
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Email or Candidate ID
            </label>
            <input
              type="text"
              value={loginId}
              onChange={(e) => setLoginId(e.target.value)}
              placeholder="Enter your email or candidate ID"
              className="input-field"
              required
            />
            <p className="text-gray-500 text-xs mt-2">
              Demo: Use any email or ID to login
            </p>
          </div>

          <div className="mb-6 relative">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Password
            </label>
            <input
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              className="input-field pr-10"
              required
            />
            <button
              type="button"
              tabIndex={-1}
              className="absolute right-3 top-9 text-gray-400 hover:text-gray-200 focus:outline-none"
              onClick={() => setShowPassword((prev) => !prev)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-5.523 0-10-4.477-10-10 0-1.657.402-3.22 1.125-4.575M15 12a3 3 0 11-6 0 3 3 0 016 0zm6.875-4.575A9.956 9.956 0 0122 9c0 5.523-4.477 10-10 10a9.956 9.956 0 01-4.575-1.125" /></svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0zm2.828-2.828A9.956 9.956 0 0122 12c0 5.523-4.477 10-10 10S2 17.523 2 12c0-2.21.896-4.21 2.343-5.657M9.88 9.88a3 3 0 104.24 4.24" /></svg>
              )}
            </button>
          </div>

          <button type="submit" className="w-full btn-primary mb-4">
            Login
          </button>

          <div className="text-center">
            <p className="text-gray-400 text-sm">
              New candidate?{' '}
              <button
                type="button"
                onClick={() => navigate('/candidate/profile')}
                className="text-blue-400 hover:text-blue-300"
              >
                Create Profile
              </button>
            </p>
          </div>
        </form>

        <div className="mt-8 pt-6 border-t border-gray-300 dark:border-gray-700">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Quick Access</h3>
          <div className="space-y-2">
            <button
              onClick={() => navigate('/candidate/applied-jobs')}
              className="w-full text-left px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg text-gray-700 dark:text-gray-300 text-sm transition-colors"
            >
              View Applied Jobs
            </button>
            <button
              onClick={() => navigate('/candidate/interviews')}
              className="w-full text-left px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg text-gray-700 dark:text-gray-300 text-sm transition-colors"
            >
              Check Interviews & Tasks
            </button>
            <button
              onClick={() => navigate('/candidate/feedback')}
              className="w-full text-left px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 rounded-lg text-gray-700 dark:text-gray-300 text-sm transition-colors"
            >
              View Feedback
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
