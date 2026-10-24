import React, { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import {
  Shield,
  ShieldAlert,
  LogIn,
  CheckCircle2,
  KeyRound,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Loader2,
  ArrowRight,
  GraduationCap,
  BookOpen,
  LogOut,
} from 'lucide-react'
import { bootstrapAdminUser } from '../../services/adminApi'

export const AdminLogin: React.FC = () => {
  const { session, user, role, signInWithEmail, isConfigured, refreshProfile, signOut } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Bootstrap helper state
  const [bootstrapToken, setBootstrapToken] = useState('')
  const [bootstrapping, setBootstrapping] = useState(false)
  const [bootstrapSuccess, setBootstrapSuccess] = useState<string | null>(null)

  const navigate = useNavigate()

  // Auto-redirect to dashboard if authenticated and verified as admin
  useEffect(() => {
    if (session && user && role === 'admin') {
      navigate('/admin/dashboard', { replace: true })
    }
  }, [session, user, role, navigate])

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMsg(null)
    setSubmitting(true)

    try {
      const { error } = await signInWithEmail(email.trim().toLowerCase(), password)
      if (error) {
        setErrorMsg(error.message)
      }
      // On success, do NOT immediately navigate. If user is already provisioned as admin,
      // the useEffect above will redirect them to /admin/dashboard. If unprovisioned,
      // they stay on this page to enter the bootstrap token.
    } catch (err: unknown) {
      setErrorMsg(
        err instanceof Error ? err.message : 'An unexpected error occurred during admin sign in.'
      )
    } finally {
      setSubmitting(false)
    }
  }

  const handleBootstrap = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!session?.access_token) {
      setErrorMsg('Please sign in with your Supabase account first before bootstrapping admin role.')
      return
    }

    setBootstrapping(true)
    setErrorMsg(null)
    setBootstrapSuccess(null)

    try {
      const res = await bootstrapAdminUser(session.access_token, bootstrapToken)
      setBootstrapSuccess(`Successfully provisioned administrator account for ${res.email}`)
      await refreshProfile()
      setTimeout(() => {
        navigate('/admin/dashboard', { replace: true })
      }, 1500)
    } catch (err: unknown) {
      setErrorMsg(
        err instanceof Error ? err.message : 'Failed to provision administrator account.'
      )
    } finally {
      setBootstrapping(false)
    }
  }

  if (session && user) {
    const isAdmin = role === 'admin'

    return (
      <div className="relative min-h-[calc(100vh-14rem)] flex flex-col justify-center items-center py-6 sm:py-10">
        <div className="relative w-full max-w-md mx-auto bg-white/95 backdrop-blur-md border border-slate-200/80 rounded-2xl shadow-xl shadow-slate-200/50 p-7 sm:p-8 overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-amber-500 to-amber-600" />

          <div className="flex items-center space-x-3 mb-5">
            <div className="w-11 h-11 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600">
              <Shield className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                Administrative Session
              </span>
              <h2 className="text-base font-bold text-slate-900 mt-0.5">Control Console</h2>
              <p className="text-xs text-slate-500 font-mono truncate max-w-[240px]">{user.email}</p>
            </div>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 mb-6 text-xs flex justify-between items-center">
            <span className="text-slate-500">System Role:</span>
            <span className={`font-bold uppercase px-2.5 py-0.5 rounded-md border ${
              isAdmin
                ? 'text-amber-800 bg-amber-50 border-amber-200'
                : 'text-slate-700 bg-slate-100 border-slate-200'
            }`}>
              {role || 'Pending Promotion'}
            </span>
          </div>

          {isAdmin ? (
            <Link
              to="/admin/dashboard"
              className="flex items-center justify-between w-full py-3 px-4 text-xs font-semibold text-white bg-slate-900 hover:bg-slate-800 active:scale-[0.99] rounded-xl shadow-md transition-all cursor-pointer"
            >
              <span>Access Operational Dashboard</span>
              <ArrowRight className="w-4 h-4 text-amber-400" />
            </Link>
          ) : (
            <div className="space-y-4">
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 leading-relaxed">
                Your account is authenticated via Supabase, but is not yet provisioned with the{' '}
                <strong>admin</strong> role in the application database. If this account is the
                designated administrator, use the bootstrap action below.
              </div>

              {errorMsg && (
                <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700">
                  {errorMsg}
                </div>
              )}

              {bootstrapSuccess && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>{bootstrapSuccess}</span>
                </div>
              )}

              <form onSubmit={handleBootstrap} className="space-y-3 pt-1">
                <div>
                  <label htmlFor="bootstrap-token" className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                    Server Bootstrap Token
                  </label>
                  <div className="relative group">
                    <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 group-focus-within:text-amber-600">
                      <KeyRound className="w-4 h-4" />
                    </div>
                    <input
                      id="bootstrap-token"
                      type="password"
                      value={bootstrapToken}
                      onChange={(e) => setBootstrapToken(e.target.value)}
                      placeholder="Enter server token if configured"
                      className="w-full pl-10 pr-3.5 py-2.5 bg-slate-50/60 hover:bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 font-mono focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-600 transition-all"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={bootstrapping}
                  className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-amber-600 hover:bg-amber-700 active:scale-[0.99] disabled:opacity-50 text-white rounded-xl text-xs font-semibold shadow-md shadow-amber-600/20 transition-all cursor-pointer"
                >
                  <KeyRound className="w-3.5 h-3.5" />
                  <span>{bootstrapping ? 'Provisioning...' : 'Provision Administrator Account'}</span>
                </button>
              </form>

              {/* Session utility footer */}
              <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs">
                <Link
                  to="/student/login"
                  className="inline-flex items-center space-x-1 font-semibold text-blue-600 hover:text-blue-700 transition-colors"
                >
                  <GraduationCap className="w-3.5 h-3.5" />
                  <span>Student Entrance</span>
                </Link>
                <button
                  type="button"
                  onClick={() => signOut()}
                  className="inline-flex items-center space-x-1 font-semibold text-rose-600 hover:text-rose-700 transition-colors cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="relative min-h-[calc(100vh-14rem)] flex flex-col justify-center items-center py-6 sm:py-10">
      {/* Ambient background glow orbs */}
      <div className="absolute top-1/4 -left-12 w-72 h-72 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 -right-12 w-72 h-72 bg-slate-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative w-full max-w-md mx-auto bg-white/95 backdrop-blur-md border border-slate-200/80 rounded-2xl shadow-xl shadow-slate-200/50 p-7 sm:p-9 overflow-hidden">
        {/* Top accent gradient bar */}
        <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-slate-800 via-amber-500 to-slate-900" />

        {/* Header Block */}
        <div className="flex items-center space-x-3.5 mb-6">
          <div className="w-12 h-12 rounded-xl bg-slate-900 flex items-center justify-center text-amber-400 shadow-md">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <div className="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-full bg-amber-50 border border-amber-200 text-[10px] font-bold text-amber-800 uppercase tracking-wider mb-0.5">
              <span>Restricted System Gateway</span>
            </div>
            <h1 className="text-xl font-extrabold text-slate-900 tracking-tight">Admin Console</h1>
            <p className="text-xs text-slate-500">Platform operations, audits, and governance</p>
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
            <label htmlFor="admin-email" className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Administrator Email
            </label>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 group-focus-within:text-amber-600 transition-colors">
                <Mail className="w-4 h-4" />
              </div>
              <input
                id="admin-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@institution.edu"
                className="w-full pl-10 pr-3.5 py-2.5 bg-slate-50/60 hover:bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-600 transition-all"
              />
            </div>
          </div>

          <div>
            <label htmlFor="admin-password" className="block text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Password
            </label>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 group-focus-within:text-amber-600 transition-colors">
                <Lock className="w-4 h-4" />
              </div>
              <input
                id="admin-password"
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter administrator password"
                className="w-full pl-10 pr-10 py-2.5 bg-slate-50/60 hover:bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-600 transition-all"
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

          <button
            type="submit"
            disabled={submitting || !isConfigured}
            className="w-full flex items-center justify-center space-x-2 py-3 px-4 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl text-sm font-semibold shadow-lg shadow-slate-900/25 active:scale-[0.99] transition-all cursor-pointer mt-2"
          >
            {submitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-amber-400" />
                <span>Verifying Access...</span>
              </>
            ) : (
              <>
                <LogIn className="w-4 h-4 text-amber-400" />
                <span>Sign In to Admin Portal</span>
              </>
            )}
          </button>
        </form>

        {/* Cross-portal switcher */}
        <div className="mt-6 pt-5 border-t border-slate-100 flex items-center justify-between text-xs">
          <Link
            to="/student/login"
            className="inline-flex items-center space-x-1 font-semibold text-blue-600 hover:text-blue-700 transition-colors"
          >
            <GraduationCap className="w-3.5 h-3.5" />
            <span>Student Entrance</span>
          </Link>
          <Link
            to="/teacher/login"
            className="inline-flex items-center space-x-1 font-semibold text-indigo-600 hover:text-indigo-700 transition-colors"
          >
            <BookOpen className="w-3.5 h-3.5" />
            <span>Faculty Portal</span>
          </Link>
        </div>
      </div>
    </div>
  )
}
