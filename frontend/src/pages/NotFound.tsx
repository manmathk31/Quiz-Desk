import React from 'react'
import { Link } from 'react-router-dom'
import { AlertCircle, ArrowLeft } from 'lucide-react'

export const NotFound: React.FC = () => {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-8 sm:p-12 text-center max-w-lg mx-auto">
      <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 mx-auto mb-4">
        <AlertCircle className="w-6 h-6" />
      </div>
      <h1 className="text-xl font-bold text-slate-900">Page Not Found</h1>
      <p className="text-sm text-slate-600 mt-2">
        The requested resource does not exist within the Quizdesk portal.
      </p>
      <div className="mt-6">
        <Link
          to="/"
          className="inline-flex items-center px-4 py-2 text-sm font-medium rounded-md bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-1.5" />
          Back to Overview
        </Link>
      </div>
    </div>
  )
}
