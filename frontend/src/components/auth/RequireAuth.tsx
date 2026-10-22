import React, { type PropsWithChildren } from 'react'
import { Navigate, useLocation, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { ShieldAlert, Loader2, LogOut } from 'lucide-react'

export const RequireAuth: React.FC<PropsWithChildren> = ({ children }) => {
  const { session, user, loading, isConfigured, profileStatus, profileError, signOut } = useAuth()
  const location = useLocation()

  // 1. Initial hydration loading state or in-flight profile resolution - prevents protected content flashing
  if (loading || (session && profileStatus === 'loading')) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center space-y-4">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
        <p className="text-sm font-medium text-slate-600">Verifying authentication session...</p>
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
        <p className="text-sm text-slate-600 mb-4">
          Protected routes require valid Supabase credentials. Copy{' '}
          <code className="text-xs bg-amber-100 px-1 py-0.5 rounded font-mono">frontend/.env.example</code> to{' '}
          <code className="text-xs bg-amber-100 px-1 py-0.5 rounded font-mono">frontend/.env.local</code> and supply your project keys.
        </p>
      </div>
    )
  }

  // 3. Unauthenticated state - redirect to login, preserving intended destination
  if (!session || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // 4. Authenticated session rejected by backend (HTTP 401 / inactive / unregistered)
  if (profileStatus === 'error') {
    return (
      <div className="max-w-md mx-auto my-12 p-6 bg-rose-50 border border-rose-200 rounded-xl text-slate-800 shadow-sm">
        <div className="flex items-center space-x-3 mb-3">
          <div className="w-10 h-10 rounded-lg bg-rose-100 flex items-center justify-center text-rose-600">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-rose-900">Session Verification Failed</h2>
            <p className="text-xs text-rose-700">Backend denied authorization</p>
          </div>
        </div>
        <p className="text-xs text-slate-600 mb-4 leading-relaxed">
          {profileError || 'Your session credentials could not be verified by the backend application.'}
        </p>
        <button
          type="button"
          onClick={() => signOut()}
          className="inline-flex items-center space-x-1.5 px-3.5 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-medium transition-colors"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign Out</span>
        </button>
      </div>
    )
  }

  // 5. Authenticated & verified
  return children ? <>{children}</> : <Outlet />
}

