import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { GraduationCap, Lock, CheckCircle2, AlertCircle } from 'lucide-react'
import { supabase, isSupabaseConfigured } from '../../lib/supabase'

export const TeacherResetPassword: React.FC = () => {
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const navigate = useNavigate()

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage(null)

    if (newPassword.length < 8) {
      setErrorMessage('Password must be at least 8 characters in length.')
      return
    }

    if (newPassword !== confirmPassword) {
      setErrorMessage('Passwords do not match. Please verify both fields.')
      return
    }

    setSubmitting(true)
    try {
      if (!isSupabaseConfigured) {
        throw new Error(
          'Supabase authentication is unconfigured in this environment. Live credential updates require valid configuration.'
        )
      }

      const { error } = await supabase.auth.updateUser({ password: newPassword })
      if (error) {
        throw new Error(error.message)
      }

      setSuccess(true)
      setTimeout(() => {
        navigate('/teacher/login')
      }, 3000)
    } catch (err: unknown) {
      setErrorMessage(
        err instanceof Error
          ? err.message
          : 'Failed to update password. Your recovery link may have expired.'
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-md mx-auto my-12 p-6 bg-white border border-slate-200 rounded-xl shadow-sm text-slate-900">
      <div className="flex items-center space-x-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-indigo-600 flex items-center justify-center text-white">
          <GraduationCap className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-slate-900">Set New Password</h1>
          <p className="text-xs text-slate-500">Update your faculty account authentication credentials</p>
        </div>
      </div>

      {success ? (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-slate-700 space-y-3">
          <div className="flex items-center space-x-2 text-emerald-800 font-semibold">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <span>Password Updated Successfully</span>
          </div>
          <p className="text-slate-600 leading-relaxed">
            Your password has been securely updated. You will be redirected to the faculty login page
            in a few moments.
          </p>
          <div className="pt-2">
            <Link
              to="/teacher/login"
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-indigo-600 text-white rounded text-xs font-medium hover:bg-indigo-700 transition-colors"
            >
              Sign In Now
            </Link>
          </div>
        </div>
      ) : (
        <form onSubmit={handleReset} className="space-y-4">
          {errorMessage && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
              <span>{errorMessage}</span>
            </div>
          )}

          <div>
            <label htmlFor="new-password" className="block text-xs font-medium text-slate-700 mb-1">
              New Password
            </label>
            <input
              id="new-password"
              type="password"
              required
              minLength={8}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div>
            <label htmlFor="confirm-password" className="block text-xs font-medium text-slate-700 mb-1">
              Confirm New Password
            </label>
            <input
              id="confirm-password"
              type="password"
              required
              minLength={8}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
          >
            <Lock className="w-4 h-4" />
            <span>{submitting ? 'Updating Password...' : 'Save New Password'}</span>
          </button>
        </form>
      )}
    </div>
  )
}
