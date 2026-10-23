import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { ShieldAlert, LogIn, CheckCircle2 } from 'lucide-react'
import { Logo } from '../../components/common/Logo'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const StudentLogin: React.FC = () => {
  const { session, user, role, signInWithEmail, isConfigured } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const navigate = useNavigate()

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg(null)
    setSubmitting(true)

    const trimmedEmail = email.trim().toLowerCase()
    const trimmedPassword = password.trim()

    try {
      // 1. Attempt standard Supabase Auth sign-in
      const { error } = await signInWithEmail(trimmedEmail, trimmedPassword)
      if (!error) {
        navigate('/student/portal', { replace: true })
        return
      }

      // 2. If sign-in failed (student not yet activated in Supabase Auth),
      // attempt first-time activation using PRN as initial password
      try {
        const activateRes = await fetch(`${API_BASE_URL}/api/v1/auth/student-activate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: trimmedEmail, prn: trimmedPassword }),
        })

        if (activateRes.ok) {
          // Activation created or synced account in Supabase; retry sign-in
          const retry = await signInWithEmail(trimmedEmail, trimmedPassword)
          if (!retry.error) {
            navigate('/student/portal', { replace: true })
            return
          }
        } else if (activateRes.status === 401) {
          const errData = await activateRes.json().catch(() => ({}))
          setErrorMsg(
            errData.detail ||
              'Invalid credentials. If this is your first time logging in, your initial password is your enrolled PRN.'
          )
          return
        }
      } catch {
        // Fall back to original error message
      }

      setErrorMsg(
        error.message === 'Invalid login credentials'
          ? 'Invalid credentials. If this is your first time logging in, your initial password is your enrolled PRN.'
          : error.message
      )
    } catch (err: unknown) {
      setErrorMsg(
        err instanceof Error ? err.message : 'An unexpected error occurred during sign in.'
      )
    } finally {
      setSubmitting(false)
    }
  }

  if (session && user) {
    return (
      <div className="max-w-md mx-auto my-12 p-6 bg-white border border-slate-200 rounded-xl shadow-sm text-slate-900">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-600">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900">Signed In</h2>
            <p className="text-xs text-slate-500 font-mono">{user.email}</p>
          </div>
        </div>

        <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 mb-6 text-xs">
          <span className="text-slate-500">Active Role: </span>
          <strong className="text-slate-800 uppercase">{role || 'Student'}</strong>
        </div>

        <Link
          to="/student/portal"
          className="block w-full py-2.5 px-3 text-center text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
        >
          Go to Student Dashboard
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-md mx-auto my-12 p-6 sm:p-8 bg-white border border-slate-200 rounded-2xl shadow-sm text-slate-900">
      <div className="flex items-center space-x-3.5 mb-6">
        <Logo size="lg" showSubtitle={false} />
        <div>
          <h1 className="text-lg font-bold text-slate-900">Student Sign In</h1>
          <p className="text-xs text-slate-500">Sign in to view your quizzes</p>
        </div>
      </div>

      {!isConfigured && (
        <div className="mb-5 p-3.5 bg-amber-50 border border-amber-200 rounded-lg text-xs text-slate-700">
          <div className="flex items-center space-x-2 text-amber-900 font-semibold mb-1">
            <ShieldAlert className="w-4 h-4 text-amber-600" />
            <span>Development Notice</span>
          </div>
          <p className="text-slate-600 leading-relaxed">
            Authentication requires credentials configured in{' '}
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
          <label htmlFor="student-email" className="block text-xs font-medium text-slate-700 mb-1">
            College Email Address
          </label>
          <input
            id="student-email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="student@mitaoe.ac.in"
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label htmlFor="student-password" className="block text-xs font-medium text-slate-700">
              Password
            </label>
            <span className="text-[11px] text-blue-600 font-medium">
              First time? Use your PRN
            </span>
          </div>
          <input
            id="student-password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your PRN or custom password"
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <button
          type="submit"
          disabled={submitting || !isConfigured}
          className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors cursor-pointer"
        >
          <LogIn className="w-4 h-4" />
          <span>{submitting ? 'Signing in...' : 'Sign In'}</span>
        </button>
      </form>
    </div>
  )
}

