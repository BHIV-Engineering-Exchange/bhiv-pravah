interface BlobLoadingOverlayProps {
  title: string
  description: string
  variant: 'recruiter' | 'client'
}

export default function BlobLoadingOverlay({ title, description, variant }: BlobLoadingOverlayProps) {
  const isClient = variant === 'client'

  const cardBg = isClient
    ? 'bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900'
    : 'bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900'

  const blob1 = isClient ? 'bg-blue-500' : 'bg-purple-500'
  const blob2 = isClient ? 'bg-indigo-500' : 'bg-emerald-500'
  const blob3 = isClient ? 'bg-sky-500' : 'bg-pink-500'

  const progressGradient = isClient
    ? 'bg-gradient-to-r from-blue-400 via-indigo-500 to-sky-500'
    : 'bg-gradient-to-r from-emerald-400 via-purple-500 to-pink-500'

  return (
    <div className="fixed inset-0 bg-black/65 backdrop-blur-lg flex items-center justify-center z-[9999] w-full h-full top-0 left-0">
      <div
        className={`relative rounded-2xl overflow-hidden border border-gray-700/50 shadow-2xl flex flex-col items-center gap-6 max-w-md w-full mx-4 p-8 ${cardBg}`}
      >
        {/* Animated gradient blobs */}
        <div className="absolute inset-0 overflow-hidden rounded-2xl">
          <div className={`absolute -top-40 -right-40 w-80 h-80 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob ${blob1}`} />
          <div className={`absolute -bottom-40 -left-40 w-80 h-80 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000 ${blob2}`} />
          <div className={`absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000 ${blob3}`} />
        </div>

        {/* Content */}
        <div className="relative z-10 flex flex-col items-center text-center w-full">
          <h3 className="text-xl font-bold text-white mb-2">{title}</h3>
          <p className="text-gray-300 text-sm mb-6">{description}</p>
          <div className="w-full bg-gray-800/80 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-300 ${progressGradient} animate-pulse`}
              style={{ width: '100%' }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
