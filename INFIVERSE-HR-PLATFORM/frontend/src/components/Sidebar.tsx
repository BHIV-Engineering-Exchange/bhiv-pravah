import { Link, useLocation } from 'react-router-dom'

export default function Sidebar() {
  const location = useLocation()
  
  const navItems = [
    {
      title: 'Recruiter Console',
      path: '/recruiter',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      ),
      subItems: [
        { title: 'Dashboard', path: '/recruiter' },
        { title: 'Create Job', path: '/recruiter/create-job' },
        { title: 'Auto-Messaging System', path: '/recruiter/automation' },
      ],
    },
    {
      title: 'Candidate Portal',
      path: '/candidate',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      ),
      subItems: [
        { title: 'Login', path: '/candidate' },
        { title: 'Profile', path: '/candidate/profile' },
        { title: 'Applied Jobs', path: '/candidate/applied-jobs' },
        { title: 'Interviews', path: '/candidate/interviews' },
        { title: 'Feedback', path: '/candidate/feedback' },
      ],
    },
    {
      title: 'Client View',
      path: '/client',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      ),
      subItems: [
        { title: 'Dashboard', path: '/client' },
      ],
    },
  ]

  const isActive = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/')
  }

  return (
    <aside className="fixed left-0 top-16 w-64 h-[calc(100vh-4rem)] glass-sidebar overflow-y-auto transition-all duration-300 animate-slide-in-left">
      <nav className="p-4 space-y-2">
        {navItems.map((item) => (
          <div key={item.path}>
            <Link
              to={item.path}
              className={`flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-300 ${
                isActive(item.path)
                  ? 'bg-gradient-to-br from-[#667eea] to-[#764ba2] text-white shadow-xl shadow-purple-500/30 scale-105'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white hover:scale-105'
              }`}
            >
              {item.icon}
              <span className="font-bold">{item.title}</span>
            </Link>
            
            {item.subItems && isActive(item.path) && (
              <div className="ml-4 mt-2 space-y-1 animate-fade-in">
                {item.subItems.map((subItem) => (
                  <Link
                    key={subItem.path}
                    to={subItem.path}
                    className={`block px-4 py-2 rounded-xl text-sm transition-all duration-300 ${
                      location.pathname === subItem.path
                        ? 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-white font-bold scale-105 shadow-lg'
                        : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800/50 hover:text-gray-900 dark:hover:text-white hover:scale-105'
                    }`}
                  >
                    {subItem.title}
                  </Link>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>
    </aside>
  )
}
