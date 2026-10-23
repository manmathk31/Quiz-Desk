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
  const iconSizes = {
    sm: 'w-7 h-7',
    md: 'w-9 h-9',
    lg: 'w-12 h-12',
  }

  const titleSizes = {
    sm: 'text-base',
    md: 'text-lg',
    lg: 'text-2xl',
  }

  return (
    <div className={`flex items-center space-x-2.5 ${className}`}>
      {/* Modern Custom Geometric Mark */}
      <div
        className={`${iconSizes[size]} relative flex items-center justify-center rounded-xl bg-gradient-to-br from-blue-600 via-indigo-600 to-blue-700 shadow-md shadow-blue-500/20 text-white shrink-0 overflow-hidden`}
      >
        <svg
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-5 h-5 text-white"
        >
          {/* Base Document / Desk Card */}
          <rect
            x="6"
            y="5"
            width="20"
            height="22"
            rx="4"
            className="stroke-white/30"
            strokeWidth="1.5"
            fill="currentColor"
            fillOpacity="0.08"
          />
          {/* Subtle Top Clip */}
          <path
            d="M12 5V4C12 3.44772 12.4477 3 13 3H19C19.5523 3 20 3.44772 20 4V5"
            className="stroke-white"
            strokeWidth="1.75"
            strokeLinecap="round"
          />
          {/* Checkmark Question Mark Combo */}
          <path
            d="M11 16.5L14.5 20L21 12"
            className="stroke-white"
            strokeWidth="2.25"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          {/* Spark Dot */}
          <circle cx="21" cy="20" r="1.5" className="fill-blue-200" />
        </svg>
      </div>

      {/* Brand Typography */}
      <div className="flex flex-col leading-none">
        <span className={`font-bold tracking-tight text-white ${titleSizes[size]}`}>
          Quizdesk
        </span>
        {showSubtitle && (
          <span className="text-[11px] text-slate-400 font-medium tracking-normal mt-0.5">
            {subtitle}
          </span>
        )}
      </div>
    </div>
  )
}
