import React, { type PropsWithChildren } from 'react'
import { Navigate, useLocation, Outlet } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { ShieldAlert, Loader2 } from 'lucide-react'

export const RequireAuth: React.FC<PropsWithChildren> = ({ children }) => {
  const { session, user, loading, isConfigured } = useAuth()
  const location = useLocation()

  // 1. Initial hydration loading state - prevents protected content flashing
  if (loading) {
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

  // 4. Authenticated
  return children ? <>{children}</> : <Outlet />
}
