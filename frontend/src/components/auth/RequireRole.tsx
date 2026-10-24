import React, { type PropsWithChildren } from 'react'
import { Navigate, useLocation, useNavigate, Link, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import type { UserRole } from '../../types/auth'
import { Shield, ShieldAlert, ShieldX, Loader2, RefreshCw, Home, LogOut } from 'lucide-react'

interface RequireRoleProps extends PropsWithChildren {
  allowedRoles: UserRole[]
}

export const RequireRole: React.FC<RequireRoleProps> = ({ allowedRoles, children }) => {
  const { session, user, role, loading, isConfigured, profileStatus, profileError, refreshProfile, signOut } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  // Helper to determine the role-appropriate login route
  const getLoginRoute = () => {
    if (
      allowedRoles.includes('admin') ||
      location.pathname.startsWith('/admin') ||
      location.pathname === '/status'
    ) {
      return '/admin/login'
    }
    if (
      allowedRoles.includes('teacher') ||
      location.pathname.startsWith('/teacher')
    ) {
      return '/teacher/login'
    }
    return '/student/login'
  }

  // 1. Initial hydration loading state - prevents flashing
  if (loading || (session && profileStatus === 'loading')) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
        <p className="text-sm font-medium text-slate-600">Resolving authoritative role permissions...</p>
      </div>
    )
  }

  // 2. Unconfigured environment notice during local development
  if (!isConfigured) {
    return (
      <div className="max-w-md mx-auto my-12 p-6 bg-amber-50 border border-amber-200 rounded-lg text-slate-800">
        <div className="flex items-center space-x-3 mb-3">
          <ShieldAlert className="w-6 h-6 text-amber-600" />
          <h2 className="text-base font-semibold text-amber-900">Supabase Not Configured</h2>
        </div>
        <p className="text-sm text-slate-600">
          Role-protected areas require live authentication. Please supply your Supabase project credentials in{' '}
          <code className="text-xs bg-amber-100 px-1 py-0.5 rounded font-mono">frontend/.env.local</code>.
        </p>
      </div>
    )
  }

  // 3. Unauthenticated state - redirect to role-specific login
  if (!session || !user) {
    return <Navigate to={getLoginRoute()} state={{ from: location }} replace />
  }

  // 4. Role resolution pending backend implementation (DEC-015: never guess role from client metadata)
  if (profileStatus === 'endpoint_unavailable' || role === null) {
    return (
      <div className="max-w-lg mx-auto my-12 p-6 bg-slate-900 border border-slate-800 rounded-xl text-white shadow-lg">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-blue-900/60 border border-blue-700/50 flex items-center justify-center text-blue-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Authoritative Role Pending</h2>
            <p className="text-xs text-slate-400">Identity authenticated, awaiting backend profile sync</p>
          </div>
        </div>

        <div className="p-3 bg-slate-800/80 rounded-lg border border-slate-700/60 mb-5 text-xs text-slate-300 space-y-2">
          <div className="flex justify-between">
            <span className="text-slate-400">Authenticated Identity:</span>
            <span className="font-mono text-blue-300">{user.email}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Assigned Role:</span>
            <span className="text-amber-400 font-medium">Unknown (Pending Backend Sync)</span>
          </div>
          {profileError && (
            <p className="text-[11px] text-amber-300/80 pt-1 border-t border-slate-700/50 font-mono">
              Notice: {profileError}
            </p>
          )}
        </div>

        <p className="text-xs text-slate-300 mb-6 leading-relaxed">
          In Quizdesk, permissions are strictly governed by the backend database (<code className="text-slate-200 font-mono">users.role</code>),
          never assumed from client metadata. Access will be unlocked once the profile synchronization endpoint is deployed.
        </p>

        <div className="flex flex-wrap items-center gap-3">
          {location.pathname.startsWith('/admin') && (
            <Link
              to="/admin/login"
              className="flex items-center space-x-1.5 px-3.5 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors"
            >
              <Shield className="w-3.5 h-3.5" />
              <span>Admin Provisioning Console</span>
            </Link>
          )}
          <button
            type="button"
            onClick={() => refreshProfile()}
            className="flex items-center space-x-2 px-3.5 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Profile Resolution</span>
          </button>
          <Link
            to="/"
            className="flex items-center space-x-1.5 px-3.5 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium transition-colors"
          >
            <Home className="w-3.5 h-3.5 text-slate-400" />
            <span>Home</span>
          </Link>
          <button
            type="button"
            onClick={async () => {
              const target = getLoginRoute()
              await signOut()
              navigate(target, { replace: true })
            }}
            className="flex items-center space-x-1.5 px-3.5 py-2 text-rose-400 hover:bg-rose-950/40 rounded-lg text-xs font-medium transition-colors ml-auto cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    )
  }

  // 5. Role mismatch (403 Forbidden state)
  if (!allowedRoles.includes(role)) {
    return (
      <div className="max-w-md mx-auto my-12 p-6 bg-rose-50 border border-rose-200 rounded-xl text-slate-900 shadow-sm">
        <div className="flex items-center space-x-3 mb-3">
          <div className="w-10 h-10 rounded-lg bg-rose-100 flex items-center justify-center text-rose-600">
            <ShieldX className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-rose-900">Access Restricted (403)</h2>
            <p className="text-xs text-rose-700">Insufficient role permissions</p>
          </div>
        </div>

        <p className="text-xs text-slate-600 mb-4 leading-relaxed">
          This portal section requires one of the following roles:{' '}
          <strong className="text-slate-800">{allowedRoles.join(' or ')}</strong>.
          Your current verified role is <strong className="text-slate-800">{role}</strong>.
        </p>

        <div className="pt-2 flex items-center space-x-3">
          <Link
            to="/"
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-medium transition-colors"
          >
            <Home className="w-3.5 h-3.5" />
            <span>Return to Home</span>
          </Link>
          <button
            type="button"
            onClick={async () => {
              const target = getLoginRoute()
              await signOut()
              navigate(target, { replace: true })
            }}
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 border border-slate-300 hover:bg-slate-100 text-slate-700 rounded-lg text-xs font-medium transition-colors cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>
      </div>
    )
  }

  // 6. Role authorized
  return children ? <>{children}</> : <Outlet />
}
