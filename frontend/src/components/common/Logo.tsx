import React from 'react'

interface LogoProps {
  className?: string
  showSubtitle?: boolean
  subtitle?: string
  size?: 'sm' | 'md' | 'lg'
}

export const Logo: React.FC<LogoProps> = ({
  className = '',
  showSubtitle = true,
  subtitle = 'MIT Academy of Engineering',
  size = 'md',
}) => {
  const containerSizes = {
    sm: 'w-8 h-8 rounded-lg',
    md: 'w-11 h-11 rounded-xl',
    lg: 'w-14 h-14 rounded-2xl',
  }

  const iconSizes = {
    sm: 'w-5 h-5',
    md: 'w-7 h-7',
    lg: 'w-9 h-9',
  }

  const titleSizes = {
    sm: 'text-base',
    md: 'text-xl',
    lg: 'text-2xl',
  }

  const subtitleSizes = {
    sm: 'text-[10px]',
    md: 'text-xs',
    lg: 'text-sm',
  }

  return (
    <div className={`flex items-center space-x-3 ${className}`}>
      {/* High-Definition Brand Mark */}
      <div
        className={`${containerSizes[size]} relative flex items-center justify-center bg-gradient-to-br from-blue-500 via-indigo-600 to-blue-700 shadow-lg shadow-indigo-600/30 text-white shrink-0 ring-1 ring-white/20 transition-transform duration-200 hover:scale-105`}
      >
        <svg
          viewBox="0 0 40 40"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className={iconSizes[size]}
        >
          {/* Subtle Inner Card Backdrop */}
          <rect
            x="8"
            y="8"
            width="24"
            height="24"
            rx="5"
            fill="white"
            fillOpacity="0.16"
          />
          {/* Distinct Assessment Checkmark */}
          <path
            d="M13 20.5L18 25.5L27 14.5"
            stroke="white"
            strokeWidth="3.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Focus Accent Spark */}
          <circle cx="28.5" cy="27.5" r="2.5" fill="#38BDF8" />
        </svg>
      </div>

      {/* Brand Typography */}
      <div className="flex flex-col justify-center leading-tight">
        <div className="flex items-center space-x-1.5">
          <span className={`font-extrabold tracking-tight text-white ${titleSizes[size]}`}>
            Quizdesk
          </span>
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400"></span>
        </div>
        {showSubtitle && (
          <span className={`text-slate-300 font-medium tracking-normal ${subtitleSizes[size]}`}>
            {subtitle}
          </span>
        )}
      </div>
    </div>
  )
}
