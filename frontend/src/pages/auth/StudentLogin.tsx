import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import {
  ShieldAlert,
  LogIn,
  CheckCircle2,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Loader2,
  ArrowRight,
  Info,
  GraduationCap,
} from 'lucide-react'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const StudentLogin: React.FC = () => {
  const { session, user, role, signInWithEmail, isConfigured } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
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
      <div className="relative min-h-[calc(100vh-14rem)] flex flex-col justify-center items-center py-6 sm:py-10">
        <div className="relative w-full max-w-md mx-auto bg-white/95 backdrop-blur-md border border-slate-200/80 rounded-2xl shadow-xl shadow-slate-200/50 p-7 sm:p-8 overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-blue-500 to-indigo-600" />

          <div className="flex items-center space-x-3 mb-5">
            <div className="w-11 h-11 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
                Active Student Session
              </span>
              <h2 className="text-base font-bold text-slate-900 mt-0.5">Enrolled Student</h2>
              <p className="text-xs text-slate-500 font-mono truncate max-w-[240px]">{user.email}</p>
            </div>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 mb-6 text-xs flex justify-between items-center">
            <span className="text-slate-500">Authorized Role:</span>
            <span className="font-bold text-blue-700 uppercase bg-blue-50 border border-blue-100 px-2.5 py-0.5 rounded-md">
              {role || 'Student'}
            </span>
          </div>

          <Link
            to="/student/portal"
            className="flex items-center justify-between w-full py-3 px-4 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 active:scale-[0.99] rounded-xl shadow-md shadow-blue-600/20 transition-all cursor-pointer"
          >
            <span>Proceed to Assessment Dashboard</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="relative min-h-[calc(100vh-14rem)] flex flex-col justify-center items-center py-6 sm:py-10">
      {/* Ambient background glow orbs */}
      <div className="absolute top-1/4 -left-12 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-12 w-72 h-72 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative w-full max-w-md mx-auto bg-white/95 backdrop-blur-md border border-slate-200/80 rounded-2xl shadow-xl shadow-slate-200/50 p-7 sm:p-9 overflow-hidden">
        {/* Top accent gradient bar */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-blue-600 via-indigo-600 to-cyan-500" />

        {/* Header Block */}
        <div className="flex items-center space-x-3.5 mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-600/25 shrink-0">
            <GraduationCap className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">Student Login</h1>
            <p className="text-xs text-slate-500 mt-0.5">Access your scheduled tests and assessments</p>
          </div>
        </div>

        {!isConfigured && (
          <div className="mb-5 p-3.5 bg-amber-50 border border-amber-200 rounded-xl text-xs text-slate-700">
            <div className="flex items-center space-x-2 text-amber-900 font-semibold mb-1">
              <ShieldAlert className="w-4 h-4 text-amber-600" />
              <span>Development Notice</span>
            </div>
            <p className="text-slate-600 leading-relaxed text-[11px]">
              Authentication requires credentials configured in{' '}
              <code className="bg-amber-100 font-mono text-[10px] px-1 py-0.5 rounded">frontend/.env.local</code>.
            </p>
          </div>
        )}

        {errorMsg && (
          <div className="mb-5 p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 leading-relaxed">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSignIn} className="space-y-4">
          <div>
            <label htmlFor="student-email" className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Institutional Email Address
            </label>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 group-focus-within:text-blue-600 transition-colors">
                <Mail className="w-4 h-4" />
              </div>
              <input
                id="student-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="student@mitaoe.ac.in"
                className="w-full pl-10 pr-3.5 py-2.5 bg-slate-50/60 hover:bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-all"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label htmlFor="student-password" className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider">
                Password
              </label>
              <span className="inline-flex items-center text-[11px] text-blue-600 font-semibold bg-blue-50 border border-blue-100 px-2 py-0.5 rounded-full">
                First time? PRN
              </span>
            </div>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 group-focus-within:text-blue-600 transition-colors">
                <Lock className="w-4 h-4" />
              </div>
              <input
                id="student-password"
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter PRN or custom password"
                className="w-full pl-10 pr-10 py-2.5 bg-slate-50/60 hover:bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-all"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 transition-colors cursor-pointer"
                title={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <div className="flex items-start space-x-2 p-2.5 bg-slate-50 border border-slate-200/70 rounded-xl text-[11px] text-slate-600">
            <Info className="w-3.5 h-3.5 text-blue-600 mt-0.5 flex-shrink-0" />
            <p>
              Your initial password is your enrolled <strong>PRN</strong>. You can change your password anytime in your dashboard profile.
            </p>
          </div>

          <button
            type="submit"
            disabled={submitting || !isConfigured}
            className="w-full flex items-center justify-center space-x-2 py-3 px-4 bg-gradient-to-r from-blue-600 via-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl text-sm font-semibold shadow-lg shadow-blue-600/25 active:scale-[0.99] transition-all cursor-pointer mt-2"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Signing In...</span>
              </>
            ) : (
              <>
                <LogIn className="w-4 h-4" />
                <span>Sign In to Assessments</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  )
}

