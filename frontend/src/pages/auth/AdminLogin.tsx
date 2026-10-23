import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { Shield, ShieldAlert, LogIn, CheckCircle2, KeyRound } from 'lucide-react'
import { bootstrapAdminUser } from '../../services/adminApi'

export const AdminLogin: React.FC = () => {
  const { session, user, role, signInWithEmail, isConfigured, refreshProfile } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Bootstrap helper state
  const [bootstrapToken, setBootstrapToken] = useState('')
  const [bootstrapping, setBootstrapping] = useState(false)
  const [bootstrapSuccess, setBootstrapSuccess] = useState<string | null>(null)

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
        navigate('/admin/dashboard', { replace: true })
      }
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
      <div className="max-w-md mx-auto my-12 p-6 bg-white border border-slate-200 rounded-xl shadow-sm text-slate-900">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center text-amber-600">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900">Signed In Session</h2>
            <p className="text-xs text-slate-500 font-mono">{user.email}</p>
          </div>
        </div>

        <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 mb-6 text-xs">
          <span className="text-slate-500">Authoritative System Role: </span>
          <strong className={`uppercase ${isAdmin ? 'text-amber-700' : 'text-slate-700'}`}>
            {role || 'Unregistered / Pending Profile'}
          </strong>
        </div>

        {isAdmin ? (
          <Link
            to="/admin/dashboard"
            className="block w-full py-2.5 px-3 text-center text-xs font-medium text-white bg-slate-900 hover:bg-slate-800 rounded-lg transition-colors"
          >
            Access Admin Operational Dashboard
          </Link>
        ) : (
          <div className="space-y-4">
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900 leading-relaxed">
              Your account is authenticated via Supabase, but is not yet provisioned with the{' '}
              <strong>admin</strong> role in the application database. If this account is the
              designated administrator, use the bootstrap action below.
            </div>

            {errorMsg && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700">
                {errorMsg}
              </div>
            )}

            {bootstrapSuccess && (
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>{bootstrapSuccess}</span>
              </div>
            )}

            <form onSubmit={handleBootstrap} className="space-y-3 pt-1">
              <div>
                <label htmlFor="bootstrap-token" className="block text-xs font-medium text-slate-700 mb-1">
                  Server Bootstrap Token (Optional if not set in server env)
                </label>
                <input
                  id="bootstrap-token"
                  type="password"
                  value={bootstrapToken}
                  onChange={(e) => setBootstrapToken(e.target.value)}
                  placeholder="Enter token if configured"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs text-slate-900 font-mono"
                />
              </div>

              <button
                type="submit"
                disabled={bootstrapping}
                className="w-full flex items-center justify-center space-x-2 py-2 px-3 bg-amber-600 hover:bg-amber-700 disabled:bg-slate-300 text-white rounded-lg text-xs font-medium transition-colors"
              >
                <KeyRound className="w-3.5 h-3.5" />
                <span>{bootstrapping ? 'Provisioning...' : 'Provision Administrator Account'}</span>
              </button>
            </form>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="max-w-md mx-auto my-12 p-6 bg-white border border-slate-200 rounded-xl shadow-sm text-slate-900">
      <div className="flex items-center space-x-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-slate-900 flex items-center justify-center text-white">
          <Shield className="w-6 h-6 text-amber-400" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-slate-900">Administrator Portal</h1>
          <p className="text-xs text-slate-500">Restricted operational administration & maintenance</p>
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
          <label htmlFor="admin-email" className="block text-xs font-medium text-slate-700 mb-1">
            Administrator Email
          </label>
          <input
            id="admin-email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@institution.edu"
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500"
          />
        </div>

        <div>
          <label htmlFor="admin-password" className="block text-xs font-medium text-slate-700 mb-1">
            Password
          </label>
          <input
            id="admin-password"
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-amber-500"
          />
        </div>

        <button
          type="submit"
          disabled={submitting || !isConfigured}
          className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
        >
          <LogIn className="w-4 h-4 text-amber-400" />
          <span>{submitting ? 'Verifying Admin Access...' : 'Sign In to Admin Portal'}</span>
        </button>
      </form>
    </div>
  )
}
