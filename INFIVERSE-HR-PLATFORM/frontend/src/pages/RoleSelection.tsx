import { useNavigate } from 'react-router-dom'

const roles = [
  {
    id: 'candidate',
    title: 'Candidate',
    description: 'Looking for your dream job? Create your profile and apply to positions.',
    icon: (
      <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    ),
    gradient: 'from-blue-500 to-cyan-500',
    hoverGradient: 'group-hover:from-blue-600 group-hover:to-cyan-600',
    path: '/auth?mode=signup',
    features: ['Apply to Jobs', 'Track Applications', 'AI-Powered Matching'],
  },
  {
    id: 'recruiter',
    title: 'Recruiter',
    description: 'Find the perfect candidates with AI-powered screening and matching.',
    icon: (
      <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
    gradient: 'from-emerald-500 to-teal-500',
    hoverGradient: 'group-hover:from-emerald-600 group-hover:to-teal-600',
    path: '/auth?mode=signup',
    features: ['Post Jobs', 'AI Screening', 'Manage Pipeline'],
  },
  {
    id: 'client',
    title: 'Client',
    description: 'Review shortlisted candidates and make informed hiring decisions.',
    icon: (
      <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
    gradient: 'from-purple-500 to-pink-500',
    hoverGradient: 'group-hover:from-purple-600 group-hover:to-pink-600',
    path: '/auth?mode=signup',
    features: ['Review Shortlists', 'Interview Scheduling', 'Analytics Dashboard'],
  },
]

export default function RoleSelection() {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex flex-col">
      {/* Background Effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-emerald-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000" />
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-4000" />
      </div>

      {/* Header */}
      <header className="relative z-10 pt-12 pb-8 text-center">
        <div className="flex items-center justify-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-400 via-purple-500 to-pink-500 p-0.5">
            <div className="w-full h-full rounded-xl bg-slate-900 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
          <h1 className="text-3xl font-bold">
            <span className="bg-gradient-to-r from-emerald-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              Sampada
            </span>
          </h1>
          <p className="text-gray-400 text-sm mt-1">HR Recruitment System</p>
        </div>
        <h2 className="text-2xl md:text-3xl font-semibold text-white mb-2">
          Welcome to the Future of Hiring
        </h2>
        <p className="text-gray-400 text-lg max-w-xl mx-auto px-4">
          Choose your role to get started with our AI-powered recruitment platform
        </p>
      </header>

      {/* Role Cards */}
      <main className="relative z-10 flex-1 flex items-center justify-center px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl w-full">
          {roles.map((role, index) => (
            <button
              key={role.id}
              onClick={() => navigate('/auth?mode=signup')}
              className="group relative bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-8 text-left transition-all duration-300 hover:scale-105 hover:border-slate-600 hover:shadow-2xl hover:shadow-purple-500/10"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              {/* Gradient Overlay on Hover */}
              <div className={`absolute inset-0 bg-gradient-to-br ${role.gradient} opacity-0 group-hover:opacity-10 rounded-2xl transition-opacity duration-300`} />
              
              {/* Icon */}
              <div className={`relative w-20 h-20 rounded-2xl bg-gradient-to-br ${role.gradient} ${role.hoverGradient} p-0.5 mb-6 transition-all duration-300 group-hover:scale-110`}>
                <div className="w-full h-full rounded-2xl bg-slate-900 flex items-center justify-center text-white">
                  {role.icon}
                </div>
              </div>

              {/* Content */}
              <h3 className="relative text-2xl font-bold text-white mb-3 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:bg-clip-text group-hover:from-white group-hover:to-gray-300 transition-all">
                {role.title}
              </h3>
              <p className="relative text-gray-400 mb-6 leading-relaxed">
                {role.description}
              </p>

              {/* Features */}
              <ul className="relative space-y-2 mb-6">
                {role.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-2 text-gray-500 text-sm">
                    <svg className={`w-4 h-4 text-${role.gradient.split('-')[1]}-400`} fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <div className={`relative flex items-center gap-2 text-white font-medium bg-gradient-to-r ${role.gradient} bg-clip-text text-transparent group-hover:gap-4 transition-all duration-300`}>
                Get Started
                <svg className="w-5 h-5 text-gray-400 group-hover:text-white group-hover:translate-x-1 transition-all duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </div>
            </button>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 py-6 text-center">
        <p className="text-gray-600 text-sm">
          © 2024 Sampada. Powered by AI • Built for Modern Recruitment
        </p>
      </footer>
    </div>
  )
}
