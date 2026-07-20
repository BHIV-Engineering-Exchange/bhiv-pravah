import { Outlet } from 'react-router-dom';
import { Building2 } from 'lucide-react';
import { useTheme } from '../../hooks/useTheme.jsx';
import clsx from 'clsx';

const AuthLayout = () => {
  const { isUniverseMode, isDarkMode } = useTheme();

  return (
    <div className="min-h-screen flex">
      {/* Left side - Branding */}
      <div className={clsx(
        'hidden lg:flex lg:w-1/2 p-12 flex-col justify-between relative overflow-hidden',
        isUniverseMode
          ? 'bg-gradient-to-br from-[hsl(270,60%,12%)] via-[hsl(240,40%,10%)] to-[hsl(300,50%,8%)]'
          : isDarkMode
            ? 'bg-gradient-to-br from-[hsl(228,30%,12%)] via-[hsl(225,25%,15%)] to-[hsl(230,20%,10%)]'
            : 'bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800'
      )}>
        {isUniverseMode && (
          <>
            <div className="absolute inset-0 opacity-40">
              <div className="absolute top-[10%] left-[15%] w-2 h-2 bg-purple-400 rounded-full animate-pulse" />
              <div className="absolute top-[30%] right-[20%] w-1.5 h-1.5 bg-cyan-400 rounded-full animate-pulse" style={{ animationDelay: '0.5s' }} />
              <div className="absolute top-[60%] left-[40%] w-1 h-1 bg-white rounded-full animate-pulse" style={{ animationDelay: '1s' }} />
              <div className="absolute top-[80%] right-[30%] w-2 h-2 bg-pink-400 rounded-full animate-pulse" style={{ animationDelay: '1.5s' }} />
              <div className="absolute top-[45%] left-[70%] w-1 h-1 bg-purple-300 rounded-full animate-pulse" style={{ animationDelay: '2s' }} />
              <div className="absolute top-[20%] left-[60%] w-1.5 h-1.5 bg-cyan-300 rounded-full animate-pulse" style={{ animationDelay: '0.8s' }} />
            </div>
            <div className="absolute inset-0"
              style={{
                background: 'radial-gradient(ellipse 80% 60% at 20% 80%, hsl(270 100% 40% / 0.15) 0%, transparent 60%), radial-gradient(ellipse 60% 50% at 80% 20%, hsl(190 100% 45% / 0.1) 0%, transparent 60%)',
              }}
            />
          </>
        )}

        {isDarkMode && !isUniverseMode && (
          <div className="absolute inset-0"
            style={{
              background: 'radial-gradient(ellipse 70% 50% at 30% 70%, hsl(160 84% 48% / 0.08) 0%, transparent 60%), radial-gradient(ellipse 50% 40% at 70% 30%, hsl(262 83% 65% / 0.06) 0%, transparent 60%)',
            }}
          />
        )}

        <div className="relative z-10">
          <div className="flex items-center gap-3">
            <div className={clsx(
              'w-12 h-12 rounded-xl flex items-center justify-center',
              isUniverseMode
                ? 'bg-gradient-to-br from-purple-500 via-pink-500 to-cyan-400 shadow-lg shadow-purple-500/30'
                : isDarkMode
                  ? 'bg-white/10 backdrop-blur-sm border border-white/10'
                  : 'bg-white/20'
            )}>
              <Building2 className="w-7 h-7 text-white" />
            </div>
            <span className={clsx(
              'text-2xl font-bold text-white',
              isUniverseMode && 'bg-gradient-to-r from-purple-300 via-cyan-300 to-pink-300 bg-clip-text text-transparent'
            )}>
              ARTHA
            </span>
          </div>
        </div>
        
        <div className="space-y-6 relative z-10">
          <h1 className="text-4xl font-bold text-white leading-tight">
            Modern Accounting<br />for Modern Business
          </h1>
          <p className={clsx(
            'text-lg max-w-md',
            isUniverseMode ? 'text-purple-200/80' : isDarkMode ? 'text-blue-200/80' : 'text-blue-100'
          )}>
            Streamline your financial operations with India-compliant accounting, 
            GST filing, and real-time insights.
          </p>
          
          <div className="grid grid-cols-2 gap-4 mt-8">
            {[
              { value: '100%', label: 'GST Compliant' },
              { value: 'Real-time', label: 'Financial Insights' },
              { value: 'Secure', label: 'Hash-Chain Ledger' },
              { value: 'OCR', label: 'Receipt Scanning' },
            ].map((stat) => (
              <div key={stat.label} className={clsx(
                'rounded-lg p-4 transition-all duration-300',
                isUniverseMode
                  ? 'bg-white/5 border border-purple-500/20 backdrop-blur-sm hover:border-purple-400/40'
                  : isDarkMode
                    ? 'bg-white/5 border border-white/10 backdrop-blur-sm hover:bg-white/10'
                    : 'bg-white/10 hover:bg-white/15'
              )}>
                <div className="text-3xl font-bold text-white">{stat.value}</div>
                <div className={clsx(
                  'text-sm',
                  isUniverseMode ? 'text-purple-300/70' : isDarkMode ? 'text-blue-300/70' : 'text-blue-200'
                )}>
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className={clsx(
          'text-sm relative z-10',
          isUniverseMode ? 'text-purple-300/50' : isDarkMode ? 'text-blue-300/50' : 'text-blue-200'
        )}>
          &copy; 2026 Artha Financial Solutions. All rights reserved.
        </div>
      </div>

      {/* Right side - Auth form */}
      <div className={clsx(
        'flex-1 flex items-center justify-center p-8',
        isUniverseMode ? 'bg-background' : isDarkMode ? 'bg-background' : 'bg-muted'
      )}>
        <div className="w-full max-w-md">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
