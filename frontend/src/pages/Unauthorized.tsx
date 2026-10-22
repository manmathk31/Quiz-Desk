import React from 'react'
import { Link } from 'react-router-dom'
import { ShieldX, Home } from 'lucide-react'

export const Unauthorized: React.FC = () => {
  return (
    <div className="max-w-md mx-auto my-16 p-8 bg-white border border-slate-200 rounded-xl shadow-sm text-center">
      <div className="w-14 h-14 bg-rose-100 rounded-full flex items-center justify-center text-rose-600 mx-auto mb-4">
        <ShieldX className="w-8 h-8" />
      </div>
      <h1 className="text-xl font-bold text-slate-900 mb-2">Access Denied (403)</h1>
      <p className="text-sm text-slate-600 mb-6 leading-relaxed">
        You do not possess the required institutional role to access this section of Quizdesk.
      </p>
      <Link
        to="/"
        className="inline-flex items-center space-x-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-sm font-medium transition-colors"
      >
        <Home className="w-4 h-4" />
        <span>Return to Home</span>
      </Link>
    </div>
  )
}
