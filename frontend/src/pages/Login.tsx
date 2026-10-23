import React, { useState } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { GraduationCap, ShieldAlert, LogIn, LogOut, CheckCircle2 } from 'lucide-react'

export const Login: React.FC = () => {
  const { session, user, role, profileStatus, signInWithEmail, signOut, isConfigured } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/'

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg(null)
    setSubmitting(true)

    try {
      const { error } = await signInWithEmail(email, password)
      if (error) {
        setErrorMsg(error.message)
      } else {
        navigate(from, { replace: true })
      }
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'An unexpected error occurred during sign in.')
    } finally {
      setSubmitting(false)
    }
  }

  // If already authenticated, show current session status
  if (session && user) {
    return (
      <div className="max-w-md mx-auto my-10 p-6 bg-white border border-slate-200 rounded-xl shadow-sm text-slate-900">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-600">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900">Active Authentication Session</h2>
            <p className="text-xs text-slate-500 font-mono">{user.email}</p>
          </div>
        </div>

        <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 mb-6 text-xs space-y-1.5">
          <div className="flex justify-between">
            <span className="text-slate-500">Verified Role:</span>
            <span className="font-semibold text-slate-800">
              {role ? role.toUpperCase() : 'Pending Backend Sync'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-500">Sync Status:</span>
            <span className="text-slate-700 capitalize font-mono text-[11px]">{profileStatus}</span>
          </div>
        </div>

        <div className="space-y-2">
          <Link
            to="/student/portal"
            className="block w-full py-2 px-3 text-center text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
          >
            Access Student Portal
          </Link>
          <Link
            to="/teacher/portal"
            className="block w-full py-2 px-3 text-center text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg transition-colors"
          >
            Access Teacher Portal
          </Link>
          <button
            type="button"
            onClick={() => signOut()}
            className="flex items-center justify-center space-x-1.5 w-full py-2 px-3 text-xs font-medium text-rose-600 border border-rose-200 hover:bg-rose-50 rounded-lg transition-colors pt-2"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-md mx-auto my-10 p-6 bg-white border border-slate-200 rounded-xl shadow-sm text-slate-900">
      <div className="flex items-center space-x-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center text-white">
          <GraduationCap className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-slate-900">Sign in to Quizdesk</h1>
          <p className="text-xs text-slate-500">Institutional assessment & examination portal</p>
        </div>
      </div>

      {/* Portal entry cards removed to keep student and faculty logins strictly segregated */}

      {!isConfigured && (
        <div className="mb-5 p-3.5 bg-amber-50 border border-amber-200 rounded-lg text-xs text-slate-700">
          <div className="flex items-center space-x-2 text-amber-900 font-semibold mb-1">
            <ShieldAlert className="w-4 h-4 text-amber-600" />
            <span>Local Development Notice</span>
          </div>
          <p className="text-slate-600 leading-relaxed">
            Live authentication requires valid keys in{' '}
            <code className="bg-amber-100 font-mono text-[11px] px-1 rounded">frontend/.env.local</code>.
          </p>
        </div>
      )}

      {errorMsg && (
        <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700">
          {errorMsg}
        </div>
      )}

      <form onSubmit={handleSignIn} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-xs font-medium text-slate-700 mb-1">
            Institutional Email
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="student@college.edu"
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <div>
          <label htmlFor="password" className="block text-xs font-medium text-slate-700 mb-1">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        <button
          type="submit"
          disabled={submitting || !isConfigured}
          className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
        >
          <LogIn className="w-4 h-4" />
          <span>{submitting ? 'Verifying...' : 'Sign In'}</span>
        </button>
      </form>
    </div>
  )
}
