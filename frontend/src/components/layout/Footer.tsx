import React from 'react'

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 border-t border-slate-800 text-slate-400 text-sm mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-xs">
          <div className="flex items-center space-x-2">
            <span className="font-semibold text-slate-300">Quizdesk</span>
            <span className="text-slate-600">•</span>
            <span className="text-slate-400">MIT Academy of Engineering</span>
          </div>

          <div className="text-slate-500">
            A simple and secure quiz platform for college tests and quizzes.
          </div>
        </div>
      </div>
    </footer>
  )
}
