import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { GraduationCap, ShieldAlert, LogIn, CheckCircle2 } from 'lucide-react'

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

    try {
      const { error } = await signInWithEmail(email, password)
      if (error) {
        setErrorMsg(error.message)
      } else {
        navigate('/student/portal', { replace: true })
      }
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
            <h2 className="text-base font-semibold text-slate-900">Signed In to Student Portal</h2>
            <p className="text-xs text-slate-500 font-mono">{user.email}</p>
          </div>
        </div>

        <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 mb-6 text-xs">
          <span className="text-slate-500">Active Role: </span>
          <strong className="text-slate-800 uppercase">{role || 'Verifying...'}</strong>
        </div>

        <Link
          to="/student/portal"
          className="block w-full py-2.5 px-3 text-center text-xs font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
        >
          Go to Student Assessment Dashboard
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-md mx-auto my-12 p-6 bg-white border border-slate-200 rounded-xl shadow-sm text-slate-900">
      <div className="flex items-center space-x-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-blue-600 flex items-center justify-center text-white">
          <GraduationCap className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-slate-900">Student Portal Login</h1>
          <p className="text-xs text-slate-500">Access your scheduled college examinations and quizzes</p>
        </div>
      </div>

      {!isConfigured && (
        <div className="mb-5 p-3.5 bg-amber-50 border border-amber-200 rounded-lg text-xs text-slate-700">
          <div className="flex items-center space-x-2 text-amber-900 font-semibold mb-1">
            <ShieldAlert className="w-4 h-4 text-amber-600" />
            <span>Local Development Notice</span>
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
            Institutional Email Address
          </label>
          <input
            id="student-email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="student@college.edu"
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label htmlFor="student-password" className="block text-xs font-medium text-slate-700 mb-1">
            Student Password
          </label>
          <input
            id="student-password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <button
          type="submit"
          disabled={submitting || !isConfigured}
          className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
        >
          <LogIn className="w-4 h-4" />
          <span>{submitting ? 'Verifying Student Identity...' : 'Sign In to Assessment Portal'}</span>
        </button>
      </form>
    </div>
  )
}
