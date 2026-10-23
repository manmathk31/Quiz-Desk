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

      <div className="mt-6 pt-6 border-t border-slate-200">
        <h2 className="text-sm font-bold text-slate-900 mb-3">Available Authoring Modules</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <a
            href="/teacher/question-bank"
            className="p-4 rounded-xl border border-blue-200 bg-blue-50/50 hover:bg-blue-50 hover:border-blue-300 transition-colors block text-left group"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-blue-900 group-hover:text-blue-700">
                Question Bank & Import
              </span>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-200 text-blue-800">
                Live
              </span>
            </div>
            <p className="text-xs text-slate-600">
              Create, edit, search, and bulk-import reusable questions from CSV or Excel files with line-by-line validation.
            </p>
          </a>

          <a
            href="/teacher/quizzes"
            className="p-4 rounded-xl border border-indigo-200 bg-indigo-50/50 hover:bg-indigo-50 hover:border-indigo-300 transition-colors block text-left group"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-indigo-900 group-hover:text-indigo-700">
                Quiz Builder & Publishing
              </span>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                Milestone 4B
              </span>
            </div>
            <p className="text-xs text-slate-600">
              Draft quizzes, clone questions from bank, configure proctoring & time limits, and publish immutable version snapshots.
            </p>
          </a>
        </div>
      </div>
    </div>
  )
}

