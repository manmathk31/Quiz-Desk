import React from 'react'
import { useAuth } from '../context/AuthContext'
import { ShieldCheck, CheckCircle2 } from 'lucide-react'

export const TeacherPortalPlaceholder: React.FC = () => {
  const { user, role } = useAuth()

  return (
    <div className="max-w-2xl mx-auto my-8 p-6 bg-white border border-slate-200 rounded-xl shadow-sm text-slate-900">
      <div className="flex items-center space-x-3 mb-4">
        <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-600">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-slate-900">Teacher & Faculty Management Area</h1>
          <p className="text-xs text-slate-500">Protected route verifying teacher/admin role guard</p>
        </div>
      </div>

      <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-900 space-y-1 mb-4">
        <div className="flex items-center space-x-1.5 font-semibold text-emerald-800">
          <CheckCircle2 className="w-4 h-4" />
          <span>Route Guard Succeeded</span>
        </div>
        <p className="text-emerald-700">
          Authenticated User: <span className="font-mono">{user?.email}</span> | Verified Role:{' '}
          <span className="font-mono font-bold uppercase">{role}</span>
        </p>
      </div>

      <p className="text-sm text-slate-600 leading-relaxed">
        This is a placeholder demonstrating successful evaluation of the{' '}
        <code className="text-xs bg-slate-100 px-1 py-0.5 rounded font-mono">
          RequireRole(['teacher', 'admin'])
        </code>{' '}
        guard. Assessment authoring tools and roster CSV engines will be implemented in Phase 4.
      </p>
    </div>
  )
}
